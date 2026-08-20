#!/usr/bin/env python3
"""Probe high-value UFC.com JSON:API surfaces before bulk ingestion."""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = "https://www.ufc.com/jsonapi"
OUT = Path("provenance/ufc_jsonapi_surface_probe.json")
RAW_DIR = Path("provenance/ufc_jsonapi_surface_probe_raw")
USER_AGENT = "ufc-edge-data/0.1 (private modeling research; bounded surface probe)"

SURFACES = {
    "fight_stat": "/fight_stat/fight_stat",
    "fight_roundboard": "/fight_roundboard/fight_roundboard",
    "article": "/node/article",
    "athlete_pairing": "/athlete_pairing/athlete_pairing",
    "event_leaderboard": "/event_leaderboard/event_leaderboard",
    "interactive_fight_card": "/interactive_fight_card/interactive_fight_card",
}


def fetch(name: str, path: str) -> dict[str, Any]:
    params = urllib.parse.urlencode({"page[limit]": "5"})
    url = BASE + path + "?" + params
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.api+json"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read()
        status = response.status
        content_type = response.headers.get("content-type", "")
    if status != 200:
        raise RuntimeError(f"{name}: HTTP {status}")
    payload = json.loads(body)
    raw_path = RAW_DIR / f"{name}.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(body)

    data = payload.get("data") if isinstance(payload, dict) else None
    samples = data if isinstance(data, list) else []
    attr_keys: set[str] = set()
    rel_keys: set[str] = set()
    types: set[str] = set()
    sample_summaries: list[dict[str, Any]] = []
    for item in samples:
        if not isinstance(item, dict):
            continue
        if item.get("type"):
            types.add(str(item["type"]))
        attrs = item.get("attributes")
        rels = item.get("relationships")
        if isinstance(attrs, dict):
            attr_keys.update(map(str, attrs.keys()))
        if isinstance(rels, dict):
            rel_keys.update(map(str, rels.keys()))
        sample_summaries.append(
            {
                "id": item.get("id"),
                "type": item.get("type"),
                "attributes": attrs,
                "relationship_keys": sorted(rels.keys()) if isinstance(rels, dict) else [],
            }
        )

    links = payload.get("links") if isinstance(payload, dict) else {}
    has_next = bool(links.get("next")) if isinstance(links, dict) else False
    return {
        "name": name,
        "url": url,
        "http_status": status,
        "content_type": content_type,
        "raw_path": raw_path.as_posix(),
        "raw_sha256": hashlib.sha256(body).hexdigest(),
        "sample_count": len(samples),
        "resource_types": sorted(types),
        "attribute_keys": sorted(attr_keys),
        "relationship_keys": sorted(rel_keys),
        "has_next_page": has_next,
        "samples": sample_summaries,
    }


def main() -> int:
    results = []
    errors = []
    for index, (name, path) in enumerate(SURFACES.items()):
        if index:
            time.sleep(2.0)
        try:
            results.append(fetch(name, path))
        except Exception as exc:
            errors.append({"name": name, "path": path, "error": repr(exc)})

    report = {
        "schema_version": 1,
        "acquired_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "Official UFC.com Drupal JSON:API",
        "bounded_probe": True,
        "surfaces": results,
        "errors": errors,
        "probe_semantics": {
            "partial_success_is_valid": True,
            "note": "Unsupported or failing CMS collections are recorded as source-coverage evidence and do not invalidate successful surface samples."
        },
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Probed {len(results)} UFC JSON:API surfaces; errors={len(errors)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
