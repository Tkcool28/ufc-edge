from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from ufc_edge.features.governance import (
    GovernanceError,
    artifact_feature_metadata,
    feature_id_for_name,
    load_governance,
    validate_repository_governance,
)

ROOT = Path(__file__).resolve().parents[2]


class FeatureGovernanceTests(unittest.TestCase):
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
        self.assertTrue(all(fid.endswith("_V1") and "-" not in fid for fid in ids))

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

    def test_known_feature_id_lookup_is_stable(self) -> None:
        self.assertEqual(feature_id_for_name("control_rate", ROOT), "FS_CONTROL_RATE_V1")


if __name__ == "__main__":
    unittest.main()
