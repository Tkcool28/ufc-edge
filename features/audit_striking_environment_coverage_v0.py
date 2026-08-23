#!/usr/bin/env python3
"""Audit temporal/non-null coverage for Feature Family A without changing features."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "features/v0/striking_environment.csv"
ENV_MANIFEST = ROOT / "features/v0/striking_environment_manifest.json"
OUT = ROOT / "features/v0/striking_environment_coverage_by_year.csv"
AUDIT = ROOT / "provenance/audits/striking_environment_coverage_v0_latest.json"

KEY_FEATURES = [
    "career_sig_attempts_per_min",
    "career_sig_landed_per_min",
    "career_sig_absorbed_per_min",
    "career_sig_accuracy",
    "career_sig_defense",
    "career_head_landed_per_min",
    "career_head_absorbed_per_min",
    "career_knockdowns_per_15",
    "career_knockdowns_suffered_per_15",
    "career_distance_attempt_share",
    "career_clinch_attempt_share",
    "career_ground_attempt_share",
    "recent3_sig_attempts_per_min",
    "recent3_sig_landed_per_min",
    "recent3_sig_absorbed_per_min",
    "recent3_knockdowns_per_15",
    "ewm365_sig_attempts_per_min",
    "ewm365_sig_landed_per_min",
    "ewm365_sig_absorbed_per_min",
    "ewm365_knockdowns_per_15",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not ENV.is_file() or not ENV_MANIFEST.is_file():
        raise RuntimeError("striking environment outputs are not materialized")
    manifest = json.loads(ENV_MANIFEST.read_text(encoding="utf-8"))
    declared = next((x for x in manifest.get("files", []) if x.get("path") == "features/v0/striking_environment.csv"), None)
    if not declared or declared.get("sha256") != sha256(ENV):
        raise RuntimeError("striking environment hash does not match manifest")
    rows = read_csv(ENV)
    if not rows:
        raise RuntimeError("empty striking environment")
    missing = sorted(set(KEY_FEATURES) - set(rows[0]))
    if missing:
        raise RuntimeError(f"key feature columns missing: {missing}")

    by_year: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        year = int(row["target_event_date"][:4])
        by_year[year].append(row)

    fields = ["target_year", "rows"] + [f"{name}_nonnull" for name in KEY_FEATURES] + [f"{name}_coverage" for name in KEY_FEATURES]
    output_rows = []
    overall_counts = {name: 0 for name in KEY_FEATURES}
    for year in sorted(by_year):
        group = by_year[year]
        out = {"target_year": year, "rows": len(group)}
        for name in KEY_FEATURES:
            nonnull = sum(row[name] != "" for row in group)
            overall_counts[name] += nonnull
            out[f"{name}_nonnull"] = nonnull
            out[f"{name}_coverage"] = nonnull / len(group)
        output_rows.append(out)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for row in output_rows:
            formatted = {}
            for field in fields:
                value = row[field]
                formatted[field] = f"{value:.6f}" if isinstance(value, float) else value
            writer.writerow(formatted)

    overall = {
        name: {
            "nonnull": overall_counts[name],
            "rows": len(rows),
            "coverage": round(overall_counts[name] / len(rows), 6),
        }
        for name in KEY_FEATURES
    }
    audit = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "striking_environment_sha256": sha256(ENV),
        "rows": len(rows),
        "target_year_min": min(by_year),
        "target_year_max": max(by_year),
        "years": len(by_year),
        "key_feature_coverage": overall,
        "output": str(OUT.relative_to(ROOT)),
        "output_sha256": sha256(OUT),
        "rule": "Coverage is descriptive QA only. No row is dropped and no missing feature is imputed by this audit.",
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "years": len(by_year), "coverage": overall}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
