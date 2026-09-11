"""Feature-governance validation and durable identity helpers.

This module is intentionally additive to F00/F01.  The feature catalog remains
semantic authority; governance files add stable identity, lifecycle, lineage,
migration, simulator, and artifact-interpretation contracts around it.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from .contract import load_feature_catalog, materialized_feature_names
from .state import active_v1_features, selected_v1_names

GOVERNANCE_FILES = (
    "features/feature_governance.json",
    "features/terminology.json",
    "features/data_requirements.json",
    "features/dependencies.json",
    "features/simulator_requirements.json",
    "features/migrations/feature_migrations.json",
)
LIFECYCLE_STATES = {
    "ACTIVE", "DEFERRED", "RESEARCH_ONLY", "SIMULATOR_REQUIRED",
    "DATA_REQUIRED", "PROXY_ONLY", "DEPRECATED", "SUPERSEDED", "UNSUPPORTED",
}
CONSUMER_PREFIX = "consumer:"
FEATURE_PREFIX = "feature:"
CANONICAL_PREFIX = "canonical:"
ELIGIBILITY_PREFIX = "eligibility:"


class GovernanceError(ValueError):
    """Raised when feature-governance contracts disagree or become ambiguous."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_json(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"cannot load {relative}: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceError(f"{relative} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_governance(root: Path | None = None) -> dict[str, Any]:
    root = root or repository_root()
    return _load_json(root, "features/feature_governance.json")


def feature_by_id(root: Path | None = None) -> dict[str, dict[str, Any]]:
    governance = load_governance(root)
    return {item["feature_id"]: item for item in governance["features"]}


def feature_id_for_name(name: str, root: Path | None = None) -> str:
    governance = load_governance(root)
    matches = [item["feature_id"] for item in governance["features"] if item["canonical_name"] == name]
    if len(matches) != 1:
        raise GovernanceError(f"expected exactly one durable feature ID for {name!r}, got {len(matches)}")
    return matches[0]


def artifact_feature_metadata(
    materialized_names: list[str],
    root: Path | None = None,
) -> dict[str, Any]:
    """Return durable identities/methodology for a persisted feature artifact."""
    root = root or repository_root()
    catalog = load_feature_catalog(root)
    governance = load_governance(root)
    by_name = {item["canonical_name"]: item for item in governance["features"]}
    prefix_to_layer = {value: key for key, value in catalog["materialization_naming"]["layer_prefixes"].items()}

    concept_names: set[str] = set()
    for column in materialized_names:
        parts = column.split("__")
        if len(parts) < 2 or parts[0] not in prefix_to_layer:
            raise GovernanceError(f"unrecognized materialized feature column: {column}")
        concept_names.add(parts[1])
    missing = sorted(concept_names - set(by_name))
    if missing:
        raise GovernanceError(f"materialized columns lack durable identities: {missing}")

    identities = [
        {
            "feature_id": by_name[name]["feature_id"],
            "canonical_name": name,
            "semantic_version": by_name[name]["semantic_version"],
            "methodology_version": by_name[name]["methodology_version"],
        }
        for name in sorted(concept_names)
    ]
    return {
        "feature_governance_version": governance["governance_version"],
        "feature_governance_sha256": sha256_file(root / "features/feature_governance.json"),
        "feature_ids": [item["feature_id"] for item in identities],
        "feature_methodologies": identities,
    }


def validate_repository_governance(root: Path | None = None) -> dict[str, Any]:
    root = root or repository_root()
    catalog = load_feature_catalog(root)
    governance = load_governance(root)
    terminology = _load_json(root, "features/terminology.json")
    requirements = _load_json(root, "features/data_requirements.json")
    dependencies = _load_json(root, "features/dependencies.json")
    simulator = _load_json(root, "features/simulator_requirements.json")
    migrations = _load_json(root, "features/migrations/feature_migrations.json")

    if governance.get("feature_contract_version") != catalog["feature_contract_version"]:
        raise GovernanceError("governance feature_contract_version does not match feature catalog")
    items = governance.get("features")
    if not isinstance(items, list) or not items:
        raise GovernanceError("feature_governance.features must be a non-empty list")

    ids = [item.get("feature_id") for item in items]
    names = [item.get("canonical_name") for item in items]
    if len(ids) != len(set(ids)):
        raise GovernanceError("durable feature IDs must be unique")
    if len(names) != len(set(names)):
        raise GovernanceError("governance canonical names must be unique")
    catalog_names = {feature["feature_name"] for feature in catalog["features"]}
    if set(names) != catalog_names:
        raise GovernanceError(
            f"governance/catalog concept mismatch: missing={sorted(catalog_names-set(names))} "
            f"extra={sorted(set(names)-catalog_names)}"
        )
    for item in items:
        if item["lifecycle_state"] not in LIFECYCLE_STATES:
            raise GovernanceError(f"invalid lifecycle state for {item['feature_id']}")
        if not item["semantic_version"] or not item["methodology_version"]:
            raise GovernanceError(f"missing semantic/methodology version for {item['feature_id']}")
        if item.get("deprecated_in") and not item.get("superseded_by") and item["lifecycle_state"] == "SUPERSEDED":
            raise GovernanceError(f"superseded feature must identify replacement: {item['feature_id']}")

    required_terms = {
        "fighter_state","matchup_interaction","context","target","predictor",
        "eligible_observation","support","exposure","elapsed_exposure","generic_control",
        "top_position","ground_control","clinch_control","positional_environment",
        "attempt_composition","rate","share","probability","prior","shrinkage",
        "opponent_adjustment","canonical","derived","proxy","research_only","deferred",
        "unsupported","materialized","consumer","historical_replay","artifact",
        "contract_version","methodology_version",
    }
    terms = terminology.get("terms", {})
    if not required_terms <= set(terms):
        raise GovernanceError(f"terminology missing required terms: {sorted(required_terms-set(terms))}")
    aliases = terminology.get("forbidden_aliases", [])
    control = next((item for item in aliases if item.get("term") == "control"), None)
    if not control or control.get("must_mean") != "generic_control" or "top_position" not in control.get("forbidden_meanings", []):
        raise GovernanceError("terminology must fail closed on generic-control/positional-control ambiguity")

    req_ids = {item["requirement_id"] for item in requirements.get("requirements", [])}
    if "DR_EXACT_POSITIONAL_DURATION_V1" not in req_ids:
        raise GovernanceError("exact positional duration requirement must remain explicit")

    valid_nodes = {FEATURE_PREFIX + item for item in ids}
    valid_nodes |= {CONSUMER_PREFIX + c for f in catalog["features"] for c in f["intended_model_consumers"]}
    for edge in dependencies.get("edges", []):
        source, target = edge.get("from", ""), edge.get("to", "")
        if source.startswith(FEATURE_PREFIX) and source not in valid_nodes:
            raise GovernanceError(f"dependency references unknown feature node: {source}")
        if target.startswith(FEATURE_PREFIX) and target not in valid_nodes:
            raise GovernanceError(f"dependency references unknown feature node: {target}")
        if target.startswith(CONSUMER_PREFIX) and target not in valid_nodes:
            raise GovernanceError(f"dependency references unknown consumer node: {target}")
    if not set(dependencies.get("unresolved_requirements", [])) <= req_ids:
        raise GovernanceError("dependency graph references unknown data requirement")

    simulator_ids = {fid for state in simulator.get("states", []) for fid in state.get("feature_ids", [])}
    if not simulator_ids <= set(ids):
        raise GovernanceError(f"simulator registry references unknown feature IDs: {sorted(simulator_ids-set(ids))}")
    blocked = {rid for state in simulator.get("states", []) for rid in state.get("blocked_by", [])}
    if not blocked <= req_ids:
        raise GovernanceError(f"simulator registry references unknown data requirements: {sorted(blocked-req_ids)}")

    migration_ids = [m["migration_id"] for m in migrations.get("migrations", [])]
    if len(migration_ids) != len(set(migration_ids)):
        raise GovernanceError("migration IDs must be unique")
    if not any(m.get("to_version") == catalog["feature_contract_version"] for m in migrations.get("migrations", [])):
        raise GovernanceError("migration history does not explain current feature contract version")

    active = active_v1_features(catalog)
    current_names = selected_v1_names(catalog)
    theoretical_active_names = [
        name for name in materialized_feature_names(catalog)
        if any(f"__{feature['feature_name']}" in name or name.endswith("__"+feature["feature_name"])
               for feature in active)
    ]
    active_layers = Counter(feature["layer"] for feature in active)
    lifecycle_counts = Counter(item["lifecycle_state"] for item in items)
    return {
        "feature_contract_version": catalog["feature_contract_version"],
        "governance_version": governance["governance_version"],
        "concept_count": len(items),
        "active_v1_concept_count": len(active),
        "f01_selected_value_count": len(current_names),
        "catalog_declared_active_variant_count": len(theoretical_active_names),
        "active_v1_layer_counts": dict(sorted(active_layers.items())),
        "lifecycle_counts": dict(sorted(lifecycle_counts.items())),
        "data_requirement_count": len(req_ids),
        "dependency_edge_count": len(dependencies.get("edges", [])),
        "simulator_state_count": len(simulator.get("states", [])),
        "migration_count": len(migrations.get("migrations", [])),
    }


def main() -> int:
    try:
        summary = validate_repository_governance()
    except GovernanceError as exc:
        print(f"FEATURE_GOVERNANCE_INVALID: {exc}")
        return 1
    print("FEATURE_GOVERNANCE_VALID")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
