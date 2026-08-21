#!/usr/bin/env python3
"""Probe candidate deterministic sort orders for UFC /node/fight pagination.

This is intentionally bounded. It tests a few pages per candidate and records overlap,
HTTP failures, and observed ordering keys. No candidate is accepted merely because the
endpoint returns 200; page overlap must be zero and a unique stable tie-breaker must be
present in the returned resource.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = "https://www.ufc.com/jsonapi/node/fight"
OUT = Path("provenance/ufc_fight_sort_probe.json")
PAGE_LIMIT = 50
OFFSETS = [0, 50, 100, 150]
CANDIDATES = [
    "created",
    "drupal_internal__nid",
    "created,drupal_internal__nid",
    "created,id",
]
HEADERS = {
    "Accept": "application/vnd.api+json",
    "User-Agent": "ufc-edge-data/0.4 (private modeling research; bounded pagination QA)",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def request(sort_value: str, offset: int) -> dict[str, Any]:
    q = urllib.parse.urlencode({
        "sort": sort_value,
        "page[limit]": str(PAGE_LIMIT),
        "page[offset]": str(offset),
    })
    url = BASE + "?" + q
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.load(resp)
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise RuntimeError("missing list-valued data")
            rows = []
            for item in data:
                attrs = item.get("attributes") if isinstance(item, dict) else None
                attrs = attrs if isinstance(attrs, dict) else {}
                rows.append({
                    "id": None if not isinstance(item, dict) else item.get("id"),
                    "created": attrs.get("created"),
                    "drupal_internal__nid": attrs.get("drupal_internal__nid"),
                })
            return {
                "ok": True,
                "status": resp.status,
                "url": url,
                "rows": rows,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read(2048).decode("utf-8", errors="replace")
        return {"ok": False, "status": exc.code, "url": url, "error": body}
    except Exception as exc:
        return {"ok": False, "status": None, "url": url, "error": f"{type(exc).__name__}: {exc}"}


def analyze(sort_value: str) -> dict[str, Any]:
    pages = []
    all_ids: list[str] = []
    for offset in OFFSETS:
        result = request(sort_value, offset)
        pages.append(result)
        if result.get("ok"):
            all_ids.extend(str(r["id"]) for r in result["rows"] if r.get("id") is not None)
        time.sleep(2.0)

    ok_pages = [p for p in pages if p.get("ok")]
    duplicates = sorted({rid for rid in all_ids if all_ids.count(rid) > 1})
    pair_overlaps = []
    for a, b in zip(ok_pages, ok_pages[1:]):
        a_ids = {str(r["id"]) for r in a["rows"] if r.get("id") is not None}
        b_ids = {str(r["id"]) for r in b["rows"] if r.get("id") is not None}
        pair_overlaps.append(len(a_ids & b_ids))

    nids = [r.get("drupal_internal__nid") for p in ok_pages for r in p["rows"]]
    nonnull_nids = [x for x in nids if x is not None]
    return {
        "sort": sort_value,
        "pages_requested": len(OFFSETS),
        "pages_ok": len(ok_pages),
        "rows_seen": len(all_ids),
        "distinct_ids": len(set(all_ids)),
        "duplicate_ids": duplicates[:50],
        "duplicate_id_count": len(duplicates),
        "adjacent_page_overlap_counts": pair_overlaps,
        "drupal_internal_nid_present_fraction": (len(nonnull_nids) / len(nids)) if nids else None,
        "drupal_internal_nid_unique_in_sample": len(nonnull_nids) == len(set(nonnull_nids)) if nonnull_nids else None,
        "sample_first": ok_pages[0]["rows"][:3] if ok_pages else [],
        "sample_last": ok_pages[-1]["rows"][-3:] if ok_pages else [],
        "page_results": pages,
    }


def main() -> int:
    results = [analyze(candidate) for candidate in CANDIDATES]
    accepted = []
    for r in results:
        if (
            r["pages_ok"] == len(OFFSETS)
            and r["duplicate_id_count"] == 0
            and all(x == 0 for x in r["adjacent_page_overlap_counts"])
        ):
            accepted.append(r["sort"])
    payload = {
        "schema_version": 1,
        "probed_at_utc": now(),
        "endpoint": "/jsonapi/node/fight",
        "page_limit": PAGE_LIMIT,
        "offsets": OFFSETS,
        "candidates": results,
        "zero_overlap_candidates_in_bounded_sample": accepted,
        "decision_rule": "A production sort still requires a unique stable tie-breaker; bounded zero overlap alone is not sufficient.",
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"probe": str(OUT), "zero_overlap_candidates": accepted}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
