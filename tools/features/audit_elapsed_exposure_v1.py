#!/usr/bin/env python3
"""Audit real canonical coverage for elapsed-exposure eligibility V1."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from ufc_edge.features.elapsed_exposure import (
    ElapsedExposureError,
    infer_fight_exposure,
    infer_round_exposure,
    load_registry,
    registry_sha256,
)


ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "data/canonical/v0"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def pct(n: int, d: int) -> float | None:
    return round(100.0 * n / d, 6) if d else None


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sorted_counter(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items(), key=lambda item: item[0]))


def audit() -> dict[str, Any]:
    registry = load_registry(ROOT)
    events = rows(CANON / "events.csv")
    fights = rows(CANON / "fights.csv")
    stats = rows(CANON / "fighter_round_stats.csv")

    event_by_id = {r["event_id"]: r for r in events}
    fight_by_id = {r["fight_id"]: r for r in fights}
    stats_by_fight: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in stats:
        stats_by_fight[row["fight_id"]].append(row)

    inventory: dict[str, Any] = {}
    promotion_fights: dict[str, list[dict[str, str]]] = defaultdict(list)
    for fight in fights:
        promotion_fights[fight["promotion"]].append(fight)

    for promotion in sorted(promotion_fights):
        pf = promotion_fights[promotion]
        dates = sorted(
            event_by_id[f["event_id"]]["event_date"]
            for f in pf
            if f["event_id"] in event_by_id and event_by_id[f["event_id"]].get("event_date")
        )
        fighter_ids = {
            fid
            for f in pf
            for fid in (f.get("fighter_a_id"), f.get("fighter_b_id"))
            if fid
        }
        stat_fights = {f["fight_id"] for f in pf if f["fight_id"] in stats_by_fight}
        stat_rows = sum(len(stats_by_fight[fid]) for fid in stat_fights)
        inventory[promotion] = {
            "fights": len(pf),
            "fighters": len(fighter_ids),
            "date_min": dates[0] if dates else None,
            "date_max": dates[-1] if dates else None,
            "fights_with_round_stats": len(stat_fights),
            "fighter_round_stat_observations": stat_rows,
        }

    status = Counter()
    rulesets = Counter()
    safe_fights = 0
    safe_ufc_fights = 0
    ufc_fights = 0
    safe_stat_fights = 0
    stat_fight_total = len(stats_by_fight)
    safe_stat_rows = 0
    stat_rows_total = len(stats)
    bad_control_bounds: list[dict[str, Any]] = []
    control_states = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    by_promotion: dict[str, Counter[str]] = defaultdict(Counter)
    by_year: dict[str, Counter[str]] = defaultdict(Counter)

    exposure_by_fight: dict[str, Any] = {}
    for fight in fights:
        event = event_by_id.get(fight["event_id"], {})
        event_date = event.get("event_date")
        ex = infer_fight_exposure(fight, event_date, registry)
        exposure_by_fight[fight["fight_id"]] = ex
        status[ex.elapsed_exposure_status] += 1
        by_promotion[fight["promotion"]]["fights"] += 1
        year = (event_date or "unknown")[:4]
        by_year[year]["fights"] += 1
        if ex.ruleset_id:
            rulesets[ex.ruleset_id] += 1
        if ex.eligible:
            safe_fights += 1
            by_promotion[fight["promotion"]]["eligible_fights"] += 1
            by_year[year]["eligible_fights"] += 1
        if fight["promotion"] == "UFC":
            ufc_fights += 1
            if ex.eligible:
                safe_ufc_fights += 1
        key = ex.elapsed_exposure_status
        if len(examples[key]) < 4:
            examples[key].append({
                "fight_id": fight["fight_id"],
                "promotion": fight["promotion"],
                "event_date": event_date,
                "ruleset_id": ex.ruleset_id,
                "elapsed_sec": ex.elapsed_sec,
                "reason": ex.reason,
            })

    for fight_id, fight_stats in stats_by_fight.items():
        fight = fight_by_id[fight_id]
        event_date = event_by_id[fight["event_id"]]["event_date"]
        row_safe = 0
        for row in fight_stats:
            elapsed = infer_round_exposure(fight, event_date, row["round"], registry)
            promotion = fight["promotion"]
            year = event_date[:4]
            by_promotion[promotion]["round_stat_observations"] += 1
            by_year[year]["round_stat_observations"] += 1
            if elapsed is not None and elapsed > 0:
                row_safe += 1
                safe_stat_rows += 1
                by_promotion[promotion]["eligible_round_stat_observations"] += 1
                by_year[year]["eligible_round_stat_observations"] += 1
                raw_control = row.get("control_sec")
                if raw_control in (None, ""):
                    control_states["missing"] += 1
                else:
                    c = int(raw_control)
                    if c == 0:
                        control_states["observed_zero"] += 1
                    elif c > 0:
                        control_states["observed_positive"] += 1
                    if c > elapsed:
                        bad_control_bounds.append({
                            "fight_id": fight_id,
                            "fighter_id": row["fighter_id"],
                            "round": row["round"],
                            "control_sec": c,
                            "elapsed_sec": elapsed,
                        })
            else:
                control_states["excluded_no_elapsed_exposure"] += 1
        if row_safe == len(fight_stats):
            safe_stat_fights += 1

    # Deterministic "current/recent" audit: fighters with a UFC fight in the final 730 days
    # of the frozen canonical UFC timeline, then all round-stat history attached to those fighters.
    ufc_dates = [
        date.fromisoformat(event_by_id[f["event_id"]]["event_date"])
        for f in fights
        if f["promotion"] == "UFC" and event_by_id.get(f["event_id"], {}).get("event_date")
    ]
    latest_ufc_date = max(ufc_dates)
    recent_cutoff = latest_ufc_date - timedelta(days=730)
    recent_fighters: set[str] = set()
    for fight in fights:
        if fight["promotion"] != "UFC":
            continue
        d = date.fromisoformat(event_by_id[fight["event_id"]]["event_date"])
        if d >= recent_cutoff:
            recent_fighters.update([fight["fighter_a_id"], fight["fighter_b_id"]])
    recent_rows = 0
    recent_safe_rows = 0
    for row in stats:
        if row["fighter_id"] not in recent_fighters:
            continue
        recent_rows += 1
        fight = fight_by_id[row["fight_id"]]
        event_date = event_by_id[fight["event_id"]]["event_date"]
        if infer_round_exposure(fight, event_date, row["round"], registry):
            recent_safe_rows += 1

    def finalize_breakdown(source: dict[str, Counter[str]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key in sorted(source):
            c = source[key]
            out[key] = dict(c)
            if c["fights"]:
                out[key]["fight_coverage_pct"] = pct(c["eligible_fights"], c["fights"])
            if c["round_stat_observations"]:
                out[key]["round_stat_coverage_pct"] = pct(
                    c["eligible_round_stat_observations"], c["round_stat_observations"]
                )
        return out

    if bad_control_bounds:
        raise ElapsedExposureError(
            f"{len(bad_control_bounds)} canonical control observations exceed compatible elapsed exposure; "
            f"first={bad_control_bounds[0]}"
        )

    deterministic = {
        "schema_version": 1,
        "registry_version": registry["registry_version"],
        "registry_sha256": registry_sha256(ROOT),
        "canonical_data_contract_version": "0.4.0-draft",
        "canonical_manifest_sha256": file_sha(CANON / "manifest.json"),
        "counts": {
            "canonical_fights": len(fights),
            "eligible_fights": safe_fights,
            "ambiguous_or_unknown_fights": len(fights) - safe_fights,
            "ufc_fights": ufc_fights,
            "eligible_ufc_fights": safe_ufc_fights,
            "fights_with_round_stats": stat_fight_total,
            "fully_eligible_fights_with_round_stats": safe_stat_fights,
            "fighter_round_stat_observations": stat_rows_total,
            "eligible_fighter_round_stat_observations": safe_stat_rows,
        },
        "coverage": {
            "overall_fights_pct": pct(safe_fights, len(fights)),
            "ufc_fights_pct": pct(safe_ufc_fights, ufc_fights),
            "fights_with_round_stats_pct": pct(safe_stat_fights, stat_fight_total),
            "fighter_round_stat_observations_pct": pct(safe_stat_rows, stat_rows_total),
            "recent_ufc_fighter_history_definition": (
                f"fighters appearing in UFC canonical fights from {recent_cutoff.isoformat()} "
                f"through {latest_ufc_date.isoformat()}"
            ),
            "recent_ufc_fighters": len(recent_fighters),
            "recent_ufc_fighter_round_stat_observations": recent_rows,
            "eligible_recent_ufc_fighter_round_stat_observations": recent_safe_rows,
            "recent_ufc_fighter_round_stat_observations_pct": pct(recent_safe_rows, recent_rows),
        },
        "inventory_by_promotion": inventory,
        "status_counts": sorted_counter(status),
        "ruleset_assignment_counts": sorted_counter(rulesets),
        "coverage_by_promotion": finalize_breakdown(by_promotion),
        "coverage_by_year": finalize_breakdown(by_year),
        "control_observation_states_on_eligible_rounds": sorted_counter(control_states),
        "control_elapsed_bound_violations": 0,
        "examples": dict(sorted(examples.items())),
    }
    encoded = json.dumps(deterministic, sort_keys=True, separators=(",", ":")).encode()
    deterministic["deterministic_payload_sha256"] = hashlib.sha256(encoded).hexdigest()
    return deterministic


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit()
    payload = {
        "deterministic": report,
        "run": {
            "code_sha": os.environ.get("GITHUB_SHA", "working_tree"),
        },
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
