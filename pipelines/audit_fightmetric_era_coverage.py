#!/usr/bin/env python3
"""Measure official UFC FightMetric field coverage by calendar year/era.

Only high-confidence joins are used:
1) direct one-to-one UFC fight node <-> FightMetric ID candidates; and
2) direct unique UFC event.relationships.fights membership with a parsed event date.

Coverage for actual rounds (round>=1) is reported separately from source fight-summary
rows (round=0). This matters because simulator availability must never be inferred from
summary-row population.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CROSSWALK = Path("data/derived/identity/ufc_fightmetric_fight_crosswalk_candidate.csv")
EVENT_BRIDGE = Path("data/derived/identity/ufc_fight_event_bridge_candidate.csv")
FM_ROOT = Path("data/raw/ufc_fightmetric_official")
OUT_JSON = Path("provenance/audits/fightmetric_era_coverage_latest.json")
OUT_MD = Path("provenance/audits/fightmetric_era_coverage_latest.md")
OUT_CSV = Path("data/derived/coverage/fightmetric_coverage_by_year.csv")

COUNT_FIELDS = [
    "knock_down", "sig_str_att", "sig_str_land", "tot_str_att", "tot_str_land",
    "grap_take_att", "grap_take_land", "grap_sub_att", "grap_rev_land", "grap_stand_land",
    "head_sig_str_att", "head_sig_str_land", "body_sig_str_att", "body_sig_str_land",
    "legs_sig_str_att", "legs_sig_str_land", "dist_str_att", "dist_str_land",
    "clinch_sig_str_att", "clinch_sig_str_land", "ground_sig_str_att", "ground_sig_str_land",
]
TIP_FIELDS = [
    "standing_time", "neutral_time", "distance_time", "clinch_time", "ground_time",
    "control_time", "ground_ctl_time", "guard_ctl_time", "half_guard_ctl_time",
    "side_ctl_time", "mount_ctl_time", "back_ctl_time", "msc_ground_ctl__time",
]
FIELDS = COUNT_FIELDS + TIP_FIELDS


def latest_manifest() -> Path:
    xs = sorted(FM_ROOT.glob("*/manifest.json"))
    if not xs:
        raise RuntimeError("No FightMetric manifest")
    return xs[-1]


def fight_stat_pages(manifest_path: Path) -> list[Path]:
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages: list[Path] = []
    for block in m.get("collections") or []:
        if not isinstance(block, dict) or block.get("collection") != "fight_stat":
            continue
        for info in block.get("files") or []:
            raw = info.get("path") or info.get("destination")
            if raw:
                pages.append(Path(str(raw)))
    if not pages:
        raise RuntimeError("Could not resolve fight_stat pages")
    return pages


def present(value: Any) -> bool:
    return value is not None and value != ""


def era(year: int) -> str:
    if year <= 2006:
        return "1993-2006"
    if year <= 2012:
        return "2007-2012"
    if year <= 2018:
        return "2013-2018"
    if year <= 2022:
        return "2019-2022"
    return "2023-present"


def empty_bucket() -> dict[str, Any]:
    return {
        "fight_ids": set(),
        "actual_round_rows": 0,
        "summary_rows": 0,
        "actual_seen": Counter(),
        "actual_nonnull": Counter(),
        "summary_seen": Counter(),
        "summary_nonnull": Counter(),
    }


def fractions(nonnull: Counter[str], seen: Counter[str]) -> dict[str, float | None]:
    return {field: (nonnull[field] / seen[field]) if seen[field] else None for field in FIELDS}


def main() -> int:
    by_uuid_fmid: dict[str, int] = {}
    with CROSSWALK.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            by_uuid_fmid[row["ufc_fight_uuid"]] = int(row["fightmetric_id"])

    dated_fmid: dict[int, dict[str, str]] = {}
    duplicate_dated_fmid: set[int] = set()
    with EVENT_BRIDGE.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            uid = row["ufc_fight_uuid"]
            if uid not in by_uuid_fmid or not row.get("event_date"):
                continue
            fmid = by_uuid_fmid[uid]
            if fmid in dated_fmid and dated_fmid[fmid]["ufc_fight_uuid"] != uid:
                duplicate_dated_fmid.add(fmid)
            dated_fmid[fmid] = {
                "ufc_fight_uuid": uid,
                "event_date": row["event_date"],
                "event_name": row.get("event_name") or "",
            }
    for fmid in duplicate_dated_fmid:
        dated_fmid.pop(fmid, None)

    years: dict[int, dict[str, Any]] = defaultdict(empty_bucket)
    unmatched_stat_ids: set[int] = set()
    matched_actual = matched_summary = 0

    for page in fight_stat_pages(latest_manifest()):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            try:
                fmid = int(attrs.get("fightmetric_id"))
            except (TypeError, ValueError):
                continue
            if fmid not in dated_fmid:
                unmatched_stat_ids.add(fmid)
                continue
            try:
                rnd = int(attrs.get("round"))
            except (TypeError, ValueError):
                continue
            year = int(dated_fmid[fmid]["event_date"][:4])
            bucket = years[year]
            bucket["fight_ids"].add(fmid)
            if rnd == 0:
                bucket["summary_rows"] += 1
                matched_summary += 1
                seen_key, nonnull_key = "summary_seen", "summary_nonnull"
            elif rnd >= 1:
                bucket["actual_round_rows"] += 1
                matched_actual += 1
                seen_key, nonnull_key = "actual_seen", "actual_nonnull"
            else:
                continue
            for field in FIELDS:
                bucket[seen_key][field] += 1
                if present(attrs.get(field)):
                    bucket[nonnull_key][field] += 1

    if not years:
        raise RuntimeError("No dated FightMetric rows available")

    era_acc: dict[str, dict[str, Any]] = defaultdict(empty_bucket)
    rows: list[dict[str, Any]] = []
    for year in sorted(years):
        b = years[year]
        actual_frac = fractions(b["actual_nonnull"], b["actual_seen"])
        summary_frac = fractions(b["summary_nonnull"], b["summary_seen"])
        row: dict[str, Any] = {
            "year": year,
            "fights": len(b["fight_ids"]),
            "actual_round_rows": b["actual_round_rows"],
            "summary_rows": b["summary_rows"],
        }
        for field in FIELDS:
            row[f"actual_{field}_nonnull_fraction"] = actual_frac[field]
            row[f"summary_{field}_nonnull_fraction"] = summary_frac[field]
        rows.append(row)

        ea = era_acc[era(year)]
        ea["fight_ids"].update(b["fight_ids"])
        ea["actual_round_rows"] += b["actual_round_rows"]
        ea["summary_rows"] += b["summary_rows"]
        ea["actual_seen"].update(b["actual_seen"])
        ea["actual_nonnull"].update(b["actual_nonnull"])
        ea["summary_seen"].update(b["summary_seen"])
        ea["summary_nonnull"].update(b["summary_nonnull"])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    era_report: dict[str, Any] = {}
    for e, b in era_acc.items():
        era_report[e] = {
            "fights": len(b["fight_ids"]),
            "actual_round_rows": b["actual_round_rows"],
            "summary_rows": b["summary_rows"],
            "actual_round_field_nonnull_fraction": fractions(b["actual_nonnull"], b["actual_seen"]),
            "summary_field_nonnull_fraction": fractions(b["summary_nonnull"], b["summary_seen"]),
        }

    first_actual_year = {}
    first_actual_year_90pct = {}
    for field in FIELDS:
        ys = [r["year"] for r in rows if (r.get(f"actual_{field}_nonnull_fraction") or 0) > 0]
        ys90 = [r["year"] for r in rows if (r.get(f"actual_{field}_nonnull_fraction") or 0) >= 0.90]
        first_actual_year[field] = min(ys) if ys else None
        first_actual_year_90pct[field] = min(ys90) if ys90 else None

    report = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "high_confidence_dated_fightmetric_ids": len(dated_fmid),
        "duplicate_dated_ids_excluded": len(duplicate_dated_fmid),
        "matched_actual_round_rows": matched_actual,
        "matched_round_zero_summary_rows": matched_summary,
        "stat_ids_without_high_confidence_date": len(unmatched_stat_ids),
        "year_min": min(years),
        "year_max": max(years),
        "years": rows,
        "eras": era_report,
        "first_year_with_nonnull_actual_round_field": first_actual_year,
        "first_year_with_90pct_actual_round_field": first_actual_year_90pct,
        "tip_fields": TIP_FIELDS,
        "count_fields": COUNT_FIELDS,
        "year_csv": OUT_CSV.as_posix(),
        "semantics": {
            "actual_round_coverage_is_primary_for_simulator_availability": True,
            "round_zero_summary_coverage_reported_separately": True,
            "round_zero_not_counted_as_actual_round": True,
            "join_gate": "direct one-to-one UFC fightmetric_id + unique direct UFC event membership + parsed official event date",
            "ambiguous_rows_inferred": False,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Official UFC FightMetric calendar-era coverage",
        "",
        f"High-confidence dated FightMetric IDs: **{len(dated_fmid)}**",
        f"Calendar span: **{min(years)}–{max(years)}**",
        f"Actual round rows: **{matched_actual}**",
        f"Round-0 summary rows: **{matched_summary}**",
        "",
        "The table below uses **actual rounds only**.",
        "",
        "| Era | Fights | Round rows | distance | clinch | ground_time | ground_ctl | guard_ctl | mount_ctl | back_ctl |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for e in ["1993-2006", "2007-2012", "2013-2018", "2019-2022", "2023-present"]:
        if e not in era_report:
            continue
        x = era_report[e]
        f = x["actual_round_field_nonnull_fraction"]
        lines.append(
            f"| {e} | {x['fights']} | {x['actual_round_rows']} | {f['distance_time']:.3f} | {f['clinch_time']:.3f} | {f['ground_time']:.3f} | {f['ground_ctl_time']:.3f} | {f['guard_ctl_time']:.3f} | {f['mount_ctl_time']:.3f} | {f['back_ctl_time']:.3f} |"
        )
    lines += ["", "Round-0 summary coverage is retained separately in the JSON. Ambiguous joins are excluded rather than inferred."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"dated_ids": len(dated_fmid), "actual_rows": matched_actual, "summary_rows": matched_summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
