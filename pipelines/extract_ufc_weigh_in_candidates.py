#!/usr/bin/env python3
"""Extract source-faithful candidate bout weigh-in rows from official UFC articles.

This is a derived discovery layer, NOT canonical data. It extracts only explicit
fighter(weight) vs fighter(weight) structures from the complete official UFC weigh-in
archive. Identity resolution, miss/catchweight interpretation, and fight matching happen
in later audited passes.
"""
from __future__ import annotations

import csv
import html as html_lib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FAMILY = ROOT / "data/raw/ufc_official_articles/20260821T210000Z/weigh_in"
MANIFEST = FAMILY / "manifest.json"
OUT = ROOT / "data/derived/discovery/ufc_weigh_in_rows_candidate.csv"
AUDIT = ROOT / "provenance/audits/ufc_weigh_in_candidate_extraction_latest.json"

PAIR_RE = re.compile(
    r"(?P<a>[^\n]{1,120}?)\s*\(\s*(?P<wa>\d{2,3}(?:\.\d{1,2})?)\s*\)\s*(?P<ma>[*†‡#]{0,4})"
    r"\s*(?:vs\.?|versus)\s*"
    r"(?P<b>[^\n]{1,120}?)\s*\(\s*(?P<wb>\d{2,3}(?:\.\d{1,2})?)\s*\)\s*(?P<mb>[*†‡#]{0,4})",
    re.I,
)
SECTION_PREFIX_RE = re.compile(
    r"^(?:main\s+event|co-main\s+event|main\s+card|prelims?|early\s+prelims?|"
    r"featured\s+bout|[a-z’' -]+weight\s+bout|women[’']?s\s+[a-z’' -]+weight\s+bout|"
    r"catchweight\s+bout(?:\s*\([^)]*\))?|title\s+bout)\s*[-–—:]\s*",
    re.I,
)


class TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        data = {str(k).lower(): (v or "") for k, v in attrs}
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            key = data.get("property") or data.get("name")
            if key and data.get("content") and key.lower() not in self.meta:
                self.meta[key.lower()] = data["content"]
        if not self.skip and tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr", "td", "th", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1
        if not self.skip and tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "tr", "td", "th"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        if self.in_title:
            self.title_parts.append(data)
        self.parts.append(data)

    def lines(self) -> list[str]:
        raw = html_lib.unescape("".join(self.parts)).replace("\xa0", " ")
        return [x for x in (re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()) if x]

    def title(self) -> str:
        return self.meta.get("og:title") or re.sub(r"\s+", " ", "".join(self.title_parts)).strip()


def load_records() -> list[dict[str, Any]]:
    final = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if final.get("complete_family_snapshot") is not True:
        raise RuntimeError("weigh-in family is not complete")
    out: list[dict[str, Any]] = []
    expected = 0
    for cm in final.get("chunk_manifests") or []:
        chunk = json.loads((ROOT / cm).read_text(encoding="utf-8"))
        if int(chunk["chunk_start_index"]) != expected:
            raise RuntimeError(f"chunk gap at {expected}")
        for row in chunk.get("records") or []:
            if int(row["candidate_index"]) != expected:
                raise RuntimeError(f"record gap at {expected}")
            out.append(row); expected += 1
    if expected != int(final["candidate_count"]):
        raise RuntimeError("record count mismatch")
    return out


def clean_fighter(value: str) -> str:
    text = re.sub(r"\s+", " ", value).strip(" -*†‡#:;|–—")
    # Article lines often prefix a bout type before the fighter name.
    for _ in range(3):
        newer = SECTION_PREFIX_RE.sub("", text).strip()
        if newer == text:
            break
        text = newer
    # A remaining descriptive prefix followed by a colon is transport text, not name.
    if ":" in text:
        tail = text.rsplit(":", 1)[-1].strip()
        if 2 <= len(tail) <= 80:
            text = tail
    return text.strip(" -*†‡#:;|–—")


def plausible(name: str, weight: str) -> bool:
    try:
        w = float(weight)
    except ValueError:
        return False
    if not (90 <= w <= 300):
        return False
    if not (2 <= len(name) <= 80):
        return False
    if not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", name):
        return False
    return True


def main() -> int:
    records = load_records()
    rows: list[dict[str, Any]] = []
    counts = Counter()
    page_counts = Counter()
    rejected_examples: list[dict[str, Any]] = []

    for record in records:
        parser = TextParser()
        parser.feed((ROOT / str(record["path"])).read_text(encoding="utf-8", errors="replace"))
        title = parser.title()
        published = parser.meta.get("article:published_time") or ""
        seen_on_page: set[tuple[str, str, str, str]] = set()
        found = 0
        line_number = 0
        for line_number, line in enumerate(parser.lines(), 1):
            if " vs" not in line.lower() and " versus " not in line.lower():
                continue
            for match in PAIR_RE.finditer(line):
                a_raw, b_raw = match.group("a"), match.group("b")
                a, b = clean_fighter(a_raw), clean_fighter(b_raw)
                wa, wb = match.group("wa"), match.group("wb")
                if not plausible(a, wa) or not plausible(b, wb):
                    counts["rejected_implausible"] += 1
                    if len(rejected_examples) < 30:
                        rejected_examples.append({"url": record["catalog_url"], "line": line, "a": a, "b": b, "wa": wa, "wb": wb})
                    continue
                key = (a.casefold(), b.casefold(), wa, wb)
                if key in seen_on_page:
                    counts["duplicate_same_page_suppressed"] += 1
                    continue
                seen_on_page.add(key)
                found += 1
                rows.append({
                    "article_candidate_index": int(record["candidate_index"]),
                    "article_url": record["catalog_url"],
                    "article_title": title,
                    "article_published_time": published,
                    "source_path": record["path"],
                    "source_line_number": line_number,
                    "bout_ordinal_in_article": found,
                    "fighter_a_text": a,
                    "fighter_b_text": b,
                    "scale_weight_a_lbs": wa,
                    "scale_weight_b_lbs": wb,
                    "marker_a": match.group("ma") or "",
                    "marker_b": match.group("mb") or "",
                    "raw_source_line": line,
                    "extraction_rule": "explicit_parenthetical_weights_vs",
                    "review_status": "candidate",
                })
        page_counts[found] += 1
        counts["pages"] += 1
        counts["pages_with_candidates"] += found > 0
        counts["pages_without_candidates"] += found == 0
        counts["candidate_bouts"] += found

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "article_candidate_index", "article_url", "article_title", "article_published_time", "source_path",
        "source_line_number", "bout_ordinal_in_article", "fighter_a_text", "fighter_b_text",
        "scale_weight_a_lbs", "scale_weight_b_lbs", "marker_a", "marker_b", "raw_source_line",
        "extraction_rule", "review_status",
    ]
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_manifest": str(MANIFEST.relative_to(ROOT)),
        "output": str(OUT.relative_to(ROOT)),
        "counts": dict(counts),
        "candidate_bouts_per_page_distribution": {str(k): v for k, v in sorted(page_counts.items())},
        "rejected_examples": rejected_examples,
        "decision": {
            "canonical": False,
            "weights_are_source_explicit": True,
            "fighter_identity_resolved": False,
            "fight_identity_resolved": False,
            "miss_catchweight_penalty_semantics_resolved": False,
            "next_gate": "Exact fighter/fight identity and article annotation audit.",
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pages": counts["pages"], "pages_with_candidates": counts["pages_with_candidates"], "candidate_bouts": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
