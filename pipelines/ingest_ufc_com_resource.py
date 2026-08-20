#!/usr/bin/env python3
"""Snapshot one public UFC.com Drupal JSON:API resource at a time.

Resource-scoped snapshots replace the earlier all-or-nothing UFC.com acquisition.
A resource is canonical raw only after its manifest exists. Partial directories left
by an interrupted process are staging evidence and must not be promoted/committed.
"""
from __future__ import annotations

import argparse
import collections
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
USER_AGENT = "ufc-edge-data/0.3 (private modeling research; respectful resource snapshotter)"
ACCEPT = "application/vnd.api+json"

COLLECTIONS: dict[str, dict[str, Any]] = {
    "athletes": {
        "path": "/node/athlete",
        "params": {
            "sort": "title",
            "page[limit]": str(PAGE_LIMIT),
            "include": "athlete_stat,athlete_ranking,stats_weight_class,fighting_style,gym,athlete_status",
        },
        "required_relationship_linkage": [],
        "notes": "Point-in-time official athlete/profile snapshot. Mutable career/ranking/status fields are not historical-backfill safe.",
    },
    "events": {
        "path": "/node/event",
        "params": {"sort": "fight_card_time_main", "page[limit]": str(PAGE_LIMIT)},
        "required_relationship_linkage": [],
        "notes": "Official event metadata and stable source identity surface.",
    },
    "fights": {
        "path": "/node/fight",
        "params": {
            "sort": "created",
            "page[limit]": str(PAGE_LIMIT),
        },
        "required_relationship_linkage": ["red_corner", "blue_corner"],
        "notes": (
            "Official fight identity surface. Full related athlete objects are intentionally not included on every page; "
            "the manifest audits base JSON:API relationship linkage and fails closed if red/blue linkage is absent."
        ),
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


def linkage_id(value: Any) -> str | None:
    if isinstance(value, dict) and value.get("id") not in (None, ""):
        return str(value["id"])
    return None


def summarize_surface(
    data: list[Any],
    attrs: set[str],
    relationships: set[str],
    types: set[str],
    linkage_counts: collections.Counter[str],
    linkage_type_counts: dict[str, collections.Counter[str]],
) -> None:
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("type"):
            types.add(str(item["type"]))
        item_attrs = item.get("attributes")
        if isinstance(item_attrs, dict):
            attrs.update(str(k) for k in item_attrs)
        rels = item.get("relationships")
        if not isinstance(rels, dict):
            continue
        relationships.update(str(k) for k in rels)
        for name, rel in rels.items():
            if not isinstance(rel, dict):
                continue
            rel_data = rel.get("data")
            if isinstance(rel_data, dict):
                if linkage_id(rel_data):
                    linkage_counts[str(name)] += 1
                if rel_data.get("type"):
                    linkage_type_counts[str(name)][str(rel_data["type"])] += 1
            elif isinstance(rel_data, list):
                ids = [linkage_id(v) for v in rel_data]
                if any(v is not None for v in ids):
                    linkage_counts[str(name)] += 1
                for v in rel_data:
                    if isinstance(v, dict) and v.get("type"):
                        linkage_type_counts[str(name)][str(v["type"])] += 1


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
    linkage_counts: collections.Counter[str] = collections.Counter()
    linkage_type_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
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
        summarize_surface(
            data,
            attribute_names,
            relationship_names,
            resource_types,
            linkage_counts,
            linkage_type_counts,
        )
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

    required_linkage = spec.get("required_relationship_linkage", [])
    missing_required = [rel for rel in required_linkage if linkage_counts.get(rel, 0) == 0]
    if missing_required:
        raise RuntimeError(
            f"{name} base resource lacks required relationship linkage: {missing_required}; "
            "refusing lean snapshot promotion"
        )

    manifest = {
        "schema_version": 2,
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
        "relationship_linkage_rows": {k: int(v) for k, v in sorted(linkage_counts.items())},
        "relationship_linkage_types": {
            k: dict(sorted(v.items())) for k, v in sorted(linkage_type_counts.items())
        },
        "required_relationship_linkage": required_linkage,
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
    if required_linkage:
        print(
            "[ufc.com:%s] required linkage rows: %s" %
            (name, ", ".join(f"{r}={linkage_counts.get(r, 0)}" for r in required_linkage)),
            flush=True,
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
