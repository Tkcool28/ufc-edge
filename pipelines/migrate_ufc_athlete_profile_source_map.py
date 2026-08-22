#!/usr/bin/env python3
"""One-time guarded migration of audited UFC athlete profile mappings.

This script exists so a large machine-readable registry is changed deterministically rather
than hand-editing JSON. It fails if the expected pre-migration mappings are not present.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "schemas/source_field_map_v0.json"
AUDIT = ROOT / "provenance/audits/ufc_athlete_profile_semantics_latest.json"
SOURCE = "ufc_com_official"
COLLECTION = "athletes"


def main() -> int:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if audit.get("athletes", 0) < 4000 or audit.get("decision", {}).get("point_in_time_only") is not True:
        raise RuntimeError("Athlete profile semantics audit is absent or insufficient")

    rows = payload.get("mappings") or []

    def matches(row: dict, *, source_field: str, target_field: str | None = None) -> bool:
        if row.get("source") != SOURCE or row.get("collection") != COLLECTION or row.get("source_field") != source_field:
            return False
        return target_field is None or row.get("target_field") == target_field

    def one(source_field: str, target_field: str | None = None) -> dict:
        found = [r for r in rows if matches(r, source_field=source_field, target_field=target_field)]
        if len(found) != 1:
            raise RuntimeError(f"Expected exactly one mapping for {source_field}->{target_field}; found={len(found)}")
        return found[0]

    # Existing provisional mappings corrected/promoted by the field-shape audit.
    weight = one("stats_weight", "listed_weight_lbs")
    weight.update({
        "mapping_status": "verified",
        "transform": "parse_decimal_pounds_zero_as_missing",
        "notes": "Official current profile weight string. 0.00 is source missingness, never a fight-specific scale weight.",
        "temporal_class": "point_in_time_snapshot",
    })

    status = one("status", "status_text")
    status.update({
        "mapping_status": "rejected",
        "target_table": None,
        "target_field": None,
        "transform": "do_not_map_publish_boolean_to_athlete_status",
        "notes": "Audit proves node attribute status is boolean publication/status transport, not the human athlete-status label.",
    })

    residence = one("residence", "residence_text")
    residence.update({
        "mapping_status": "verified",
        "transform": "format_structured_address_locality_admin_country",
        "notes": "Audit proves residence is a structured address object; preserve locality/admin/country components deterministically.",
    })

    origin = one("origin", "origin_text")
    origin.update({
        "mapping_status": "verified",
        "transform": "format_structured_address_locality_admin_country",
        "notes": "Audit proves origin is a structured address object; preserve locality/admin/country components deterministically.",
    })

    additions = [
        {
            "source": SOURCE,
            "collection": COLLECTION,
            "source_field": "relationships.stats_weight_class",
            "target_table": "fighter_profile_snapshots",
            "target_field": "listed_weight_class",
            "mapping_status": "verified",
            "source_role": "primary_candidate",
            "temporal_class": "point_in_time_snapshot",
            "transform": "resolve_included_relationship_label",
            "notes": "Included taxonomy object label audited present for all 3,271 relationship-bearing athletes.",
        },
        {
            "source": SOURCE,
            "collection": COLLECTION,
            "source_field": "relationships.gym",
            "target_table": "fighter_profile_snapshots",
            "target_field": "gym_text",
            "mapping_status": "verified",
            "source_role": "primary_candidate",
            "temporal_class": "point_in_time_snapshot",
            "transform": "resolve_included_relationship_label",
            "notes": "Included gym label audited present for all 1,203 relationship IDs.",
        },
        {
            "source": SOURCE,
            "collection": COLLECTION,
            "source_field": "relationships.fighting_style",
            "target_table": "fighter_profile_snapshots",
            "target_field": "fighting_style_text",
            "mapping_status": "verified",
            "source_role": "primary_candidate",
            "temporal_class": "point_in_time_snapshot",
            "transform": "resolve_included_relationship_labels_sorted_semicolon",
            "notes": "Relationship may contain multiple IDs; included labels are sorted and joined without inventing a hierarchy.",
        },
        {
            "source": SOURCE,
            "collection": COLLECTION,
            "source_field": "relationships.athlete_status",
            "target_table": "fighter_profile_snapshots",
            "target_field": "status_text",
            "mapping_status": "verified",
            "source_role": "primary_candidate",
            "temporal_class": "point_in_time_snapshot",
            "transform": "resolve_included_relationship_label",
            "notes": "This taxonomy relationship, not the boolean node status attribute, carries labels such as Active / Not Fighting.",
        },
    ]

    existing_keys = {
        (r.get("source"), r.get("collection"), r.get("source_field"), r.get("target_table"), r.get("target_field"))
        for r in rows
    }
    for add in additions:
        key = (add["source"], add["collection"], add["source_field"], add["target_table"], add["target_field"])
        if key in existing_keys:
            raise RuntimeError(f"Refusing duplicate mapping: {key}")
        rows.append(add)
        existing_keys.add(key)

    payload["map_version"] = "0.4.0-draft"
    payload.setdefault("rules", {})["ufc_athlete_profiles_are_point_in_time_only"] = True
    payload.setdefault("rules", {})["ufc_node_status_boolean_is_not_athlete_status"] = True
    PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"map_version": payload["map_version"], "mappings": len(rows), "added": len(additions)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
