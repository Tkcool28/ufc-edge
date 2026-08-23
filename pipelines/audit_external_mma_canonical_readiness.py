#!/usr/bin/env python3
"""Measure the exact non-UFC external-MMA subset eligible for canonical v0 insertion.

DATA PHASE ONLY. Read-only audit; no canonical tables are changed.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/kaggle_pro_mma_fights/v1/pro_mma_fights.csv"
XWALK = ROOT / "data/derived/identity/external_mma_canonical_crosswalk_candidate.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
EVENTS = ROOT / "data/canonical/v0/events.csv"
OUT = ROOT / "provenance/audits/external_mma_canonical_readiness_latest.json"
UFC_ORG = "Ultimate Fighting Championship (UFC)"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_date(value: str) -> str:
    return datetime.strptime((value or "").strip(), "%b %d, %Y").date().isoformat()


def parse_time(value: str) -> int | None:
    text = (value or "").strip()
    m = re.fullmatch(r"(\d+):(\d{2})", text)
    if not m or int(m.group(2)) >= 60:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def normalize_method(value: str) -> str:
    text = (value or "").strip().lower()
    if text in {"ko", "tko"}:
        return "KO_TKO"
    if text in {"submission", "technical submission"}:
        return "SUBMISSION"
    if text == "decision":
        return "DECISION"
    if text == "disqualification":
        return "DQ"
    if text == "draw":
        return "DRAW"
    if text == "no contest":
        return "NO_CONTEST"
    return "OTHER"


def result_semantics(r1: str, r2: str) -> tuple[str, int | None]:
    a, b = (r1 or "").strip().lower(), (r2 or "").strip().lower()
    if (a, b) == ("win", "loss"):
        return "win_loss", 1
    if (a, b) == ("loss", "win"):
        return "win_loss", 2
    if (a, b) == ("draw", "draw"):
        return "draw", None
    if (a, b) == ("nc", "nc"):
        return "no_contest", None
    return "unknown", None


def main() -> int:
    raw = read_csv(RAW)
    xwalk = read_csv(XWALK)
    fights = read_csv(FIGHTS)
    events = read_csv(EVENTS)

    trusted: dict[str, str] = {}
    for r in xwalk:
        if (r.get("review_status") or "").strip() != "trusted":
            continue
        url = (r.get("external_fighter_url") or "").strip()
        fid = (r.get("canonical_fighter_id") or "").strip()
        if not url or not fid:
            continue
        old = trusted.get(url)
        if old and old != fid:
            raise SystemExit(f"trusted crosswalk collision for {url}")
        trusted[url] = fid

    event_dates = {
        (r.get("event_id") or "").strip(): (r.get("event_date") or "").strip()
        for r in events if (r.get("event_id") or "").strip()
    }
    by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for f in fights:
        a = (f.get("fighter_a_id") or "").strip()
        b = (f.get("fighter_b_id") or "").strip()
        if a and b and a != b:
            by_pair[tuple(sorted((a, b)))].append(f)

    key_counts = Counter(((r.get("url") or "").strip(), (r.get("match_nr") or "").strip()) for r in raw)
    duplicate_keys = {k for k, n in key_counts.items() if n > 1}

    classes = Counter()
    eligible_rows: list[dict[str, object]] = []
    same_pair_examples: list[dict[str, object]] = []
    result_pairs = Counter()
    normalized_results = Counter()
    raw_methods = Counter()
    normalized_methods = Counter()
    raw_rounds = Counter()
    time_parse = Counter()
    eligible_event_urls: set[str] = set()
    eligible_orgs = Counter()

    for row in raw:
        org = (row.get("organisation") or "").strip()
        if org == UFC_ORG:
            classes["excluded_ufc_label"] += 1
            continue
        key = ((row.get("url") or "").strip(), (row.get("match_nr") or "").strip())
        if key in duplicate_keys:
            classes["duplicate_source_key_quarantine"] += 1
            continue
        f1 = trusted.get((row.get("fighter1_url") or "").strip(), "")
        f2 = trusted.get((row.get("fighter2_url") or "").strip(), "")
        if not f1 or not f2 or f1 == f2:
            classes["unresolved_trusted_fighter_identity"] += 1
            continue

        src_date = parse_date(row.get("date") or "")
        pair_matches = by_pair.get(tuple(sorted((f1, f2))), [])
        nearest_delta: int | None = None
        if pair_matches:
            src = datetime.fromisoformat(src_date).date()
            deltas = []
            for f in pair_matches:
                cdate = event_dates.get((f.get("event_id") or "").strip(), "")
                if cdate:
                    deltas.append((src - datetime.fromisoformat(cdate).date()).days)
            if deltas:
                nearest_delta = min(deltas, key=lambda d: (abs(d), d))
            if nearest_delta is not None and abs(nearest_delta) <= 1:
                classes["canonical_ufc_overlap_pair_within_one_day"] += 1
                continue
            classes["eligible_non_ufc_same_pair_distinct_date"] += 1
            if len(same_pair_examples) < 50:
                same_pair_examples.append({
                    "source_event_url": key[0],
                    "source_match_nr": key[1],
                    "event_title": (row.get("event_title") or "").strip(),
                    "organisation": org,
                    "source_event_date": src_date,
                    "fighter1_name": (row.get("fighter1_name") or "").strip(),
                    "fighter2_name": (row.get("fighter2_name") or "").strip(),
                    "canonical_pair_fight_count": len(pair_matches),
                    "nearest_source_minus_canonical_days": nearest_delta,
                })
        else:
            classes["eligible_non_ufc_no_canonical_pair"] += 1

        rpair = ((row.get("fighter1_result") or "").strip(), (row.get("fighter2_result") or "").strip())
        result, winner_side = result_semantics(*rpair)
        method_raw = (row.get("win_method") or "").strip()
        method = normalize_method(method_raw)
        round_raw = (row.get("round") or "").strip()
        try:
            round_int = int(round_raw)
        except ValueError:
            round_int = -1
        time_sec = parse_time(row.get("time") or "")

        result_pairs[rpair] += 1
        normalized_results[result] += 1
        raw_methods[method_raw] += 1
        normalized_methods[method] += 1
        raw_rounds[round_raw] += 1
        time_parse["valid_mmss"] += int(time_sec is not None)
        time_parse["invalid_mmss"] += int(time_sec is None)
        eligible_event_urls.add(key[0])
        eligible_orgs[org] += 1
        eligible_rows.append({
            "source_event_url": key[0],
            "source_match_nr": key[1],
            "source_event_date": src_date,
            "organisation": org,
            "fighter1_canonical_id": f1,
            "fighter2_canonical_id": f2,
            "result": result,
            "winner_side": winner_side,
            "method": method,
            "round_raw": round_raw,
            "round_int": round_int,
            "time_sec": time_sec,
            "nearest_canonical_pair_date_delta": nearest_delta,
        })

    unknown_result_rows = sum(1 for r in eligible_rows if r["result"] == "unknown")
    invalid_round_rows = sum(1 for r in eligible_rows if not (1 <= int(r["round_int"]) <= 10))
    invalid_time_rows = sum(1 for r in eligible_rows if r["time_sec"] is None)
    other_method_rows = sum(1 for r in eligible_rows if r["method"] == "OTHER")
    contract_ready = [
        r for r in eligible_rows
        if r["result"] != "unknown" and 1 <= int(r["round_int"]) <= 10 and r["time_sec"] is not None
    ]

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_rows": len(raw),
        "trusted_external_fighter_urls": len(trusted),
        "classification_counts": dict(classes),
        "eligible_non_ufc_rows_before_contract_semantic_gate": len(eligible_rows),
        "eligible_distinct_event_urls": len(eligible_event_urls),
        "eligible_organisation_counts": dict(eligible_orgs),
        "eligible_result_pair_counts": {f"{a}|{b}": n for (a, b), n in sorted(result_pairs.items())},
        "eligible_normalized_result_counts": dict(normalized_results),
        "eligible_raw_method_counts": dict(raw_methods),
        "eligible_normalized_method_counts": dict(normalized_methods),
        "eligible_round_counts": dict(raw_rounds),
        "eligible_time_parse_counts": dict(time_parse),
        "semantic_gate_failures": {
            "unknown_result_rows": unknown_result_rows,
            "round_outside_contract_1_to_10_rows": invalid_round_rows,
            "invalid_time_mmss_rows": invalid_time_rows,
            "method_mapped_to_other_rows": other_method_rows,
        },
        "contract_ready_fight_rows": len(contract_ready),
        "same_pair_distinct_date_examples": same_pair_examples,
        "decision": {
            "canonical_rows_written": False,
            "ufc_overlap_boundary_candidate": "trusted unordered fighter pair and source date within +/-1 day of an existing canonical UFC pair event date",
            "same_pair_outside_one_day_remains_eligible": True,
            "unknown_result_is_canonical_eligible": False,
            "round_zero_is_canonical_finish_round": False,
            "required_next": "Promote only the contract-ready non-UFC rows after reviewing this audit. Preserve semantic failures as exclusions; do not fabricate finish round/time."
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification_counts": dict(classes),
        "eligible_rows": len(eligible_rows),
        "eligible_events": len(eligible_event_urls),
        "contract_ready_fight_rows": len(contract_ready),
        "semantic_gate_failures": payload["semantic_gate_failures"],
        "same_pair_examples": same_pair_examples[:10],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
