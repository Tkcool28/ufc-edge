#!/usr/bin/env python3
"""Audit page-level UFC weigh-in marker/footnote semantics.

DATA PHASE ONLY. No canonical fields are promoted by this pass.

The candidate extractor preserves inline *, **, *** and **** markers but explanatory
footnotes often live elsewhere on the official article page. This audit reconnects those
page-level definitions to the markers actually used by extracted fighter observations and
classifies only explicit source language (miss, catchweight, purse/penalty, re-weigh/attempt).
"""
from __future__ import annotations

import csv
import html as html_lib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "data/raw/ufc_official_articles/20260821T210000Z/weigh_in"
MANIFEST = FAMILY / "manifest.json"
CANDIDATES = ROOT / "data/derived/discovery/ufc_weigh_in_rows_candidate.csv"
OUT = ROOT / "provenance/audits/ufc_weigh_in_footnote_semantics_latest.json"

LEADING_MARKER_RE = re.compile(r"^\s*(\*{1,4})\s*(.*)$")
SEMANTIC_PATTERNS = {
    "missed_weight": re.compile(r"\b(?:miss(?:ed|es|ing)?\s+(?:the\s+)?weight|miss(?:ed|es|ing)?\s+(?:the\s+)?(?:division|contract)?\s*limit|over\s*(?:the\s+)?weight\s*limit|overweight)\b", re.I),
    "catchweight": re.compile(r"\bcatch\s*weight\b", re.I),
    "purse_or_penalty": re.compile(r"\b(?:forfeit(?:s|ed)?|fine(?:d)?|penalt(?:y|ies)|purse|percent|%)\b", re.I),
    "additional_attempt": re.compile(r"\b(?:second\s+attempt|additional\s+attempt|another\s+attempt|re[- ]?weigh|one\s+hour|two\s+hours?|extra\s+hour)\b", re.I),
    "title_limit": re.compile(r"\b(?:championship|title)\s+(?:fight|bout|weight|limit)\b|\bchampionship\s+weight\b", re.I),
}


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
        if not self.skip and tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr", "td", "th", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1
        if not self.skip and tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr", "td", "th"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)

    def lines(self) -> list[str]:
        raw = html_lib.unescape("".join(self.parts)).replace("\xa0", " ")
        return [x for x in (re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()) if x]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def records_by_index() -> dict[int, dict[str, Any]]:
    final = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if final.get("complete_family_snapshot") is not True:
        raise RuntimeError("weigh-in family snapshot incomplete")
    result: dict[int, dict[str, Any]] = {}
    expected = 0
    for cm in final.get("chunk_manifests") or []:
        chunk = json.loads((ROOT / cm).read_text(encoding="utf-8"))
        if int(chunk["chunk_start_index"]) != expected:
            raise RuntimeError(f"chunk gap at {expected}")
        for row in chunk.get("records") or []:
            idx = int(row["candidate_index"])
            if idx != expected:
                raise RuntimeError(f"record gap at {expected}")
            result[idx] = row
            expected += 1
    if expected != int(final["candidate_count"]):
        raise RuntimeError("manifest count mismatch")
    return result


def main() -> int:
    candidates = read_csv(CANDIDATES)
    records = records_by_index()
    markers_by_article: dict[int, Counter[str]] = defaultdict(Counter)
    for row in candidates:
        idx = int(row["article_candidate_index"])
        for marker in (row.get("marker_a") or "", row.get("marker_b") or ""):
            marker = marker.strip()
            if marker:
                markers_by_article[idx][marker] += 1

    counts = Counter()
    marker_definition_counts = Counter()
    marker_semantics: dict[str, Counter[str]] = defaultdict(Counter)
    semantic_page_counts: dict[str, set[int]] = defaultdict(set)
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    article_summaries: list[dict[str, Any]] = []

    for idx, used in sorted(markers_by_article.items()):
        record = records[idx]
        parser = TextParser()
        parser.feed((ROOT / str(record["path"])).read_text(encoding="utf-8", errors="replace"))
        lines = parser.lines()
        counts["articles_with_inline_markers"] += 1
        counts["inline_marker_observations"] += sum(used.values())
        definitions: list[dict[str, Any]] = []
        semantic_lines: list[dict[str, Any]] = []

        for line in lines:
            semantics = [name for name, pattern in SEMANTIC_PATTERNS.items() if pattern.search(line)]
            if semantics:
                for semantic in semantics:
                    semantic_page_counts[semantic].add(idx)
                if len(semantic_lines) < 25:
                    semantic_lines.append({"line": line, "semantics": semantics})
            marker_match = LEADING_MARKER_RE.match(line)
            if not marker_match:
                continue
            marker, body = marker_match.groups()
            if marker not in used:
                continue
            marker_definition_counts[marker] += 1
            body_semantics = [name for name, pattern in SEMANTIC_PATTERNS.items() if pattern.search(body)]
            for semantic in body_semantics:
                marker_semantics[marker][semantic] += 1
            definition = {"marker": marker, "line": line, "semantics": body_semantics}
            definitions.append(definition)
            if len(examples[f"marker_{len(marker)}"]) < 40:
                examples[f"marker_{len(marker)}"].append({
                    "article_url": record["catalog_url"], "line": line, "semantics": body_semantics,
                    "marker_observations_on_page": used[marker],
                })

        if definitions:
            counts["articles_with_marker_definition_line"] += 1
        else:
            counts["articles_without_marker_definition_line"] += 1
            if len(examples["no_marker_definition"]) < 40:
                examples["no_marker_definition"].append({
                    "article_url": record["catalog_url"], "markers_used": dict(used),
                    "semantic_line_samples": semantic_lines[:8],
                })
        article_summaries.append({
            "candidate_index": idx,
            "article_url": record["catalog_url"],
            "markers_used": dict(used),
            "marker_definitions": definitions,
            "semantic_line_samples": semantic_lines,
        })

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_rows": len(candidates),
        "counts": dict(counts),
        "inline_marker_counts": {marker: sum(c.values()) for marker, c in sorted({m: Counter({m: sum(v[m] for v in markers_by_article.values())}) for m in {x for v in markers_by_article.values() for x in v}}.items())},
        "marker_definition_line_counts": dict(sorted(marker_definition_counts.items())),
        "marker_semantic_line_counts": {marker: dict(sorted(values.items())) for marker, values in sorted(marker_semantics.items())},
        "semantic_page_counts_among_marker_pages": {name: len(pages) for name, pages in sorted(semantic_page_counts.items())},
        "examples": dict(examples),
        "article_summaries": article_summaries,
        "decision": {
            "canonical_annotation_rules_promoted": False,
            "marker_is_globally_stable_semantic_code": False,
            "page_local_marker_definition_required_for_marker_interpretation": True,
            "missing_definition_means_unknown": True,
            "required_next": "Inspect marker definition consistency by page and semantic class. Any promoted miss/penalty/attempt rule must be page-local and source-explicit; never assign a global meaning to *, **, *** or ****."
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "articles_with_inline_markers": counts["articles_with_inline_markers"],
        "articles_with_marker_definition_line": counts["articles_with_marker_definition_line"],
        "articles_without_marker_definition_line": counts["articles_without_marker_definition_line"],
        "marker_definition_line_counts": dict(marker_definition_counts),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
