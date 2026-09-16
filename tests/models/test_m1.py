from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ufc_edge.models.m1 import (  # noqa: E402
    ACCEPTANCE_GATES,
    ABLATION_FAMILIES,
    CANDIDATE_GRID,
    M1Error,
    M1Projector,
    FittedM1,
    candidate_name,
    feature_surface_hash,
    fold_frames,
    orientation_error,
    swap_frame,
    surface_pairs,
    validate_candidate_grid,
)

SURFACE_PATH = ROOT / "models" / "m1" / "feature_surface_v1.json"


class M1ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.surface = json.loads(SURFACE_PATH.read_text())

    def test_feature_surface_hash_is_deterministic_and_frozen(self) -> None:
        self.assertEqual(feature_surface_hash(self.surface), self.surface["feature_surface_logical_sha256"])
        self.assertEqual(self.surface["projection"]["final_projected_dimensions"], 197)
        self.assertEqual(self.surface["paired_fighter_predictors"]["semantic_pairs"], 96)
        self.assertEqual(self.surface["matchup_predictors"]["reviewed_columns"], 5)
        self.assertEqual(len(self.surface["shared_context_diagnostic_only"]), 3)

    def test_every_exclusion_has_reason(self) -> None:
        excluded = self.surface["excluded_predictors"]
        self.assertTrue(excluded)
        for item in excluded:
            self.assertFalse(item["accepted"])
            self.assertTrue(item["reason"].strip())

    def test_candidate_grid_is_fixed_and_only_two_families(self) -> None:
        validate_candidate_grid()
        self.assertEqual(len(CANDIDATE_GRID), 13)
        self.assertEqual({spec["family"] for spec in CANDIDATE_GRID}, {"l2", "elasticnet"})
        self.assertEqual(len({candidate_name(spec) for spec in CANDIDATE_GRID}), 13)

    def test_acceptance_gates_are_numeric_and_predeclared(self) -> None:
        self.assertEqual(ACCEPTANCE_GATES["clear_min_both_fold_wins"], 8)
        self.assertEqual(ACCEPTANCE_GATES["modest_min_log_loss_fold_wins"], 7)
        self.assertEqual(ACCEPTANCE_GATES["max_material_ece_deterioration"], 0.010)

    def test_ablation_families_are_predeclared(self) -> None:
        self.assertEqual(len(ABLATION_FAMILIES), 9)
        self.assertIn("sample_support_missingness", ABLATION_FAMILIES)
        self.assertIn("existing_matchup", ABLATION_FAMILIES)


class M1OrientationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.surface = json.loads(SURFACE_PATH.read_text())

    def synthetic_frame(self, rows: int = 16) -> pd.DataFrame:
        rng = np.random.default_rng(7)
        data: dict[str, object] = {}
        for pair in surface_pairs(self.surface):
            a = rng.normal(size=rows)
            b = rng.normal(size=rows)
            a[::7] = np.nan
            b[::5] = np.nan
            data[pair["f1_column"]] = a
            data[pair["f2_column"]] = b
        for item in self.surface["matchup_predictors"]["review"]:
            if len(item["columns"]) == 2:
                a = rng.normal(size=rows); b = rng.normal(size=rows)
                a[::6] = np.nan; b[::4] = np.nan
                data[item["columns"][0]] = a
                data[item["columns"][1]] = b
            else:
                v = rng.normal(size=rows); v[::8] = np.nan
                data[item["columns"][0]] = v
        return pd.DataFrame(data)

    def test_projection_negates_under_swap(self) -> None:
        frame = self.synthetic_frame()
        projector = M1Projector(self.surface).fit(frame)
        original = projector.transform(frame)
        swapped = projector.transform(swap_frame(frame, self.surface))
        np.testing.assert_allclose(swapped, -original, atol=1e-12, rtol=0.0)

    def test_projection_dimensions(self) -> None:
        frame = self.synthetic_frame()
        projector = M1Projector(self.surface).fit(frame)
        self.assertEqual(projector.transform(frame).shape[1], 197)
        missing_ablated = M1Projector(self.surface, ablate_family="sample_support_missingness").fit(frame)
        self.assertEqual(missing_ablated.transform(frame).shape[1], 99)
        mx_ablated = M1Projector(self.surface, ablate_family="existing_matchup").fit(frame)
        self.assertEqual(mx_ablated.transform(frame).shape[1], 192)

    def test_model_probability_complements_under_swap(self) -> None:
        frame = self.synthetic_frame(40)
        target = pd.Series(([0, 1] * 20), dtype=int)
        spec = {"family": "l2", "C": 0.1, "l1_ratio": None}
        model = FittedM1.fit(frame, target, self.surface, spec)
        self.assertLessEqual(orientation_error(model, frame, self.surface), 1e-10)


class M1ChronologyTests(unittest.TestCase):
    def test_outer_training_strictly_precedes_validation(self) -> None:
        frame = pd.DataFrame({
            "fight_id": [f"f{i}" for i in range(12)],
            "event_date": pd.to_datetime([
                "2010-01-01", "2011-01-01", "2012-01-01", "2013-01-01",
                "2014-01-01", "2015-01-02", "2015-03-01", "2016-01-01",
                "2017-01-01", "2018-01-01", "2019-01-01", "2020-01-01",
            ]),
        })
        train, valid = fold_frames(frame, 2015)
        self.assertLess(train["event_date"].max(), valid["event_date"].min())
        self.assertFalse(set(train["fight_id"]) & set(valid["fight_id"]))

    def test_overlap_fails_closed(self) -> None:
        frame = pd.DataFrame({"fight_id": ["same", "same"], "event_date": pd.to_datetime(["2014-01-01", "2015-01-01"])})
        with self.assertRaises(M1Error):
            fold_frames(frame, 2015)


if __name__ == "__main__":
    unittest.main()
