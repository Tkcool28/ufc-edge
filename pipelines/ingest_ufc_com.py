#!/usr/bin/env python3
"""Snapshot additive public data from UFC.com's Drupal JSON:API.

Raw-only ingestion.  No canonicalization or historical feature backfill occurs here.
Every run writes a new immutable point-in-time snapshot.
"""

from __future__ import annotations

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
OUT_ROOT = Path("data/raw/ufc_com")
PAGE_LIMIT = 50
MIN_INTERVAL_SECONDS = 2.0
USER_AGENT = "ufc-edge-data/0.1 (private modeling research; respectful snapshotter)"
ACCEPT = "application/vnd.api+json"

COLLECTIONS = {
    "athletes": {
        "path": "/node/athlete",
        "params": {
            "sort": "title",
            "page[limit]": str(PAGE_LIMIT),
            "include": ",".join(
                [
                    "athlete_stat",
                    "athlete_ranking",
                    "stats_weight_class",
                    "fighting_style",
                    "gym",
                    "athlete_status",
                ]
            ),
        },
        "historical_feature_safe": False,
        "notes": (
            "Point-in-time athlete snapshot. Static/near-static physical fields may later "
            "be eligible with provenance; career totals/rates, rankings, status and streaks "
            "must never be backfilled into historical target fights."
        ),
    },
    "events": {
        "path": "/node/event",
        "params": {
            "sort": "fight_card_time_main",
            "page[limit]": str(PAGE_LIMIT),
        },
        "historical_feature_safe": False,
        "notes": "Raw official event metadata; preserve source timestamps and do not infer historical availability from current CMS state.",
    },
    "fights": {
        "path": "/node/fight",
        "params": {
            "sort": "created",
            "page[limit]": str(PAGE_LIMIT),
            "include": "red_corner,blue_corner,fight_final_winner",
        },
        "historical_feature_safe": False,
        "notes": "Official bout/corner/winner snapshot used for identity and QA; Greco remains the historical stats backbone.",
    },
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def snapshot_id() -> str:
    override = os.environ.get("UFC_EDGE_SNAPSHOT_ID")
    if override:
        return override
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def safe_url(path: str, params: dict[str, str] | None = None) -> str:
    url = BASE.rstrip("/") + "/" + path.lstrip("/")
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return url


def validate_next_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError(f"Refusing non-HTTPS pagination URL: {url}")
    if parsed.netloc not in {"www.ufc.com", "ufc.com"}:
        raise RuntimeError(f"Refusing pagination host outside ufc.com: {url}")
    if not parsed.path.startswith("/jsonapi"):
        raise RuntimeError(f"Refusing pagination path outside /jsonapi: {url}")


_last_request_at = 0.0


def fetch_bytes(url: str, *, attempts: int = 5) -> tuple[bytes, dict[str, str]]:
    global _last_request_at
    validate_next_url(url)

    for attempt in range(1, attempts + 1):
        delay = MIN_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
        if delay > 0:
            time.sleep(delay)

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": ACCEPT,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                _last_request_at = time.monotonic()
                body = response.read()
                content_type = response.headers.get("content-type", "")
                if "json" not in content_type.lower():
                    raise RuntimeError(
                        f"Expected JSON from {url}, got content-type={content_type!r}"
                    )
                headers = {
                    "content-type": content_type,
                    "etag": response.headers.get("etag", ""),
                    "last-modified": response.headers.get("last-modified", ""),
                }
                return body, headers
        except urllib.error.HTTPError as exc:
            _last_request_at = time.monotonic()
            if exc.code == 429 or 500 <= exc.code <= 599:
                if attempt < attempts:
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


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_payload(body: bytes, url: str) -> dict[str, Any]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object from {url}")
    return payload


def write_raw(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite immutable raw file: {path}")
    path.write_bytes(body)


def snapshot_single(url: str, path: Path, manifest_files: list[dict[str, Any]]) -> None:
    body, headers = fetch_bytes(url)
    payload = parse_payload(body, url)
    write_raw(path, body)
    manifest_files.append(
        {
            "path": path.as_posix(),
            "url": url,
            "bytes": len(body),
            "sha256": sha256_hex(body),
            "record_count": len(payload.get("data", []))
            if isinstance(payload.get("data"), list)
            else None,
            "content_type": headers["content-type"],
            "etag": headers["etag"] or None,
            "last_modified": headers["last-modified"] or None,
        }
    )


def snapshot_collection(
    name: str,
    spec: dict[str, Any],
    snapshot_dir: Path,
    manifest_files: list[dict[str, Any]],
) -> dict[str, Any]:
    next_url = safe_url(spec["path"], spec["params"])
    page_number = 1
    rows = 0
    seen_urls: set[str] = set()

    while next_url:
        validate_next_url(next_url)
        if next_url in seen_urls:
            raise RuntimeError(f"Pagination loop detected for {name}: {next_url}")
        seen_urls.add(next_url)

        body, headers = fetch_bytes(next_url)
        payload = parse_payload(body, next_url)
        data = payload.get("data")
        if not isinstance(data, list):
            raise RuntimeError(f"{name} page {page_number} missing list-valued data")

        path = snapshot_dir / name / f"page_{page_number:04d}.json"
        write_raw(path, body)
        rows += len(data)

        manifest_files.append(
            {
                "path": path.as_posix(),
                "url": next_url,
                "bytes": len(body),
                "sha256": sha256_hex(body),
                "record_count": len(data),
                "content_type": headers["content-type"],
                "etag": headers["etag"] or None,
                "last_modified": headers["last-modified"] or None,
            }
        )

        links = payload.get("links") or {}
        candidate = None
        if isinstance(links, dict):
            next_link = links.get("next")
            if isinstance(next_link, str):
                candidate = next_link
            elif isinstance(next_link, dict):
                candidate = next_link.get("href")
        next_url = candidate if candidate else ""
        page_number += 1

    return {
        "collection": name,
        "pages": page_number - 1,
        "records": rows,
        "historical_feature_safe": spec["historical_feature_safe"],
        "notes": spec["notes"],
    }


def main() -> int:
    acquired_at = utc_now().isoformat().replace("+00:00", "Z")
    sid = snapshot_id()
    snapshot_dir = OUT_ROOT / sid

    if snapshot_dir.exists():
        raise RuntimeError(f"Snapshot directory already exists: {snapshot_dir}")
    snapshot_dir.mkdir(parents=True)

    manifest_files: list[dict[str, Any]] = []
    collection_summaries: list[dict[str, Any]] = []

    snapshot_single(
        BASE,
        snapshot_dir / "jsonapi_index.json",
        manifest_files,
    )

    for name, spec in COLLECTIONS.items():
        print(f"[ufc.com] snapshotting {name}...", flush=True)
        summary = snapshot_collection(name, spec, snapshot_dir, manifest_files)
        collection_summaries.append(summary)
        print(
            f"[ufc.com] {name}: {summary['records']} records "
            f"across {summary['pages']} pages",
            flush=True,
        )

    manifest = {
        "schema_version": 1,
        "source": "ufc.com Drupal JSON:API",
        "base_url": BASE,
        "snapshot_id": sid,
        "acquired_at_utc": acquired_at,
        "request_policy": {
            "min_interval_seconds": MIN_INTERVAL_SECONDS,
            "page_limit": PAGE_LIMIT,
            "user_agent": USER_AGENT,
            "accept": ACCEPT,
        },
        "semantics": {
            "raw_only": True,
            "point_in_time_snapshot": True,
            "historical_backfill_allowed": False,
            "warning": (
                "Current career aggregates, rankings, streaks, status and other mutable "
                "fields are not historical features. They may only be used at prediction "
                "time if the snapshot predates the target fight, or for QA/current context."
            ),
        },
        "collections": collection_summaries,
        "files": manifest_files,
    }

    manifest_path = snapshot_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        f"[ufc.com] complete: snapshot={sid}; files={len(manifest_files)}; "
        f"bytes={sum(item['bytes'] for item in manifest_files)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
