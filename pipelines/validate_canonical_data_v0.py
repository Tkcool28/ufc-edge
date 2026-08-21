#!/usr/bin/env python3
"""Fail-closed validation for materialized UFC Edge canonical v0 tables."""
from __future__ import annotations

import csv
import json
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
DATA = ROOT / "data/canonical/v0"

TABLE_FILES = {
    "fighters": "fighters.csv",
    "events": "events.csv",
    "fights": "fights.csv",
    "fighter_round_stats": "fighter_round_stats.csv",
    "source_identity_links": "source_identity_links.csv",
    "field_provenance": "field_provenance.csv",
}


def fail(msg: str) -> None:
    raise SystemExit(f"CANONICAL_DATA_INVALID: {msg}")


def read_table(name: str, fields: dict) -> list[dict[str, str]]:
    path = DATA / TABLE_FILES[name]
    if not path.exists():
        fail(f"missing {path}")
    with path.open("r", encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        if r.fieldnames != list(fields):
            fail(f"{name}: header mismatch expected={list(fields)} got={r.fieldnames}")
        return list(r)


def validate_scalar(table: str, field: str, raw: str, spec: dict) -> None:
    if raw == "":
        if not spec.get("nullable"):
            fail(f"{table}.{field}: null in non-nullable field")
        return
    typ = spec["type"]
    try:
        if typ == "integer":
            val = int(raw)
            if str(val) != raw and not (raw.startswith("+") and str(val) == raw[1:]):
                fail(f"{table}.{field}: non-canonical integer {raw!r}")
        elif typ == "number":
            val = Decimal(raw)
        elif typ == "boolean":
            if raw not in {"true", "false"}:
                fail(f"{table}.{field}: bad boolean {raw!r}")
            return
        elif typ == "date":
            date.fromisoformat(raw); return
        elif typ == "timestamp":
            datetime.fromisoformat(raw.replace("Z", "+00:00")); return
        elif typ == "enum":
            if raw not in spec["values"]:
                fail(f"{table}.{field}: enum value {raw!r} outside {spec['values']}")
            return
        elif typ == "string":
            return
        else:
            fail(f"{table}.{field}: unsupported type {typ}")
    except (ValueError, InvalidOperation) as exc:
        fail(f"{table}.{field}: invalid {typ} {raw!r}: {exc}")
    if "min" in spec and val < Decimal(str(spec["min"])):
        fail(f"{table}.{field}: {raw} below min {spec['min']}")
    if "max" in spec and val > Decimal(str(spec["max"])):
        fail(f"{table}.{field}: {raw} above max {spec['max']}")


def validate_table(name: str, rows: list[dict[str, str]], table: dict) -> None:
    fields = table["fields"]
    pk_fields = table["primary_key"]
    seen = set()
    for idx, row in enumerate(rows, start=2):
        for field, spec in fields.items():
            validate_scalar(name, field, row[field], spec)
        pk = tuple(row[x] for x in pk_fields)
        if pk in seen:
            fail(f"{name}: duplicate primary key at row {idx}: {pk}")
        seen.add(pk)
        for landed, attempted in table.get("pair_rules", []):
            if row[landed] != "" and row[attempted] != "" and int(row[landed]) > int(row[attempted]):
                fail(f"{name}: landed > attempted at row {idx}: {landed}/{attempted}")
    print(f"TABLE_OK {name} rows={len(rows)}")


def validate_uuid(value: str, context: str) -> None:
    try:
        parsed = uuid.UUID(value)
    except ValueError:
        fail(f"{context}: canonical ID is not UUID: {value!r}")
    if str(parsed) != value.lower():
        fail(f"{context}: UUID not canonical lowercase format: {value!r}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    tables: dict[str, list[dict[str, str]]] = {}
    for name, filename in TABLE_FILES.items():
        spec = contract["tables"][name]
        rows = read_table(name, spec["fields"])
        validate_table(name, rows, spec)
        tables[name] = rows

    fighter_ids = {r["fighter_id"] for r in tables["fighters"]}
    event_ids = {r["event_id"] for r in tables["events"]}
    fight_ids = {r["fight_id"] for r in tables["fights"]}
    for fid in fighter_ids: validate_uuid(fid, "fighters")
    for eid in event_ids: validate_uuid(eid, "events")
    for fight_id in fight_ids: validate_uuid(fight_id, "fights")

    fight_by_id = {r["fight_id"]: r for r in tables["fights"]}
    for row in tables["fights"]:
        if row["event_id"] not in event_ids:
            fail(f"fight {row['fight_id']} references missing event")
        if row["fighter_a_id"] not in fighter_ids or row["fighter_b_id"] not in fighter_ids:
            fail(f"fight {row['fight_id']} references missing fighter")
        if row["fighter_a_id"] == row["fighter_b_id"]:
            fail(f"fight {row['fight_id']} has same fighter twice")
        if row["winner_id"] and row["winner_id"] not in {row["fighter_a_id"], row["fighter_b_id"]}:
            fail(f"fight {row['fight_id']} winner is not participant")
        if row["result"] == "win_loss" and not row["winner_id"]:
            fail(f"fight {row['fight_id']} win_loss lacks winner")
        if row["result"] in {"draw", "no_contest"} and row["winner_id"]:
            fail(f"fight {row['fight_id']} {row['result']} must not have winner")

    for row in tables["fighter_round_stats"]:
        fight = fight_by_id.get(row["fight_id"])
        if not fight:
            fail(f"round references missing fight {row['fight_id']}")
        participant_set = {fight["fighter_a_id"], fight["fighter_b_id"]}
        if row["fighter_id"] not in participant_set or row["opponent_id"] not in participant_set:
            fail(f"round {row['fight_id']} R{row['round']} references nonparticipant")
        if row["fighter_id"] == row["opponent_id"]:
            fail(f"round {row['fight_id']} R{row['round']} fighter equals opponent")
        if int(row["round"]) < 1:
            fail("round zero/negative leaked into canonical data")

    entity_sets = {"fighter": fighter_ids, "event": event_ids, "fight": fight_ids}
    for row in tables["source_identity_links"]:
        expected = entity_sets.get(row["entity_type"])
        if expected is not None and row["canonical_id"] not in expected:
            fail(f"identity link references missing {row['entity_type']} {row['canonical_id']}")

    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("canonical_contract_version") != contract.get("contract_version"):
        fail("manifest contract version does not match current contract")
    if manifest.get("counts", {}).get("fighters") != len(tables["fighters"]):
        fail("manifest fighter count mismatch")
    if manifest.get("counts", {}).get("fights") != len(tables["fights"]):
        fail("manifest fight count mismatch")
    if manifest.get("counts", {}).get("fighter_round_stats") != len(tables["fighter_round_stats"]):
        fail("manifest round count mismatch")

    print(
        "CANONICAL_DATA_OK "
        f"contract={contract.get('contract_version')} fighters={len(fighter_ids)} events={len(event_ids)} "
        f"fights={len(fight_ids)} rounds={len(tables['fighter_round_stats'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
