#!/usr/bin/env python3
"""Snapshot official UFC.com FightMetric fight_stat and round-record resources.

This is raw acquisition plus source-coverage accounting only. It does not join the
records to Greco or treat missing fields as zero.
"""

from __future__ import annotations

import collections
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

BASE = "https://www.ufc.com/jsonapi"
OUT_ROOT = Path("data/raw/ufc_fightmetric_official")
PAGE_LIMIT = 50
MIN_INTERVAL_SECONDS = 2.0
USER_AGENT = "ufc-edge-data/0.1 (private modeling research; respectful official FightMetric snapshotter)"

COLLECTIONS = {
    "fight_stat": "/fight_stat/fight_stat",
    "fight_roundboard": "/fight_roundboard/fight_roundboard",
}

TIP_FIELDS = [
    "standing_time",
    "neutral_time",
    "distance_time",
    "clinch_time",
    "ground_time",
    "control_time",
    "ground_ctl_time",
    "guard_ctl_time",
    "half_guard_ctl_time",
    "side_ctl_time",
    "mount_ctl_time",
    "back_ctl_time",
    "msc_ground_ctl__time",
]

_last_request_at = 0.0


def snapshot_id() -> str:
    return os.environ.get("UFC_EDGE_SNAPSHOT_ID") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def validate_url(url: str, path_prefix: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc not in {"www.ufc.com", "ufc.com"}:
        raise RuntimeError(f"Refusing unexpected host: {url}")
    if not parsed.path.startswith("/jsonapi" + path_prefix):
        raise RuntimeError(f"Refusing pagination outside expected collection: {url}")


def fetch(url: str, path_prefix: str) -> tuple[bytes, dict[str, str]]:
    global _last_request_at
    validate_url(url, path_prefix)
    delay = MIN_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
    if delay > 0:
        time.sleep(delay)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.api+json"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        _last_request_at = time.monotonic()
        body = response.read()
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type.lower():
            raise RuntimeError(f"Expected JSON; got {content_type!r} from {url}")
        return body, {
            "content_type": content_type,
            "etag": response.headers.get("etag", ""),
            "last_modified": response.headers.get("last-modified", ""),
        }


def first_url(path: str) -> str:
    return BASE + path + "?" + urllib.parse.urlencode({"page[limit]": str(PAGE_LIMIT)})


def next_url(payload: dict[str, Any]) -> str | None:
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

    files: list[dict[str, Any]] = []
    collection_reports: list[dict[str, Any]] = []

    for name, path in COLLECTIONS.items():
        url: str | None = first_url(path)
        page = 1
        seen: set[str] = set()
        row_count = 0
        attribute_seen = collections.Counter()
        attribute_nonnull = collections.Counter()
        type_counts = collections.Counter()
        fightmetric_ids: set[str] = set()
        round_counts = collections.Counter()
        internal_ids: list[int] = []

        while url:
            validate_url(url, path)
            if url in seen:
                raise RuntimeError(f"Pagination loop in {name}: {url}")
            seen.add(url)
            body, headers = fetch(url, path)
            payload = json.loads(body)
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise RuntimeError(f"{name} page {page} lacks list-valued data")

            dest = out_dir / name / f"page_{page:04d}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            files.append(
                {
                    "collection": name,
                    "path": dest.as_posix(),
                    "url": url,
                    "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "records": len(data),
                    "content_type": headers["content_type"],
                    "etag": headers["etag"] or None,
                    "last_modified": headers["last_modified"] or None,
                }
            )

            for item in data:
                if not isinstance(item, dict):
                    continue
                row_count += 1
                if item.get("type"):
                    type_counts[str(item["type"])] += 1
                attrs = item.get("attributes")
                if not isinstance(attrs, dict):
                    continue
                for key, value in attrs.items():
                    attribute_seen[str(key)] += 1
                    if value is not None and value != "":
                        attribute_nonnull[str(key)] += 1
                fid = attrs.get("fightmetric_id")
                if fid is not None and fid != "":
                    fightmetric_ids.add(str(fid))
                rnd = attrs.get("round")
                if rnd is not None and rnd != "":
                    round_counts[str(rnd)] += 1
                iid = attrs.get("drupal_internal__id")
                if isinstance(iid, int):
                    internal_ids.append(iid)

            if page % 50 == 0:
                print(f"[ufc FightMetric] {name}: page={page} rows={row_count}", flush=True)
            url = next_url(payload)
            page += 1

        if row_count == 0:
            raise RuntimeError(f"Official UFC collection {name} returned zero rows")

        coverage = {
            key: {
                "seen_rows": int(attribute_seen[key]),
                "nonnull_rows": int(attribute_nonnull[key]),
                "nonnull_fraction": (attribute_nonnull[key] / row_count) if row_count else None,
            }
            for key in sorted(attribute_seen)
        }
        collection_reports.append(
            {
                "collection": name,
                "pages": page - 1,
                "rows": row_count,
                "resource_type_counts": dict(sorted(type_counts.items())),
                "distinct_nonnull_fightmetric_ids": len(fightmetric_ids),
                "round_value_counts": dict(sorted(round_counts.items())),
                "drupal_internal_id_min": min(internal_ids) if internal_ids else None,
                "drupal_internal_id_max": max(internal_ids) if internal_ids else None,
                "attribute_coverage": coverage,
                "tip_field_coverage": {key: coverage.get(key) for key in TIP_FIELDS},
            }
        )
        print(f"[ufc FightMetric] {name}: complete rows={row_count} pages={page - 1}", flush=True)

    manifest = {
        "schema_version": 1,
        "source": "Official UFC.com Drupal JSON:API FightMetric resources",
        "snapshot_id": sid,
        "acquired_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "request_policy": {
            "page_limit": PAGE_LIMIT,
            "min_interval_seconds": MIN_INTERVAL_SECONDS,
        },
        "collections": collection_reports,
        "files": files,
        "semantics": {
            "raw_only": True,
            "missing_is_not_zero": True,
            "fightmetric_identity_not_yet_crosswalked": True,
            "notes": [
                "fight_stat exposes detailed FightMetric striking, grappling and time-in-position fields including guard/half-guard/side/mount/back control.",
                "Coverage varies by era; manifest non-null counts must be consulted before any historical feature or simulator state is defined.",
                "fight_roundboard is a record-book surface and is not assumed to enumerate every fighter-round.",
                "No current or future source row may be used for a historical target without a separately audited identity/time join."
            ],
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[ufc FightMetric] snapshot complete: {sid}; files={len(files)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
