from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ufc_edge.models.m1 import (
    C_GRID,
    EXPECTED_FIGHTER_SIDE_PREDICTORS,
    EXPECTED_F02_PREDICTORS,
    EXPECTED_MATCHUP_PREDICTORS,
    M1Error,
    M1Logistic,
    SHARED_CONTEXT_COLUMNS,
    discover_feature_contract,
    inner_validation_years,
    orientation_error,
    swap_model_columns,
)


def schema_fixture() -> dict:
    columns = [
        {"name": "fight_id", "role": "identity", "predictor": False},
        {"name": "event_date", "role": "identity", "predictor": False},
        {
            "name": "scheduled_rounds",
            "role": "fight_context",
            "predictor": True,
            "source_materialized_name": "ctx__scheduled_rounds",
            "source_concept": "scheduled_rounds",
        },
        {
            "name": "ctx__title_bout",
            "role": "fight_context",
            "predictor": True,
            "source_materialized_name": "ctx__title_bout",
            "source_concept": "title_bout",
        },
        {
            "name": "ctx__weight_class",
            "role": "fight_context",
            "predictor": True,
            "source_materialized_name": "ctx__weight_class",
            "source_concept": "weight_class",
        },
    ]
    for i in range(EXPECTED_FIGHTER_SIDE_PREDICTORS):
        source = f"fs__feature_{i:03d}__career__raw"
        columns.append({
            "name": f"f1__{source}", "role": "f1", "predictor": True,
            "source_materialized_name": source, "source_concept": f"feature_{i:03d}",
        })
        columns.append({
            "name": f"f2__{source}", "role": "f2", "predictor": True,
            "source_materialized_name": source, "source_concept": f"feature_{i:03d}",
        })
    for window in ("career", "last5"):
        for direction in ("f1_vs_f2", "f2_vs_f1"):
            source = f"mx__knockdown_creation_vs_vulnerability__{direction}__{window}"
            columns.append({
                "name": source, "role": "mx", "predictor": True,
                "source_materialized_name": source,
                "source_concept": "knockdown_creation_vs_vulnerability",
            })
    source = "mx__reach_difference_cm"
    columns.append({
        "name": source, "role": "mx", "predictor": True,
        "source_materialized_name": source, "source_concept": "reach_difference_cm",
    })
    return {"columns": columns}


def frame_fixture(rows: int = 30) -> pd.DataFrame:
    schema = schema_fixture()
    contract = discover_feature_contract(schema)
    rng = np.random.default_rng(23)
    data: dict[str, object] = {
        "fight_id": [f"f{i}" for i in range(rows)],
        "event_id": [f"e{i}" for i in range(rows)],
        "event_date": pd.date_range("2010-01-01", periods=rows, freq="120D"),
        "promotion": ["UFC"] * rows,
        "binary_winner_eligible": [True] * rows,
        "fighter_1_win": [bool(i % 2) for i in range(rows)],
        "scheduled_rounds": [3] * rows,
        "ctx__title_bout": [False] * rows,
        "ctx__weight_class": ["Lightweight"] * rows,
    }
    for j, (_, left, right) in enumerate(contract.fighter_pairs):
        base = rng.normal(loc=j / 50.0, scale=1.0, size=rows)
        data[left] = base + 0.25
        data[right] = -base + 0.10
    for j, (_, left, right) in enumerate(contract.matchup_pairs):
        base = rng.normal(loc=j / 10.0, scale=0.4, size=rows)
        data[left] = base + 0.2
        data[right] = -base - 0.1
    for _, column in contract.self_antisymmetric_matchups:
        data[column] = rng.normal(size=rows)
    return pd.DataFrame(data)


class M1Tests(unittest.TestCase):
    def test_exact_broad_contract_accounting(self):
        contract = discover_feature_contract(schema_fixture())
        self.assertEqual(EXPECTED_F02_PREDICTORS, 200)
        self.assertEqual(len(contract.fighter_pairs), EXPECTED_FIGHTER_SIDE_PREDICTORS)
        self.assertEqual(len(contract.matchup_pairs), 2)
        self.assertEqual(len(contract.self_antisymmetric_matchups), 1)
        self.assertEqual(contract.source_predictor_count, 197)
        self.assertEqual(len(contract.output_names), 197)
        self.assertEqual(len(contract.model_source_columns), 197)

    def test_shared_context_is_diagnostic_only(self):
        contract = discover_feature_contract(schema_fixture())
        self.assertEqual(contract.excluded_shared_context, SHARED_CONTEXT_COLUMNS)
        self.assertFalse(set(contract.model_source_columns) & set(SHARED_CONTEXT_COLUMNS))

    def test_requires_mirrored_fighter_sources(self):
        schema = schema_fixture()
        schema["columns"] = [item for item in schema["columns"] if item.get("name") != "f2__fs__feature_000__career__raw"]
        with self.assertRaises(M1Error):
            discover_feature_contract(schema)

    def test_requires_directional_matchup_mirror(self):
        schema = schema_fixture()
        schema["columns"] = [
            item for item in schema["columns"]
            if item.get("name") != "mx__knockdown_creation_vs_vulnerability__f2_vs_f1__career"
        ]
        with self.assertRaises(M1Error):
            discover_feature_contract(schema, strict_counts=False)

    def test_logistic_is_deterministic_and_swap_invariant(self):
        contract = discover_feature_contract(schema_fixture())
        frame = frame_fixture(36)
        frame.loc[3, contract.fighter_pairs[5][1]] = np.nan
        frame.loc[4, contract.matchup_pairs[0][2]] = np.nan
        frame.loc[5, contract.self_antisymmetric_matchups[0][1]] = np.nan
        target = frame["fighter_1_win"].astype(int)
        a = M1Logistic.fit(frame, target, contract, C=0.1)
        b = M1Logistic.fit(frame, target, contract, C=0.1)
        pa = a.predict_proba(frame)
        pb = b.predict_proba(frame)
        np.testing.assert_allclose(pa, pb, atol=1e-12)
        swapped = swap_model_columns(frame, contract)
        ps = a.predict_proba(swapped)
        np.testing.assert_allclose(pa + ps, 1.0, atol=1e-10)
        self.assertLessEqual(orientation_error(a, frame, contract), 1e-10)

    def test_training_only_pooled_median(self):
        contract = discover_feature_contract(schema_fixture())
        train = frame_fixture(20)
        valid = frame_fixture(3)
        source, left, _ = contract.fighter_pairs[0]
        train[left] = 10.0
        valid[left] = 9999.0
        model = M1Logistic.fit(train, train["fighter_1_win"].astype(int), contract, C=0.1)
        self.assertNotEqual(model.projector.medians[f"pair::{source}"], 9999.0)

    def test_predeclared_regularization_grid_is_small_l2_grid(self):
        self.assertEqual(C_GRID, (0.01, 0.1, 1.0, 10.0))
        self.assertEqual(len(C_GRID), 4)
        self.assertTrue(all(value > 0 for value in C_GRID))

    def test_inner_years_are_strictly_pre_outer(self):
        frame = frame_fixture(60)
        frame["event_date"] = pd.date_range("2010-01-01", "2019-12-01", periods=60)
        outer_train = frame[frame["event_date"].dt.year < 2018].copy()
        years = inner_validation_years(outer_train)
        self.assertGreaterEqual(len(years), 2)
        self.assertTrue(all(year < 2018 for year in years))
        self.assertGreaterEqual(min(years), 2013)

    def test_forbidden_market_token_fails_closed(self):
        schema = schema_fixture()
        for item in schema["columns"]:
            if item.get("role") == "f1":
                item["name"] = item["name"] + "__sportsbook_odds"
                break
        with self.assertRaises(M1Error):
            discover_feature_contract(schema, strict_counts=False)


if __name__ == "__main__":
    unittest.main()
