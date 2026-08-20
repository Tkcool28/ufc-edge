#!/usr/bin/env python3
"""Validate the raw-source -> canonical-field registry against both ends.

This prevents adapter drift caused by typoed provider fields, renamed canonical fields,
or optimistic mappings to surfaces that were never actually acquired.
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path("schemas/canonical_data_contract_v0.json")
MAP_PATH = Path("schemas/source_field_map_v0.json")
SURFACE_PATH = Path("provenance/audits/source_surface_inventory.json")


def fail(message: str) -> None:
    raise SystemExit(f"SOURCE_MAP_INVALID: {message}")


def load(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        fail(f"{path}: expected JSON object")
    return obj


def build_surfaces(payload: dict[str, Any]) -> dict[tuple[str, str], set[str]]:
    result: dict[tuple[str, str], set[str]] = {}
    for item in payload.get("sources", []):
        if not isinstance(item, dict):
            continue
        key = (str(item.get("source")), str(item.get("collection")))
        fields = set(str(x) for x in (item.get("columns") or []))
        fields.update(str(x) for x in (item.get("attributes") or []))
        fields.update(f"relationships.{x}" for x in (item.get("relationship_names") or []))
        result[key] = fields
    return result


def source_field_exists(source_field: str, available: set[str]) -> bool:
    if source_field == "$id":
        return True
    # Composite exact fields such as FIRST+LAST or a set of ESPN play types.
    if "+" in source_field and "|" not in source_field:
        return all(part in available for part in source_field.split("+") if part)
    if "|" in source_field:
        parts = [part for part in source_field.split("|") if part]
        for part in parts:
            if "*" in part:
                if not any(fnmatch.fnmatch(candidate, part) for candidate in available):
                    return False
            elif part not in available:
                return False
        return True
    if "*" in source_field:
        return any(fnmatch.fnmatch(candidate, source_field) for candidate in available)
    return source_field in available


def main() -> int:
    contract = load(CONTRACT_PATH)
    mapping = load(MAP_PATH)
    surface_payload = load(SURFACE_PATH)

    tables = contract.get("tables") or {}
    surfaces = build_surfaces(surface_payload)
    allowed_status = set(mapping.get("mapping_status_values") or [])
    allowed_temporal = set(mapping.get("temporal_class_values") or [])
    allowed_roles = set(mapping.get("source_role_values") or [])
    rows = mapping.get("mappings")
    if not isinstance(rows, list) or not rows:
        fail("mappings must be a non-empty list")

    seen: set[tuple[str, str, str, str, str]] = set()
    status_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}

    for i, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            fail(f"row {i}: expected object")
        source = str(row.get("source") or "")
        collection = str(row.get("collection") or "")
        source_field = str(row.get("source_field") or "")
        status = str(row.get("mapping_status") or "")
        temporal = str(row.get("temporal_class") or "")
        role = str(row.get("source_role") or "")
        target_table = row.get("target_table")
        target_field = row.get("target_field")

        if not source or not collection or not source_field:
            fail(f"row {i}: source, collection, and source_field are required")
        if status not in allowed_status:
            fail(f"row {i}: invalid mapping_status {status!r}")
        if temporal not in allowed_temporal:
            fail(f"row {i}: invalid temporal_class {temporal!r}")
        if role not in allowed_roles:
            fail(f"row {i}: invalid source_role {role!r}")

        key = (source, collection)
        if key not in surfaces:
            fail(f"row {i}: source surface not acquired/inventoried: {source}/{collection}")
        if not source_field_exists(source_field, surfaces[key]):
            fail(
                f"row {i}: provider field not found in acquired surface: "
                f"{source}/{collection}/{source_field}"
            )

        if target_table is None or target_field is None:
            if status not in {"unresolved", "rejected"}:
                fail(f"row {i}: {status} mapping requires canonical target")
        else:
            if target_table not in tables:
                fail(f"row {i}: target table does not exist: {target_table}")
            if target_field not in (tables[target_table].get("fields") or {}):
                fail(f"row {i}: target field does not exist: {target_table}.{target_field}")

        dedupe_key = (source, collection, source_field, str(target_table), str(target_field))
        if dedupe_key in seen:
            fail(f"row {i}: duplicate mapping key {dedupe_key}")
        seen.add(dedupe_key)
        status_counts[status] = status_counts.get(status, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1

    if mapping.get("rules", {}).get("name_similarity_is_not_semantic_verification") is not True:
        fail("name-similarity safety rule must remain true")
    if mapping.get("rules", {}).get("unresolved_mappings_do_not_emit_canonical_values") is not True:
        fail("unresolved mappings must fail closed")

    print(
        "SOURCE_MAP_OK "
        f"version={mapping.get('map_version')} mappings={len(rows)} "
        f"statuses={json.dumps(status_counts, sort_keys=True)} "
        f"source_count={len(source_counts)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
