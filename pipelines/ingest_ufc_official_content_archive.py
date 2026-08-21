#!/usr/bin/env python3
"""Snapshot official UFC weigh-in and scorecard content discovered from public indexes.

This is a source-acquisition step only. It does not parse scorecard images, infer fighter
identity, or canonicalize weigh-in values. Discovery uses UFC's own public sitemap/index
routes and preserves source HTML plus image links for later deterministic parsing/QA.
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
from typing import Iterable

BASE = "https://www.ufc.com"
ROOT = Path("data/raw/ufc_official_content")
UA = "ufc-edge-research/1.0 (+private research; low-rate archival fetch)"
MIN_INTERVAL_SEC = 1.0
TIMEOUT_SEC = 45

WEIGH_PATTERNS = (
    "weigh-results",
    "weigh-in-results",
    "weighin-results",
    "official-weigh",
    "weigh-in",
    "weighins",
)
SCORECARD_PATTERNS = ("scorecard", "scorecards")

_last_request = 0.0


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    base = (parsed.path.strip("/") or "root").replace("/", "__")
    q = ("__" + parsed.query.replace("&", "_").replace("=", "-")) if parsed.query else ""
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", base + q).strip("_")
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{text[:140]}__{digest}.html"


def fetch(url: str) -> tuple[int | None, str | None, bytes, str | None]:
    global _last_request
    wait = MIN_INTERVAL_SEC - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xml;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            body = resp.read()
            _last_request = time.monotonic()
            return resp.status, resp.headers.get("Content-Type"), body, None
    except urllib.error.HTTPError as exc:
        _last_request = time.monotonic()
        try:
            body = exc.read()
        except Exception:
            body = b""
        return exc.code, exc.headers.get("Content-Type") if exc.headers else None, body, f"HTTPError: {exc}"
    except Exception as exc:
        _last_request = time.monotonic()
        return None, None, b"", f"{type(exc).__name__}: {exc}"


def text_links(body: bytes) -> list[str]:
    text = body.decode("utf-8", errors="replace")
    raw = re.findall(r"https?://[^\s<>\"']+", html.unescape(text))
    out: list[str] = []
    seen: set[str] = set()
    for value in raw:
        value = value.rstrip(".,);]")
        if value.startswith(BASE) and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def candidate_kind(url: str) -> str | None:
    low = urllib.parse.urlparse(url).path.lower()
    if any(token in low for token in SCORECARD_PATTERNS):
        return "scorecard"
    if any(token in low for token in WEIGH_PATTERNS):
        return "weigh_in"
    return None


def extract_image_links(body: bytes) -> list[str]:
    text = html.unescape(body.decode("utf-8", errors="replace"))
    vals = re.findall(r"(?:src|data-src|data-lazy-src|content)=[\"']([^\"']+)[\"']", text, flags=re.I)
    out: list[str] = []
    seen: set[str] = set()
    for value in vals:
        if not re.search(r"\.(?:png|jpe?g|webp)(?:\?|$)", value, flags=re.I):
            continue
        absolute = urllib.parse.urljoin(BASE, value)
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / snapshot_id
    index_dir = out / "indexes"
    page_dir = out / "pages"
    index_dir.mkdir(parents=True, exist_ok=False)
    page_dir.mkdir(parents=True, exist_ok=True)

    acquisition_started = now_utc()
    route_rows: list[dict] = []
    discovered: dict[str, str] = {}

    # Root sitemap exposes the current page range. news-sitemap is kept as an additive
    # current-news index, while /scorecards gives an independent scorecard enumeration.
    seeds = [f"{BASE}/sitemap.xml", f"{BASE}/news-sitemap.xml", f"{BASE}/scorecards"]
    sitemap_pages: list[str] = []

    for url in seeds:
        status, ctype, body, error = fetch(url)
        path = index_dir / slugify(url)
        path.write_bytes(body)
        links = text_links(body)
        route_rows.append({
            "url": url, "status": status, "content_type": ctype, "bytes": len(body),
            "sha256": sha256(body), "error": error, "path": str(path), "link_count": len(links),
        })
        if url.endswith("/sitemap.xml") and status == 200:
            sitemap_pages.extend(sorted({u for u in links if u.startswith(f"{BASE}/sitemap.xml?page=")}))
        for link in links:
            kind = candidate_kind(link)
            if kind:
                discovered.setdefault(link, kind)

    # Exhaust the published sitemap page list only; do not guess page numbers.
    for url in sitemap_pages:
        status, ctype, body, error = fetch(url)
        path = index_dir / slugify(url)
        path.write_bytes(body)
        links = text_links(body)
        route_rows.append({
            "url": url, "status": status, "content_type": ctype, "bytes": len(body),
            "sha256": sha256(body), "error": error, "path": str(path), "link_count": len(links),
        })
        for link in links:
            kind = candidate_kind(link)
            if kind:
                discovered.setdefault(link, kind)

    # Independently walk /scorecards pager only as advertised by each page.
    seen_scorecard_index: set[str] = set()
    queue = [f"{BASE}/scorecards"]
    while queue:
        url = queue.pop(0)
        if url in seen_scorecard_index:
            continue
        seen_scorecard_index.add(url)
        if url != f"{BASE}/scorecards":
            status, ctype, body, error = fetch(url)
            path = index_dir / slugify(url)
            path.write_bytes(body)
            links = text_links(body)
            route_rows.append({
                "url": url, "status": status, "content_type": ctype, "bytes": len(body),
                "sha256": sha256(body), "error": error, "path": str(path), "link_count": len(links),
            })
        else:
            # Reuse first seed body from disk.
            seed_row = next(r for r in route_rows if r["url"] == url)
            body = Path(seed_row["path"]).read_bytes()
            links = text_links(body)
        for link in links:
            kind = candidate_kind(link)
            if kind:
                discovered.setdefault(link, kind)
            parsed = urllib.parse.urlparse(link)
            if parsed.path.rstrip("/") == "/scorecards" and "page=" in parsed.query and link not in seen_scorecard_index:
                queue.append(link)
        if len(seen_scorecard_index) > 200:
            raise RuntimeError("scorecards pager exceeded conservative 200-page safety cap")

    page_rows: list[dict] = []
    counts = {"scorecard": 0, "weigh_in": 0}
    success_counts = {"scorecard": 0, "weigh_in": 0}
    for url, kind in sorted(discovered.items(), key=lambda item: (item[1], item[0])):
        counts[kind] += 1
        status, ctype, body, error = fetch(url)
        dest = page_dir / kind / slugify(url)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        if status == 200:
            success_counts[kind] += 1
        page_rows.append({
            "url": url,
            "kind": kind,
            "status": status,
            "content_type": ctype,
            "bytes": len(body),
            "sha256": sha256(body),
            "error": error,
            "path": str(dest),
            "image_links": extract_image_links(body),
        })

    manifest = {
        "schema_version": 1,
        "snapshot_id": snapshot_id,
        "acquisition_started_at_utc": acquisition_started,
        "acquisition_completed_at_utc": now_utc(),
        "source": "official UFC public web indexes/pages",
        "base_url": BASE,
        "request_policy": {"min_interval_seconds": MIN_INTERVAL_SEC, "timeout_seconds": TIMEOUT_SEC, "user_agent": UA},
        "discovery": {
            "root_seeds": seeds,
            "published_sitemap_pages": len(sitemap_pages),
            "scorecard_index_pages_visited": len(seen_scorecard_index),
            "candidate_counts": counts,
            "successful_page_counts": success_counts,
        },
        "index_requests": route_rows,
        "pages": page_rows,
        "semantics": {
            "raw_only": True,
            "official_source": True,
            "scorecard_images_not_ocr_parsed": True,
            "weigh_in_text_not_canonicalized": True,
            "missing_candidate_page_is_not_zero": True,
            "blocked_routes_are_not_bypassed": True,
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "snapshot_id": snapshot_id,
        "sitemap_pages": len(sitemap_pages),
        "scorecard_index_pages": len(seen_scorecard_index),
        "candidate_counts": counts,
        "success_counts": success_counts,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
