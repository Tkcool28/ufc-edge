#!/usr/bin/env python3
"""Audit the latest official UFC FightMetric snapshot before canonicalization.

This script is deliberately read-only with respect to raw data.  It answers three
questions with repository-resident evidence:

1. What does round=0 represent?
2. How complete is the rich FightMetric/TIP layer across the ordered source rows?
3. What identity/join material exists in the current Greco raw files?

It does *not* guess a FightMetric<->Greco crosswalk.  If no stable bridge is present,
that is reported as an unresolved dependency rather than falling back to names.
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FM_ROOT = Path("data/raw/ufc_fightmetric_official")
GRECO_ROOT = Path("data/raw/greco1899")
OUT_JSON = Path("provenance/audits/fightmetric_semantics_latest.json")
OUT_MD = Path("provenance/audits/fightmetric_semantics_latest.md")

TIME_FIELDS = [
    "standing_time", "neutral_time", "distance_time", "clinch_time", "ground_time",
    "control_time", "ground_ctl_time", "guard_ctl_time", "half_guard_ctl_time",
    "side_ctl_time", "mount_ctl_time", "back_ctl_time", "msc_ground_ctl__time",
]
COUNT_FIELDS = [
    "knock_down", "sig_str_att", "sig_str_land", "tot_str_att", "tot_str_land",
    "grap_take_att", "grap_take_land", "grap_sub_att", "grap_rev_land",
    "grap_stand_land", "dist_str_att", "dist_str_land", "clinch_str_att",
    "clinch_str_land", "ground_str_att", "ground_str_land",
]


def latest_dir(root: Path) -> Path:
    candidates = sorted(p for p in root.iterdir() if p.is_dir() and (p / "manifest.json").exists())
    if not candidates:
        raise RuntimeError(f"No complete snapshots under {root}")
    return candidates[-1]


def parse_time(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    text = str(value).strip()
    if re.fullmatch(r"\d+", text):
        return int(text)
    match = re.fullmatch(r"(\d+):(\d{1,2})", text)
    if match:
        return int(match.group(1)) * 60 + int(match.group(2))
    return None


def parse_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def load_fightmetric(snapshot: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in sorted((snapshot / "fight_stat").glob("page_*.json")):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data", []):
            attrs = item.get("attributes") if isinstance(item, dict) else None
            if isinstance(attrs, dict):
                rows.append(attrs)
    return rows


def field_sum_test(groups: dict[tuple[str, str], list[dict[str, Any]]], field: str, *, is_time: bool) -> dict[str, Any]:
    parser = parse_time if is_time else parse_number
    compared = exact = 0
    abs_diffs: list[float] = []
    examples: list[dict[str, Any]] = []
    missing_summary = incomplete_rounds = 0

    for (fid, color), rows in groups.items():
        summary_rows = [r for r in rows if str(r.get("round")) == "0"]
        actual = [r for r in rows if isinstance(r.get("round"), int) and r.get("round") >= 1]
        if len(summary_rows) != 1 or not actual:
            continue
        summary = parser(summary_rows[0].get(field))
        if summary is None:
            missing_summary += 1
            continue
        vals = [parser(r.get(field)) for r in actual]
        if any(v is None for v in vals):
            incomplete_rounds += 1
            continue
        expected = sum(v for v in vals if v is not None)
        diff = float(summary - expected)
        compared += 1
        abs_diffs.append(abs(diff))
        if abs(diff) < 1e-9:
            exact += 1
        elif len(examples) < 5:
            examples.append({
                "fightmetric_id": fid,
                "color": color,
                "summary": summary,
                "sum_rounds_1_plus": expected,
                "difference": diff,
                "rounds": [r.get("round") for r in actual],
            })
    return {
        "field": field,
        "kind": "time_seconds" if is_time else "count",
        "groups_compared": compared,
        "exact_matches": exact,
        "exact_match_fraction": exact / compared if compared else None,
        "mean_absolute_difference": sum(abs_diffs) / len(abs_diffs) if abs_diffs else None,
        "max_absolute_difference": max(abs_diffs) if abs_diffs else None,
        "missing_summary_groups": missing_summary,
        "incomplete_round_groups": incomplete_rounds,
        "mismatch_examples": examples,
    }


def ordered_coverage(rows: list[dict[str, Any]], field: str, bins: int = 12) -> list[dict[str, Any]]:
    ordered = sorted(
        [r for r in rows if isinstance(r.get("drupal_internal__id"), int)],
        key=lambda r: r["drupal_internal__id"],
    )
    if not ordered:
        return []
    size = math.ceil(len(ordered) / bins)
    out = []
    for start in range(0, len(ordered), size):
        chunk = ordered[start:start + size]
        nonnull = sum(1 for r in chunk if r.get(field) not in (None, ""))
        out.append({
            "row_start": start + 1,
            "row_end": start + len(chunk),
            "drupal_internal_id_min": chunk[0]["drupal_internal__id"],
            "drupal_internal_id_max": chunk[-1]["drupal_internal__id"],
            "rows": len(chunk),
            "nonnull": nonnull,
            "nonnull_fraction": nonnull / len(chunk),
        })
    return out


def inspect_greco(root: Path) -> dict[str, Any]:
    snapshot = latest_dir(root)
    files = {}
    stable_id_candidates: set[str] = set()
    for path in sorted(snapshot.glob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            sample = []
            for idx, row in enumerate(reader):
                if idx < 3:
                    sample.append({k: row.get(k) for k in headers})
                if idx >= 3:
                    break
        candidates = [
            h for h in headers
            if any(token in h.lower() for token in ("url", "id", "link", "fighter", "event", "fight"))
        ]
        stable_id_candidates.update(candidates)
        files[path.name] = {
            "headers": headers,
            "identity_candidate_columns": candidates,
            "first_rows": sample,
        }
    return {
        "snapshot": snapshot.as_posix(),
        "files": files,
        "identity_candidate_columns_union": sorted(stable_id_candidates),
        "policy": "Candidate columns are inventory only; no display-name-only crosswalk is authorized.",
    }


def main() -> int:
    snapshot = latest_dir(FM_ROOT)
    rows = load_fightmetric(snapshot)
    usable = [r for r in rows if r.get("fightmetric_id") not in (None, "") and r.get("color") not in (None, "")]
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in usable:
        groups[(str(row["fightmetric_id"]), str(row["color"]))].append(row)

    round_counts = Counter(str(r.get("round")) for r in usable if r.get("round") is not None)
    group_shape_counts = Counter()
    for members in groups.values():
        rounds = tuple(sorted(int(r["round"]) for r in members if isinstance(r.get("round"), int)))
        group_shape_counts[rounds] += 1

    tests = [field_sum_test(groups, f, is_time=False) for f in COUNT_FIELDS]
    tests += [field_sum_test(groups, f, is_time=True) for f in TIME_FIELDS]
    decisive = [t for t in tests if (t["groups_compared"] or 0) >= 100 and t["exact_match_fraction"] is not None]
    near_unanimous = [t for t in decisive if t["exact_match_fraction"] >= 0.995]
    round0_summary_supported = bool(decisive) and len(near_unanimous) / len(decisive) >= 0.8

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "fightmetric_snapshot": snapshot.as_posix(),
        "rows_total": len(rows),
        "rows_with_fightmetric_id_and_color": len(usable),
        "distinct_fightmetric_color_groups": len(groups),
        "round_counts_usable": dict(sorted(round_counts.items(), key=lambda kv: int(kv[0]))),
        "most_common_round_shapes": [
            {"rounds": list(shape), "groups": count}
            for shape, count in group_shape_counts.most_common(20)
        ],
        "round0_semantics": {
            "hypothesis": "round=0 is a per-fighter fight-total/summary row whose additive fields equal the sum of rounds 1+.",
            "supported_by_additivity_tests": round0_summary_supported,
            "decision_rule": "Supported only if >=80% of well-powered tested additive fields match exactly in >=99.5% of comparable groups.",
            "decisive_fields": len(decisive),
            "near_unanimous_fields": len(near_unanimous),
            "field_tests": tests,
            "canonicalization_rule_if_supported": "Exclude round=0 from fighter-round tables; preserve separately as source-provided fight summary and verify against derived fight totals.",
        },
        "ordered_source_coverage": {
            "warning": "Drupal internal ID order is not calendar time. These bins locate coverage transitions only; year/era labeling requires a fight/date identity bridge.",
            "control_time": ordered_coverage(usable, "control_time"),
            "guard_ctl_time": ordered_coverage(usable, "guard_ctl_time"),
            "sig_str_att": ordered_coverage(usable, "sig_str_att"),
        },
        "greco_inventory": inspect_greco(GRECO_ROOT),
        "identity_status": {
            "crosswalk_created": False,
            "reason": "FightMetric rows contain fightmetric_id/color but no fighter/date attributes. A stable official fight/athlete bridge must be acquired before matching to Greco.",
            "prohibited_fallback": "Do not join by display name alone.",
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Official UFC FightMetric semantics audit",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Snapshot: `{report['fightmetric_snapshot']}`",
        "",
        "## Round 0",
        "",
        f"Additivity verdict: **{'SUPPORTED' if round0_summary_supported else 'NOT YET SUPPORTED'}**.",
        f"Decisive fields: {len(decisive)}; near-unanimous exact fields: {len(near_unanimous)}.",
        "",
        "| Field | Compared groups | Exact fraction | Mean abs diff |",
        "|---|---:|---:|---:|",
    ]
    for t in tests:
        frac = t["exact_match_fraction"]
        if t["groups_compared"]:
            lines.append(f"| {t['field']} | {t['groups_compared']} | {frac:.6f} | {t['mean_absolute_difference']:.4f} |")
    lines += [
        "",
        "## Identity status",
        "",
        "No FightMetric↔Greco crosswalk is asserted by this audit. FightMetric rows have fightmetric ID + corner but no fighter/date identity. The next acquisition step is an official fight-node bridge; display-name-only matching remains prohibited.",
        "",
        "## Coverage-order warning",
        "",
        "The JSON report includes coverage by Drupal internal-ID bins to locate where rich fields turn on/off. Those bins are **not calendar eras**. Calendar-year coverage must wait for a verified fight/date identity bridge.",
        "",
        "## Greco identity inventory",
        "",
        f"Pinned raw snapshot: `{report['greco_inventory']['snapshot']}`",
        "",
    ]
    for name, info in report["greco_inventory"]["files"].items():
        lines.append(f"- `{name}` identity candidates: {', '.join(info['identity_candidate_columns']) or '(none)' }")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}; round0_summary_supported={round0_summary_supported}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
