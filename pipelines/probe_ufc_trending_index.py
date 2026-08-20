#!/usr/bin/env python3
"""Bounded probe of UFC.com's public Trending index as a lawful article enumerator.

The blocked `/jsonapi/node/article` collection is not touched.  This probe fetches
only the public `/trending/all` page and records form controls, pagination links,
article hrefs/categories, and visible evidence needed to design a respectful
weigh-in/scorecard enumerator.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

URL = "https://www.ufc.com/trending/all"
OUT = Path("provenance/ufc_trending_index_probe.json")
RAW = Path("provenance/ufc_trending_index_probe.raw.html")
UA = "ufc-edge-data/0.2 (private modeling research; bounded public index probe)"


class ProbeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.inputs: list[dict[str, str]] = []
        self.selects: list[dict[str, str]] = []
        self.forms: list[dict[str, str]] = []
        self._link_href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k: (v or "") for k, v in attrs}
        if tag == "a" and d.get("href"):
            self._link_href = d["href"]
            self._link_text = []
        elif tag == "input":
            self.inputs.append({k: d.get(k, "") for k in ("name", "type", "value", "placeholder", "id")})
        elif tag == "select":
            self.selects.append({k: d.get(k, "") for k in ("name", "id")})
        elif tag == "form":
            self.forms.append({k: d.get(k, "") for k in ("action", "method", "id", "class")})

    def handle_data(self, data: str) -> None:
        if self._link_href is not None:
            self._link_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._link_href is not None:
            text = re.sub(r"\s+", " ", " ".join(self._link_text)).strip()
            self.links.append({"href": self._link_href, "text": text})
            self._link_href = None
            self._link_text = []


def main() -> int:
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read()
        status = response.status
        content_type = response.headers.get("content-type", "")
    text = body.decode("utf-8", errors="replace")
    parser = ProbeParser()
    parser.feed(text)

    article_links = []
    pagination_links = []
    relevant_links = []
    seen = set()
    for link in parser.links:
        absolute = urljoin(URL, link["href"])
        parsed = urlparse(absolute)
        if parsed.netloc not in {"www.ufc.com", "ufc.com"}:
            continue
        key = (absolute, link["text"])
        if key in seen:
            continue
        seen.add(key)
        row = {"url": absolute, "text": link["text"]}
        if parsed.path.startswith("/news/"):
            article_links.append(row)
            hay = (absolute + " " + link["text"]).lower()
            if any(token in hay for token in ("weigh", "scorecard", "score-card", "official-score")):
                relevant_links.append(row)
        if parsed.path == "/trending/all" and ("page" in parsed.query.lower() or "sort" in parsed.query.lower() or "filter" in parsed.query.lower()):
            pagination_links.append(row)

    story_count_match = re.search(r"([0-9][0-9,]+)\s+Stories", text, flags=re.I)
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "url": URL,
        "http_status": status,
        "content_type": content_type,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "visible_story_count": int(story_count_match.group(1).replace(",", "")) if story_count_match else None,
        "forms": parser.forms,
        "inputs": parser.inputs,
        "selects": parser.selects,
        "article_links_on_page_count": len(article_links),
        "article_links_on_page": article_links,
        "relevant_weigh_or_scorecard_links": relevant_links,
        "pagination_or_filter_links": pagination_links,
        "raw_html_path": RAW.as_posix(),
        "decision": {
            "article_jsonapi_403_bypassed": False,
            "purpose": "Discover whether UFC's own public content index can enumerate official weigh-in/scorecard pages without restricted article API access.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_bytes(body)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"trending probe status={status} bytes={len(body)} articles={len(article_links)} relevant={len(relevant_links)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
