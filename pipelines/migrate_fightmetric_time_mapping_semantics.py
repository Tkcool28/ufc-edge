#!/usr/bin/env python3
"""One-time audited correction to official FightMetric time/corner source mappings.

Evidence:
- numeric color mapping was promoted by provenance/audits/fightmetric_color_semantics_latest.json;
- archived control_time matches floor(Greco CTRL seconds / 60) on 97.45% of 23,876
  aligned observations, disproving the previous seconds mapping.

No archived positional time field may emit canonical seconds until its quantization/unit
semantics are represented explicitly in the canonical contract.
"""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path("schemas/source_field_map_v0.json")
COLOR_AUDIT = Path("provenance/audits/fightmetric_color_semantics_latest.json")
ROUND_AUDIT = Path("provenance/audits/ufc_greco_round_overlap_latest.json")
TIME_FIELDS = {
    "standing_time", "neutral_time", "distance_time", "clinch_time", "ground_time",
    "control_time", "ground_ctl_time", "guard_ctl_time", "half_guard_ctl_time",
    "side_ctl_time", "mount_ctl_time", "back_ctl_time", "msc_ground_ctl__time",
}


def main() -> int:
    mapping = json.loads(PATH.read_text(encoding="utf-8"))
    color = json.loads(COLOR_AUDIT.read_text(encoding="utf-8"))
    round_audit = json.loads(ROUND_AUDIT.read_text(encoding="utf-8"))

    decision = color.get("decision") or {}
    if decision.get("mapping_promoted") is not True or decision.get("numeric_to_corner") != {"0": "red", "1": "blue"}:
        raise RuntimeError("Expected promoted FightMetric color mapping 0=red,1=blue")

    floor_test = (((round_audit.get("archived_control_time_semantics") or {}).get("candidate_tests") or {}).get("raw_equals_floor_minutes") or {})
    if float(floor_test.get("match_fraction") or 0) < 0.95:
        raise RuntimeError("Control-time floor-minute evidence is below required 95% gate")

    changed_time = 0
    changed_color = 0
    for row in mapping.get("mappings") or []:
        if row.get("source") != "ufc_fightmetric_official" or row.get("collection") != "fight_stat":
            continue
        field = row.get("source_field")
        if field == "color":
            row["transform"] = "map_numeric_corner_0_red_1_blue_then_resolve_official_fighter"
            row["mapping_status"] = "verified"
            row["notes"] = (
                "Transport-only corner code. Full audit over 250,782 shared field comparisons promoted "
                "0=red and 1=blue; never expose numeric color as a predictive field."
            )
            changed_color += 1
        elif field in TIME_FIELDS:
            row["target_table"] = None
            row["target_field"] = None
            row["transform"] = "none"
            row["mapping_status"] = "unresolved"
            evidence = (
                "Archived FightMetric positional time fields are integer-quantized, not exact seconds. "
                "For control_time, raw == floor(Greco control seconds/60) in 97.45% of 23,876 aligned rows. "
                "Do not emit canonical *_sec values. Preserve raw until a coarse-time canonical representation is defined."
            )
            row["notes"] = evidence
            changed_time += 1

    if changed_color != 1:
        raise RuntimeError(f"Expected exactly one color mapping, changed={changed_color}")
    if changed_time < 8:
        raise RuntimeError(f"Expected multiple archived time mappings, changed only {changed_time}")

    mapping["map_version"] = "0.2.0-draft"
    rules = mapping.setdefault("rules", {})
    rules["duration_units_require_semantic_verification"] = True
    rules["quantized_time_must_not_emit_exact_seconds"] = True
    PATH.write_text(json.dumps(mapping, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"updated color={changed_color} archived_time_mappings={changed_time}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
