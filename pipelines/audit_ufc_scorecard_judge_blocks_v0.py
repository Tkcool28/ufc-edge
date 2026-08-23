#!/usr/bin/env python3
"""Audit per-block judge-name OCR on official UFC scorecard images.

DATA PHASE ONLY. Uses the spatially located judge-name band immediately above the
POINT DEDUCTIONS section, then runs two OCR page-segmentation modes independently on
each of the three judge blocks. No canonical official or score rows are emitted.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SPATIAL = ROOT / "data/derived/qa/ufc_scorecard_spatial_structure_v0.csv"
ARCHIVE_DIR = ROOT / "data/raw/ufc_official_scorecard_images/selected_v0/images"
OUT = ROOT / "data/derived/qa/ufc_scorecard_judge_blocks_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_judge_blocks_v0_latest.json"

BLOCK_BOUNDS = [(0.02, 0.34), (0.34, 0.66), (0.66, 0.98)]
Y_HALF = 0.035
UPSCALE = 5
BANNED = {"point", "deductions", "notes", "result", "round", "total", "score", "judge"}

FIELDS = [
    "archive_key", "fight_id", "event_date", "judge_band_y", "whole_line_candidate",
    "judge_block", "psm7_text", "psm11_text", "agreement_ratio", "candidate_judge_name",
    "block_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(text: str) -> str:
    s = (text or "").replace("’", "'").replace("‘", "'")
    s = re.sub(r"[^A-Za-z' .-]+", " ", s)
    return " ".join(s.upper().split())


def alpha_words(text: str) -> list[str]:
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'.-]*", text or "") if w.lower().strip("'.-") not in BANNED]


def find_judge_line(lower_lines: list[dict]) -> dict | None:
    point_idx = None
    for i, line in enumerate(lower_lines):
        text = str(line.get("text") or "").upper()
        if "DEDUCTION" in text or ("POINT" in text and "NOTES" in text):
            point_idx = i; break
    if point_idx is None or point_idx == 0:
        return None
    candidates = []
    for line in lower_lines[:point_idx]:
        text = str(line.get("text") or "").strip()
        if len(alpha_words(text)) >= 4 and float(line.get("x_max", 0)) - float(line.get("x_min", 0)) >= 0.45:
            candidates.append(line)
    return candidates[-1] if candidates else None


def crop_band(image: Image.Image, x0: float, x1: float, y: float) -> Image.Image:
    w, h = image.size
    left = max(0, int(x0 * w)); right = min(w, int(x1 * w))
    top = max(0, int((y - Y_HALF) * h)); bottom = min(h, int((y + Y_HALF) * h))
    crop = image.crop((left, top, right, bottom)).convert("L")
    crop = ImageOps.autocontrast(crop)
    crop = ImageEnhance.Contrast(crop).enhance(1.8)
    crop = crop.resize((crop.width * UPSCALE, crop.height * UPSCALE), Image.Resampling.LANCZOS)
    return crop


def ocr(crop: Image.Image, psm: int) -> str:
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        crop.save(tmp.name, format="PNG")
        proc = subprocess.run(["tesseract", tmp.name, "stdout", "--psm", str(psm), "-l", "eng"], capture_output=True, text=True, check=False)
    return norm(proc.stdout)


def clean_name(text: str) -> str:
    words = alpha_words(text)
    # Judge names on these cards are normally 2-4 words; refuse labels/noise rather than trimming by guess.
    if not (2 <= len(words) <= 4):
        return ""
    return " ".join(w.upper() for w in words)


def main() -> int:
    spatial = read_csv(SPATIAL)
    if len(spatial) != 48:
        raise RuntimeError(f"spatial sample drift: {len(spatial)}")

    rows_out = []
    card_status = Counter()
    block_status = Counter()
    cards_with_band = 0
    cards_three_resolved = 0

    for row in spatial:
        lower = json.loads(row["lower_grid_lines_json"])
        line = find_judge_line(lower)
        if not line:
            card_status["judge_band_missing"] += 1
            continue
        cards_with_band += 1
        y = float(line["y"])
        path = ARCHIVE_DIR / row["archive_key"]
        if not path.exists():
            raise RuntimeError(f"archived image missing: {path}")
        image = Image.open(path)
        resolved = 0
        for block, (x0, x1) in enumerate(BLOCK_BOUNDS, start=1):
            crop = crop_band(image, x0, x1, y)
            t7 = ocr(crop, 7)
            t11 = ocr(crop, 11)
            n7 = clean_name(t7); n11 = clean_name(t11)
            ratio = SequenceMatcher(None, n7, n11).ratio() if n7 and n11 else 0.0
            candidate = ""
            status = "unresolved"
            if n7 and n11 and ratio >= 0.72:
                # Prefer the cleaner/shorter rendering if one pass picked up punctuation/noise.
                candidate = n7 if len(n7) <= len(n11) else n11
                status = "dual_ocr_consensus"
                resolved += 1
            elif n7 and not n11:
                status = "psm7_only"
            elif n11 and not n7:
                status = "psm11_only"
            elif n7 and n11:
                status = "ocr_disagreement"
            block_status[status] += 1
            rows_out.append({
                "archive_key": row["archive_key"],
                "fight_id": row["candidate_fight_id"],
                "event_date": row["candidate_event_date"],
                "judge_band_y": round(y, 5),
                "whole_line_candidate": str(line.get("text") or ""),
                "judge_block": block,
                "psm7_text": t7,
                "psm11_text": t11,
                "agreement_ratio": round(ratio, 5),
                "candidate_judge_name": candidate,
                "block_status": status,
            })
        if resolved == 3:
            cards_three_resolved += 1; card_status["three_judges_dual_ocr_consensus"] += 1
        else:
            card_status["partial_or_unresolved_judges"] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(rows_out)

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sample_images": len(spatial),
        "cards_with_spatial_judge_band": cards_with_band,
        "cards_with_three_dual_ocr_consensus_judges": cards_three_resolved,
        "card_status_counts": dict(card_status),
        "block_status_counts": dict(block_status),
        "judge_block_bounds": BLOCK_BOUNDS,
        "judge_band_half_height": Y_HALF,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False,
            "judge_names_are_ocr_candidates_not_official_ids": True,
            "per_block_dual_ocr_consensus_required": True,
            "three_judge_consensus_subset_can_advance": cards_three_resolved > 0,
            "required_next": "Intersect three-judge consensus cards with strict fighter-column orientation and fully recovered score-cell cards. Validate paired round scores and decision totals before canonicalization.",
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cards_with_band": cards_with_band, "three_resolved": cards_three_resolved, "block_status": dict(block_status)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
