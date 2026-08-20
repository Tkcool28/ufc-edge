#!/usr/bin/env python3
"""Snapshot official UFC.com weigh-in and scorecard article families via JSON:API.

Raw-only acquisition. The article body is preserved exactly as returned by UFC.com;
weight/score parsing and fight identity are separate canonicalization work.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = "https://www.ufc.com/jsonapi/node/article"
OUT_ROOT = Path("data/raw/ufc_official_articles")
PAGE_LIMIT = 50
MIN_INTERVAL_SECONDS = 2.0
USER_AGENT = "ufc-edge-data/0.1 (private modeling research; respectful official-article snapshotter)"

FAMILIES = {
    "official_weigh_ins": "Official Weigh-In",
    "official_scorecards": "Official Scorecard",
}

_last_request = 0.0


def snapshot_id() -> str:
    return os.environ.get("UFC_EDGE_SNAPSHOT_ID") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"www.ufc.com", "ufc.com"}:
        raise RuntimeError(f"Refusing unexpected URL: {url}")
    if not parsed.path.startswith("/jsonapi/node/article"):
        raise RuntimeError(f"Refusing pagination outside article resource: {url}")


def fetch(url: str) -> tuple[bytes, dict[str, str]]:
    global _last_request
    validate_url(url)
    delay = MIN_INTERVAL_SECONDS - (time.monotonic() - _last_request)
    if delay > 0:
        time.sleep(delay)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.api+json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        _last_request = time.monotonic()
        body = response.read()
        return body, {
            "content_type": response.headers.get("content-type", ""),
            "etag": response.headers.get("etag", ""),
            "last_modified": response.headers.get("last-modified", ""),
        }


def first_url(term: str) -> str:
    params = {
        "filter[title][value]": term,
        "filter[title][operator]": "CONTAINS",
        "sort": "-created",
        "page[limit]": str(PAGE_LIMIT),
    }
    return BASE + "?" + urllib.parse.urlencode(params)


def next_href(payload: dict[str, Any]) -> str | None:
    links = payload.get("links")
    if not isinstance(links, dict):
        return None
    value = links.get("next")
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("href"), str):
        return value["href"]
    return None


def main() -> int:
    sid = snapshot_id()
    out_dir = OUT_ROOT / sid
    if out_dir.exists():
        raise RuntimeError(f"Snapshot already exists: {out_dir}")
    out_dir.mkdir(parents=True)

    manifest_files: list[dict[str, Any]] = []
    family_summaries: list[dict[str, Any]] = []

    for family, term in FAMILIES.items():
        url: str | None = first_url(term)
        seen: set[str] = set()
        page = 1
        records = 0
        titles: list[dict[str, Any]] = []
        while url:
            validate_url(url)
            if url in seen:
                raise RuntimeError(f"Pagination loop for {family}: {url}")
            seen.add(url)
            body, headers = fetch(url)
            payload = json.loads(body)
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise RuntimeError(f"{family} page {page} lacks data list")

            path = out_dir / family / f"page_{page:04d}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            manifest_files.append(
                {
                    "family": family,
                    "path": path.as_posix(),
                    "url": url,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "records": len(data),
                    "content_type": headers["content_type"],
                    "etag": headers["etag"] or None,
                    "last_modified": headers["last_modified"] or None,
                }
            )
            records += len(data)
            for item in data:
                if not isinstance(item, dict):
                    continue
                attrs = item.get("attributes")
                if not isinstance(attrs, dict):
                    continue
                titles.append(
                    {
                        "id": item.get("id"),
                        "title": attrs.get("title"),
                        "created": attrs.get("created"),
                        "changed": attrs.get("changed"),
                        "path": (attrs.get("path") or {}).get("alias") if isinstance(attrs.get("path"), dict) else None,
                    }
                )
            url = next_href(payload)
            page += 1

        family_summaries.append(
            {
                "family": family,
                "title_filter_contains": term,
                "pages": page - 1,
                "records": records,
                "articles": titles,
            }
        )
        print(f"[ufc articles] {family}: {records} records", flush=True)

    manifest = {
        "schema_version": 1,
        "source": "Official UFC.com Drupal JSON:API node/article",
        "snapshot_id": sid,
        "acquired_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "families": family_summaries,
        "files": manifest_files,
        "semantics": {
            "raw_only": True,
            "article_body_is_source_text": True,
            "historical_event_join_not_yet_approved": True,
            "notes": [
                "Official weigh-in articles are candidates for fight-specific scale weight, miss/catchweight and purse-penalty context.",
                "Official scorecard articles are candidates for decision/judging labels, but scorecards may be embedded as images and require a separate verified parser.",
                "Title-filter coverage must be audited against UFC events before this feed is considered complete."
            ],
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[ufc articles] complete: snapshot={sid}; files={len(manifest_files)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
