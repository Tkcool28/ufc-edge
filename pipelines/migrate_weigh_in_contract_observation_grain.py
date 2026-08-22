#!/usr/bin/env python3
"""One-way DATA-phase contract correction for fight-specific weigh-in observations.

The migration accepts exactly two states:
- the known v0.3 draft shape, which is migrated to v0.4; or
- the exact intended v0.4 shape, which is a verified no-op.
Any other state fails closed.
"""
from __future__ import annotations

import json
from pathlib import Path

JSON_PATH = Path("schemas/canonical_data_contract_v0.json")
MD_PATH = Path("schemas/canonical_data_contract_v0.md")
OLD_VERSION = "0.3.0-draft"
NEW_VERSION = "0.4.0-draft"
OLD_PK = ["fight_id", "fighter_id", "attempt_number"]
NEW_PK = ["weigh_in_observation_id"]
NEW_GRAIN = "one fight-specific fighter official weigh-in observation; scale-attempt number may be unknown"

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


def safety_rules_ok(payload: dict) -> bool:
    rules = payload.get("global_rules") or {}
    return rules.get("missing_is_not_zero") is True and rules.get("display_name_only_identity_is_trusted") is False


def exact_v04(payload: dict, md: str) -> bool:
    table = (payload.get("tables") or {}).get("weigh_ins") or {}
    fields = table.get("fields") or {}
    obs = fields.get("weigh_in_observation_id") or {}
    attempt = fields.get("attempt_number") or {}
    version_line = f"Machine contract: `schemas/canonical_data_contract_v0.json` (`{NEW_VERSION}`)"
    return (
        payload.get("contract_version") == NEW_VERSION
        and safety_rules_ok(payload)
        and table.get("primary_key") == NEW_PK
        and table.get("grain") == NEW_GRAIN
        and obs.get("type") == "string" and obs.get("nullable") is False
        and attempt.get("type") == "integer" and attempt.get("nullable") is True
        and md.count(version_line) == 1
        and md.count(NEW_MD) == 1
        and OLD_MD not in md
    )


def main() -> int:
    payload = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    md = MD_PATH.read_text(encoding="utf-8")

    if exact_v04(payload, md):
        print("WEIGH_IN_CONTRACT_MIGRATION_ALREADY_OK version=0.4.0-draft")
        return 0

    if payload.get("contract_version") != OLD_VERSION:
        fail(f"expected exact v0.3 source or exact v0.4 target, got {payload.get('contract_version')!r}")
    if not safety_rules_ok(payload):
        fail("global safety rules are not at expected strict values")

    table = (payload.get("tables") or {}).get("weigh_ins")
    if not isinstance(table, dict):
        fail("weigh_ins table missing")
    if table.get("primary_key") != OLD_PK:
        fail(f"unexpected old primary key: {table.get('primary_key')!r}")
    fields = table.get("fields") or {}
    attempt = fields.get("attempt_number")
    if not isinstance(attempt, dict) or attempt.get("nullable") is not False or attempt.get("type") != "integer":
        fail("attempt_number old field shape is not the expected required integer")
    if "weigh_in_observation_id" in fields:
        fail("weigh_in_observation_id already exists in v0.3 source")

    old_version_line = f"Machine contract: `schemas/canonical_data_contract_v0.json` (`{OLD_VERSION}`)"
    if md.count(old_version_line) != 1 or md.count(OLD_MD) != 1:
        fail("markdown v0.3 source shape is not exact")

    new_fields = {
        "weigh_in_observation_id": {
            "nullable": False,
            "type": "string",
            "semantics": "stable canonical ID for one source-supported fight-specific fighter weigh-in observation",
        }
    }
    for name, spec in fields.items():
        spec = dict(spec)
        if name == "attempt_number":
            spec["nullable"] = True
            spec["semantics"] = "scale attempt number only when source-explicit; null means unknown, not first attempt"
        new_fields[name] = spec

    table["fields"] = new_fields
    table["grain"] = NEW_GRAIN
    table["primary_key"] = NEW_PK
    payload["contract_version"] = NEW_VERSION
    JSON_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = md.replace(old_version_line, f"Machine contract: `schemas/canonical_data_contract_v0.json` (`{NEW_VERSION}`)", 1)
    md = md.replace(OLD_MD, NEW_MD, 1)
    MD_PATH.write_text(md, encoding="utf-8")

    check = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    check_md = MD_PATH.read_text(encoding="utf-8")
    if not exact_v04(check, check_md):
        fail("post-migration target shape failed exact verification")

    print("WEIGH_IN_CONTRACT_MIGRATION_OK version=0.4.0-draft pk=weigh_in_observation_id attempt_number_nullable=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
