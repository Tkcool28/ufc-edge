#!/usr/bin/env python3
"""Build the context-clean UFC weigh-in canonical candidate set.

DATA PHASE ONLY. Output remains derived/identity, not canonical.

The earlier identity bridge intentionally used participant/event consensus and exposed one
historical contamination: a Strikeforce article containing Brunson-Souza was transported to
the later UFC rematch. Canonical UFC weigh-ins therefore require UFC article context in
addition to the already-audited high-confidence fight/fighter identity.

This pass excludes explicit Strikeforce article context, then requires exactly two unique
fighter observations per canonical UFC fight and no conflicting duplicate scale weights.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/derived/identity/ufc_weigh_in_identity_candidate.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
OUT = ROOT / "data/derived/identity/ufc_weigh_in_canonical_candidate_v2.csv"
AUDIT = ROOT / "provenance/audits/ufc_weigh_in_canonical_candidate_v2_latest.json"


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def is_explicit_non_ufc_article(row: dict[str, str]) -> bool:
    context = " ".join([
        (row.get("article_title") or "").strip(),
        (row.get("article_url") or "").strip(),
    ]).lower()
    return "strikeforce" in context


def main() -> int:
    fields, rows = read_csv(SOURCE)
    _fight_fields, fights = read_csv(FIGHTS)
    fight_by_id = {(r.get("fight_id") or "").strip(): r for r in fights}

    expected_fields = {
        "article_candidate_index", "article_url", "article_title", "article_published_time",
        "source_path", "source_line_number", "bout_ordinal_in_article", "candidate_event_id",
        "fight_id", "fighter_id", "opponent_id", "source_side", "fighter_text",
        "opponent_text", "scale_weight_lbs", "marker", "raw_source_line", "identity_rule",
        "review_status",
    }
    missing = expected_fields - set(fields)
    if missing:
        raise SystemExit(f"source candidate header drift; missing={sorted(missing)}")

    exclusions = []
    eligible = []
    counts = Counter()
    for row in rows:
        fight_id = (row.get("fight_id") or "").strip()
        fight = fight_by_id.get(fight_id)
        if not fight:
            raise SystemExit(f"candidate fight missing from canonical spine: {fight_id}")
        if (fight.get("promotion") or "").strip() != "UFC":
            counts["non_ufc_canonical_fight"] += 1
            exclusions.append({
                "article_url": (row.get("article_url") or "").strip(),
                "article_title": (row.get("article_title") or "").strip(),
                "fight_id": fight_id,
                "fighter_id": (row.get("fighter_id") or "").strip(),
                "reason": "canonical_fight_not_ufc",
            })
            continue
        if is_explicit_non_ufc_article(row):
            counts["explicit_non_ufc_article_context"] += 1
            exclusions.append({
                "article_url": (row.get("article_url") or "").strip(),
                "article_title": (row.get("article_title") or "").strip(),
                "fight_id": fight_id,
                "fighter_id": (row.get("fighter_id") or "").strip(),
                "reason": "explicit_strikeforce_article_context",
            })
            continue
        if (row.get("review_status") or "").strip() != "high_confidence_identity_candidate":
            raise SystemExit("source candidate review status drift")
        try:
            weight = float((row.get("scale_weight_lbs") or "").strip())
        except ValueError as exc:
            raise SystemExit(f"non-numeric candidate scale weight: {row.get('scale_weight_lbs')!r}") from exc
        if not 80 <= weight <= 400:
            raise SystemExit(f"candidate scale weight outside contract: {weight}")
        eligible.append(row)

    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in eligible:
        groups[((row.get("fight_id") or "").strip(), (row.get("fighter_id") or "").strip())].append(row)

    remaining_duplicate_groups = []
    output_rows = []
    for (fight_id, fighter_id), group in sorted(groups.items()):
        weights = {float((r.get("scale_weight_lbs") or "").strip()) for r in group}
        if len(group) != 1:
            remaining_duplicate_groups.append({
                "fight_id": fight_id,
                "fighter_id": fighter_id,
                "row_count": len(group),
                "weights": sorted(weights),
                "article_urls": sorted({(r.get("article_url") or "").strip() for r in group}),
            })
            continue
        output_rows.append(group[0])

    if remaining_duplicate_groups:
        raise SystemExit(f"duplicate fight/fighter groups remain after context gate: {remaining_duplicate_groups[:10]}")

    by_fight: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in output_rows:
        by_fight[(row.get("fight_id") or "").strip()].append(row)
    bad_fight_cardinality = {
        fight_id: len(group) for fight_id, group in by_fight.items() if len(group) != 2
    }
    if bad_fight_cardinality:
        raise SystemExit(f"canonical UFC weigh-in fights do not have exactly two fighter observations: {list(bad_fight_cardinality.items())[:20]}")
    for fight_id, group in by_fight.items():
        fighters = {(r.get("fighter_id") or "").strip() for r in group}
        opponents = {(r.get("opponent_id") or "").strip() for r in group}
        fight = fight_by_id[fight_id]
        participants = {(fight.get("fighter_a_id") or "").strip(), (fight.get("fighter_b_id") or "").strip()}
        if fighters != participants or opponents != participants:
            raise SystemExit(f"participant integrity failure after context gate: {fight_id}")

    if len(rows) != 12892:
        raise SystemExit(f"source candidate count drift: {len(rows)} != 12892")
    if counts.get("explicit_non_ufc_article_context") != 2:
        raise SystemExit(f"explicit Strikeforce exclusion count drift: {counts.get('explicit_non_ufc_article_context', 0)} != 2")
    if counts.get("non_ufc_canonical_fight", 0) != 0:
        raise SystemExit("unexpected non-UFC canonical fights in UFC weigh-in candidate")
    if len(output_rows) != 12890 or len(by_fight) != 6445:
        raise SystemExit(f"context-clean cardinality drift: rows={len(output_rows)} fights={len(by_fight)}")

    output_rows.sort(key=lambda r: ((r.get("fight_id") or ""), (r.get("fighter_id") or "")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        writer.writeheader(); writer.writerows(output_rows)

    payload = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_rows": len(rows),
        "excluded_rows": len(exclusions),
        "exclusion_reason_counts": dict(counts),
        "exclusion_examples": exclusions,
        "canonical_candidate_rows": len(output_rows),
        "canonical_candidate_fights": len(by_fight),
        "canonical_candidate_fighters": len({(r.get("fighter_id") or "").strip() for r in output_rows}),
        "nonempty_marker_rows_preserved_as_raw_only": sum(bool((r.get("marker") or "").strip()) for r in output_rows),
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_rows_written": False,
            "identity_promotable": True,
            "scale_weight_promotable": True,
            "exact_two_observations_per_fight": True,
            "explicit_non_ufc_article_context_excluded": True,
            "weigh_in_date_promoted": False,
            "attempt_number_promoted": False,
            "marker_semantics_promoted": False,
            "required_next": "Materialize 12,890 canonical UFC weigh-in observations (6,445 fights x 2 fighters) with fight/fighter identity and scale weight. Preserve source article lineage in field provenance; leave unresolved annotation/date/attempt semantics null."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_rows": len(rows),
        "excluded_rows": len(exclusions),
        "exclusion_reason_counts": dict(counts),
        "canonical_candidate_rows": len(output_rows),
        "canonical_candidate_fights": len(by_fight),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
