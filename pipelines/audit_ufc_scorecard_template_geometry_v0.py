#!/usr/bin/env python3
"""Quantify repeatable UFC scorecard grid geometry from the spatial audit sample.

DATA PHASE ONLY. Learns six normalized score-column centers from the sampled official
scorecards, compares score-row counts to conservative canonical round eligibility, and
identifies only exact geometry candidates. No judge or score semantics are canonicalized.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPATIAL = ROOT / "data/derived/qa/ufc_scorecard_spatial_structure_v0.csv"
SPATIAL_AUDIT = ROOT / "provenance/audits/ufc_scorecard_spatial_structure_v0_latest.json"
ROUND_ELIG = ROOT / "data/derived/qa/ufc_scorecard_round_eligibility_v0.csv"
OUT = ROOT / "data/derived/qa/ufc_scorecard_template_geometry_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_template_geometry_v0_latest.json"

FIELDS = [
    "archive_key", "fight_id", "event_date", "year", "expected_scored_round_count",
    "grid_score_token_count", "grid_y_cluster_count", "max_x_deviation", "fighter_anchor_near_column_count",
    "judge_line_candidate", "geometry_status", "reason",
]
GRID_Y_MIN = 0.35
GRID_Y_MAX = 0.67
MAX_X_DEVIATION = 0.038


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def kmeans_1d(values: list[float], k: int = 6) -> list[float]:
    if len(values) < k:
        raise RuntimeError("insufficient values for score-column clustering")
    ordered = sorted(values)
    centers = [ordered[round(i * (len(ordered) - 1) / (k - 1))] for i in range(k)]
    for _ in range(100):
        groups = [[] for _ in range(k)]
        for value in values:
            idx = min(range(k), key=lambda j: abs(value - centers[j]))
            groups[idx].append(value)
        if any(not group for group in groups):
            raise RuntimeError("empty score-column kmeans cluster")
        new = [sum(group) / len(group) for group in groups]
        if max(abs(a - b) for a, b in zip(centers, new)) < 1e-8:
            centers = new
            break
        centers = new
    return sorted(centers)


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


def expected_round_count(raw: str) -> int | None:
    text = (raw or "").strip()
    if not text:
        return 0
    values = [int(x) for x in text.split(",") if x.strip()]
    if values != list(range(1, len(values) + 1)):
        raise RuntimeError(f"non-contiguous expected round list: {text!r}")
    return len(values)


def judge_line_candidate(lower_lines: list[dict]) -> str:
    # Find POINT DEDUCTIONS label line, then take the nearest meaningful line immediately above it.
    point_idx = None
    for i, line in enumerate(lower_lines):
        text = str(line.get("text") or "").upper()
        if "DEDUCTION" in text or ("POINT" in text and "NOTES" in text):
            point_idx = i; break
    if point_idx is None or point_idx == 0:
        return ""
    candidates = []
    for line in lower_lines[:point_idx]:
        text = str(line.get("text") or "").strip()
        alpha_words = [w for w in text.replace("'", "").replace(".", "").split() if any(c.isalpha() for c in w)]
        if len(alpha_words) >= 4 and float(line.get("x_max", 0)) - float(line.get("x_min", 0)) >= 0.45:
            candidates.append(line)
    if not candidates:
        return ""
    return str(candidates[-1].get("text") or "")


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    pos = (len(vals) - 1) * q
    lo = math.floor(pos); hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - pos) + vals[hi] * (pos - lo)


def main() -> int:
    spatial_audit = json.loads(SPATIAL_AUDIT.read_text(encoding="utf-8"))
    if spatial_audit.get("sample_images") != 48:
        raise RuntimeError("spatial sample cardinality drift")
    if (spatial_audit.get("decision") or {}).get("spatial_coordinates_audited") is not True:
        raise RuntimeError("spatial audit not accepted")
    spatial = read_csv(SPATIAL)
    eligibility = {r["fight_id"]: r for r in read_csv(ROUND_ELIG)}
    if len(spatial) != 48 or len(eligibility) != 575:
        raise RuntimeError(f"template input cardinality drift spatial={len(spatial)} eligibility={len(eligibility)}")

    all_grid = []
    parsed_by_key = {}
    for row in spatial:
        tokens = [t for t in json.loads(row["score_tokens_json"]) if GRID_Y_MIN <= float(t["y"]) <= GRID_Y_MAX]
        anchors = json.loads(row["fighter_anchor_tokens_json"])
        lower = json.loads(row["lower_grid_lines_json"])
        parsed_by_key[row["archive_key"]] = (tokens, anchors, lower)
        all_grid.extend(tokens)
    centers = kmeans_1d([float(t["x"]) for t in all_grid], 6)
    if any(b - a < 0.055 for a, b in zip(centers, centers[1:])):
        raise RuntimeError(f"score-column centers collapse: {centers}")

    assignments = Counter(); deviations = []
    for token in all_grid:
        x = float(token["x"])
        idx = min(range(6), key=lambda j: abs(x - centers[j]))
        assignments[idx] += 1
        deviations.append(abs(x - centers[idx]))

    out_rows = []; statuses = Counter(); year_status: dict[str, Counter] = defaultdict(Counter)
    for row in spatial:
        tokens, anchors, lower = parsed_by_key[row["archive_key"]]
        elig = eligibility.get(row["candidate_fight_id"])
        if not elig:
            raise RuntimeError(f"spatial sample fight missing eligibility row: {row['candidate_fight_id']}")
        if elig["eligibility_status"] != "eligible":
            expected = None
        else:
            expected = expected_round_count(elig["expected_scored_rounds"])
        y_groups = cluster_y(tokens)
        max_dev = 0.0
        group_column_sets = []
        for group in y_groups:
            cols = []
            for token in group:
                x = float(token["x"])
                idx = min(range(6), key=lambda j: abs(x - centers[j]))
                dev = abs(x - centers[idx]); max_dev = max(max_dev, dev)
                cols.append(idx)
            group_column_sets.append(cols)

        anchor_near = set()
        for anchor in anchors:
            y = float(anchor["y"]); x = float(anchor["x"])
            if 0.25 <= y <= 0.40:
                idx = min(range(6), key=lambda j: abs(x - centers[j]))
                if abs(x - centers[idx]) <= 0.07:
                    anchor_near.add(idx)
        judge_line = judge_line_candidate(lower)

        status = "not_exact_geometry"; reasons = []
        if expected is None:
            reasons.append("round_eligibility_review")
        elif expected == 0:
            if not tokens:
                status = "zero_round_clean"
                reasons.append("no completed score-eligible rounds and no grid score tokens")
            else:
                reasons.append("score_tokens_present_despite_zero_expected_rounds")
        else:
            if len(tokens) != 6 * expected:
                reasons.append(f"score_token_count={len(tokens)} expected={6*expected}")
            if len(y_groups) != expected:
                reasons.append(f"y_clusters={len(y_groups)} expected={expected}")
            if any(len(group) != 6 for group in y_groups):
                reasons.append("one_or_more_round_rows_not_six_tokens")
            if any(sorted(cols) != list(range(6)) for cols in group_column_sets):
                reasons.append("one_or_more_round_rows_not_one_token_per_column")
            if max_dev > MAX_X_DEVIATION:
                reasons.append(f"max_x_deviation={max_dev:.4f}")
            if not judge_line:
                reasons.append("judge_line_candidate_missing")
            if len(anchor_near) < 4:
                reasons.append(f"fighter_anchor_column_coverage={len(anchor_near)}")
            if not reasons:
                status = "exact_six_column_geometry_candidate"
                reasons.append("exact score grid cardinality/rows/columns plus judge-line and fighter-anchor evidence")

        year = (row["candidate_event_date"] or "")[:4]
        statuses[status] += 1; year_status[year][status] += 1
        out_rows.append({
            "archive_key": row["archive_key"],
            "fight_id": row["candidate_fight_id"],
            "event_date": row["candidate_event_date"],
            "year": year,
            "expected_scored_round_count": "" if expected is None else expected,
            "grid_score_token_count": len(tokens),
            "grid_y_cluster_count": len(y_groups),
            "max_x_deviation": round(max_dev, 5),
            "fighter_anchor_near_column_count": len(anchor_near),
            "judge_line_candidate": judge_line,
            "geometry_status": status,
            "reason": "; ".join(reasons),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(sorted(out_rows, key=lambda r: r["archive_key"]))

    year_out = {year: dict(sorted(c.items())) for year, c in sorted(year_status.items())}
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sample_images": len(out_rows),
        "grid_y_window": [GRID_Y_MIN, GRID_Y_MAX],
        "learned_score_column_centers": [round(x, 5) for x in centers],
        "score_column_assignment_counts": {str(i): assignments[i] for i in range(6)},
        "score_column_max_abs_deviation": round(max(deviations), 5) if deviations else 0,
        "score_column_p95_abs_deviation": round(percentile(deviations, 0.95), 5),
        "score_column_p99_abs_deviation": round(percentile(deviations, 0.99), 5),
        "exact_geometry_max_x_deviation": MAX_X_DEVIATION,
        "geometry_status_counts": dict(statuses),
        "year_geometry_status_counts": year_out,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False,
            "six_score_columns_repeatably_observed": True,
            "column_centers_learned_from_sample_not_single_image": True,
            "top_to_bottom_round_order_promoted": False,
            "fighter_column_identity_promoted": False,
            "judge_name_identity_promoted": False,
            "exact_geometry_subset_can_advance_to_candidate_parser": statuses["exact_six_column_geometry_candidate"] > 0,
            "required_next": "Run a candidate parser only on exact_six_column_geometry_candidate template rows first. Prove fighter A/B column assignment and three judge-name blocks, then validate parsed totals/results before expanding coverage."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"centers": payload["learned_score_column_centers"], "statuses": dict(statuses), "p95": payload["score_column_p95_abs_deviation"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
