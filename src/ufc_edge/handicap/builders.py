from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .store import CanonicalStore, iso_utc, parse_cutoff

SUMMARY_STAT_FIELDS = (
    "knockdowns",
    "sig_strikes_landed",
    "sig_strikes_attempted",
    "total_strikes_landed",
    "total_strikes_attempted",
    "takedowns_landed",
    "takedowns_attempted",
    "submission_attempts",
    "reversals",
    "control_sec",
    "sig_head_landed",
    "sig_head_attempted",
    "sig_body_landed",
    "sig_body_attempted",
    "sig_leg_landed",
    "sig_leg_attempted",
    "sig_distance_landed",
    "sig_distance_attempted",
    "sig_clinch_landed",
    "sig_clinch_attempted",
    "sig_ground_landed",
    "sig_ground_attempted",
)

BASE_WARNINGS = [
    "Missing canonical values remain null/absent; H00 does not zero-fill.",
    "FightMetric positional/TIP time fields are coarse quantized bucket evidence, not exact elapsed seconds.",
    "Exact round control_sec remains distinct and comes from the canonical exact-control transport.",
    "Historical rankings are dated observations and only rows strictly before the information cutoff are included.",
    "Official fighter profiles are point-in-time snapshots and are never backfilled before observed_at_utc.",
    "Canonical judge-round scores are unavailable in DATA v0 and are not included.",
]

def generator_commit(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None

def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

def _parse_date(value: str) -> date:
    return date.fromisoformat(value)

def _event_before_cutoff(event: dict[str, Any], cutoff: datetime) -> bool:
    start = event.get("event_start_utc")
    if start:
        return _parse_timestamp(str(start)) < cutoff
    event_date = event.get("event_date")
    if not event_date:
        return False
    # Date-only observations on the cutoff date fail closed because event time is unknown.
    return _parse_date(str(event_date)) < cutoff.date()

def _weigh_in_safe(
    row: dict[str, Any],
    fight: dict[str, Any] | None,
    event: dict[str, Any] | None,
    cutoff: datetime,
) -> bool:
    observed_date = row.get("weigh_in_date")
    if observed_date:
        # Date-only observation: require a strictly prior calendar date.
        return _parse_date(str(observed_date)) < cutoff.date()
    # If no trusted weigh-in date exists, a weigh-in is historically safe only after
    # its associated fight itself is already strictly before cutoff.
    return bool(fight and event and _event_before_cutoff(event, cutoff))

def _method_group(method: Any) -> str:
    text = str(method or "").upper()
    if "KO" in text:
        return "ko_tko"
    if "SUB" in text:
        return "submission"
    if "DEC" in text:
        return "decision"
    return "other"

def _fighter_result(fight: dict[str, Any], fighter_id: str) -> str:
    winner = fight.get("winner_id")
    result = str(fight.get("result") or "").casefold()
    if winner == fighter_id:
        return "win"
    if winner:
        return "loss"
    if "draw" in result:
        return "draw"
    if "no contest" in result or result in {"nc", "no_contest"}:
        return "no_contest"
    return "unknown"

def _row_sort_round(row: dict[str, Any]) -> tuple[int, str]:
    round_no = row.get("round")
    return (int(round_no) if round_no is not None else 999, str(row))

def _safe_round_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Canonical round zero is forbidden; fail closed even if a malformed source appears.
    return sorted(
        [copy.deepcopy(row) for row in rows if row.get("round") is not None and int(row["round"]) >= 1],
        key=_row_sort_round,
    )

def _nullable_metric_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [row.get(field) for row in rows]
    observed = [value for value in values if value is not None]
    return {
        "sum": sum(observed) if observed else None,
        "observed_rounds": len(observed),
        "total_rounds": len(rows),
    }

def _age_on(dob_value: str | None, cutoff: datetime) -> int | None:
    if not dob_value:
        return None
    dob = _parse_date(dob_value)
    on = cutoff.date()
    if on < dob:
        return None
    return on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))

def _substantive_hash(packet: dict[str, Any]) -> str:
    payload = copy.deepcopy(packet)

    def scrub(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("generated_at_utc", None)
            value.pop("substantive_sha256", None)
            for child in value.values():
                scrub(child)
        elif isinstance(value, list):
            for child in value:
                scrub(child)

    scrub(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

def _now() -> datetime:
    return datetime.now(timezone.utc)

def build_fighter_index(
    store: CanonicalStore,
    *,
    generated_at: datetime | None = None,
    generator_commit_sha: str | None = None,
) -> dict[str, Any]:
    store.ensure_indexes()
    generated_at = generated_at or _now()
    generator_commit_sha = generator_commit_sha if generator_commit_sha is not None else generator_commit(store.root)
    exact_lookup: dict[str, list[str]] = {}
    normalized_lookup: dict[str, list[str]] = {}

    from .store import normalize_lookup_text

    entries: list[dict[str, Any]] = []
    for fighter_id in sorted(store.fighters_by_id):
        row = store.fighters_by_id[fighter_id]
        canonical_name = str(row["canonical_name"])
        aliases = store.trusted_aliases(fighter_id)
        links = store.trusted_fighter_links(fighter_id)
        urls = sorted(
            {
                str(link.get("source_url") or link.get("source_id"))
                for link in links
                if str(link.get("source_url") or link.get("source_id") or "").startswith(("http://", "https://"))
            }
        )
        ufcstats_url = next(
            (
                url
                for url in urls
                if "ufcstats.com" in url.casefold()
            ),
            None,
        )
        entries.append(
            {
                "canonical_fighter_id": fighter_id,
                "canonical_name": canonical_name,
                "trusted_aliases": aliases,
                "ufcstats_url": ufcstats_url,
                "trusted_source_links": links,
            }
        )
        for name in [canonical_name, *aliases]:
            exact_lookup.setdefault(name, []).append(fighter_id)
            normalized_lookup.setdefault(normalize_lookup_text(name), []).append(fighter_id)

    packet = {
        "metadata": {
            **store.metadata(
                cutoff=generated_at,
                generated_at=generated_at,
                generator_commit=generator_commit_sha,
            ),
            "artifact_type": "fighter_index",
            "lookup_rule": (
                "canonical ID, exact canonical/trusted alias, then unique normalized text; "
                "ambiguous/unknown names fail closed; no fuzzy identity guessing"
            ),
        },
        "fighters": entries,
        "lookup": {
            "exact": {key: sorted(value) for key, value in sorted(exact_lookup.items())},
            "normalized": {key: sorted(value) for key, value in sorted(normalized_lookup.items())},
        },
    }
    packet["substantive_sha256"] = _substantive_hash(packet)
    return packet

def _fight_context(
    store: CanonicalStore,
    fight: dict[str, Any],
    fighter_id: str,
    cutoff: datetime,
) -> dict[str, Any]:
    event = store.events_by_id.get(fight["event_id"])
    opponent_id = (
        fight["fighter_b_id"]
        if fight["fighter_a_id"] == fighter_id
        else fight["fighter_a_id"]
    )
    opponent = store.fighters_by_id.get(opponent_id)

    fighter_stats = _safe_round_rows(store.stats_by_fight_fighter.get((fight["fight_id"], fighter_id), []))
    opponent_stats = _safe_round_rows(store.stats_by_fight_fighter.get((fight["fight_id"], opponent_id), []))
    fighter_position = _safe_round_rows(store.position_by_fight_fighter.get((fight["fight_id"], fighter_id), []))
    opponent_position = _safe_round_rows(store.position_by_fight_fighter.get((fight["fight_id"], opponent_id), []))

    weigh_ins: list[dict[str, Any]] = []
    for participant_id in (fighter_id, opponent_id):
        for row in store.weigh_ins_by_fight_fighter.get((fight["fight_id"], participant_id), []):
            if _weigh_in_safe(row, fight, event, cutoff):
                enriched = copy.deepcopy(row)
                enriched["canonical_fighter_name"] = store.canonical_name(participant_id)
                weigh_ins.append(enriched)
    weigh_ins.sort(
        key=lambda r: (
            str(r.get("weigh_in_date") or ""),
            str(r.get("fighter_id") or ""),
            str(r.get("weigh_in_observation_id") or ""),
        )
    )

    return {
        "canonical_fight": copy.deepcopy(fight),
        "event": copy.deepcopy(event),
        "fighter_id": fighter_id,
        "fighter_name": store.canonical_name(fighter_id),
        "opponent_id": opponent_id,
        "opponent_name": opponent.get("canonical_name") if opponent else None,
        "fighter_result": _fighter_result(fight, fighter_id),
        "fighter_round_stats": fighter_stats,
        "opponent_round_stats": opponent_stats,
        "fighter_round_position": fighter_position,
        "opponent_round_position": opponent_position,
        "weigh_ins": weigh_ins,
        "provenance_key": {
            "table_name": "fights",
            "row_key": str(fight["fight_id"]),
        },
    }

def _descriptive_summary(history: list[dict[str, Any]]) -> dict[str, Any]:
    results = Counter(item["fighter_result"] for item in history)
    promotions = [str((item.get("event") or {}).get("promotion") or "") for item in history]
    ufc_count = sum(1 for promotion in promotions if promotion.upper() == "UFC")
    fighter_round_rows = [
        row
        for item in history
        for row in item.get("fighter_round_stats", [])
    ]
    opponent_round_rows = [
        row
        for item in history
        for row in item.get("opponent_round_stats", [])
    ]

    win_methods = Counter()
    loss_methods = Counter()
    for item in history:
        method = (item["canonical_fight"] or {}).get("method")
        group = _method_group(method)
        if item["fighter_result"] == "win":
            win_methods[group] += 1
        elif item["fighter_result"] == "loss":
            loss_methods[group] += 1

    most_recent = history[0] if history else None
    stat_totals = {
        field: {
            "created": _nullable_metric_summary(fighter_round_rows, field),
            "suffered": _nullable_metric_summary(opponent_round_rows, field),
        }
        for field in SUMMARY_STAT_FIELDS
    }
    def compact_fight(item: dict[str, Any]) -> dict[str, Any]:
        fight = item["canonical_fight"]
        event = item.get("event") or {}
        return {
            "fight_id": fight.get("fight_id"),
            "event_date": event.get("event_date"),
            "opponent_id": item.get("opponent_id"),
            "opponent_name": item.get("opponent_name"),
            "result": item.get("fighter_result"),
            "method": fight.get("method"),
            "finish_round": fight.get("finish_round"),
            "finish_time_sec": fight.get("finish_time_sec"),
            "promotion": event.get("promotion"),
        }

    return {
        "observed_total_fights": len(history),
        "observed_ufc_fights": ufc_count,
        "observed_external_fights": len(history) - ufc_count,
        "results": dict(sorted(results.items())),
        "method_results": {
            "wins": dict(sorted(win_methods.items())),
            "losses": dict(sorted(loss_methods.items())),
        },
        "total_observed_round_rows": len(fighter_round_rows),
        "most_recent_fight": compact_fight(most_recent) if most_recent else None,
        "last_3_fights": [compact_fight(item) for item in history[:3]],
        "last_5_fights": [compact_fight(item) for item in history[:5]],
        "round_stat_totals": stat_totals,
    }

def build_fighter_dossier(
    store: CanonicalStore,
    fighter: str,
    cutoff: str | datetime | date,
    *,
    generated_at: datetime | None = None,
    generator_commit_sha: str | None = None,
) -> dict[str, Any]:
    store.ensure_indexes()
    cutoff_dt = parse_cutoff(cutoff)
    generated_at = generated_at or _now()
    generator_commit_sha = generator_commit_sha if generator_commit_sha is not None else generator_commit(store.root)
    fighter_id = store.resolve_fighter(fighter)
    fighter_row = copy.deepcopy(store.fighters_by_id[fighter_id])

    eligible_fights: list[tuple[str, str, dict[str, Any]]] = []
    for fight in store.fights_by_fighter.get(fighter_id, []):
        event = store.events_by_id.get(fight.get("event_id"))
        if event and _event_before_cutoff(event, cutoff_dt):
            eligible_fights.append(
                (str(event.get("event_date") or ""), str(fight["fight_id"]), fight)
            )
    eligible_fights.sort(key=lambda x: (x[0], x[1]), reverse=True)
    history = [_fight_context(store, fight, fighter_id, cutoff_dt) for _, _, fight in eligible_fights]

    rankings = [
        copy.deepcopy(row)
        for row in store.rankings_by_fighter.get(fighter_id, [])
        if row.get("ranking_date")
        and _parse_date(str(row["ranking_date"])) < cutoff_dt.date()
    ]
    rankings.sort(
        key=lambda r: (
            str(r.get("ranking_date") or ""),
            str(r.get("weight_class") or ""),
            str(r.get("ranking_body") or ""),
        ),
        reverse=True,
    )

    profiles = [
        copy.deepcopy(row)
        for row in store.profiles_by_fighter.get(fighter_id, [])
        if row.get("observed_at_utc")
        and _parse_timestamp(str(row["observed_at_utc"])) <= cutoff_dt
    ]
    profiles.sort(key=lambda r: str(r.get("observed_at_utc") or ""), reverse=True)

    safe_weigh_ins: list[dict[str, Any]] = []
    for (fight_id, candidate_id), rows in store.weigh_ins_by_fight_fighter.items():
        if candidate_id != fighter_id:
            continue
        fight = store.fights_by_id.get(fight_id)
        event = store.events_by_id.get(fight.get("event_id")) if fight else None
        for row in rows:
            if _weigh_in_safe(row, fight, event, cutoff_dt):
                enriched = copy.deepcopy(row)
                enriched["event"] = copy.deepcopy(event)
                safe_weigh_ins.append(enriched)
    safe_weigh_ins.sort(
        key=lambda r: (
            str(r.get("weigh_in_date") or ""),
            str((r.get("event") or {}).get("event_date") or ""),
            str(r.get("weigh_in_observation_id") or ""),
        ),
        reverse=True,
    )

    physical = copy.deepcopy(fighter_row)
    physical["age_as_of_cutoff"] = _age_on(
        str(fighter_row.get("dob")) if fighter_row.get("dob") else None,
        cutoff_dt,
    )

    warnings = list(BASE_WARNINGS)
    if not history:
        warnings.append("No canonical pre-cutoff fight history is available for this fighter.")
    if not rankings:
        warnings.append("No canonical pre-cutoff ranking observations are available for this fighter.")
    if not safe_weigh_ins:
        warnings.append("No canonically time-safe fight-specific weigh-ins are available before this cutoff.")
    if not profiles:
        warnings.append("No canonical profile snapshots are available at or before this cutoff.")
    if not any(item["fighter_round_position"] for item in history):
        warnings.append("No eligible canonical positional/TIP round evidence is available in this dossier.")

    packet = {
        "metadata": {
            **store.metadata(cutoff_dt, generated_at, generator_commit_sha),
            "artifact_type": "fighter_dossier",
            "canonical_fighter_id": fighter_id,
            "canonical_fighter_name": fighter_row["canonical_name"],
            "warnings": warnings,
        },
        "fighter": {
            "identity_physical_context": physical,
            "trusted_source_identity_links": store.trusted_fighter_links(fighter_id),
            "trusted_aliases": store.trusted_aliases(fighter_id),
        },
        "descriptive_summary": _descriptive_summary(history),
        "fight_history": history,
        "ranking_history": rankings,
        "weigh_in_history": safe_weigh_ins,
        "profile_snapshots": profiles,
    }
    packet["substantive_sha256"] = _substantive_hash(packet)
    return packet

def build_matchup_packet(
    store: CanonicalStore,
    fighter_a: str,
    fighter_b: str,
    cutoff: str | datetime | date,
    *,
    generated_at: datetime | None = None,
    generator_commit_sha: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or _now()
    generator_commit_sha = generator_commit_sha if generator_commit_sha is not None else generator_commit(store.root)
    a = build_fighter_dossier(
        store, fighter_a, cutoff, generated_at=generated_at, generator_commit_sha=generator_commit_sha
    )
    b = build_fighter_dossier(
        store, fighter_b, cutoff, generated_at=generated_at, generator_commit_sha=generator_commit_sha
    )
    a_id = a["metadata"]["canonical_fighter_id"]
    b_id = b["metadata"]["canonical_fighter_id"]
    if a_id == b_id:
        raise ValueError("matchup requires two distinct canonical fighter identities")

    a_by_fight = {item["canonical_fight"]["fight_id"]: item for item in a["fight_history"]}
    b_by_fight = {item["canonical_fight"]["fight_id"]: item for item in b["fight_history"]}
    direct_ids = sorted(
        set(a_by_fight).intersection(b_by_fight),
        key=lambda fight_id: (
            str((a_by_fight[fight_id].get("event") or {}).get("event_date") or ""),
            fight_id,
        ),
        reverse=True,
    )
    direct = [copy.deepcopy(a_by_fight[fight_id]) for fight_id in direct_ids]

    opponent_map: dict[str, dict[str, Any]] = {}
    for owner_id, dossier in ((a_id, a), (b_id, b)):
        for item in dossier["fight_history"]:
            opponent_id = item["opponent_id"]
            entry = opponent_map.setdefault(
                opponent_id,
                {
                    "canonical_opponent_id": opponent_id,
                    "name": item["opponent_name"],
                    "faced_by": set(),
                    "meetings": [],
                    "optional_dossier_path": f"handicap/v0/fighters/{opponent_id}.json",
                },
            )
            entry["faced_by"].add(owner_id)
            fight = item["canonical_fight"]
            event = item.get("event") or {}
            entry["meetings"].append(
                {
                    "fighter_id": owner_id,
                    "fight_id": fight.get("fight_id"),
                    "event_id": fight.get("event_id"),
                    "event_date": event.get("event_date"),
                    "promotion": event.get("promotion"),
                    "result": item.get("fighter_result"),
                    "method": fight.get("method"),
                    "finish_round": fight.get("finish_round"),
                    "finish_time_sec": fight.get("finish_time_sec"),
                }
            )
    opponents: list[dict[str, Any]] = []
    for opponent_id in sorted(opponent_map):
        entry = opponent_map[opponent_id]
        entry["faced_by"] = sorted(entry["faced_by"])
        entry["meetings"].sort(
            key=lambda row: (str(row.get("event_date") or ""), str(row.get("fight_id") or "")),
            reverse=True,
        )
        opponents.append(entry)

    cutoff_dt = parse_cutoff(cutoff)
    warnings = sorted(
        set(a["metadata"]["warnings"]).union(b["metadata"]["warnings"])
    )
    packet = {
        "metadata": {
            **store.metadata(cutoff_dt, generated_at, generator_commit_sha),
            "artifact_type": "matchup_packet",
            "fighter_a": {"id": a_id, "name": a["metadata"]["canonical_fighter_name"]},
            "fighter_b": {"id": b_id, "name": b["metadata"]["canonical_fighter_name"]},
            "warnings": warnings,
        },
        "fighter_a": a,
        "fighter_b": b,
        "direct_prior_meetings": direct,
        "opponent_index": opponents,
    }
    packet["substantive_sha256"] = _substantive_hash(packet)
    return packet

def write_json(packet: dict[str, Any], path: Path, *, pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        packet,
        ensure_ascii=False,
        sort_keys=True,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    )
    path.write_text(text + "\n", encoding="utf-8")

def packet_output_guard(root: Path, output: Path) -> Path:
    handicap_root = (root / "handicap").resolve()
    resolved = output.resolve()
    if resolved != handicap_root and handicap_root not in resolved.parents:
        raise ValueError(f"default H00 output must remain beneath {handicap_root}")
    return resolved
