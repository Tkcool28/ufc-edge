#!/usr/bin/env python3
"""Derive conservative scored-round eligibility for identity-mapped official scorecards.

DATA PHASE ONLY. This is a guardrail, not a score parser.
- Ordinary completed DECISION/DRAW: scheduled rounds are score-eligible.
- Source-explicit technical decisions: rounds 1..finish_round are eligible, including the
  partial technical-decision round, because the official scorecard/result explicitly says
  the bout went to a technical decision at that in-round time.
- KO/TKO/SUBMISSION/DQ/NO_CONTEST/OTHER stoppages: only fully completed rounds before
  finish_round are eligible.
Unknown/contradictory timing fails closed rather than inventing a scored round.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/derived/identity/ufc_scorecard_archive_plan_v0.csv"
FULL_OCR = ROOT / "data/derived/qa/ufc_scorecard_ocr_v0.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
OUT = ROOT / "data/derived/qa/ufc_scorecard_round_eligibility_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_round_eligibility_v0_latest.json"

FIELDS = [
    "fight_id", "event_name", "event_date", "result", "method", "finish_round", "finish_time_sec",
    "scheduled_rounds", "scorecard_image_count", "technical_decision_evidence", "expected_scored_rounds",
    "eligibility_status", "reason",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def positive_int(raw: str) -> int | None:
    if not (raw or "").strip():
        return None
    value = int(raw)
    return value if value > 0 else None


def is_technical_decision_text(text: str) -> bool:
    t = " ".join((text or "").lower().replace("-", " ").split())
    return "technical" in t and "decision" in t


def main() -> int:
    plan = read_csv(PLAN)
    ocr = read_csv(FULL_OCR)
    fights = {r["fight_id"]: r for r in read_csv(FIGHTS)}
    by_fight: dict[str, list[dict[str, str]]] = {}
    for row in plan:
        if (row.get("identity_status") or "") != "high_confidence_fight_candidate":
            raise RuntimeError("archive plan contains non-high-confidence identity row")
        by_fight.setdefault(row["candidate_fight_id"], []).append(row)
    if len(plan) != 578 or len(by_fight) != 575 or len(ocr) != 578:
        raise RuntimeError(f"scorecard cardinality drift plan={len(plan)} fights={len(by_fight)} ocr={len(ocr)}")

    ocr_by_fight: dict[str, list[dict[str, str]]] = {}
    for row in ocr:
        ocr_by_fight.setdefault(row["candidate_fight_id"], []).append(row)

    rows = []
    status_counts = Counter(); method_counts = Counter(); scored_round_counts = Counter(); technical_count = 0
    for fight_id, images in sorted(by_fight.items()):
        fight = fights.get(fight_id)
        if not fight:
            raise RuntimeError(f"scorecard fight missing canonical row: {fight_id}")
        method = (fight.get("method") or "").strip()
        result = (fight.get("result") or "").strip()
        scheduled = positive_int(fight.get("scheduled_rounds") or "")
        finish_round = positive_int(fight.get("finish_round") or "")
        finish_time = positive_int(fight.get("finish_time_sec") or "")

        evidence_parts = []
        for image in images:
            if is_technical_decision_text(image.get("image_alt") or "") or is_technical_decision_text(image.get("image_title") or ""):
                evidence_parts.append("official_page_image_text")
        for image in ocr_by_fight.get(fight_id, []):
            if is_technical_decision_text(image.get("ocr_text") or ""):
                evidence_parts.append("archived_official_image_ocr")
        evidence_parts = sorted(set(evidence_parts))
        technical_evidence = ";".join(evidence_parts)

        status = "eligible"
        reason = ""
        expected = None

        if method == "DECISION":
            if finish_time is not None and finish_time < 300:
                if technical_evidence and finish_round is not None and scheduled in {3, 5} and 1 <= finish_round <= scheduled:
                    expected = finish_round
                    technical_count += 1
                    reason = "source-explicit technical decision scores rounds through the partial technical-decision round"
                else:
                    status = "review"
                    reason = "sub-300 decision lacks source-explicit technical-decision evidence or valid round metadata"
            elif scheduled in {3, 5}:
                expected = scheduled
                reason = "completed ordinary decision uses all known scheduled rounds"
            else:
                status = "review"
                reason = "decision lacks supported scheduled_rounds 3/5"
        elif method == "DRAW":
            if finish_time is not None and finish_time < 300:
                if technical_evidence and finish_round is not None and scheduled in {3, 5} and 1 <= finish_round <= scheduled:
                    expected = finish_round
                    technical_count += 1
                    reason = "source-explicit technical draw/decision scores rounds through the partial technical round"
                else:
                    status = "review"
                    reason = "sub-300 draw lacks source-explicit technical-decision evidence or valid round metadata"
            elif result == "draw" and scheduled in {3, 5}:
                expected = scheduled
                reason = "completed draw uses all known scheduled rounds"
            else:
                status = "review"
                reason = "draw method/result/timing not jointly resolved"
        elif method in {"KO_TKO", "SUBMISSION", "DQ", "NO_CONTEST", "OTHER"}:
            if finish_round is None:
                status = "review"
                reason = "stoppage-like method lacks finish_round"
            elif finish_round < 1 or (scheduled is not None and finish_round > scheduled):
                status = "review"
                reason = "finish_round outside scheduled fight"
            else:
                expected = max(0, finish_round - 1)
                reason = "only fully completed rounds before stoppage round are score-eligible"
        else:
            status = "review"
            reason = f"unsupported canonical method {method!r}"

        expected_text = "" if expected is None else ",".join(str(x) for x in range(1, expected + 1))
        status_counts[status] += 1
        method_counts[method or "<empty>"] += 1
        if expected is not None:
            scored_round_counts[expected] += 1
        first = images[0]
        rows.append({
            "fight_id": fight_id,
            "event_name": first.get("candidate_event_name") or "",
            "event_date": first.get("candidate_event_date") or "",
            "result": result,
            "method": method,
            "finish_round": fight.get("finish_round") or "",
            "finish_time_sec": fight.get("finish_time_sec") or "",
            "scheduled_rounds": fight.get("scheduled_rounds") or "",
            "scorecard_image_count": len(images),
            "technical_decision_evidence": technical_evidence,
            "expected_scored_rounds": expected_text,
            "eligibility_status": status,
            "reason": reason,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(rows)

    reviews = [r for r in rows if r["eligibility_status"] != "eligible"]
    technical_rows = [r for r in rows if r["technical_decision_evidence"]]
    payload = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scorecard_fights": len(rows),
        "scorecard_images": len(plan),
        "eligibility_status_counts": dict(status_counts),
        "method_counts": dict(sorted(method_counts.items())),
        "expected_completed_or_technical_scored_round_count_distribution": {str(k): v for k, v in sorted(scored_round_counts.items())},
        "source_verified_technical_decisions": technical_count,
        "technical_decision_examples": technical_rows[:20],
        "review_examples": reviews[:50],
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False,
            "ordinary_stoppage_unfinished_round_is_score_eligible": False,
            "source_verified_technical_decision_partial_round_is_score_eligible": True,
            "technical_decision_requires_explicit_official_scorecard_evidence": True,
            "round_eligibility_can_guard_future_parser": len(reviews) == 0,
            "required_next": "Use expected_scored_rounds as a hard upper bound. A partial finish round is eligible only where official scorecard/page evidence explicitly establishes a technical decision."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"fights": len(rows), "statuses": dict(status_counts), "technical_decisions": technical_count, "round_counts": dict(scored_round_counts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
