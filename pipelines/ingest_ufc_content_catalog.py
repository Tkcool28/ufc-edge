#!/usr/bin/env python3
"""Acquire UFC's public paginated sitemap as an immutable content catalog.

The sitemap is used only for enumeration. Raw XML pages are preserved, and a derived
candidate catalog identifies URLs whose slugs explicitly indicate official weigh-in or
scorecard content. Classification is conservative: an unrecognized URL remains cataloged
but is not guessed into a data family.
"""
from __future__ import annotations

import csv
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

BASE = "https://www.ufc.com"
ROOT_SITEMAP = BASE + "/sitemap.xml"
RAW_ROOT = Path("data/raw/ufc_content_catalog")
DERIVED = Path("data/derived/discovery/ufc_content_candidates.csv")
MIN_INTERVAL = 2.0
MAX_PAGES = 100
HEADERS = {
    "User-Agent": "ufc-edge-data/0.5 (private modeling research; respectful official sitemap snapshot)",
    "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.5",
}
_last = 0.0


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(url: str, attempts: int = 4) -> tuple[bytes, dict[str, str]]:
    global _last
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"www.ufc.com", "ufc.com"} or parsed.path != "/sitemap.xml":
        raise RuntimeError(f"Refusing non-sitemap URL: {url}")
    for attempt in range(1, attempts + 1):
        delay = MIN_INTERVAL - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                _last = time.monotonic()
                body = resp.read()
                if resp.status != 200:
                    raise RuntimeError(f"Unexpected HTTP {resp.status}: {url}")
                return body, {
                    "content_type": resp.headers.get("content-type", ""),
                    "etag": resp.headers.get("etag", ""),
                    "last_modified": resp.headers.get("last-modified", ""),
                }
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            _last = time.monotonic()
            if attempt < attempts:
                time.sleep(min(30, 2**attempt)); continue
            raise RuntimeError(f"Failed {url}: {exc}") from exc
    raise RuntimeError(f"Failed {url}")


def locs(text: str) -> list[str]:
    return [html.unescape(re.sub(r"<.*?>", "", raw).strip()) for raw in re.findall(r"<loc>\s*(.*?)\s*</loc>", text, flags=re.I | re.S)]


def page_number(url: str) -> int | None:
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    raw = query.get("page", [None])[0]
    try:
        return None if raw is None else int(raw)
    except ValueError:
        return None


def classify(url: str) -> str | None:
    slug = urllib.parse.urlparse(url).path.lower().strip("/")
    if "scorecard" in slug or "score-card" in slug:
        return "scorecard"
    weigh_patterns = (
        "official-weigh-in-results",
        "official-weigh-results",
        "official-weighin-results",
        "weigh-in-results",
        "weigh-results",
        "weighin-results",
    )
    if any(token in slug for token in weigh_patterns):
        return "weigh_in"
    return None


def extract_urls(text: str) -> list[dict[str, str | None]]:
    # Sitemap pages may include lastmod. Keep a forgiving per-url block parser.
    records: list[dict[str, str | None]] = []
    blocks = re.findall(r"<url\b[^>]*>(.*?)</url>", text, flags=re.I | re.S)
    if blocks:
        for block in blocks:
            found = locs(block)
            if not found:
                continue
            m = re.search(r"<lastmod>\s*(.*?)\s*</lastmod>", block, flags=re.I | re.S)
            records.append({"url": found[0], "lastmod": html.unescape(m.group(1).strip()) if m else None})
        return records
    return [{"url": url, "lastmod": None} for url in locs(text)]


def main() -> int:
    snapshot = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RAW_ROOT / snapshot
    out.mkdir(parents=True, exist_ok=False)

    root_body, root_headers = fetch(ROOT_SITEMAP)
    root_text = root_body.decode("utf-8", errors="replace")
    root_path = out / "sitemap_root.xml"
    root_path.write_bytes(root_body)

    page_urls = []
    for url in locs(root_text):
        n = page_number(url)
        if n is not None and 0 <= n <= MAX_PAGES:
            page_urls.append((n, url))
    page_urls = sorted(set(page_urls))
    if len(page_urls) < 50:
        raise RuntimeError(f"Suspiciously few paginated sitemap pages discovered: {len(page_urls)}")
    if len(page_urls) > MAX_PAGES:
        raise RuntimeError(f"Sitemap page count exceeds safety bound: {len(page_urls)}")

    files: list[dict[str, Any]] = [{
        "path": root_path.as_posix(),
        "url": ROOT_SITEMAP,
        "bytes": len(root_body),
        "sha256": hashlib.sha256(root_body).hexdigest(),
        **{k: (v or None) for k, v in root_headers.items()},
    }]
    catalog: dict[str, dict[str, str | None]] = {}

    for n, url in page_urls:
        body, headers = fetch(url)
        text = body.decode("utf-8", errors="replace")
        path = out / f"sitemap_page_{n:03d}.xml"
        path.write_bytes(body)
        records = extract_urls(text)
        files.append({
            "path": path.as_posix(),
            "url": url,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "url_records": len(records),
            **{k: (v or None) for k, v in headers.items()},
        })
        for record in records:
            u = str(record["url"])
            prior = catalog.get(u)
            if prior and prior.get("lastmod") != record.get("lastmod"):
                # Duplicate URL is okay only if metadata is not contradictory.
                raise RuntimeError(f"Conflicting sitemap lastmod for {u}: {prior} vs {record}")
            catalog[u] = record

    candidates = []
    counts = {"weigh_in": 0, "scorecard": 0}
    for url, record in sorted(catalog.items()):
        family = classify(url)
        if family is None:
            continue
        counts[family] += 1
        candidates.append({"family": family, "url": url, "lastmod": record.get("lastmod") or ""})

    if counts["scorecard"] < 20:
        raise RuntimeError(f"Suspiciously low scorecard candidate count: {counts['scorecard']}")
    if counts["weigh_in"] < 20:
        raise RuntimeError(f"Suspiciously low weigh-in candidate count: {counts['weigh_in']}")

    DERIVED.parent.mkdir(parents=True, exist_ok=True)
    with DERIVED.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["family", "url", "lastmod"])
        writer.writeheader(); writer.writerows(candidates)

    manifest = {
        "schema_version": 1,
        "source": "Official UFC.com public sitemap",
        "snapshot_id": snapshot,
        "acquired_at_utc": now(),
        "root_url": ROOT_SITEMAP,
        "sitemap_pages": len(page_urls),
        "distinct_catalog_urls": len(catalog),
        "candidate_counts": counts,
        "candidate_catalog": DERIVED.as_posix(),
        "files": files,
        "rules": {
            "raw_xml_immutable": True,
            "slug_classification_conservative": True,
            "unclassified_urls_retained_in_raw_xml": True,
            "candidate_does_not_mean_canonical": True,
        },
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"snapshot": snapshot, "urls": len(catalog), **counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
