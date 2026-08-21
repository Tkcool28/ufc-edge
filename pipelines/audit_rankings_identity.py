#!/usr/bin/env python3
"""Audit exact-name identity coverage for the dated historical UFC rankings snapshot.

This is deliberately conservative: no fuzzy matching, nickname substitution, or future
ranking inference. It emits candidate links only when a ranking display name maps to
exactly one normalized Greco/UFCStats fighter identity.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

GRECO = Path("data/raw/greco1899/8e40eb945e11/ufc_fighter_details.csv")
RANKINGS = Path("data/raw/tidytuesday_ufc_rankings/107ff6c70de0/ufc_rankings_dataset.csv")
OUT_JSON = Path("provenance/audits/rankings_identity_latest.json")
OUT_CSV = Path("data/derived/identity/rankings_greco_name_crosswalk_candidate.csv")


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def main() -> int:
    greco_by_norm: dict[str, list[dict[str, str]]] = defaultdict(list)
    with GRECO.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            name = " ".join(x.strip() for x in (row.get("FIRST") or "", row.get("LAST") or "") if x.strip())
            url = (row.get("URL") or "").strip()
            if not name or not url:
                continue
            greco_by_norm[normalize_name(name)].append({"name": name, "url": url})

    unique_greco: dict[str, dict[str, str]] = {}
    ambiguous_greco: dict[str, list[dict[str, str]]] = {}
    for norm, rows in greco_by_norm.items():
        urls = {row["url"] for row in rows}
        if len(urls) == 1:
            unique_greco[norm] = rows[0]
        else:
            ambiguous_greco[norm] = rows

    rows_total = 0
    status_counts = Counter()
    year_counts: dict[str, Counter] = defaultdict(Counter)
    ranking_names: dict[str, dict[str, str]] = {}
    min_date = None
    max_date = None

    with RANKINGS.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"date", "weightclass", "fighter", "rank"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise RuntimeError(f"Ranking columns changed: {reader.fieldnames}")
        for row in reader:
            rows_total += 1
            raw_name = (row.get("fighter") or "").strip()
            date = (row.get("date") or "").strip()
            if date:
                min_date = date if min_date is None or date < min_date else min_date
                max_date = date if max_date is None or date > max_date else max_date
            year = date[:4] if len(date) >= 4 else "unknown"
            norm = normalize_name(raw_name)
            if not norm:
                status = "blank_name"
            elif norm in ambiguous_greco:
                status = "ambiguous_exact_name"
            elif norm in unique_greco:
                status = "unique_exact_name"
            else:
                status = "unmatched_exact_name"
            status_counts[status] += 1
            year_counts[year][status] += 1
            if raw_name:
                ranking_names.setdefault(raw_name, {"normalized_name": norm, "status": status})

    candidate_rows = []
    name_status = Counter()
    unmatched_examples = []
    ambiguous_examples = []
    for raw_name, info in sorted(ranking_names.items(), key=lambda kv: kv[0].lower()):
        norm = info["normalized_name"]
        status = info["status"]
        name_status[status] += 1
        if status == "unique_exact_name":
            target = unique_greco[norm]
            candidate_rows.append({
                "ranking_fighter_name": raw_name,
                "normalized_name": norm,
                "greco_fighter_name": target["name"],
                "greco_fighter_url": target["url"],
                "match_method": "exact_normalized_display_name_unique",
                "review_status": "candidate",
            })
        elif status == "unmatched_exact_name" and len(unmatched_examples) < 100:
            unmatched_examples.append(raw_name)
        elif status == "ambiguous_exact_name" and len(ambiguous_examples) < 100:
            ambiguous_examples.append({
                "ranking_fighter_name": raw_name,
                "normalized_name": norm,
                "greco_candidates": ambiguous_greco[norm],
            })

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "ranking_fighter_name", "normalized_name", "greco_fighter_name",
        "greco_fighter_url", "match_method", "review_status",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidate_rows)

    matched_rows = status_counts["unique_exact_name"]
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "rankings_source": str(RANKINGS),
        "greco_source": str(GRECO),
        "ranking_rows": rows_total,
        "ranking_date_min": min_date,
        "ranking_date_max": max_date,
        "distinct_ranking_display_names": len(ranking_names),
        "row_status_counts": dict(status_counts),
        "row_unique_exact_fraction": matched_rows / rows_total if rows_total else None,
        "distinct_name_status_counts": dict(name_status),
        "candidate_crosswalk_rows": len(candidate_rows),
        "candidate_crosswalk_csv": str(OUT_CSV),
        "greco_normalized_name_collisions": len(ambiguous_greco),
        "coverage_by_year": {year: dict(counts) for year, counts in sorted(year_counts.items())},
        "unmatched_name_examples": unmatched_examples,
        "ambiguous_name_examples": ambiguous_examples,
        "decision": {
            "canonical_promoted": False,
            "fuzzy_matching_used": False,
            "candidate_rule": "Only exact normalized ranking display names resolving to one Greco fighter URL are emitted as candidates.",
            "historical_join_rule": "A ranking observation may be used only when ranking_date is strictly before or otherwise valid at the target prediction cutoff; future-nearest joins are prohibited.",
            "unmatched_rule": "Unmatched or ambiguous names remain unresolved rather than guessed.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": rows_total,
        "distinct_names": len(ranking_names),
        "candidate_names": len(candidate_rows),
        "row_unique_exact_fraction": report["row_unique_exact_fraction"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
