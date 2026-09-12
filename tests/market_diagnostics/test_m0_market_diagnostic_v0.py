from __future__ import annotations

import inspect
import unittest
import numpy as np
import pandas as pd

import ufc_edge.market_diagnostics.m0_v0 as md
from ufc_edge.market_diagnostics.m0_v0 import (
    BLEND_WEIGHT,
    MarketDiagnosticError,
    american_moneyline_to_raw_implied,
    chronological_incremental_test,
    decimal_odds_to_raw_implied,
    fixed_blend,
    match_market,
    median_no_vig_probability,
    normalize_name,
    prepare_public_market_rows,
    proportional_no_vig,
)


class MarketDiagnosticTests(unittest.TestCase):
    def test_moneyline_to_implied_probability(self):
        self.assertAlmostEqual(american_moneyline_to_raw_implied(-150), 0.6)
        self.assertAlmostEqual(american_moneyline_to_raw_implied(200), 1 / 3)
        self.assertAlmostEqual(decimal_odds_to_raw_implied(2.0), 0.5)
        with self.assertRaises(MarketDiagnosticError):
            decimal_odds_to_raw_implied(1.0)

    def test_proportional_no_vig(self):
        a, b = proportional_no_vig(0.60, 0.50)
        self.assertAlmostEqual(a + b, 1.0, places=12)
        self.assertAlmostEqual(a, 0.60 / 1.10, places=12)

    def test_bookmaker_aggregation_is_median(self):
        self.assertEqual(median_no_vig_probability([0.4, 0.5, 0.9]), 0.5)

    def test_blend_weight_fixed_exactly_half(self):
        self.assertEqual(BLEND_WEIGHT, 0.5)
        got = fixed_blend([0.2, 0.8], [0.6, 0.4])
        np.testing.assert_allclose(got, np.array([0.4, 0.6]), atol=1e-15)

    def test_normalized_name_is_conservative(self):
        self.assertEqual(normalize_name("José Aldo"), "jose aldo")
        self.assertEqual(normalize_name("  Max   Holloway "), "max holloway")

    def test_ambiguous_fighter_name_fails_closed(self):
        fighters = pd.DataFrame({
            "fighter_id": ["a", "b", "c"],
            "canonical_name": ["Same Name", "Same-Name", "Other Fighter"],
        })
        market = pd.DataFrame({
            "date": ["2020-01-01"],
            "favourite": ["Same Name"],
            "underdog": ["Other Fighter"],
            "favourite_odds": [1.5],
            "underdog_odds": [2.5],
        })
        prepared = prepare_public_market_rows(market, fighters)
        self.assertEqual(prepared.ambiguous_name_rows, 1)
        self.assertTrue(prepared.usable.empty)

    def test_conflicting_duplicate_market_rows_fail_closed(self):
        fighters = pd.DataFrame({
            "fighter_id": ["a", "b"],
            "canonical_name": ["Alpha", "Beta"],
        })
        market = pd.DataFrame({
            "date": ["2020-01-01", "2020-01-01"],
            "favourite": ["Alpha", "Alpha"],
            "underdog": ["Beta", "Beta"],
            "favourite_odds": [1.5, 1.6],
            "underdog_odds": [2.5, 2.4],
        })
        prepared = prepare_public_market_rows(market, fighters)
        self.assertEqual(prepared.conflicting_duplicate_groups, 1)
        self.assertTrue(prepared.usable.empty)

    def test_identical_duplicate_market_rows_collapse_deterministically(self):
        fighters = pd.DataFrame({"fighter_id": ["a", "b"], "canonical_name": ["Alpha", "Beta"]})
        market = pd.DataFrame({
            "date": ["2020-01-01", "2020-01-01"], "favourite": ["Alpha", "Alpha"],
            "underdog": ["Beta", "Beta"], "favourite_odds": [1.5, 1.5], "underdog_odds": [2.5, 2.5],
        })
        prepared = prepare_public_market_rows(market, fighters)
        self.assertEqual(len(prepared.usable), 1)
        self.assertEqual(prepared.identical_duplicate_rows_collapsed, 1)

    def test_market_orientation_to_fighter_1(self):
        oof = pd.DataFrame({
            "fight_id": ["f1", "f2"], "event_id": ["e1", "e2"],
            "event_date": ["2020-01-01", "2020-01-02"], "fold_id": ["2020", "2020"],
            "target": [1, 0], "logistic_probability": [0.7, 0.4],
            "fighter_1_id": ["a", "d"], "fighter_2_id": ["b", "c"],
        })
        market = pd.DataFrame({
            "event_date": ["2020-01-01", "2020-01-02"], "pair_lo": ["a", "c"], "pair_hi": ["b", "d"],
            "favorite_id": ["b", "c"], "underdog_id": ["a", "d"],
            "favorite_no_vig": [0.65, 0.60], "underdog_no_vig": [0.35, 0.40],
        })
        matched, _ = match_market(oof, market)
        self.assertEqual(matched["market_probability"].tolist(), [0.35, 0.40])
        self.assertEqual(matched["m0_probability"].tolist(), [0.7, 0.4])

    def test_matched_population_equality_across_probabilities(self):
        oof = pd.DataFrame({
            "fight_id": ["f1"], "event_id": ["e1"], "event_date": ["2020-01-01"], "fold_id": ["2020"],
            "target": [1], "logistic_probability": [0.7], "fighter_1_id": ["a"], "fighter_2_id": ["b"],
        })
        market = pd.DataFrame({
            "event_date": ["2020-01-01"], "pair_lo": ["a"], "pair_hi": ["b"],
            "favorite_id": ["a"], "underdog_id": ["b"], "favorite_no_vig": [0.6], "underdog_no_vig": [0.4],
        })
        matched, _ = match_market(oof, market)
        self.assertEqual(len(matched["target"]), len(matched["m0_probability"]))
        self.assertEqual(len(matched["target"]), len(matched["market_probability"]))
        self.assertEqual(len(matched["target"]), len(matched["blend_probability"]))

    def test_incremental_model_is_strictly_chronological(self):
        rows = []
        rng = np.random.default_rng(7)
        for year in range(2018, 2022):
            for i in range(80):
                market = 0.25 + 0.5 * rng.random()
                m0 = 0.25 + 0.5 * rng.random()
                target = int((0.65 * market + 0.35 * m0 + rng.normal(0, 0.16)) >= 0.5)
                rows.append({
                    "fight_id": f"{year}-{i}", "event_date": f"{year}-06-01", "target": target,
                    "market_probability": market, "m0_probability": m0,
                })
        result = chronological_incremental_test(pd.DataFrame(rows))
        self.assertEqual(result["first_evaluated_year"], "2019")
        for fold in result["folds"]:
            year = int(fold["fold_year"])
            self.assertEqual(fold["train_rows"], 80 * (year - 2018))

    def test_no_random_split_or_roi_code_path(self):
        source = inspect.getsource(md).casefold()
        for forbidden in ("train_test_split", "random_split", "def roi", "def profit", "kelly"):
            self.assertNotIn(forbidden, source)

    def test_market_data_cannot_retrain_m0(self):
        source = inspect.getsource(md)
        self.assertNotIn("M0Logistic", source)
        self.assertNotIn("run_validation", source)


if __name__ == "__main__":
    unittest.main()
