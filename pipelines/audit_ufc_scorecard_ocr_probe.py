#!/usr/bin/env python3
"""Bounded OCR probe over immutable selected UFC scorecard images.

DATA PHASE ONLY. OCR is derived/QA evidence, never canonical by itself.
The probe compares Tesseract PSM 6 and 11 on a deterministic stratified sample and records
confidence/text-recovery metrics without attempting judge-round canonicalization.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/derived/identity/ufc_scorecard_archive_plan_v0.csv"
ARCHIVE = ROOT / "data/raw/ufc_official_scorecard_images/selected_v0"
MANIFEST = ARCHIVE / "manifest.json"
IMAGES = ARCHIVE / "images"
OUT = ROOT / "data/derived/qa/ufc_scorecard_ocr_probe_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_ocr_probe_v0_latest.json"

FIELDS = [
    "archive_key", "candidate_fight_id", "candidate_event_id", "candidate_event_name", "candidate_event_date",
    "matched_fighter_names", "image_signature", "sample_reason",
    "psm6_mean_confidence", "psm6_word_count", "psm6_score_token_count", "psm6_fighter_name_hit_count", "psm6_text",
    "psm11_mean_confidence", "psm11_word_count", "psm11_score_token_count", "psm11_fighter_name_hit_count", "psm11_text",
]
SCORE_TOKEN_RE = re.compile(r"(?<!\d)(?:10|9|8|7)(?!\d)")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def evenly_spaced(items: list[dict[str, str]], n: int) -> list[dict[str, str]]:
    if len(items) <= n:
        return list(items)
    if n <= 1:
        return [items[len(items) // 2]]
    indexes = [round(i * (len(items) - 1) / (n - 1)) for i in range(n)]
    return [items[i] for i in indexes]


def tesseract_tsv(path: Path, psm: int) -> dict[str, Any]:
    proc = subprocess.run(
        ["tesseract", str(path), "stdout", "-l", "eng", "--psm", str(psm), "tsv"],
        capture_output=True, text=True, check=False, timeout=90,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"tesseract failed psm={psm} file={path.name}: {proc.stderr[-500:]}")
    rows = list(csv.DictReader(proc.stdout.splitlines(), delimiter="\t"))
    words: list[str] = []
    confs: list[float] = []
    for row in rows:
        text = (row.get("text") or "").strip()
        if not text:
            continue
        words.append(text)
        try:
            conf = float(row.get("conf") or "-1")
        except ValueError:
            conf = -1
        if conf >= 0:
            confs.append(conf)
    text = " ".join(words)
    return {
        "text": text,
        "word_count": len(words),
        "mean_confidence": round(sum(confs) / len(confs), 3) if confs else 0.0,
        "score_token_count": len(SCORE_TOKEN_RE.findall(text)),
    }


def fighter_hits(text: str, matched_names: str) -> int:
    ocr = norm(text)
    hits = 0
    for name in [x.strip() for x in (matched_names or "").split("|") if x.strip()]:
        n = norm(name)
        if not n:
            continue
        # Full normalized name is strongest; otherwise require the full trailing surname phrase.
        tokens = n.split()
        surname = " ".join(tokens[-2:]) if len(tokens) >= 2 else tokens[-1]
        if n in ocr or surname in ocr:
            hits += 1
    return hits


def main() -> int:
    if subprocess.run(["tesseract", "--version"], capture_output=True).returncode != 0:
        raise RuntimeError("tesseract is not installed")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("image_count") != 578 or manifest.get("mapped_fight_count") != 575:
        raise RuntimeError("immutable scorecard archive cardinality drift")
    rules = manifest.get("rules") or {}
    if rules.get("ocr_performed") is not False or rules.get("canonical_judge_round_scores_written") is not False:
        raise RuntimeError("raw archive semantic boundary changed")

    plan = read_csv(PLAN)
    by_key = {r["archive_key"]: r for r in plan}
    image_meta = {r["archive_key"]: r for r in manifest.get("images") or []}
    if set(by_key) != set(image_meta) or len(by_key) != 578:
        raise RuntimeError("archive plan/manifest key mismatch")

    enriched = []
    for row in plan:
        item = dict(row)
        item["image_signature"] = str(image_meta[row["archive_key"]].get("image_signature") or "")
        enriched.append(item)
    enriched.sort(key=lambda r: (r.get("candidate_event_date") or "", r.get("candidate_fight_id") or "", r["archive_key"]))

    sample_by_key: dict[str, tuple[dict[str, str], set[str]]] = {}
    for sig, n in (("jpeg", 24), ("png", 24)):
        group = [r for r in enriched if r["image_signature"] == sig]
        for row in evenly_spaced(group, n):
            sample_by_key.setdefault(row["archive_key"], (row, set()))[1].add(f"stratified_{sig}")

    fight_counts = Counter(r["candidate_fight_id"] for r in enriched)
    multi_fights = {fight for fight, count in fight_counts.items() if count > 1}
    if len(multi_fights) != 3:
        raise RuntimeError(f"expected three multi-image fights, got {len(multi_fights)}")
    for row in enriched:
        if row["candidate_fight_id"] in multi_fights:
            sample_by_key.setdefault(row["archive_key"], (row, set()))[1].add("multi_image_fight")

    sample = sorted(sample_by_key.values(), key=lambda x: x[0]["archive_key"])
    if not 48 <= len(sample) <= 54:
        raise RuntimeError(f"unexpected OCR probe sample size: {len(sample)}")

    out_rows = []
    psm_summary: dict[int, Counter] = {6: Counter(), 11: Counter()}
    for row, reasons in sample:
        path = IMAGES / row["archive_key"]
        if not path.is_file():
            raise RuntimeError(f"missing archived image: {path.name}")
        results = {psm: tesseract_tsv(path, psm) for psm in (6, 11)}
        record: dict[str, Any] = {
            "archive_key": row["archive_key"],
            "candidate_fight_id": row.get("candidate_fight_id") or "",
            "candidate_event_id": row.get("candidate_event_id") or "",
            "candidate_event_name": row.get("candidate_event_name") or "",
            "candidate_event_date": row.get("candidate_event_date") or "",
            "matched_fighter_names": row.get("matched_fighter_names") or "",
            "image_signature": row["image_signature"],
            "sample_reason": "|".join(sorted(reasons)),
        }
        for psm in (6, 11):
            result = results[psm]
            hits = fighter_hits(result["text"], row.get("matched_fighter_names") or "")
            record[f"psm{psm}_mean_confidence"] = result["mean_confidence"]
            record[f"psm{psm}_word_count"] = result["word_count"]
            record[f"psm{psm}_score_token_count"] = result["score_token_count"]
            record[f"psm{psm}_fighter_name_hit_count"] = hits
            record[f"psm{psm}_text"] = result["text"]
            psm_summary[psm]["images"] += 1
            psm_summary[psm]["word_count"] += result["word_count"]
            psm_summary[psm]["score_tokens"] += result["score_token_count"]
            psm_summary[psm][f"fighter_hits_{hits}"] += 1
            if result["word_count"] >= 10:
                psm_summary[psm]["images_with_10plus_words"] += 1
            if result["score_token_count"] >= 6:
                psm_summary[psm]["images_with_6plus_score_tokens"] += 1
        out_rows.append(record)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(out_rows)

    summary = {}
    for psm in (6, 11):
        counter = psm_summary[psm]
        summary[str(psm)] = {
            "images": counter["images"],
            "total_words": counter["word_count"],
            "total_score_tokens_7_to_10": counter["score_tokens"],
            "images_with_10plus_words": counter["images_with_10plus_words"],
            "images_with_6plus_score_tokens": counter["images_with_6plus_score_tokens"],
            "fighter_name_hit_distribution": {
                str(h): counter[f"fighter_hits_{h}"] for h in range(3) if counter[f"fighter_hits_{h}"]
            },
            "mean_of_image_mean_confidence": round(
                sum(float(r[f"psm{psm}_mean_confidence"]) for r in out_rows) / len(out_rows), 3
            ),
        }

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "archive_image_count": 578,
        "probe_sample_images": len(out_rows),
        "sample_signature_counts": dict(Counter(r["image_signature"] for r in out_rows)),
        "sample_multi_image_fight_objects": sum("multi_image_fight" in r["sample_reason"] for r in out_rows),
        "psm_summary": summary,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "ocr_is_derived_qa_only": True,
            "canonical_judge_round_scores_written": False,
            "judge_identity_resolved": False,
            "round_score_structure_resolved": False,
            "required_next": "Review probe recovery by PSM and image era/format. Choose a bounded OCR configuration for the full 578-image derived layer only if fighter/score text recovery is adequate; canonicalization still requires independent judge/round/fighter semantics."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"sample": len(out_rows), "psm_summary": summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
