#!/usr/bin/env python3
"""Audit high-confidence UFC weigh-in identity candidates for canonical materialization.

DATA PHASE ONLY. Read-only audit; no canonical rows are written.

The canonical grain is one fight-specific fighter official weigh-in observation. Multiple
official articles may repeat the same observation, so this audit measures duplicate
(fight_id, fighter_id) groups and requires scale-weight agreement before a later builder may
deduplicate them. Annotation marker semantics remain page-local and are not promoted here.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data/derived/identity/ufc_weigh_in_identity_candidate.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
FIGHTERS = ROOT / "data/canonical/v0/fighters.csv"
OUT = ROOT / "provenance/audits/ufc_weigh_in_canonical_readiness_latest.json"

REQUIRED_FIELDS = {
    "article_candidate_index", "article_url", "article_title", "article_published_time",
    "source_path", "source_line_number", "bout_ordinal_in_article", "candidate_event_id",
    "fight_id", "fighter_id", "opponent_id", "source_side", "fighter_text",
    "opponent_text", "scale_weight_lbs", "marker", "raw_source_line", "identity_rule",
    "review_status",
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    fields, rows = read_csv(CANDIDATES)
    _fight_fields, fights = read_csv(FIGHTS)
    _fighter_fields, fighters = read_csv(FIGHTERS)
    missing = REQUIRED_FIELDS - set(fields)
    if missing:
        raise SystemExit(f"candidate header drift; missing={sorted(missing)}")

    canonical_fight_participants = {
        (r.get("fight_id") or "").strip(): {
            (r.get("fighter_a_id") or "").strip(),
            (r.get("fighter_b_id") or "").strip(),
        }
        for r in fights
        if (r.get("fight_id") or "").strip()
    }
    canonical_fighter_ids = {
        (r.get("fighter_id") or "").strip() for r in fighters if (r.get("fighter_id") or "").strip()
    }

    counts = Counter()
    by_fight_fighter: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    invalid_examples: list[dict[str, str]] = []
    marker_counts = Counter()
    article_counts = Counter()

    for row in rows:
        fight_id = (row.get("fight_id") or "").strip()
        fighter_id = (row.get("fighter_id") or "").strip()
        opponent_id = (row.get("opponent_id") or "").strip()
        review_status = (row.get("review_status") or "").strip()
        article_url = (row.get("article_url") or "").strip()
        marker = (row.get("marker") or "").strip()

        if review_status != "high_confidence_identity_candidate":
            counts["non_high_confidence_review_status"] += 1
        participants = canonical_fight_participants.get(fight_id)
        if participants is None:
            counts["fight_fk_missing"] += 1
        elif {fighter_id, opponent_id} != participants:
            counts["participant_integrity_failure"] += 1
        if fighter_id not in canonical_fighter_ids:
            counts["fighter_fk_missing"] += 1

        try:
            weight = float((row.get("scale_weight_lbs") or "").strip())
        except ValueError:
            counts["invalid_scale_weight"] += 1
            if len(invalid_examples) < 25:
                invalid_examples.append({
                    "article_url": article_url,
                    "fight_id": fight_id,
                    "fighter_id": fighter_id,
                    "scale_weight_lbs": row.get("scale_weight_lbs") or "",
                })
            continue
        if not 80 <= weight <= 400:
            counts["scale_weight_outside_contract"] += 1
        by_fight_fighter[(fight_id, fighter_id)].append(row)
        marker_counts[marker or "<empty>"] += 1
        article_counts[article_url] += 1

    duplicate_groups = {key: group for key, group in by_fight_fighter.items() if len(group) > 1}
    duplicate_group_examples = []
    conflicting_weight_groups = 0
    conflicting_marker_groups = 0
    duplicate_extra_rows = 0
    for (fight_id, fighter_id), group in duplicate_groups.items():
        duplicate_extra_rows += len(group) - 1
        weights = sorted({float((r.get("scale_weight_lbs") or "").strip()) for r in group})
        markers = sorted({(r.get("marker") or "").strip() for r in group})
        if len(weights) > 1:
            conflicting_weight_groups += 1
        if len(markers) > 1:
            conflicting_marker_groups += 1
        if len(duplicate_group_examples) < 25:
            duplicate_group_examples.append({
                "fight_id": fight_id,
                "fighter_id": fighter_id,
                "row_count": len(group),
                "weights": weights,
                "markers": markers,
                "article_urls": sorted({(r.get("article_url") or "").strip() for r in group}),
                "source_records": [
                    {
                        "article_candidate_index": (r.get("article_candidate_index") or "").strip(),
                        "bout_ordinal_in_article": (r.get("bout_ordinal_in_article") or "").strip(),
                        "source_side": (r.get("source_side") or "").strip(),
                    }
                    for r in group
                ],
            })

    unique_observations = len(by_fight_fighter)
    expected_two_per_fight = 2 * len({fight_id for fight_id, _ in by_fight_fighter})
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_candidate_rows": len(rows),
        "source_articles": len(article_counts),
        "source_fights": len({fight_id for fight_id, _ in by_fight_fighter}),
        "source_fighters": len({fighter_id for _, fighter_id in by_fight_fighter}),
        "unique_fight_fighter_observations": unique_observations,
        "expected_two_per_distinct_fight": expected_two_per_fight,
        "duplicate_fight_fighter_groups": len(duplicate_groups),
        "duplicate_extra_source_rows": duplicate_extra_rows,
        "duplicate_groups_with_conflicting_scale_weight": conflicting_weight_groups,
        "duplicate_groups_with_conflicting_marker": conflicting_marker_groups,
        "integrity_counts": dict(counts),
        "marker_counts": dict(marker_counts),
        "duplicate_group_examples": duplicate_group_examples,
        "invalid_examples": invalid_examples,
        "decision": {
            "canonical_rows_written": False,
            "scale_weight_promotable": (
                counts.get("invalid_scale_weight", 0) == 0
                and counts.get("scale_weight_outside_contract", 0) == 0
                and conflicting_weight_groups == 0
            ),
            "identity_promotable": (
                counts.get("non_high_confidence_review_status", 0) == 0
                and counts.get("fight_fk_missing", 0) == 0
                and counts.get("fighter_fk_missing", 0) == 0
                and counts.get("participant_integrity_failure", 0) == 0
            ),
            "dedupe_rule_candidate": "one canonical observation per exact (fight_id, fighter_id) only if all official source rows agree on scale_weight_lbs",
            "weigh_in_date_promoted": False,
            "attempt_number_promoted": False,
            "marker_semantics_promoted": False,
            "required_next": "If identity, weight, and duplicate agreement gates pass, materialize one canonical weigh-in observation per fight/fighter with scale weight only. Preserve all supporting official article records in field provenance; leave page-local semantics null unless explicitly resolved observation-by-observation."
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_candidate_rows": len(rows),
        "unique_observations": unique_observations,
        "duplicate_groups": len(duplicate_groups),
        "duplicate_extra_rows": duplicate_extra_rows,
        "conflicting_weight_groups": conflicting_weight_groups,
        "integrity_counts": dict(counts),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
