#!/usr/bin/env python3
"""Correct Greco round-stat transform labels after transport audit.

The committed Greco `ufc_fight_stats.csv` is one fighter per round. Values are scalar
(`0`, `3:38`) or single landed-attempted pairs (`3 of 5`), not two-corner packed cells.
This idempotent correction updates the source mapping registry to reflect the actual
raw grain/transport discovered in `provenance/audits/greco_cell_encoding_latest.json`.
"""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path("schemas/source_field_map_v0.json")

PAIR_TARGETS = {
    "sig_strikes_landed": "parse_landed_attempted_landed",
    "sig_strikes_attempted": "parse_landed_attempted_attempted",
    "total_strikes_landed": "parse_landed_attempted_landed",
    "total_strikes_attempted": "parse_landed_attempted_attempted",
    "takedowns_landed": "parse_landed_attempted_landed",
    "takedowns_attempted": "parse_landed_attempted_attempted",
    "sig_head_landed": "parse_landed_attempted_landed",
    "sig_head_attempted": "parse_landed_attempted_attempted",
    "sig_body_landed": "parse_landed_attempted_landed",
    "sig_body_attempted": "parse_landed_attempted_attempted",
    "sig_leg_landed": "parse_landed_attempted_landed",
    "sig_leg_attempted": "parse_landed_attempted_attempted",
    "sig_distance_landed": "parse_landed_attempted_landed",
    "sig_distance_attempted": "parse_landed_attempted_attempted",
    "sig_clinch_landed": "parse_landed_attempted_landed",
    "sig_clinch_attempted": "parse_landed_attempted_attempted",
    "sig_ground_landed": "parse_landed_attempted_landed",
    "sig_ground_attempted": "parse_landed_attempted_attempted",
}
SCALAR_TARGETS = {
    "knockdowns": "parse_nonnegative_int",
    "submission_attempts": "parse_nonnegative_int",
    "reversals": "parse_nonnegative_int",
    "control_sec": "parse_mmss_to_seconds",
    "round": "parse_round_number",
}


def main() -> int:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    changed = 0
    touched = 0
    for row in payload.get("mappings") or []:
        if row.get("source") != "greco1899_ufcstats" or row.get("collection") != "ufc_fight_stats":
            continue
        target = row.get("target_field")
        wanted = PAIR_TARGETS.get(target) or SCALAR_TARGETS.get(target)
        if wanted is None:
            continue
        touched += 1
        if row.get("transform") != wanted:
            row["transform"] = wanted
            changed += 1
        note = row.get("notes") or ""
        evidence = "Greco transport audit confirms one fighter per round; source cell is not a two-corner packed value."
        if evidence not in note:
            row["notes"] = (note + " " + evidence).strip()
            changed += 1

    if touched != len(PAIR_TARGETS) + len(SCALAR_TARGETS):
        raise RuntimeError(f"Expected {len(PAIR_TARGETS)+len(SCALAR_TARGETS)} Greco mappings, touched {touched}")
    PATH.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"GRECO_MAPPING_SEMANTICS_OK touched={touched} changes={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
