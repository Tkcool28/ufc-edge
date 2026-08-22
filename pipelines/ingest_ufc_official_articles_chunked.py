#!/usr/bin/env python3
"""Acquire official UFC weigh-in/scorecard articles in bounded immutable chunks.

Enumeration comes only from the already-snapshotted official UFC sitemap candidate
catalog. The collector never searches or follows arbitrary links. Navigation/index URLs
that were classified by keyword are excluded before candidate indexing. Existing chunks
may be resumed only when their stored URL prefix exactly matches the filtered catalog.
404/410/403 responses are preserved as coverage evidence rather than converted to missing
values. A family-level manifest is written only after every eligible candidate index is covered.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CATALOG = Path("data/derived/discovery/ufc_content_candidates.csv")
OUT_ROOT = Path("data/raw/ufc_official_articles")
PAGE_DELAY = 2.0
USER_AGENT = "ufc-edge-data/0.7 (private modeling research; official UFC catalog article snapshot)"
ALLOWED_FAMILIES = {"weigh_in", "scorecard"}
ALLOWED_HOSTS = {"ufc.com", "www.ufc.com"}
_last_request = 0.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def is_eligible_news_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.netloc.lower() in ALLOWED_HOSTS
        and parsed.path.startswith("/news/")
    )


def load_candidates(family: str) -> list[dict[str, str]]:
    if family not in ALLOWED_FAMILIES:
        raise RuntimeError(f"Unsupported family: {family}")
    with CATALOG.open("r", encoding="utf-8", newline="") as fh:
        family_rows = [row for row in csv.DictReader(fh) if row.get("family") == family]
    # The discovery catalog intentionally preserves keyword hits including navigation pages
    # such as /scorecards. Acquisition is narrower: only explicit UFC /news/ article URLs.
    rows = [row for row in family_rows if is_eligible_news_url(row.get("url") or "")]
    rows.sort(key=lambda row: row["url"])
    if not rows:
        raise RuntimeError(f"No eligible UFC /news/ catalog candidates for {family}")
    urls = [row["url"] for row in rows]
    if len(urls) != len(set(urls)):
        raise RuntimeError(f"Duplicate URLs in filtered candidate catalog for {family}")
    return rows


def validate_ufc_url(url: str) -> None:
    if not is_eligible_news_url(url):
        raise RuntimeError(f"Refusing non-news candidate URL: {url}")


def fetch(url: str, attempts: int = 4) -> dict[str, Any]:
    global _last_request
    validate_ufc_url(url)
    for attempt in range(1, attempts + 1):
        wait = PAGE_DELAY - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                _last_request = time.monotonic()
                final_url = response.geturl()
                validate_ufc_url(final_url)
                body = response.read(8_000_000)
                return {
                    "status": int(response.status),
                    "body": body,
                    "final_url": final_url,
                    "content_type": response.headers.get("content-type", ""),
                    "etag": response.headers.get("etag", ""),
                    "last_modified": response.headers.get("last-modified", ""),
                }
        except urllib.error.HTTPError as exc:
            _last_request = time.monotonic()
            body = exc.read(2_000_000)
            if exc.code in {404, 410, 403}:
                final_url = exc.geturl() or url
                # A redirect to a non-news landing page is not a valid article response.
                validate_ufc_url(final_url)
                return {
                    "status": int(exc.code),
                    "body": body,
                    "final_url": final_url,
                    "content_type": exc.headers.get("content-type", "") if exc.headers else "",
                    "etag": exc.headers.get("etag", "") if exc.headers else "",
                    "last_modified": exc.headers.get("last-modified", "") if exc.headers else "",
                }
            if (exc.code == 429 or 500 <= exc.code <= 599) and attempt < attempts:
                time.sleep(min(30.0, 2.0**attempt))
                continue
            raise
        except urllib.error.URLError:
            _last_request = time.monotonic()
            if attempt < attempts:
                time.sleep(min(30.0, 2.0**attempt))
                continue
            raise
    raise RuntimeError(f"Exhausted retries for {url}")


def safe_stub(url: str) -> str:
    slug = urllib.parse.urlparse(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")[:70]
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{slug or 'article'}-{digest}"


def existing_records(family_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    expected = 0
    for path in sorted(family_dir.glob("chunks/index_*/chunk_manifest.json")):
        chunk = json.loads(path.read_text(encoding="utf-8"))
        start = int(chunk["chunk_start_index"])
        stop = int(chunk["chunk_end_index_exclusive"])
        if start != expected:
            raise RuntimeError(f"Existing chunk gap/overlap: expected {expected}, found {start}")
        chunk_records = list(chunk.get("records") or [])
        if len(chunk_records) != stop - start:
            raise RuntimeError(f"Existing chunk record count mismatch: {path}")
        records.extend(chunk_records)
        expected = stop
    return records


def verify_resume_prefix(series_id: str, family: str, candidates: list[dict[str, str]], start_index: int) -> None:
    family_dir = OUT_ROOT / series_id / family
    records = existing_records(family_dir)
    if start_index == 0:
        if records:
            raise RuntimeError("Cannot start at zero when immutable chunks already exist")
        return
    if len(records) != start_index:
        raise RuntimeError(
            f"Resume index does not equal existing gap-free record count: start={start_index}, existing={len(records)}"
        )
    stored_urls = [str(row["catalog_url"]) for row in records]
    candidate_prefix = [row["url"] for row in candidates[:start_index]]
    if stored_urls != candidate_prefix:
        for idx, (stored, expected) in enumerate(zip(stored_urls, candidate_prefix)):
            if stored != expected:
                raise RuntimeError(
                    f"Filtered-catalog resume prefix mismatch at {idx}: stored={stored!r}, expected={expected!r}"
                )
        raise RuntimeError("Filtered-catalog resume prefix mismatch")


def collect(series_id: str, family: str, start_index: int, max_items: int) -> Path:
    candidates = load_candidates(family)
    if start_index < 0 or start_index >= len(candidates):
        raise RuntimeError(f"start_index out of range: {start_index} of {len(candidates)}")
    if max_items < 1 or max_items > 100:
        raise RuntimeError("max_items must be in [1,100]")

    family_dir = OUT_ROOT / series_id / family
    if (family_dir / "manifest.json").exists():
        raise RuntimeError(f"Family already finalized: {family_dir}")
    verify_resume_prefix(series_id, family, candidates, start_index)

    chunk_dir = family_dir / "chunks" / f"index_{start_index:06d}"
    if chunk_dir.exists():
        raise RuntimeError(f"Immutable chunk already exists: {chunk_dir}")
    chunk_dir.mkdir(parents=True, exist_ok=False)

    stop = min(len(candidates), start_index + max_items)
    selected = candidates[start_index:stop]
    records: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    started = utc_now()

    for relative, candidate in enumerate(selected):
        absolute_index = start_index + relative
        url = candidate["url"]
        response = fetch(url)
        status = int(response["status"])
        status_counts[str(status)] = status_counts.get(str(status), 0) + 1
        body: bytes = response["body"]
        filename = f"item_{absolute_index:06d}_{safe_stub(url)}.html"
        path = chunk_dir / filename
        path.write_bytes(body)
        records.append(
            {
                "candidate_index": absolute_index,
                "catalog_url": url,
                "catalog_lastmod": candidate.get("lastmod") or None,
                "http_status": status,
                "final_url": response["final_url"],
                "content_type": response["content_type"] or None,
                "etag": response["etag"] or None,
                "last_modified": response["last_modified"] or None,
                "path": path.as_posix(),
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )

    terminal = stop == len(candidates)
    manifest = {
        "schema_version": 2,
        "source": "Official UFC.com public news pages",
        "enumeration_source": CATALOG.as_posix(),
        "series_id": series_id,
        "family": family,
        "catalog_family_rows_before_url_gate": sum(
            1 for row in csv.DictReader(CATALOG.open("r", encoding="utf-8", newline="")) if row.get("family") == family
        ),
        "eligible_candidate_count": len(candidates),
        "chunk_start_index": start_index,
        "chunk_end_index_exclusive": stop,
        "items": len(records),
        "terminal": terminal,
        "next_index": None if terminal else stop,
        "started_at_utc": started,
        "completed_at_utc": utc_now(),
        "request_policy": {
            "min_interval_seconds": PAGE_DELAY,
            "max_items_per_chunk": max_items,
            "allowed_hosts": sorted(ALLOWED_HOSTS),
            "allowed_path_prefix": "/news/",
            "navigation_keyword_hits_excluded_before_indexing": True,
        },
        "status_counts": status_counts,
        "records": records,
        "semantics": {
            "raw_only": True,
            "404_410_403_are_coverage_evidence": True,
            "chunk_immutable": True,
            "no_article_parsing_yet": True,
            "candidate_url_does_not_imply_valid_structured_observation": True,
            "resume_prefix_must_match_filtered_catalog_exactly": True,
        },
    }
    path = chunk_dir / "chunk_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "family": family,
        "start": start_index,
        "stop": stop,
        "terminal": terminal,
        "next_index": manifest["next_index"],
        "status_counts": status_counts,
    }, sort_keys=True))
    return path


def finalize(series_id: str, family: str) -> Path:
    candidates = load_candidates(family)
    family_dir = OUT_ROOT / series_id / family
    final = family_dir / "manifest.json"
    if final.exists():
        return final
    manifests = sorted(family_dir.glob("chunks/index_*/chunk_manifest.json"))
    if not manifests:
        raise RuntimeError(f"No chunks for {family}")

    expected = 0
    total_items = 0
    statuses: dict[str, int] = {}
    records: list[dict[str, Any]] = []
    chunk_paths: list[str] = []
    for path in manifests:
        chunk = json.loads(path.read_text(encoding="utf-8"))
        start = int(chunk["chunk_start_index"])
        stop = int(chunk["chunk_end_index_exclusive"])
        if start != expected:
            raise RuntimeError(f"Gap/overlap for {family}: expected {expected}, found {start}")
        expected = stop
        total_items += int(chunk["items"])
        chunk_paths.append(path.as_posix())
        records.extend(chunk["records"])
        for key, value in (chunk.get("status_counts") or {}).items():
            statuses[key] = statuses.get(key, 0) + int(value)

    if expected != len(candidates):
        raise RuntimeError(f"Incomplete {family}: covered {expected}/{len(candidates)} eligible candidates")
    indexes = [int(record["candidate_index"]) for record in records]
    if indexes != list(range(len(candidates))):
        raise RuntimeError(f"Candidate index series is not exactly gap-free for {family}")
    urls = [str(record["catalog_url"]) for record in records]
    expected_urls = [row["url"] for row in candidates]
    if urls != expected_urls:
        raise RuntimeError(f"Finalized URL order differs from filtered catalog for {family}")

    with CATALOG.open("r", encoding="utf-8", newline="") as fh:
        family_catalog_count = sum(1 for row in csv.DictReader(fh) if row.get("family") == family)
    manifest = {
        "schema_version": 2,
        "source": "Official UFC.com public news pages",
        "enumeration_source": CATALOG.as_posix(),
        "series_id": series_id,
        "family": family,
        "complete_family_snapshot": True,
        "catalog_family_rows_before_url_gate": family_catalog_count,
        "eligible_candidate_count": len(candidates),
        "excluded_navigation_or_non_news_rows": family_catalog_count - len(candidates),
        "items": total_items,
        "status_counts": statuses,
        "chunk_manifests": chunk_paths,
        "completed_at_utc": utc_now(),
        "rules": {
            "gap_free_filtered_catalog_index_required": True,
            "raw_responses_immutable": True,
            "http_errors_preserved_as_coverage_evidence": True,
            "structured_parsing_requires_separate_audit": True,
            "only_https_ufc_news_urls_eligible": True,
        },
    }
    final.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"family": family, "complete": True, "items": total_items, "status_counts": statuses}, sort_keys=True))
    return final


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--series-id", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    chunk = sub.add_parser("chunk")
    chunk.add_argument("--family", required=True, choices=sorted(ALLOWED_FAMILIES))
    chunk.add_argument("--start-index", type=int, required=True)
    chunk.add_argument("--max-items", type=int, default=75)
    fin = sub.add_parser("finalize")
    fin.add_argument("--family", required=True, choices=sorted(ALLOWED_FAMILIES))
    args = parser.parse_args()
    if args.command == "chunk":
        collect(args.series_id, args.family, args.start_index, args.max_items)
    else:
        finalize(args.series_id, args.family)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
