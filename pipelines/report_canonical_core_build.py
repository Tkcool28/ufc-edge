#!/usr/bin/env python3
"""Print compact canonical-core build diagnostics before validation."""
import json
from pathlib import Path

p = Path("data/canonical/v0/manifest.json")
if not p.exists():
    raise SystemExit("CANONICAL_BUILD_REPORT: manifest missing")
m = json.loads(p.read_text(encoding="utf-8"))
print("CANONICAL_BUILD_COUNTS " + json.dumps(m.get("counts", {}), sort_keys=True))
print("CANONICAL_EXCLUSION_REASONS " + json.dumps(m.get("exclusion_reason_counts", {}), sort_keys=True))
