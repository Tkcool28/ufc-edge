#!/usr/bin/env python3
"""Characterize conflicting duplicate official FightMetric source rows.

A duplicate is the same (fightmetric_id, color, round) with multiple Drupal rows.
The audit measures whether higher Drupal internal IDs look like richer/corrected source
versions, but deliberately does not select a winner unless the evidence is sufficient.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("data/raw/ufc_fightmetric_official")
OUT_JSON = Path("provenance/audits/fightmetric_duplicate_versions_latest.json")
OUT_MD = Path("provenance/audits/fightmetric_duplicate_versions_latest.md")
TIP_FIELDS = {
    "standing_time", "neutral_time", "distance_time", "clinch_time", "ground_time",
    "control_time", "ground_ctl_time", "guard_ctl_time", "half_guard_ctl_time",
    "side_ctl_time", "mount_ctl_time", "back_ctl_time", "msc_ground_ctl__time",
}
META = {"drupal_internal__id", "fightmetric_id", "round", "color", "metatag"}


def latest_complete() -> Path:
    candidates = sorted(p for p in ROOT.iterdir() if p.is_dir() and (p / "manifest.json").exists())
    if not candidates:
        raise RuntimeError("No complete FightMetric snapshot")
    return candidates[-1]


def load_rows(snapshot: Path) -> list[dict[str, Any]]:
    rows = []
    for page in sorted((snapshot / "fight_stat").glob("page_*.json")):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data", []):
            attrs = item.get("attributes") if isinstance(item, dict) else None
            if isinstance(attrs, dict) and attrs.get("fightmetric_id") not in (None, "") and attrs.get("color") not in (None, "") and isinstance(attrs.get("round"), int):
                rows.append(attrs)
    return rows


def nonnull_metric_count(row: dict[str, Any]) -> int:
    return sum(1 for k, v in row.items() if k not in META and v not in (None, ""))


def tip_count(row: dict[str, Any]) -> int:
    return sum(1 for k in TIP_FIELDS if row.get(k) not in (None, ""))


def diff_fields(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    keys = set(a) | set(b)
    return sorted(
        k for k in keys
        if k not in META and json.dumps(a.get(k), sort_keys=True, default=str) != json.dumps(b.get(k), sort_keys=True, default=str)
    )


def main() -> int:
    snapshot = latest_complete()
    rows = load_rows(snapshot)
    keyed: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        keyed[(str(row["fightmetric_id"]), str(row["color"]), int(row["round"]))].append(row)

    duplicates = {k: v for k, v in keyed.items() if len(v) > 1}
    size_counts = Counter(len(v) for v in duplicates.values())
    relation = Counter()
    tip_relation = Counter()
    changed_field_counts = Counter()
    duplicated_fids = Counter(k[0] for k in duplicates)
    newer_iids = []
    older_iids = []
    examples = []

    for (fid, color, rnd), versions in sorted(duplicates.items()):
        ordered = sorted(versions, key=lambda r: int(r.get("drupal_internal__id") or -1))
        oldest, newest = ordered[0], ordered[-1]
        old_count = nonnull_metric_count(oldest)
        new_count = nonnull_metric_count(newest)
        if new_count > old_count:
            relation["newest_more_nonnull"] += 1
        elif new_count == old_count:
            relation["newest_equal_nonnull"] += 1
        else:
            relation["newest_less_nonnull"] += 1
        old_tip = tip_count(oldest)
        new_tip = tip_count(newest)
        if new_tip > old_tip:
            tip_relation["newest_more_tip"] += 1
        elif new_tip == old_tip:
            tip_relation["newest_equal_tip"] += 1
        else:
            tip_relation["newest_less_tip"] += 1
        changed = diff_fields(oldest, newest)
        changed_field_counts.update(changed)
        older_iids.append(int(oldest.get("drupal_internal__id") or -1))
        newer_iids.append(int(newest.get("drupal_internal__id") or -1))
        if len(examples) < 30:
            examples.append({
                "fightmetric_id": fid,
                "color": color,
                "round": rnd,
                "version_count": len(versions),
                "oldest_drupal_internal_id": oldest.get("drupal_internal__id"),
                "newest_drupal_internal_id": newest.get("drupal_internal__id"),
                "oldest_nonnull_metric_fields": old_count,
                "newest_nonnull_metric_fields": new_count,
                "oldest_tip_fields": old_tip,
                "newest_tip_fields": new_tip,
                "changed_field_count": len(changed),
                "changed_fields": changed[:60],
            })

    total = len(duplicates)
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "snapshot": snapshot.as_posix(),
        "duplicate_keys": total,
        "duplicate_version_count_distribution": dict(sorted(size_counts.items())),
        "distinct_fightmetric_ids_with_duplicates": len(duplicated_fids),
        "duplicate_keys_per_fightmetric_id_top": duplicated_fids.most_common(30),
        "newest_vs_oldest_nonnull": dict(relation),
        "newest_vs_oldest_tip": dict(tip_relation),
        "oldest_internal_id_min": min(older_iids) if older_iids else None,
        "oldest_internal_id_max": max(older_iids) if older_iids else None,
        "newest_internal_id_min": min(newer_iids) if newer_iids else None,
        "newest_internal_id_max": max(newer_iids) if newer_iids else None,
        "most_frequently_changed_fields": changed_field_counts.most_common(80),
        "examples": examples,
        "selection_status": {
            "canonical_version_rule_frozen": False,
            "reason": "Drupal internal ID ordering is evidence of source insertion/version order, not by itself proof that highest ID is the authoritative corrected row. Cross-source comparison against Greco and official fight identity is required before selecting a version.",
            "fail_closed_rule": "Preserve all conflicting source rows until a version-selection rule is validated; never arbitrary first/last-row dedupe.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def pct(n: int) -> str:
        return f"{(n / total * 100):.2f}%" if total else "n/a"

    lines = [
        "# Official UFC FightMetric duplicate-version audit",
        "",
        f"Snapshot: `{snapshot}`",
        f"Conflicting fighter/round keys: **{total}** across **{len(duplicated_fids)} FightMetric fight IDs**.",
        "",
        "## Newest Drupal row vs oldest row",
        "",
        f"- More non-null metric fields: {relation['newest_more_nonnull']} ({pct(relation['newest_more_nonnull'])})",
        f"- Equal non-null metric fields: {relation['newest_equal_nonnull']} ({pct(relation['newest_equal_nonnull'])})",
        f"- Fewer non-null metric fields: {relation['newest_less_nonnull']} ({pct(relation['newest_less_nonnull'])})",
        f"- More TIP fields: {tip_relation['newest_more_tip']} ({pct(tip_relation['newest_more_tip'])})",
        f"- Equal TIP fields: {tip_relation['newest_equal_tip']} ({pct(tip_relation['newest_equal_tip'])})",
        f"- Fewer TIP fields: {tip_relation['newest_less_tip']} ({pct(tip_relation['newest_less_tip'])})",
        "",
        "## Decision",
        "",
        "**No automatic newest-row-wins rule is frozen yet.** Drupal internal-ID ordering is useful version evidence, but the duplicated rows must be tied to actual fights and cross-checked against Greco/shared statistics before one version is selected for canonical use.",
        "",
        "The raw contract remains fail-closed: preserve every conflicting row; never arbitrary first/last-row dedupe.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote duplicate-version audit: keys={total}, fights={len(duplicated_fids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
