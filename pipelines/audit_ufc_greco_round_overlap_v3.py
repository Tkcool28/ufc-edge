#!/usr/bin/env python3
"""Reconcile official UFC FightMetric round stats against Greco/UFCStats.

Inputs are already conservative identity evidence:
- exact official UFC -> FightMetric one-to-one candidate crosswalk;
- exact event/date + official athlete-name -> unique Greco fight alignment;
- audited FightMetric numeric corner mapping (0=red, 1=blue).

Count fields are compared directly. Archived FightMetric ``control_time`` is deliberately
NOT assumed to be seconds; several candidate unit/quantization interpretations are tested
against Greco CTRL before any canonical time mapping can be promoted.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.data.manifest_readers import latest_manifest, manifest_page_paths  # noqa: E402
from ufc_edge.data.parsing import landed_attempted, mmss_to_seconds, nonnegative_int, round_number  # noqa: E402

ALIGN = ROOT / "data/derived/identity/ufc_greco_fight_alignment_candidate.csv"
COLOR_AUDIT = ROOT / "provenance/audits/fightmetric_color_semantics_latest.json"
FM_ROOT = ROOT / "data/raw/ufc_fightmetric_official"
GRECO_ROOT = ROOT / "data/raw/greco1899"
OUT_JSON = ROOT / "provenance/audits/ufc_greco_round_overlap_latest.json"
OUT_MD = ROOT / "provenance/audits/ufc_greco_round_overlap_latest.md"
OUT_DUP = ROOT / "data/derived/qa/fightmetric_duplicate_version_greco_scores.csv"

COUNT_FIELDS = {
    "knock_down": ("KD", "scalar"),
    "sig_str_land": ("SIG.STR.", "landed"),
    "sig_str_att": ("SIG.STR.", "attempted"),
    "tot_str_land": ("TOTAL STR.", "landed"),
    "tot_str_att": ("TOTAL STR.", "attempted"),
    "grap_take_land": ("TD", "landed"),
    "grap_take_att": ("TD", "attempted"),
    "grap_sub_att": ("SUB.ATT", "scalar"),
    "grap_rev_land": ("REV.", "scalar"),
    "head_sig_str_land": ("HEAD", "landed"),
    "head_sig_str_att": ("HEAD", "attempted"),
    "body_sig_str_land": ("BODY", "landed"),
    "body_sig_str_att": ("BODY", "attempted"),
    "legs_sig_str_land": ("LEG", "landed"),
    "legs_sig_str_att": ("LEG", "attempted"),
    "dist_str_land": ("DISTANCE", "landed"),
    "dist_str_att": ("DISTANCE", "attempted"),
    "clinch_sig_str_land": ("CLINCH", "landed"),
    "clinch_sig_str_att": ("CLINCH", "attempted"),
    "ground_sig_str_land": ("GROUND", "landed"),
    "ground_sig_str_att": ("GROUND", "attempted"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_color_map() -> dict[int, str]:
    payload = json.loads(COLOR_AUDIT.read_text(encoding="utf-8"))
    decision = payload.get("decision") if isinstance(payload, dict) else None
    if not isinstance(decision, dict) or decision.get("mapping_promoted") is not True:
        raise RuntimeError("FightMetric numeric corner semantics are not promoted")
    raw = decision.get("numeric_to_corner")
    if not isinstance(raw, dict):
        raise RuntimeError("Promoted color audit lacks numeric_to_corner mapping")
    mapping = {int(k): str(v) for k, v in raw.items()}
    if mapping != {0: "red", 1: "blue"}:
        raise RuntimeError(f"Unexpected promoted FightMetric color map: {mapping}")
    return mapping


def greco_count(field: str, row: dict[str, str]) -> int | None:
    source, component = COUNT_FIELDS[field]
    raw = row.get(source)
    if component == "scalar":
        parsed = nonnegative_int(raw)
        return None if parsed is None else int(parsed)
    pair = landed_attempted(raw)
    if pair is None:
        return None
    return pair[0] if component == "landed" else pair[1]


def official_count(value: Any) -> int | None:
    parsed = nonnegative_int(value)
    return None if parsed is None else int(parsed)


def main() -> int:
    color_map = load_color_map()
    alignments = read_csv(ALIGN)
    if not alignments:
        raise RuntimeError("Missing/empty exact UFC-Greco fight alignment")

    greco_dir = sorted(p for p in GRECO_ROOT.iterdir() if p.is_dir())[-1]
    bout_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(greco_dir / "ufc_fight_stats.csv"):
        if row.get("EVENT") and row.get("BOUT"):
            bout_rows[(row["EVENT"], row["BOUT"])].append(row)

    greco: dict[tuple[int, str, int], dict[str, str]] = {}
    for a in alignments:
        fmid = int(a["fightmetric_id"])
        semantic_by_name = {
            str(a["red_name"]).strip(): "red",
            str(a["blue_name"]).strip(): "blue",
        }
        # Exact names were already used to create this alignment. Permit only those two.
        for row in bout_rows.get((a["greco_event"], a["greco_bout"]), []):
            fighter = str(row.get("FIGHTER") or "").strip()
            corner = semantic_by_name.get(fighter)
            if not corner:
                # Alignment generation normalized names, so recover only if exactly one
                # corner's display string becomes equal after ASCII-alnum normalization.
                import re, unicodedata
                def norm(x: str) -> str:
                    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode("ascii").lower())
                matches = [c for n, c in semantic_by_name.items() if norm(n) == norm(fighter)]
                if len(matches) != 1:
                    continue
                corner = matches[0]
            try:
                rnd = round_number(row.get("ROUND"))
            except ValueError:
                continue
            if rnd is None:
                continue
            key = (fmid, corner, int(rnd))
            if key in greco:
                raise RuntimeError(f"Duplicate Greco aligned fighter-round key: {key}")
            greco[key] = row

    fm: dict[tuple[int, str, int], list[dict[str, Any]]] = defaultdict(list)
    fm_manifest = latest_manifest(FM_ROOT)
    observed_numeric_colors: Counter[int] = Counter()
    for page in manifest_page_paths(fm_manifest, collection="fight_stat"):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            fmid = nonnegative_int(attrs.get("fightmetric_id"))
            try:
                rnd = round_number(attrs.get("round"))
            except ValueError:
                continue  # round=0 and malformed summaries excluded
            raw_color = attrs.get("color")
            if isinstance(raw_color, bool):
                continue
            try:
                numeric_color = int(raw_color)
            except (TypeError, ValueError):
                continue
            if fmid is None or rnd is None or numeric_color not in color_map:
                continue
            observed_numeric_colors[numeric_color] += 1
            key = (int(fmid), color_map[numeric_color], int(rnd))
            if key not in greco:
                continue
            fm[key].append({"resource_id": item.get("id"), "attrs": attrs})

    field_total: Counter[str] = Counter()
    field_exact: Counter[str] = Counter()
    field_abs_error: Counter[str] = Counter()
    single_keys = multi_keys = 0

    # Control-time unit/quantization candidates. These are semantic tests, not transforms.
    control_tests: dict[str, Counter[str]] = {
        name: Counter() for name in (
            "raw_equals_seconds",
            "raw_times_60_equals_seconds",
            "raw_equals_floor_minutes",
            "raw_equals_nearest_minute",
            "raw_equals_ceil_minutes",
        )
    }

    duplicate_rows: list[dict[str, Any]] = []
    newest_strict_best = newest_tied_best = newest_not_best = 0

    def score_version(attrs: dict[str, Any], grow: dict[str, str]) -> tuple[int, int, int]:
        exact = compared = abs_error = 0
        for field in COUNT_FIELDS:
            oval = official_count(attrs.get(field))
            try:
                gval = greco_count(field, grow)
            except ValueError:
                continue
            if oval is None or gval is None:
                continue
            compared += 1
            exact += int(oval == gval)
            abs_error += abs(oval - gval)
        return exact, abs_error, compared

    for key, versions in fm.items():
        grow = greco[key]
        if len(versions) == 1:
            single_keys += 1
            attrs = versions[0]["attrs"]
            for field in COUNT_FIELDS:
                oval = official_count(attrs.get(field))
                try:
                    gval = greco_count(field, grow)
                except ValueError:
                    continue
                if oval is None or gval is None:
                    continue
                field_total[field] += 1
                field_exact[field] += int(oval == gval)
                field_abs_error[field] += abs(oval - gval)

            raw_control = attrs.get("control_time")
            try:
                raw_control_int = None if raw_control in (None, "") else int(raw_control)
            except (TypeError, ValueError):
                raw_control_int = None
            try:
                greco_sec = mmss_to_seconds(grow.get("CTRL"))
            except ValueError:
                greco_sec = None
            if raw_control_int is not None and greco_sec is not None:
                candidates = {
                    "raw_equals_seconds": raw_control_int == greco_sec,
                    "raw_times_60_equals_seconds": raw_control_int * 60 == greco_sec,
                    "raw_equals_floor_minutes": raw_control_int == greco_sec // 60,
                    "raw_equals_nearest_minute": raw_control_int == int(math.floor(greco_sec / 60 + 0.5)),
                    "raw_equals_ceil_minutes": raw_control_int == int(math.ceil(greco_sec / 60)),
                }
                for name, matched in candidates.items():
                    control_tests[name]["comparisons"] += 1
                    control_tests[name]["matches"] += int(matched)
            continue

        multi_keys += 1
        scored: list[dict[str, Any]] = []
        for version in versions:
            exact, abs_error, compared = score_version(version["attrs"], grow)
            attrs = version["attrs"]
            scored.append({
                "fightmetric_id": key[0],
                "corner": key[1],
                "round": key[2],
                "resource_id": version["resource_id"],
                "drupal_internal_id": attrs.get("drupal_internal__id"),
                "compared_fields": compared,
                "exact_fields": exact,
                "absolute_error_sum": abs_error,
            })
        duplicate_rows.extend(scored)
        if scored:
            def ranking(row: dict[str, Any]) -> tuple[int, int, int]:
                return (int(row["exact_fields"]), -int(row["absolute_error_sum"]), int(row["compared_fields"]))
            best_score = max(ranking(row) for row in scored)
            best = [row for row in scored if ranking(row) == best_score]
            newest = max(scored, key=lambda row: int(row["drupal_internal_id"] or -1))
            if ranking(newest) == best_score:
                if len(best) == 1:
                    newest_strict_best += 1
                else:
                    newest_tied_best += 1
            else:
                newest_not_best += 1

    OUT_DUP.parent.mkdir(parents=True, exist_ok=True)
    dup_fields = [
        "fightmetric_id", "corner", "round", "resource_id", "drupal_internal_id",
        "compared_fields", "exact_fields", "absolute_error_sum",
    ]
    with OUT_DUP.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=dup_fields)
        writer.writeheader(); writer.writerows(duplicate_rows)

    field_report: dict[str, dict[str, float | int | None]] = {}
    for field in COUNT_FIELDS:
        total = int(field_total[field]); exact = int(field_exact[field])
        field_report[field] = {
            "comparisons": total,
            "exact": exact,
            "exact_fraction": exact / total if total else None,
            "mean_absolute_error": field_abs_error[field] / total if total else None,
        }

    control_report: dict[str, dict[str, int | float | None]] = {}
    for name, counts in control_tests.items():
        comparisons = int(counts["comparisons"]); matches = int(counts["matches"])
        control_report[name] = {
            "comparisons": comparisons,
            "matches": matches,
            "match_fraction": matches / comparisons if comparisons else None,
        }

    report = {
        "schema_version": 3,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "identity": {
            "aligned_fights": len(alignments),
            "aligned_greco_fighter_round_keys": len(greco),
            "matched_fightmetric_fighter_round_keys": len(fm),
            "audited_numeric_corner_map": {str(k): v for k, v in color_map.items()},
            "observed_numeric_color_counts": dict(sorted(observed_numeric_colors.items())),
        },
        "count_stat_comparison": {
            "single_version_keys": single_keys,
            "multi_version_keys": multi_keys,
            "field_agreement_single_version_keys": field_report,
        },
        "archived_control_time_semantics": {
            "candidate_tests": control_report,
            "canonical_seconds_mapping_promoted": False,
            "rule": "No archived FightMetric time field is mapped to canonical seconds until a unit/quantization interpretation is explicitly promoted by a separate semantic decision.",
        },
        "duplicate_version_evidence": {
            "newest_strict_best_keys": newest_strict_best,
            "newest_tied_best_keys": newest_tied_best,
            "newest_not_best_keys": newest_not_best,
            "version_score_csv": OUT_DUP.relative_to(ROOT).as_posix(),
            "automatic_version_selection": False,
        },
        "decision": {
            "comparison_completed": True,
            "automatic_source_winner_selected": False,
            "automatic_duplicate_version_selected": False,
            "name_only_global_matching_used": False,
            "note": "Count-stat agreement is source QA evidence. Archived TIP time semantics remain separate and unresolved until unit audit is complete.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Official UFC FightMetric vs Greco/UFCStats round audit",
        "",
        f"- Exact aligned fights: **{len(alignments)}**",
        f"- Matched fighter-round keys: **{len(fm)}**",
        f"- Single-version keys: **{single_keys}**",
        f"- Multi-version keys: **{multi_keys}**",
        "",
        "## Shared count-field agreement",
        "",
    ]
    for field, values in field_report.items():
        frac = values["exact_fraction"]
        pct = "n/a" if frac is None else f"{100 * float(frac):.3f}%"
        lines.append(f"- `{field}`: {values['exact']}/{values['comparisons']} exact ({pct})")
    lines += ["", "## Archived `control_time` candidate semantics", ""]
    for name, values in control_report.items():
        frac = values["match_fraction"]
        pct = "n/a" if frac is None else f"{100 * float(frac):.3f}%"
        lines.append(f"- `{name}`: {values['matches']}/{values['comparisons']} ({pct})")
    lines += [
        "",
        "No FightMetric time-unit mapping and no duplicate-version selection are automatically promoted by this audit.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"matched_keys": len(fm), "single": single_keys, "multi": multi_keys}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
