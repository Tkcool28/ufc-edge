#!/usr/bin/env python3
"""Audit article-level canonical event consensus for official UFC weigh-in pages.

DATA PHASE ONLY. This pass does not create trusted identity links or canonical weigh-ins.

The purpose is to test a second identity signal that does not depend on mutable article
publication metadata. Unique canonical fighter names remain a fail-closed transport aid only.
For every extracted bout pair, all existing canonical fights for that participant pair are
collected. We then ask whether multiple bout pairs from the same official article converge
on one canonical event.
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

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data/derived/discovery/ufc_weigh_in_rows_candidate.csv"
FIGHTERS = ROOT / "data/canonical/v0/fighters.csv"
EVENTS = ROOT / "data/canonical/v0/events.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
OUT = ROOT / "data/derived/identity/ufc_weigh_in_article_event_consensus_candidate.csv"
AUDIT = ROOT / "provenance/audits/ufc_weigh_in_article_event_consensus_latest.json"

OUT_FIELDS = [
    "article_candidate_index", "article_url", "article_title", "article_published_time",
    "article_candidate_rows", "rows_with_unique_name_transport", "rows_with_canonical_pair",
    "rows_with_unique_event_candidate", "distinct_candidate_events", "intersection_event_count",
    "intersection_event_id", "unique_vote_event_count", "unique_vote_top_event_id",
    "unique_vote_top_support", "unique_vote_second_support", "unique_vote_unanimous",
    "candidate_event_id", "candidate_event_name", "candidate_event_date", "consensus_status",
    "review_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


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
    pair_events: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in fights:
        a = (row.get("fighter_a_id") or "").strip()
        b = (row.get("fighter_b_id") or "").strip()
        event_id = (row.get("event_id") or "").strip()
        if a and b and a != b and event_id:
            pair_events[tuple(sorted((a, b)))].add(event_id)

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in candidates:
        grouped[((row.get("article_candidate_index") or "").strip(), (row.get("article_url") or "").strip())].append(row)

    counts = Counter()
    intersection_size_dist = Counter()
    unique_vote_top_support_dist = Counter()
    resolvable_rows_dist = Counter()
    distinct_event_dist = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    output_rows: list[dict[str, Any]] = []

    for (article_index, article_url), rows in sorted(grouped.items(), key=lambda item: int(item[0][0] or 0)):
        counts["articles"] += 1
        event_sets: list[set[str]] = []
        unique_event_votes = Counter()
        rows_unique_names = 0
        rows_pair = 0
        all_candidate_events: set[str] = set()

        for row in rows:
            a_ids = ids_by_norm.get(norm_name(row.get("fighter_a_text") or ""), set())
            b_ids = ids_by_norm.get(norm_name(row.get("fighter_b_text") or ""), set())
            if len(a_ids) != 1 or len(b_ids) != 1:
                continue
            rows_unique_names += 1
            a_id = next(iter(a_ids)); b_id = next(iter(b_ids))
            if a_id == b_id:
                continue
            possible = set(pair_events.get(tuple(sorted((a_id, b_id))), set()))
            if not possible:
                continue
            rows_pair += 1
            event_sets.append(possible)
            all_candidate_events.update(possible)
            if len(possible) == 1:
                unique_event_votes[next(iter(possible))] += 1

        resolvable_rows_dist[rows_pair] += 1
        distinct_event_dist[len(all_candidate_events)] += 1
        intersection = set.intersection(*event_sets) if event_sets else set()
        intersection_size_dist[len(intersection)] += 1

        vote_ranked = unique_event_votes.most_common()
        top_event = vote_ranked[0][0] if vote_ranked else ""
        top_support = vote_ranked[0][1] if vote_ranked else 0
        second_support = vote_ranked[1][1] if len(vote_ranked) > 1 else 0
        unique_vote_top_support_dist[top_support] += 1
        vote_unanimous = bool(unique_event_votes) and len(unique_event_votes) == 1

        intersection_event = next(iter(intersection)) if len(intersection) == 1 else ""
        candidate_event = ""
        status = ""
        if not event_sets:
            status = "no_resolvable_pair_event"
        elif len(intersection) == 1:
            candidate_event = intersection_event
            status = "singleton_event_intersection_unpromoted"
        elif len(intersection) > 1:
            status = "multi_event_intersection"
        elif vote_unanimous and top_support >= 2:
            candidate_event = top_event
            status = "unanimous_unique_event_votes_unpromoted"
        elif top_support >= 2:
            status = "competing_unique_event_votes"
        else:
            status = "no_article_event_consensus"
        counts[status] += 1

        event = event_by_id.get(candidate_event, {}) if candidate_event else {}
        out = {
            "article_candidate_index": article_index,
            "article_url": article_url,
            "article_title": rows[0].get("article_title") or "",
            "article_published_time": rows[0].get("article_published_time") or "",
            "article_candidate_rows": len(rows),
            "rows_with_unique_name_transport": rows_unique_names,
            "rows_with_canonical_pair": rows_pair,
            "rows_with_unique_event_candidate": sum(unique_event_votes.values()),
            "distinct_candidate_events": len(all_candidate_events),
            "intersection_event_count": len(intersection),
            "intersection_event_id": intersection_event,
            "unique_vote_event_count": len(unique_event_votes),
            "unique_vote_top_event_id": top_event,
            "unique_vote_top_support": top_support,
            "unique_vote_second_support": second_support,
            "unique_vote_unanimous": "true" if vote_unanimous else "false",
            "candidate_event_id": candidate_event,
            "candidate_event_name": event.get("event_name") or "",
            "candidate_event_date": event.get("event_date") or "",
            "consensus_status": status,
            "review_status": "candidate",
        }
        output_rows.append(out)

        if status in {"competing_unique_event_votes", "no_article_event_consensus", "multi_event_intersection"} and len(examples[status]) < 30:
            examples[status].append({
                "article_url": article_url,
                "article_title": out["article_title"],
                "rows": len(rows),
                "rows_with_canonical_pair": rows_pair,
                "distinct_candidate_events": len(all_candidate_events),
                "intersection_size": len(intersection),
                "top_votes": vote_ranked[:5],
            })
        if candidate_event and len(examples[status]) < 30:
            examples[status].append({
                "article_url": article_url,
                "article_title": out["article_title"],
                "candidate_event_name": out["candidate_event_name"],
                "candidate_event_date": out["candidate_event_date"],
                "rows": len(rows),
                "rows_with_canonical_pair": rows_pair,
                "unique_vote_top_support": top_support,
                "unique_vote_second_support": second_support,
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(output_rows)

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_rows": len(candidates),
        "articles_with_candidate_rows": len(grouped),
        "counts": dict(counts),
        "intersection_event_count_distribution": {str(k): v for k, v in sorted(intersection_size_dist.items())},
        "rows_with_canonical_pair_distribution": {str(k): v for k, v in sorted(resolvable_rows_dist.items())},
        "distinct_candidate_event_count_distribution": {str(k): v for k, v in sorted(distinct_event_dist.items())},
        "unique_vote_top_support_distribution": {str(k): v for k, v in sorted(unique_vote_top_support_dist.items())},
        "examples": dict(examples),
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_event_identity_promoted": False,
            "display_name_only_identity_trusted": False,
            "publication_date_required": False,
            "required_next": "Inspect singleton-intersection and unanimous-vote coverage/error modes. Promote only an article-event gate that has an independently auditable participant-pair consensus rule; preserve multi-event/weak-consensus pages as unresolved."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "articles": counts["articles"],
        "singleton_intersection": counts["singleton_event_intersection_unpromoted"],
        "unanimous_votes": counts["unanimous_unique_event_votes_unpromoted"],
        "competing_votes": counts["competing_unique_event_votes"],
        "no_consensus": counts["no_article_event_consensus"],
        "no_resolvable": counts["no_resolvable_pair_event"],
        "multi_intersection": counts["multi_event_intersection"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
