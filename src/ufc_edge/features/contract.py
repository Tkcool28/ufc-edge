"""F00 feature-contract loader and fail-closed validator.

This module validates architecture metadata only. It does not read feature data,
materialize fighter states, train models, or access provider raw data.
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
    ".github/workflows/f00-feature-contract.yml",
)

NON_MATERIALIZED_STATUSES = {"RESEARCH_ONLY", "DEFERRED", "UNSUPPORTED"}
V1_STATUSES = {"V1_MUST", "V1_DERIVED"}
ROUND_TABLES = {"fighter_round_stats", "fighter_round_position", "judge_round_scores"}
ROUND_TARGET_ONLY_STATUSES = {"SIMULATOR_COMPONENT", "UNSUPPORTED"}
FEATURE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_object(path: Path) -> dict[str, Any]:
    """Load JSON-compatible YAML/JSON with only the standard library."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot parse contract document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"contract document must be an object: {path}")
    return value


def load_feature_catalog(root: Path | None = None) -> dict[str, Any]:
    return _load_object((root or repository_root()) / "features/feature_catalog.yaml")


def load_feature_schema(root: Path | None = None) -> dict[str, Any]:
    return _load_object((root or repository_root()) / "features/feature_schema.json")


def load_leakage_registry(root: Path | None = None) -> dict[str, Any]:
    return _load_object((root or repository_root()) / "features/leakage_registry.yaml")


def load_canonical_contract(root: Path | None = None) -> dict[str, Any]:
    return _load_object((root or repository_root()) / "schemas/canonical_data_contract_v0.json")


def _require_keys(obj: dict[str, Any], keys: Iterable[str], where: str) -> None:
    missing = sorted(set(keys) - set(obj))
    if missing:
        raise ContractError(f"{where} missing required keys: {', '.join(missing)}")


def _enum(schema: dict[str, Any], name: str) -> set[str]:
    try:
        return set(schema["$defs"][name]["enum"])
    except KeyError as exc:
        raise ContractError(f"schema missing enum definition {name}") from exc


def _canonical_fields(canonical: dict[str, Any]) -> dict[str, set[str]]:
    tables = canonical.get("tables")
    if not isinstance(tables, dict):
        raise ContractError("canonical DATA contract has no tables object")
    result: dict[str, set[str]] = {}
    for table, spec in tables.items():
        fields = spec.get("fields") if isinstance(spec, dict) else None
        if not isinstance(fields, dict):
            raise ContractError(f"canonical table {table} has no fields object")
        result[table] = set(fields)
    return result


def _all_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _all_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _all_strings(item)


def _normalized_cutoff(text: str) -> str:
    # Accept equivalent contract prose such as strictly-before and strictly pre-H
    # without weakening the requirement that historical evidence be strictly prior.
    return re.sub(r"\s+", " ", text.lower().replace("-", " ")).strip()


def _declares_strict_prior(text: str) -> bool:
    normalized = _normalized_cutoff(text)
    return "strictly before" in normalized or "strictly pre " in normalized


def _referenced_fields(feature: dict[str, Any]) -> set[str]:
    return {
        f"{table}.{field}"
        for table, fields in feature["canonical_input_fields"].items()
        for field in fields
    }


def _validate_shape(feature: dict[str, Any], schema: dict[str, Any], index: int) -> None:
    spec = schema["$defs"]["featureConcept"]
    name = feature.get("feature_name", f"features[{index}]")
    _require_keys(feature, spec["required"], f"features[{index}]")
    extras = sorted(set(feature) - set(spec["properties"]))
    if extras:
        raise ContractError(f"{name} has unsupported keys: {', '.join(extras)}")
    if not isinstance(feature["feature_name"], str) or not FEATURE_NAME_RE.fullmatch(feature["feature_name"]):
        raise ContractError(f"invalid feature concept name: {feature['feature_name']!r}")

    for field in (
        "is_rate",
        "career_variant",
        "recent_3_variant",
        "recent_5_variant",
        "ewma_variant",
        "round_specific_variant",
        "opponent_adjusted_variant",
        "matchup_interaction_variant",
    ):
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
            raise ContractError(f"{name} has invalid component {component!r}")


def _validate_enums_and_consumers(feature: dict[str, Any], schema: dict[str, Any]) -> None:
    name = feature["feature_name"]
    definitions = {
        "status": "status",
        "layer": "layer",
        "input_time_scope": "inputTimeScope",
        "history_scope": "historyScope",
        "round_policy": "roundPolicy",
        "precision_semantics": "precisionSemantics",
    }
    for field, definition in definitions.items():
        if feature[field] not in _enum(schema, definition):
            raise ContractError(f"{name}.{field} has invalid value {feature[field]!r}")

    consumers = feature["intended_model_consumers"]
    if len(consumers) != len(set(consumers)):
        raise ContractError(f"{name} has duplicate consumer tags")
    invalid = sorted(set(consumers) - _enum(schema, "consumer"))
    if invalid:
        raise ContractError(f"{name} has invalid consumer tags: {', '.join(invalid)}")

    shrinkage_values = set(schema["$defs"]["featureConcept"]["properties"]["shrinkage_rule"]["enum"])
    if feature["shrinkage_rule"] not in shrinkage_values:
        raise ContractError(f"{name}.shrinkage_rule has invalid value {feature['shrinkage_rule']!r}")

    required_layer = {
        "V2_OPPONENT_ADJUSTED": "opponent_adjusted",
        "SIMULATOR_COMPONENT": "simulator_component",
        "RESEARCH_ONLY": "research",
        "UNSUPPORTED": "unsupported",
    }.get(feature["status"])
    if required_layer and feature["layer"] != required_layer:
        raise ContractError(f"{name}: status {feature['status']} requires layer {required_layer}")
    if feature["status"] in V1_STATUSES and not consumers:
        raise ContractError(f"{name}: every V1 concept needs at least one intended consumer")
    if feature["status"] == "SIMULATOR_COMPONENT":
        baseline = {"model0", "model1", "tree"} & set(consumers)
        if baseline:
            raise ContractError(f"{name}: simulator component cannot be required by baseline model consumers: {sorted(baseline)}")


def _validate_data_boundary(feature: dict[str, Any], registry: dict[str, Any]) -> None:
    name = feature["feature_name"]
    forbidden_prefixes = tuple(registry["raw_boundary"]["forbidden_path_prefixes"])
    structural = list(_all_strings(feature["canonical_input_tables"])) + list(_all_strings(feature["canonical_input_fields"]))
    for value in structural:
        normalized = value.lower().replace("\\", "/")
        if any(prefix in normalized for prefix in forbidden_prefixes):
            raise ContractError(f"{name} references forbidden raw/provider path {value!r}")

    searchable = " ".join(
        str(feature[field]).lower()
        for field in ("feature_name", "description", "exact_formula_or_definition")
    )
    for term in registry["sportsbook_prohibited_terms"]:
        if term.lower() in searchable:
            raise ContractError(f"{name} contains prohibited sportsbook feature term {term!r}")


def _validate_canonical_references(feature: dict[str, Any], canonical_fields: dict[str, set[str]]) -> None:
    name = feature["feature_name"]
    tables = feature["canonical_input_tables"]
    field_map = feature["canonical_input_fields"]
    if len(tables) != len(set(tables)):
        raise ContractError(f"{name} has duplicate canonical_input_tables")
    if set(tables) != set(field_map):
        raise ContractError(f"{name}: canonical_input_fields keys must exactly match canonical_input_tables")
    for table in tables:
        if table not in canonical_fields:
            raise ContractError(f"{name} references unknown canonical table {table}")
        fields = field_map[table]
        if not isinstance(fields, list) or len(fields) != len(set(fields)):
            raise ContractError(f"{name}: fields for {table} must be a unique list")
        invalid = sorted(set(fields) - canonical_fields[table])
        if invalid:
            raise ContractError(f"{name} references unknown canonical fields on {table}: {', '.join(invalid)}")


def _validate_point_in_time(feature: dict[str, Any], registry: dict[str, Any]) -> None:
    name = feature["feature_name"]
    scope = feature["input_time_scope"]
    cutoff = feature["information_cutoff_rule"]
    refs = _referenced_fields(feature)

    postfight = set(registry["current_target_postfight_fields"])
    leaked = sorted(refs & postfight)
    if leaked:
        policy = registry["historical_postfight_field_policy"]
        if scope != policy["allowed_only_when_input_time_scope"]:
            raise ContractError(f"{name} references target/postfight fields outside historical_only scope: {leaked}")
        if not _declares_strict_prior(cutoff):
            raise ContractError(f"{name} historical target-field use lacks strict cutoff semantics")

    round_tables = set(registry["current_target_round_tables"]) & set(feature["canonical_input_tables"])
    if round_tables:
        if scope != "historical_only":
            raise ContractError(f"{name} references round/postfight table outside historical_only scope")
        # Simulator components declare realized historical round observations as
        # component-training labels, not as pre-fight predictors. Their consumer
        # restrictions and leakage tests enforce that boundary separately.
        if feature["status"] not in ROUND_TARGET_ONLY_STATUSES and not (feature["status"] == "DEFERRED" and feature["layer"] == "simulator_component") and not _declares_strict_prior(cutoff):
            raise ContractError(f"{name} round-stat history lacks strictly-before cutoff semantics")

    if scope == "target_prefight_context" and "fights" in feature["canonical_input_fields"]:
        allowed = set(registry["target_prefight_allowed_fight_fields"])
        used = {f"fights.{field}" for field in feature["canonical_input_fields"]["fights"]}
        invalid = sorted(used - allowed)
        if invalid:
            raise ContractError(f"{name} uses non-prefight target fight fields: {invalid}")


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



def _uses_elapsed_time_exposure(feature: dict[str, Any]) -> bool:
    """Detect fight/round elapsed-time denominators generically."""
    denominator = feature["exposure_denominator"]["denominator"].lower().replace("-", " ")
    unit = feature["unit"].lower().replace("-", "_")
    elapsed_denominator = (
        ("elapsed" in denominator and any(token in denominator for token in ("time", "minute", "second", "fight", "round")))
        or "eligible minute" in denominator
        or "compatible minute" in denominator
        or "fight minute" in denominator
        or "fight second" in denominator
        or "round exposure" in denominator
    )
    time_unit = any(token in unit for token in ("per_minute", "per_15_minutes", "share_of_elapsed", "per_time_interval", "per_elapsed"))
    return elapsed_denominator or time_unit


def _validate_elapsed_exposure_policy(catalog: dict[str, Any], features: list[dict[str, Any]]) -> None:
    policy = catalog.get("elapsed_exposure_policy")
    if not isinstance(policy, dict):
        raise ContractError("catalog must declare elapsed_exposure_policy")
    _require_keys(policy, ("version", "canonical_v0_status", "allowed_sources", "blocked_feature_concepts", "forbidden_inferences", "materializable_requirement", "promotion_requirement"), "elapsed_exposure_policy")
    if policy["version"] != 1:
        raise ContractError("elapsed_exposure_policy.version must be 1")
    if policy["canonical_v0_status"] != "no_general_safe_elapsed_round_or_fight_exposure_source":
        raise ContractError("canonical v0 elapsed-exposure status cannot be weakened silently")
    allowed_sources = policy["allowed_sources"]
    blocked = policy["blocked_feature_concepts"]
    if not isinstance(allowed_sources, list) or len(allowed_sources) != len(set(allowed_sources)):
        raise ContractError("elapsed_exposure_policy.allowed_sources must be a unique list")
    if not isinstance(blocked, list) or len(blocked) != len(set(blocked)):
        raise ContractError("elapsed_exposure_policy.blocked_feature_concepts must be a unique list")
    by_name = {feature["feature_name"]: feature for feature in features}
    missing = sorted(set(blocked) - set(by_name))
    if missing:
        raise ContractError(f"elapsed-exposure policy references unknown concepts: {missing}")
    for name in blocked:
        if by_name[name]["status"] != "DEFERRED":
            raise ContractError(f"{name} is blocked by canonical-v0 elapsed exposure and must remain DEFERRED")
    for feature in features:
        name = feature["feature_name"]
        source = feature.get("elapsed_exposure_source")
        if source is not None:
            if not isinstance(source, dict):
                raise ContractError(f"{name}.elapsed_exposure_source must be an object")
            _require_keys(source, ("source", "eligibility", "provenance", "contract_safe"), f"{name}.elapsed_exposure_source")
            if type(source["contract_safe"]) is not bool:
                raise ContractError(f"{name}.elapsed_exposure_source.contract_safe must be boolean")
            for field in ("source", "eligibility", "provenance"):
                if not isinstance(source[field], str) or not source[field].strip():
                    raise ContractError(f"{name}.elapsed_exposure_source.{field} must be explicit")
            if source["contract_safe"] and source["source"] not in allowed_sources:
                raise ContractError(f"{name} claims an elapsed-exposure source not allowed by the contract")
        if _uses_elapsed_time_exposure(feature) and feature["status"] not in NON_MATERIALIZED_STATUSES:
            if source is None or source["contract_safe"] is not True or source["source"] not in allowed_sources:
                raise ContractError(f"{name} uses elapsed-time exposure without a contract-safe allowed source/eligibility")
        if source is not None:
            combined = " ".join(str(source[key]).lower() for key in ("source", "eligibility", "provenance")) + " " + feature["exact_formula_or_definition"].lower()
            if ("300 second" in combined or "five minute" in combined or "5 minute" in combined) and "assum" in combined:
                raise ContractError(f"{name} attempts to assume a standard historical round duration")

def _validate_round_and_position_precision(feature: dict[str, Any]) -> None:
    name = feature["feature_name"]
    tables = set(feature["canonical_input_tables"])
    formula = feature["exact_formula_or_definition"].lower().replace(" ", "")
    if "round=0" in formula or "round==0" in formula:
        raise ContractError(f"{name} declares forbidden round=0 predictive usage")
    if ROUND_TABLES & tables and feature["round_policy"] != "actual_rounds_only":
        raise ContractError(f"{name} references round-level table without actual_rounds_only policy")

    if "fighter_round_position" in tables:
        if feature["precision_semantics"] != "quantized_interval_only":
            raise ContractError(f"{name} must preserve quantized positional interval semantics")
        unit = feature["unit"].lower()
        if feature["status"] != "UNSUPPORTED" and (
            unit == "seconds" or "exact_seconds" in unit or "exact seconds" in unit
        ):
            raise ContractError(f"{name} overclaims exact positional seconds from coarse buckets")

    fields = set(feature["canonical_input_fields"].get("fighter_round_stats", []))
    if "control_sec" in fields and feature["is_rate"] and feature["status"] != "UNSUPPORTED":
        denominator = feature["exposure_denominator"]["denominator"].lower()
        if "ground" in denominator and "not ground" not in denominator:
            raise ContractError(f"{name} improperly treats control_sec as exact ground-time denominator")


def _validate_targets(
    catalog: dict[str, Any],
    schema: dict[str, Any],
    canonical_fields: dict[str, set[str]],
) -> None:
    spec = schema["$defs"]["targetConcept"]
    names: set[str] = set()
    for index, target in enumerate(catalog["targets"]):
        if not isinstance(target, dict):
            raise ContractError(f"targets[{index}] must be an object")
        _require_keys(target, spec["required"], f"targets[{index}]")
        extras = sorted(set(target) - set(spec["properties"]))
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
        invalid = sorted(set(target["canonical_fields"]) - canonical_fields[table])
        if invalid:
            raise ContractError(f"target {name} references unknown canonical fields on {table}: {', '.join(invalid)}")


def materialized_feature_names(catalog: dict[str, Any]) -> list[str]:
    prefixes = catalog["materialization_naming"]["layer_prefixes"]
    window_flags = (
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
        windows = [label for flag, label in window_flags if feature[flag]]
        estimator = "shrunk" if feature["shrinkage_rule"] != "none" else "raw"
        for component in components:
            base = f"{prefix}__{feature['feature_name']}"
            if component:
                base += f"__{component}"
            if not windows:
                names.append(base)
                continue
            for window in windows:
                names.append(f"{base}__{window}__{estimator}")
                if feature["round_specific_variant"]:
                    for band in catalog["round_bands"]:
                        names.append(f"{base}__{band}__{window}__{estimator}")
    return names


def validate_catalog(
    catalog: dict[str, Any],
    schema: dict[str, Any],
    canonical: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    _require_keys(catalog, schema["required"], "catalog")
    if catalog["feature_contract_version"] != "0.1.1-draft":
        raise ContractError("feature_contract_version must be 0.1.1-draft for remediated F00")
    if catalog["data_contract_version"] != canonical.get("contract_version"):
        raise ContractError("catalog DATA contract version does not match frozen canonical contract")
    if catalog["canonical_root"] != "data/canonical/v0/":
        raise ContractError("F00 canonical_root must remain data/canonical/v0/")

    required_missingness = {
        "observed_positive",
        "observed_zero",
        "missing_observation",
        "not_applicable",
        "insufficient_exposure",
    }
    if set(catalog["missingness_states"]) != required_missingness:
        raise ContractError("catalog must preserve all five F00 missingness semantic states")

    canonical_fields = _canonical_fields(canonical)
    features = catalog["features"]
    if not isinstance(features, list) or not features:
        raise ContractError("catalog.features must be a non-empty list")

    names: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise ContractError(f"features[{index}] must be an object")
        _validate_shape(feature, schema, index)
        name = feature["feature_name"]
        if name in names:
            raise ContractError(f"duplicate feature concept name: {name}")
        names.add(name)
        _validate_enums_and_consumers(feature, schema)
        _validate_data_boundary(feature, registry)
        _validate_canonical_references(feature, canonical_fields)
        _validate_point_in_time(feature, registry)
        _validate_denominator_and_missingness(feature)
        _validate_round_and_position_precision(feature)

    _validate_elapsed_exposure_policy(catalog, features)
    _validate_targets(catalog, schema, canonical_fields)

    materialized = materialized_feature_names(catalog)
    duplicate_columns = sorted(name for name, count in Counter(materialized).items() if count > 1)
    if duplicate_columns:
        raise ContractError(f"duplicate generated materialized feature names: {duplicate_columns[:10]}")

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
