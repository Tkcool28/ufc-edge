#!/usr/bin/env python3
"""Audit fighter-side orientation across the six-column official UFC scorecard grid.

DATA PHASE ONLY. Uses source filename-derived left/right fighter phrases already accepted
for fight identity, canonical participant names, and OCR anchor coordinates from the
spatial audit. It does not emit judge-round scores.
"""
from __future__ import annotations

import csv
import json
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/derived/identity/ufc_scorecard_archive_plan_v0.csv"
SPATIAL = ROOT / "data/derived/qa/ufc_scorecard_spatial_structure_v0.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
FIGHTERS = ROOT / "data/canonical/v0/fighters.csv"
GEOM = ROOT / "provenance/audits/ufc_scorecard_template_geometry_v0_latest.json"
OUT = ROOT / "data/derived/qa/ufc_scorecard_fighter_column_orientation_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_fighter_column_orientation_v0_latest.json"

FIELDS = [
    "archive_key", "fight_id", "left_phrase", "right_phrase", "left_fighter_id", "right_fighter_id",
    "left_canonical_name", "right_canonical_name", "orientation_status", "left_anchor_columns",
    "right_anchor_columns", "unexpected_anchor_votes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(text: str) -> str:
    s = unicodedata.normalize("NFKD", text or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join("".join(c if c.isalnum() else " " for c in s).split())


def tokens(text: str) -> set[str]:
    return {t for t in norm(text).split() if len(t) >= 3}


def phrase_matches(phrase: str, canonical_name: str) -> bool:
    p = norm(phrase); n = norm(canonical_name)
    if not p or not n:
        return False
    if p in n:
        return True
    pt = p.split(); nt = n.split()
    return bool(pt) and all(t in nt for t in pt)


def resolve_phrase(phrase: str, participant_ids: list[str], names: dict[str, str]) -> str:
    hits = [fid for fid in participant_ids if phrase_matches(phrase, names.get(fid, ""))]
    return hits[0] if len(hits) == 1 else ""


def main() -> int:
    plan = {r["archive_key"]: r for r in read_csv(PLAN)}
    spatial = read_csv(SPATIAL)
    fights = {r["fight_id"]: r for r in read_csv(FIGHTS)}
    names = {r["fighter_id"]: r["canonical_name"] for r in read_csv(FIGHTERS)}
    geom = json.loads(GEOM.read_text(encoding="utf-8"))
    centers = [float(x) for x in geom.get("learned_score_column_centers") or []]
    if len(centers) != 6:
        raise RuntimeError("six learned score columns required")
    if len(spatial) != 48:
        raise RuntimeError(f"spatial sample drift: {len(spatial)}")

    global_votes = {i: Counter() for i in range(6)}
    rows_out = []
    statuses = Counter()
    phrase_resolution_failures = []

    for row in spatial:
        p = plan.get(row["archive_key"])
        fight = fights.get(row["candidate_fight_id"])
        if not p or not fight:
            raise RuntimeError(f"missing plan/fight for {row['archive_key']}")
        participants = [fight["fighter_a_id"], fight["fighter_b_id"]]
        left_id = resolve_phrase(p["fighter_left_phrase"], participants, names)
        right_id = resolve_phrase(p["fighter_right_phrase"], participants, names)
        if not left_id or not right_id or left_id == right_id:
            phrase_resolution_failures.append(row["archive_key"])
            status = "phrase_identity_unresolved"
            left_cols = []; right_cols = []; unexpected = 0
        else:
            left_unique = tokens(names[left_id]) - tokens(names[right_id])
            right_unique = tokens(names[right_id]) - tokens(names[left_id])
            # Include source phrases because some scorecards show abbreviated surnames only.
            left_unique |= tokens(p["fighter_left_phrase"]) - tokens(p["fighter_right_phrase"])
            right_unique |= tokens(p["fighter_right_phrase"]) - tokens(p["fighter_left_phrase"])
            left_votes = Counter(); right_votes = Counter(); unexpected = 0
            anchors = json.loads(row["fighter_anchor_tokens_json"])
            for a in anchors:
                y = float(a["y"]); x = float(a["x"])
                if not (0.25 <= y <= 0.40):
                    continue
                word = norm(a["text"])
                if not word:
                    continue
                col = min(range(6), key=lambda j: abs(x - centers[j]))
                if abs(x - centers[col]) > 0.075:
                    continue
                side = ""
                if word in left_unique and word not in right_unique:
                    side = "left"; left_votes[col] += 1
                elif word in right_unique and word not in left_unique:
                    side = "right"; right_votes[col] += 1
                if side:
                    global_votes[col][side] += 1
                    if (side == "left" and col % 2 != 0) or (side == "right" and col % 2 != 1):
                        unexpected += 1
            left_cols = sorted(left_votes)
            right_cols = sorted(right_votes)
            expected_votes = sum(left_votes[c] for c in left_votes if c % 2 == 0) + sum(right_votes[c] for c in right_votes if c % 2 == 1)
            total_votes = sum(left_votes.values()) + sum(right_votes.values())
            if total_votes >= 3 and unexpected == 0:
                status = "supports_left_even_right_odd"
            elif total_votes == 0:
                status = "no_unique_anchor_votes"
            else:
                status = "mixed_or_conflicting_anchor_orientation"
        statuses[status] += 1
        rows_out.append({
            "archive_key": row["archive_key"],
            "fight_id": row["candidate_fight_id"],
            "left_phrase": p["fighter_left_phrase"],
            "right_phrase": p["fighter_right_phrase"],
            "left_fighter_id": left_id,
            "right_fighter_id": right_id,
            "left_canonical_name": names.get(left_id, ""),
            "right_canonical_name": names.get(right_id, ""),
            "orientation_status": status,
            "left_anchor_columns": ",".join(str(x) for x in left_cols),
            "right_anchor_columns": ",".join(str(x) for x in right_cols),
            "unexpected_anchor_votes": unexpected,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(sorted(rows_out, key=lambda r: r["archive_key"]))

    vote_summary = {str(i): dict(global_votes[i]) for i in range(6)}
    left_even = sum(global_votes[i]["left"] for i in (0,2,4))
    left_odd = sum(global_votes[i]["left"] for i in (1,3,5))
    right_odd = sum(global_votes[i]["right"] for i in (1,3,5))
    right_even = sum(global_votes[i]["right"] for i in (0,2,4))
    supporting = left_even + right_odd
    conflicting = left_odd + right_even
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sample_images": len(spatial),
        "phrase_identity_resolution_failures": len(phrase_resolution_failures),
        "orientation_status_counts": dict(statuses),
        "column_side_vote_counts": vote_summary,
        "left_even_votes": left_even,
        "left_odd_votes": left_odd,
        "right_odd_votes": right_odd,
        "right_even_votes": right_even,
        "supporting_votes": supporting,
        "conflicting_votes": conflicting,
        "support_fraction": round(supporting / (supporting + conflicting), 6) if supporting + conflicting else 0,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False,
            "source_filename_phrase_identity_used_only_after_canonical_participant_resolution": True,
            "fighter_column_orientation_audited": True,
            "fighter_left_is_even_columns_candidate": conflicting == 0 and supporting > 0 and not phrase_resolution_failures,
            "fighter_right_is_odd_columns_candidate": conflicting == 0 and supporting > 0 and not phrase_resolution_failures,
            "required_next": "Combine only accepted fighter-column orientation with fully recovered targeted score cells and independently resolved judge-name blocks before emitting score candidates.",
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"statuses": dict(statuses), "supporting": supporting, "conflicting": conflicting, "support_fraction": payload["support_fraction"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
