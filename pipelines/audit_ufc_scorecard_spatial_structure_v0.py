#!/usr/bin/env python3
"""Audit spatial scorecard structure from immutable official UFC images.

DATA PHASE ONLY. This is a template/geometry audit, not a score parser. It records OCR
bounding boxes for labels, plausible 7..10 score tokens, fighter anchors, and lower-grid
text lines on a deterministic year-stratified sample. Canonical fight metadata is included
only to test actual-round plausibility; no OCR token becomes a canonical score here.
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
MANIFEST = ROOT / "data/raw/ufc_official_scorecard_images/selected_v0/manifest.json"
IMAGES = ROOT / "data/raw/ufc_official_scorecard_images/selected_v0/images"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
OUT = ROOT / "data/derived/qa/ufc_scorecard_spatial_structure_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_spatial_structure_v0_latest.json"

FIELDS = [
    "archive_key", "candidate_fight_id", "candidate_event_name", "candidate_event_date", "image_signature",
    "canonical_result", "canonical_finish_round", "canonical_scheduled_rounds", "sample_reason",
    "page_width", "page_height", "word_count", "score_token_count", "score_y_cluster_count",
    "score_tokens_json", "label_tokens_json", "fighter_anchor_tokens_json", "lower_grid_lines_json",
]
SCORE_RE = re.compile(r"^(?:10|9|8|7)$")
LABEL_WORDS = {"round", "score", "total", "judge", "points", "point", "deductions", "notes", "result", "referee"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def evenly_spaced(items: list[dict[str, str]], n: int) -> list[dict[str, str]]:
    if len(items) <= n:
        return list(items)
    if n == 1:
        return [items[len(items) // 2]]
    idxs = [round(i * (len(items) - 1) / (n - 1)) for i in range(n)]
    return [items[i] for i in idxs]


def run_tsv(path: Path) -> tuple[int, int, list[dict[str, Any]]]:
    proc = subprocess.run(
        ["tesseract", str(path), "stdout", "-l", "eng", "--psm", "11", "tsv"],
        capture_output=True, text=True, check=False, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"tesseract failed {path.name}: {proc.stderr[-500:]}")
    reader = csv.DictReader(proc.stdout.splitlines(), delimiter="\t")
    rows = []
    page_width = page_height = 0
    for raw in reader:
        try:
            level = int(raw.get("level") or "0")
            left = int(raw.get("left") or "0"); top = int(raw.get("top") or "0")
            width = int(raw.get("width") or "0"); height = int(raw.get("height") or "0")
            conf = float(raw.get("conf") or "-1")
        except ValueError:
            continue
        if level == 1:
            page_width = max(page_width, width); page_height = max(page_height, height)
        text = (raw.get("text") or "").strip()
        if not text:
            continue
        rows.append({
            "text": text, "norm": norm(text), "left": left, "top": top, "width": width, "height": height,
            "cx": left + width / 2, "cy": top + height / 2, "conf": conf,
            "block": raw.get("block_num") or "", "par": raw.get("par_num") or "", "line": raw.get("line_num") or "",
        })
    if page_width <= 0 or page_height <= 0:
        raise RuntimeError(f"unable to determine page geometry for {path.name}")
    return page_width, page_height, rows


def y_clusters(tokens: list[dict[str, Any]], page_height: int) -> list[list[dict[str, Any]]]:
    if not tokens:
        return []
    tolerance = max(8.0, page_height * 0.018)
    clusters: list[list[dict[str, Any]]] = []
    for token in sorted(tokens, key=lambda x: (x["cy"], x["cx"])):
        if not clusters:
            clusters.append([token]); continue
        center = sum(x["cy"] for x in clusters[-1]) / len(clusters[-1])
        if abs(token["cy"] - center) <= tolerance:
            clusters[-1].append(token)
        else:
            clusters.append([token])
    return clusters


def line_groups(tokens: list[dict[str, Any]], page_height: int) -> list[dict[str, Any]]:
    tolerance = max(8.0, page_height * 0.014)
    groups: list[list[dict[str, Any]]] = []
    for token in sorted(tokens, key=lambda x: (x["cy"], x["cx"])):
        if not groups:
            groups.append([token]); continue
        center = sum(x["cy"] for x in groups[-1]) / len(groups[-1])
        if abs(token["cy"] - center) <= tolerance:
            groups[-1].append(token)
        else:
            groups.append([token])
    out = []
    for group in groups:
        ordered = sorted(group, key=lambda x: x["left"])
        out.append({
            "y": round(sum(x["cy"] for x in group) / len(group), 1),
            "text": " ".join(x["text"] for x in ordered),
            "x_min": min(x["left"] for x in group),
            "x_max": max(x["left"] + x["width"] for x in group),
        })
    return out


def token_public(t: dict[str, Any], w: int, h: int) -> dict[str, Any]:
    return {
        "text": t["text"], "x": round(t["cx"] / w, 4), "y": round(t["cy"] / h, 4),
        "w": round(t["width"] / w, 4), "h": round(t["height"] / h, 4), "conf": round(t["conf"], 1),
    }


def main() -> int:
    if subprocess.run(["tesseract", "--version"], capture_output=True).returncode != 0:
        raise RuntimeError("tesseract is not installed")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("image_count") != 578 or manifest.get("mapped_fight_count") != 575:
        raise RuntimeError("selected scorecard archive cardinality drift")
    image_meta = {str(x.get("archive_key")): x for x in manifest.get("images") or []}
    plan = read_csv(PLAN)
    fights = {r["fight_id"]: r for r in read_csv(FIGHTS)}
    if len(plan) != 578 or len(image_meta) != 578:
        raise RuntimeError("scorecard plan/archive mismatch")

    plan = sorted(plan, key=lambda r: (r.get("candidate_event_date") or "", r.get("candidate_fight_id") or "", r["archive_key"]))
    by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in plan:
        by_year[(row.get("candidate_event_date") or "")[:4] or "unknown"].append(row)

    selected: dict[str, tuple[dict[str, str], set[str]]] = {}
    for year, rows in sorted(by_year.items()):
        for row in evenly_spaced(rows, 6):
            selected.setdefault(row["archive_key"], (row, set()))[1].add(f"year_{year}")
    fight_counts = Counter(r["candidate_fight_id"] for r in plan)
    multi = {fight for fight, count in fight_counts.items() if count > 1}
    if len(multi) != 3:
        raise RuntimeError(f"expected 3 multi-image fights, got {len(multi)}")
    for row in plan:
        if row["candidate_fight_id"] in multi:
            selected.setdefault(row["archive_key"], (row, set()))[1].add("multi_image_fight")

    samples = sorted(selected.values(), key=lambda x: x[0]["archive_key"])
    if not 36 <= len(samples) <= 54:
        raise RuntimeError(f"unexpected spatial sample size: {len(samples)}")

    out_rows = []
    summary = Counter()
    year_summary: dict[str, Counter] = defaultdict(Counter)
    for row, reasons in samples:
        key = row["archive_key"]
        fight = fights.get(row["candidate_fight_id"])
        if not fight:
            raise RuntimeError(f"sample fight missing from canonical: {row['candidate_fight_id']}")
        page_w, page_h, tokens = run_tsv(IMAGES / key)
        score_tokens = [t for t in tokens if SCORE_RE.fullmatch(t["text"])]
        labels = [t for t in tokens if t["norm"] in LABEL_WORDS]
        fighter_parts = set()
        for full in (row.get("matched_fighter_names") or "").split("|"):
            for part in re.findall(r"[A-Za-z0-9]+", unicodedata.normalize("NFKD", full).encode("ascii", "ignore").decode("ascii")):
                if len(part) >= 3:
                    fighter_parts.add(norm(part))
        fighter_anchors = [t for t in tokens if t["norm"] in fighter_parts]
        clusters = y_clusters(score_tokens, page_h)

        # Lower-grid text is a diagnostic zone only. Judges are usually printed below score cells,
        # but we do not call any line a judge until a later audit proves that semantic placement.
        lower_tokens = [t for t in tokens if 0.58 <= t["cy"] / page_h <= 0.92 and not SCORE_RE.fullmatch(t["text"])]
        lower_lines = line_groups(lower_tokens, page_h)
        lower_lines = [
            {"y": round(x["y"] / page_h, 4), "x_min": round(x["x_min"] / page_w, 4), "x_max": round(x["x_max"] / page_w, 4), "text": x["text"]}
            for x in lower_lines if len(x["text"].strip()) >= 3
        ]

        score_public = [token_public(t, page_w, page_h) for t in score_tokens]
        label_public = [token_public(t, page_w, page_h) for t in labels]
        anchor_public = [token_public(t, page_w, page_h) for t in fighter_anchors]
        year = (row.get("candidate_event_date") or "")[:4] or "unknown"
        summary["images"] += 1
        summary["score_tokens"] += len(score_tokens)
        summary["score_y_clusters"] += len(clusters)
        summary["images_6plus_scores"] += len(score_tokens) >= 6
        summary["images_12plus_scores"] += len(score_tokens) >= 12
        summary["images_with_score_label"] += any(t["norm"] == "score" for t in labels)
        summary["images_with_total_label"] += any(t["norm"] == "total" for t in labels)
        summary["images_with_point_deduction_label"] += any(t["norm"] in {"point", "points", "deductions"} for t in labels)
        year_summary[year]["images"] += 1
        year_summary[year]["score_tokens"] += len(score_tokens)
        year_summary[year]["images_6plus_scores"] += len(score_tokens) >= 6
        year_summary[year]["score_y_clusters"] += len(clusters)

        out_rows.append({
            "archive_key": key,
            "candidate_fight_id": row["candidate_fight_id"],
            "candidate_event_name": row.get("candidate_event_name") or "",
            "candidate_event_date": row.get("candidate_event_date") or "",
            "image_signature": str(image_meta[key].get("image_signature") or ""),
            "canonical_result": fight.get("result") or "",
            "canonical_finish_round": fight.get("finish_round") or "",
            "canonical_scheduled_rounds": fight.get("scheduled_rounds") or "",
            "sample_reason": "|".join(sorted(reasons)),
            "page_width": page_w,
            "page_height": page_h,
            "word_count": len(tokens),
            "score_token_count": len(score_tokens),
            "score_y_cluster_count": len(clusters),
            "score_tokens_json": json.dumps(score_public, separators=(",", ":")),
            "label_tokens_json": json.dumps(label_public, separators=(",", ":")),
            "fighter_anchor_tokens_json": json.dumps(anchor_public, separators=(",", ":")),
            "lower_grid_lines_json": json.dumps(lower_lines, separators=(",", ":")),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(sorted(out_rows, key=lambda r: r["archive_key"]))

    by_year_out = {}
    for year, c in sorted(year_summary.items()):
        by_year_out[year] = {
            "images": c["images"],
            "total_score_tokens": c["score_tokens"],
            "images_with_6plus_scores": c["images_6plus_scores"],
            "avg_score_y_clusters": round(c["score_y_clusters"] / c["images"], 2),
        }
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "archive_images": 578,
        "sample_images": len(out_rows),
        "sample_year_counts": dict(Counter((r["candidate_event_date"] or "")[:4] for r in out_rows)),
        "sample_signature_counts": dict(Counter(r["image_signature"] for r in out_rows)),
        "sample_multi_image_objects": sum("multi_image_fight" in r["sample_reason"] for r in out_rows),
        "summary": dict(summary),
        "year_summary": by_year_out,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False,
            "spatial_coordinates_audited": True,
            "score_token_order_used_as_semantics": False,
            "judge_identity_resolved": False,
            "fighter_column_order_resolved": False,
            "round_row_order_resolved": False,
            "required_next": "Inspect coordinate clusters and lower-grid lines by template/year. Promote only template classes where fighter columns, judge labels, round rows, and paired score cells are jointly and repeatably resolved."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"sample": len(out_rows), "summary": dict(summary), "years": by_year_out}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
