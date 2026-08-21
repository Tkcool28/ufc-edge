#!/usr/bin/env python3
"""Compact transport audit for the pinned Greco/UFCStats core tables.

This exists to keep canonical adapters based on observed raw syntax rather than guesses.
It reads only the pinned immutable snapshot and emits a small provenance artifact.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data/raw/greco1899"
OUT = ROOT / "provenance/audits/greco_core_transport_latest.json"


def latest_snapshot() -> Path:
    dirs = sorted(p for p in RAW_ROOT.iterdir() if p.is_dir())
    if not dirs:
        raise RuntimeError("No Greco snapshot")
    return dirs[-1]


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        yield from csv.DictReader(fh)


def top_values(path: Path, field: str, n: int = 30):
    c = Counter((r.get(field) or "<EMPTY>").strip() for r in rows(path))
    return [{"value": k, "count": v} for k, v in c.most_common(n)]


def sample(path: Path, n: int = 12):
    out = []
    for i, r in enumerate(rows(path)):
        if i >= n:
            break
        out.append(r)
    return out


def main() -> int:
    snap = latest_snapshot()
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "snapshot": snap.name,
        "fight_details_sample": sample(snap / "ufc_fight_details.csv"),
        "fight_results_sample": sample(snap / "ufc_fight_results.csv"),
        "fighter_details_sample": sample(snap / "ufc_fighter_details.csv"),
        "fighter_tott_sample": sample(snap / "ufc_fighter_tott.csv"),
        "event_details_sample": sample(snap / "ufc_event_details.csv"),
        "result_value_domains": {
            key: top_values(snap / "ufc_fight_results.csv", key)
            for key in ["OUTCOME", "WEIGHTCLASS", "METHOD", "ROUND", "TIME", "TIME FORMAT", "REFEREE"]
        },
        "tott_value_domains": {
            key: top_values(snap / "ufc_fighter_tott.csv", key)
            for key in ["HEIGHT", "WEIGHT", "REACH", "STANCE", "DOB"]
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"snapshot": snap.name, "output": str(OUT.relative_to(ROOT))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
