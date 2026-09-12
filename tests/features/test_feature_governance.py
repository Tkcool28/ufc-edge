from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from ufc_edge.features.contract import load_feature_catalog
from ufc_edge.features.governance import (
    GovernanceError,
    artifact_feature_metadata,
    feature_id_for_name,
    feature_id_for_name_or_alias,
    load_governance,
    validate_repository_governance,
)

ROOT = Path(__file__).resolve().parents[2]


class FeatureGovernanceTests(unittest.TestCase):
    def _renamed_control_fixture(
        self,
        current_name: str,
        renamed_from: list[str],
    ) -> tuple[dict, dict]:
        governance = deepcopy(load_governance(ROOT))
        catalog = deepcopy(load_feature_catalog(ROOT))
        governance_item = next(
            x for x in governance["features"] if x["canonical_name"] == "control_rate"
        )
        catalog_item = next(
            x for x in catalog["features"] if x["feature_name"] == "control_rate"
        )
        governance_item["canonical_name"] = current_name
        governance_item["renamed_from"] = renamed_from
        catalog_item["feature_name"] = current_name
        return governance, catalog

    def _validate_fixture(self, governance: dict, catalog: dict) -> dict:
        with (
            patch("ufc_edge.features.governance.load_governance", return_value=governance),
            patch("ufc_edge.features.governance.load_feature_catalog", return_value=catalog),
        ):
            return validate_repository_governance(ROOT)

    def test_repository_governance_validates(self) -> None:
        summary = validate_repository_governance(ROOT)
        self.assertEqual(summary["feature_contract_version"], "0.1.2-draft")
        self.assertEqual(summary["governance_version"], "1.0.0")
        self.assertEqual(summary["concept_count"], 60)
        self.assertEqual(summary["active_v1_concept_count"], 24)
        self.assertEqual(summary["f01_selected_value_count"], 104)

    def test_every_catalog_concept_has_stable_human_readable_id(self) -> None:
        governance = load_governance(ROOT)
        ids = [item["feature_id"] for item in governance["features"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all("-" not in fid for fid in ids))

    def test_durable_ids_do_not_duplicate_layer_namespace(self) -> None:
        governance = load_governance(ROOT)
        prefixes = set(governance["identity_policy"]["layer_prefixes"].values())
        for item in governance["features"]:
            for prefix in prefixes:
                self.assertNotIn(f"{prefix}_{prefix}_", item["feature_id"])

    def test_known_normalized_feature_ids(self) -> None:
        self.assertEqual(feature_id_for_name("control_rate", ROOT), "FS_CONTROL_RATE_V1")
        self.assertEqual(feature_id_for_name("oa_control_creation", ROOT), "OA_CONTROL_CREATION_V1")
        self.assertEqual(
            feature_id_for_name("sim_takedown_success_probability", ROOT),
            "SIM_TAKEDOWN_SUCCESS_PROBABILITY_V1",
        )

    def test_semantic_major_suffix_matches_semantic_version(self) -> None:
        governance = load_governance(ROOT)
        for item in governance["features"]:
            major = int(item["semantic_version"].split(".", 1)[0])
            self.assertTrue(item["feature_id"].endswith(f"_V{major}"), item["feature_id"])

    def test_duplicate_namespace_fixture_is_rejected(self) -> None:
        governance = deepcopy(load_governance(ROOT))
        item = next(x for x in governance["features"] if x["canonical_name"] == "oa_control_creation")
        item["feature_id"] = "OA_" + item["feature_id"]
        with patch("ufc_edge.features.governance.load_governance", return_value=governance):
            with self.assertRaisesRegex(GovernanceError, "duplicated|convention"):
                validate_repository_governance(ROOT)

    def test_semantic_major_mismatch_fixture_is_rejected(self) -> None:
        governance = deepcopy(load_governance(ROOT))
        item = next(x for x in governance["features"] if x["canonical_name"] == "control_rate")
        item["semantic_version"] = "2.0.0"
        with patch("ufc_edge.features.governance.load_governance", return_value=governance):
            with self.assertRaisesRegex(GovernanceError, "semantic-major|convention"):
                validate_repository_governance(ROOT)

    def test_unrenamed_feature_must_match_clean_initial_id(self) -> None:
        governance = deepcopy(load_governance(ROOT))
        catalog = deepcopy(load_feature_catalog(ROOT))
        item = next(x for x in governance["features"] if x["canonical_name"] == "control_rate")
        self.assertEqual(item["renamed_from"], [])
        item["feature_id"] = "FS_SOMETHING_ELSE_V1"
        with self.assertRaisesRegex(GovernanceError, "initial durable identity convention"):
            self._validate_fixture(governance, catalog)

    def test_pure_rename_preserves_durable_id(self) -> None:
        governance, catalog = self._renamed_control_fixture(
            "generic_control_rate",
            ["control_rate"],
        )
        summary = self._validate_fixture(governance, catalog)
        item = next(x for x in governance["features"] if x["canonical_name"] == "generic_control_rate")
        self.assertEqual(item["feature_id"], "FS_CONTROL_RATE_V1")
        self.assertEqual(summary["concept_count"], 60)

    def test_multiple_pure_renames_preserve_original_id(self) -> None:
        governance, catalog = self._renamed_control_fixture(
            "generic_control_share",
            ["control_rate", "generic_control_rate"],
        )
        summary = self._validate_fixture(governance, catalog)
        item = next(x for x in governance["features"] if x["canonical_name"] == "generic_control_share")
        self.assertEqual(item["feature_id"], "FS_CONTROL_RATE_V1")
        self.assertEqual(summary["f01_selected_value_count"], 104)

    def test_undocumented_rename_fails(self) -> None:
        governance, catalog = self._renamed_control_fixture("generic_control_rate", [])
        with self.assertRaisesRegex(GovernanceError, "initial durable identity convention"):
            self._validate_fixture(governance, catalog)

    def test_current_name_cannot_appear_in_renamed_from(self) -> None:
        governance, catalog = self._renamed_control_fixture(
            "generic_control_rate",
            ["control_rate", "generic_control_rate"],
        )
        with self.assertRaisesRegex(GovernanceError, "current canonical_name"):
            self._validate_fixture(governance, catalog)

    def test_duplicate_historical_alias_fails(self) -> None:
        governance, catalog = self._renamed_control_fixture(
            "generic_control_rate",
            ["control_rate", "control_rate"],
        )
        with self.assertRaisesRegex(GovernanceError, "duplicate historical"):
            self._validate_fixture(governance, catalog)

    def test_alias_collision_with_current_name_fails(self) -> None:
        governance = deepcopy(load_governance(ROOT))
        catalog = deepcopy(load_feature_catalog(ROOT))
        item = next(x for x in governance["features"] if x["canonical_name"] == "sig_strike_flow")
        item["renamed_from"] = ["control_rate"]
        with self.assertRaisesRegex(GovernanceError, "ambiguous"):
            self._validate_fixture(governance, catalog)

    def test_historical_alias_collision_across_features_fails(self) -> None:
        governance = deepcopy(load_governance(ROOT))
        catalog = deepcopy(load_feature_catalog(ROOT))
        first = next(x for x in governance["features"] if x["canonical_name"] == "sig_strike_flow")
        second = next(x for x in governance["features"] if x["canonical_name"] == "knockdown_rate")
        first["renamed_from"] = ["old_shared_metric"]
        second["renamed_from"] = ["old_shared_metric"]
        with self.assertRaisesRegex(GovernanceError, "ambiguous"):
            self._validate_fixture(governance, catalog)

    def test_name_or_alias_resolution_is_unique(self) -> None:
        governance, _ = self._renamed_control_fixture(
            "generic_control_rate",
            ["control_rate"],
        )
        with patch("ufc_edge.features.governance.load_governance", return_value=governance):
            self.assertEqual(
                feature_id_for_name_or_alias("control_rate", ROOT),
                "FS_CONTROL_RATE_V1",
            )
            self.assertEqual(
                feature_id_for_name_or_alias("generic_control_rate", ROOT),
                "FS_CONTROL_RATE_V1",
            )
            with self.assertRaises(GovernanceError):
                feature_id_for_name_or_alias("not_a_feature_name", ROOT)

        ambiguous = deepcopy(governance)
        other = next(x for x in ambiguous["features"] if x["canonical_name"] == "sig_strike_flow")
        other["renamed_from"] = ["control_rate"]
        with patch("ufc_edge.features.governance.load_governance", return_value=ambiguous):
            with self.assertRaisesRegex(GovernanceError, "got 2"):
                feature_id_for_name_or_alias("control_rate", ROOT)

    def test_layer_check_remains_enforced(self) -> None:
        governance = deepcopy(load_governance(ROOT))
        catalog = deepcopy(load_feature_catalog(ROOT))
        item = next(x for x in catalog["features"] if x["feature_name"] == "oa_control_creation")
        item["layer"] = "fighter_state"
        with self.assertRaisesRegex(GovernanceError, "uses layer prefix"):
            self._validate_fixture(governance, catalog)

    def test_semantic_change_cannot_be_documented_as_pure_rename_policy(self) -> None:
        doc = (ROOT / "features/FEATURE_GOVERNANCE.md").read_text(encoding="utf-8")
        self.assertIn(
            "A semantic change cannot be smuggled through `renamed_from`",
            doc,
        )
        self.assertIn(
            "`control_rate` to an exact top-position share",
            doc,
        )

    def test_rename_policy_does_not_require_new_identity(self) -> None:
        governance = load_governance(ROOT)
        policy = governance["identity_policy"]
        self.assertIs(policy["stable_under_rename"], True)
        self.assertIs(policy["semantic_change_requires_new_id"], True)
        self.assertIs(policy["never_recycled"], True)

    def test_control_identity_is_generic_not_positional(self) -> None:
        governance = load_governance(ROOT)
        control = next(x for x in governance["features"] if x["canonical_name"] == "control_rate")
        self.assertIn("Generic canonical control", control["notes"])
        terminology = json.loads((ROOT / "features/terminology.json").read_text())
        alias = next(x for x in terminology["forbidden_aliases"] if x["term"] == "control")
        self.assertEqual(alias["must_mean"], "generic_control")
        self.assertIn("top_position", alias["forbidden_meanings"])

    def test_exact_positional_duration_remains_data_required(self) -> None:
        req = json.loads((ROOT / "features/data_requirements.json").read_text())
        item = next(x for x in req["requirements"] if x["requirement_id"] == "DR_EXACT_POSITIONAL_DURATION_V1")
        self.assertEqual(item["status"], "DATA_REQUIRED")
        self.assertIn("generic control_sec as exact positional duration", item["forbidden_substitutions"])

    def test_simulator_ground_state_is_blocked_not_fabricated(self) -> None:
        sim = json.loads((ROOT / "features/simulator_requirements.json").read_text())
        ground = next(x for x in sim["states"] if x["state"] == "ground/top-control environment")
        self.assertEqual(ground["availability"], "DATA_REQUIRED")
        self.assertIn("DR_EXACT_POSITIONAL_DURATION_V1", ground["blocked_by"])

    def test_artifact_metadata_resolves_ids_and_methodologies(self) -> None:
        payload = artifact_feature_metadata(
            ["fs__control_rate__created_share__career__shrunk", "ctx__scheduled_rounds"],
            ROOT,
        )
        self.assertEqual(len(payload["feature_ids"]), 2)
        self.assertTrue(all(x["methodology_version"] == "1.0.0" for x in payload["feature_methodologies"]))

    def test_unknown_materialized_column_fails_closed(self) -> None:
        with self.assertRaises(GovernanceError):
            artifact_feature_metadata(["madeup__thing"], ROOT)

    def test_dependency_and_simulator_references_resolve(self) -> None:
        summary = validate_repository_governance(ROOT)
        self.assertGreater(summary["dependency_edge_count"], 0)
        self.assertEqual(summary["simulator_state_count"], 8)

    def test_generated_governance_reference_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/features/generate_feature_reference.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_authoritative_files_contain_no_duplicate_layer_prefixes(self) -> None:
        governance = load_governance(ROOT)
        prefixes = set(governance["identity_policy"]["layer_prefixes"].values())
        current_files = (
            "features/feature_governance.json",
            "features/dependencies.json",
            "features/simulator_requirements.json",
            "features/data_requirements.json",
            "features/migrations/feature_migrations.json",
            "features/feature_inventory.json",
            "features/FEATURE_REFERENCE.md",
            "features/FEATURE_GOVERNANCE.md",
            "features/README.md",
            "features/repository_inventory.json",
            "features/FEATURE_REPOSITORY_INVENTORY.md",
            "src/ufc_edge/features/governance.py",
            "src/ufc_edge/features/materializer.py",
            "tools/features/generate_feature_reference.py",
        )
        for relative in current_files:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for prefix in prefixes:
                self.assertNotIn(f"{prefix}_{prefix}_", text, relative)


if __name__ == "__main__":
    unittest.main()
