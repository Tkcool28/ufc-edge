#!/usr/bin/env python3
"""One-way DATA-phase contract correction for fight-specific weigh-in observations.

Why this exists:
Official UFC weigh-in result pages reliably publish fighter scale weights but often do not
state which scale attempt produced the published official result. The v0.3 draft incorrectly
required attempt_number and used it in the primary key, which would force fabricated attempt
numbers or discard valid official scale observations.

This migration is deliberately fail-closed and only accepts the exact known v0.3 starting
shape. It does not weaken identity, missingness, unit, or validation rules.
"""
from __future__ import annotations

import json
from pathlib import Path

JSON_PATH = Path("schemas/canonical_data_contract_v0.json")
MD_PATH = Path("schemas/canonical_data_contract_v0.md")
OLD_VERSION = "0.3.0-draft"
NEW_VERSION = "0.4.0-draft"

OLD_MD = """## `weigh_ins`

One fight-specific fighter weigh-in attempt:

- `fight_id`
- `fighter_id`
- `weigh_in_date`
- `attempt_number`
- `scale_weight_lbs`
- `contract_limit_lbs`
- `missed_weight`
- `pounds_over`
- `catchweight_bout`
- `purse_penalty_pct`
- `official_status_text`

Roster/listed weight is not a substitute for scale weight.
"""

NEW_MD = """## `weigh_ins`

One fight-specific fighter **official weigh-in observation**. A published official result may
have an unknown scale-attempt number; unknown is preserved as `null`, never fabricated as 1.

- `weigh_in_observation_id` — stable canonical observation ID
- `fight_id`
- `fighter_id`
- `weigh_in_date`
- `attempt_number` — nullable; populated only when the source explicitly identifies the attempt
- `scale_weight_lbs`
- `contract_limit_lbs`
- `missed_weight`
- `pounds_over`
- `catchweight_bout`
- `purse_penalty_pct`
- `official_status_text`

Primary key: `weigh_in_observation_id`.

Roster/listed weight is not a substitute for scale weight. Page-local annotation markers are
not global semantic codes: miss/penalty/attempt fields may be populated only from explicit
source language tied to that observation.
"""


def fail(message: str) -> None:
    raise SystemExit(f"WEIGH_IN_CONTRACT_MIGRATION_REFUSED: {message}")


def main() -> int:
    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    if payload.get("contract_version") != OLD_VERSION:
        fail(f"expected contract_version={OLD_VERSION}, got {payload.get('contract_version')!r}")
    rules = payload.get("global_rules") or {}
    if rules.get("missing_is_not_zero") is not True or rules.get("display_name_only_identity_is_trusted") is not False:
        fail("global safety rules are not at expected strict values")

    table = (payload.get("tables") or {}).get("weigh_ins")
    if not isinstance(table, dict):
        fail("weigh_ins table missing")
    if table.get("primary_key") != ["fight_id", "fighter_id", "attempt_number"]:
        fail(f"unexpected old primary key: {table.get('primary_key')!r}")
    fields = table.get("fields") or {}
    attempt = fields.get("attempt_number")
    if not isinstance(attempt, dict) or attempt.get("nullable") is not False or attempt.get("type") != "integer":
        fail("attempt_number old field shape is not the expected required integer")
    if "weigh_in_observation_id" in fields:
        fail("weigh_in_observation_id already exists")

    new_fields = {
        "weigh_in_observation_id": {
            "nullable": False,
            "type": "string",
            "semantics": "stable canonical ID for one source-supported fight-specific fighter weigh-in observation"
        }
    }
    for name, spec in fields.items():
        spec = dict(spec)
        if name == "attempt_number":
            spec["nullable"] = True
            spec["semantics"] = "scale attempt number only when source-explicit; null means unknown, not first attempt"
        new_fields[name] = spec

    table["fields"] = new_fields
    table["grain"] = "one fight-specific fighter official weigh-in observation; scale-attempt number may be unknown"
    table["primary_key"] = ["weigh_in_observation_id"]
    payload["contract_version"] = NEW_VERSION
    JSON_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = MD_PATH.read_text(encoding="utf-8")
    expected_version_line = f"Machine contract: `schemas/canonical_data_contract_v0.json` (`{OLD_VERSION}`)"
    if md.count(expected_version_line) != 1:
        fail("markdown contract version line not found exactly once")
    md = md.replace(expected_version_line, f"Machine contract: `schemas/canonical_data_contract_v0.json` (`{NEW_VERSION}`)", 1)
    if md.count(OLD_MD) != 1:
        fail(f"expected exactly one old weigh_ins markdown block, found {md.count(OLD_MD)}")
    md = md.replace(OLD_MD, NEW_MD, 1)
    MD_PATH.write_text(md, encoding="utf-8")

    print(
        "WEIGH_IN_CONTRACT_MIGRATION_OK "
        f"version={NEW_VERSION} pk=weigh_in_observation_id attempt_number_nullable=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
