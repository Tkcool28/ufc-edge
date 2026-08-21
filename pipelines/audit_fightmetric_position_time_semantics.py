#!/usr/bin/env python3
"""Characterize official UFC FightMetric positional `_time` fields.

This audit does not convert archived integers into seconds. It determines whether the
position-time family behaves like a common coarse whole-minute bucket representation and
records internal partition relationships. Precise control seconds remain owned by Greco.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.data.manifest_readers import latest_manifest, manifest_page_paths  # noqa: E402

FM_ROOT = ROOT / "data/raw/ufc_fightmetric_official"
CONTROL_AUDIT = ROOT / "provenance/audits/ufc_greco_round_overlap_latest.json"
OUT = ROOT / "provenance/audits/fightmetric_position_time_semantics_latest.json"

FIELDS = [
    "standing_time", "neutral_time", "distance_time", "clinch_time", "ground_time",
    "control_time", "ground_ctl_time", "guard_ctl_time", "half_guard_ctl_time",
    "side_ctl_time", "mount_ctl_time", "back_ctl_time", "msc_ground_ctl__time",
]


def as_int(value: Any) -> int | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        out = int(value)
    except (TypeError, ValueError):
        return None
    return out if str(out) == str(value) or isinstance(value, int) else None


def main() -> int:
    manifest = latest_manifest(FM_ROOT)
    stats = {f: {"nonnull": 0, "noninteger": 0, "negative": 0, "values": Counter()} for f in FIELDS}
    actual_rows = 0
    identified_actual_rows = 0
    standing_partition = Counter()
    ground_control_partition = Counter()
    exposure_sum = Counter()

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
            if rnd < 1:
                continue
            actual_rows += 1
            if attrs.get("fightmetric_id") not in (None, ""):
                identified_actual_rows += 1

            vals: dict[str, int | None] = {}
            for field in FIELDS:
                raw = attrs.get(field)
                if raw in (None, ""):
                    vals[field] = None
                    continue
                stats[field]["nonnull"] += 1
                value = as_int(raw)
                if value is None:
                    stats[field]["noninteger"] += 1
                    vals[field] = None
                    continue
                if value < 0:
                    stats[field]["negative"] += 1
                stats[field]["values"][value] += 1
                vals[field] = value

            standing = vals["standing_time"]
            distance = vals["distance_time"]
            clinch = vals["clinch_time"]
            ground = vals["ground_time"]
            if None not in (standing, distance, clinch):
                diff = int(standing) - (int(distance) + int(clinch))
                standing_partition[diff] += 1
            if None not in (standing, ground):
                exposure_sum[int(standing) + int(ground)] += 1

            ground_ctl = vals["ground_ctl_time"]
            parts = [vals[x] for x in ("guard_ctl_time", "half_guard_ctl_time", "side_ctl_time", "mount_ctl_time", "back_ctl_time", "msc_ground_ctl__time")]
            if ground_ctl is not None and all(v is not None for v in parts):
                diff = int(ground_ctl) - sum(int(v) for v in parts if v is not None)
                ground_control_partition[diff] += 1

    prior_control = json.loads(CONTROL_AUDIT.read_text(encoding="utf-8"))
    control_candidates = prior_control.get("archived_control_time_semantics", {}).get("candidate_tests", {})
    floor_test = control_candidates.get("raw_equals_floor_minutes", {}) if isinstance(control_candidates, dict) else {}
    floor_fraction = floor_test.get("match_fraction")

    field_summary = {}
    all_integer_nonnegative = True
    all_bounded_roundscale = True
    for field, block in stats.items():
        values: Counter = block.pop("values")
        total = sum(values.values())
        minimum = min(values) if values else None
        maximum = max(values) if values else None
        if block["noninteger"] or block["negative"]:
            all_integer_nonnegative = False
        if maximum is not None and maximum > 5:
            all_bounded_roundscale = False
        field_summary[field] = {
            **block,
            "integer_values": total,
            "min": minimum,
            "max": maximum,
            "top_values": [{"value": k, "rows": v} for k, v in values.most_common(12)],
        }

    standing_n = sum(standing_partition.values())
    standing_close = sum(v for k, v in standing_partition.items() if abs(k) <= 1)
    ground_n = sum(ground_control_partition.values())
    ground_close = sum(v for k, v in ground_control_partition.items() if abs(k) <= 1)

    strong_family_evidence = (
        all_integer_nonnegative
        and all_bounded_roundscale
        and isinstance(floor_fraction, (int, float))
        and floor_fraction >= 0.95
        and standing_n >= 10000
        and standing_close / standing_n >= 0.95
    )

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "fightmetric_manifest": str(manifest.relative_to(ROOT)),
        "actual_round_rows": actual_rows,
        "identified_actual_round_rows": identified_actual_rows,
        "fields": field_summary,
        "internal_relationships": {
            "standing_minus_distance_plus_clinch": {
                "comparisons": standing_n,
                "difference_counts": dict(sorted(standing_partition.items())),
                "within_one_bucket_fraction": standing_close / standing_n if standing_n else None,
            },
            "ground_control_minus_subposition_sum": {
                "comparisons": ground_n,
                "difference_counts": dict(sorted(ground_control_partition.items())),
                "within_one_bucket_fraction": ground_close / ground_n if ground_n else None,
            },
            "standing_plus_ground_bucket_sum_distribution": dict(sorted(exposure_sum.items())),
        },
        "cross_source_control_evidence": {
            "source_audit": str(CONTROL_AUDIT.relative_to(ROOT)),
            "raw_equals_floor_minutes": floor_test,
        },
        "decision": {
            "family_behaves_like_coarse_whole_minute_buckets": strong_family_evidence,
            "canonical_seconds_promoted": False,
            "rule": (
                "Even if the family behaves like whole-minute truncated buckets, preserve the official raw integers. "
                "Do not reconstruct seconds. Greco remains the precise control-second source; other positional fields "
                "may be used later only with their coarse resolution explicitly represented."
            ),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
