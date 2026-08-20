#!/usr/bin/env python3
"""Fetch UFC.com's JSON:API root once and inventory exposed resource types.

This is a small acquisition probe used to discover official additive surfaces such as
news/articles, weigh-ins, scorecards, media, rankings and fight-related entities.
It writes source-faithful raw bytes plus a compact parsed inventory for review.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

URL = "https://www.ufc.com/jsonapi"
OUT = Path("provenance/ufc_jsonapi_resource_probe.json")
RAW = Path("provenance/ufc_jsonapi_resource_probe.raw.json")
USER_AGENT = "ufc-edge-data/0.1 (private modeling research; one-request resource probe)"
KEYWORDS = (
    "article",
    "news",
    "weigh",
    "score",
    "fight",
    "event",
    "athlete",
    "rank",
    "result",
    "stat",
    "media",
    "video",
)


def main() -> int:
    req = urllib.request.Request(
        URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.api+json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read()
        status = response.status
        content_type = response.headers.get("content-type", "")

    if status != 200:
        raise RuntimeError(f"Unexpected UFC JSON:API status {status}")
    if "json" not in content_type.lower():
        raise RuntimeError(f"Unexpected content type {content_type!r}")

    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise RuntimeError("JSON:API root was not an object")

    RAW.write_bytes(body)

    links = payload.get("links") or {}
    resources: list[dict[str, Any]] = []
    if isinstance(links, dict):
        for rel, value in sorted(links.items()):
            href = value
            if isinstance(value, dict):
                href = value.get("href")
            if not isinstance(href, str):
                continue
            resources.append(
                {
                    "rel": str(rel),
                    "href": href,
                    "keyword_match": [
                        keyword
                        for keyword in KEYWORDS
                        if keyword in f"{rel} {href}".lower()
                    ],
                }
            )

    matched = [item for item in resources if item["keyword_match"]]
    acquired_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = {
        "schema_version": 1,
        "source_url": URL,
        "acquired_at_utc": acquired_at,
        "http_status": status,
        "content_type": content_type,
        "raw_sha256": hashlib.sha256(body).hexdigest(),
        "resource_count": len(resources),
        "keyword_matches": matched,
        "all_resources": resources,
        "notes": [
            "This is a discovery inventory, not a canonical data source.",
            "Resource existence does not imply every historical article/entity is complete or stable.",
            "Any new collection promoted to raw ingestion needs its own coverage and leakage rules."
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"UFC JSON:API resource probe: {len(resources)} resources, {len(matched)} keyword matches")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
