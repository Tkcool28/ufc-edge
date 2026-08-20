#!/usr/bin/env python3
"""Snapshot one public UFC.com Drupal JSON:API resource at a time.

Resource-scoped snapshots replace the earlier all-or-nothing UFC.com acquisition.
A resource is canonical raw only after its manifest exists.  Partial directories left
by an interrupted process are staging evidence and must not be promoted/committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = "https://www.ufc.com/jsonapi"
OUT_ROOT = Path("data/raw/ufc_com_resources")
PAGE_LIMIT = 50
MIN_INTERVAL_SECONDS = 2.0
USER_AGENT = "ufc-edge-data/0.2 (private modeling research; respectful resource snapshotter)"
ACCEPT = "application/vnd.api+json"

COLLECTIONS: dict[str, dict[str, Any]] = {
    "athletes": {
        "path": "/node/athlete",
        "params": {
            "sort": "title",
            "page[limit]": str(PAGE_LIMIT),
            "include": "athlete_stat,athlete_ranking,stats_weight_class,fighting_style,gym,athlete_status",
        },
        "notes": "Point-in-time official athlete/profile snapshot. Mutable career/ranking/status fields are not historical-backfill safe.",
    },
    "events": {
        "path": "/node/event",
        "params": {"sort": "fight_card_time_main", "page[limit]": str(PAGE_LIMIT)},
        "notes": "Official event metadata and stable source identity surface.",
    },
    "fights": {
        "path": "/node/fight",
        "params": {
            "sort": "created",
            "page[limit]": str(PAGE_LIMIT),
            "include": "red_corner,blue_corner,fight_final_winner",
        },
        "notes": "Official fight/corner/winner identity surface; intended bridge to FightMetric and historical sources after audit.",
    },
}

_last_request_at = 0.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def snapshot_id() -> str:
    return os.environ.get("UFC_EDGE_SNAPSHOT_ID") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def safe_url(path: str, params: dict[str, str]) -> str:
    return BASE + path + "?" + urllib.parse.urlencode(params)


def validate_url(url: str, expected_path: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"www.ufc.com", "ufc.com"}:
        raise RuntimeError(f"Refusing unexpected pagination host: {url}")
    if not parsed.path.startswith("/jsonapi" + expected_path):
        raise RuntimeError(f"Refusing pagination outside {expected_path}: {url}")


def fetch(url: str, expected_path: str, attempts: int = 5) -> tuple[bytes, dict[str, str]]:
    global _last_request_at
    validate_url(url, expected_path)
    for attempt in range(1, attempts + 1):
        delay = MIN_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
        if delay > 0:
            time.sleep(delay)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": ACCEPT})
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                _last_request_at = time.monotonic()
                body = response.read()
                content_type = response.headers.get("content-type", "")
                if "json" not in content_type.lower():
                    raise RuntimeError(f"Expected JSON, got {content_type!r} from {url}")
                return body, {
                    "content_type": content_type,
                    "etag": response.headers.get("etag", ""),
                    "last_modified": response.headers.get("last-modified", ""),
                }
        except urllib.error.HTTPError as exc:
            _last_request_at = time.monotonic()
            if (exc.code == 429 or 500 <= exc.code <= 599) and attempt < attempts:
                time.sleep(min(60.0, 2.0**attempt))
                continue
            raise
        except urllib.error.URLError:
            _last_request_at = time.monotonic()
            if attempt < attempts:
                time.sleep(min(60.0, 2.0**attempt))
                continue
            raise
    raise RuntimeError(f"Failed to fetch {url}")


def next_url(payload: dict[str, Any]) -> str | None:
    links = payload.get("links")
    if not isinstance(links, dict):
        return None
    nxt = links.get("next")
    if isinstance(nxt, str):
        return nxt
    if isinstance(nxt, dict) and isinstance(nxt.get("href"), str):
        return nxt["href"]
    return None


def summarize_surface(data: list[Any], attrs: set[str], relationships: set[str], types: set[str]) -> None:
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("type"):
            types.add(str(item["type"]))
        item_attrs = item.get("attributes")
        if isinstance(item_attrs, dict):
            attrs.update(str(k) for k in item_attrs)
        rels = item.get("relationships")
        if isinstance(rels, dict):
            relationships.update(str(k) for k in rels)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", required=True, choices=sorted(COLLECTIONS))
    args = parser.parse_args()
    name = args.collection
    spec = COLLECTIONS[name]
    sid = snapshot_id()
    out_dir = OUT_ROOT / name / sid
    if out_dir.exists():
        raise RuntimeError(f"Snapshot path already exists: {out_dir}")
    out_dir.mkdir(parents=True)

    url: str | None = safe_url(spec["path"], spec["params"])
    page = 1
    rows = 0
    files: list[dict[str, Any]] = []
    attribute_names: set[str] = set()
    relationship_names: set[str] = set()
    resource_types: set[str] = set()
    seen: set[str] = set()
    started = utc_now()

    while url:
        validate_url(url, spec["path"])
        if url in seen:
            raise RuntimeError(f"Pagination loop for {name}: {url}")
        seen.add(url)
        body, headers = fetch(url, spec["path"])
        payload = json.loads(body)
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise RuntimeError(f"{name} page {page} missing list-valued data")
        path = out_dir / f"page_{page:04d}.json"
        path.write_bytes(body)
        rows += len(data)
        summarize_surface(data, attribute_names, relationship_names, resource_types)
        files.append({
            "path": path.as_posix(),
            "url": url,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "records": len(data),
            "content_type": headers["content_type"],
            "etag": headers["etag"] or None,
            "last_modified": headers["last_modified"] or None,
        })
        if page % 25 == 0:
            print(f"[ufc.com:{name}] page={page} rows={rows}", flush=True)
        url = next_url(payload)
        page += 1

    if rows == 0:
        raise RuntimeError(f"UFC.com {name} collection returned zero rows")

    manifest = {
        "schema_version": 1,
        "source": "Official UFC.com Drupal JSON:API",
        "collection": name,
        "snapshot_id": sid,
        "started_at_utc": started,
        "completed_at_utc": utc_now(),
        "endpoint": spec["path"],
        "request_params": spec["params"],
        "request_policy": {"page_limit": PAGE_LIMIT, "min_interval_seconds": MIN_INTERVAL_SECONDS},
        "rows": rows,
        "pages": page - 1,
        "resource_types": sorted(resource_types),
        "attribute_names": sorted(attribute_names),
        "relationship_names": sorted(relationship_names),
        "files": files,
        "semantics": {
            "raw_only": True,
            "complete_collection_snapshot": True,
            "point_in_time": True,
            "missing_is_not_zero": True,
            "historical_backfill_allowed": False,
            "notes": spec["notes"],
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[ufc.com:{name}] complete rows={rows} pages={page - 1} snapshot={sid}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
