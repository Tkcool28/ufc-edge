#!/usr/bin/env python3
"""Estimate storage footprint for official UFC scorecard image candidates.

This bounded probe never writes binary media to the repository. It deduplicates the
candidate URL catalog, takes a deterministic evenly-spaced sample, and uses HEAD (with a
small ranged GET fallback) to estimate content lengths/types before any archive decision.
"""
from __future__ import annotations

import csv
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/derived/discovery/ufc_scorecard_image_candidates.csv"
OUT = ROOT / "provenance/audits/ufc_scorecard_image_storage_probe_latest.json"
SAMPLE_N = 240
DELAY = 0.25
UA = "ufc-edge-data/0.8 (private modeling research; scorecard media sizing probe)"


def read_urls() -> list[str]:
    with CATALOG.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    seen: set[str] = set(); urls: list[str] = []
    for row in rows:
        url = (row.get("image_url") or "").strip()
        if not url or url in seen:
            continue
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc.lower() not in {"ufc.com", "www.ufc.com"}:
            continue
        seen.add(url); urls.append(url)
    return sorted(urls)


def sample_evenly(items: list[str], n: int) -> list[str]:
    if len(items) <= n:
        return items
    indexes = sorted({round(i * (len(items) - 1) / (n - 1)) for i in range(n)})
    return [items[i] for i in indexes]


def probe(url: str) -> dict:
    headers = {"User-Agent": UA, "Accept": "image/*,*/*;q=0.1"}
    request = urllib.request.Request(url, headers=headers, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return {
                "status": int(response.status), "content_length": response.headers.get("Content-Length"),
                "content_type": response.headers.get("Content-Type"), "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"), "method": "HEAD", "error": None,
            }
    except urllib.error.HTTPError as exc:
        if exc.code not in {400, 403, 405, 501}:
            return {"status": exc.code, "content_length": None, "content_type": None, "etag": None, "last_modified": None, "method": "HEAD", "error": str(exc)}
    except Exception:
        pass

    request = urllib.request.Request(url, headers={**headers, "Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            total = None
            content_range = response.headers.get("Content-Range") or ""
            if "/" in content_range:
                total = content_range.rsplit("/", 1)[-1]
            if not total or total == "*":
                total = response.headers.get("Content-Length")
            return {
                "status": int(response.status), "content_length": total,
                "content_type": response.headers.get("Content-Type"), "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"), "method": "RANGE_GET", "error": None,
            }
    except Exception as exc:
        return {"status": getattr(exc, "code", None), "content_length": None, "content_type": None, "etag": None, "last_modified": None, "method": "RANGE_GET", "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    urls = read_urls(); sampled = sample_evenly(urls, SAMPLE_N)
    rows = []; sizes = []; statuses = Counter(); types = Counter(); methods = Counter()
    for url in sampled:
        result = probe(url); result["url"] = url; rows.append(result)
        statuses[str(result.get("status"))] += 1; methods[str(result.get("method"))] += 1
        if result.get("content_type"): types[str(result["content_type"]).split(";",1)[0].strip().lower()] += 1
        try:
            size = int(result.get("content_length"))
            if size > 0: sizes.append(size)
        except (TypeError, ValueError):
            pass
        time.sleep(DELAY)

    estimate = None
    if sizes:
        ordered = sorted(sizes)
        mean = sum(sizes) / len(sizes)
        median = ordered[len(ordered)//2]
        p90 = ordered[min(len(ordered)-1, math.floor(0.90*(len(ordered)-1)))]
        estimate = {
            "sample_with_size": len(sizes), "mean_bytes": mean, "median_bytes": median, "p90_bytes": p90,
            "estimated_unique_catalog_bytes_from_mean": round(mean * len(urls)),
            "estimated_unique_catalog_mib_from_mean": round(mean * len(urls) / (1024*1024), 2),
        }

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_catalog": str(CATALOG.relative_to(ROOT)),
        "unique_eligible_urls": len(urls), "sample_requested": SAMPLE_N, "sampled_urls": len(sampled),
        "status_counts": dict(statuses), "method_counts": dict(methods), "content_type_counts": dict(types),
        "size_estimate": estimate, "sample_results": rows,
        "decision": {
            "binary_media_committed": False,
            "probe_only": True,
            "next_gate": "Choose Git storage vs hashed transient-fetch OCR based on measured footprint and repository-size budget.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"unique_urls": len(urls), "sampled": len(sampled), "size_estimate": estimate}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
