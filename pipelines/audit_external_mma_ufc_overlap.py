#!/usr/bin/env python3
"""Audit UFC overlap before external-MMA canonical fight insertion.

DATA PHASE ONLY. No canonical rows are written.

Required identity chain:
- external fighter URL -> trusted canonical fighter ID from the existing audited crosswalk;
- source fight date parses exactly as abbreviated-month MDY;
- exact unordered canonical participant pair;
- exact canonical event date.

Only pair+date equality is called exact UFC overlap. Pair-only matches, UFC-labelled rows
missing from the canonical spine, unresolved fighters, and the known duplicate source fight
key all fail closed into review/quarantine classes.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/kaggle_pro_mma_fights/v1/pro_mma_fights.csv"
XWALK = ROOT / "data/derived/identity/external_mma_canonical_crosswalk_candidate.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
EVENTS = ROOT / "data/canonical/v0/events.csv"
OUT_CSV = ROOT / "data/derived/identity/external_mma_ufc_overlap_candidate.csv"
OUT_JSON = ROOT / "provenance/audits/external_mma_ufc_overlap_latest.json"
UFC_ORG = "Ultimate Fighting Championship (UFC)"

OUT_FIELDS = [
    "source_event_url", "source_match_nr", "source_event_title", "source_organisation",
    "source_event_date", "fighter1_url", "fighter2_url", "fighter1_name", "fighter2_name",
    "fighter1_canonical_id", "fighter2_canonical_id", "trusted_fighter_count",
    "canonical_pair_fight_count", "canonical_pair_same_date_count", "canonical_fight_id",
    "canonical_event_id", "classification", "review_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_source_date(value: str) -> str:
    return datetime.strptime((value or "").strip(), "%b %d, %Y").date().isoformat()


def main() -> int:
    raw = read_csv(RAW)
    xwalk = read_csv(XWALK)
    fights = read_csv(FIGHTS)
    events = read_csv(EVENTS)

    # Assert only fields this audit is allowed to depend on.
    required_raw = {
        "url", "event_title", "organisation", "date", "match_nr",
        "fighter1_url", "fighter2_url", "fighter1_name", "fighter2_name",
    }
    required_xwalk = {"external_fighter_url", "canonical_fighter_id", "review_status"}
    required_fights = {"fight_id", "event_id", "fighter_a_id", "fighter_b_id"}
    required_events = {"event_id", "event_date"}
    for label, rows, required in (
        ("raw", raw, required_raw), ("xwalk", xwalk, required_xwalk),
        ("fights", fights, required_fights), ("events", events, required_events),
    ):
        actual = set(rows[0]) if rows else set()
        missing = sorted(required - actual)
        if missing:
            raise SystemExit(f"{label} missing required columns: {missing}; actual={sorted(actual)}")

    trusted_by_url: dict[str, str] = {}
    duplicate_trusted_urls: set[str] = set()
    for row in xwalk:
        if (row.get("review_status") or "").strip() != "trusted":
            continue
        url = (row.get("external_fighter_url") or "").strip()
        fid = (row.get("canonical_fighter_id") or "").strip()
        if not url or not fid:
            continue
        if url in trusted_by_url and trusted_by_url[url] != fid:
            duplicate_trusted_urls.add(url)
        trusted_by_url[url] = fid
    if duplicate_trusted_urls:
        raise SystemExit(f"trusted crosswalk maps external URL to multiple canonical IDs: {sorted(duplicate_trusted_urls)[:10]}")

    event_date_by_id = {
        (r.get("event_id") or "").strip(): (r.get("event_date") or "").strip()
        for r in events if (r.get("event_id") or "").strip()
    }
    fights_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for fight in fights:
        a = (fight.get("fighter_a_id") or "").strip()
        b = (fight.get("fighter_b_id") or "").strip()
        if a and b and a != b:
            fights_by_pair[tuple(sorted((a, b)))].append(fight)

    source_key_counts = Counter(
        ((r.get("url") or "").strip(), (r.get("match_nr") or "").strip()) for r in raw
    )
    duplicate_keys = {k for k, n in source_key_counts.items() if n > 1}

    counts = Counter()
    org_counts_by_class: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[dict[str, str | int]]] = defaultdict(list)
    out_rows: list[dict[str, str | int]] = []

    for row in raw:
        source_url = (row.get("url") or "").strip()
        match_nr = (row.get("match_nr") or "").strip()
        source_key = (source_url, match_nr)
        org = (row.get("organisation") or "").strip()
        try:
            source_date = parse_source_date(row.get("date") or "")
        except ValueError as exc:
            raise SystemExit(f"source date stopped matching audited %b %d, %Y semantics: {row.get('date')!r}") from exc

        f1_url = (row.get("fighter1_url") or "").strip()
        f2_url = (row.get("fighter2_url") or "").strip()
        f1_id = trusted_by_url.get(f1_url, "")
        f2_id = trusted_by_url.get(f2_url, "")
        trusted_count = int(bool(f1_id)) + int(bool(f2_id))
        pair_matches: list[dict[str, str]] = []
        same_date: list[dict[str, str]] = []

        if source_key in duplicate_keys:
            classification = "duplicate_source_fight_key_quarantine"
        elif trusted_count != 2 or f1_id == f2_id:
            classification = "unresolved_trusted_fighter_identity"
        else:
            pair = tuple(sorted((f1_id, f2_id)))
            pair_matches = fights_by_pair.get(pair, [])
            same_date = [
                fight for fight in pair_matches
                if event_date_by_id.get((fight.get("event_id") or "").strip(), "") == source_date
            ]
            if len(same_date) == 1:
                classification = "exact_ufc_overlap_pair_plus_date"
            elif len(same_date) > 1:
                classification = "ambiguous_multiple_canonical_pair_plus_date"
            elif org == UFC_ORG and pair_matches:
                classification = "ufc_label_pair_exists_date_mismatch_review"
            elif org == UFC_ORG:
                classification = "ufc_label_not_in_canonical_spine_review"
            elif pair_matches:
                classification = "non_ufc_pair_has_canonical_ufc_history_no_date_overlap"
            else:
                classification = "non_ufc_cross_promotion_candidate"

        canonical = same_date[0] if len(same_date) == 1 else {}
        counts[classification] += 1
        org_counts_by_class[classification][org] += 1
        out = {
            "source_event_url": source_url,
            "source_match_nr": match_nr,
            "source_event_title": (row.get("event_title") or "").strip(),
            "source_organisation": org,
            "source_event_date": source_date,
            "fighter1_url": f1_url,
            "fighter2_url": f2_url,
            "fighter1_name": (row.get("fighter1_name") or "").strip(),
            "fighter2_name": (row.get("fighter2_name") or "").strip(),
            "fighter1_canonical_id": f1_id,
            "fighter2_canonical_id": f2_id,
            "trusted_fighter_count": trusted_count,
            "canonical_pair_fight_count": len(pair_matches),
            "canonical_pair_same_date_count": len(same_date),
            "canonical_fight_id": (canonical.get("fight_id") or "").strip(),
            "canonical_event_id": (canonical.get("event_id") or "").strip(),
            "classification": classification,
            "review_status": "candidate" if classification == "non_ufc_cross_promotion_candidate" else "audit_only",
        }
        out_rows.append(out)
        if len(examples[classification]) < 25:
            examples[classification].append({
                "source_event_url": source_url,
                "source_match_nr": match_nr,
                "event_title": out["source_event_title"],
                "organisation": org,
                "source_event_date": source_date,
                "fighter1_name": out["fighter1_name"],
                "fighter2_name": out["fighter2_name"],
                "canonical_pair_fight_count": len(pair_matches),
                "canonical_pair_same_date_count": len(same_date),
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(out_rows)

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_rows": len(raw),
        "trusted_external_fighter_urls": len(trusted_by_url),
        "duplicate_source_fight_keys": len(duplicate_keys),
        "classification_counts": dict(counts),
        "organisation_counts_by_classification": {
            k: dict(v.most_common()) for k, v in sorted(org_counts_by_class.items())
        },
        "examples": dict(examples),
        "output": str(OUT_CSV.relative_to(ROOT)),
        "decision": {
            "canonical_external_fights_written": False,
            "exact_ufc_overlap_rule_promoted_candidate": "two trusted fighter URL crosswalks + exact unordered canonical participant pair + exact canonical event date",
            "pair_only_overlap_is_sufficient": False,
            "ufc_label_alone_is_sufficient": False,
            "non_ufc_cross_promotion_rows_promoted": False,
            "required_next": "Review exact-overlap coverage and all UFC-labelled misses. Only after those explain cleanly may non-UFC cross-promotion candidates be deduplicated and inserted with source event/fight keys and provenance."
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_rows": len(raw),
        "trusted_external_fighter_urls": len(trusted_by_url),
        "duplicate_source_fight_keys": len(duplicate_keys),
        "classification_counts": dict(counts),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
