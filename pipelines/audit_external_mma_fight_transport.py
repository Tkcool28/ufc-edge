#!/usr/bin/env python3
"""Audit structural semantics of the CC0 external MMA fight snapshot before canonicalization."""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/kaggle_pro_mma_fights/v1/pro_mma_fights.csv"
OUT = ROOT / "provenance/audits/external_mma_fight_transport_latest.json"


def rows() -> list[dict[str, str]]:
    with RAW.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def parse(value: str, fmt: str) -> str | None:
    try:
        return datetime.strptime((value or "").strip(), fmt).date().isoformat()
    except ValueError:
        return None


def main() -> int:
    data = rows()
    url_counts = Counter((r.get("url") or "").strip() for r in data)
    event_signature_counts = Counter(
        (
            (r.get("organisation") or "").strip(),
            (r.get("event_title") or "").strip(),
            (r.get("date") or "").strip(),
            (r.get("location") or "").strip(),
        )
        for r in data
    )
    event_url_signatures: dict[str, set[tuple[str, str, str, str]]] = defaultdict(set)
    for r in data:
        url = (r.get("url") or "").strip()
        if not url:
            continue
        event_url_signatures[url].add((
            (r.get("organisation") or "").strip(),
            (r.get("event_title") or "").strip(),
            (r.get("date") or "").strip(),
            (r.get("location") or "").strip(),
        ))

    raw_dates = [(r.get("date") or "").strip() for r in data]
    date_candidates = {
        "ISO_YMD": "%Y-%m-%d",
        "DMY_SLASH": "%d/%m/%Y",
        "MDY_SLASH": "%m/%d/%Y",
        "DMY_DASH": "%d-%m-%Y",
        "MDY_DASH": "%m-%d-%Y",
        "FULL_MONTH_DMY": "%d %B %Y",
        "FULL_MONTH_MDY": "%B %d, %Y",
        "ABBREV_MONTH_MDY": "%b %d, %Y",
    }
    date_parse_counts = {
        name: sum(parse(value, fmt) is not None for value in raw_dates)
        for name, fmt in date_candidates.items()
    }

    result1 = Counter((r.get("fighter1_result") or "").strip() for r in data)
    result2 = Counter((r.get("fighter2_result") or "").strip() for r in data)
    methods = Counter((r.get("win_method") or "").strip() for r in data)
    rounds = Counter((r.get("round") or "").strip() for r in data)
    times = Counter((r.get("time") or "").strip() for r in data)
    organisations = Counter((r.get("organisation") or "").strip() for r in data)

    pair_seen: Counter[tuple[str, str]] = Counter()
    for r in data:
        pair_seen[((r.get("url") or "").strip(), (r.get("match_nr") or "").strip())] += 1
    duplicate_url_match_pairs = sum(1 for count in pair_seen.values() if count > 1)
    duplicate_url_match_rows = sum(count for count in pair_seen.values() if count > 1)

    missing_counts = {
        field: sum(not (r.get(field) or "").strip() for r in data)
        for field in [
            "url", "event_title", "organisation", "date", "location", "match_nr",
            "fighter1_url", "fighter2_url", "fighter1_name", "fighter2_name",
            "fighter1_result", "fighter2_result", "win_method", "round", "time",
        ]
    }

    examples = [
        {k: r.get(k) for k in [
            "url", "event_title", "organisation", "date", "location", "match_nr",
            "fighter1_url", "fighter2_url", "fighter1_name", "fighter2_name",
            "fighter1_result", "fighter2_result", "win_method", "win_details", "round", "time",
        ]}
        for r in data[:25]
    ]

    payload = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "rows": len(data),
        "distinct_nonempty_url": sum(bool(k) for k in url_counts),
        "urls_used_by_multiple_rows": sum(count > 1 for url, count in url_counts.items() if url),
        "max_rows_per_url": max((count for url, count in url_counts.items() if url), default=0),
        "distinct_event_signatures": len(event_signature_counts),
        "event_urls_with_multiple_event_signatures": sum(len(v) > 1 for v in event_url_signatures.values()),
        "duplicate_url_match_pairs": duplicate_url_match_pairs,
        "duplicate_url_match_rows": duplicate_url_match_rows,
        "url_match_pair_unique_fraction": (len(pair_seen) - duplicate_url_match_pairs) / len(pair_seen) if pair_seen else 0,
        "date_parse_counts": date_parse_counts,
        "missing_counts": missing_counts,
        "fighter1_result_counts": dict(result1),
        "fighter2_result_counts": dict(result2),
        "organisation_counts": dict(organisations),
        "top_win_methods": methods.most_common(50),
        "round_counts": dict(rounds),
        "top_time_values": times.most_common(50),
        "examples": examples,
        "decision": {
            "canonicalization_promoted": False,
            "event_identity_candidate": "source event url if every nonempty url maps to exactly one event signature",
            "fight_identity_candidate": "(source event url, match_nr) except duplicate pair(s), which must be quarantined",
            "date_parser_candidate": "ABBREV_MONTH_MDY only if it explains essentially all nonmissing source dates",
            "required_next": "Promote only keys/date semantics that pass these exact gates, then deduplicate UFC overlap before canonical insertion."
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(data),
        "distinct_urls": payload["distinct_nonempty_url"],
        "urls_multiple_rows": payload["urls_used_by_multiple_rows"],
        "distinct_event_signatures": payload["distinct_event_signatures"],
        "event_urls_with_multiple_signatures": payload["event_urls_with_multiple_event_signatures"],
        "duplicate_url_match_pairs": duplicate_url_match_pairs,
        "date_parse_counts": date_parse_counts,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
