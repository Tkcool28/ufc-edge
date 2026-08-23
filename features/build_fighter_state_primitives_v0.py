#!/usr/bin/env python3
"""Build leakage-safe pre-fight fighter-state primitives from frozen canonical v0.

FEATURES phase only. The output is shared state, not a model and not a sportsbook layer.
All history is cutoff strictly before the target event date. Same-day fights are never
ordered implicitly. Missing canonical statistics do not become zero: each metric domain
carries its own observed exposure seconds.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/canonical/v0"
FEATURE_DIR = ROOT / "features/v0"
CONTRACT_PATH = ROOT / "features/feature_contract_v0.json"
FREEZE_PATH = ROOT / "provenance/data_phase_freeze_v0.json"
COMPLETE_PATH = ROOT / "DATA_PHASE_COMPLETE.md"
OUT = FEATURE_DIR / "fighter_state_primitives.csv"
LINEAGE = FEATURE_DIR / "fighter_state_history_lineage.csv"
MANIFEST = FEATURE_DIR / "manifest.json"
AUDIT_JSON = ROOT / "provenance/audits/fighter_state_primitives_v0_latest.json"
AUDIT_MD = ROOT / "provenance/audits/fighter_state_primitives_v0_latest.md"

BASE_FIELDS = [
    "target_fight_id", "target_event_id", "target_event_date", "fighter_id", "opponent_id",
    "target_weight_class", "target_scheduled_rounds", "target_title_bout",
    "fighter_age_years", "fighter_height_cm", "fighter_reach_cm", "fighter_leg_reach_cm", "fighter_stance",
    "observed_prior_fight_count", "observed_prior_ufc_fight_count", "observed_prior_external_fight_count",
    "observed_prior_win_count", "observed_prior_loss_count", "observed_prior_draw_count", "observed_prior_no_contest_count",
    "observed_prior_ko_win_count", "observed_prior_submission_win_count", "observed_prior_decision_win_count",
    "observed_prior_ko_loss_count", "observed_prior_submission_loss_count", "observed_prior_decision_loss_count",
    "observed_prior_r1_finish_win_count", "observed_prior_r2_finish_win_count", "observed_prior_r3plus_finish_win_count",
    "observed_prior_r1_finish_loss_count", "observed_prior_r2plus_finish_loss_count",
    "days_since_last_fight", "latest_prior_event_date", "latest_prior_stat_event_date",
    "current_win_streak", "current_loss_streak", "history_sequence_ambiguous",
    "same_day_other_fights_excluded", "eligible_prior_stat_fight_count",
    "recent3_boundary_ambiguous", "recent5_boundary_ambiguous",
]
LINEAGE_FIELDS = [
    "target_fight_id", "fighter_id", "history_fight_id", "history_event_date", "history_promotion",
    "days_before_target", "history_stat_eligible", "included_recent3", "included_recent5", "ewm365_weight",
]

DOMAIN_MAP = {
    "sig": [
        ("sig_landed", "sig_strikes_landed", "own"),
        ("sig_attempted", "sig_strikes_attempted", "own"),
        ("opp_sig_landed", "sig_strikes_landed", "opp"),
        ("opp_sig_attempted", "sig_strikes_attempted", "opp"),
    ],
    "head": [
        ("head_landed", "sig_head_landed", "own"),
        ("head_attempted", "sig_head_attempted", "own"),
        ("opp_head_landed", "sig_head_landed", "opp"),
        ("opp_head_attempted", "sig_head_attempted", "opp"),
    ],
    "body": [
        ("body_landed", "sig_body_landed", "own"),
        ("body_attempted", "sig_body_attempted", "own"),
        ("opp_body_landed", "sig_body_landed", "opp"),
        ("opp_body_attempted", "sig_body_attempted", "opp"),
    ],
    "leg": [
        ("leg_landed", "sig_leg_landed", "own"),
        ("leg_attempted", "sig_leg_attempted", "own"),
        ("opp_leg_landed", "sig_leg_landed", "opp"),
        ("opp_leg_attempted", "sig_leg_attempted", "opp"),
    ],
    "distance": [
        ("distance_landed", "sig_distance_landed", "own"),
        ("distance_attempted", "sig_distance_attempted", "own"),
        ("opp_distance_landed", "sig_distance_landed", "opp"),
        ("opp_distance_attempted", "sig_distance_attempted", "opp"),
    ],
    "clinch": [
        ("clinch_landed", "sig_clinch_landed", "own"),
        ("clinch_attempted", "sig_clinch_attempted", "own"),
        ("opp_clinch_landed", "sig_clinch_landed", "opp"),
        ("opp_clinch_attempted", "sig_clinch_attempted", "opp"),
    ],
    "ground": [
        ("ground_landed", "sig_ground_landed", "own"),
        ("ground_attempted", "sig_ground_attempted", "own"),
        ("opp_ground_landed", "sig_ground_landed", "opp"),
        ("opp_ground_attempted", "sig_ground_attempted", "opp"),
    ],
    "knockdown": [
        ("knockdowns", "knockdowns", "own"),
        ("knockdowns_suffered", "knockdowns", "opp"),
    ],
    "takedown": [
        ("takedowns_landed", "takedowns_landed", "own"),
        ("takedowns_attempted", "takedowns_attempted", "own"),
        ("opp_takedowns_landed", "takedowns_landed", "opp"),
        ("opp_takedowns_attempted", "takedowns_attempted", "opp"),
    ],
    "control": [
        ("control_sec", "control_sec", "own"),
        ("control_sec_allowed", "control_sec", "opp"),
    ],
    "submission": [
        ("submission_attempts", "submission_attempts", "own"),
        ("submission_attempts_faced", "submission_attempts", "opp"),
    ],
    "reversal": [
        ("reversals", "reversals", "own"),
        ("reversals_faced", "reversals", "opp"),
    ],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_data_freeze() -> dict[str, Any]:
    if not COMPLETE_PATH.is_file():
        raise RuntimeError("DATA_PHASE_COMPLETE.md is missing")
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    if freeze.get("phase") != "DATA" or freeze.get("status") != "complete":
        raise RuntimeError(f"DATA freeze is not complete: {freeze.get('phase')}/{freeze.get('status')}")
    for item in freeze.get("frozen_files") or []:
        path = ROOT / str(item.get("path") or "")
        if not path.is_file():
            raise RuntimeError(f"frozen DATA file missing: {path}")
        if path.stat().st_size != int(item.get("bytes")):
            raise RuntimeError(f"frozen DATA file byte drift: {path}")
        if sha256(path) != item.get("sha256"):
            raise RuntimeError(f"frozen DATA file hash drift: {path}")
    return freeze


def parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def integer(raw: str) -> int | None:
    text = str(raw or "").strip()
    if not text:
        return None
    return int(text)


def number(raw: str) -> Decimal | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise RuntimeError(f"bad numeric value {raw!r}") from exc


def bool_value(raw: str) -> bool | None:
    text = str(raw or "").strip().lower()
    if text == "":
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    raise RuntimeError(f"bad boolean {raw!r}")


def format_num(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return str(int(value))
        return format(value.normalize(), "f")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RuntimeError("non-finite float in feature output")
        text = f"{value:.10f}".rstrip("0").rstrip(".")
        return text if text else "0"
    return str(value)


def age_years(dob_raw: str, target_date: date) -> float | None:
    if not str(dob_raw or "").strip():
        return None
    dob = parse_date(dob_raw)
    days = (target_date - dob).days
    if days < 0:
        raise RuntimeError(f"DOB after target date: {dob} > {target_date}")
    return days / 365.2425


def stat_fields(contract: dict[str, Any]) -> tuple[list[str], list[str]]:
    spec = contract["fighter_state_primitives"]
    return list(spec["stat_window_prefixes"]), list(spec["stat_primitive_suffixes"])


def empty_aggregate(suffixes: list[str]) -> dict[str, Decimal]:
    return {suffix: Decimal(0) for suffix in suffixes}


def add_scaled(dst: dict[str, Decimal], src: dict[str, Decimal], suffixes: list[str], weight: Decimal) -> None:
    for suffix in suffixes:
        if suffix == "stat_fight_count":
            continue
        dst[suffix] += src.get(suffix, Decimal(0)) * weight


def aggregate_fights(items: list[dict[str, Any]], suffixes: list[str], weights: dict[str, Decimal] | None = None) -> dict[str, Decimal]:
    out = empty_aggregate(suffixes)
    out["stat_fight_count"] = Decimal(len(items))
    for item in items:
        weight = weights[item["fight_id"]] if weights is not None else Decimal(1)
        add_scaled(out, item["primitives"], suffixes, weight)
    return out


def select_recent(items: list[dict[str, Any]], n: int) -> tuple[list[dict[str, Any]] | None, bool]:
    if len(items) <= n:
        return list(items), False
    by_date = Counter(item["event_date"] for item in items)
    dates_desc = sorted(by_date, reverse=True)
    selected_dates: list[date] = []
    count = 0
    for d in dates_desc:
        group = by_date[d]
        if count + group > n:
            return None, True
        selected_dates.append(d)
        count += group
        if count == n:
            break
    selected_set = set(selected_dates)
    selected = [item for item in items if item["event_date"] in selected_set]
    if len(selected) != n:
        raise RuntimeError(f"recent{n} selection cardinality bug {len(selected)}")
    return selected, False


def outcome_for(fight: dict[str, str], fighter_id: str) -> str:
    result = fight.get("result") or ""
    if result == "win_loss":
        return "win" if fight.get("winner_id") == fighter_id else "loss"
    if result == "draw":
        return "draw"
    if result == "no_contest":
        return "no_contest"
    return "other"


def history_counts(prior: list[dict[str, Any]], fighter_id: str) -> dict[str, int]:
    out = {
        "observed_prior_fight_count": len(prior),
        "observed_prior_ufc_fight_count": sum(item["fight"].get("promotion") == "UFC" for item in prior),
        "observed_prior_external_fight_count": sum(item["fight"].get("promotion") != "UFC" for item in prior),
        "observed_prior_win_count": 0, "observed_prior_loss_count": 0,
        "observed_prior_draw_count": 0, "observed_prior_no_contest_count": 0,
        "observed_prior_ko_win_count": 0, "observed_prior_submission_win_count": 0, "observed_prior_decision_win_count": 0,
        "observed_prior_ko_loss_count": 0, "observed_prior_submission_loss_count": 0, "observed_prior_decision_loss_count": 0,
        "observed_prior_r1_finish_win_count": 0, "observed_prior_r2_finish_win_count": 0,
        "observed_prior_r3plus_finish_win_count": 0, "observed_prior_r1_finish_loss_count": 0,
        "observed_prior_r2plus_finish_loss_count": 0,
    }
    for item in prior:
        fight = item["fight"]
        outcome = outcome_for(fight, fighter_id)
        method = fight.get("method") or ""
        finish_round = integer(fight.get("finish_round") or "")
        if outcome == "win":
            out["observed_prior_win_count"] += 1
            if method == "KO_TKO": out["observed_prior_ko_win_count"] += 1
            if method == "SUBMISSION": out["observed_prior_submission_win_count"] += 1
            if method == "DECISION": out["observed_prior_decision_win_count"] += 1
            if method != "DECISION" and finish_round == 1: out["observed_prior_r1_finish_win_count"] += 1
            if method != "DECISION" and finish_round == 2: out["observed_prior_r2_finish_win_count"] += 1
            if method != "DECISION" and finish_round is not None and finish_round >= 3: out["observed_prior_r3plus_finish_win_count"] += 1
        elif outcome == "loss":
            out["observed_prior_loss_count"] += 1
            if method == "KO_TKO": out["observed_prior_ko_loss_count"] += 1
            if method == "SUBMISSION": out["observed_prior_submission_loss_count"] += 1
            if method == "DECISION": out["observed_prior_decision_loss_count"] += 1
            if method != "DECISION" and finish_round == 1: out["observed_prior_r1_finish_loss_count"] += 1
            if method != "DECISION" and finish_round is not None and finish_round >= 2: out["observed_prior_r2plus_finish_loss_count"] += 1
        elif outcome == "draw":
            out["observed_prior_draw_count"] += 1
        elif outcome == "no_contest":
            out["observed_prior_no_contest_count"] += 1
    return out


def streaks(prior: list[dict[str, Any]], fighter_id: str) -> tuple[int | None, int | None, bool]:
    date_counts = Counter(item["event_date"] for item in prior)
    ambiguous = any(v > 1 for v in date_counts.values())
    if ambiguous:
        return None, None, True
    ordered = sorted(prior, key=lambda x: x["event_date"], reverse=True)
    if not ordered:
        return 0, 0, False
    outcomes = [outcome_for(item["fight"], fighter_id) for item in ordered]
    if outcomes[0] == "win":
        count = 0
        for value in outcomes:
            if value != "win": break
            count += 1
        return count, 0, False
    if outcomes[0] == "loss":
        count = 0
        for value in outcomes:
            if value != "loss": break
            count += 1
        return 0, count, False
    return 0, 0, False


def build_stat_fight_primitives(fights, round_rows, event_dates, suffixes):
    rows_by_fight_round = defaultdict(list)
    rounds_by_fight = defaultdict(set)
    for row in round_rows:
        rnd = integer(row.get("round") or "")
        if rnd is None or rnd < 1:
            raise RuntimeError(f"invalid canonical round {row.get('fight_id')}/{row.get('round')}")
        rows_by_fight_round[(row["fight_id"], rnd)].append(row)
        rounds_by_fight[row["fight_id"]].add(rnd)

    out = {}
    reasons = Counter()
    for fight_id, observed_rounds in rounds_by_fight.items():
        fight = fights.get(fight_id)
        if not fight:
            reasons["missing_fight"] += 1
            continue
        finish_round = integer(fight.get("finish_round") or "")
        finish_time = integer(fight.get("finish_time_sec") or "")
        if finish_round is None or finish_round < 1 or finish_time is None or not (1 <= finish_time <= 300):
            reasons["invalid_or_missing_finish_timing"] += 1
            continue
        expected_rounds = set(range(1, finish_round + 1))
        if observed_rounds != expected_rounds:
            reasons["incomplete_or_extra_round_set"] += 1
            continue
        participants = {fight["fighter_a_id"], fight["fighter_b_id"]}
        per_fighter = {fid: empty_aggregate(suffixes) for fid in participants}
        valid = True
        for rnd in range(1, finish_round + 1):
            rows = rows_by_fight_round[(fight_id, rnd)]
            if len(rows) != 2 or {r.get("fighter_id") for r in rows} != participants:
                valid = False; reasons["unpaired_or_wrong_participants"] += 1; break
            by_fighter = {r["fighter_id"]: r for r in rows}
            exposure = Decimal(300 if rnd < finish_round else finish_time)
            for fid in participants:
                own = by_fighter[fid]
                opp_id = next(x for x in participants if x != fid)
                opp = by_fighter[opp_id]
                if own.get("opponent_id") != opp_id or opp.get("opponent_id") != fid:
                    valid = False; reasons["opponent_id_mismatch"] += 1; break
                per_fighter[fid]["exposure_sec"] += exposure
                for domain, mappings in DOMAIN_MAP.items():
                    values = []
                    for suffix, source_field, side in mappings:
                        raw = own.get(source_field) if side == "own" else opp.get(source_field)
                        value = number(raw or "")
                        if value is None:
                            values = []
                            break
                        values.append((suffix, value))
                    if not values:
                        continue
                    per_fighter[fid][f"{domain}_exposure_sec"] += exposure
                    for suffix, value in values:
                        per_fighter[fid][suffix] += value
            if not valid:
                break
        if not valid:
            continue
        for fid in participants:
            per_fighter[fid]["stat_fight_count"] = Decimal(1)
            out[(fight_id, fid)] = {
                "fight_id": fight_id, "fighter_id": fid,
                "event_date": event_dates[fight["event_id"]],
                "primitives": per_fighter[fid],
            }
    return out, reasons


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_num(row.get(field)) for field in fields})


def main() -> int:
    freeze = verify_data_freeze()
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    prefixes, suffixes = stat_fields(contract)
    required_exposure_suffixes = {"exposure_sec"} | {f"{domain}_exposure_sec" for domain in DOMAIN_MAP}
    missing_exposures = sorted(required_exposure_suffixes - set(suffixes))
    if missing_exposures:
        raise RuntimeError(f"feature contract missing domain exposure suffixes: {missing_exposures}")

    fighters = {row["fighter_id"]: row for row in read_csv(DATA / "fighters.csv")}
    events = {row["event_id"]: row for row in read_csv(DATA / "events.csv")}
    fights = {row["fight_id"]: row for row in read_csv(DATA / "fights.csv")}
    round_rows = read_csv(DATA / "fighter_round_stats.csv")
    event_dates = {eid: parse_date(row["event_date"]) for eid, row in events.items()}
    stat_fights, stat_ineligible_reasons = build_stat_fight_primitives(fights, round_rows, event_dates, suffixes)

    history_by_fighter = defaultdict(list)
    for fight in fights.values():
        event_date = event_dates[fight["event_id"]]
        for fighter_id in (fight["fighter_a_id"], fight["fighter_b_id"]):
            history_by_fighter[fighter_id].append({"fight": fight, "event_date": event_date})
    for items in history_by_fighter.values():
        items.sort(key=lambda x: (x["event_date"], x["fight"]["fight_id"]))

    targets = [fight for fight in fights.values() if fight.get("promotion") == "UFC"]
    targets.sort(key=lambda fight: (event_dates[fight["event_id"]], fight["fight_id"]))
    output_fields = BASE_FIELDS + [f"{prefix}_{suffix}" for prefix in prefixes for suffix in suffixes]
    rows_out = []
    lineage_rows = []
    recent3_ambiguous_rows = recent5_ambiguous_rows = 0
    rows_without_prior_history = rows_without_prior_stat_history = 0
    rows_with_same_day_exclusions = 0
    max_lineage_date = None

    for target in targets:
        target_date = event_dates[target["event_id"]]
        participants = [target["fighter_a_id"], target["fighter_b_id"]]
        for fighter_id in participants:
            opponent_id = participants[1] if fighter_id == participants[0] else participants[0]
            prior = [item for item in history_by_fighter[fighter_id] if item["event_date"] < target_date]
            same_day_other = sum(item["event_date"] == target_date and item["fight"]["fight_id"] != target["fight_id"] for item in history_by_fighter[fighter_id])
            if same_day_other: rows_with_same_day_exclusions += 1
            if not prior: rows_without_prior_history += 1
            prior_stat = []
            for item in prior:
                stat_item = stat_fights.get((item["fight"]["fight_id"], fighter_id))
                if stat_item:
                    prior_stat.append({**stat_item, "fight": item["fight"]})
            if not prior_stat: rows_without_prior_stat_history += 1

            recent3, amb3 = select_recent(prior_stat, 3)
            recent5, amb5 = select_recent(prior_stat, 5)
            recent3_ambiguous_rows += amb3; recent5_ambiguous_rows += amb5
            recent3_ids = {item["fight_id"] for item in recent3 or []}
            recent5_ids = {item["fight_id"] for item in recent5 or []}
            weights = {}
            for item in prior_stat:
                days_before = (target_date - item["event_date"]).days
                if days_before <= 0: raise RuntimeError("non-prior stat fight leaked into history")
                weights[item["fight_id"]] = Decimal(str(2 ** (-days_before / 365.0)))

            aggregates = {
                "career": aggregate_fights(prior_stat, suffixes),
                "recent3": None if amb3 else aggregate_fights(recent3 or [], suffixes),
                "recent5": None if amb5 else aggregate_fights(recent5 or [], suffixes),
                "ewm365": aggregate_fights(prior_stat, suffixes, weights=weights),
            }
            fighter = fighters[fighter_id]
            hcounts = history_counts(prior, fighter_id)
            win_streak, loss_streak, sequence_ambiguous = streaks(prior, fighter_id)
            latest_prior = max((item["event_date"] for item in prior), default=None)
            latest_prior_stat = max((item["event_date"] for item in prior_stat), default=None)
            row = {
                "target_fight_id": target["fight_id"], "target_event_id": target["event_id"],
                "target_event_date": target_date.isoformat(), "fighter_id": fighter_id, "opponent_id": opponent_id,
                "target_weight_class": target.get("weight_class") or None,
                "target_scheduled_rounds": integer(target.get("scheduled_rounds") or ""),
                "target_title_bout": bool_value(target.get("title_bout") or ""),
                "fighter_age_years": age_years(fighter.get("dob") or "", target_date),
                "fighter_height_cm": number(fighter.get("height_cm") or ""),
                "fighter_reach_cm": number(fighter.get("reach_cm") or ""),
                "fighter_leg_reach_cm": number(fighter.get("leg_reach_cm") or ""),
                "fighter_stance": fighter.get("stance") or None,
                **hcounts,
                "days_since_last_fight": (target_date - latest_prior).days if latest_prior else None,
                "latest_prior_event_date": latest_prior.isoformat() if latest_prior else None,
                "latest_prior_stat_event_date": latest_prior_stat.isoformat() if latest_prior_stat else None,
                "current_win_streak": win_streak, "current_loss_streak": loss_streak,
                "history_sequence_ambiguous": sequence_ambiguous,
                "same_day_other_fights_excluded": same_day_other,
                "eligible_prior_stat_fight_count": len(prior_stat),
                "recent3_boundary_ambiguous": amb3, "recent5_boundary_ambiguous": amb5,
            }
            for prefix in prefixes:
                agg = aggregates[prefix]
                for suffix in suffixes:
                    row[f"{prefix}_{suffix}"] = None if agg is None else agg[suffix]
            rows_out.append(row)

            for item in prior:
                history_fight = item["fight"]
                history_id = history_fight["fight_id"]
                stat_eligible = (history_id, fighter_id) in stat_fights
                days_before = (target_date - item["event_date"]).days
                if days_before <= 0: raise RuntimeError("lineage cutoff violation")
                max_lineage_date = max(max_lineage_date, item["event_date"]) if max_lineage_date else item["event_date"]
                lineage_rows.append({
                    "target_fight_id": target["fight_id"], "fighter_id": fighter_id,
                    "history_fight_id": history_id, "history_event_date": item["event_date"].isoformat(),
                    "history_promotion": history_fight.get("promotion") or "", "days_before_target": days_before,
                    "history_stat_eligible": stat_eligible,
                    "included_recent3": stat_eligible and not amb3 and history_id in recent3_ids,
                    "included_recent5": stat_eligible and not amb5 and history_id in recent5_ids,
                    "ewm365_weight": weights.get(history_id) if stat_eligible else None,
                })

    expected_rows = len(targets) * 2
    if len(rows_out) != expected_rows:
        raise RuntimeError(f"target state cardinality mismatch {len(rows_out)} != {expected_rows}")
    rows_out.sort(key=lambda r: (r["target_event_date"], r["target_fight_id"], r["fighter_id"]))
    lineage_rows.sort(key=lambda r: (r["target_fight_id"], r["fighter_id"], r["history_event_date"], r["history_fight_id"]))
    write_csv(OUT, output_fields, rows_out)
    write_csv(LINEAGE, LINEAGE_FIELDS, lineage_rows)

    manifest = {
        "schema_version": 1,
        "feature_contract_version": contract.get("contract_version"),
        "data_phase_freeze_sha256": sha256(FREEZE_PATH),
        "data_phase_completed_at_local": freeze.get("completed_at_local"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "target_scope": "canonical promotion == UFC",
        "cutoff_rule": "history_event_date < target_event_date",
        "same_day_policy": "exclude same-day other fights as prior evidence",
        "ewm365_half_life_days": 365,
        "counts": {
            "canonical_fights": len(fights), "ufc_target_fights": len(targets), "fighter_state_rows": len(rows_out),
            "history_lineage_rows": len(lineage_rows), "stat_eligible_fighter_fight_keys": len(stat_fights),
            "rows_without_prior_history": rows_without_prior_history,
            "rows_without_prior_stat_history": rows_without_prior_stat_history,
            "rows_with_same_day_other_fights_excluded": rows_with_same_day_exclusions,
            "recent3_boundary_ambiguous_rows": recent3_ambiguous_rows,
            "recent5_boundary_ambiguous_rows": recent5_ambiguous_rows,
        },
        "stat_ineligible_reason_counts": dict(stat_ineligible_reasons),
        "files": [
            {"path": str(OUT.relative_to(ROOT)), "bytes": OUT.stat().st_size, "sha256": sha256(OUT)},
            {"path": str(LINEAGE.relative_to(ROOT)), "bytes": LINEAGE.stat().st_size, "sha256": sha256(LINEAGE)},
        ],
        "rules": {
            "missing_is_not_zero": true,
            "same_day_order_inferred": false,
            "external_fights_can_supply_missing_round_stats": false,
            "recent_boundary_ties_fail_closed": true,
            "ewm_uses_calendar_days_not_fabricated_fight_order": true,
            "market_data_used": false
        }
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    audit = {
        **manifest,
        "output_columns": len(output_fields), "lineage_columns": len(LINEAGE_FIELDS),
        "target_date_min": rows_out[0]["target_event_date"] if rows_out else None,
        "target_date_max": rows_out[-1]["target_event_date"] if rows_out else None,
        "max_included_history_event_date": max_lineage_date.isoformat() if max_lineage_date else None,
        "decision": {
            "fighter_state_primitives_materialized": true,
            "safe_for_feature_family_builders": true,
            "opponent_adjustment_built": false,
            "matchup_interactions_built": false,
            "model_training_started": false
        }
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "# Fighter state primitives v0\n\n"
        f"- UFC target fights: **{len(targets):,}**\n"
        f"- Fighter-state rows: **{len(rows_out):,}**\n"
        f"- History lineage rows: **{len(lineage_rows):,}**\n"
        f"- Stat-eligible fighter/fight keys: **{len(stat_fights):,}**\n"
        f"- Same-day-exclusion state rows: **{rows_with_same_day_exclusions:,}**\n"
        f"- Recent-3 boundary ambiguities: **{recent3_ambiguous_rows:,}**\n"
        f"- Recent-5 boundary ambiguities: **{recent5_ambiguous_rows:,}**\n\n"
        "All history dates are strictly earlier than target event dates. Missing stat domains use domain-specific exposure and never become zero.\n",
        encoding="utf-8"
    )
    print(json.dumps({
        "ufc_target_fights": len(targets), "fighter_state_rows": len(rows_out),
        "lineage_rows": len(lineage_rows), "stat_eligible_keys": len(stat_fights),
        "recent3_ambiguous": recent3_ambiguous_rows, "recent5_ambiguous": recent5_ambiguous_rows
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
