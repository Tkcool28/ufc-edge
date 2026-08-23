from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
import math
import unittest

from ufc_edge.features.aggregations import FightStats, aggregate_fight_stats, semantic_state, shrink_component
from ufc_edge.features.contract import load_feature_catalog, materialized_feature_names
from ufc_edge.features.history import AmbiguousWindowBoundary, CanonicalStore, FightRef
from ufc_edge.features.materializer import V1Materializer
from ufc_edge.features.state import (
    ACTIVE_V1_STATUSES,
    IMPLEMENTED_V1_CONCEPTS,
    MATCHUP_IMPLEMENTATIONS,
    MaterializationError,
    StateBuilder,
    active_v1_features,
    concept_columns,
    selected_v1_names,
)


ROOT = Path(__file__).resolve().parents[2]


def fight(fid: str, when: str, a: str = "a", b: str = "b", weight_class: str | None = "Lightweight") -> FightRef:
    return FightRef(
        fight_id=fid,
        event_id=f"event-{fid}",
        event_date=date.fromisoformat(when),
        fighter_a_id=a,
        fighter_b_id=b,
        promotion="UFC",
        weight_class=weight_class,
        scheduled_rounds=3,
        title_bout=False,
        winner_id=a,
        result="WIN",
        method="DECISION",
        finish_round=3,
        finish_time_sec=300,
    )


class WindowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = object.__new__(CanonicalStore)

    def test_career_contains_all_without_using_order_for_selection(self) -> None:
        rows = [fight("f3", "2024-03-01"), fight("f1", "2024-01-01"), fight("f2", "2024-02-01")]
        selected = self.store.select_window(rows, "career", "2025-01-01T00:00:00Z")
        self.assertEqual(set(selected.fight_ids), {"f1", "f2", "f3"})
        self.assertTrue(all(weight == 1 for weight in selected.weights.values()))

    def test_last3_and_last5_are_date_bounded(self) -> None:
        rows = [fight(f"f{i}", f"2024-0{i}-01") for i in range(1, 7)]
        self.assertEqual(set(self.store.select_window(rows, "last3", "2025-01-01").fight_ids), {"f4", "f5", "f6"})
        self.assertEqual(set(self.store.select_window(rows, "last5", "2025-01-01").fight_ids), {"f2", "f3", "f4", "f5", "f6"})

    def test_same_date_boundary_is_unavailable(self) -> None:
        rows = [
            fight("f5", "2024-05-01"),
            fight("f4a", "2024-04-01"),
            fight("f4b", "2024-04-01"),
            fight("f3", "2024-03-01"),
        ]
        with self.assertRaises(AmbiguousWindowBoundary):
            self.store.select_window(rows, "last3", "2025-01-01")

    def test_same_date_group_is_allowed_when_whole_group_fits(self) -> None:
        rows = [fight("f5a", "2024-05-01"), fight("f5b", "2024-05-01"), fight("f4", "2024-04-01")]
        selected = self.store.select_window(rows, "last3", "2025-01-01")
        self.assertEqual(set(selected.fight_ids), {"f5a", "f5b", "f4"})

    def test_ewma_weight_matches_contract(self) -> None:
        rows = [fight("f", "2024-01-02")]
        selected = self.store.select_window(rows, "ewma_365d", "2025-01-01T12:00:00Z")
        self.assertAlmostEqual(selected.weights["f"], 0.5, places=12)

    def test_ewma_pools_sufficient_statistics_not_ratios(self) -> None:
        stats = [
            FightStats("old", {"x": 1.0}, {"x": 1.0}, 1),
            FightStats("new", {"x": 0.0}, {"x": 9.0}, 1),
        ]
        agg = aggregate_fight_stats(stats, {"old": 0.5, "new": 1.0})
        pooled = agg.numerators["x"] / agg.denominators["x"]
        average_of_rates = ((1.0 / 1.0) * 0.5 + (0.0 / 9.0) * 1.0) / 1.5
        self.assertNotAlmostEqual(pooled, average_of_rates)
        self.assertAlmostEqual(pooled, 0.5 / 9.5)


class MissingnessAndShrinkageTests(unittest.TestCase):
    def test_observed_zero_is_not_missing(self) -> None:
        state = semantic_state(
            value=0.0,
            personal_denominator=4.0,
            compatible_observations=1,
            prior_fight_count=1,
        )
        self.assertEqual(state, "observed_zero")

    def test_zero_denominator_is_insufficient_not_zero(self) -> None:
        state = semantic_state(
            value=0.42,
            personal_denominator=0.0,
            compatible_observations=1,
            prior_fight_count=1,
        )
        self.assertEqual(state, "insufficient_exposure")

    def test_missing_stat_domain_is_missing_observation(self) -> None:
        state = semantic_state(
            value=None,
            personal_denominator=0.0,
            compatible_observations=0,
            prior_fight_count=3,
        )
        self.assertEqual(state, "missing_observation")

    def test_debutant_zero_personal_support_can_receive_prior(self) -> None:
        estimate = shrink_component(
            0.0,
            0.0,
            shrinkage_rule="attempt_probability_v1",
            prior_numerator=40.0,
            prior_denominator=100.0,
            prior_source="global",
        )
        self.assertAlmostEqual(estimate.value or -1, 0.4)
        state = semantic_state(
            value=estimate.value,
            personal_denominator=0.0,
            compatible_observations=0,
            prior_fight_count=0,
        )
        self.assertEqual(state, "insufficient_exposure")

    def test_missing_history_does_not_become_debutant_prior(self) -> None:
        state = semantic_state(
            value=None,
            personal_denominator=None,
            compatible_observations=0,
            prior_fight_count=None,
            missing_history=True,
        )
        self.assertEqual(state, "missing_observation")

    def test_time_rate_shrinkage_is_inactive(self) -> None:
        with self.assertRaisesRegex(ValueError, "not materializable"):
            shrink_component(
                1.0, 2.0,
                shrinkage_rule="time_rate_v1",
                prior_numerator=1.0,
                prior_denominator=2.0,
                prior_source="global",
            )


class ContractSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_feature_catalog(ROOT)

    def test_contract_version_and_elapsed_gate(self) -> None:
        self.assertEqual(self.catalog["feature_contract_version"], "0.1.1-draft")
        self.assertEqual(self.catalog["elapsed_exposure_policy"]["allowed_sources"], [])

    def test_only_v1_statuses_are_selected(self) -> None:
        selected = active_v1_features(self.catalog)
        self.assertEqual({feature["status"] for feature in selected}, ACTIVE_V1_STATUSES)
        self.assertEqual(len(selected), 18)
        self.assertEqual({feature["feature_name"] for feature in selected}, IMPLEMENTED_V1_CONCEPTS)

    def test_non_core_statuses_are_excluded(self) -> None:
        selected = {feature["feature_name"] for feature in active_v1_features(self.catalog)}
        for feature in self.catalog["features"]:
            if feature["status"] in {"DEFERRED", "UNSUPPORTED", "RESEARCH_ONLY", "PROXY_ONLY", "V2_OPPONENT_ADJUSTED", "SIMULATOR_COMPONENT"}:
                self.assertNotIn(feature["feature_name"], selected)

    def test_blocked_elapsed_concepts_are_excluded(self) -> None:
        selected = {feature["feature_name"] for feature in active_v1_features(self.catalog)}
        blocked = set(self.catalog["elapsed_exposure_policy"]["blocked_feature_concepts"])
        self.assertFalse(selected & blocked)

    def test_core_v1_does_not_read_position_rankings_or_profile_snapshots(self) -> None:
        tables = {
            table
            for feature in active_v1_features(self.catalog)
            for table in feature["canonical_input_tables"]
        }
        self.assertNotIn("fighter_round_position", tables)
        self.assertNotIn("rankings", tables)
        self.assertNotIn("fighter_profile_snapshots", tables)

    def test_consumer_projection_is_contract_driven(self) -> None:
        model0 = {feature["feature_name"] for feature in active_v1_features(self.catalog, "model0")}
        model1 = {feature["feature_name"] for feature in active_v1_features(self.catalog, "model1")}
        self.assertLess(model0, {feature["feature_name"] for feature in active_v1_features(self.catalog)})
        self.assertIn("sig_strike_efficiency", model0)
        self.assertIn("knockdown_creation_vs_vulnerability", model1)
        self.assertNotIn("knockdown_creation_vs_vulnerability", model0)

    def test_selected_names_are_deterministic_and_bounded(self) -> None:
        names = selected_v1_names(self.catalog)
        self.assertEqual(names, selected_v1_names(deepcopy(self.catalog)))
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 58)
        self.assertTrue(set(names) <= set(materialized_feature_names(self.catalog)))

    def test_selected_names_contain_no_deferred_time_concepts(self) -> None:
        names = "\n".join(selected_v1_names(self.catalog))
        for concept in self.catalog["elapsed_exposure_policy"]["blocked_feature_concepts"]:
            self.assertNotIn(f"__{concept}__", names)

    def test_active_contract_change_fails_closed_without_implementation(self) -> None:
        catalog = deepcopy(self.catalog)
        deferred = next(feature for feature in catalog["features"] if feature["feature_name"] == "reversal_rate")
        deferred["status"] = "V1_MUST"
        catalog["elapsed_exposure_policy"]["blocked_feature_concepts"].remove("reversal_rate")
        with self.assertRaisesRegex(MaterializationError, "lack F01 implementation"):
            active_v1_features(catalog)


class PointInTimeAndRealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.materializer = V1Materializer(ROOT)
        cls.store = cls.materializer.store
        cls.fights = sorted(cls.store.fights.values(), key=lambda f: (f.event_date, f.fight_id), reverse=True)
        cls.target = cls.fights[0]
        cls.cutoff = f"{cls.target.event_date.isoformat()}T12:00:00Z"

    def test_target_fight_is_excluded_for_both_participants(self) -> None:
        for fighter_id in (self.target.fighter_a_id, self.target.fighter_b_id):
            prior = self.store.prior_fights(fighter_id, self.cutoff)
            self.assertNotIn(self.target.fight_id, {fight.fight_id for fight in prior})

    def test_future_and_same_date_fights_are_excluded(self) -> None:
        for fighter_id in (self.target.fighter_a_id, self.target.fighter_b_id):
            prior = self.store.prior_fights(fighter_id, self.cutoff)
            self.assertTrue(all(fight.event_date < self.target.event_date for fight in prior))

    def test_current_weighin_context_is_not_selected(self) -> None:
        self.assertNotIn("current_fight_weighin_context", self.materializer.concepts())

    def test_orientation_is_canonical_id_order(self) -> None:
        low, high = sorted((self.target.fighter_a_id, self.target.fighter_b_id))
        self.assertEqual(self.materializer.builder.orient(high, low), (low, high))

    def test_real_fighter_state_has_exact_contract_projection(self) -> None:
        state = self.materializer.materialize_fighter(
            self.target.fighter_a_id,
            self.cutoff,
            target_fight_id=self.target.fight_id,
        )
        expected = {
            name for feature in active_v1_features(self.materializer.catalog)
            if feature["feature_name"] not in MATCHUP_IMPLEMENTATIONS
            for name in concept_columns(self.materializer.catalog, feature).values()
        }
        self.assertEqual(set(state.values), expected)
        self.assertEqual(len(state.values), 53)
        self.assertFalse(any("winner" in name or "finish_time" in name for name in state.values))

    def test_matchup_is_invariant_to_input_side(self) -> None:
        forward = self.materializer.materialize_matchup(
            self.target.fighter_a_id,
            self.target.fighter_b_id,
            self.cutoff,
            target_fight_id=self.target.fight_id,
        )
        reverse = self.materializer.materialize_matchup(
            self.target.fighter_b_id,
            self.target.fighter_a_id,
            self.cutoff,
            target_fight_id=self.target.fight_id,
        )
        self.assertEqual(forward.projection(), reverse.projection())
        self.assertEqual(len(forward.interactions), 5)

    def test_deferred_dependency_cannot_activate_indirectly(self) -> None:
        interactions = {feature["feature_name"] for feature in active_v1_features(self.materializer.catalog) if feature["feature_name"] in MATCHUP_IMPLEMENTATIONS}
        self.assertEqual(interactions, {"knockdown_creation_vs_vulnerability", "reach_difference_cm"})
        self.assertNotIn("takedown_pressure_vs_defense", interactions)

    def test_bounded_real_validation_is_deterministic(self) -> None:
        first = self.materializer.bounded_real_validation()
        second = self.materializer.bounded_real_validation()
        self.assertEqual(first, second)
        self.assertEqual(first["active_v1_concept_count"], 18)
        self.assertEqual(first["active_v1_name_count"], 58)
        self.assertEqual(first["elapsed_allowed_sources"], [])
        self.assertIn("long_history", first["cases"])
        self.assertIn("sparse_history", first["cases"])

    def test_provenance_manifest_is_complete_and_deterministically_hashed(self) -> None:
        fields = self.materializer.names("model1")
        a = self.materializer.manifest(
            prediction_cutoff=self.cutoff,
            row_count=1,
            consumer="model1",
            materialized_names=fields,
            code_commit="test-sha",
            generated_at_utc="2026-01-01T00:00:00Z",
        )
        b = self.materializer.manifest(
            prediction_cutoff=self.cutoff,
            row_count=1,
            consumer="model1",
            materialized_names=fields,
            code_commit="test-sha",
            generated_at_utc="2026-02-01T00:00:00Z",
        )
        self.assertEqual(a.deterministic, b.deterministic)
        self.assertEqual(a.deterministic_payload_sha256, b.deterministic_payload_sha256)
        self.assertNotEqual(a.generated_at_utc, b.generated_at_utc)
        required = {
            "feature_contract_version", "feature_catalog_sha256", "feature_schema_sha256",
            "leakage_registry_sha256", "data_contract_version", "data_freeze_sha256",
            "canonical_manifest_sha256", "materializer_code_commit", "prediction_cutoff",
            "selected_consumer", "selected_statuses", "fighter_orientation_policy",
            "window_policy", "shrinkage_policy", "elapsed_exposure_policy",
            "materialized_feature_names", "row_count",
        }
        self.assertTrue(required <= set(a.deterministic))
        rendered = str(a.to_dict()).lower()
        self.assertNotIn("data/raw", rendered)
        self.assertNotIn("provider-specific", rendered)


class TimeExposureSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_feature_catalog(ROOT)
        cls.selected = active_v1_features(cls.catalog)

    def test_no_elapsed_exposure_source_is_allowed(self) -> None:
        self.assertEqual(self.catalog["elapsed_exposure_policy"]["allowed_sources"], [])

    def test_no_active_formula_uses_historical_elapsed_denominator(self) -> None:
        for feature in self.selected:
            denominator = feature["exposure_denominator"]["denominator"].lower()
            self.assertFalse("elapsed" in denominator and any(token in denominator for token in ("minute", "second", "time")), feature["feature_name"])

    def test_no_hidden_round_duration_reconstruction_inputs_are_selected(self) -> None:
        selected_names = {feature["feature_name"] for feature in self.selected}
        self.assertNotIn("historical_fight_duration", selected_names)
        self.assertNotIn("control_rate", selected_names)
        self.assertNotIn("position_occupancy_profile", selected_names)

    def test_no_300_second_assumption_in_f01_code(self) -> None:
        text = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "src/ufc_edge/features/history.py",
                "src/ufc_edge/features/aggregations.py",
                "src/ufc_edge/features/state.py",
                "src/ufc_edge/features/materializer.py",
            )
        ).lower()
        self.assertNotIn("300 seconds", text)
        self.assertNotIn("300-second", text)
        self.assertNotIn("five minutes", text)
        self.assertNotIn("5 minutes", text)
        self.assertNotIn("finish_round * 300", text)


if __name__ == "__main__":
    unittest.main()
