#!/usr/bin/env python3
"""Archive the identity-filtered official UFC scorecard image bytes with hashes.

DATA PHASE ONLY. No OCR is performed here.

The selected_v0 raw directory is immutable desired state: a rerun may verify existing bytes,
but any URL/hash/content mismatch fails closed rather than rewriting accepted raw evidence.
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/derived/identity/ufc_scorecard_archive_plan_v0.csv"
PLAN_AUDIT = ROOT / "provenance/audits/ufc_scorecard_archive_plan_v0_latest.json"
RAW = ROOT / "data/raw/ufc_official_scorecard_images/selected_v0"
IMAGES = RAW / "images"
MANIFEST = RAW / "manifest.json"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_selected_archive_latest.json"
USER_AGENT = "Mozilla/5.0 (compatible; UFC-Edge-DataPhase/1.0; archival)"
MAX_BYTES = 12 * 1024 * 1024


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def image_signature(data: bytes) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def fetch_one(row: dict[str, str]) -> dict[str, object]:
    url = (row.get("image_url") or "").strip()
    key = (row.get("archive_key") or "").strip()
    if not url or not key:
        raise RuntimeError("archive plan row lacks image_url/archive_key")
    path = IMAGES / key

    if path.exists():
        data = path.read_bytes()
        sig = image_signature(data)
        if sig == "unknown" or not data:
            raise RuntimeError(f"existing archive object is not a recognized image: {key}")
        return {
            "archive_key": key,
            "source_url": url,
            "final_url": url,
            "http_status": 200,
            "content_type": f"image/{'jpeg' if sig == 'jpeg' else sig}",
            "image_signature": sig,
            "bytes": len(data),
            "sha256": sha256_bytes(data),
            "reused_existing": True,
            "candidate_fight_id": row.get("candidate_fight_id") or "",
            "candidate_event_id": row.get("candidate_event_id") or "",
            "article_url": row.get("article_url") or "",
        }

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*,*/*;q=0.8"})
            with urllib.request.urlopen(req, timeout=30) as response:
                status = int(getattr(response, "status", 200))
                final_url = response.geturl()
                content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                data = response.read(MAX_BYTES + 1)
            if status != 200:
                raise RuntimeError(f"HTTP {status}")
            if len(data) > MAX_BYTES:
                raise RuntimeError(f"object exceeds {MAX_BYTES} bytes")
            if len(data) < 500:
                raise RuntimeError(f"implausibly small image: {len(data)} bytes")
            sig = image_signature(data)
            if sig == "unknown":
                raise RuntimeError(f"unrecognized image signature content_type={content_type!r}")
            if content_type and not content_type.startswith("image/"):
                raise RuntimeError(f"non-image content type {content_type!r}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return {
                "archive_key": key,
                "source_url": url,
                "final_url": final_url,
                "http_status": status,
                "content_type": content_type,
                "image_signature": sig,
                "bytes": len(data),
                "sha256": sha256_bytes(data),
                "reused_existing": False,
                "candidate_fight_id": row.get("candidate_fight_id") or "",
                "candidate_event_id": row.get("candidate_event_id") or "",
                "article_url": row.get("article_url") or "",
            }
        except Exception as exc:  # bounded retry; final failure is fatal
            last_error = exc
            if attempt < 3:
                time.sleep(attempt * 1.5)
    raise RuntimeError(f"failed to archive {url}: {last_error}")


def main() -> int:
    plan_audit = json.loads(PLAN_AUDIT.read_text(encoding="utf-8"))
    decision = plan_audit.get("decision") or {}
    if decision.get("selected_urls_ready_for_archive") is not True:
        raise RuntimeError("archive plan is not promoted for binary acquisition")
    if decision.get("ocr_performed") is not False or decision.get("canonical_judge_round_scores_written") is not False:
        raise RuntimeError("archive plan semantic boundary changed")
    if plan_audit.get("selected_images") != 578 or plan_audit.get("unique_image_urls") != 578 or plan_audit.get("mapped_fights") != 575:
        raise RuntimeError("archive plan cardinality changed")

    rows = read_csv(PLAN)
    if len(rows) != 578:
        raise RuntimeError(f"archive plan rows changed: {len(rows)}")
    if len({r.get("archive_key") for r in rows}) != 578 or len({r.get("image_url") for r in rows}) != 578:
        raise RuntimeError("archive plan keys/URLs are not unique")

    prior = None
    if MANIFEST.exists():
        prior = json.loads(MANIFEST.read_text(encoding="utf-8"))
        prior_map = {x["archive_key"]: x for x in prior.get("images") or []}
        if len(prior_map) != 578:
            raise RuntimeError("existing selected_v0 manifest is not the expected immutable 578-object set")
        for row in rows:
            key = row["archive_key"]
            old = prior_map.get(key)
            if not old or old.get("source_url") != row["image_url"]:
                raise RuntimeError(f"immutable archive URL mapping mismatch: {key}")

    IMAGES.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fetch_one, row): row for row in rows}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                errors.append(str(exc))
    if errors:
        raise RuntimeError(f"scorecard archive failures={len(errors)} examples={errors[:10]}")
    if len(results) != 578:
        raise RuntimeError(f"archived result count drift: {len(results)}")

    results.sort(key=lambda r: str(r["archive_key"]))
    for result in results:
        path = IMAGES / str(result["archive_key"])
        if not path.is_file():
            raise RuntimeError(f"missing archived object: {path.name}")
        if path.stat().st_size != int(result["bytes"]) or sha256_file(path) != result["sha256"]:
            raise RuntimeError(f"post-write hash/size mismatch: {path.name}")

    if prior:
        prior_map = {x["archive_key"]: x for x in prior.get("images") or []}
        for result in results:
            old = prior_map[str(result["archive_key"])]
            if old.get("sha256") != result["sha256"] or int(old.get("bytes", -1)) != int(result["bytes"]):
                raise RuntimeError(f"immutable archived bytes changed upstream: {result['archive_key']}")

    type_counts = Counter(str(r["image_signature"]) for r in results)
    content_type_counts = Counter(str(r["content_type"]) for r in results)
    final_host_counts = Counter(urlsplit(str(r["final_url"])).hostname or "" for r in results)
    total_bytes = sum(int(r["bytes"]) for r in results)
    manifest = {
        "schema_version": 1,
        "archive_id": "selected_v0",
        "source": "ufc_official_content",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "selection_plan": str(PLAN.relative_to(ROOT)),
        "selection_plan_audit": str(PLAN_AUDIT.relative_to(ROOT)),
        "image_count": len(results),
        "mapped_fight_count": 575,
        "total_bytes": total_bytes,
        "image_signature_counts": dict(sorted(type_counts.items())),
        "content_type_counts": dict(sorted(content_type_counts.items())),
        "final_host_counts": dict(sorted(final_host_counts.items())),
        "images": results,
        "rules": {
            "raw_bytes_immutable_after_acceptance": True,
            "all_objects_sha256_hashed": True,
            "ocr_performed": False,
            "canonical_judge_round_scores_written": False,
            "only_identity_filtered_selected_urls_archived": True,
        },
    }
    RAW.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit = {
        "schema_version": 1,
        "archive_id": "selected_v0",
        "image_count": len(results),
        "mapped_fight_count": 575,
        "total_bytes": total_bytes,
        "image_signature_counts": dict(sorted(type_counts.items())),
        "final_host_counts": dict(sorted(final_host_counts.items())),
        "reused_existing_objects": sum(bool(r["reused_existing"]) for r in results),
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "decision": {
            "binary_images_archived": True,
            "all_selected_objects_hashed": True,
            "ocr_performed": False,
            "canonical_judge_round_scores_written": False,
            "required_next": "Run OCR only as a derived candidate layer against these immutable hashed images, then independently validate judge/fighter/round score semantics before any canonical score rows."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "images": len(results), "total_bytes": total_bytes, "signatures": dict(type_counts),
        "final_hosts": dict(final_host_counts), "reused": audit["reused_existing_objects"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
