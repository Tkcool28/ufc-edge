#!/usr/bin/env python3
"""Separate dominant round-scale UFC FightMetric time values from sparse anomalies."""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ufc_edge.data.manifest_readers import latest_manifest, manifest_page_paths  # noqa: E402

FM_ROOT = ROOT / "data/raw/ufc_fightmetric_official"
OUT = ROOT / "provenance/audits/fightmetric_position_time_quality_latest.json"
FIELDS = [
    "standing_time", "neutral_time", "distance_time", "clinch_time", "ground_time",
    "control_time", "ground_ctl_time", "guard_ctl_time", "half_guard_ctl_time",
    "side_ctl_time", "mount_ctl_time", "back_ctl_time", "msc_ground_ctl__time",
]


def main() -> int:
    manifest = latest_manifest(FM_ROOT)
    per_field = {f: Counter() for f in FIELDS}
    outlier_examples = []
    clean_relation = Counter()
    clean_ground_relation = Counter()
    rows = 0

    for page in manifest_page_paths(manifest, collection="fight_stat"):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            try:
                rnd = int(attrs.get("round"))
            except (TypeError, ValueError):
                continue
            if rnd < 1 or attrs.get("fightmetric_id") in (None, ""):
                continue
            rows += 1
            vals = {}
            row_outliers = {}
            for field in FIELDS:
                raw = attrs.get(field)
                if raw in (None, ""):
                    vals[field] = None
                    per_field[field]["missing"] += 1
                    continue
                try:
                    val = int(raw)
                except (TypeError, ValueError):
                    vals[field] = None
                    per_field[field]["noninteger"] += 1
                    continue
                vals[field] = val
                per_field[field]["nonnull"] += 1
                if 0 <= val <= 5:
                    per_field[field]["roundscale_0_5"] += 1
                elif val > 5:
                    per_field[field]["gt_5"] += 1
                    row_outliers[field] = val
                else:
                    per_field[field]["negative"] += 1
                    row_outliers[field] = val
            if row_outliers and len(outlier_examples) < 100:
                outlier_examples.append({
                    "resource_id": item.get("id"),
                    "fightmetric_id": attrs.get("fightmetric_id"),
                    "drupal_internal__id": attrs.get("drupal_internal__id"),
                    "round": rnd,
                    "color": attrs.get("color"),
                    "outlier_fields": row_outliers,
                    "all_time_fields": {f: attrs.get(f) for f in FIELDS},
                })

            # Internal relationships only where all participating values are clean 0..5 buckets.
            s, d, c = vals["standing_time"], vals["distance_time"], vals["clinch_time"]
            if all(v is not None and 0 <= v <= 5 for v in (s, d, c)):
                clean_relation[int(s) - int(d) - int(c)] += 1
            gctl = vals["ground_ctl_time"]
            parts = [vals[x] for x in ("guard_ctl_time", "half_guard_ctl_time", "side_ctl_time", "mount_ctl_time", "back_ctl_time", "msc_ground_ctl__time")]
            if gctl is not None and 0 <= gctl <= 5 and all(v is not None and 0 <= v <= 5 for v in parts):
                clean_ground_relation[int(gctl) - sum(int(v) for v in parts)] += 1

    field_summary = {}
    min_roundscale_fraction = 1.0
    for field, counts in per_field.items():
        nonnull = counts["nonnull"]
        fraction = counts["roundscale_0_5"] / nonnull if nonnull else None
        if fraction is not None:
            min_roundscale_fraction = min(min_roundscale_fraction, fraction)
        field_summary[field] = {**dict(counts), "roundscale_0_5_fraction_of_nonnull": fraction}

    relation_n = sum(clean_relation.values())
    relation_close = sum(v for k, v in clean_relation.items() if abs(k) <= 1)
    ground_n = sum(clean_ground_relation.values())
    ground_close = sum(v for k, v in clean_ground_relation.items() if abs(k) <= 1)

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "identified_actual_round_rows": rows,
        "fields": field_summary,
        "minimum_roundscale_fraction_across_fields": min_roundscale_fraction,
        "clean_0_5_internal_relationships": {
            "standing_minus_distance_plus_clinch": {
                "comparisons": relation_n,
                "difference_counts": dict(sorted(clean_relation.items())),
                "within_one_bucket_fraction": relation_close / relation_n if relation_n else None,
            },
            "ground_control_minus_subposition_sum": {
                "comparisons": ground_n,
                "difference_counts": dict(sorted(clean_ground_relation.items())),
                "within_one_bucket_fraction": ground_close / ground_n if ground_n else None,
            },
        },
        "outlier_examples": outlier_examples,
        "decision": {
            "dominant_0_5_bucket_encoding": min_roundscale_fraction >= 0.99,
            "gt_5_values_canonical_eligible": False,
            "canonical_seconds_promoted": False,
            "rule": "Treat >5 values in actual-round positional time fields as source anomalies pending independent proof. Preserve all raw rows; future adapters may expose clean 0-5 coarse buckets separately, but must never synthesize seconds.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
