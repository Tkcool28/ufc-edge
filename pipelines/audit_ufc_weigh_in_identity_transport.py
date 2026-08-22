#!/usr/bin/env python3
"""Audit fail-closed transport from official UFC weigh-in candidates to canonical fights.

DATA PHASE ONLY. This does not create canonical weigh-ins.

Display names are used only as a transport aid to search already-trusted canonical fighter
participants. This pass measures whether an unordered fighter pair identifies a unique
canonical fight and what the article-published-date -> canonical-event-date offsets look
like. No date window is promoted here; the audit must establish it first.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data/derived/discovery/ufc_weigh_in_rows_candidate.csv"
FIGHTERS = ROOT / "data/canonical/v0/fighters.csv"
EVENTS = ROOT / "data/canonical/v0/events.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
OUT = ROOT / "data/derived/identity/ufc_weigh_in_identity_transport_candidate.csv"
AUDIT = ROOT / "provenance/audits/ufc_weigh_in_identity_transport_latest.json"

OUT_FIELDS = [
    "article_candidate_index", "article_url", "article_title", "article_published_date",
    "bout_ordinal_in_article", "fighter_a_text", "fighter_b_text", "scale_weight_a_lbs",
    "scale_weight_b_lbs", "marker_a", "marker_b", "fighter_a_transport_id",
    "fighter_b_transport_id", "canonical_pair_fight_count", "candidate_fight_id",
    "candidate_event_id", "candidate_event_date", "event_minus_article_days",
    "transport_status", "review_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def parse_iso_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    # Article metadata is expected to be ISO-like. Date prefix is sufficient for this audit.
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", text)
    if not m:
        return None
    try:
        return date.fromisoformat(m.group(1))
    except ValueError:
        return None


def parse_canonical_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def main() -> int:
    candidates = read_csv(CANDIDATES)
    fighters = read_csv(FIGHTERS)
    events = read_csv(EVENTS)
    fights = read_csv(FIGHTS)

    ids_by_norm: dict[str, set[str]] = defaultdict(set)
    for row in fighters:
        fid = (row.get("fighter_id") or "").strip()
        name = (row.get("canonical_name") or "").strip()
        if fid and name:
            ids_by_norm[norm_name(name)].add(fid)

    event_by_id = {
        (row.get("event_id") or "").strip(): row
        for row in events
        if (row.get("event_id") or "").strip()
    }
    pair_fights: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in fights:
        a = (row.get("fighter_a_id") or "").strip()
        b = (row.get("fighter_b_id") or "").strip()
        if a and b and a != b:
            pair_fights[tuple(sorted((a, b)))].append(row)

    counts = Counter()
    pair_count_dist = Counter()
    unique_delta_dist = Counter()
    multi_nearest_abs_delta_dist = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    out_rows: list[dict[str, Any]] = []

    for row in candidates:
        a_text = row.get("fighter_a_text") or ""
        b_text = row.get("fighter_b_text") or ""
        a_ids = ids_by_norm.get(norm_name(a_text), set())
        b_ids = ids_by_norm.get(norm_name(b_text), set())
        article_date = parse_iso_date(row.get("article_published_time") or "")
        if article_date is None:
            counts["article_date_missing_or_unparseable"] += 1

        base: dict[str, Any] = {
            "article_candidate_index": row.get("article_candidate_index") or "",
            "article_url": row.get("article_url") or "",
            "article_title": row.get("article_title") or "",
            "article_published_date": article_date.isoformat() if article_date else "",
            "bout_ordinal_in_article": row.get("bout_ordinal_in_article") or "",
            "fighter_a_text": a_text,
            "fighter_b_text": b_text,
            "scale_weight_a_lbs": row.get("scale_weight_a_lbs") or "",
            "scale_weight_b_lbs": row.get("scale_weight_b_lbs") or "",
            "marker_a": row.get("marker_a") or "",
            "marker_b": row.get("marker_b") or "",
            "fighter_a_transport_id": "",
            "fighter_b_transport_id": "",
            "canonical_pair_fight_count": 0,
            "candidate_fight_id": "",
            "candidate_event_id": "",
            "candidate_event_date": "",
            "event_minus_article_days": "",
            "transport_status": "",
            "review_status": "candidate",
        }

        if len(a_ids) != 1 or len(b_ids) != 1:
            if len(a_ids) == 0 or len(b_ids) == 0:
                status = "unresolved_normalized_name"
            else:
                status = "ambiguous_normalized_name"
            counts[status] += 1
            base["transport_status"] = status
            if len(examples[status]) < 30:
                examples[status].append({"a": a_text, "b": b_text, "url": base["article_url"], "a_ids": len(a_ids), "b_ids": len(b_ids)})
            out_rows.append(base)
            continue

        a_id = next(iter(a_ids)); b_id = next(iter(b_ids))
        base["fighter_a_transport_id"] = a_id
        base["fighter_b_transport_id"] = b_id
        counts["both_names_unique_transport"] += 1
        if a_id == b_id:
            counts["same_fighter_transport"] += 1
            base["transport_status"] = "same_fighter_transport"
            out_rows.append(base)
            continue

        matches = pair_fights.get(tuple(sorted((a_id, b_id))), [])
        pair_count_dist[len(matches)] += 1
        base["canonical_pair_fight_count"] = len(matches)
        if not matches:
            status = "no_canonical_fight_for_pair"
            counts[status] += 1
            base["transport_status"] = status
            if len(examples[status]) < 30:
                examples[status].append({"a": a_text, "b": b_text, "url": base["article_url"]})
            out_rows.append(base)
            continue

        decorated: list[tuple[dict[str, str], date | None, int | None]] = []
        for fight in matches:
            event = event_by_id.get((fight.get("event_id") or "").strip(), {})
            event_date = parse_canonical_date(event.get("event_date") or "")
            delta = (event_date - article_date).days if event_date and article_date else None
            decorated.append((fight, event_date, delta))

        if len(matches) == 1:
            fight, event_date, delta = decorated[0]
            status = "unique_canonical_pair_unpromoted"
            counts[status] += 1
            if delta is not None:
                unique_delta_dist[delta] += 1
            base.update({
                "candidate_fight_id": fight.get("fight_id") or "",
                "candidate_event_id": fight.get("event_id") or "",
                "candidate_event_date": event_date.isoformat() if event_date else "",
                "event_minus_article_days": delta if delta is not None else "",
                "transport_status": status,
            })
            out_rows.append(base)
            continue

        counts["multiple_canonical_fights_for_pair"] += 1
        deltas = [abs(delta) for _, _, delta in decorated if delta is not None]
        if deltas:
            multi_nearest_abs_delta_dist[min(deltas)] += 1
        base["transport_status"] = "multiple_canonical_fights_for_pair"
        if len(examples["multiple_canonical_fights_for_pair"]) < 40:
            examples["multiple_canonical_fights_for_pair"].append({
                "a": a_text,
                "b": b_text,
                "url": base["article_url"],
                "article_date": base["article_published_date"],
                "candidate_event_dates": [event_date.isoformat() if event_date else None for _, event_date, _ in decorated],
                "event_minus_article_days": [delta for _, _, delta in decorated],
            })
        out_rows.append(base)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(out_rows)

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_rows": len(candidates),
        "canonical_fighters": len(fighters),
        "canonical_events": len(events),
        "canonical_fights": len(fights),
        "counts": dict(counts),
        "canonical_pair_fight_count_distribution": {str(k): v for k, v in sorted(pair_count_dist.items())},
        "unique_pair_event_minus_article_days_distribution": {str(k): v for k, v in sorted(unique_delta_dist.items())},
        "multi_pair_nearest_abs_event_date_delta_distribution": {str(k): v for k, v in sorted(multi_nearest_abs_delta_dist.items())},
        "examples": dict(examples),
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_identity_promoted": False,
            "display_name_only_identity_trusted": False,
            "unique_normalized_names_are_transport_only": True,
            "date_window_promoted": False,
            "required_next": "Use this audit to define a conservative article-date/event-date gate, then resolve only exact canonical participant pairs with a unique eligible fight; quarantine all other rows."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_rows": len(candidates),
        "both_names_unique_transport": counts["both_names_unique_transport"],
        "unique_pair_unpromoted": counts["unique_canonical_pair_unpromoted"],
        "multiple_pair": counts["multiple_canonical_fights_for_pair"],
        "no_pair": counts["no_canonical_fight_for_pair"],
        "unresolved_name": counts["unresolved_normalized_name"],
        "ambiguous_name": counts["ambiguous_normalized_name"],
        "article_date_missing_or_unparseable": counts["article_date_missing_or_unparseable"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
