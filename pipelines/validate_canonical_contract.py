#!/usr/bin/env python3
"""Fail-closed structural validation for the UFC Edge canonical data contract.

This validates the contract itself before any provider adapter is allowed to target it.
It intentionally contains no feature formulas.
"""
from __future__ import annotations

import json
from pathlib import Path

CONTRACT = Path("schemas/canonical_data_contract_v0.json")
ALLOWED_TYPES = {"string", "integer", "number", "boolean", "date", "enum"}
ALLOWED_UNITS = {"cm", "lb", "sec", "percent"}

REQUIRED_CORE = {
    "fighters": {"fighter_id", "canonical_name", "dob", "height_cm", "reach_cm", "stance"},
    "events": {"event_id", "promotion", "event_name", "event_date", "location"},
    "fights": {
        "fight_id", "event_id", "fighter_a_id", "fighter_b_id", "winner_id", "result", "method",
        "finish_round", "finish_time_sec", "scheduled_rounds", "weight_class", "title_bout", "promotion",
    },
    "fighter_round_stats": {
        "fight_id", "fighter_id", "opponent_id", "round", "knockdowns", "control_sec", "reversals",
        "submission_attempts", "sig_strikes_landed", "sig_strikes_attempted", "total_strikes_landed",
        "total_strikes_attempted", "takedowns_landed", "takedowns_attempted", "head_landed",
        "head_attempted", "body_landed", "body_attempted", "leg_landed", "leg_attempted",
        "distance_landed", "distance_attempted", "clinch_landed", "clinch_attempted", "ground_landed",
        "ground_attempted",
    },
}


def fail(message: str) -> None:
    raise SystemExit(f"CONTRACT_INVALID: {message}")


def main() -> int:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tables = payload.get("tables")
    if not isinstance(tables, dict) or not tables:
        fail("tables must be a non-empty object")

    rules = payload.get("global_rules") or {}
    if rules.get("missing_is_not_zero") is not True:
        fail("missing_is_not_zero must remain true")
    if rules.get("display_name_only_identity_is_trusted") is not False:
        fail("display-name-only identity must not be trusted")
    if rules.get("round_zero_is_actual_round") is not False:
        fail("round zero must not be treated as an actual round")

    field_count = 0
    for table_name, table in tables.items():
        if not isinstance(table, dict):
            fail(f"{table_name}: table definition must be an object")
        fields = table.get("fields")
        pk = table.get("primary_key")
        if not isinstance(fields, dict) or not fields:
            fail(f"{table_name}: fields missing")
        if not isinstance(pk, list) or not pk:
            fail(f"{table_name}: primary_key missing")
        if len(pk) != len(set(pk)):
            fail(f"{table_name}: primary_key contains duplicates")

        for key in pk:
            if key not in fields:
                fail(f"{table_name}: primary key field {key!r} is undefined")
            if fields[key].get("nullable") is not False:
                fail(f"{table_name}: primary key field {key!r} must be non-nullable")

        for field_name, spec in fields.items():
            field_count += 1
            if not isinstance(spec, dict):
                fail(f"{table_name}.{field_name}: field spec must be an object")
            field_type = spec.get("type")
            if field_type not in ALLOWED_TYPES:
                fail(f"{table_name}.{field_name}: unsupported type {field_type!r}")
            if not isinstance(spec.get("nullable"), bool):
                fail(f"{table_name}.{field_name}: nullable must be boolean")
            unit = spec.get("unit")
            if unit is not None and unit not in ALLOWED_UNITS:
                fail(f"{table_name}.{field_name}: unsupported unit {unit!r}")
            if "min" in spec and "max" in spec and spec["min"] > spec["max"]:
                fail(f"{table_name}.{field_name}: min exceeds max")
            if field_type == "enum":
                values = spec.get("values")
                if not isinstance(values, list) or not values or len(values) != len(set(values)):
                    fail(f"{table_name}.{field_name}: enum values must be non-empty and unique")
            if field_name.endswith("_sec") and unit != "sec":
                fail(f"{table_name}.{field_name}: *_sec must declare unit=sec")
            if field_name.endswith("_cm") and unit != "cm":
                fail(f"{table_name}.{field_name}: *_cm must declare unit=cm")
            if field_name.endswith("_lbs") and unit != "lb":
                fail(f"{table_name}.{field_name}: *_lbs must declare unit=lb")

        for pair in table.get("pair_rules", []):
            if not isinstance(pair, list) or len(pair) != 2 or pair[0] not in fields or pair[1] not in fields:
                fail(f"{table_name}: invalid pair rule {pair!r}")

    for table_name, required in REQUIRED_CORE.items():
        if table_name not in tables:
            fail(f"required core table missing: {table_name}")
        missing = required - set(tables[table_name]["fields"])
        if missing:
            fail(f"{table_name}: master-plan core fields missing: {sorted(missing)}")

    for table_name in ("fighter_round_stats", "fighter_round_position", "judge_round_scores"):
        round_spec = tables[table_name]["fields"].get("round", {})
        if round_spec.get("min") != 1:
            fail(f"{table_name}.round must have min=1")

    print(
        "CONTRACT_OK "
        f"version={payload.get('contract_version')} tables={len(tables)} fields={field_count} "
        "missing_is_not_zero=true round_zero_actual=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
