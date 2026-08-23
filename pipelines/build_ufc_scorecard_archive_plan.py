#!/usr/bin/env python3
"""Build a fail-closed archive plan for high-confidence official UFC scorecard images.

DATA PHASE ONLY. This step downloads nothing. It selects only v5
high_confidence_fight_candidate rows and audits URL/fight multiplicity before binary archival.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/derived/identity/ufc_scorecard_identity_transport_candidate.csv"
IDENTITY_AUDIT = ROOT / "provenance/audits/ufc_scorecard_identity_transport_latest.json"
OUT = ROOT / "data/derived/identity/ufc_scorecard_archive_plan_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_archive_plan_v0_latest.json"

FIELDS = [
    "archive_key", "candidate_fight_id", "candidate_event_id", "candidate_event_name", "candidate_event_date",
    "article_candidate_index", "article_url", "article_title", "image_url", "image_alt", "image_title",
    "fighter_left_phrase", "fighter_right_phrase", "matched_fighter_ids", "matched_fighter_names",
    "identity_text_source", "identity_text", "identity_status", "review_status",
]
ALLOWED_IMAGE_HOSTS = {
    "ufc.com",
    "www.ufc.com",
    "dmxg5wxfqgb4u.cloudfront.net",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def archive_key(url: str) -> str:
    path = urlsplit(url).path
    ext = Path(path).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".bin"
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24] + ext


def main() -> int:
    audit = json.loads(IDENTITY_AUDIT.read_text(encoding="utf-8"))
    if audit.get("schema_version") != 5:
        raise RuntimeError("scorecard identity audit is not v5")
    counts = audit.get("counts") or {}
    if counts.get("images_high_confidence_fight_candidate") != 578:
        raise RuntimeError("scorecard high-confidence image count drift")
    if audit.get("mapped_fights") != 575:
        raise RuntimeError(f"scorecard mapped-fight count drift: {audit.get('mapped_fights')}")
    decision = audit.get("decision") or {}
    required = {
        "ocr_performed": False,
        "canonical_judge_round_scores_written": False,
        "display_name_only_identity_trusted": False,
        "free_floating_surname_match_forbidden": True,
        "generic_hero_alt_identity_forbidden": True,
        "scorecard_token_required_for_identity_text": True,
        "whole_side_trailing_name_phrase_required": True,
        "rematch_disambiguation_requires_article_event_consensus": True,
    }
    for key, value in required.items():
        if decision.get(key) is not value:
            raise RuntimeError(f"scorecard identity decision gate changed: {key}={decision.get(key)!r}")

    rows = read_csv(SOURCE)
    selected = [r for r in rows if (r.get("identity_status") or "").strip() == "high_confidence_fight_candidate"]
    if len(selected) != 578:
        raise RuntimeError(f"selected image count drift: {len(selected)}")

    url_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    fight_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    host_counts = Counter()
    plan = []
    for row in selected:
        url = (row.get("image_url") or "").strip()
        fight_id = (row.get("candidate_fight_id") or "").strip()
        event_id = (row.get("candidate_event_id") or "").strip()
        parsed = urlsplit(url)
        host = parsed.hostname or ""
        host_counts[host] += 1
        if parsed.scheme != "https" or host not in ALLOWED_IMAGE_HOSTS:
            raise RuntimeError(f"selected image host outside audited UFC delivery allowlist: {url}")
        if not fight_id or not event_id:
            raise RuntimeError("high-confidence scorecard row lacks fight/event ID")
        if (row.get("review_status") or "").strip() != "candidate":
            raise RuntimeError("scorecard review status drift")
        url_groups[url].append(row)
        fight_groups[fight_id].append(row)
        plan.append({field: row.get(field) or "" for field in FIELDS if field != "archive_key"} | {"archive_key": archive_key(url)})

    duplicate_urls = {url: group for url, group in url_groups.items() if len(group) > 1}
    if duplicate_urls:
        raise RuntimeError(f"same official image URL selected multiple times: {list(duplicate_urls)[:10]}")
    multi_image_fights = {fight: group for fight, group in fight_groups.items() if len(group) > 1}
    if len(url_groups) != 578 or len(fight_groups) != 575:
        raise RuntimeError(f"scorecard plan cardinality drift urls={len(url_groups)} fights={len(fight_groups)}")

    archive_keys = [r["archive_key"] for r in plan]
    if len(set(archive_keys)) != len(archive_keys):
        raise RuntimeError("archive key collision")
    plan.sort(key=lambda r: (r["candidate_event_date"], r["candidate_fight_id"], r["image_url"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(plan)

    multi_examples = []
    multiplicities = Counter()
    for fight_id, group in sorted(multi_image_fights.items()):
        multiplicities[len(group)] += 1
        multi_examples.append({
            "fight_id": fight_id,
            "event_name": group[0].get("candidate_event_name") or "",
            "event_date": group[0].get("candidate_event_date") or "",
            "image_urls": sorted((r.get("image_url") or "").strip() for r in group),
            "identity_texts": sorted((r.get("identity_text") or "").strip() for r in group),
        })

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_candidate_rows": len(rows),
        "selected_images": len(plan),
        "unique_image_urls": len(url_groups),
        "mapped_fights": len(fight_groups),
        "image_host_counts": dict(sorted(host_counts.items())),
        "allowed_image_hosts": sorted(ALLOWED_IMAGE_HOSTS),
        "fights_with_multiple_selected_images": len(multi_image_fights),
        "multi_image_fight_multiplicity": {str(k): v for k, v in sorted(multiplicities.items())},
        "multi_image_fight_examples": multi_examples,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "binary_images_archived": False,
            "ocr_performed": False,
            "canonical_judge_round_scores_written": False,
            "selected_urls_ready_for_archive": True,
            "official_page_linked_cdn_allowed": True,
            "required_next": "Archive exactly these 578 official-page-linked UFC image URLs with response metadata, byte counts and SHA-256 hashes. Fail closed on HTTP/content/hash errors before any OCR."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_images": len(plan), "unique_urls": len(url_groups), "mapped_fights": len(fight_groups),
        "hosts": dict(host_counts), "multi_image_fights": len(multi_image_fights), "multiplicity": dict(multiplicities),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
