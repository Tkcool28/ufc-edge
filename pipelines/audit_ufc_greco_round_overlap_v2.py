#!/usr/bin/env python3
"""Conservative official UFC FightMetric ↔ Greco/UFCStats round-stat audit.

Only stable/direct identity evidence is used before comparing stats:
1. unique official UFC fight -> FightMetric ID candidate;
2. unique official event membership/date candidate;
3. direct red/blue official athlete UUIDs -> official athlete names;
4. exact normalized unordered fighter pair + exact date -> exactly one Greco bout.

No fuzzy global fighter matching is used. Duplicate FightMetric source versions are
reported separately and are never silently deduplicated.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.data.manifest_readers import (  # noqa: E402
    chunked_snapshot_page_paths,
    latest_complete_snapshot,
    latest_manifest,
    manifest_page_paths,
)
from ufc_edge.data.parsing import landed_attempted, mmss_to_seconds, nonnegative_int, round_number  # noqa: E402

CROSSWALK = ROOT / "data/derived/identity/ufc_fightmetric_fight_crosswalk_candidate.csv"
EVENT_BRIDGE = ROOT / "data/derived/identity/ufc_fight_event_bridge_candidate.csv"
UFC_FIGHT_ROOT = ROOT / "data/raw/ufc_com_resources/fights"
UFC_ATHLETE_ROOT = ROOT / "data/raw/ufc_com_resources/athletes"
FM_ROOT = ROOT / "data/raw/ufc_fightmetric_official"
GRECO_ROOT = ROOT / "data/raw/greco1899"

OUT_JSON = ROOT / "provenance/audits/ufc_greco_round_overlap_latest.json"
OUT_MD = ROOT / "provenance/audits/ufc_greco_round_overlap_latest.md"
OUT_ALIGN = ROOT / "data/derived/identity/ufc_greco_fight_alignment_candidate.csv"
OUT_DUP = ROOT / "data/derived/qa/fightmetric_duplicate_version_greco_scores.csv"

FIELD_MAP = {
    "knock_down": "KD",
    "sig_str_land": "SIG.STR.",
    "sig_str_att": "SIG.STR.",
    "tot_str_land": "TOTAL STR.",
    "tot_str_att": "TOTAL STR.",
    "grap_take_land": "TD",
    "grap_take_att": "TD",
    "grap_sub_att": "SUB.ATT",
    "grap_rev_land": "REV.",
    "control_time": "CTRL",
    "head_sig_str_land": "HEAD",
    "head_sig_str_att": "HEAD",
    "body_sig_str_land": "BODY",
    "body_sig_str_att": "BODY",
    "legs_sig_str_land": "LEG",
    "legs_sig_str_att": "LEG",
    "dist_str_land": "DISTANCE",
    "dist_str_att": "DISTANCE",
    "clinch_sig_str_land": "CLINCH",
    "clinch_sig_str_att": "CLINCH",
    "ground_sig_str_land": "GROUND",
    "ground_sig_str_att": "GROUND",
}
PAIR_LANDED = {name for name in FIELD_MAP if name.endswith("_land")}
PAIR_ATTEMPTED = {name for name in FIELD_MAP if name.endswith("_att")}


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def parse_date(value: str) -> str:
    text = value.strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Unrecognized date: {value!r}")


def rel_id(item: dict[str, Any], name: str) -> str | None:
    rels = item.get("relationships") if isinstance(item.get("relationships"), dict) else {}
    rel = rels.get(name)
    data = rel.get("data") if isinstance(rel, dict) else None
    if isinstance(data, dict) and data.get("id") is not None:
        return str(data["id"])
    return None


def official_value(field: str, value: Any) -> int | None:
    if value in (None, ""):
        return None
    if field == "control_time":
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        parsed = mmss_to_seconds(value)
        return None if parsed is None else int(parsed)
    parsed = nonnegative_int(value)
    return None if parsed is None else int(parsed)


def greco_value(field: str, row: dict[str, str]) -> int | None:
    source = FIELD_MAP[field]
    raw = row.get(source)
    if source == "CTRL":
        parsed = mmss_to_seconds(raw)
        return None if parsed is None else int(parsed)
    if source in {"KD", "SUB.ATT", "REV."}:
        parsed = nonnegative_int(raw)
        return None if parsed is None else int(parsed)
    pair = landed_attempted(raw)
    if pair is None:
        return None
    landed, attempted = pair
    if field in PAIR_LANDED:
        return landed
    if field in PAIR_ATTEMPTED:
        return attempted
    raise RuntimeError(f"No pair component rule for {field}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_crosswalk() -> dict[str, int]:
    out: dict[str, int] = {}
    seen_fmid: set[int] = set()
    for row in read_csv(CROSSWALK):
        uid = (row.get("ufc_fight_uuid") or "").strip()
        fmid_raw = (row.get("fightmetric_id") or "").strip()
        if not uid or not fmid_raw:
            continue
        fmid = int(fmid_raw)
        if uid in out or fmid in seen_fmid:
            raise RuntimeError("Candidate crosswalk is not one-to-one as promised")
        out[uid] = fmid
        seen_fmid.add(fmid)
    if not out:
        raise RuntimeError("Empty FightMetric candidate crosswalk")
    return out


def load_unique_event_bridge() -> tuple[dict[str, dict[str, str]], int]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(EVENT_BRIDGE):
        uid = (row.get("ufc_fight_uuid") or "").strip()
        if uid and row.get("event_date"):
            grouped[uid].append(row)

    unique: dict[str, dict[str, str]] = {}
    ambiguous = 0
    for uid, rows in grouped.items():
        signatures = {
            ((row.get("event_uuid") or "").strip(), (row.get("event_date") or "").strip())
            for row in rows
        }
        if len(signatures) != 1:
            ambiguous += 1
            continue
        unique[uid] = rows[0]
    return unique, ambiguous


def load_athlete_names() -> dict[str, str]:
    snapshot = latest_complete_snapshot(UFC_ATHLETE_ROOT)
    names: dict[str, str] = {}
    for page in manifest_page_paths(snapshot / "manifest.json"):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            name = attrs.get("title") or attrs.get("name")
            if name not in (None, ""):
                names[str(item["id"])] = str(name).strip()
    if not names:
        raise RuntimeError("No official athlete names loaded")
    return names


def load_official_fights(crosswalk: dict[str, int], events: dict[str, dict[str, str]], names: dict[str, str]) -> dict[str, dict[str, Any]]:
    snapshot = latest_complete_snapshot(UFC_FIGHT_ROOT)
    out: dict[str, dict[str, Any]] = {}
    for page in chunked_snapshot_page_paths(snapshot):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            uid = str(item["id"])
            if uid not in crosswalk or uid not in events:
                continue
            red_uid = rel_id(item, "red_corner")
            blue_uid = rel_id(item, "blue_corner")
            if not red_uid or not blue_uid or red_uid not in names or blue_uid not in names:
                continue
            out[uid] = {
                "fightmetric_id": crosswalk[uid],
                "event_date": events[uid]["event_date"],
                "event_name": events[uid].get("event_name") or "",
                "red_uid": red_uid,
                "blue_uid": blue_uid,
                "red_name": names[red_uid],
                "blue_name": names[blue_uid],
            }
    return out


def load_greco() -> tuple[dict[tuple[str, str], list[dict[str, str]]], dict[tuple[str, tuple[str, str]], list[tuple[str, str]]]]:
    greco_dir = sorted(p for p in GRECO_ROOT.iterdir() if p.is_dir())[-1]
    event_dates: dict[str, str] = {}
    for row in read_csv(greco_dir / "ufc_event_details.csv"):
        if row.get("EVENT") and row.get("DATE"):
            event_dates[row["EVENT"]] = parse_date(row["DATE"])

    bouts: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(greco_dir / "ufc_fight_stats.csv"):
        if row.get("EVENT") and row.get("BOUT"):
            bouts[(row["EVENT"], row["BOUT"])].append(row)

    index: dict[tuple[str, tuple[str, str]], list[tuple[str, str]]] = defaultdict(list)
    for key, rows in bouts.items():
        event, _ = key
        event_date = event_dates.get(event)
        if not event_date:
            continue
        fighter_names = sorted({str(r.get("FIGHTER") or "").strip() for r in rows if r.get("FIGHTER")})
        if len(fighter_names) != 2:
            continue
        pair = tuple(sorted(normalize_name(name) for name in fighter_names))
        if pair[0] == pair[1]:
            continue
        index[(event_date, pair)].append(key)
    return bouts, index


def build_alignments(official: dict[str, dict[str, Any]], greco_index: dict[tuple[str, tuple[str, str]], list[tuple[str, str]]]) -> tuple[list[dict[str, Any]], int, int]:
    rows: list[dict[str, Any]] = []
    no_match = ambiguous = 0
    for uid, info in official.items():
        pair = tuple(sorted((normalize_name(info["red_name"]), normalize_name(info["blue_name"]))))
        candidates = greco_index.get((info["event_date"], pair), [])
        if not candidates:
            no_match += 1
            continue
        if len(candidates) != 1:
            ambiguous += 1
            continue
        event, bout = candidates[0]
        rows.append(
            {
                "ufc_fight_uuid": uid,
                "fightmetric_id": info["fightmetric_id"],
                "event_date": info["event_date"],
                "ufc_event_name": info["event_name"],
                "red_athlete_uuid": info["red_uid"],
                "blue_athlete_uuid": info["blue_uid"],
                "red_name": info["red_name"],
                "blue_name": info["blue_name"],
                "greco_event": event,
                "greco_bout": bout,
            }
        )
    return rows, no_match, ambiguous


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    crosswalk = load_crosswalk()
    event_bridge, event_ambiguous = load_unique_event_bridge()
    athlete_names = load_athlete_names()
    official = load_official_fights(crosswalk, event_bridge, athlete_names)
    greco_bouts, greco_index = load_greco()
    alignments, no_exact_pair, ambiguous_greco = build_alignments(official, greco_index)

    align_fields = [
        "ufc_fight_uuid", "fightmetric_id", "event_date", "ufc_event_name",
        "red_athlete_uuid", "blue_athlete_uuid", "red_name", "blue_name",
        "greco_event", "greco_bout",
    ]
    write_csv(OUT_ALIGN, alignments, align_fields)

    # Build Greco lookup at exact fight/color/actual-round grain.
    greco_lookup: dict[tuple[int, str, int], dict[str, str]] = {}
    for alignment in alignments:
        fmid = int(alignment["fightmetric_id"])
        bout_key = (str(alignment["greco_event"]), str(alignment["greco_bout"]))
        color_by_name = {
            normalize_name(str(alignment["red_name"])): "red",
            normalize_name(str(alignment["blue_name"])): "blue",
        }
        for row in greco_bouts[bout_key]:
            color = color_by_name.get(normalize_name(str(row.get("FIGHTER") or "")))
            if not color:
                continue
            try:
                rnd = round_number(row.get("ROUND"))
            except ValueError:
                continue
            if rnd is None:
                continue
            key = (fmid, color, int(rnd))
            if key in greco_lookup:
                raise RuntimeError(f"Duplicate Greco fighter-round key after exact fight alignment: {key}")
            greco_lookup[key] = row

    fm_manifest = latest_manifest(FM_ROOT)
    fm_versions: dict[tuple[int, str, int], list[dict[str, Any]]] = defaultdict(list)
    for page in manifest_page_paths(fm_manifest, collection="fight_stat"):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            fmid = nonnegative_int(attrs.get("fightmetric_id"))
            raw_round = attrs.get("round")
            try:
                rnd = round_number(raw_round)
            except ValueError:
                continue  # round=0 summaries intentionally excluded
            color = str(attrs.get("color") or "").lower()
            if fmid is None or rnd is None or color not in {"red", "blue"}:
                continue
            key = (int(fmid), color, int(rnd))
            if key not in greco_lookup:
                continue
            fm_versions[key].append({"resource_id": item.get("id"), "attrs": attrs})

    field_total: Counter[str] = Counter()
    field_exact: Counter[str] = Counter()
    field_abs_error: Counter[str] = Counter()
    single_keys = multi_keys = 0
    duplicate_rows: list[dict[str, Any]] = []
    newest_strict_best = newest_tied_best = newest_not_best = 0

    for key, versions in fm_versions.items():
        greco_row = greco_lookup[key]
        if len(versions) == 1:
            single_keys += 1
            attrs = versions[0]["attrs"]
            for field in FIELD_MAP:
                try:
                    official_val = official_value(field, attrs.get(field))
                    greco_val = greco_value(field, greco_row)
                except ValueError:
                    continue
                if official_val is None or greco_val is None:
                    continue
                field_total[field] += 1
                field_abs_error[field] += abs(official_val - greco_val)
                if official_val == greco_val:
                    field_exact[field] += 1
            continue

        multi_keys += 1
        scored: list[dict[str, Any]] = []
        for version in versions:
            attrs = version["attrs"]
            exact = compared = abs_error = 0
            for field in FIELD_MAP:
                try:
                    official_val = official_value(field, attrs.get(field))
                    greco_val = greco_value(field, greco_row)
                except ValueError:
                    continue
                if official_val is None or greco_val is None:
                    continue
                compared += 1
                abs_error += abs(official_val - greco_val)
                exact += int(official_val == greco_val)
            scored.append(
                {
                    "fightmetric_id": key[0],
                    "color": key[1],
                    "round": key[2],
                    "resource_id": version["resource_id"],
                    "drupal_internal_id": attrs.get("drupal_internal__id"),
                    "compared_fields": compared,
                    "exact_fields": exact,
                    "absolute_error_sum": abs_error,
                }
            )
        duplicate_rows.extend(scored)
        if scored:
            def score(row: dict[str, Any]) -> tuple[int, int, int]:
                return (int(row["exact_fields"]), -int(row["absolute_error_sum"]), int(row["compared_fields"]))

            best_score = max(score(row) for row in scored)
            best = [row for row in scored if score(row) == best_score]
            newest = max(scored, key=lambda row: int(row["drupal_internal_id"] or -1))
            if score(newest) == best_score:
                if len(best) == 1:
                    newest_strict_best += 1
                else:
                    newest_tied_best += 1
            else:
                newest_not_best += 1

    dup_fields = [
        "fightmetric_id", "color", "round", "resource_id", "drupal_internal_id",
        "compared_fields", "exact_fields", "absolute_error_sum",
    ]
    write_csv(OUT_DUP, duplicate_rows, dup_fields)

    field_report: dict[str, dict[str, float | int | None]] = {}
    for field in FIELD_MAP:
        total = int(field_total[field])
        exact = int(field_exact[field])
        field_report[field] = {
            "comparisons": total,
            "exact": exact,
            "exact_fraction": exact / total if total else None,
            "mean_absolute_error": field_abs_error[field] / total if total else None,
        }

    report = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "identity_inputs": {
            "one_to_one_ufc_fightmetric_crosswalk_rows": len(crosswalk),
            "unique_event_bridge_rows": len(event_bridge),
            "ambiguous_event_memberships_excluded": event_ambiguous,
            "official_fights_with_direct_identity_date_and_both_athletes": len(official),
        },
        "greco_alignment": {
            "aligned_fights": len(alignments),
            "no_exact_date_pair_match": no_exact_pair,
            "ambiguous_exact_greco_matches": ambiguous_greco,
            "aligned_fighter_round_keys": len(greco_lookup),
        },
        "fightmetric_comparison": {
            "matched_fighter_round_keys": len(fm_versions),
            "single_version_keys": single_keys,
            "multi_version_keys": multi_keys,
            "field_agreement_single_version_keys": field_report,
        },
        "duplicate_version_evidence": {
            "newest_strict_best_keys": newest_strict_best,
            "newest_tied_best_keys": newest_tied_best,
            "newest_not_best_keys": newest_not_best,
            "version_score_csv": OUT_DUP.relative_to(ROOT).as_posix(),
            "rule": "Duplicate source versions remain unresolved; this audit scores them against Greco but does not select a canonical version automatically.",
        },
        "outputs": {
            "fight_alignment_csv": OUT_ALIGN.relative_to(ROOT).as_posix(),
            "duplicate_version_score_csv": OUT_DUP.relative_to(ROOT).as_posix(),
        },
        "decision": {
            "comparison_completed": True,
            "automatic_source_winner_selected": False,
            "name_only_global_matching_used": False,
            "rule": "Shared-field agreement is QA evidence for source ownership. Canonical source precedence must be documented separately and may be field/era-specific.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Official UFC FightMetric vs Greco/UFCStats round audit",
        "",
        f"- Exact conservative fight alignments: **{len(alignments)}**",
        f"- Matched fighter-round keys: **{len(fm_versions)}**",
        f"- Single-version keys: **{single_keys}**",
        f"- Multi-version keys: **{multi_keys}**",
        "",
        "## Shared-field exact agreement on uncontested FightMetric keys",
        "",
    ]
    for field, values in field_report.items():
        fraction = values["exact_fraction"]
        pct = "n/a" if fraction is None else f"{100 * float(fraction):.3f}%"
        lines.append(f"- `{field}`: {values['exact']}/{values['comparisons']} exact ({pct})")
    lines += [
        "",
        "## Duplicate FightMetric versions",
        "",
        f"- Newest version strictly best vs Greco: **{newest_strict_best}** keys",
        f"- Newest version tied for best: **{newest_tied_best}** keys",
        f"- Newest version not best: **{newest_not_best}** keys",
        "",
        "No duplicate version is automatically selected by this audit.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"aligned_fights": len(alignments), "single_keys": single_keys, "multi_keys": multi_keys}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
