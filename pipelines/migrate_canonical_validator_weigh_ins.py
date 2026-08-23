#!/usr/bin/env python3
"""Exact/idempotent validator migration for canonical weigh_ins coverage."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "pipelines/validate_canonical_data_v0.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"{label} patch target not found")
    return text.replace(old, new, 1)


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    "field_provenance": "field_provenance.csv",\n}',
        '    "field_provenance": "field_provenance.csv",\n    "weigh_ins": "weigh_ins.csv",\n}',
        "TABLE_FILES",
    )
    marker = '    for row in tables["fighter_round_stats"]:\n'
    insert = '''    for row in tables["weigh_ins"]:
        validate_uuid(row["weigh_in_observation_id"], "weigh_ins")
        fight = fight_by_id.get(row["fight_id"])
        if not fight:
            fail(f"weigh-in references missing fight {row['fight_id']}")
        if row["fighter_id"] not in {fight["fighter_a_id"], fight["fighter_b_id"]}:
            fail(f"weigh-in {row['weigh_in_observation_id']} references nonparticipant fighter")

'''
    if insert not in text:
        if marker not in text:
            raise RuntimeError("weigh_ins FK validation patch target not found")
        text = text.replace(marker, insert + marker, 1)
    text = replace_once(
        text,
        'for name in ("fighters", "fights", "fighter_round_stats", "fighter_round_position"):',
        'for name in ("fighters", "fights", "fighter_round_stats", "fighter_round_position", "field_provenance", "weigh_ins"):',
        "manifest counts",
    )
    text = replace_once(
        text,
        'f"position_rows={len(tables[\'fighter_round_position\'])} "',
        'f"position_rows={len(tables[\'fighter_round_position\'])} weigh_ins={len(tables[\'weigh_ins\'])} "',
        "summary",
    )
    PATH.write_text(text, encoding="utf-8")
    print("CANONICAL_VALIDATOR_WEIGH_INS_MIGRATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
