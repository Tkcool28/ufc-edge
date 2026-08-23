#!/usr/bin/env python3
"""Audit targeted OCR recovery from learned UFC scorecard grid cells.

DATA PHASE ONLY. This does not emit canonical judge-round scores. It learns round-row
centers from the already-audited spatial sample, uses the learned six score-column
centers, crops each expected score cell from immutable archived official images, and
runs digits-only OCR. Results are QA evidence for whether a strict parser is viable.
"""
from __future__ import annotations

import csv
import io
import json
import re
import statistics
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SPATIAL = ROOT / "data/derived/qa/ufc_scorecard_spatial_structure_v0.csv"
GEOMETRY_AUDIT = ROOT / "provenance/audits/ufc_scorecard_template_geometry_v0_latest.json"
ROUND_ELIG = ROOT / "data/derived/qa/ufc_scorecard_round_eligibility_v0.csv"
ARCHIVE_DIR = ROOT / "data/raw/ufc_official_scorecard_images/selected_v0"
OUT = ROOT / "data/derived/qa/ufc_scorecard_targeted_cell_ocr_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_targeted_cell_ocr_v0_latest.json"

X_HALF = 0.032
Y_HALF = 0.024
UPSCALE = 7

FIELDS = [
    "archive_key", "fight_id", "event_date", "expected_scored_rounds", "round_row",
    "judge_block", "fighter_column_in_block", "column_index", "x_center", "y_center",
    "ocr_text", "parsed_points", "contract_valid_0_10", "typical_7_10",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def cluster_y(tokens: list[dict], tol: float = 0.022) -> list[list[dict]]:
    groups: list[list[dict]] = []
    for token in sorted(tokens, key=lambda t: (float(t["y"]), float(t["x"]))):
        y = float(token["y"])
        if not groups:
            groups.append([token]); continue
        center = sum(float(x["y"]) for x in groups[-1]) / len(groups[-1])
        if abs(y - center) <= tol:
            groups[-1].append(token)
        else:
            groups.append([token])
    return groups


def parse_rounds(text: str) -> list[int]:
    raw = (text or "").strip()
    if not raw:
        return []
    vals = [int(x) for x in raw.split(",") if x.strip()]
    if vals != list(range(1, len(vals) + 1)):
        raise RuntimeError(f"non-contiguous expected rounds: {text!r}")
    return vals


def learn_y_centers(spatial: list[dict[str, str]], eligibility: dict[str, dict[str, str]]) -> list[float]:
    by_round: dict[int, list[float]] = defaultdict(list)
    for row in spatial:
        elig = eligibility.get(row["candidate_fight_id"])
        if not elig or elig["eligibility_status"] != "eligible":
            continue
        rounds = parse_rounds(elig["expected_scored_rounds"])
        if not rounds:
            continue
        tokens = [t for t in json.loads(row["score_tokens_json"]) if 0.35 <= float(t["y"]) <= 0.67]
        groups = cluster_y(tokens)
        # Only use cards where observed row count equals the conservative expected count.
        # Missing cells within those rows are allowed because this audit exists to measure that recall.
        if len(groups) != len(rounds):
            continue
        for idx, group in enumerate(groups):
            by_round[idx + 1].append(statistics.median(float(t["y"]) for t in group))
    centers = []
    for rnd in range(1, 6):
        vals = by_round.get(rnd) or []
        if not vals:
            raise RuntimeError(f"cannot learn score row center for round {rnd}")
        centers.append(statistics.median(vals))
    if any(b <= a for a, b in zip(centers, centers[1:])):
        raise RuntimeError(f"non-increasing learned y centers: {centers}")
    return centers


def crop_cell(image: Image.Image, x: float, y: float) -> Image.Image:
    w, h = image.size
    left = max(0, int((x - X_HALF) * w)); right = min(w, int((x + X_HALF) * w))
    top = max(0, int((y - Y_HALF) * h)); bottom = min(h, int((y + Y_HALF) * h))
    crop = image.crop((left, top, right, bottom)).convert("L")
    crop = ImageOps.autocontrast(crop)
    crop = ImageEnhance.Contrast(crop).enhance(2.2)
    crop = crop.resize((crop.width * UPSCALE, crop.height * UPSCALE), Image.Resampling.LANCZOS)
    return crop


def ocr_digit(crop: Image.Image) -> tuple[str, str]:
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
        crop.save(tmp.name, format="PNG")
        proc = subprocess.run(
            ["tesseract", tmp.name, "stdout", "--psm", "10", "-l", "eng",
             "-c", "tessedit_char_whitelist=0123456789"],
            capture_output=True, text=True, check=False,
        )
    text = re.sub(r"\s+", "", proc.stdout or "")
    m = re.search(r"(?:10|[0-9])", text)
    return text, (m.group(0) if m else "")


def main() -> int:
    spatial = read_csv(SPATIAL)
    eligibility = {r["fight_id"]: r for r in read_csv(ROUND_ELIG)}
    geom = json.loads(GEOMETRY_AUDIT.read_text(encoding="utf-8"))
    if len(spatial) != 48 or len(eligibility) != 575:
        raise RuntimeError(f"input cardinality drift spatial={len(spatial)} eligibility={len(eligibility)}")
    centers_x = [float(x) for x in geom.get("learned_score_column_centers") or []]
    if len(centers_x) != 6:
        raise RuntimeError(f"expected six learned x centers, got {centers_x}")
    if (geom.get("decision") or {}).get("six_score_columns_repeatably_observed") is not True:
        raise RuntimeError("six-column geometry was not accepted")
    centers_y = learn_y_centers(spatial, eligibility)

    rows_out = []
    card_stats = []
    for row in spatial:
        elig = eligibility[row["candidate_fight_id"]]
        if elig["eligibility_status"] != "eligible":
            continue
        rounds = parse_rounds(elig["expected_scored_rounds"])
        if not rounds:
            continue
        image_path = ARCHIVE_DIR / row["archive_key"]
        if not image_path.exists():
            raise RuntimeError(f"archived image missing: {image_path}")
        image = Image.open(image_path)
        parsed = 0; typical = 0; values = []
        for rnd in rounds:
            y = centers_y[rnd - 1]
            for col, x in enumerate(centers_x):
                text, value = ocr_digit(crop_cell(image, x, y))
                intval = int(value) if value else None
                valid = intval is not None and 0 <= intval <= 10
                usual = intval is not None and 7 <= intval <= 10
                parsed += int(valid); typical += int(usual)
                if intval is not None:
                    values.append(intval)
                rows_out.append({
                    "archive_key": row["archive_key"],
                    "fight_id": row["candidate_fight_id"],
                    "event_date": row["candidate_event_date"],
                    "expected_scored_rounds": ",".join(str(x) for x in rounds),
                    "round_row": rnd,
                    "judge_block": col // 2 + 1,
                    "fighter_column_in_block": col % 2 + 1,
                    "column_index": col,
                    "x_center": round(x, 5),
                    "y_center": round(y, 5),
                    "ocr_text": text,
                    "parsed_points": "" if intval is None else intval,
                    "contract_valid_0_10": str(valid).lower(),
                    "typical_7_10": str(usual).lower(),
                })
        expected_cells = 6 * len(rounds)
        card_stats.append({"archive_key": row["archive_key"], "expected": expected_cells, "parsed": parsed, "typical": typical})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(rows_out)

    expected_total = sum(x["expected"] for x in card_stats)
    parsed_total = sum(x["parsed"] for x in card_stats)
    typical_total = sum(x["typical"] for x in card_stats)
    complete_cards = sum(x["parsed"] == x["expected"] for x in card_stats)
    almost_cards = sum(x["parsed"] >= max(0, x["expected"] - 1) for x in card_stats)
    by_expected = Counter()
    by_complete = Counter()
    for x in card_stats:
        by_expected[str(x["expected"] // 6)] += 1
        if x["parsed"] == x["expected"]:
            by_complete[str(x["expected"] // 6)] += 1

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sample_images": len(spatial),
        "scored_sample_images": len(card_stats),
        "learned_score_column_centers": [round(x, 5) for x in centers_x],
        "learned_score_row_centers": [round(y, 5) for y in centers_y],
        "crop_half_width": X_HALF,
        "crop_half_height": Y_HALF,
        "upscale": UPSCALE,
        "expected_score_cells": expected_total,
        "contract_valid_cells_recovered": parsed_total,
        "typical_7_10_cells_recovered": typical_total,
        "contract_valid_cell_recovery_fraction": round(parsed_total / expected_total, 6) if expected_total else 0,
        "complete_card_count": complete_cards,
        "within_one_missing_cell_card_count": almost_cards,
        "scored_card_count_by_rounds": dict(sorted(by_expected.items())),
        "complete_card_count_by_rounds": dict(sorted(by_complete.items())),
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False,
            "targeted_cell_ocr_is_qa_only": True,
            "whole_page_missing_tokens_are_not_treated_as_empty_cells": True,
            "targeted_cell_recovery_measured": True,
            "fighter_column_identity_promoted": False,
            "judge_name_identity_promoted": False,
            "required_next": "Use only fully recovered targeted-cell cards for fighter-column/judge-line semantic validation. Do not infer missing cells or canonicalize partially recovered grids.",
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"scored_cards": len(card_stats), "expected_cells": expected_total, "recovered": parsed_total, "complete_cards": complete_cards, "row_centers": payload["learned_score_row_centers"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
