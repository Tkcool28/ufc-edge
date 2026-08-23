#!/usr/bin/env python3
"""Report the exact raw schema of the pinned external pro-MMA fight CSV.

DATA PHASE ONLY. This is a read-only source audit; no canonical rows are written.
The audit is intentionally narrow: measure the source before writing any overlap logic.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/raw/kaggle_pro_mma_fights/v1/pro_mma_fights.csv"
OUT = ROOT / "provenance/audits/external_mma_raw_schema_latest.json"


def main() -> int:
    with SRC.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        if not fields or len(set(fields)) != len(fields):
            raise SystemExit("invalid or duplicate CSV header")
        rows = list(reader)

    nonempty = {f: sum(bool((r.get(f) or "").strip()) for r in rows) for f in fields}
    samples = {}
    for f in fields:
        vals = []
        seen = set()
        for r in rows:
            v = (r.get(f) or "").strip()
            if v and v not in seen:
                vals.append(v)
                seen.add(v)
            if len(vals) >= 8:
                break
        samples[f] = vals

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": str(SRC.relative_to(ROOT)),
        "row_count": len(rows),
        "column_count": len(fields),
        "columns": fields,
        "nonempty_counts": nonempty,
        "bounded_distinct_samples": samples,
        "decision": {
            "canonical_rows_written": False,
            "schema_inferred_from_filename": False,
            "required_next": "Use only these measured column names to build the external-MMA fight identity/overlap audit."
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "columns": fields}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
