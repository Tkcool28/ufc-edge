#!/usr/bin/env python3
"""Build high-confidence official UFC weigh-in identity candidates.

DATA PHASE ONLY. Output is derived/identity, not canonical.

Eligibility is deliberately strict:
1. the official article has a singleton canonical-event intersection across all resolvable
   participant-pair candidates;
2. each source fighter name has exactly one canonical-name transport candidate;
3. that exact unordered canonical participant pair has exactly one fight inside the
   article's consensus event;
4. the mapped source-side fighter IDs are exactly the participants in that fight.

Scale weight and marker are preserved source-faithfully. Attempt number, missed-weight,
contract limit, catchweight and penalty semantics are not inferred here.
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
CONSENSUS = ROOT / "data/derived/identity/ufc_weigh_in_article_event_consensus_candidate.csv"
FIGHTERS = ROOT / "data/canonical/v0/fighters.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
OUT = ROOT / "data/derived/identity/ufc_weigh_in_identity_candidate.csv"
AUDIT = ROOT / "provenance/audits/ufc_weigh_in_identity_candidate_latest.json"

FIELDS = [
    "article_candidate_index", "article_url", "article_title", "article_published_time",
    "source_path", "source_line_number", "bout_ordinal_in_article", "candidate_event_id",
    "fight_id", "fighter_id", "opponent_id", "source_side", "fighter_text",
    "opponent_text", "scale_weight_lbs", "marker", "raw_source_line", "identity_rule",
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
    consensus = read_csv(CONSENSUS)
    fighters = read_csv(FIGHTERS)
    fights = read_csv(FIGHTS)

    ids_by_norm: dict[str, set[str]] = defaultdict(set)
    name_by_id: dict[str, str] = {}
    for row in fighters:
        fid = (row.get("fighter_id") or "").strip()
        name = (row.get("canonical_name") or "").strip()
        if fid and name:
            ids_by_norm[norm_name(name)].add(fid)
            name_by_id[fid] = name

    consensus_event_by_article = {
        ((row.get("article_candidate_index") or "").strip(), (row.get("article_url") or "").strip()): (row.get("candidate_event_id") or "").strip()
        for row in consensus
        if (row.get("consensus_status") or "").strip() == "singleton_event_intersection_unpromoted"
        and (row.get("candidate_event_id") or "").strip()
    }

    fights_by_event_pair: dict[tuple[str, tuple[str, str]], list[dict[str, str]]] = defaultdict(list)
    for fight in fights:
        event_id = (fight.get("event_id") or "").strip()
        a = (fight.get("fighter_a_id") or "").strip()
        b = (fight.get("fighter_b_id") or "").strip()
        if event_id and a and b and a != b:
            fights_by_event_pair[(event_id, tuple(sorted((a, b))))].append(fight)

    counts = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    out_rows: list[dict[str, Any]] = []
    emitted_keys: set[tuple[str, str, str]] = set()

    for row in candidates:
        article_key = ((row.get("article_candidate_index") or "").strip(), (row.get("article_url") or "").strip())
        event_id = consensus_event_by_article.get(article_key)
        if not event_id:
            counts["row_article_not_singleton_consensus"] += 1
            continue

        a_text = row.get("fighter_a_text") or ""
        b_text = row.get("fighter_b_text") or ""
        a_ids = ids_by_norm.get(norm_name(a_text), set())
        b_ids = ids_by_norm.get(norm_name(b_text), set())
        if len(a_ids) != 1 or len(b_ids) != 1:
            counts["row_name_transport_not_unique"] += 1
            continue
        a_id = next(iter(a_ids)); b_id = next(iter(b_ids))
        if a_id == b_id:
            counts["row_same_fighter_transport"] += 1
            continue

        eligible_fights = fights_by_event_pair.get((event_id, tuple(sorted((a_id, b_id)))), [])
        if len(eligible_fights) != 1:
            status = "row_event_pair_no_fight" if not eligible_fights else "row_event_pair_multiple_fights"
            counts[status] += 1
            if len(examples[status]) < 30:
                examples[status].append({
                    "article_url": article_key[1], "event_id": event_id,
                    "fighter_a": a_text, "fighter_b": b_text, "eligible_fights": len(eligible_fights),
                })
            continue

        fight = eligible_fights[0]
        fight_id = (fight.get("fight_id") or "").strip()
        participants = {(fight.get("fighter_a_id") or "").strip(), (fight.get("fighter_b_id") or "").strip()}
        if participants != {a_id, b_id}:
            counts["row_participant_integrity_failure"] += 1
            continue

        source_record = f"article:{article_key[0]}:bout:{(row.get('bout_ordinal_in_article') or '').strip()}"
        for side, fighter_id, opponent_id, fighter_text, opponent_text, weight, marker in (
            ("a", a_id, b_id, a_text, b_text, row.get("scale_weight_a_lbs") or "", row.get("marker_a") or ""),
            ("b", b_id, a_id, b_text, a_text, row.get("scale_weight_b_lbs") or "", row.get("marker_b") or ""),
        ):
            key = (source_record, fight_id, fighter_id)
            if key in emitted_keys:
                counts["duplicate_identity_observation_suppressed"] += 1
                continue
            emitted_keys.add(key)
            out_rows.append({
                "article_candidate_index": article_key[0],
                "article_url": article_key[1],
                "article_title": row.get("article_title") or "",
                "article_published_time": row.get("article_published_time") or "",
                "source_path": row.get("source_path") or "",
                "source_line_number": row.get("source_line_number") or "",
                "bout_ordinal_in_article": row.get("bout_ordinal_in_article") or "",
                "candidate_event_id": event_id,
                "fight_id": fight_id,
                "fighter_id": fighter_id,
                "opponent_id": opponent_id,
                "source_side": side,
                "fighter_text": fighter_text,
                "opponent_text": opponent_text,
                "scale_weight_lbs": weight,
                "marker": marker,
                "raw_source_line": row.get("raw_source_line") or "",
                "identity_rule": "official_article_singleton_event_intersection+unique_contextual_participant_pair",
                "review_status": "high_confidence_identity_candidate",
            })
        counts["mapped_bout_rows"] += 1

    counts["mapped_fighter_observations"] = len(out_rows)
    counts["mapped_articles"] = len({(r["article_candidate_index"], r["article_url"]) for r in out_rows})
    counts["mapped_fights"] = len({r["fight_id"] for r in out_rows})
    counts["mapped_fighters"] = len({r["fighter_id"] for r in out_rows})
    counts["mapped_nonempty_markers"] = sum(bool(str(r["marker"]).strip()) for r in out_rows)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(out_rows)

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_candidate_rows": len(candidates),
        "singleton_consensus_articles": len(consensus_event_by_article),
        "counts": dict(counts),
        "examples": dict(examples),
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_weigh_ins_written": False,
            "scale_weight_semantics_resolved": True,
            "identity_rule_promotable_candidate": True,
            "attempt_number_semantics_resolved": False,
            "missed_weight_semantics_resolved": False,
            "contract_limit_semantics_resolved": False,
            "catchweight_semantics_resolved": False,
            "penalty_semantics_resolved": False,
            "required_next": "Audit page-level marker/footnote semantics for these mapped observations. Do not fabricate required attempt_number; either prove attempt semantics or revise the canonical contract to represent final official weigh-in observations separately."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "mapped_articles": counts["mapped_articles"],
        "mapped_bout_rows": counts["mapped_bout_rows"],
        "mapped_fighter_observations": counts["mapped_fighter_observations"],
        "mapped_fights": counts["mapped_fights"],
        "mapped_nonempty_markers": counts["mapped_nonempty_markers"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
