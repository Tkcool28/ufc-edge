from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
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

    def test_career_correct(self) -> None:
        rows = [fight("f3", "2024-03-01"), fight("f1", "2024-01-01"), fight("f2", "2024-02-01")]
        selected = self.store.select_window(rows, "career", "2025-01-01T00:00:00Z")
        self.assertEqual(set(selected.fight_ids), {"f1", "f2", "f3"})
        self.assertTrue(all(weight == 1 for weight in selected.weights.values()))

    def test_last3_and_last5_correct(self) -> None:
        rows = [fight(f"f{i}", f"2024-0{i}-01") for i in range(1, 7)]
        self.assertEqual(set(self.store.select_window(rows, "last3", "2025-01-01").fight_ids), {"f4", "f5", "f6"})
        self.assertEqual(set(self.store.select_window(rows, "last5", "2025-01-01").fight_ids), {"f2", "f3", "f4", "f5", "f6"})

    def test_same_date_boundary_is_unavailable(self) -> None:
        rows = [
            fight("f5", "2024-05-01"),
            fight("f4", "2024-04-01"),
            fight("f3a", "2024-03-01"),
            fight("f3b", "2024-03-01"),
        ]
        with self.assertRaises(AmbiguousWindowBoundary):
            self.store.select_window(rows, "last3", "2025-01-01")

    def test_same_date_group_is_allowed_if_whole_group_fits(self) -> None:
        rows = [fight("f5a", "2024-05-01"), fight("f5b", "2024-05-01"), fight("f4", "2024-04-01")]
        selected = self.store.select_window(rows, "last3", "2025-01-01")
        self.assertEqual(set(selected.fight_ids), {"f5a", "f5b", "f4"})

    def test_ewma_weight_matches_contract(self) -> None:
        selected = self.store.select_window([fight("f", "2024-01-02")], "ewma_365d", "2025-01-01T12:00:00Z")
        self.assertAlmostEqual(selected.weights["f"], 0.5, places=12)

    def test_ewma_pools_sufficient_statistics_not_ratios(self) -> None:
        stats = [
            FightStats("old", {"x": 1.0}, {"x": 1.0}, 1),
            FightStats("new", {"x": 0.0}, {"x": 9.0}, 1),
        ]
        aggregate = aggregate_fight_stats(stats, {"old": 0.5, "new": 1.0})
        pooled = aggregate.numerators["x"] / aggregate.denominators["x"]
        average_of_rates = ((1.0 / 1.0) * 0.5 + (0.0 / 9.0)) / 1.5
        self.assertAlmostEqual(pooled, 0.5 / 9.5)
        self.assertNotAlmostEqual(pooled, average_of_rates)


class MissingnessAndShrinkageTests(unittest.TestCase):
    def test_observed_zero_distinct_from_missing(self) -> None:
        self.assertEqual(
            semantic_state(value=0.0, personal_denominator=4.0, compatible_observations=1, prior_fight_count=1),
            "observed_zero",
        )

    def test_zero_denominator_is_insufficient_not_zero(self) -> None:
        self.assertEqual(
            semantic_state(value=0.42, personal_denominator=0.0, compatible_observations=1, prior_fight_count=1),
            "insufficient_exposure",
        )

    def test_missing_stat_domain_is_missing_observation(self) -> None:
        self.assertEqual(
            semantic_state(value=None, personal_denominator=0.0, compatible_observations=0, prior_fight_count=3),
            "missing_observation",
        )

    def test_not_applicable_remains_distinct(self) -> None:
        self.assertEqual(
            semantic_state(
                value=None,
                personal_denominator=None,
                compatible_observations=0,
                prior_fight_count=0,
                not_applicable=True,
            ),
            "not_applicable",
        )

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
        self.assertEqual(
            semantic_state(
                value=estimate.value,
                personal_denominator=0.0,
                compatible_observations=0,
                prior_fight_count=0,
            ),
            "insufficient_exposure",
        )

    def test_missing_history_does_not_masquerade_as_debutant(self) -> None:
        self.assertEqual(
            semantic_state(
                value=None,
                personal_denominator=None,
                compatible_observations=0,
                prior_fight_count=None,
                missing_history=True,
            ),
            "missing_observation",
        )

    def test_time_rate_shrinkage_is_inactive(self) -> None:
        with self.assertRaisesRegex(ValueError, "not materializable"):
            shrink_component(
                1.0,
                2.0,
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

    def test_only_current_v1_statuses_are_selected(self) -> None:
        selected = active_v1_features(self.catalog)
        self.assertEqual({feature["status"] for feature in selected}, ACTIVE_V1_STATUSES)
        self.assertEqual(len(selected), 18)
        self.assertEqual({feature["feature_name"] for feature in selected}, IMPLEMENTED_V1_CONCEPTS)

    def test_non_core_and_time_blocked_statuses_are_excluded(self) -> None:
        selected = {feature["feature_name"] for feature in active_v1_features(self.catalog)}
        blocked = set(self.catalog["elapsed_exposure_policy"]["blocked_feature_concepts"])
        self.assertFalse(selected & blocked)
        for feature in self.catalog["features"]:
            if feature["status"] in {"DEFERRED", "UNSUPPORTED", "RESEARCH_ONLY", "PROXY_ONLY", "V2_OPPONENT_ADJUSTED", "SIMULATOR_COMPONENT"}:
                self.assertNotIn(feature["feature_name"], selected)

    def test_core_v1_does_not_read_position_rankings_or_profile_snapshots(self) -> None:
        tables = {table for feature in active_v1_features(self.catalog) for table in feature["canonical_input_tables"]}
        self.assertTrue({"fighter_round_position", "rankings", "fighter_profile_snapshots"}.isdisjoint(tables))

    def test_consumer_projection_is_contract_driven(self) -> None:
        all_v1 = {feature["feature_name"] for feature in active_v1_features(self.catalog)}
        model0 = {feature["feature_name"] for feature in active_v1_features(self.catalog, "model0")}
        model1 = {feature["feature_name"] for feature in active_v1_features(self.catalog, "model1")}
        self.assertLess(model0, all_v1)
        self.assertIn("sig_strike_efficiency", model0)
        self.assertIn("knockdown_creation_vs_vulnerability", model1)
        self.assertNotIn("knockdown_creation_vs_vulnerability", model0)

    def test_selected_names_are_deterministic_match_contract_and_do_not_collide(self) -> None:
        names = selected_v1_names(self.catalog)
        self.assertEqual(names, selected_v1_names(deepcopy(self.catalog)))
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 58)
        self.assertTrue(set(names) <= set(materialized_feature_names(self.catalog)))

    def test_active_contract_change_fails_closed_without_implementation(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = next(item for item in catalog["features"] if item["feature_name"] == "reversal_rate")
        feature["status"] = "V1_MUST"
        catalog["elapsed_exposure_policy"]["blocked_feature_concepts"].remove("reversal_rate")
        with self.assertRaisesRegex(MaterializationError, "lack F01 implementation"):
            active_v1_features(catalog)


class PriorHierarchyTests(unittest.TestCase):
    class FakeStore:
        def __init__(self, count: int):
            self.count = count
            self.calls: list[str] = []
            self.light = fight("light", "2024-01-01", weight_class="Lightweight")
            self.other = fight("other", "2024-01-02", weight_class="Welterweight")

        def fight_count_in_weight_class(self, weight_class: str, prediction_as_of: str) -> int:
            self.calls.append(prediction_as_of)
            return self.count

        def all_prior_fights(self, prediction_as_of: str) -> list[FightRef]:
            self.calls.append(prediction_as_of)
            return [self.light, self.other]

    class FakeBuilder(StateBuilder):
        def _single_fight_stats(self, fighter_id: str, feature_name: str, prior: FightRef) -> dict[str, FightStats]:
            # Only the lightweight fight has compatible statistical support.
            if prior.weight_class != "Lightweight":
                return {}
            return {"success": FightStats(prior.fight_id, {"success": 1.0}, {"success": 2.0}, 1)}

    def builder(self, count: int) -> StateBuilder:
        builder = object.__new__(self.FakeBuilder)
        builder.store = self.FakeStore(count)
        builder._prior_cache = {}
        return builder

    def test_99_fights_uses_global_hierarchy(self) -> None:
        builder = self.builder(99)
        numerator, denominator, source = builder._population_prior(
            "takedown_conversion", "success", "2025-01-01T00:00:00Z", "Lightweight"
        )
        self.assertEqual((numerator, denominator, source), (1.0, 2.0, "global"))

    def test_100_fights_uses_weight_class_hierarchy(self) -> None:
        builder = self.builder(100)
        numerator, denominator, source = builder._population_prior(
            "takedown_conversion", "success", "2025-01-01T00:00:00Z", "Lightweight"
        )
        self.assertEqual((numerator, denominator, source), (1.0, 2.0, "weight_class:Lightweight"))

    def test_prior_construction_passes_prediction_cutoff_to_store(self) -> None:
        builder = self.builder(99)
        cutoff = "2020-02-03T00:00:00Z"
        builder._population_prior("takedown_conversion", "success", cutoff, "Lightweight")
        self.assertTrue(builder.store.calls)
        self.assertTrue(all(call == cutoff for call in builder.store.calls))


class PointInTimeAndRealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.materializer = V1Materializer(ROOT)
        cls.store = cls.materializer.store
        cls.fights = sorted(cls.store.fights.values(), key=lambda item: (item.event_date, item.fight_id), reverse=True)
        cls.target = cls.fights[0]
        cls.cutoff = f"{cls.target.event_date.isoformat()}T12:00:00Z"

    def test_target_future_and_same_date_fights_are_excluded(self) -> None:
        for fighter_id in (self.target.fighter_a_id, self.target.fighter_b_id):
            prior = self.store.prior_fights(fighter_id, self.cutoff)
            self.assertNotIn(self.target.fight_id, {item.fight_id for item in prior})
            self.assertTrue(all(item.event_date < self.target.event_date for item in prior))

    def test_current_profile_ranking_and_weighin_context_are_not_core(self) -> None:
        concepts = set(self.materializer.concepts())
        self.assertTrue({"profile_context_asof", "ranking_state_asof", "current_fight_weighin_context"}.isdisjoint(concepts))

    def test_orientation_is_canonical_and_provider_side_invariant(self) -> None:
        low, high = sorted((self.target.fighter_a_id, self.target.fighter_b_id))
        self.assertEqual(self.materializer.builder.orient(high, low), (low, high))
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

    def test_real_state_has_exact_contract_projection_and_no_target_names(self) -> None:
        state = self.materializer.materialize_fighter(
            self.target.fighter_a_id,
            self.cutoff,
            target_fight_id=self.target.fight_id,
        )
        expected = {
            name
            for feature in active_v1_features(self.materializer.catalog)
            if feature["feature_name"] not in MATCHUP_IMPLEMENTATIONS
            for name in concept_columns(self.materializer.catalog, feature).values()
        }
        self.assertEqual(set(state.values), expected)
        self.assertEqual(len(state.values), 53)
        self.assertFalse(any("winner" in name or "finish_time" in name for name in state.values))

    def test_deferred_dependency_cannot_activate_indirectly(self) -> None:
        interactions = {
            feature["feature_name"]
            for feature in active_v1_features(self.materializer.catalog)
            if feature["feature_name"] in MATCHUP_IMPLEMENTATIONS
        }
        self.assertEqual(interactions, {"knockdown_creation_vs_vulnerability", "reach_difference_cm"})

    def test_bounded_real_validation_is_repeatable(self) -> None:
        first = self.materializer.bounded_real_validation()
        second = self.materializer.bounded_real_validation()
        self.assertEqual(first, second)
        self.assertEqual(first["active_v1_concept_count"], 18)
        self.assertEqual(first["active_v1_name_count"], 58)
        self.assertEqual(first["elapsed_allowed_sources"], [])
        self.assertIn("long_history", first["cases"])
        self.assertIn("sparse_history", first["cases"])

    def test_provenance_manifest_contains_required_deterministic_identity(self) -> None:
        names = self.materializer.names("model1")
        a = self.materializer.manifest(
            prediction_cutoff=self.cutoff,
            row_count=1,
            consumer="model1",
            materialized_names=names,
            code_commit="test-sha",
            generated_at_utc="2026-01-01T00:00:00Z",
        )
        b = self.materializer.manifest(
            prediction_cutoff=self.cutoff,
            row_count=1,
            consumer="model1",
            materialized_names=names,
            code_commit="test-sha",
            generated_at_utc="2026-02-01T00:00:00Z",
        )
        self.assertEqual(a.deterministic, b.deterministic)
        self.assertEqual(a.deterministic_payload_sha256, b.deterministic_payload_sha256)
        self.assertNotEqual(a.generated_at_utc, b.generated_at_utc)
        required = {
            "feature_contract_version",
            "feature_catalog_sha256",
            "feature_schema_sha256",
            "leakage_registry_sha256",
            "data_contract_version",
            "data_freeze_sha256",
            "canonical_manifest_sha256",
            "materializer_code_commit",
            "prediction_cutoff",
            "selected_consumer",
            "selected_statuses",
            "fighter_orientation_policy",
            "window_policy",
            "shrinkage_policy",
            "elapsed_exposure_policy",
            "materialized_feature_names",
            "row_count",
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

    def test_no_elapsed_time_materializable_concepts_under_current_contract(self) -> None:
        self.assertEqual(self.catalog["elapsed_exposure_policy"]["allowed_sources"], [])
        selected_names = {feature["feature_name"] for feature in self.selected}
        self.assertTrue({"historical_fight_duration", "control_rate", "position_occupancy_profile"}.isdisjoint(selected_names))
        for feature in self.selected:
            denominator = feature["exposure_denominator"]["denominator"].lower()
            self.assertFalse(
                "elapsed" in denominator and any(token in denominator for token in ("minute", "second", "time")),
                feature["feature_name"],
            )

    def test_f01_source_contains_no_hidden_standard_round_or_duration_reconstruction(self) -> None:
        text = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "src/ufc_edge/features/history.py",
                "src/ufc_edge/features/aggregations.py",
                "src/ufc_edge/features/state.py",
                "src/ufc_edge/features/materializer.py",
            )
        ).lower()
        for forbidden in ("300 seconds", "300-second", "five minutes", "5 minutes", "finish_round * 300"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
