#!/usr/bin/env python3
"""Record exact transport encoding of Greco/UFCStats round-stat cells.

This is a bounded schema/transport audit so shared parsers are written against actual
committed raw values rather than assumptions about embedded corner formatting.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

SRC_ROOT = Path("data/raw/greco1899")
OUT = Path("provenance/audits/greco_cell_encoding_latest.json")
FIELDS = ["ROUND", "FIGHTER", "KD", "SIG.STR.", "TOTAL STR.", "TD", "SUB.ATT", "REV.", "CTRL", "HEAD", "BODY", "LEG", "DISTANCE", "CLINCH", "GROUND"]


def latest_file() -> Path:
    files = sorted(SRC_ROOT.glob("*/ufc_fight_stats.csv"))
    if not files:
        raise RuntimeError("No Greco ufc_fight_stats.csv")
    return files[-1]


def main() -> int:
    path = latest_file()
    samples = []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise RuntimeError("CSV missing header")
        missing = [x for x in FIELDS if x not in reader.fieldnames]
        if missing:
            raise RuntimeError(f"Expected fields missing: {missing}")
        for i, row in enumerate(reader):
            if i >= 12:
                break
            samples.append({
                "row_number_1_based_after_header": i + 2,
                "event": row.get("EVENT"),
                "bout": row.get("BOUT"),
                "values": {field: row.get(field) for field in FIELDS},
                "repr_values": {field: repr(row.get(field)) for field in FIELDS},
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "schema_version": 1,
        "source_file": path.as_posix(),
        "fields": FIELDS,
        "sample_rows": samples,
        "note": "repr_values are transport QA only; canonical parsers must still validate cardinality and landed<=attempted.",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"GRECO_CELL_ENCODING_OK samples={len(samples)} output={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
