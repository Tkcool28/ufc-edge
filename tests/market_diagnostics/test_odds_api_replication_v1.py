from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from ufc_edge.market_diagnostics.core import (
    BLEND_WEIGHT,
    MarketDiagnosticError,
    decimal_odds_to_raw_implied,
    fixed_blend,
    median_no_vig_probability,
    proportional_no_vig,
)
from ufc_edge.market_diagnostics.odds_api_v1 import (
    EXPECTED_CREDITS,
    EXPECTED_EVENTS,
    HARD_CREDIT_CEILING,
    HARD_REQUEST_CEILING,
    match_and_evaluate,
    normalize_snapshot_files,
    preflight,
    snapshot_timestamp,
)


class OddsApiReplicationV1Tests(unittest.TestCase):
    def test_deterministic_snapshot_policy(self):
        self.assertEqual(snapshot_timestamp("2024-04-13"), "2024-04-13T00:00:00Z")
        self.assertEqual(snapshot_timestamp("2020-06-06"), "2020-06-06T10:05:00Z")

    def test_decimal_odds_and_vig_removal(self):
        p1 = decimal_odds_to_raw_implied(1.50)
        p2 = decimal_odds_to_raw_implied(2.70)
        n1, n2 = proportional_no_vig(p1, p2)
        self.assertAlmostEqual(n1 + n2, 1.0, places=12)
        self.assertGreater(n1, n2)

    def test_bookmaker_median(self):
        self.assertAlmostEqual(median_no_vig_probability([0.60, 0.55, 0.58]), 0.58)

    def test_fixed_blend_is_exactly_half(self):
        self.assertEqual(BLEND_WEIGHT, 0.5)
        got = fixed_blend([0.7, 0.2], [0.5, 0.6])
        np.testing.assert_allclose(got, [0.6, 0.4])

    def test_preflight_requires_explicit_authorization(self):
        events = pd.DataFrame({"event_id": range(EXPECTED_EVENTS)})
        with self.assertRaises(MarketDiagnosticError):
            preflight(events, authorized=False, approved_ceiling=3000)

    def test_preflight_enforces_exact_approved_cost(self):
        events = pd.DataFrame({"event_id": range(EXPECTED_EVENTS)})
        report = preflight(events, authorized=True, approved_ceiling=3000)
        self.assertEqual(report["credits_expected"], EXPECTED_CREDITS)
        self.assertEqual(report["hard_credit_ceiling"], HARD_CREDIT_CEILING)
        self.assertEqual(report["hard_request_ceiling"], HARD_REQUEST_CEILING)
        with self.assertRaises(MarketDiagnosticError):
            preflight(events.iloc[:-1], authorized=True, approved_ceiling=3000)
        with self.assertRaises(MarketDiagnosticError):
            preflight(events, authorized=True, approved_ceiling=3001)

    def test_normalization_filters_to_target_event_and_orients_books(self):
        fighters = pd.DataFrame([
            {"fighter_id": "a", "canonical_name": "Alpha One"},
            {"fighter_id": "b", "canonical_name": "Beta Two"},
            {"fighter_id": "c", "canonical_name": "Other Three"},
        ])
        eligible = pd.DataFrame([
            {"event_id": "evt", "fighter_1_id": "b", "fighter_2_id": "a"},
        ])
        payload = {
            "target_event_id": "evt",
            "target_event_date": "2024-01-01",
            "requested_snapshot_timestamp": "2024-01-01T00:00:00Z",
            "provider_response": {
                "data": [
                    {
                        "id": "provider-fight",
                        "home_team": "Alpha One",
                        "away_team": "Beta Two",
                        "commence_time": "2024-01-02T01:00:00Z",
                        "bookmakers": [
                            {"key": "book1", "markets": [{"key": "h2h", "outcomes": [
                                {"name": "Alpha One", "price": 1.80},
                                {"name": "Beta Two", "price": 2.05},
                            ]}]},
                            {"key": "book2", "markets": [{"key": "h2h", "outcomes": [
                                {"name": "Alpha One", "price": 1.75},
                                {"name": "Beta Two", "price": 2.10},
                            ]}]},
                        ],
                    },
                    {
                        "id": "non-target",
                        "home_team": "Alpha One",
                        "away_team": "Other Three",
                        "commence_time": "2024-01-02T02:00:00Z",
                        "bookmakers": [],
                    },
                ]
            },
        }
        with tempfile.TemporaryDirectory() as td:
            Path(td, "2024-01-01_evt.json").write_text(json.dumps(payload))
            market, report = normalize_snapshot_files(Path(td), fighters, eligible)
        self.assertEqual(len(market), 1)
        self.assertEqual(market.iloc[0]["book_count"], 2)
        self.assertEqual(report["non_target_provider_pairs"], 1)

    def test_conflicting_duplicate_provider_pair_fails_closed(self):
        fighters = pd.DataFrame([
            {"fighter_id": "a", "canonical_name": "Alpha"},
            {"fighter_id": "b", "canonical_name": "Beta"},
        ])
        eligible = pd.DataFrame([{"event_id": "evt", "fighter_1_id": "a", "fighter_2_id": "b"}])
        base = {
            "home_team": "Alpha", "away_team": "Beta",
            "bookmakers": [{"key": "book", "markets": [{"key": "h2h", "outcomes": [
                {"name": "Alpha", "price": 1.8}, {"name": "Beta", "price": 2.1}
            ]}]}],
        }
        payload = {
            "target_event_id": "evt",
            "target_event_date": "2024-01-01",
            "requested_snapshot_timestamp": "2024-01-01T00:00:00Z",
            "provider_response": {"data": [
                {**base, "id": "p1", "commence_time": "2024-01-01T20:00:00Z"},
                {**base, "id": "p2", "commence_time": "2024-01-01T20:00:00Z"},
            ]},
        }
        with tempfile.TemporaryDirectory() as td:
            Path(td, "x.json").write_text(json.dumps(payload))
            market, report = normalize_snapshot_files(Path(td), fighters, eligible)
        self.assertTrue(market.empty)
        self.assertEqual(report["ambiguous_duplicate_groups"], 1)

    def test_same_sample_orientation_uses_f02_fighter_1(self):
        eligible = pd.DataFrame([
            {
                "fight_id": "f1", "event_id": "e1", "event_date": "2021-01-01",
                "fighter_1_id": "b", "fighter_2_id": "a", "target": 1,
                "logistic_probability": 0.60,
            },
            {
                "fight_id": "f2", "event_id": "e2", "event_date": "2022-01-01",
                "fighter_1_id": "c", "fighter_2_id": "d", "target": 0,
                "logistic_probability": 0.40,
            },
        ])
        # This tiny fixture cannot run the chronological model (minimum train size),
        # but the join/orientation contract is exercised by expecting that diagnostic gate.
        market = pd.DataFrame([
            {
                "target_event_id": "e1", "pair_lo": "a", "pair_hi": "b",
                "home_id": "a", "away_id": "b",
                "home_market_probability": 0.3, "away_market_probability": 0.7,
                "provider_event_id": "p1", "commence_time": "x",
                "requested_snapshot_timestamp": "x", "book_count": 1,
            },
            {
                "target_event_id": "e2", "pair_lo": "c", "pair_hi": "d",
                "home_id": "c", "away_id": "d",
                "home_market_probability": 0.4, "away_market_probability": 0.6,
                "provider_event_id": "p2", "commence_time": "x",
                "requested_snapshot_timestamp": "x", "book_count": 1,
            },
        ])
        with self.assertRaises(MarketDiagnosticError):
            match_and_evaluate(eligible, market)

    def test_no_roi_optimization_surface_in_replication_source(self):
        source = Path("src/ufc_edge/market_diagnostics/odds_api_v1.py").read_text().lower()
        runner = Path("tools/market_diagnostics/run_m0_md0r_odds_api_v1.py").read_text().lower()
        forbidden = ("kelly", "profit", "units", "edge_threshold", "roi_threshold", "optimal_disagreement")
        for token in forbidden:
            self.assertNotIn(token, source)
            self.assertNotIn(token, runner)
        self.assertIn('"roi_performed": false', runner)


if __name__ == "__main__":
    unittest.main()
