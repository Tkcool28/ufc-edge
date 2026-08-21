#!/usr/bin/env python3
"""Record a compact, non-transforming sample of Greco/UFCStats cell encodings.

The purpose is to design shared adapter parsers from actual raw values rather than
column-name assumptions. This script does not canonicalize, split fighter identity, or
infer semantics. It only records representative raw strings and coarse shape counts.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path("data/raw/greco1899/8e40eb945e11/ufc_fight_stats.csv")
OUT = Path("provenance/audits/greco_cell_shapes.json")
FIELDS = [
    "FIGHTER", "KD", "SIG.STR.", "SIG.STR. %", "TOTAL STR.", "TD", "TD %",
    "SUB.ATT", "REV.", "CTRL", "HEAD", "BODY", "LEG", "DISTANCE", "CLINCH", "GROUND",
]
SAMPLE_ROWS = 12
MAX_UNIQUE_EXAMPLES = 12


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def shape(value: str) -> str:
    if value == "":
        return "empty"
    if "\n" in value or "\r" in value:
        return "contains_newline"
    if re.fullmatch(r"\s*\d+\s+of\s+\d+\s*", value, flags=re.I):
        return "landed_of_attempted"
    if re.fullmatch(r"\s*\d{1,2}:\d{2}\s*", value):
        return "minute_second"
    if re.fullmatch(r"\s*\d+%\s*", value):
        return "percent"
    if re.fullmatch(r"\s*\d+\s*", value):
        return "integer"
    if re.fullmatch(r"\s*\d+(?:\.\d+)?\s*", value):
        return "number"
    if re.search(r"\s{2,}", value):
        return "contains_multi_space"
    return "text"


def main() -> int:
    if not SOURCE.exists():
        raise SystemExit(f"missing source: {SOURCE}")

    first_rows = []
    examples: dict[str, list[str]] = {field: [] for field in FIELDS}
    shape_counts: dict[str, Counter[str]] = {field: Counter() for field in FIELDS}
    row_count = 0

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise SystemExit("missing header")
        missing = [f for f in FIELDS if f not in reader.fieldnames]
        if missing:
            raise SystemExit(f"missing expected columns: {missing}")

        for row in reader:
            row_count += 1
            if len(first_rows) < SAMPLE_ROWS:
                first_rows.append({field: row.get(field) for field in ["EVENT", "BOUT", "ROUND", *FIELDS]})
            for field in FIELDS:
                value = row.get(field)
                if value is None:
                    shape_counts[field]["missing_key"] += 1
                    continue
                shape_counts[field][shape(value)] += 1
                if value not in examples[field] and len(examples[field]) < MAX_UNIQUE_EXAMPLES:
                    examples[field].append(value)

    payload = {
        "schema_version": 1,
        "audited_at_utc": now(),
        "source": SOURCE.as_posix(),
        "rows": row_count,
        "fields": FIELDS,
        "first_rows": first_rows,
        "shape_counts": {field: dict(counter) for field, counter in shape_counts.items()},
        "representative_raw_values": examples,
        "semantics": {
            "raw_only": True,
            "no_canonicalization": True,
            "purpose": "Define shared adapter parsing from observed raw cell encodings.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"GRECO_CELL_SHAPES_OK rows={row_count} out={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
