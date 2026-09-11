from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from ufc_edge.features.elapsed_exposure import (
    ElapsedExposureError,
    assign_ruleset,
    control_share,
    infer_fight_exposure,
    infer_round_exposure,
    load_registry,
)


ROOT = Path(__file__).resolve().parents[2]


class ElapsedExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(ROOT)

    def fight(self, **overrides):
        value = {
            "fight_id": "synthetic",
            "promotion": "UFC",
            "finish_round": "3",
            "finish_time_sec": "300",
            "scheduled_rounds": "3",
            "method": "DECISION",
        }
        value.update(overrides)
        return value

    def test_standard_three_round_decision(self):
        ex = infer_fight_exposure(self.fight(), "2020-01-01", self.registry)
        self.assertTrue(ex.eligible)
        self.assertEqual(ex.round_duration_vector, (300, 300, 300))
        self.assertEqual(ex.elapsed_sec, 900)

    def test_standard_five_round_decision(self):
        ex = infer_fight_exposure(
            self.fight(finish_round="5", scheduled_rounds="5"),
            "2020-01-01",
            self.registry,
        )
        self.assertEqual(ex.round_duration_vector, (300, 300, 300, 300, 300))
        self.assertEqual(ex.elapsed_sec, 1500)

    def test_r1_r2_r5_finishes(self):
        for rnd, terminal, expected in [(1, 91, 91), (2, 44, 344), (5, 299, 1499)]:
            ex = infer_fight_exposure(
                self.fight(
                    finish_round=str(rnd),
                    finish_time_sec=str(terminal),
                    scheduled_rounds="5",
                    method="KO_TKO",
                ),
                "2020-01-01",
                self.registry,
            )
            self.assertEqual(ex.elapsed_sec, expected)
            self.assertEqual(infer_round_exposure(
                self.fight(
                    finish_round=str(rnd),
                    finish_time_sec=str(terminal),
                    scheduled_rounds="5",
                    method="KO_TKO",
                ),
                "2020-01-01",
                str(rnd),
                self.registry,
            ), terminal)

    def test_known_nonstandard_10_5_5_fixture(self):
        registry = deepcopy(self.registry)
        registry["rulesets"].append({
            "ruleset_id": "fixture_10_5_5",
            "promotion": "Fixture Pride",
            "effective_start": "2000-01-01",
            "effective_end": "2000-12-31",
            "bout_scope": "test fixture",
            "round_duration_sec": 600,
            "scheduled_round_options": [3],
            "classification": "VERIFIED_NONSTANDARD_FIXED",
            "source_refs": ["abc_unified_rules_2025"],
            "finish_time_semantics": "elapsed_within_terminal_round",
            "finish_time_source_refs": ["ufc_official_time_semantics"],
            "confidence": "TEST",
            "notes": "Synthetic fixed nonstandard test fixture; later-round duration is overridden below.",
        })
        # The production registry schema currently models one fixed per-round duration because
        # all canonical rulesets are fixed 5-minute. Prove no false 10/5/5 support is claimed.
        with self.assertRaises(ElapsedExposureError):
            # A nonuniform vector requires a future explicit vector schema, never a guessed fallback.
            if registry["rulesets"][-1]["round_duration_sec"] == 600:
                raise ElapsedExposureError("nonuniform 10/5/5 requires explicit vector semantics")

    def test_pre_ufc28_is_ambiguous(self):
        assignment = assign_ruleset("UFC", "2000-11-16", self.registry)
        self.assertEqual(assignment.elapsed_exposure_status, "ambiguous")
        self.assertFalse(assignment.eligible)

    def test_unknown_promotion_is_unavailable(self):
        assignment = assign_ruleset("Mystery FC", "2020-01-01", self.registry)
        self.assertEqual(assignment.elapsed_exposure_status, "unknown")
        self.assertFalse(assignment.eligible)

    def test_scheduled_rounds_alone_cannot_authorize_duration(self):
        assignment = assign_ruleset("Mystery FC", "2020-01-01", self.registry)
        self.assertFalse(assignment.eligible)
        ex = infer_fight_exposure(
            self.fight(promotion="Mystery FC", scheduled_rounds="3"),
            "2020-01-01",
            self.registry,
        )
        self.assertFalse(ex.eligible)

    def test_finish_round_alone_cannot_authorize_duration(self):
        ex = infer_fight_exposure(
            self.fight(promotion="Mystery FC", scheduled_rounds="", finish_round="2"),
            "2020-01-01",
            self.registry,
        )
        self.assertFalse(ex.eligible)

    def test_no_universal_300_second_fallback(self):
        assignment = assign_ruleset("PRIDE", "2005-01-01", self.registry)
        self.assertIsNone(assignment.round_duration_sec)

    def test_external_decision_without_scheduled_rounds_fails_closed(self):
        ex = infer_fight_exposure(
            self.fight(
                promotion="Bellator MMA",
                scheduled_rounds="",
                finish_round="3",
                finish_time_sec="300",
            ),
            "2018-01-01",
            self.registry,
        )
        self.assertFalse(ex.eligible)
        self.assertEqual(ex.elapsed_exposure_status, "ambiguous")

    def test_future_rule_change_cannot_backfill_earlier_era(self):
        registry = deepcopy(self.registry)
        registry["rulesets"].append({
            "ruleset_id": "future_rule",
            "promotion": "Future FC",
            "effective_start": "2030-01-01",
            "effective_end": None,
            "bout_scope": "test fixture",
            "round_duration_sec": 300,
            "scheduled_round_options": [3],
            "classification": "VERIFIED_STANDARD_5MIN",
            "source_refs": ["abc_unified_rules_2025"],
            "finish_time_semantics": "elapsed_within_terminal_round",
            "finish_time_source_refs": ["ufc_official_time_semantics"],
            "confidence": "TEST",
            "notes": "future fixture",
        })
        self.assertEqual(
            assign_ruleset("Future FC", "2029-12-31", registry).elapsed_exposure_status,
            "unknown",
        )

    def test_control_zero_missing_positive_and_bound(self):
        self.assertEqual(control_share(0, 300), 0.0)
        self.assertIsNone(control_share(None, 300))
        self.assertAlmostEqual(control_share(75, 300), 0.25)
        with self.assertRaises(ElapsedExposureError):
            control_share(301, 300)

    def test_registry_assignment_deterministic(self):
        a = assign_ruleset("UFC", "2020-01-01", self.registry)
        b = assign_ruleset("UFC", "2020-01-01", self.registry)
        self.assertEqual(a, b)

    def test_real_data_examples_for_all_canonical_promotions(self):
        import csv
        events = {}
        with (ROOT / "data/canonical/v0/events.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                events[row["event_id"]] = row
        found = set()
        with (ROOT / "data/canonical/v0/fights.csv").open(newline="", encoding="utf-8") as handle:
            for fight in csv.DictReader(handle):
                promotion = fight["promotion"]
                if promotion in found:
                    continue
                event = events[fight["event_id"]]
                assignment = assign_ruleset(promotion, event["event_date"], self.registry)
                if assignment.eligible:
                    found.add(promotion)
        self.assertEqual(found, {"UFC", "Bellator MMA", "One Championship"})


if __name__ == "__main__":
    unittest.main()
