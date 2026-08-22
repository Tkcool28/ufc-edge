#!/usr/bin/env python3
"""Fail-closed validator for source precedence rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
SOURCE_MAP = ROOT / "schemas/source_field_map_v0.json"
PRECEDENCE = ROOT / "schemas/source_precedence_v0.json"

ALLOWED_STATUSES = {"active", "pending_acquisition", "acquired_qa_pending"}


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source_map = json.loads(SOURCE_MAP.read_text(encoding="utf-8"))
    precedence = json.loads(PRECEDENCE.read_text(encoding="utf-8"))

    tables = contract.get("tables") or {}
    known_sources = {str(row.get("source")) for row in source_map.get("mappings") or [] if row.get("source")}
    families: set[str] = set()
    active = pending_acquisition = acquired_qa_pending = 0

    for rule in precedence.get("rules") or []:
        family = str(rule.get("family") or "")
        if not family or family in families:
            raise RuntimeError(f"Missing/duplicate precedence family: {family!r}")
        families.add(family)
        status = rule.get("status")
        if status not in ALLOWED_STATUSES:
            raise RuntimeError(f"Unsupported precedence status for {family}: {status!r}")
        active += status == "active"
        pending_acquisition += status == "pending_acquisition"
        acquired_qa_pending += status == "acquired_qa_pending"

        target_tables = []
        if rule.get("canonical_table"):
            target_tables.append(rule["canonical_table"])
        target_tables.extend(rule.get("canonical_tables") or [])
        if not target_tables:
            raise RuntimeError(f"No canonical table declared for {family}")
        for table in target_tables:
            if table not in tables:
                raise RuntimeError(f"Unknown canonical table in {family}: {table}")

        fields = rule.get("fields") or []
        if fields:
            if len(target_tables) != 1:
                raise RuntimeError(f"Field list requires one canonical table in {family}")
            table_fields = (tables[target_tables[0]].get("fields") or {})
            missing = sorted(set(fields) - set(table_fields))
            if missing:
                raise RuntimeError(f"Unknown canonical fields in {family}: {missing}")

        # Only active families may feed canonical values now, so their source IDs must
        # already exist in the adapter map. Acquired-but-QA-pending families may name a
        # raw provider before structured mappings are promoted.
        if status == "active":
            unknown_sources = [source for source in rule.get("priority") or [] if source not in known_sources]
            if unknown_sources:
                raise RuntimeError(f"Unknown active priority sources in {family}: {unknown_sources}; known={sorted(known_sources)}")

        if status == "acquired_qa_pending":
            evidence = rule.get("evidence")
            if not evidence:
                raise RuntimeError(f"Acquired QA-pending family lacks acquisition evidence: {family}")
            if not (ROOT / str(evidence)).exists():
                raise RuntimeError(f"Acquired QA-pending evidence missing for {family}: {evidence}")

    for name, rel in (precedence.get("evidence") or {}).items():
        path = ROOT / str(rel)
        if not path.exists():
            raise RuntimeError(f"Missing precedence evidence {name}: {rel}")

    print(
        "SOURCE_PRECEDENCE_OK "
        f"version={precedence.get('precedence_version')} families={len(families)} "
        f"active={active} pending_acquisition={pending_acquisition} "
        f"acquired_qa_pending={acquired_qa_pending} sources={len(known_sources)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
