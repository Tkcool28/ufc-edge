#!/usr/bin/env python3
"""Build full derived OCR text layer for immutable selected UFC scorecard images.

DATA PHASE ONLY. PSM 11 is selected by the bounded probe. This output is QA/derived text,
not canonical judge-round scores. Every OCR row is tied to the archived image SHA-256.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/derived/identity/ufc_scorecard_archive_plan_v0.csv"
ARCHIVE = ROOT / "data/raw/ufc_official_scorecard_images/selected_v0"
MANIFEST = ARCHIVE / "manifest.json"
IMAGES = ARCHIVE / "images"
PROBE = ROOT / "provenance/audits/ufc_scorecard_ocr_probe_v0_latest.json"
OUT = ROOT / "data/derived/qa/ufc_scorecard_ocr_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_ocr_v0_latest.json"

FIELDS = [
    "archive_key", "image_sha256", "candidate_fight_id", "candidate_event_id", "candidate_event_name",
    "candidate_event_date", "matched_fighter_names", "image_signature", "psm", "word_count",
    "score_token_count", "fighter_name_hit_count", "ocr_text",
]
SCORE_TOKEN_RE = re.compile(r"(?<!\d)(?:10|9|8|7)(?!\d)")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def fighter_hits(text: str, matched_names: str) -> int:
    ocr = norm(text)
    hits = 0
    for name in [x.strip() for x in (matched_names or "").split("|") if x.strip()]:
        n = norm(name)
        if not n:
            continue
        tokens = n.split()
        surname = " ".join(tokens[-2:]) if len(tokens) >= 2 else tokens[-1]
        if n in ocr or surname in ocr:
            hits += 1
    return hits


def ocr_text(path: Path) -> str:
    proc = subprocess.run(
        ["tesseract", str(path), "stdout", "-l", "eng", "--psm", "11"],
        capture_output=True, text=True, check=False, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"tesseract failed file={path.name}: {proc.stderr[-500:]}")
    # Preserve line boundaries as an explicit separator without carrying platform newlines into CSV.
    lines = [" ".join(line.split()) for line in proc.stdout.splitlines() if line.strip()]
    return " | ".join(lines)


def main() -> int:
    if subprocess.run(["tesseract", "--version"], capture_output=True).returncode != 0:
        raise RuntimeError("tesseract is not installed")
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    p11 = (probe.get("psm_summary") or {}).get("11") or {}
    if probe.get("probe_sample_images") != 53:
        raise RuntimeError("OCR probe sample cardinality drift")
    if p11.get("fighter_name_hit_distribution", {}).get("2", 0) < 50:
        raise RuntimeError("PSM 11 fighter-name recovery no longer supports full derived OCR")
    if p11.get("images_with_6plus_score_tokens", 0) < 35:
        raise RuntimeError("PSM 11 score-token recovery no longer supports full derived OCR")
    decision = probe.get("decision") or {}
    if decision.get("ocr_is_derived_qa_only") is not True or decision.get("canonical_judge_round_scores_written") is not False:
        raise RuntimeError("OCR probe semantic boundary changed")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("image_count") != 578 or manifest.get("mapped_fight_count") != 575:
        raise RuntimeError("scorecard archive cardinality drift")
    image_meta = {str(x.get("archive_key")): x for x in manifest.get("images") or []}
    plan = read_csv(PLAN)
    if len(plan) != 578 or len(image_meta) != 578:
        raise RuntimeError("scorecard plan/archive cardinality mismatch")

    rows: list[dict[str, Any]] = []
    signature_counts = Counter()
    hit_counts = Counter()
    score_bucket_counts = Counter()
    year_stats: dict[str, Counter] = defaultdict(Counter)
    for idx, item in enumerate(plan, start=1):
        key = (item.get("archive_key") or "").strip()
        meta = image_meta.get(key)
        if not meta:
            raise RuntimeError(f"archive metadata missing for {key}")
        path = IMAGES / key
        if not path.is_file():
            raise RuntimeError(f"archived image missing: {key}")
        text = ocr_text(path)
        words = text.replace("|", " ").split()
        score_tokens = len(SCORE_TOKEN_RE.findall(text))
        hits = fighter_hits(text, item.get("matched_fighter_names") or "")
        sig = str(meta.get("image_signature") or "")
        year = (item.get("candidate_event_date") or "")[:4] or "unknown"
        signature_counts[sig] += 1
        hit_counts[hits] += 1
        score_bucket_counts["0"] += score_tokens == 0
        score_bucket_counts["1_5"] += 1 <= score_tokens <= 5
        score_bucket_counts["6_11"] += 6 <= score_tokens <= 11
        score_bucket_counts["12_plus"] += score_tokens >= 12
        year_stats[year]["images"] += 1
        year_stats[year][f"fighter_hits_{hits}"] += 1
        year_stats[year]["score_tokens"] += score_tokens
        year_stats[year]["words"] += len(words)
        rows.append({
            "archive_key": key,
            "image_sha256": str(meta.get("sha256") or ""),
            "candidate_fight_id": item.get("candidate_fight_id") or "",
            "candidate_event_id": item.get("candidate_event_id") or "",
            "candidate_event_name": item.get("candidate_event_name") or "",
            "candidate_event_date": item.get("candidate_event_date") or "",
            "matched_fighter_names": item.get("matched_fighter_names") or "",
            "image_signature": sig,
            "psm": 11,
            "word_count": len(words),
            "score_token_count": score_tokens,
            "fighter_name_hit_count": hits,
            "ocr_text": text,
        })
        if idx % 50 == 0:
            print(f"OCR_PROGRESS {idx}/578", flush=True)

    if len(rows) != 578 or len({r["archive_key"] for r in rows}) != 578:
        raise RuntimeError("full OCR row/key cardinality failure")
    if any(len(str(r["image_sha256"])) != 64 for r in rows):
        raise RuntimeError("OCR row lacks archived SHA-256")
    if any(int(r["word_count"]) < 1 for r in rows):
        raise RuntimeError("one or more scorecard images produced empty OCR")

    rows.sort(key=lambda r: (str(r["candidate_event_date"]), str(r["candidate_fight_id"]), str(r["archive_key"])))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(rows)

    by_year = {}
    for year, c in sorted(year_stats.items()):
        images = c["images"]
        by_year[year] = {
            "images": images,
            "two_fighter_hits": c["fighter_hits_2"],
            "one_fighter_hit": c["fighter_hits_1"],
            "zero_fighter_hits": c["fighter_hits_0"],
            "avg_words": round(c["words"] / images, 2),
            "avg_score_tokens": round(c["score_tokens"] / images, 2),
        }

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ocr_engine": "tesseract",
        "psm": 11,
        "archive_image_count": 578,
        "ocr_rows": len(rows),
        "mapped_fights": len({r["candidate_fight_id"] for r in rows}),
        "image_signature_counts": dict(sorted(signature_counts.items())),
        "fighter_name_hit_distribution": {str(k): v for k, v in sorted(hit_counts.items())},
        "score_token_bucket_counts": dict(score_bucket_counts),
        "images_with_10plus_words": sum(int(r["word_count"]) >= 10 for r in rows),
        "images_with_6plus_score_tokens": sum(int(r["score_token_count"]) >= 6 for r in rows),
        "year_recovery": by_year,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "ocr_complete_for_selected_archive": True,
            "ocr_is_derived_qa_only": True,
            "canonical_judge_round_scores_written": False,
            "judge_identity_resolved": False,
            "round_score_structure_resolved": False,
            "fighter_pair_identity_from_ocr_used": False,
            "required_next": "Audit OCR text structure for judge-name blocks, fighter column ordering, round headers and per-round score cells. Do not canonicalize any OCR score until all four semantics are jointly resolved for that image/template."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ocr_rows": len(rows), "mapped_fights": payload["mapped_fights"],
        "fighter_hits": dict(hit_counts), "score_buckets": dict(score_bucket_counts),
        "images_6plus_scores": payload["images_with_6plus_score_tokens"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
