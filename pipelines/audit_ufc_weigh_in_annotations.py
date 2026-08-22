#!/usr/bin/env python3
"""Audit explicit annotation language in archived official UFC weigh-in rows.

No fight identity and no inferred contract limits are used here. This pass only inventories
what the official source explicitly says around extracted scale-weight pairs so canonical
annotation rules can be defined from observed text rather than assumptions.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "data/derived/discovery/ufc_weigh_in_rows_candidate.csv"
OUT = ROOT / "provenance/audits/ufc_weigh_in_annotations_latest.json"

PATTERNS = {
    "asterisk": re.compile(r"\*"),
    "miss_phrase": re.compile(r"\b(?:miss(?:ed|es|ing)?\s+(?:weight|the\s+weight)|failed\s+to\s+make\s+weight|over\s+(?:the\s+)?weight\s+limit)\b", re.I),
    "pounds_over_phrase": re.compile(r"\b(?:\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)\s+(?:over|heavy)\b|\b(?:over|heavy)\s+by\s+(?:\d+(?:\.\d+)?)\b", re.I),
    "catchweight": re.compile(r"\bcatch\s*weight\b|\bcatchweight\b", re.I),
    "purse_forfeit": re.compile(r"\b(?:forfeit|forfeits|forfeited|fine|fined)\b.{0,80}\b(?:purse|percent|%)\b|\b\d+(?:\.\d+)?%\b.{0,80}\bpurse\b", re.I),
    "percent": re.compile(r"\b\d+(?:\.\d+)?\s*%"),
    "second_attempt": re.compile(r"\b(?:second\s+attempt|second\s+try|re-?weigh|weighed\s+in\s+again|returned\s+to\s+the\s+scale)\b", re.I),
    "extra_time": re.compile(r"\b(?:additional|extra)\s+(?:hour|time|minutes?)\b", re.I),
    "commission_allowance": re.compile(r"\b(?:one|1)(?:\.0)?\s*(?:lb|lbs|pound)?\s*(?:allowance|over)\b", re.I),
    "title_bout": re.compile(r"\btitle\s+(?:bout|fight)|championship\b", re.I),
}


def read_rows() -> list[dict[str, str]]:
    with CANDIDATES.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    rows = read_rows()
    counts = Counter()
    marker_counts = Counter()
    examples: dict[str, list[dict[str, str]]] = defaultdict(list)
    marker_examples: dict[str, list[dict[str, str]]] = defaultdict(list)
    pages_by_pattern: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        line = row.get("raw_source_line") or ""
        url = row.get("article_url") or ""
        for side in ("a", "b"):
            marker = (row.get(f"marker_{side}") or "").strip()
            marker_counts[marker if marker else "<empty>"] += 1
            if marker and len(marker_examples[marker]) < 30:
                marker_examples[marker].append({
                    "url": url,
                    "fighter": row.get(f"fighter_{side}_text") or "",
                    "weight": row.get(f"scale_weight_{side}_lbs") or "",
                    "marker": marker,
                    "line": line,
                })
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                counts[name] += 1
                pages_by_pattern[name].add(url)
                if len(examples[name]) < 50:
                    examples[name].append({
                        "url": url,
                        "fighter_a": row.get("fighter_a_text") or "",
                        "weight_a": row.get("scale_weight_a_lbs") or "",
                        "marker_a": row.get("marker_a") or "",
                        "fighter_b": row.get("fighter_b_text") or "",
                        "weight_b": row.get("scale_weight_b_lbs") or "",
                        "marker_b": row.get("marker_b") or "",
                        "line": line,
                    })

    # Cross-pattern combinations show whether source conventions are stable enough to promote.
    combo_counts = Counter()
    for row in rows:
        line = row.get("raw_source_line") or ""
        matched = tuple(sorted(name for name, pattern in PATTERNS.items() if pattern.search(line)))
        if matched:
            combo_counts["+".join(matched)] += 1

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_rows": len(rows),
        "marker_counts": dict(marker_counts),
        "pattern_row_counts": dict(counts),
        "pattern_page_counts": {k: len(v) for k, v in pages_by_pattern.items()},
        "pattern_combination_counts": dict(combo_counts),
        "marker_examples": dict(marker_examples),
        "pattern_examples": dict(examples),
        "decision": {
            "canonical_annotation_rules_promoted": False,
            "scale_weights_are_source_explicit": True,
            "contract_limit_inference_allowed": False,
            "required_next": "Resolve exact fight/fighter identity, then promote only annotation fields whose source language/markers are unambiguous in this audit."
        }
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(rows),
        "markers": dict(marker_counts),
        "patterns": dict(counts),
        "pages": {k: len(v) for k, v in pages_by_pattern.items()},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
