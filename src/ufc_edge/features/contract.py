"""F00 feature-contract loader and fail-closed validator.

This module validates architecture metadata only. It does not read feature data,
materialize fighter states, or train models.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
from typing import Any, Iterable


class ContractError(ValueError):
    """Raised when the F00 contract is malformed or violates a safety rule."""


AUTHORITATIVE_FILES = (
    "features/FEATURE_CONTRACT.md",
    "features/feature_catalog.yaml",
    "features/feature_schema.json",
    "features/leakage_registry.yaml",
    "src/ufc_edge/features/contract.py",
    "tests/features/test_feature_contract.py",
)

NON_MATERIALIZED_STATUSES = {"RESEARCH_ONLY", "DEFERRED", "UNSUPPORTED"}
V1_STATUSES = {"V1_MUST", "V1_DERIVED"}
HISTORICAL_TABLES = {"fighter_round_stats", "fighter_round_position", "judge_round_scores"}
FEATURE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_json_compatible(path: Path) -> dict[str, Any]:
    """Load JSON-compatible YAML using only the standard library.

    F00 intentionally stores the two .yaml files as JSON-compatible YAML so the
    contract validator has no third-party parser dependency.
    """

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot parse contract document {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractError(f"contract document must be an object: {path}")
    return payload


def load_feature_catalog(root: Path | None = None) -> dict[str, Any]:
    return _load_json_compatible((root or repository_root()) / "features/feature_catalog.yaml")


def load_feature_schema(root: Path | None = None) -> dict[str, Any]:
    return _load_json_compatible((root or repository_root()) / "features/feature_schema.json")


def load_leakage_registry(root: Path | None = None) -> dict[str, Any]:
    return _load_json_compatible((root or repository_root()) / "features/leakage_registry.yaml")


def load_canonical_contract(root: Path | None = None) -> dict[str, Any]:
    return _load_json_compatible((root or repository_root()) / "schemas/canonical_data_contract_v0.json")


def _require_keys(obj: dict[str, Any], required: Iterable[str], where: str) -> None:
    missing = sorted(set(required) - set(obj))
    if missing:
        raise ContractError(f"{where} missing required keys: {', '.join(missing)}")


def _enum_values(schema: dict[str, Any], definition: str) -> set[str]:
    try:
        values = schema["$defs"][definition]["enum"]
    except KeyError as exc:
        raise ContractError(f"schema missing enum definition {definition}") from exc
    return set(values)


def _all_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)


def _canonical_fields(canonical: dict[str, Any]) -> dict[str, set[str]]:
    tables = canonical.get("tables")
    if not isinstance(tables, dict):
        raise ContractError("canonical DATA contract has no tables object")
    result: dict[str, set[str]] = {}
    for table_name, table_spec in tables.items():
        fields = table_spec.get("fields") if isinstance(table_spec, dict) else None
        if not isinstance(fields, dict):
            raise ContractError(f"canonical table {table_name} has no fields object")
        result[table_name] = set(fields)
    return result


def _validate_feature_shape(feature: dict[str, Any], schema: dict[str, Any], index: int) -> None:
    spec = schema["$defs"]["featureConcept"]
    required = spec["required"]
    allowed = set(spec["properties"])
    where = f"features[{index}]"
    _require_keys(feature, required, where)
    extras = sorted(set(feature) - allowed)
    if extras:
        raise ContractError(f"{where} has unsupported keys: {', '.join(extras)}")

    name = feature["feature_name"]
    if not isinstance(name, str) or not FEATURE_NAME_RE.fullmatch(name):
        raise ContractError(f"{where}.feature_name is invalid: {name!r}")

    bool_fields = (
        "is_rate",
        "career_variant",
        "recent_3_variant",
        "recent_5_variant",
        "ewma_variant",
        "round_specific_variant",
        "opponent_adjusted_variant",
        "matchup_interaction_variant",
    )
    for field in bool_fields:
        if type(feature[field]) is not bool:
            raise ContractError(f"{name}.{field} must be boolean")

    for field in (
        "description",
        "exact_formula_or_definition",
        "unit",
        "information_cutoff_rule",
        "minimum_sample",
        "missingness_behavior",
        "zero_semantics",
        "coverage_expectation",
        "known_limitations",
        "leakage_test",
        "provenance_requirement",
    ):
        if not isinstance(feature[field], str) or not feature[field].strip():
            raise ContractError(f"{name}.{field} must be a non-empty string")

    if not isinstance(feature["canonical_input_tables"], list):
        raise ContractError(f"{name}.canonical_input_tables must be a list")
    if not isinstance(feature["canonical_input_fields"], dict):
        raise ContractError(f"{name}.canonical_input_fields must be an object")
    if not isinstance(feature["intended_model_consumers"], list):
        raise ContractError(f"{name}.intended_model_consumers must be a list")

    denominator = feature["exposure_denominator"]
    if not isinstance(denominator, dict):
        raise ContractError(f"{name}.exposure_denominator must be an object")
    _require_keys(
        denominator,
        ("numerator", "denominator", "eligibility", "zero_denominator", "missing_denominator"),
        f"{name}.exposure_denominator",
    )
    for key, value in denominator.items():
        if not isinstance(value, str) or not value.strip():
            raise ContractError(f"{name}.exposure_denominator.{key} must be explicit")

    components = feature.get("components", [])
    if not isinstance(components, list) or len(components) != len(set(components)):
        raise ContractError(f"{name}.components must be a unique list")
    for component in components:
        if not isinstance(component, str) or not FEATURE_NAME_RE.fullmatch(component):
            raise ContractError(f"{name} has invalid component name {component!r}")


def _validate_targets(catalog: dict[str, Any], schema: dict[str, Any], canonical_fields: dict[str, set[str]]) -> None:
    spec = schema["$defs"]["targetConcept"]
    required = spec["required"]
    allowed = set(spec["properties"])
    names: set[str] = set()
    for index, target in enumerate(catalog["targets"]):
        if not isinstance(target, dict):
            raise ContractError(f"targets[{index}] must be an object")
        _require_keys(target, required, f"targets[{index}]")
        extras = sorted(set(target) - allowed)
        if extras:
            raise ContractError(f"targets[{index}] has unsupported keys: {', '.join(extras)}")
        name = target["target_name"]
        if name in names:
            raise ContractError(f"duplicate target name: {name}")
        names.add(name)
        if target.get("training_only") is not True:
            raise ContractError(f"target {name} must be training_only")
        table = target["canonical_table"]
        if table not in canonical_fields:
            raise ContractError(f"target {name} references unknown canonical table {table}")
        for field in target["canonical_fields"]:
            if field not in canonical_fields[table]:
                raise ContractError(f"target {name} references unknown canonical field {table}.{field}")


def _validate_enums(feature: dict[str, Any], schema: dict[str, Any]) -> None:
    name = feature["feature_name"]
    checks = {
        "status": "status",
        "layer": "layer",
        "input_time_scope": "inputTimeScope",
        "round_policy": "roundPolicy",
        "precision_semantics": "precisionSemantics",
        "history_scope": "historyScope",
    }
    for field, definition in checks.items():
        if feature[field] not in _enum_values(schema, definition):
            raise ContractError(f"{name}.{field} has invalid value {feature[field]!r}")

    consumers = _enum_values(schema, "consumer")
    if len(feature["intended_model_consumers"]) != len(set(feature["intended_model_consumers"])):
        raise ContractError(f"{name} has duplicate consumer tags")
    invalid = sorted(set(feature["intended_model_consumers"]) - consumers)
    if invalid:
        raise ContractError(f"{name} has invalid consumer tags: {', '.join(invalid)}")

    shrinkage_allowed = set(schema["$defs"]["featureConcept"]["properties"]["shrinkage_rule"]["enum"])
    if feature["shrinkage_rule"] not in shrinkage_allowed:
        raise ContractError(f"{name}.shrinkage_rule has invalid value {feature['shrinkage_rule']!r}")


def _validate_status_layer_and_consumers(feature: dict[str, Any]) -> None:
    name = feature["feature_name"]
    status = feature["status"]
    layer = feature["layer"]
    required_layers = {
        "V2_OPPONENT_ADJUSTED": "opponent_adjusted",
        "SIMULATOR_COMPONENT": "simulator_component",
        "RESEARCH_ONLY": "research",
        "UNSUPPORTED": "unsupported",
    }
    expected = required_layers.get(status)
    if expected and layer != expected:
        raise ContractError(f"{name}: status {status} requires layer {expected}")
    if status in V1_STATUSES and not feature["intended_model_consumers"]:
        raise ContractError(f"{name}: every V1 concept needs at least one consumer")
    if status == "SIMULATOR_COMPONENT":
        forbidden = {"model0", "model1", "tree"} & set(feature["intended_model_consumers"])
        if forbidden:
            raise ContractError(f"{name}: simulator component cannot be required by baseline model consumers: {sorted(forbidden)}")


def _validate_canonical_references(feature: dict[str, Any], canonical_fields: dict[str, set[str]]) -> None:
    name = feature["feature_name"]
    tables = feature["canonical_input_tables"]
    field_map = feature["canonical_input_fields"]
    if len(tables) != len(set(tables)):
        raise ContractError(f"{name} has duplicate canonical_input_tables")
    if set(field_map) != set(tables):
        raise ContractError(f"{name}: canonical_input_fields keys must exactly match canonical_input_tables")
    for table in tables:
        if table not in canonical_fields:
            raise ContractError(f"{name} references unknown canonical table {table}")
        fields = field_map[table]
        if not isinstance(fields, list) or len(fields) != len(set(fields)):
            raise ContractError(f"{name}: fields for {table} must be a unique list")
        invalid_fields = sorted(set(fields) - canonical_fields[table])
        if invalid_fields:
            raise ContractError(f"{name} references unknown canonical fields on {table}: {', '.join(invalid_fields)}")


def _validate_data_boundary(feature: dict[str, Any], registry: dict[str, Any]) -> None:
    name = feature["feature_name"]
    forbidden_prefixes = tuple(registry["raw_boundary"]["forbidden_path_prefixes"])
    structural_strings = list(_all_strings(feature["canonical_input_tables"])) + list(_all_strings(feature["canonical_input_fields"]))
    for value in structural_strings:
        lowered = value.lower().replace("\\", "/")
        if any(prefix in lowered for prefix in forbidden_prefixes):
            raise ContractError(f"{name} references forbidden raw/provider path {value!r}")

    searchable = " ".join(
        str(feature[key]).lower()
        for key in ("feature_name", "description", "exact_formula_or_definition")
    )
    for term in registry["sportsbook_prohibited_terms"]:
        if term.lower() in searchable:
            raise ContractError(f"{name} contains prohibited sportsbook feature term {term!r}")


def _referenced_fields(feature: dict[str, Any]) -> set[str]:
    return {
        f"{table}.{field}"
        for table, fields in feature["canonical_input_fields"].items()
        for field in fields
    }


def _validate_point_in_time(feature: dict[str, Any], registry: dict[str, Any]) -> None:
    name = feature["feature_name"]
    cutoff = feature["information_cutoff_rule"].lower()
    scope = feature["input_time_scope"]
    refs = _referenced_fields(feature)
    current_postfight = set(registry["current_target_postfight_fields"])
    leaked_labels = sorted(refs & current_postfight)
    if leaked_labels:
        historical_policy = registry["historical_postfight_field_policy"]
        if scope != historical_policy["allowed_only_when_input_time_scope"]:
            raise ContractError(f"{name} references target/postfight fields outside historical_only scope: {leaked_labels}")
        required_phrase = historical_policy["required_cutoff_phrase"].lower()
        if required_phrase not in cutoff:
            raise ContractError(f"{name} historical target-field use lacks strict cutoff phrase {required_phrase!r}")

    current_round_tables = set(registry["current_target_round_tables"])
    if current_round_tables & set(feature["canonical_input_tables"]):
        if scope != "historical_only":
            raise ContractError(f"{name} references round/postfight table outside historical_only scope")
        if "strictly before" not in cutoff and feature["status"] not in {"UNSUPPORTED"}:
            raise ContractError(f"{name} round-stat history lacks strictly-before cutoff")

    if scope == "target_prefight_context" and "fights" in feature["canonical_input_fields"]:
        allowed = set(registry["target_prefight_allowed_fight_fields"])
        used = {f"fights.{field}" for field in feature["canonical_input_fields"]["fights"]}
        invalid = sorted(used - allowed)
        if invalid:
            raise ContractError(f"{name} uses non-prefight target fight fields: {invalid}")

    if not feature["information_cutoff_rule"].strip():
        raise ContractError(f"{name} has no information cutoff rule")


def _validate_denominator_and_missingness(feature: dict[str, Any]) -> None:
    name = feature["feature_name"]
    denominator = feature["exposure_denominator"]
    if feature["is_rate"]:
        value = denominator["denominator"].strip().lower()
        if value in {"", "none", "n/a", "not_applicable", "not applicable", "unsupported"}:
            raise ContractError(f"{name} is a rate but has no usable denominator declaration")
        if not denominator["zero_denominator"].strip() or not denominator["missing_denominator"].strip():
            raise ContractError(f"{name} rate must define zero and missing denominator behavior")
    if not feature["missingness_behavior"].strip() or not feature["zero_semantics"].strip():
        raise ContractError(f"{name} must distinguish missingness and zero semantics")


def _validate_round_and_position_precision(feature: dict[str, Any]) -> None:
    name = feature["feature_name"]
    tables = set(feature["canonical_input_tables"])
    formula = feature["exact_formula_or_definition"].lower().replace(" ", "")
    if "round=0" in formula or "round==0" in formula:
        raise ContractError(f"{name} declares forbidden round=0 predictive usage")
    if HISTORICAL_TABLES & tables and feature["round_policy"] != "actual_rounds_only":
        raise ContractError(f"{name} references round-level table without actual_rounds_only policy")
    if "fighter_round_position" in tables:
        if feature["precision_semantics"] != "quantized_interval_only":
            raise ContractError(f"{name} must preserve quantized positional interval semantics")
        unit = feature["unit"].lower()
        if feature["status"] != "UNSUPPORTED" and (unit == "seconds" or "exact_seconds" in unit or "exact seconds" in unit):
            raise ContractError(f"{name} overclaims exact positional seconds from coarse buckets")

    if "fighter_round_stats" in tables:
        fields = set(feature["canonical_input_fields"].get("fighter_round_stats", []))
        if "control_sec" in fields and feature["is_rate"]:
            denom = feature["exposure_denominator"]["denominator"].lower()
            if "ground" in denom and "not ground" not in denom and feature["status"] != "UNSUPPORTED":
                raise ContractError(f"{name} improperly treats control_sec as exact ground-time denominator")


def materialized_feature_names(catalog: dict[str, Any]) -> list[str]:
    prefixes = catalog["materialization_naming"]["layer_prefixes"]
    windows = (
        ("career_variant", "career"),
        ("recent_3_variant", "last3"),
        ("recent_5_variant", "last5"),
        ("ewma_variant", "ewma_365d"),
    )
    names: list[str] = []
    for feature in catalog["features"]:
        if feature["status"] in NON_MATERIALIZED_STATUSES:
            continue
        prefix = prefixes[feature["layer"]]
        components = feature.get("components") or [None]
        enabled_windows = [label for key, label in windows if feature[key]]
        estimator = "shrunk" if feature["shrinkage_rule"] != "none" else "raw"
        for component in components:
            base = f"{prefix}__{feature['feature_name']}"
            if component:
                base += f"__{component}"
            if enabled_windows:
                for window in enabled_windows:
                    names.append(f"{base}__{window}__{estimator}")
                    if feature["round_specific_variant"]:
                        for round_band in catalog["round_bands"]:
                            names.append(f"{base}__{round_band}__{window}__{estimator}")
            else:
                names.append(base)
    return names


def validate_catalog(
    catalog: dict[str, Any],
    schema: dict[str, Any],
    canonical: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    _require_keys(catalog, schema["required"], "catalog")
    if catalog["feature_contract_version"] != "0.1.0-draft":
        raise ContractError("feature_contract_version must be 0.1.0-draft for F00")
    if catalog["data_contract_version"] != canonical.get("contract_version"):
        raise ContractError(
            f"DATA contract mismatch: catalog={catalog['data_contract_version']!r} canonical={canonical.get('contract_version')!r}"
        )
    if catalog["canonical_root"] != "data/canonical/v0/":
        raise ContractError("F00 canonical_root must remain data/canonical/v0/")

    required_missing = {"observed_positive", "observed_zero", "missing_observation", "not_applicable", "insufficient_exposure"}
    if set(catalog["missingness_states"]) != required_missing:
        raise ContractError("catalog missingness_states must preserve all five F00 semantic states")

    canonical_fields = _canonical_fields(canonical)
    features = catalog["features"]
    if not isinstance(features, list) or not features:
        raise ContractError("catalog.features must be a non-empty list")
    names: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise ContractError(f"features[{index}] must be an object")
        _validate_feature_shape(feature, schema, index)
        name = feature["feature_name"]
        if name in names:
            raise ContractError(f"duplicate feature concept name: {name}")
        names.add(name)
        _validate_enums(feature, schema)
        _validate_status_layer_and_consumers(feature)
        _validate_canonical_references(feature, canonical_fields)
        _validate_data_boundary(feature, registry)
        _validate_point_in_time(feature, registry)
        _validate_denominator_and_missingness(feature)
        _validate_round_and_position_precision(feature)

    _validate_targets(catalog, schema, canonical_fields)

    materialized = materialized_feature_names(catalog)
    duplicates = sorted(name for name, count in Counter(materialized).items() if count > 1)
    if duplicates:
        raise ContractError(f"duplicate generated materialized feature names: {duplicates[:10]}")

    status_counts = Counter(feature["status"] for feature in features)
    layer_counts = Counter(feature["layer"] for feature in features)
    consumer_counts = Counter(
        consumer
        for feature in features
        for consumer in feature["intended_model_consumers"]
    )
    return {
        "feature_contract_version": catalog["feature_contract_version"],
        "feature_count": len(features),
        "target_count": len(catalog["targets"]),
        "materialized_name_count": len(materialized),
        "status_counts": dict(sorted(status_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "consumer_counts": dict(sorted(consumer_counts.items())),
    }


def validate_repository_contract(root: Path | None = None) -> dict[str, Any]:
    root = root or repository_root()
    return validate_catalog(
        load_feature_catalog(root),
        load_feature_schema(root),
        load_canonical_contract(root),
        load_leakage_registry(root),
    )


def main() -> int:
    try:
        summary = validate_repository_contract()
    except ContractError as exc:
        print(f"F00_FEATURE_CONTRACT_INVALID: {exc}")
        return 1
    print("F00_FEATURE_CONTRACT_VALID")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
