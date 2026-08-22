#!/usr/bin/env python3
"""Audit structure of the complete official UFC weigh-in article archive.

No canonical rows are produced. This pass measures what can be extracted consistently
from the archived HTML and records examples for every weak/ambiguous class.
"""
from __future__ import annotations

import html as html_lib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SERIES_ROOT = ROOT / "data/raw/ufc_official_articles/20260821T210000Z/weigh_in"
FINAL_MANIFEST = SERIES_ROOT / "manifest.json"
OUT_JSON = ROOT / "provenance/audits/ufc_weigh_in_structure_latest.json"
OUT_MD = ROOT / "provenance/audits/ufc_weigh_in_structure_latest.md"

PAIR_PATTERNS = [
    (
        "paren_vs_paren",
        re.compile(
            r"(?P<a>[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’ .\-]{1,70}?)\s*\(\s*(?P<wa>\d{2,3}(?:\.\d{1,2})?)\s*\)"
            r"\s*(?:vs\.?|versus)\s*"
            r"(?P<b>[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’ .\-]{1,70}?)\s*\(\s*(?P<wb>\d{2,3}(?:\.\d{1,2})?)\s*\)",
            re.I,
        ),
    ),
    (
        "dash_weight_vs_dash_weight",
        re.compile(
            r"(?P<a>[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’ .\-]{1,70}?)\s*[-–—:]\s*(?P<wa>\d{2,3}(?:\.\d{1,2})?)"
            r"\s*(?:lbs?\.?|pounds?)?\s*(?:vs\.?|versus)\s*"
            r"(?P<b>[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’ .\-]{1,70}?)\s*[-–—:]\s*(?P<wb>\d{2,3}(?:\.\d{1,2})?)",
            re.I,
        ),
    ),
]

MISS_RE = re.compile(r"\b(?:miss(?:ed|es|ing)?\s+(?:the\s+)?weight|overweight|over\s+the\s+.*?limit)\b", re.I)
CATCH_RE = re.compile(r"\bcatch\s*weight\b|\bcatchweight\b", re.I)
FORFEIT_RE = re.compile(r"\bforfeit(?:s|ed|ing)?\b|\bpercent\s+of\s+(?:his|her|their)\s+purse\b", re.I)
SECOND_RE = re.compile(r"\b(?:second|2nd)\s+(?:weigh[- ]?in|attempt)|\bre-?weigh", re.I)
WEIGHT_TOKEN_RE = re.compile(r"(?<!\d)(\d{2,3}(?:\.\d{1,2})?)(?:\s*(?:lbs?\.?|pounds?))?(?!\d)", re.I)


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            data = {str(k).lower(): (v or "") for k, v in attrs}
            key = data.get("property") or data.get("name")
            value = data.get("content")
            if key and value and key not in self.meta:
                self.meta[key.lower()] = value
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

    def text(self) -> str:
        raw = html_lib.unescape("".join(self.parts)).replace("\xa0", " ")
        lines = []
        for line in raw.splitlines():
            clean = re.sub(r"\s+", " ", line).strip()
            if clean:
                lines.append(clean)
        return "\n".join(lines)

    def title(self) -> str:
        return self.meta.get("og:title") or re.sub(r"\s+", " ", "".join(self.title_parts)).strip()


def load_records() -> list[dict[str, Any]]:
    final = json.loads(FINAL_MANIFEST.read_text(encoding="utf-8"))
    if final.get("complete_family_snapshot") is not True:
        raise RuntimeError("Official weigh-in family is not complete")
    records: list[dict[str, Any]] = []
    expected = 0
    for raw_path in final.get("chunk_manifests") or []:
        path = ROOT / raw_path
        chunk = json.loads(path.read_text(encoding="utf-8"))
        if int(chunk["chunk_start_index"]) != expected:
            raise RuntimeError(f"Chunk gap: expected {expected}, got {chunk['chunk_start_index']}")
        for row in chunk.get("records") or []:
            if int(row["candidate_index"]) != expected:
                raise RuntimeError(f"Record index gap: expected {expected}, got {row['candidate_index']}")
            records.append(row)
            expected += 1
    if expected != int(final["candidate_count"]):
        raise RuntimeError(f"Final record count mismatch: {expected} vs {final['candidate_count']}")
    return records


def context(text: str, pattern: re.Pattern[str], radius: int = 180) -> str | None:
    match = pattern.search(text)
    if not match:
        return None
    start = max(0, match.start() - radius)
    stop = min(len(text), match.end() + radius)
    return re.sub(r"\s+", " ", text[start:stop]).strip()


def plausible_weight(value: str) -> bool:
    try:
        number = float(value)
    except ValueError:
        return False
    return 90 <= number <= 300


def main() -> int:
    records = load_records()
    counts = Counter()
    pattern_counts = Counter()
    title_years = Counter()
    pages: list[dict[str, Any]] = []
    examples: dict[str, list[dict[str, Any]]] = {
        "no_pair_pattern": [],
        "multiple_pair_patterns": [],
        "miss_language": [],
        "catchweight_language": [],
        "forfeit_language": [],
        "second_attempt_language": [],
    }

    for record in records:
        path = ROOT / str(record["path"])
        body = path.read_text(encoding="utf-8", errors="replace")
        parser = VisibleText()
        parser.feed(body)
        text = parser.text()
        collapsed = re.sub(r"\s+", " ", text)
        title = parser.title()
        published = parser.meta.get("article:published_time")
        year = None
        if published and re.match(r"^\d{4}", published):
            year = published[:4]
            title_years[year] += 1

        pair_matches: list[dict[str, Any]] = []
        per_pattern = Counter()
        for pattern_name, pattern in PAIR_PATTERNS:
            for match in pattern.finditer(collapsed):
                if not plausible_weight(match.group("wa")) or not plausible_weight(match.group("wb")):
                    continue
                pair_matches.append(
                    {
                        "pattern": pattern_name,
                        "fighter_a_text": re.sub(r"\s+", " ", match.group("a")).strip(" -–—:"),
                        "fighter_b_text": re.sub(r"\s+", " ", match.group("b")).strip(" -–—:"),
                        "weight_a": match.group("wa"),
                        "weight_b": match.group("wb"),
                    }
                )
                per_pattern[pattern_name] += 1
                pattern_counts[pattern_name] += 1

        all_weight_tokens = [m.group(1) for m in WEIGHT_TOKEN_RE.finditer(collapsed) if plausible_weight(m.group(1))]
        miss = bool(MISS_RE.search(collapsed))
        catch = bool(CATCH_RE.search(collapsed))
        forfeit = bool(FORFEIT_RE.search(collapsed))
        second = bool(SECOND_RE.search(collapsed))

        counts["pages"] += 1
        counts["pages_with_pair_pattern"] += bool(pair_matches)
        counts["pages_without_pair_pattern"] += not pair_matches
        counts["pages_with_multiple_pairs"] += len(pair_matches) > 1
        counts["pages_with_plausible_weight_token"] += bool(all_weight_tokens)
        counts["pages_with_miss_language"] += miss
        counts["pages_with_catchweight_language"] += catch
        counts["pages_with_forfeit_language"] += forfeit
        counts["pages_with_second_attempt_language"] += second
        counts["total_pair_matches"] += len(pair_matches)

        page_summary = {
            "candidate_index": int(record["candidate_index"]),
            "url": record["catalog_url"],
            "title": title,
            "published_time": published,
            "year": year,
            "pair_match_count": len(pair_matches),
            "pair_pattern_counts": dict(per_pattern),
            "plausible_weight_token_count": len(all_weight_tokens),
            "miss_language": miss,
            "catchweight_language": catch,
            "forfeit_language": forfeit,
            "second_attempt_language": second,
        }
        pages.append(page_summary)

        compact = {**page_summary, "path": str(record["path"])}
        if not pair_matches and len(examples["no_pair_pattern"]) < 30:
            compact["weight_context"] = context(collapsed, WEIGHT_TOKEN_RE)
            examples["no_pair_pattern"].append(compact)
        if len(pair_matches) > 1 and len(examples["multiple_pair_patterns"]) < 15:
            compact["pair_samples"] = pair_matches[:5]
            examples["multiple_pair_patterns"].append(compact)
        for key, enabled, regex in (
            ("miss_language", miss, MISS_RE),
            ("catchweight_language", catch, CATCH_RE),
            ("forfeit_language", forfeit, FORFEIT_RE),
            ("second_attempt_language", second, SECOND_RE),
        ):
            if enabled and len(examples[key]) < 15:
                sample = dict(compact)
                sample["context"] = context(collapsed, regex)
                examples[key].append(sample)

    output = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_manifest": str(FINAL_MANIFEST.relative_to(ROOT)),
        "counts": dict(counts),
        "pair_pattern_counts": dict(pattern_counts),
        "published_year_counts": dict(sorted(title_years.items())),
        "examples": examples,
        "decision": {
            "canonical_rows_produced": False,
            "next_gate": "Design extractor only after recurring page structures and unmatched classes are reviewed.",
            "identity_matching_not_attempted": True,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    total = counts["pages"]
    lines = [
        "# Official UFC weigh-in article structure audit",
        "",
        f"- Complete official article pages audited: **{total}**",
        f"- Pages with a recognized fighter-vs-fighter weight pattern: **{counts['pages_with_pair_pattern']}** ({counts['pages_with_pair_pattern']/total:.1%})",
        f"- Pages with any plausible 90-300 weight token: **{counts['pages_with_plausible_weight_token']}** ({counts['pages_with_plausible_weight_token']/total:.1%})",
        f"- Total recognized fighter-pair weight rows: **{counts['total_pair_matches']}**",
        f"- Pages with missed-weight language: **{counts['pages_with_miss_language']}**",
        f"- Pages with catchweight language: **{counts['pages_with_catchweight_language']}**",
        f"- Pages with purse-forfeit language: **{counts['pages_with_forfeit_language']}**",
        f"- Pages with second-attempt/re-weigh language: **{counts['pages_with_second_attempt_language']}**",
        "",
        "No weigh-in row is canonicalized by this audit.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"pages": total, "recognized_pages": counts["pages_with_pair_pattern"], "pair_rows": counts["total_pair_matches"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
