#!/usr/bin/env python3
"""Acquire the official UFC.com fight collection in bounded immutable chunks.

The full /node/fight collection is large enough that repeated all-or-nothing runs have
hit the process timeout. This collector makes progress durable without pretending a
partial series is a complete raw snapshot.

Layout:
  data/raw/ufc_com_resources/fights/<series_id>/
    chunks/offset_000000/
      page_0001.json
      ...
      chunk_manifest.json
    manifest.json              # written ONLY after gap-free terminal finalization

A chunk is immutable once committed. The top-level manifest is the promotion marker
that says the series is complete.
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
PATH = "/node/fight"
PAGE_LIMIT = 50
MIN_INTERVAL_SECONDS = 2.0
USER_AGENT = "ufc-edge-data/0.3 (private modeling research; respectful bounded snapshotter)"
ACCEPT = "application/vnd.api+json"
OUT_ROOT = Path("data/raw/ufc_com_resources/fights")

_last_request_at = 0.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"www.ufc.com", "ufc.com"}:
        raise RuntimeError(f"Refusing unexpected pagination host: {url}")
    if not parsed.path.startswith("/jsonapi" + PATH):
        raise RuntimeError(f"Refusing pagination outside {PATH}: {url}")


def fetch(url: str, attempts: int = 5) -> tuple[bytes, dict[str, str]]:
    global _last_request_at
    validate_url(url)
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


def relationship_id(item: dict[str, Any], name: str) -> str | None:
    rels = item.get("relationships")
    if not isinstance(rels, dict):
        return None
    rel = rels.get(name)
    if not isinstance(rel, dict):
        return None
    data = rel.get("data")
    if isinstance(data, dict) and data.get("id") is not None:
        return str(data["id"])
    return None


def collect_chunk(series_id: str, start_offset: int, max_pages: int) -> Path:
    if start_offset < 0:
        raise RuntimeError("start_offset must be >= 0")
    if max_pages < 1 or max_pages > 100:
        raise RuntimeError("max_pages must be in [1, 100]")

    series_dir = OUT_ROOT / series_id
    chunk_dir = series_dir / "chunks" / f"offset_{start_offset:06d}"
    if chunk_dir.exists():
        raise RuntimeError(f"Chunk already exists and is immutable: {chunk_dir}")
    if (series_dir / "manifest.json").exists():
        raise RuntimeError(f"Series is already finalized: {series_dir}")
    chunk_dir.mkdir(parents=True, exist_ok=False)

    params = {
        "sort": "created",
        "page[limit]": str(PAGE_LIMIT),
        "page[offset]": str(start_offset),
    }
    url: str | None = BASE + PATH + "?" + urllib.parse.urlencode(params)
    started = utc_now()
    files: list[dict[str, Any]] = []
    rows = 0
    pages = 0
    attrs: set[str] = set()
    relationships: set[str] = set()
    resource_ids: set[str] = set()
    duplicate_resource_ids: set[str] = set()
    red_linked = 0
    blue_linked = 0
    winner_linked = 0
    terminal = False

    while url and pages < max_pages:
        body, headers = fetch(url)
        payload = json.loads(body)
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise RuntimeError(f"offset={start_offset} page={pages + 1} missing list-valued data")

        page_path = chunk_dir / f"page_{pages + 1:04d}.json"
        page_path.write_bytes(body)
        files.append({
            "path": page_path.as_posix(),
            "url": url,
            "records": len(data),
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "content_type": headers["content_type"],
            "etag": headers["etag"] or None,
            "last_modified": headers["last_modified"] or None,
        })

        for item in data:
            if not isinstance(item, dict):
                continue
            rid = item.get("id")
            if rid is not None:
                rid = str(rid)
                if rid in resource_ids:
                    duplicate_resource_ids.add(rid)
                resource_ids.add(rid)
            item_attrs = item.get("attributes")
            if isinstance(item_attrs, dict):
                attrs.update(str(k) for k in item_attrs)
            rels = item.get("relationships")
            if isinstance(rels, dict):
                relationships.update(str(k) for k in rels)
            if relationship_id(item, "red_corner"):
                red_linked += 1
            if relationship_id(item, "blue_corner"):
                blue_linked += 1
            if relationship_id(item, "fight_final_winner"):
                winner_linked += 1

        rows += len(data)
        pages += 1
        nxt = next_url(payload)
        if not nxt:
            terminal = True
            url = None
            break
        if len(data) == 0:
            terminal = True
            url = None
            break
        url = nxt

    if pages == 0:
        raise RuntimeError("No page was fetched")
    if duplicate_resource_ids:
        raise RuntimeError(
            f"Duplicate fight resource IDs inside chunk: {sorted(duplicate_resource_ids)[:10]}"
        )

    next_offset = None if terminal else start_offset + rows
    manifest = {
        "schema_version": 1,
        "source": "Official UFC.com Drupal JSON:API",
        "collection": "fights",
        "series_id": series_id,
        "chunk_start_offset": start_offset,
        "chunk_end_offset_exclusive": start_offset + rows,
        "started_at_utc": started,
        "completed_at_utc": utc_now(),
        "endpoint": PATH,
        "request_params": params,
        "request_policy": {
            "page_limit": PAGE_LIMIT,
            "max_pages_per_chunk": max_pages,
            "min_interval_seconds": MIN_INTERVAL_SECONDS,
        },
        "rows": rows,
        "pages": pages,
        "terminal": terminal,
        "next_offset": next_offset,
        "attribute_names": sorted(attrs),
        "relationship_names": sorted(relationships),
        "relationship_linkage_counts": {
            "red_corner_with_id": red_linked,
            "blue_corner_with_id": blue_linked,
            "fight_final_winner_with_id": winner_linked,
        },
        "distinct_resource_ids": len(resource_ids),
        "files": files,
        "semantics": {
            "raw_only": True,
            "complete_collection_snapshot": False,
            "chunk_immutable": True,
            "missing_relationship_is_coverage_evidence": True,
            "promotion_marker": "Top-level manifest.json is written only after gap-free terminal finalization.",
        },
    }
    manifest_path = chunk_dir / "chunk_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "series_id": series_id,
        "start_offset": start_offset,
        "rows": rows,
        "pages": pages,
        "terminal": terminal,
        "next_offset": next_offset,
        "manifest": manifest_path.as_posix(),
    }, sort_keys=True))
    return manifest_path


def finalize_series(series_id: str) -> Path:
    series_dir = OUT_ROOT / series_id
    final_path = series_dir / "manifest.json"
    if final_path.exists():
        print(f"Already finalized: {final_path}")
        return final_path
    chunk_root = series_dir / "chunks"
    manifests = sorted(chunk_root.glob("offset_*/chunk_manifest.json"))
    if not manifests:
        raise RuntimeError(f"No chunks found for series {series_id}")

    chunks = [json.loads(p.read_text(encoding="utf-8")) for p in manifests]
    chunks.sort(key=lambda x: int(x["chunk_start_offset"]))
    expected = 0
    all_ids: set[str] = set()
    attrs: set[str] = set()
    relationships: set[str] = set()
    total_rows = 0
    total_pages = 0
    red = blue = winner = 0
    files: list[dict[str, Any]] = []

    for i, chunk in enumerate(chunks):
        start = int(chunk["chunk_start_offset"])
        rows = int(chunk["rows"])
        if start != expected:
            raise RuntimeError(f"Gap/overlap in series: expected offset {expected}, found {start}")
        if rows <= 0 and not chunk.get("terminal"):
            raise RuntimeError(f"Non-terminal zero-row chunk at {start}")
        expected = start + rows
        total_rows += rows
        total_pages += int(chunk["pages"])
        attrs.update(chunk.get("attribute_names") or [])
        relationships.update(chunk.get("relationship_names") or [])
        linkage = chunk.get("relationship_linkage_counts") or {}
        red += int(linkage.get("red_corner_with_id") or 0)
        blue += int(linkage.get("blue_corner_with_id") or 0)
        winner += int(linkage.get("fight_final_winner_with_id") or 0)
        files.extend(chunk.get("files") or [])
        if chunk.get("terminal") and i != len(chunks) - 1:
            raise RuntimeError(f"Terminal chunk at offset {start} is not last")

    if not chunks[-1].get("terminal"):
        raise RuntimeError(
            f"Series incomplete: last chunk at {chunks[-1]['chunk_start_offset']} is not terminal; "
            f"next_offset={chunks[-1].get('next_offset')}"
        )

    # Cross-chunk resource-ID uniqueness is checked from the raw page payloads.
    for f in files:
        path = Path(f["path"])
        payload = json.loads(path.read_text(encoding="utf-8"))
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise RuntimeError(f"Malformed page during finalization: {path}")
        for item in data:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            rid = str(item["id"])
            if rid in all_ids:
                raise RuntimeError(f"Duplicate fight resource ID across chunks: {rid}")
            all_ids.add(rid)

    if len(all_ids) != total_rows:
        raise RuntimeError(
            f"Fight resource ID count mismatch: rows={total_rows} distinct_ids={len(all_ids)}"
        )

    final = {
        "schema_version": 1,
        "source": "Official UFC.com Drupal JSON:API",
        "collection": "fights",
        "series_id": series_id,
        "endpoint": PATH,
        "sort": "created",
        "complete_collection_snapshot": True,
        "rows": total_rows,
        "pages": total_pages,
        "chunks": len(chunks),
        "distinct_resource_ids": len(all_ids),
        "attribute_names": sorted(attrs),
        "relationship_names": sorted(relationships),
        "relationship_linkage_counts": {
            "red_corner_with_id": red,
            "blue_corner_with_id": blue,
            "fight_final_winner_with_id": winner,
        },
        "chunk_manifests": [p.as_posix() for p in manifests],
        "acquisition_started_at_utc": chunks[0]["started_at_utc"],
        "acquisition_completed_at_utc": chunks[-1]["completed_at_utc"],
        "semantics": {
            "raw_only": True,
            "missing_is_not_zero": True,
            "historical_backfill_allowed": False,
            "identity_bridge_candidate": True,
            "notes": "Gap-free terminal snapshot assembled from immutable bounded chunks. Relationship IDs are source identity evidence pending canonical reconciliation.",
        },
    }
    final_path.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"finalized": True, "manifest": final_path.as_posix(), "rows": total_rows, "pages": total_pages}, sort_keys=True))
    return final_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-id", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    p_chunk = sub.add_parser("chunk")
    p_chunk.add_argument("--start-offset", required=True, type=int)
    p_chunk.add_argument("--max-pages", type=int, default=50)
    sub.add_parser("finalize")
    args = parser.parse_args()

    if args.command == "chunk":
        collect_chunk(args.series_id, args.start_offset, args.max_pages)
    else:
        finalize_series(args.series_id)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
