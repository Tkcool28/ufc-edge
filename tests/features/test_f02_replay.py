from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import importlib.util
import json
import unittest

from ufc_edge.features.replay import ReplayEngine, ReplayError, build_target_row, prediction_as_of


ROOT = Path(__file__).resolve().parents[2]


class F02ReplayContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = ReplayEngine(ROOT, optimized=False)
        cls.targets = cls.engine.targets()
        cls.fixture = cls.engine.equivalence_fixture(max_targets=16)
        cls.by_id = {item.fight_id: item for item in cls.targets}

    def test_current_governed_surface_counts_and_namespaces(self) -> None:
        schema = self.engine.schema
        self.assertEqual(len(self.engine.materializer.catalog["features"]), 60)
        self.assertEqual(len(self.engine.materializer.concepts()), 24)
        inventory = json.loads((ROOT / "features/feature_inventory.json").read_text(encoding="utf-8"))
        self.assertEqual(inventory["catalog_declared_active_variant_count"], 164)
        self.assertEqual(inventory["governance_version"], "1.0.0")
        self.assertEqual(schema.f01_materialized_value_count, 104)
        self.assertEqual(schema.fighter_specific_value_count, 96)
        self.assertEqual(schema.shared_fight_context_value_count, 3)
        self.assertEqual(schema.matchup_interaction_value_count, 5)
        self.assertEqual(schema.row_predictor_count, 200)
        predictors = [item for item in schema.columns if item["predictor"]]
        self.assertEqual(len(predictors), 200)
        self.assertEqual(len(schema.columns), 207)
        self.assertEqual(len({item["name"] for item in predictors}), 200)
        self.assertEqual(sum(item["role"] == "f1" for item in predictors), 96)
        self.assertEqual(sum(item["role"] == "f2" for item in predictors), 96)
        self.assertEqual(sum(item["role"] == "fight_context" for item in predictors), 3)
        self.assertEqual(sum(item["role"] == "mx" for item in predictors), 5)

    def test_shared_context_classification_and_nonduplication(self) -> None:
        schema = self.engine.schema
        shared = [item for item in schema.columns if item["role"] == "fight_context"]
        self.assertEqual(
            {item["source_concept"] for item in shared},
            {"scheduled_rounds", "title_bout", "weight_class"},
        )
        by_concept = {item["source_concept"]: item for item in shared}
        self.assertEqual(by_concept["scheduled_rounds"]["name"], "scheduled_rounds")
        self.assertEqual(by_concept["title_bout"]["name"], "ctx__title_bout")
        self.assertEqual(by_concept["weight_class"]["name"], "ctx__weight_class")
        names = {item["name"] for item in schema.columns}
        for concept in ("scheduled_rounds", "title_bout", "weight_class"):
            source = by_concept[concept]["source_materialized_name"]
            self.assertNotIn(f"f1__{source}", names)
            self.assertNotIn(f"f2__{source}", names)

    def test_fighter_specific_context_remains_oriented(self) -> None:
        columns = self.engine.schema.columns
        by_source_role = {
            (item.get("source_materialized_name"), item["role"])
            for item in columns
            if item.get("source_materialized_name")
        }
        expected_concepts = {
            "age_at_fight",
            "layoff_days",
            "physical_size_profile",
            "prior_scale_weight_lbs",
        }
        sources_by_concept: dict[str, list[str]] = {}
        for source in self.engine.materializer.names():
            parts = source.split("__")
            if len(parts) >= 2 and parts[1] in expected_concepts:
                sources_by_concept.setdefault(parts[1], []).append(source)
        self.assertEqual(set(sources_by_concept), expected_concepts)
        for sources in sources_by_concept.values():
            for source in sources:
                self.assertIn((source, "f1"), by_source_role)
                self.assertIn((source, "f2"), by_source_role)

    def test_scheduled_rounds_is_exactly_one_model_predictor(self) -> None:
        scheduled = [
            item for item in self.engine.schema.columns
            if item.get("source_concept") == "scheduled_rounds" and item["predictor"]
        ]
        self.assertEqual(len(scheduled), 1)
        self.assertEqual(scheduled[0]["name"], "scheduled_rounds")
        self.assertEqual(scheduled[0]["role"], "fight_context")
        promotion = next(item for item in self.engine.schema.columns if item["name"] == "promotion")
        self.assertFalse(promotion["predictor"])
        self.assertEqual(promotion["role"], "identity")

    def test_shared_context_equality_guard(self) -> None:
        target = self.fixture[-1]
        original = self.engine.materializer.materialize_matchup(
            target.fighter_a_id,
            target.fighter_b_id,
            prediction_as_of(target),
            target_fight_id=target.fight_id,
        )
        source = next(
            name for name in original.fighter_2.values
            if original.fighter_2.values[name].source_concept == "title_bout"
        )
        values = dict(original.fighter_2.values)
        values[source] = replace(values[source], value=not bool(values[source].value))
        broken = replace(original, fighter_2=replace(original.fighter_2, values=values))
        materialize = self.engine.materializer.materialize_matchup
        self.engine.materializer.materialize_matchup = lambda *args, **kwargs: broken
        try:
            with self.assertRaisesRegex(ReplayError, "shared fight-context disagreement"):
                self.engine.build_row(target)
        finally:
            self.engine.materializer.materialize_matchup = materialize

    def test_shared_context_missingness_guard(self) -> None:
        target = self.fixture[-1]
        original = self.engine.materializer.materialize_matchup(
            target.fighter_a_id,
            target.fighter_b_id,
            prediction_as_of(target),
            target_fight_id=target.fight_id,
        )
        source = next(
            name for name in original.fighter_2.values
            if original.fighter_2.values[name].source_concept == "weight_class"
        )
        values = dict(original.fighter_2.values)
        current = values[source].missingness_state
        alternate = "missing_observation" if current != "missing_observation" else "observed_positive"
        values[source] = replace(values[source], missingness_state=alternate)
        broken = replace(original, fighter_2=replace(original.fighter_2, values=values))
        materialize = self.engine.materializer.materialize_matchup
        self.engine.materializer.materialize_matchup = lambda *args, **kwargs: broken
        try:
            with self.assertRaisesRegex(ReplayError, "shared fight-context disagreement"):
                self.engine.build_row(target)
        finally:
            self.engine.materializer.materialize_matchup = materialize

    def test_universe_is_unique_and_deterministically_ordered(self) -> None:
        ids = [item.fight_id for item in self.targets]
        self.assertEqual(len(ids), 9252)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(
            self.targets,
            sorted(self.targets, key=lambda item: (item.event_date, item.event_id, item.fight_id)),
        )

    def test_cutoff_is_target_date_and_excludes_target_and_same_day_history(self) -> None:
        for target in self.fixture[:6]:
            cutoff = prediction_as_of(target)
            self.assertTrue(cutoff.startswith(target.event_date.isoformat()))
            built = self.engine.build_row(target)
            for meta in built.audit.values():
                self.assertNotIn(target.fight_id, meta["lineage_fight_ids"])
            for fighter_id in (target.fighter_a_id, target.fighter_b_id):
                prior = self.engine.store.prior_fights(fighter_id, cutoff)
                self.assertTrue(all(item.event_date < target.event_date for item in prior))

    def test_orientation_reversal_is_invariant(self) -> None:
        target = self.fixture[-1]
        cutoff = prediction_as_of(target)
        forward = self.engine.materializer.materialize_matchup(
            target.fighter_a_id, target.fighter_b_id, cutoff, target_fight_id=target.fight_id
        )
        reverse = self.engine.materializer.materialize_matchup(
            target.fighter_b_id, target.fighter_a_id, cutoff, target_fight_id=target.fight_id
        )
        self.assertEqual(forward.projection(), reverse.projection())
        self.assertEqual((forward.fighter_1_id, forward.fighter_2_id), tuple(sorted((target.fighter_a_id, target.fighter_b_id))))

    def test_target_label_mutation_does_not_change_predictors(self) -> None:
        target = self.fixture[-1]
        before = self.engine.build_row(target).row
        original = self.engine.store.fights[target.fight_id]
        mutated = replace(
            original,
            winner_id=original.fighter_b_id if original.winner_id != original.fighter_b_id else original.fighter_a_id,
            result="no_contest",
            method="SUBMISSION",
            finish_round=1,
            finish_time_sec=1,
        )
        self.engine.store.fights[target.fight_id] = mutated
        self.engine.materializer.builder._prior_cache.clear()
        try:
            after = self.engine.build_row(mutated).row
        finally:
            self.engine.store.fights[target.fight_id] = original
            self.engine.materializer.builder._prior_cache.clear()
        self.assertEqual(before, after)

    def test_future_result_and_round_stat_mutation_does_not_change_earlier_predictor(self) -> None:
        pair = None
        for target in self.targets:
            for fighter_id in (target.fighter_a_id, target.fighter_b_id):
                future = next(
                    (
                        item for item in self.engine.store.fights_by_fighter.get(fighter_id, [])
                        if item.event_date > target.event_date
                    ),
                    None,
                )
                if future is not None:
                    pair = (target, future, fighter_id)
                    break
            if pair:
                break
        self.assertIsNotNone(pair)
        target, future, fighter_id = pair  # type: ignore[misc]
        before = self.engine.build_row(target).row
        original_future = self.engine.store.fights[future.fight_id]
        self.engine.store.fights[future.fight_id] = replace(
            original_future,
            winner_id=original_future.fighter_b_id,
            result="no_contest",
            method="SUBMISSION",
            finish_round=1,
            finish_time_sec=1,
        )
        round_rows = self.engine.store.round_rows_for_fight(fighter_id, future.fight_id)
        changed_row = round_rows[0] if round_rows else None
        old_value = None
        if changed_row is not None:
            old_value = changed_row.get("sig_strikes_landed")
            changed_row["sig_strikes_landed"] = "999999"
        self.engine.materializer.builder._prior_cache.clear()
        self.engine.materializer.builder._round_elapsed_cache.clear()
        try:
            after = self.engine.build_row(target).row
        finally:
            self.engine.store.fights[future.fight_id] = original_future
            if changed_row is not None:
                changed_row["sig_strikes_landed"] = old_value or ""
            self.engine.materializer.builder._prior_cache.clear()
            self.engine.materializer.builder._round_elapsed_cache.clear()
        self.assertEqual(before, after)

    def test_removing_all_post_cutoff_fights_does_not_change_row(self) -> None:
        target = self.fixture[len(self.fixture) // 2]
        before = self.engine.build_row(target).row
        original_fights = self.engine.store.fights
        self.engine.store.fights = {
            fight_id: fight for fight_id, fight in original_fights.items()
            if fight.event_date <= target.event_date
        }
        self.engine.materializer.builder._prior_cache.clear()
        try:
            after = self.engine.build_row(target).row
        finally:
            self.engine.store.fights = original_fights
            self.engine.materializer.builder._prior_cache.clear()
        self.assertEqual(before, after)

    def test_target_contract_preserves_nonbinary_states(self) -> None:
        candidate_states = {"draw", "no_contest"}
        seen = set()
        for target in self.targets:
            if target.result not in candidate_states:
                continue
            predictor = self.engine.build_row(target).row
            attached = build_target_row(target, predictor)
            self.assertFalse(attached["binary_winner_eligible"])
            self.assertIsNone(attached["fighter_1_win"])
            self.assertEqual(attached["target_state"], target.result)
            seen.add(target.result)
            if seen == candidate_states:
                break
        self.assertTrue(seen, "canonical universe should expose at least one explicit draw/no_contest case")

    def test_external_history_is_not_zero_filled_into_round_features(self) -> None:
        target = None
        fighter_id = None
        external_id = None
        for candidate in self.fixture:
            cutoff = prediction_as_of(candidate)
            for fid in (candidate.fighter_a_id, candidate.fighter_b_id):
                external = next(
                    (
                        prior for prior in self.engine.store.prior_fights(fid, cutoff)
                        if (prior.promotion or "").casefold() != "ufc"
                        and not self.engine.store.round_rows_for_fight(fid, prior.fight_id)
                    ),
                    None,
                )
                if external is not None:
                    target, fighter_id, external_id = candidate, fid, external.fight_id
                    break
            if target is not None:
                break
        if target is None:
            self.skipTest("equivalence fixture has no external/no-round-stat edge")
        built = self.engine.build_row(target)
        role = "f1" if built.row["fighter_1_id"] == fighter_id else "f2"
        count_meta = next(
            meta for name, meta in built.audit.items()
            if name.startswith(f"{role}__") and meta["source_concept"] == "prior_fight_count"
        )
        sig_meta = next(
            meta for name, meta in built.audit.items()
            if name.startswith(f"{role}__")
            and meta["source_concept"] == "sig_strike_efficiency"
            and meta["component"] == "accuracy"
            and meta["window"] == "career"
        )
        self.assertIn(external_id, count_meta["lineage_fight_ids"])
        self.assertNotIn(external_id, sig_meta["lineage_fight_ids"])

    def test_elapsed_states_are_auditable_without_positional_duration_proxy(self) -> None:
        target = self.fixture[-1]
        built = self.engine.build_row(target)
        elapsed = [
            meta for meta in built.audit.values()
            if meta["source_concept"] in self.engine.elapsed_feature_names
        ]
        self.assertTrue(elapsed)
        self.assertTrue(all(meta["missingness_state"] in {
            "observed_positive", "observed_zero", "missing_observation", "not_applicable", "insufficient_exposure"
        } for meta in elapsed))
        self.assertFalse(any("position" in meta["source_concept"] for meta in elapsed))


class F02OptimizedEquivalenceTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("numpy"), "numpy is replay-only; dedicated F02 CI installs it")
    def test_optimized_path_is_exact_on_representative_fixture(self) -> None:
        engine = ReplayEngine(ROOT)
        fixture = engine.equivalence_fixture(max_targets=8)
        result = engine.validate_reference_equivalence(fixture)
        self.assertEqual(result["status"], "exact_equal")
        self.assertEqual(result["target_count"], len(fixture))


if __name__ == "__main__":
    unittest.main()
