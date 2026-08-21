#!/usr/bin/env python3
"""Cross-check official UFC FightMetric round stats against pinned Greco/UFCStats rows.

Fight alignment is deliberately conservative:
- direct one-to-one official UFC fight -> FightMetric ID candidate;
- direct unique official UFC fight -> event/date bridge;
- official UFC red/blue athlete UUID -> official athlete display name;
- exact normalized unordered fighter pair + exact event date -> exactly one Greco bout.

No fuzzy global name matching is used. For FightMetric fighter/round keys with multiple
source rows, every version is scored against Greco; no winner is silently selected.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CROSSWALK = Path("data/derived/identity/ufc_fightmetric_fight_crosswalk_candidate.csv")
EVENT_BRIDGE = Path("data/derived/identity/ufc_fight_event_bridge_candidate.csv")
UFC_FIGHT_ROOT = Path("data/raw/ufc_com_resources/fights")
UFC_ATHLETE_ROOT = Path("data/raw/ufc_com_resources/athletes")
FM_ROOT = Path("data/raw/ufc_fightmetric_official")
GRECO_ROOT = Path("data/raw/greco1899")
OUT_JSON = Path("provenance/audits/ufc_greco_round_overlap_latest.json")
OUT_MD = Path("provenance/audits/ufc_greco_round_overlap_latest.md")
OUT_ALIGN = Path("data/derived/identity/ufc_greco_fight_alignment_candidate.csv")
OUT_DUP = Path("data/derived/qa/fightmetric_duplicate_version_greco_scores.csv")

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
PAIR_LANDED = {k for k in FIELD_MAP if k.endswith("_land") or k.endswith("_landed")}
PAIR_ATT = {k for k in FIELD_MAP if k.endswith("_att") or k.endswith("_attempted")}


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


def parse_pair(value: str) -> tuple[int, int]:
    m = re.fullmatch(r"\s*(\d+)\s+of\s+(\d+)\s*", value or "", flags=re.I)
    if not m:
        raise ValueError(f"Bad landed/attempted cell: {value!r}")
    a, b = int(m.group(1)), int(m.group(2))
    if a > b:
        raise ValueError(f"Landed exceeds attempted: {value!r}")
    return a, b


def parse_mmss(value: str) -> int:
    parts = str(value).strip().split(":")
    if len(parts) == 2:
        m, s = map(int, parts)
        if s >= 60:
            raise ValueError(value)
        return 60 * m + s
    if len(parts) == 3:
        h, m, s = map(int, parts)
        if m >= 60 or s >= 60:
            raise ValueError(value)
        return 3600 * h + 60 * m + s
    raise ValueError(value)


def int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def official_value(field: str, value: Any) -> int | None:
    if value is None or value == "":
        return None
    if field == "control_time":
        if isinstance(value, (int, float)):
            return int(value)
        return parse_mmss(str(value))
    return int_or_none(value)


def greco_value(field: str, row: dict[str, str]) -> int | None:
    source = FIELD_MAP[field]
    value = row.get(source)
    if value is None or value == "" or value == "--":
        return None
    if source == "CTRL":
        return parse_mmss(value)
    if source in {"KD", "SUB.ATT", "REV."}:
        return int(value)
    landed, attempted = parse_pair(value)
    return landed if field in PAIR_LANDED else attempted


def latest_complete(root: Path) -> Path:
    for p in reversed(sorted(x for x in root.iterdir() if x.is_dir() and (x / "manifest.json").exists())):
        m = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
        if m.get("complete_collection_snapshot") is True or m.get("semantics", {}).get("complete_collection_snapshot") is True:
            return p
    raise RuntimeError(f"No complete snapshot under {root}")


def flat_pages(snapshot: Path) -> list[Path]:
    m = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    return [Path(str(x["path"])) for x in m.get("files", []) if isinstance(x, dict) and x.get("path")]


def chunk_pages(snapshot: Path) -> list[Path]:
    m = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    pages: list[Path] = []
    for cm_raw in m.get("chunk_manifests") or []:
        cm = json.loads(Path(str(cm_raw)).read_text(encoding="utf-8"))
        pages.extend(Path(str(x["path"])) for x in cm.get("files") or [])
    return pages


def fm_pages() -> list[Path]:
    manifests = sorted(FM_ROOT.glob("*/manifest.json"))
    if not manifests:
        raise RuntimeError("No FightMetric manifest")
    m = json.loads(manifests[-1].read_text(encoding="utf-8"))
    for block in m.get("collections") or []:
        if isinstance(block, dict) and block.get("collection") == "fight_stat":
            pages = [Path(str(x.get("path") or x.get("destination"))) for x in block.get("files") or []]
            if pages:
                return pages
    raise RuntimeError("No FightMetric fight_stat pages")


def rel_id(item: dict[str, Any], name: str) -> str | None:
    rel = (item.get("relationships") or {}).get(name)
    data = rel.get("data") if isinstance(rel, dict) else None
    return str(data.get("id")) if isinstance(data, dict) and data.get("id") is not None else None


def main() -> int:
    # Clean direct UFC fight -> FightMetric candidates.
    clean_fmid_by_uuid: dict[str, int] = {}
    with CROSSWALK.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            clean_fmid_by_uuid[row["ufc_fight_uuid"]] = int(row["fightmetric_id"])

    # Unique official event membership/date candidates.
    event_by_uuid: dict[str, dict[str, str]] = {}
    with EVENT_BRIDGE.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["ufc_fight_uuid"] in clean_fmid_by_uuid and row.get("event_date"):
                event_by_uuid[row["ufc_fight_uuid"]] = row

    # Official athlete names.
    athletes = latest_complete(UFC_ATHLETE_ROOT)
    athlete_name: dict[str, str] = {}
    for page in flat_pages(athletes):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            name = attrs.get("title") or attrs.get("name")
            if name:
                athlete_name[str(item["id"])] = str(name).strip()

    # Official fight identities with direct red/blue athlete relationships.
    fights = latest_complete(UFC_FIGHT_ROOT)
    official: dict[str, dict[str, Any]] = {}
    for page in chunk_pages(fights):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            uid = str(item["id"])
            if uid not in clean_fmid_by_uuid or uid not in event_by_uuid:
                continue
            red_uid, blue_uid = rel_id(item, "red_corner"), rel_id(item, "blue_corner")
            if not red_uid or not blue_uid or red_uid not in athlete_name or blue_uid not in athlete_name:
                continue
            official[uid] = {
                "fightmetric_id": clean_fmid_by_uuid[uid],
                "event_date": event_by_uuid[uid]["event_date"],
                "event_name": event_by_uuid[uid].get("event_name") or "",
                "red_uid": red_uid,
                "blue_uid": blue_uid,
                "red_name": athlete_name[red_uid],
                "blue_name": athlete_name[blue_uid],
            }

    # Greco event dates.
    greco_dir = sorted(x for x in GRECO_ROOT.iterdir() if x.is_dir())[-1]
    event_date: dict[str, str] = {}
    with (greco_dir / "ufc_event_details.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("EVENT") and row.get("DATE"):
                event_date[row["EVENT"]] = parse_date(row["DATE"])

    # Greco stats grouped by bout, then indexed by date+unordered exact normalized pair.
    greco_bouts: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    with (greco_dir / "ufc_fight_stats.csv").open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            greco_bouts[(row["EVENT"], row["BOUT"])].append(row)

    greco_index: dict[tuple[str, tuple[str, str]], list[tuple[str, str]]] = defaultdict(list)
    greco_fighters: dict[tuple[str, str], dict[str, str]] = {}
    for key, rows in greco_bouts.items():
        event, bout = key
        if event not in event_date:
            continue
        names = sorted({r["FIGHTER"].strip() for r in rows if r.get("FIGHTER")})
        if len(names) != 2:
            continue
        norm_map = {normalize_name(x): x for x in names}
        if len(norm_map) != 2:
            continue
        pair = tuple(sorted(norm_map))
        greco_index[(event_date[event], pair)].append(key)
        greco_fighters[key] = norm_map

    alignments: list[dict[str, Any]] = []
    no_exact_pair = 0
    ambiguous_greco = 0
    for uid, info in official.items():
        pair = tuple(sorted((normalize_name(info["red_name"]), normalize_name(info["blue_name"]))))
        candidates = greco_index.get((info["event_date"], pair), [])
        if not candidates:
            no_exact_pair += 1
            continue
        if len(candidates) != 1:
            ambiguous_greco += 1
            continue
        event, bout = candidates[0]
        alignments.append({
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
        })

    OUT_ALIGN.parent.mkdir(parents=True, exist_ok=True)
    align_fields = list(alignments[0]) if alignments else ["ufc_fight_uuid"]
    with OUT_ALIGN.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=align_fields)
        w.writeheader(); w.writerows(alignments)

    # Greco lookup per aligned fight/fighter/round.
    greco_lookup: dict[tuple[int, str, int], dict[str, str]] = {}
    fmid_color_name: dict[tuple[int, str], str] = {}
    for a in alignments:
        fmid = int(a["fightmetric_id"])
        key = (a["greco_event"], a["greco_bout"])
        norm_to_color = {normalize_name(a["red_name"]): "red", normalize_name(a["blue_name"]): "blue"}
        for row in greco_bouts[key]:
            norm = normalize_name(row["FIGHTER"])
            color = norm_to_color.get(norm)
            if not color:
                continue
            m = re.fullmatch(r"Round\s+(\d+)", row["ROUND"], re.I)
            if not m:
                continue
            rnd = int(m.group(1))
            greco_lookup[(fmid, color, rnd)] = row
            fmid_color_name[(fmid, color)] = row["FIGHTER"]

    # All FightMetric source versions by fight/color/actual round.
    fm_versions: dict[tuple[int, str, int], list[dict[str, Any]]] = defaultdict(list)
    for page in fm_pages():
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            fmid = int_or_none(attrs.get("fightmetric_id")); rnd = int_or_none(attrs.get("round"))
            color = str(attrs.get("color") or "").lower()
            if fmid is None or rnd is None or rnd < 1 or color not in {"red", "blue"}:
                continue
            if (fmid, color, rnd) not in greco_lookup:
                continue
            fm_versions[(fmid, color, rnd)].append({"resource_id": item.get("id"), "attrs": attrs})

    field_totals = Counter(); field_exact = Counter(); field_abs_error = Counter()
    keys_compared = 0; single_version_keys = 0; multi_version_keys = 0
    duplicate_unique_best = 0; duplicate_tied_best = 0
    duplicate_rows: list[dict[str, Any]] = []

    for key, versions in fm_versions.items():
        greco_row = greco_lookup[key]
        version_scores = []
        for version in versions:
            exact = compared = 0
            values = {}
            for field in FIELD_MAP:
                try:
                    g = greco_value(field, greco_row)
                    o = official_value(field, version["attrs"].get(field))
                except (ValueError, TypeError):
                    continue
                if g is None or o is None:
                    continue
                compared += 1
                is_exact = int(g == o)
                exact += is_exact
                values[field] = {"greco": g, "ufc": o, "exact": bool(is_exact)}
            version_scores.append({"resource_id": version["resource_id"], "exact": exact, "compared": compared, "values": values})

        if not version_scores:
            continue
        keys_compared += 1
        best_exact = max(x["exact"] for x in version_scores)
        best_compared = max(x["compared"] for x in version_scores if x["exact"] == best_exact)
        best = [x for x in version_scores if x["exact"] == best_exact and x["compared"] == best_compared]
        if len(versions) == 1:
            single_version_keys += 1
        else:
            multi_version_keys += 1
            if len(best) == 1:
                duplicate_unique_best += 1
            else:
                duplicate_tied_best += 1
            duplicate_rows.append({
                "fightmetric_id": key[0], "color": key[1], "round": key[2],
                "fighter": fmid_color_name.get((key[0], key[1]), ""),
                "version_count": len(versions), "best_count": len(best),
                "best_exact": best_exact, "best_compared": best_compared,
                "scores_json": json.dumps([{k: v for k, v in x.items() if k != "values"} for x in version_scores], sort_keys=True),
            })

        # Overall agreement uses the uniquely best version for duplicate keys; tied duplicate keys are excluded.
        chosen = version_scores[0] if len(versions) == 1 else (best[0] if len(best) == 1 else None)
        if chosen is None:
            continue
        for field, vals in chosen["values"].items():
            field_totals[field] += 1
            field_exact[field] += int(vals["exact"])
            field_abs_error[field] += abs(vals["ufc"] - vals["greco"])

    OUT_DUP.parent.mkdir(parents=True, exist_ok=True)
    dup_fields = ["fightmetric_id", "color", "round", "fighter", "version_count", "best_count", "best_exact", "best_compared", "scores_json"]
    with OUT_DUP.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=dup_fields); w.writeheader(); w.writerows(duplicate_rows)

    field_report = {
        field: {
            "comparisons": field_totals[field],
            "exact": field_exact[field],
            "exact_fraction": field_exact[field] / field_totals[field] if field_totals[field] else None,
            "mean_abs_error": field_abs_error[field] / field_totals[field] if field_totals[field] else None,
        }
        for field in FIELD_MAP
    }
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "clean_official_fights_with_date_and_athletes": len(official),
        "exact_date_and_pair_aligned_greco_fights": len(alignments),
        "official_fights_without_exact_greco_pair": no_exact_pair,
        "ambiguous_greco_pair_matches": ambiguous_greco,
        "round_fighter_keys_compared": keys_compared,
        "single_version_keys": single_version_keys,
        "multi_version_keys": multi_version_keys,
        "duplicate_keys_with_unique_best_greco_match": duplicate_unique_best,
        "duplicate_keys_with_tied_best": duplicate_tied_best,
        "field_agreement": field_report,
        "alignment_csv": OUT_ALIGN.as_posix(),
        "duplicate_version_score_csv": OUT_DUP.as_posix(),
        "semantics": {
            "fuzzy_global_name_matching_used": False,
            "alignment_rule": "exact event date + exact normalized unordered official athlete pair + unique Greco bout",
            "duplicate_version_rule": "score all source versions; do not auto-promote a version here",
            "overall_field_agreement_excludes_tied_duplicate_versions": True,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Official UFC FightMetric ↔ Greco round-stat overlap",
        "",
        f"- Exact date + fighter-pair aligned fights: **{len(alignments)}**",
        f"- Round/fighter keys compared: **{keys_compared}**",
        f"- Duplicate-version keys: **{multi_version_keys}**",
        f"- Duplicate keys with a unique best Greco match: **{duplicate_unique_best}**",
        f"- Duplicate keys tied: **{duplicate_tied_best}**",
        "",
        "| Field | Comparisons | Exact | Exact % | Mean abs error |",
        "|---|---:|---:|---:|---:|",
    ]
    for field, x in field_report.items():
        frac = x["exact_fraction"]
        mae = x["mean_abs_error"]
        lines.append(f"| `{field}` | {x['comparisons']} | {x['exact']} | {frac:.4f} | {mae:.4f} |" if frac is not None and mae is not None else f"| `{field}` | 0 | 0 |  |  |")
    lines += ["", "No canonical source winner or duplicate-selection rule is created by this audit."]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"aligned_fights": len(alignments), "keys": keys_compared, "multi_versions": multi_version_keys, "unique_best": duplicate_unique_best}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
