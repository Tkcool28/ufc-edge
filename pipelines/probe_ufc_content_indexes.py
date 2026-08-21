#!/usr/bin/env python3
"""Bounded probe of public UFC content-index routes for data acquisition.

This does not crawl articles. It tests only known public index/sitemap/landing routes and
records response status, content type, pagination evidence, and candidate UFC links. A
403 remains a blocked route; the probe never retries with bypass headers or alternate
identities.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT = Path("provenance/audits/ufc_content_index_probe_latest.json")
URLS = [
    "https://www.ufc.com/news-sitemap.xml",
    "https://www.ufc.com/sitemap.xml",
    "https://www.ufc.com/scorecards",
    "https://www.ufc.com/scorecards?page=1",
    "https://www.ufc.com/trending/all",
    "https://www.ufc.com/trending/all?page=1",
]
HEADERS = {
    "User-Agent": "ufc-edge-data/0.5 (private modeling research; bounded public-index probe)",
    "Accept": "text/html,application/xml,text/xml;q=0.9,*/*;q=0.5",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def absolute_ufc(base: str, href: str) -> str | None:
    href = html.unescape(href.strip())
    if not href or href.startswith(("#", "javascript:", "mailto:")):
        return None
    url = urllib.parse.urljoin(base, href)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"ufc.com", "www.ufc.com"}:
        return None
    return urllib.parse.urlunparse(("https", "www.ufc.com", parsed.path, "", parsed.query, ""))


def classify(url: str, surrounding: str = "") -> set[str]:
    text = f"{url} {surrounding}".lower()
    classes: set[str] = set()
    if re.search(r"\bweigh(?:-?in|ing)?\b", text) or "official-weigh" in text or "weigh-results" in text:
        classes.add("weigh_in")
    if "scorecard" in text or "score-card" in text:
        classes.add("scorecard")
    return classes


def probe(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read(8_000_000)
            status = resp.status
            ctype = resp.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        body = exc.read(200_000)
        status = exc.code
        ctype = exc.headers.get("content-type", "") if exc.headers else ""
    except Exception as exc:
        return {
            "url": url,
            "ok": False,
            "status": None,
            "error": f"{type(exc).__name__}: {exc}",
        }

    text = body.decode("utf-8", errors="replace")
    candidates: dict[str, list[str]] = {"weigh_in": [], "scorecard": []}
    all_links: set[str] = set()

    # XML sitemap locations.
    for raw in re.findall(r"<loc>\s*(.*?)\s*</loc>", text, flags=re.I | re.S):
        candidate = absolute_ufc(url, re.sub(r"<.*?>", "", raw))
        if not candidate:
            continue
        all_links.add(candidate)
        for cls in classify(candidate):
            if len(candidates[cls]) < 100:
                candidates[cls].append(candidate)

    # HTML anchors with a small amount of surrounding anchor text.
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", text, flags=re.I | re.S):
        candidate = absolute_ufc(url, match.group(1))
        if not candidate:
            continue
        all_links.add(candidate)
        anchor_text = re.sub(r"<[^>]+>", " ", match.group(2))
        for cls in classify(candidate, anchor_text):
            if len(candidates[cls]) < 100:
                candidates[cls].append(candidate)

    pager_links = sorted(
        link for link in all_links
        if re.search(r"(?:\?|&)page=\d+", link)
    )[:100]

    return {
        "url": url,
        "ok": 200 <= status < 300,
        "status": status,
        "content_type": ctype,
        "bytes_read": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "ufc_link_count": len(all_links),
        "pager_links": pager_links,
        "candidate_links": {k: sorted(set(v)) for k, v in candidates.items()},
        "candidate_counts": {k: len(set(v)) for k, v in candidates.items()},
        "title_sample": (re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S).group(1).strip()
                         if re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S) else None),
        "body_prefix": text[:500] if status != 200 else None,
    }


def main() -> int:
    results = []
    for url in URLS:
        results.append(probe(url))
        time.sleep(2.0)

    successful = [r["url"] for r in results if r.get("ok")]
    scorecard_routes = [r["url"] for r in results if r.get("ok") and r.get("candidate_counts", {}).get("scorecard", 0)]
    weigh_routes = [r["url"] for r in results if r.get("ok") and r.get("candidate_counts", {}).get("weigh_in", 0)]
    payload = {
        "schema_version": 1,
        "generated_at_utc": now(),
        "routes": results,
        "summary": {
            "successful_routes": successful,
            "routes_exposing_scorecard_candidates": scorecard_routes,
            "routes_exposing_weigh_in_candidates": weigh_routes,
        },
        "rules": {
            "blocked_routes_are_not_bypassed": True,
            "probe_is_not_bulk_acquisition": True,
            "candidate_links_require_coverage_and_identity_validation": True,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
