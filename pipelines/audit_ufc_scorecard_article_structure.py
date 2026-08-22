#!/usr/bin/env python3
"""Audit complete official UFC scorecard article archive for structured text vs images.

This pass does not OCR images or create canonical judge scores. It produces a candidate
catalog of official scorecard-related image URLs and quantifies how much score information
is directly present in HTML text.
"""
from __future__ import annotations

import csv
import html as html_lib
import json
import re
import urllib.parse
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SERIES_ROOT = ROOT / "data/raw/ufc_official_articles/20260821T210000Z/scorecard"
FINAL_MANIFEST = SERIES_ROOT / "manifest.json"
OUT_JSON = ROOT / "provenance/audits/ufc_scorecard_structure_latest.json"
OUT_MD = ROOT / "provenance/audits/ufc_scorecard_structure_latest.md"
OUT_IMAGES = ROOT / "data/derived/discovery/ufc_scorecard_image_candidates.csv"

SCORE_PAIR_RE = re.compile(r"\b(?:10|9|8|7)\s*[-–]\s*(?:10|9|8|7)\b")
ROUND_RE = re.compile(r"\bround\s*[1-5]\b", re.I)
JUDGE_RE = re.compile(r"\bjudge(?:s)?\b", re.I)
CARD_HINT_RE = re.compile(r"score\s*card|scorecard|judge", re.I)
IMAGE_EXT_RE = re.compile(r"\.(?:png|jpe?g|webp)(?:\?|$)", re.I)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.images: list[dict[str, str]] = []
        self.in_title = False
        self.title_parts: list[str] = []

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
        if tag == "img":
            src = data.get("src") or data.get("data-src") or data.get("data-lazy-src")
            if src:
                self.images.append({"src": src, "alt": data.get("alt", ""), "title": data.get("title", "")})
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
        return "\n".join(
            clean for clean in (re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()) if clean
        )

    def title(self) -> str:
        return self.meta.get("og:title") or re.sub(r"\s+", " ", "".join(self.title_parts)).strip()


def load_records() -> list[dict[str, Any]]:
    final = json.loads(FINAL_MANIFEST.read_text(encoding="utf-8"))
    if final.get("complete_family_snapshot") is not True:
        raise RuntimeError("Official scorecard family is not complete")
    records: list[dict[str, Any]] = []
    expected = 0
    for raw in final.get("chunk_manifests") or []:
        chunk = json.loads((ROOT / raw).read_text(encoding="utf-8"))
        if int(chunk["chunk_start_index"]) != expected:
            raise RuntimeError(f"Chunk gap: expected {expected}, got {chunk['chunk_start_index']}")
        for row in chunk.get("records") or []:
            if int(row["candidate_index"]) != expected:
                raise RuntimeError(f"Record gap: expected {expected}, got {row['candidate_index']}")
            records.append(row)
            expected += 1
    expected_total = int(final.get("eligible_candidate_count") or final.get("candidate_count"))
    if expected != expected_total:
        raise RuntimeError(f"Final record count mismatch: {expected} vs {expected_total}")
    return records


def canonical_image_url(page_url: str, src: str) -> str:
    return urllib.parse.urljoin(page_url, html_lib.unescape(src))


def likely_scorecard_image(url: str, alt: str, title: str) -> bool:
    hay = " ".join((url, alt, title))
    # Prefer explicit semantic hints. Generic article hero images are intentionally excluded.
    return bool(CARD_HINT_RE.search(hay)) and bool(IMAGE_EXT_RE.search(url))


def main() -> int:
    records = load_records()
    counts = Counter()
    years = Counter()
    image_rows: list[dict[str, Any]] = []
    examples: dict[str, list[dict[str, Any]]] = {
        "no_candidate_image": [],
        "text_score_pairs": [],
        "many_candidate_images": [],
    }

    for record in records:
        path = ROOT / str(record["path"])
        body = path.read_text(encoding="utf-8", errors="replace")
        parser = PageParser(); parser.feed(body)
        text = parser.text()
        collapsed = re.sub(r"\s+", " ", text)
        title = parser.title()
        published = parser.meta.get("article:published_time")
        year = published[:4] if published and re.match(r"^\d{4}", published) else None
        if year:
            years[year] += 1

        score_pairs = SCORE_PAIR_RE.findall(collapsed)
        round_mentions = ROUND_RE.findall(collapsed)
        judge_mentions = JUDGE_RE.findall(collapsed)
        candidates: list[dict[str, str]] = []
        seen: set[str] = set()
        for img in parser.images:
            url = canonical_image_url(str(record["catalog_url"]), img["src"])
            if url in seen:
                continue
            seen.add(url)
            if likely_scorecard_image(url, img["alt"], img["title"]):
                candidate = {"url": url, "alt": img["alt"], "title": img["title"]}
                candidates.append(candidate)
                image_rows.append(
                    {
                        "article_candidate_index": int(record["candidate_index"]),
                        "article_url": record["catalog_url"],
                        "article_title": title,
                        "article_published_time": published or "",
                        "image_url": url,
                        "image_alt": img["alt"],
                        "image_title": img["title"],
                    }
                )

        counts["pages"] += 1
        counts["pages_with_candidate_image"] += bool(candidates)
        counts["pages_without_candidate_image"] += not candidates
        counts["candidate_images"] += len(candidates)
        counts["pages_with_text_score_pair"] += bool(score_pairs)
        counts["text_score_pairs"] += len(score_pairs)
        counts["pages_with_round_text"] += bool(round_mentions)
        counts["pages_with_judge_text"] += bool(judge_mentions)

        compact = {
            "candidate_index": int(record["candidate_index"]),
            "url": record["catalog_url"],
            "title": title,
            "published_time": published,
            "candidate_image_count": len(candidates),
            "text_score_pair_count": len(score_pairs),
            "round_mention_count": len(round_mentions),
            "judge_mention_count": len(judge_mentions),
        }
        if not candidates and len(examples["no_candidate_image"]) < 30:
            examples["no_candidate_image"].append(compact)
        if score_pairs and len(examples["text_score_pairs"]) < 20:
            examples["text_score_pairs"].append({**compact, "score_pair_samples": score_pairs[:10]})
        if len(candidates) >= 3 and len(examples["many_candidate_images"]) < 15:
            examples["many_candidate_images"].append({**compact, "image_samples": candidates[:6]})

    OUT_IMAGES.parent.mkdir(parents=True, exist_ok=True)
    image_fields = [
        "article_candidate_index", "article_url", "article_title", "article_published_time",
        "image_url", "image_alt", "image_title",
    ]
    with OUT_IMAGES.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=image_fields); writer.writeheader(); writer.writerows(image_rows)

    total = counts["pages"]
    output = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_manifest": str(FINAL_MANIFEST.relative_to(ROOT)),
        "counts": dict(counts),
        "published_year_counts": dict(sorted(years.items())),
        "image_candidate_csv": str(OUT_IMAGES.relative_to(ROOT)),
        "examples": examples,
        "decision": {
            "ocr_performed": False,
            "canonical_judge_rows_produced": False,
            "image_candidate_is_not_scorecard_truth": True,
            "next_gate": "If official judge-round values are not reliably present as HTML text, archive candidate official images before any OCR-derived layer.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# Official UFC scorecard article structure audit\n\n"
        f"- Complete official scorecard pages audited: **{total}**\n"
        f"- Pages with candidate scorecard image URLs: **{counts['pages_with_candidate_image']}** ({counts['pages_with_candidate_image']/total:.1%})\n"
        f"- Candidate scorecard image URLs: **{counts['candidate_images']}**\n"
        f"- Pages with score-like text pairs (e.g. 10-9): **{counts['pages_with_text_score_pair']}** ({counts['pages_with_text_score_pair']/total:.1%})\n"
        f"- Pages mentioning rounds in visible text: **{counts['pages_with_round_text']}**\n"
        f"- Pages mentioning judges in visible text: **{counts['pages_with_judge_text']}**\n\n"
        "No OCR or canonical judge-score extraction is performed by this audit.\n",
        encoding="utf-8",
    )
    print(json.dumps({"pages": total, "candidate_images": counts["candidate_images"], "text_score_pages": counts["pages_with_text_score_pair"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
