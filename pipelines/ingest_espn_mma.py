#!/usr/bin/env python3
"""Snapshot free additive UFC data from ESPN's public MMA APIs.

This is a raw point-in-time acquisition pass. It intentionally keeps ESPN identity
and payloads separate from Greco/UFCStats. Historical feature use is a later,
explicit decision.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SITE_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"
CORE_BASE = "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc"
OUT_ROOT = Path("data/raw/espn_mma")
START_YEAR = 1993
MAX_RPS = 8.0
WORKERS = 8
USER_AGENT = "ufc-edge-data/0.1 (private modeling research; public ESPN snapshotter)"
OPTIONAL_KINDS = {"status", "officials", "plays", "competitor_stats"}

rate_lock = threading.Lock()
write_lock = threading.Lock()
schema_lock = threading.Lock()
last_request = 0.0
schema_summary: dict[str, set[str]] = {
    "competitor_stat_names": set(),
    "play_type_names": set(),
    "official_position_names": set(),
    "result_names": set(),
}
http_counts: dict[str, dict[int, int]] = {}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def snapshot_id() -> str:
    return os.environ.get("UFC_EDGE_SNAPSHOT_ID") or now_utc().strftime("%Y%m%dT%H%M%SZ")


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        raise RuntimeError(f"Refusing non-HTTPS URL: {url}")
    if parsed.netloc not in {"site.api.espn.com", "sports.core.api.espn.com"}:
        raise RuntimeError(f"Refusing unexpected ESPN host: {url}")


def throttle() -> None:
    global last_request
    with rate_lock:
        minimum = 1.0 / MAX_RPS
        wait = minimum - (time.monotonic() - last_request)
        if wait > 0:
            time.sleep(wait)
        last_request = time.monotonic()


def fetch_raw(url: str, *, attempts: int = 5) -> tuple[int, bytes, dict[str, str]]:
    validate_url(url)
    for attempt in range(1, attempts + 1):
        throttle()
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = resp.read()
                return resp.status, body, {
                    "content-type": resp.headers.get("content-type", ""),
                    "etag": resp.headers.get("etag", ""),
                    "last-modified": resp.headers.get("last-modified", ""),
                }
        except urllib.error.HTTPError as exc:
            body = exc.read()
            status = exc.code
            if (status == 429 or 500 <= status <= 599) and attempt < attempts:
                time.sleep(min(30.0, 2.0**attempt))
                continue
            return status, body, {
                "content-type": exc.headers.get("content-type", "") if exc.headers else "",
                "etag": exc.headers.get("etag", "") if exc.headers else "",
                "last-modified": exc.headers.get("last-modified", "") if exc.headers else "",
            }
        except urllib.error.URLError:
            if attempt < attempts:
                time.sleep(min(30.0, 2.0**attempt))
                continue
            raise
    raise RuntimeError(f"Failed to fetch {url}")


def parse_json(body: bytes, url: str, status: int) -> Any:
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        if 200 <= status < 300:
            raise RuntimeError(f"Non-JSON success response from {url}")
        return None


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def record_http(kind: str, status: int) -> None:
    with schema_lock:
        bucket = http_counts.setdefault(kind, {})
        bucket[status] = bucket.get(status, 0) + 1


def line_for(url: str, status: int, body: bytes, headers: dict[str, str]) -> str:
    try:
        body_text = body.decode("utf-8")
    except UnicodeDecodeError:
        body_text = body.decode("utf-8", errors="replace")
    obj = {
        "url": url,
        "http_status": status,
        "sha256": sha256_hex(body),
        "bytes": len(body),
        "content_type": headers.get("content-type") or None,
        "etag": headers.get("etag") or None,
        "last_modified": headers.get("last-modified") or None,
        "body": body_text,
    }
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"


def append_line(path: Path, line: str) -> None:
    with write_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)


def event_year(event: dict[str, Any], fallback: int) -> int:
    date = event.get("date")
    if isinstance(date, str) and len(date) >= 4 and date[:4].isdigit():
        return int(date[:4])
    season = event.get("season")
    if isinstance(season, dict) and isinstance(season.get("year"), int):
        return season["year"]
    return fallback


def extract_athlete_id(competitor: dict[str, Any]) -> str | None:
    athlete = competitor.get("athlete")
    if isinstance(athlete, dict):
        if athlete.get("id") is not None:
            return str(athlete["id"])
        ref = athlete.get("$ref")
        if isinstance(ref, str):
            match = re.search(r"/athletes/(\d+)", ref)
            if match:
                return match.group(1)
    ref = competitor.get("$ref")
    if isinstance(ref, str):
        match = re.search(r"/competitors/(\d+)", ref)
        if match:
            return match.group(1)
    return None


def update_schema(kind: str, payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    with schema_lock:
        if kind == "competitor_stats":
            splits = payload.get("splits")
            if isinstance(splits, dict):
                for category in splits.get("categories") or []:
                    if not isinstance(category, dict):
                        continue
                    for stat in category.get("stats") or []:
                        if isinstance(stat, dict) and stat.get("name"):
                            schema_summary["competitor_stat_names"].add(str(stat["name"]))
        elif kind == "plays":
            for item in payload.get("items") or []:
                if not isinstance(item, dict):
                    continue
                ptype = item.get("type")
                if isinstance(ptype, dict):
                    value = ptype.get("text") or ptype.get("name")
                    if value:
                        schema_summary["play_type_names"].add(str(value))
        elif kind == "officials":
            for item in payload.get("items") or []:
                if not isinstance(item, dict):
                    continue
                position = item.get("position")
                if isinstance(position, dict):
                    value = position.get("name") or position.get("displayName")
                    if value:
                        schema_summary["official_position_names"].add(str(value))
        elif kind == "status":
            result = payload.get("result")
            if isinstance(result, dict) and result.get("name"):
                schema_summary["result_names"].add(str(result["name"]))


def fetch_and_store(kind: str, url: str, out_path: Path) -> tuple[str, int]:
    status, body, headers = fetch_raw(url)
    record_http(kind, status)
    payload = parse_json(body, url, status)
    if 200 <= status < 300:
        update_schema(kind, payload)
    append_line(out_path, line_for(url, status, body, headers))
    if kind not in OPTIONAL_KINDS and not (200 <= status < 300):
        raise RuntimeError(f"Required ESPN request failed: kind={kind} status={status} url={url}")
    return kind, status


def scoreboard_url(year: int) -> str:
    params = {"dates": f"{year}0101-{year}1231", "limit": "1000"}
    return SITE_SCOREBOARD + "?" + urllib.parse.urlencode(params)


def core_event_url(event_id: str) -> str:
    return f"{CORE_BASE}/events/{event_id}?lang=en&region=us"


def main() -> int:
    current_year = now_utc().year
    sid = snapshot_id()
    snapshot_dir = OUT_ROOT / sid
    if snapshot_dir.exists():
        raise RuntimeError(f"Snapshot already exists: {snapshot_dir}")
    snapshot_dir.mkdir(parents=True)

    acquired_at = now_utc().isoformat().replace("+00:00", "Z")
    discovered_events: dict[str, int] = {}
    scoreboard_counts: dict[int, int] = {}

    for year in range(START_YEAR, current_year + 1):
        url = scoreboard_url(year)
        status, body, headers = fetch_raw(url)
        record_http("scoreboard", status)
        if not (200 <= status < 300):
            raise RuntimeError(f"Scoreboard discovery failed for {year}: HTTP {status}")
        payload = parse_json(body, url, status)
        events = payload.get("events") if isinstance(payload, dict) else None
        if not isinstance(events, list):
            raise RuntimeError(f"Scoreboard discovery returned no events list for {year}")
        scoreboard_counts[year] = len(events)
        year_dir = snapshot_dir / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)
        (year_dir / "scoreboard.json").write_bytes(body)
        (year_dir / "scoreboard.meta.json").write_text(
            json.dumps(
                {
                    "url": url,
                    "http_status": status,
                    "sha256": sha256_hex(body),
                    "bytes": len(body),
                    "content_type": headers.get("content-type") or None,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        for event in events:
            if not isinstance(event, dict) or event.get("id") is None:
                continue
            eid = str(event["id"])
            discovered_events[eid] = event_year(event, year)
        print(f"[espn] scoreboard {year}: {len(events)} events", flush=True)

    recent_complete_years = [y for y in range(max(2018, current_year - 5), current_year)]
    weak = [y for y in recent_complete_years if scoreboard_counts.get(y, 0) < 10]
    if weak:
        raise RuntimeError(
            "ESPN historical scoreboard discovery looks incomplete for years "
            + ", ".join(map(str, weak))
            + "; refusing to create a misleading partial archive."
        )

    event_details: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {}
        for eid, year in discovered_events.items():
            url = core_event_url(eid)
            path = snapshot_dir / str(year) / "event_details.jsonl"
            futures[pool.submit(fetch_raw, url)] = (eid, year, url, path)

        for i, future in enumerate(as_completed(futures), 1):
            eid, year, url, path = futures[future]
            status, body, headers = future.result()
            record_http("event_detail", status)
            if not (200 <= status < 300):
                raise RuntimeError(f"Core event failed: {eid} HTTP {status}")
            payload = parse_json(body, url, status)
            append_line(path, line_for(url, status, body, headers))
            if isinstance(payload, dict):
                event_details[eid] = payload
            if i % 100 == 0:
                print(f"[espn] event details: {i}/{len(futures)}", flush=True)

    requests: list[tuple[str, str, Path]] = []
    competition_count = 0
    competitor_stat_request_count = 0

    for eid, event in event_details.items():
        year = discovered_events[eid]
        competitions = event.get("competitions") or []
        if not isinstance(competitions, list):
            continue
        for comp in competitions:
            if not isinstance(comp, dict) or comp.get("id") is None:
                continue
            cid = str(comp["id"])
            competition_count += 1
            base = f"{CORE_BASE}/events/{eid}/competitions/{cid}"
            year_dir = snapshot_dir / str(year)
            requests.extend(
                [
                    ("status", base + "/status?lang=en&region=us", year_dir / "competition_status.jsonl"),
                    ("officials", base + "/officials?limit=100&lang=en&region=us", year_dir / "officials.jsonl"),
                    ("plays", base + "/plays?limit=100&lang=en&region=us", year_dir / "plays.jsonl"),
                ]
            )
            competitors = comp.get("competitors") or []
            if isinstance(competitors, list):
                for competitor in competitors:
                    if not isinstance(competitor, dict):
                        continue
                    athlete_id = extract_athlete_id(competitor)
                    if not athlete_id:
                        continue
                    stats_url = base + f"/competitors/{athlete_id}/statistics?lang=en&region=us"
                    requests.append(("competitor_stats", stats_url, year_dir / "competitor_stats.jsonl"))
                    competitor_stat_request_count += 1

    print(
        f"[espn] discovered {len(discovered_events)} events, {competition_count} competitions, "
        f"{competitor_stat_request_count} competitor-stat requests",
        flush=True,
    )

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(fetch_and_store, kind, url, path) for kind, url, path in requests]
        for i, future in enumerate(as_completed(futures), 1):
            future.result()
            if i % 1000 == 0:
                print(f"[espn] fight-level requests: {i}/{len(futures)}", flush=True)

    summary = {
        "schema_version": 1,
        "source": "ESPN public MMA APIs",
        "snapshot_id": sid,
        "acquired_at_utc": acquired_at,
        "years": [START_YEAR, current_year],
        "discovery": {
            "method": "site scoreboard yearly date ranges",
            "event_count": len(discovered_events),
            "events_by_scoreboard_year": scoreboard_counts,
        },
        "counts": {
            "competitions": competition_count,
            "fight_level_requests": len(requests),
            "competitor_stat_requests": competitor_stat_request_count,
        },
        "http_status_counts": {
            kind: {str(status): count for status, count in sorted(values.items())}
            for kind, values in sorted(http_counts.items())
        },
        "schema_observed": {key: sorted(values) for key, values in schema_summary.items()},
        "semantics": {
            "raw_only": True,
            "historical_feature_use_not_yet_approved": True,
            "notes": [
                "ESPN identifiers remain source-specific until a separately audited crosswalk is built.",
                "404/empty optional fight-level surfaces are preserved as coverage evidence, not converted to zero values.",
                "Competitor statistics are collected for source inventory/coverage comparison with Greco; duplicate concepts are not merged here.",
                "ESPN plays are expected to be sparse/structural and are not labeled strike-by-strike without evidence.",
            ],
        },
    }
    (snapshot_dir / "manifest.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        f"[espn] complete: snapshot={sid}; events={len(discovered_events)}; "
        f"competitions={competition_count}; requests={len(requests)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
