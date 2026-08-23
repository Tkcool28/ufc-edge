#!/usr/bin/env python3
"""Diagnose duplicate UFC weigh-in source observations against canonical fight/event context."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data/derived/identity/ufc_weigh_in_identity_candidate.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
EVENTS = ROOT / "data/canonical/v0/events.csv"
FIGHTERS = ROOT / "data/canonical/v0/fighters.csv"
OUT = ROOT / "provenance/audits/ufc_weigh_in_duplicate_context_latest.json"


def read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = read(CANDIDATES)
    fights = {(r.get("fight_id") or "").strip(): r for r in read(FIGHTS)}
    events = {(r.get("event_id") or "").strip(): r for r in read(EVENTS)}
    fighters = {(r.get("fighter_id") or "").strip(): r for r in read(FIGHTERS)}

    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[((row.get("fight_id") or "").strip(), (row.get("fighter_id") or "").strip())].append(row)

    output = []
    for (fight_id, fighter_id), group in groups.items():
        if len(group) <= 1:
            continue
        fight = fights.get(fight_id, {})
        event_id = (fight.get("event_id") or "").strip()
        event = events.get(event_id, {})
        output.append({
            "fight_id": fight_id,
            "fighter_id": fighter_id,
            "fighter_name": (fighters.get(fighter_id, {}).get("canonical_name") or "").strip(),
            "canonical_event_id": event_id,
            "canonical_event_name": (event.get("event_name") or "").strip(),
            "canonical_event_date": (event.get("event_date") or "").strip(),
            "canonical_promotion": (fight.get("promotion") or "").strip(),
            "candidate_rows": [
                {
                    "candidate_event_id": (r.get("candidate_event_id") or "").strip(),
                    "article_candidate_index": (r.get("article_candidate_index") or "").strip(),
                    "article_url": (r.get("article_url") or "").strip(),
                    "article_title": (r.get("article_title") or "").strip(),
                    "article_published_time": (r.get("article_published_time") or "").strip(),
                    "bout_ordinal_in_article": (r.get("bout_ordinal_in_article") or "").strip(),
                    "source_side": (r.get("source_side") or "").strip(),
                    "fighter_text": (r.get("fighter_text") or "").strip(),
                    "opponent_text": (r.get("opponent_text") or "").strip(),
                    "scale_weight_lbs": (r.get("scale_weight_lbs") or "").strip(),
                    "marker": (r.get("marker") or "").strip(),
                    "raw_source_line": (r.get("raw_source_line") or "").strip(),
                    "source_path": (r.get("source_path") or "").strip(),
                    "source_line_number": (r.get("source_line_number") or "").strip(),
                }
                for r in group
            ],
        })

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "duplicate_fight_fighter_groups": len(output),
        "groups": output,
        "decision": {
            "canonical_rows_written": False,
            "required_next": "Use canonical event/article context to quarantine false article-event transport before canonical weigh-in deduplication. Do not choose conflicting scale weight by averaging or arbitrary source order."
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"duplicate_groups": len(output), "fight_ids": sorted({g['fight_id'] for g in output})}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
