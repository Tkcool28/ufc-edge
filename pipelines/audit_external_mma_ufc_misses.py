#!/usr/bin/env python3
"""Diagnose UFC-labelled external-MMA rows that miss the strict canonical overlap gate.

DATA PHASE ONLY. Read-only audit; no canonical rows are written.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/kaggle_pro_mma_fights/v1/pro_mma_fights.csv"
XWALK = ROOT / "data/derived/identity/external_mma_canonical_crosswalk_candidate.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
EVENTS = ROOT / "data/canonical/v0/events.csv"
OUT = ROOT / "provenance/audits/external_mma_ufc_misses_latest.json"
UFC_ORG = "Ultimate Fighting Championship (UFC)"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def iso_source_date(value: str) -> str:
    return datetime.strptime((value or "").strip(), "%b %d, %Y").date().isoformat()


def main() -> int:
    raw = read_csv(RAW)
    xwalk = read_csv(XWALK)
    fights = read_csv(FIGHTS)
    events = read_csv(EVENTS)

    trusted: dict[str, str] = {}
    for row in xwalk:
        if (row.get("review_status") or "").strip() != "trusted":
            continue
        url = (row.get("external_fighter_url") or "").strip()
        fid = (row.get("canonical_fighter_id") or "").strip()
        if url and fid:
            previous = trusted.get(url)
            if previous and previous != fid:
                raise SystemExit(f"non-unique trusted mapping for {url}")
            trusted[url] = fid

    event_date = {
        (r.get("event_id") or "").strip(): (r.get("event_date") or "").strip()
        for r in events if (r.get("event_id") or "").strip()
    }
    by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in fights:
        a = (row.get("fighter_a_id") or "").strip()
        b = (row.get("fighter_b_id") or "").strip()
        if a and b and a != b:
            by_pair[tuple(sorted((a, b)))].append(row)

    ufc_rows = [r for r in raw if (r.get("organisation") or "").strip() == UFC_ORG]
    trusted_count_dist = Counter()
    status_counts = Counter()
    mismatch_delta_counts = Counter()
    mismatch_nearest_delta_counts = Counter()
    absent_result_pairs = Counter()
    absent_win_methods = Counter()
    mismatch_examples: list[dict[str, object]] = []
    absent_examples: list[dict[str, object]] = []
    unresolved_examples: list[dict[str, object]] = []

    for row in ufc_rows:
        f1 = trusted.get((row.get("fighter1_url") or "").strip(), "")
        f2 = trusted.get((row.get("fighter2_url") or "").strip(), "")
        trusted_count = int(bool(f1)) + int(bool(f2))
        trusted_count_dist[trusted_count] += 1
        src_date = iso_source_date(row.get("date") or "")

        if trusted_count != 2 or f1 == f2:
            status_counts["unresolved_trusted_fighter_identity"] += 1
            if len(unresolved_examples) < 50:
                unresolved_examples.append({
                    "event_title": (row.get("event_title") or "").strip(),
                    "source_event_date": src_date,
                    "fighter1_name": (row.get("fighter1_name") or "").strip(),
                    "fighter2_name": (row.get("fighter2_name") or "").strip(),
                    "fighter1_trusted": bool(f1),
                    "fighter2_trusted": bool(f2),
                    "fighter1_result": (row.get("fighter1_result") or "").strip(),
                    "fighter2_result": (row.get("fighter2_result") or "").strip(),
                    "win_method": (row.get("win_method") or "").strip(),
                })
            continue

        pair_matches = by_pair.get(tuple(sorted((f1, f2))), [])
        same_date = [f for f in pair_matches if event_date.get((f.get("event_id") or "").strip(), "") == src_date]
        if len(same_date) == 1:
            status_counts["exact_pair_plus_date"] += 1
            continue
        if len(same_date) > 1:
            status_counts["ambiguous_multiple_pair_plus_date"] += 1
            continue

        if pair_matches:
            status_counts["pair_exists_date_mismatch"] += 1
            src = datetime.fromisoformat(src_date).date()
            deltas: list[int] = []
            candidates: list[dict[str, str | int]] = []
            for fight in pair_matches:
                eid = (fight.get("event_id") or "").strip()
                cdate = event_date.get(eid, "")
                if not cdate:
                    continue
                delta = (src - datetime.fromisoformat(cdate).date()).days
                deltas.append(delta)
                mismatch_delta_counts[delta] += 1
                candidates.append({
                    "canonical_fight_id": (fight.get("fight_id") or "").strip(),
                    "canonical_event_id": eid,
                    "canonical_event_date": cdate,
                    "source_minus_canonical_days": delta,
                })
            if deltas:
                nearest = min(deltas, key=lambda d: (abs(d), d))
                mismatch_nearest_delta_counts[nearest] += 1
            if len(mismatch_examples) < 100:
                mismatch_examples.append({
                    "event_title": (row.get("event_title") or "").strip(),
                    "source_event_date": src_date,
                    "source_event_url": (row.get("url") or "").strip(),
                    "source_match_nr": (row.get("match_nr") or "").strip(),
                    "fighter1_name": (row.get("fighter1_name") or "").strip(),
                    "fighter2_name": (row.get("fighter2_name") or "").strip(),
                    "fighter1_result": (row.get("fighter1_result") or "").strip(),
                    "fighter2_result": (row.get("fighter2_result") or "").strip(),
                    "win_method": (row.get("win_method") or "").strip(),
                    "canonical_candidates": candidates,
                })
        else:
            status_counts["pair_absent_from_canonical_spine"] += 1
            rpair = ((row.get("fighter1_result") or "").strip(), (row.get("fighter2_result") or "").strip())
            absent_result_pairs[rpair] += 1
            absent_win_methods[(row.get("win_method") or "").strip()] += 1
            if len(absent_examples) < 100:
                absent_examples.append({
                    "event_title": (row.get("event_title") or "").strip(),
                    "source_event_date": src_date,
                    "source_event_url": (row.get("url") or "").strip(),
                    "source_match_nr": (row.get("match_nr") or "").strip(),
                    "fighter1_name": (row.get("fighter1_name") or "").strip(),
                    "fighter2_name": (row.get("fighter2_name") or "").strip(),
                    "fighter1_result": rpair[0],
                    "fighter2_result": rpair[1],
                    "win_method": (row.get("win_method") or "").strip(),
                    "win_details": (row.get("win_details") or "").strip(),
                    "round": (row.get("round") or "").strip(),
                    "time": (row.get("time") or "").strip(),
                })

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ufc_labelled_source_rows": len(ufc_rows),
        "trusted_fighter_count_distribution": {str(k): v for k, v in sorted(trusted_count_dist.items())},
        "status_counts": dict(status_counts),
        "pair_date_mismatch_all_candidate_delta_days": {str(k): v for k, v in sorted(mismatch_delta_counts.items())},
        "pair_date_mismatch_nearest_delta_days": {str(k): v for k, v in sorted(mismatch_nearest_delta_counts.items())},
        "pair_absent_result_pair_counts": {f"{a}|{b}": n for (a, b), n in sorted(absent_result_pairs.items())},
        "pair_absent_win_method_counts": dict(absent_win_methods),
        "pair_date_mismatch_examples": mismatch_examples,
        "pair_absent_examples": absent_examples,
        "unresolved_examples": unresolved_examples,
        "decision": {
            "canonical_rows_written": False,
            "date_tolerance_promoted": False,
            "pair_absent_rows_promoted": False,
            "required_next": "Use the measured mismatch deltas and absent-result semantics to decide whether this is timezone/date convention and/or a canonical-spine omission. Do not widen overlap identity without explicit evidence."
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ufc_labelled_source_rows": len(ufc_rows),
        "trusted_fighter_count_distribution": dict(trusted_count_dist),
        "status_counts": dict(status_counts),
        "nearest_delta_days": dict(mismatch_nearest_delta_counts),
        "pair_absent_result_pairs": {f"{a}|{b}": n for (a,b), n in absent_result_pairs.items()},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
