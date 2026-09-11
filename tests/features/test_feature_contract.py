from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from ufc_edge.features.contract import (
    AUTHORITATIVE_FILES,
    ContractError,
    load_canonical_contract,
    load_feature_catalog,
    load_feature_schema,
    load_leakage_registry,
    materialized_feature_names,
    validate_catalog,
    validate_repository_contract,
)


ROOT = Path(__file__).resolve().parents[2]


class FeatureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_feature_catalog(ROOT)
        cls.schema = load_feature_schema(ROOT)
        cls.registry = load_leakage_registry(ROOT)
        cls.canonical = load_canonical_contract(ROOT)

    def validate(self, catalog: dict | None = None) -> dict:
        return validate_catalog(
            deepcopy(catalog if catalog is not None else self.catalog),
            deepcopy(self.schema),
            deepcopy(self.canonical),
            deepcopy(self.registry),
        )

    def feature(self, name: str, catalog: dict | None = None) -> dict:
        source = catalog if catalog is not None else self.catalog
        return next(feature for feature in source["features"] if feature["feature_name"] == name)

    # Contract structure -------------------------------------------------

    def test_repository_contract_validates(self) -> None:
        summary = validate_repository_contract(ROOT)
        self.assertEqual(summary["feature_contract_version"], "0.1.2-draft")
        self.assertGreater(summary["feature_count"], 0)
        self.assertGreater(summary["materialized_name_count"], 0)

    def test_catalog_and_schema_parse_and_names_are_unique(self) -> None:
        names = [feature["feature_name"] for feature in self.catalog["features"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertLess(len(names), 100, "F00 should remain concept-disciplined, not chase feature count")

    def test_invalid_status_fails_closed(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("sig_strike_flow", catalog)["status"] = "MAGIC"
        with self.assertRaises(ContractError):
            self.validate(catalog)

    def test_invalid_layer_fails_closed(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("sig_strike_flow", catalog)["layer"] = "model1_private_layer"
        with self.assertRaises(ContractError):
            self.validate(catalog)

    def test_invalid_consumer_fails_closed(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("sig_strike_flow", catalog)["intended_model_consumers"].append("sportsbook")
        with self.assertRaises(ContractError):
            self.validate(catalog)

    # Point in time / leakage -------------------------------------------

    def test_all_concepts_declare_information_cutoff(self) -> None:
        for feature in self.catalog["features"]:
            self.assertTrue(feature["information_cutoff_rule"].strip(), feature["feature_name"])

    def test_current_fight_target_field_is_rejected_as_predictor(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("scheduled_rounds", catalog)
        feature["canonical_input_fields"]["fights"].append("winner_id")
        with self.assertRaisesRegex(ContractError, "postfight|prefight"):
            self.validate(catalog)

    def test_historical_method_field_is_allowed_only_with_strict_scope(self) -> None:
        # The real contract should pass because result/method history is explicitly historical_only.
        self.validate()
        catalog = deepcopy(self.catalog)
        feature = self.feature("finish_method_win_profile", catalog)
        feature["input_time_scope"] = "target_prefight_context"
        with self.assertRaises(ContractError):
            self.validate(catalog)

    def test_historical_target_use_without_strict_cutoff_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("finish_method_loss_profile", catalog)
        feature["information_cutoff_rule"] = "Use historical outcomes whenever convenient."
        with self.assertRaisesRegex(ContractError, "strict cutoff"):
            self.validate(catalog)

    def test_current_fight_round_stats_are_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("scheduled_rounds", catalog)
        feature["canonical_input_tables"] = ["fighter_round_stats"]
        feature["canonical_input_fields"] = {"fighter_round_stats": ["fight_id", "fighter_id", "round", "knockdowns"]}
        feature["input_time_scope"] = "target_prefight_context"
        feature["round_policy"] = "actual_rounds_only"
        with self.assertRaisesRegex(ContractError, "historical_only"):
            self.validate(catalog)

    # DATA boundary ------------------------------------------------------

    def test_unknown_canonical_table_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("sig_strike_flow", catalog)
        feature["canonical_input_tables"] = ["made_up_provider_table"]
        feature["canonical_input_fields"] = {"made_up_provider_table": ["strikes"]}
        with self.assertRaisesRegex(ContractError, "unknown canonical table"):
            self.validate(catalog)

    def test_raw_provider_path_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("sig_strike_flow", catalog)
        feature["canonical_input_tables"] = ["data/raw/provider/fights.csv"]
        feature["canonical_input_fields"] = {"data/raw/provider/fights.csv": []}
        with self.assertRaises(ContractError):
            self.validate(catalog)

    def test_canonical_field_name_is_validated(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("sig_strike_flow", catalog)["canonical_input_fields"]["fighter_round_stats"].append("provider_magic_power")
        with self.assertRaisesRegex(ContractError, "unknown canonical fields"):
            self.validate(catalog)

    # Denominators / missingness ----------------------------------------

    def test_rate_requires_explicit_denominator(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("takedown_conversion", catalog)["exposure_denominator"]["denominator"] = ""
        with self.assertRaises(ContractError):
            self.validate(catalog)

    def test_rate_zero_and_missing_denominator_policies_are_required(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("sig_strike_efficiency", catalog)["exposure_denominator"]["zero_denominator"] = ""
        with self.assertRaises(ContractError):
            self.validate(catalog)

    def test_missingness_behavior_is_required(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("control_rate", catalog)["missingness_behavior"] = ""
        with self.assertRaises(ContractError):
            self.validate(catalog)

    def test_zero_attempt_and_missing_attempt_are_distinct(self) -> None:
        self.assertIn("observed_zero", self.catalog["missingness_states"])
        self.assertIn("missing_observation", self.catalog["missingness_states"])
        feature = self.feature("takedown_conversion")
        zero_rule = feature["exposure_denominator"]["zero_denominator"].lower()
        missing_rule = feature["exposure_denominator"]["missing_denominator"].lower()
        self.assertIn("null", zero_rule)
        self.assertIn("missing", missing_rule)
        self.assertNotEqual(zero_rule, missing_rule)

    # FightMetric / round limitations -----------------------------------

    def test_round_zero_predictive_usage_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("sig_strike_flow", catalog)["exact_formula_or_definition"] += " Include round=0 summary."
        with self.assertRaisesRegex(ContractError, "round=0"):
            self.validate(catalog)

    def test_round_table_requires_actual_round_policy(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("submission_attempt_rate", catalog)["round_policy"] = "not_applicable"
        with self.assertRaisesRegex(ContractError, "actual_rounds_only"):
            self.validate(catalog)

    def test_coarse_position_cannot_claim_exact_seconds(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("position_occupancy_profile", catalog)
        feature["unit"] = "exact_seconds"
        with self.assertRaisesRegex(ContractError, "exact positional seconds"):
            self.validate(catalog)

    def test_position_proxy_requires_quantized_interval_semantics(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("position_occupancy_profile", catalog)["precision_semantics"] = "exact_canonical"
        with self.assertRaisesRegex(ContractError, "quantized positional"):
            self.validate(catalog)

    def test_control_cannot_be_ground_time_denominator(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("control_rate", catalog)
        feature["exposure_denominator"]["denominator"] = "Exact ground seconds inferred from control_sec."
        with self.assertRaisesRegex(ContractError, "ground-time"):
            self.validate(catalog)

    def test_elapsed_time_feature_fails_without_safe_source(self) -> None:
        catalog = deepcopy(self.catalog)
        self.feature("sig_strike_flow", catalog)["elapsed_exposure_source"]["contract_safe"] = False
        with self.assertRaisesRegex(ContractError, "elapsed-time exposure"):
            self.validate(catalog)

    def test_ruleset_registry_is_the_only_allowed_elapsed_source(self) -> None:
        policy = self.catalog["elapsed_exposure_policy"]
        self.assertEqual(policy["version"], 2)
        self.assertEqual(policy["allowed_sources"], ["ruleset_registry_v1"])
        self.assertEqual(policy["blocked_feature_concepts"], [])
        promoted = {
            "sig_strike_flow",
            "knockdown_rate",
            "takedown_pressure",
            "control_rate",
            "submission_attempt_rate",
            "reversal_rate",
        }
        for name in promoted:
            feature = self.feature(name)
            self.assertEqual(feature["status"], "V1_MUST", name)
            self.assertEqual(feature["elapsed_exposure_source"]["source"], "ruleset_registry_v1")
            self.assertIs(feature["elapsed_exposure_source"]["contract_safe"], True)

    def test_elapsed_source_must_be_contract_allowed(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("sig_strike_flow", catalog)
        feature["elapsed_exposure_source"]["source"] = "unreviewed_duration_source"
        with self.assertRaisesRegex(ContractError, "not allowed"):
            self.validate(catalog)

    def test_standard_300_second_round_assumption_is_rejected(self) -> None:
        catalog = deepcopy(self.catalog)
        feature = self.feature("sig_strike_flow", catalog)
        feature["status"] = "V1_MUST"
        feature["elapsed_exposure_source"] = {
            "source": "assumed_round_duration",
            "eligibility": "Assume every historical nonterminal round is 300 seconds.",
            "provenance": "Assumed five minute standard round.",
            "contract_safe": True,
        }
        catalog["elapsed_exposure_policy"]["allowed_sources"] = ["ruleset_registry_v1", "assumed_round_duration"]
        with self.assertRaisesRegex(ContractError, "standard historical round duration"):
            self.validate(catalog)

    def test_safe_attempt_denominator_remains_materializable(self) -> None:
        self.assertEqual(self.feature("takedown_conversion")["status"], "V1_MUST")
        self.assertEqual(self.feature("oa_takedown_creation")["status"], "V2_OPPONENT_ADJUSTED")
        self.assertEqual(self.feature("sim_takedown_success_probability")["status"], "SIMULATOR_COMPONENT")
        names = materialized_feature_names(self.catalog)
        self.assertTrue(any("takedown_conversion" in name for name in names))
        self.assertTrue(any("sig_strike_flow" in name for name in names))

    # Materialization naming / consumers --------------------------------

    def test_materialized_names_are_deterministic_and_unique(self) -> None:
        first = materialized_feature_names(self.catalog)
        second = materialized_feature_names(deepcopy(self.catalog))
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(set(first)))
        self.assertTrue(all("fighter_a" not in name and "fighter_b" not in name for name in first))

    def test_v1_concepts_have_consumers(self) -> None:
        for feature in self.catalog["features"]:
            if feature["status"] in {"V1_MUST", "V1_DERIVED"}:
                self.assertTrue(feature["intended_model_consumers"], feature["feature_name"])

    def test_simulator_components_are_not_baseline_model_requirements(self) -> None:
        for feature in self.catalog["features"]:
            if feature["status"] == "SIMULATOR_COMPONENT":
                consumers = set(feature["intended_model_consumers"])
                self.assertFalse(consumers & {"model0", "model1", "tree"}, feature["feature_name"])

        catalog = deepcopy(self.catalog)
        self.feature("sim_takedown_success_probability", catalog)["intended_model_consumers"].append("model1")
        with self.assertRaisesRegex(ContractError, "baseline model"):
            self.validate(catalog)

    # Repository hygiene intent -----------------------------------------

    def test_authoritative_f00_file_list_has_no_generated_feature_artifacts(self) -> None:
        forbidden_suffixes = {".csv", ".parquet", ".feather"}
        for path in AUTHORITATIVE_FILES:
            self.assertNotIn("/runs/", path)
            self.assertNotIn("features/v0/", path)
            self.assertNotIn(Path(path).suffix, forbidden_suffixes)

    def test_core_catalog_contains_no_sportsbook_features(self) -> None:
        prohibited = {term.lower() for term in self.registry["sportsbook_prohibited_terms"]}
        for feature in self.catalog["features"]:
            text = " ".join(
                [feature["feature_name"], feature["description"], feature["exact_formula_or_definition"]]
            ).lower()
            self.assertFalse(any(term in text for term in prohibited), feature["feature_name"])

    def test_external_promotion_round_stats_are_not_implied_zero(self) -> None:
        feature = self.feature("sig_strike_flow")
        self.assertEqual(feature["history_scope"], "canonical_round_stats_only")
        self.assertIn("external fights without round stats do not contribute", feature["coverage_expectation"].lower())


if __name__ == "__main__":
    unittest.main()
