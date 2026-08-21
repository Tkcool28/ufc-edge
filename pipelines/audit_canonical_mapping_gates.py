#!/usr/bin/env python3
"""Run canonical schema + source mapping gates and persist their exact terminal result."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("provenance/audits/canonical_mapping_gate_latest.json")
CHECKS = [
    ("canonical_contract", ["python", "pipelines/validate_canonical_contract.py"]),
    ("source_field_map", ["python", "pipelines/validate_source_field_map.py"]),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    results = []
    overall = 0
    for name, cmd in CHECKS:
        proc = subprocess.run(cmd, text=True, capture_output=True)
        result = {
            "name": name,
            "command": cmd,
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "passed": proc.returncode == 0,
        }
        results.append(result)
        if proc.returncode != 0:
            overall = 1
    payload = {
        "schema_version": 1,
        "audited_at_utc": now(),
        "passed": overall == 0,
        "checks": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"audit": str(OUT), "passed": overall == 0}, sort_keys=True))
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
