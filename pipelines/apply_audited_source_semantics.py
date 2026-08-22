#!/usr/bin/env python3
"""Apply machine-audited source semantics to the source-field registry.

This is intentionally narrow: it promotes only mappings whose semantics have already
passed durable audits. It never weakens validation or infers a unit from field names.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "schemas/source_field_map_v0.json"
POSITION_AUDIT = ROOT / "provenance/audits/fightmetric_position_time_quality_latest.json"

POSITION_TARGETS = {
    "standing_time": "standing_bucket_min",
    "neutral_time": "neutral_bucket_min",
    "distance_time": "distance_bucket_min",
    "clinch_time": "clinch_bucket_min",
    "ground_time": "ground_bucket_min",
    "ground_ctl_time": "ground_control_bucket_min",
    "guard_ctl_time": "guard_control_bucket_min",
    "half_guard_ctl_time": "half_guard_control_bucket_min",
    "side_ctl_time": "side_control_bucket_min",
    "mount_ctl_time": "mount_control_bucket_min",
    "back_ctl_time": "back_control_bucket_min",
    "msc_ground_ctl__time": "misc_ground_control_bucket_min",
}


def main() -> int:
    registry = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    audit = json.loads(POSITION_AUDIT.read_text(encoding="utf-8"))
    decision = audit.get("decision") or {}
    minimum = float(audit.get("minimum_roundscale_fraction_across_fields") or 0.0)
    if decision.get("dominant_0_5_bucket_encoding") is not True:
        raise RuntimeError("Position-time audit did not approve dominant 0-5 bucket encoding")
    if decision.get("gt_5_values_canonical_eligible") is not False:
        raise RuntimeError("Position-time audit must explicitly reject >5 anomalies")
    if minimum < 0.99:
        raise RuntimeError(f"Position-time roundscale coverage too weak: {minimum}")

    seen: set[str] = set()
    changed = 0
    mappings = registry.get("mappings") or []
    for row in mappings:
        if row.get("source") != "ufc_fightmetric_official" or row.get("collection") != "fight_stat":
            continue
        source_field = row.get("source_field")
        if source_field not in POSITION_TARGETS:
            continue
        target = POSITION_TARGETS[source_field]
        row.update(
            {
                "mapping_status": "verified",
                "source_role": "official_primary_coarse_position",
                "target_table": "fighter_round_position",
                "target_field": target,
                "transform": "parse_int_0_5_as_floor_min_bucket_else_reject",
                "notes": (
                    "Audited actual-round FightMetric positional encoding is overwhelmingly 0-5; "
                    ">5 values are source anomalies and are not canonical-eligible. Preserve the "
                    "accepted value as a floor-whole-minute bucket, never as exact seconds. "
                    "Evidence: provenance/audits/fightmetric_position_time_quality_latest.json."
                ),
            }
        )
        seen.add(source_field)
        changed += 1

    missing = sorted(set(POSITION_TARGETS) - seen)
    if missing:
        raise RuntimeError(f"Expected FightMetric position mappings missing from registry: {missing}")

    # control_time is intentionally NOT mapped to the coarse position table because Greco
    # supplies precise seconds. Keep the UFC value as raw/QA-only evidence.
    control_rows = [
        row for row in mappings
        if row.get("source") == "ufc_fightmetric_official"
        and row.get("collection") == "fight_stat"
        and row.get("source_field") == "control_time"
    ]
    if len(control_rows) != 1:
        raise RuntimeError(f"Expected exactly one FightMetric control_time mapping, found {len(control_rows)}")
    control_rows[0].update(
        {
            "mapping_status": "unresolved",
            "source_role": "qa_coarse_duplicate",
            "target_table": None,
            "target_field": None,
            "transform": "none",
            "notes": (
                "Do not map archived UFC control_time to exact seconds. Against Greco, raw UFC "
                "control_time equals floor(control_seconds/60) in 97.45% of 23,876 comparisons. "
                "Greco remains the precise canonical control_sec source where available."
            ),
        }
    )

    registry["map_version"] = "0.3.1-draft"
    registry["audited_semantics"] = {
        "fightmetric_position_bucket_audit": str(POSITION_AUDIT.relative_to(ROOT)),
        "minimum_0_5_fraction": minimum,
        "promoted_position_fields": sorted(seen),
        "rejected_position_values": ">5",
        "control_time_exact_seconds_source": "greco1899_ufcstats",
    }
    MAP_PATH.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"changed": changed, "map_version": registry["map_version"], "minimum_fraction": minimum}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
