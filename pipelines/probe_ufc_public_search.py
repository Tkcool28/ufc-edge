#!/usr/bin/env python3
"""Bounded probe of UFC.com's own public `/search` route.

This intentionally avoids the blocked article JSON:API collection. It tests whether
UFC's normal site search can provide a stable, paginated enumeration surface for
Official Weigh-In and Official Scorecard pages.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE = "https://www.ufc.com/search"
OUT = Path("provenance/ufc_public_search_probe.json")
UA = "ufc-edge-data/0.2 (private modeling research; bounded public search probe)"
QUERIES = ["Official Weigh-In Results", "Official Scorecards"]


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        d = {k: (v or "") for k, v in attrs}
        if d.get("href"):
            self._href = d["href"]
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append({"href": self._href, "text": re.sub(r"\s+", " ", " ".join(self._text)).strip()})
            self._href = None
            self._text = []


def fetch(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read(), response.headers.get("content-type", "")


def classify(link: dict[str, str]) -> str | None:
    hay = (link["text"] + " " + link["url"]).lower()
    if re.search(r"\bweigh[- ]?in\b|\bweigh[- ]?results\b", hay):
        return "weigh_in"
    if re.search(r"\bscorecards?\b|official[- ]judges?[- ]scorecards?", hay):
        return "scorecard"
    return None


def main() -> int:
    reports = []
    for qi, query in enumerate(QUERIES):
        for page in (0, 1):
            params = {"query": query}
            if page:
                params["page"] = str(page)
            url = BASE + "?" + urllib.parse.urlencode(params)
            body, content_type = fetch(url)
            text = body.decode("utf-8", errors="replace")
            parser = Parser()
            parser.feed(text)
            article_links = []
            pagination = []
            for raw in parser.links:
                absolute = urljoin(url, raw["href"])
                parsed = urlparse(absolute)
                if parsed.netloc not in {"www.ufc.com", "ufc.com"}:
                    continue
                item = {"url": absolute, "text": raw["text"]}
                if parsed.path.startswith("/news/"):
                    kind = classify(item)
                    item["classification"] = kind
                    article_links.append(item)
                if parsed.path == "/search" and "page=" in parsed.query:
                    pagination.append(item)
            count_match = re.search(r"([0-9][0-9,]*)\s+(?:results?|stories)", text, flags=re.I)
            reports.append({
                "query": query,
                "page": page,
                "url": url,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "content_type": content_type,
                "visible_result_count": int(count_match.group(1).replace(",", "")) if count_match else None,
                "article_links_count": len(article_links),
                "classified_weigh_in_count": sum(1 for x in article_links if x["classification"] == "weigh_in"),
                "classified_scorecard_count": sum(1 for x in article_links if x["classification"] == "scorecard"),
                "article_links": article_links,
                "pagination_links": pagination,
            })
            if qi or page:
                time.sleep(2)
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "route": BASE,
        "probes": reports,
        "decision": {
            "article_jsonapi_used": False,
            "promotion_gate": "Use as article enumeration source only if query pagination is stable and returned links are official UFC article pages with acceptable precision/recall.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote UFC public-search probe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
