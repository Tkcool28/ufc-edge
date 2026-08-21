#!/usr/bin/env python3
"""Print compact canonical-core build diagnostics before validation."""
import csv
import json
from pathlib import Path

p = Path("data/canonical/v0/manifest.json")
if not p.exists():
    raise SystemExit("CANONICAL_BUILD_REPORT: manifest missing")
m = json.loads(p.read_text(encoding="utf-8"))
print("CANONICAL_BUILD_COUNTS " + json.dumps(m.get("counts", {}), sort_keys=True))
print("CANONICAL_EXCLUSION_REASONS " + json.dumps(m.get("exclusion_reason_counts", {}), sort_keys=True))

ex = Path("data/derived/qa/canonical_core_exclusions_v0.csv")
examples = []
if ex.exists():
    with ex.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("reason") == "invalid_round_stat_transport":
                examples.append({k: row.get(k) for k in ["source_record_id", "fighter", "details"]})
                if len(examples) >= 12:
                    break
print("CANONICAL_INVALID_ROUND_EXAMPLES " + json.dumps(examples, ensure_ascii=False, sort_keys=True))
