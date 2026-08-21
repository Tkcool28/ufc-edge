#!/usr/bin/env python3
"""Test UFC fight-node `*_fight_weight` against official UFC weigh-in observations.

Missed-weight examples are deliberately used because actual scale weight differs from
the normal division limit. If the fight-node field matches the official published scale
weight, that is strong evidence it represents fight-specific weigh-in weight rather than
weight-class metadata. This audit does not yet promote the field canonically.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

FIGHT_ROOT = Path("data/raw/ufc_com_resources/fights")
ATHLETE_ROOT = Path("data/raw/ufc_com_resources/athletes")
EVENT_BRIDGE = Path("data/derived/identity/ufc_fight_event_bridge_candidate.csv")
OUT = Path("provenance/audits/ufc_fight_weight_semantics_latest.json")

# Primary-source observations manually transcribed from official UFC weigh-in articles.
CASES = [
    {
        "event_date": "2026-07-18",
        "fighter": "Chase Hooper",
        "opponent": "Mitch Ramirez",
        "scale_weight_lbs": "157.5",
        "normal_division_limit_lbs": "156",
        "miss_note": "1.5 pounds over lightweight limit",
        "source_url": "https://www.ufc.com/news/official-weigh-results-ufc-fight-night-oklahoma-city-du-plessis-usman",
    },
    {
        "event_date": "2026-07-18",
        "fighter": "Ezra Elliott",
        "opponent": "Damien Anderson",
        "scale_weight_lbs": "147.5",
        "normal_division_limit_lbs": "146",
        "miss_note": "1.5 pounds over featherweight limit",
        "source_url": "https://www.ufc.com/news/official-weigh-results-ufc-fight-night-oklahoma-city-du-plessis-usman",
    },
    {
        "event_date": "2026-06-20",
        "fighter": "Kevin Borjas",
        "opponent": "Andre Lima",
        "scale_weight_lbs": "129",
        "normal_division_limit_lbs": "126",
        "miss_note": "3 pounds over flyweight limit",
        "source_url": "https://www.ufc.com/news/official-weigh-results-kape-horiguchi-vegas-119",
    },
]


def norm(x: str) -> str:
    t = unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", t)


def latest_complete(root: Path) -> Path:
    for p in reversed(sorted(x for x in root.iterdir() if x.is_dir() and (x / "manifest.json").exists())):
        m = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
        if m.get("complete_collection_snapshot") is True or m.get("semantics", {}).get("complete_collection_snapshot") is True:
            return p
    raise RuntimeError(f"No complete snapshot under {root}")


def flat_pages(snapshot: Path) -> list[Path]:
    m = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    return [Path(str(x["path"])) for x in m.get("files") or [] if isinstance(x, dict) and x.get("path")]


def chunk_pages(snapshot: Path) -> list[Path]:
    m = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    out: list[Path] = []
    for cm_raw in m.get("chunk_manifests") or []:
        cm = json.loads(Path(str(cm_raw)).read_text(encoding="utf-8"))
        out.extend(Path(str(x["path"])) for x in cm.get("files") or [])
    return out


def rel_id(item: dict[str, Any], name: str) -> str | None:
    rel = (item.get("relationships") or {}).get(name)
    data = rel.get("data") if isinstance(rel, dict) else None
    return str(data.get("id")) if isinstance(data, dict) and data.get("id") is not None else None


def main() -> int:
    athlete_names: dict[str, str] = {}
    for page in flat_pages(latest_complete(ATHLETE_ROOT)):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            name = attrs.get("title") or attrs.get("name")
            if name:
                athlete_names[str(item["id"])] = str(name).strip()

    # Event date by fight UUID from already audited direct event membership.
    import csv
    date_by_fight: dict[str, str] = {}
    with EVENT_BRIDGE.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("event_date"):
                date_by_fight[row["ufc_fight_uuid"]] = row["event_date"]

    indexed: dict[tuple[str, tuple[str, str]], list[dict[str, Any]]] = {}
    for page in chunk_pages(latest_complete(FIGHT_ROOT)):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            uid = str(item["id"])
            date = date_by_fight.get(uid)
            red, blue = rel_id(item, "red_corner"), rel_id(item, "blue_corner")
            if not date or not red or not blue or red not in athlete_names or blue not in athlete_names:
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            pair = tuple(sorted((norm(athlete_names[red]), norm(athlete_names[blue]))))
            indexed.setdefault((date, pair), []).append({
                "ufc_fight_uuid": uid,
                "red_uuid": red,
                "blue_uuid": blue,
                "red_name": athlete_names[red],
                "blue_name": athlete_names[blue],
                "red_corner_fight_weight": attrs.get("red_corner_fight_weight"),
                "blue_corner_fight_weight": attrs.get("blue_corner_fight_weight"),
                "fightmetric_id": attrs.get("fightmetric_id"),
                "title": attrs.get("title"),
            })

    results = []
    exact_scale_matches = 0
    matched_cases = 0
    for case in CASES:
        pair = tuple(sorted((norm(case["fighter"]), norm(case["opponent"]))))
        candidates = indexed.get((case["event_date"], pair), [])
        result = {**case, "candidate_count": len(candidates), "candidates": candidates}
        if len(candidates) == 1:
            matched_cases += 1
            f = candidates[0]
            if norm(f["red_name"]) == norm(case["fighter"]):
                raw_weight = f["red_corner_fight_weight"]
                corner = "red"
            elif norm(f["blue_name"]) == norm(case["fighter"]):
                raw_weight = f["blue_corner_fight_weight"]
                corner = "blue"
            else:
                raw_weight = None; corner = None
            result["fighter_corner"] = corner
            result["fight_node_weight_raw"] = raw_weight
            try:
                equal = Decimal(str(raw_weight)) == Decimal(case["scale_weight_lbs"])
            except Exception:
                equal = False
            result["matches_official_scale_weight"] = equal
            result["matches_normal_division_limit"] = (
                Decimal(str(raw_weight)) == Decimal(case["normal_division_limit_lbs"])
                if raw_weight not in (None, "") else False
            )
            exact_scale_matches += int(equal)
        results.append(result)

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "cases": results,
        "matched_unique_cases": matched_cases,
        "exact_official_scale_weight_matches": exact_scale_matches,
        "decision": {
            "canonical_weigh_in_mapping_promoted": False,
            "strong_scale_weight_evidence": matched_cases >= 2 and exact_scale_matches == matched_cases,
            "rule": "Even if missed-weight cases match exactly, full-field zero/null and historical coverage behavior must be audited before canonical promotion.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"matched": matched_cases, "scale_matches": exact_scale_matches}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
