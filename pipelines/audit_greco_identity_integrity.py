#!/usr/bin/env python3
"""Audit whether Greco raw tables can be joined to stable source identities safely.

This is an internal-source reconciliation audit, not global canonical identity matching.
It proves where display names/event+bout keys uniquely resolve to Greco/UFCStats URLs and
lists every ambiguity/unmatched key. Adapters may only promote the audited unique cases.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path("data/raw/greco1899/8e40eb945e11")
OUT = Path("provenance/audits/greco_identity_integrity.json")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rows(name: str) -> list[dict[str, str]]:
    path = ROOT / name
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(text: str | None) -> str:
    return " ".join((text or "").split())


def multi_map(items: Iterable[tuple[str, str]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for key, value in items:
        if key and value:
            out[key].add(value)
    return out


def ambiguous(mapping: dict[str, set[str]]) -> dict[str, list[str]]:
    return {k: sorted(v) for k, v in mapping.items() if len(v) != 1}


def fight_key(row: dict[str, str]) -> str:
    return f"{norm(row.get('EVENT'))} || {norm(row.get('BOUT'))}"


def main() -> int:
    fighter_details = rows("ufc_fighter_details.csv")
    fighter_tott = rows("ufc_fighter_tott.csv")
    fight_details = rows("ufc_fight_details.csv")
    fight_results = rows("ufc_fight_results.csv")
    fight_stats = rows("ufc_fight_stats.csv")

    tott_name_to_urls = multi_map(
        (norm(r.get("FIGHTER")), norm(r.get("URL"))) for r in fighter_tott
    )
    detail_name_to_urls = multi_map(
        (norm(f"{r.get('FIRST','')} {r.get('LAST','')}"), norm(r.get("URL"))) for r in fighter_details
    )
    fight_key_to_urls = multi_map(
        (fight_key(r), norm(r.get("URL"))) for r in fight_details
    )
    result_key_to_urls = multi_map(
        (fight_key(r), norm(r.get("URL"))) for r in fight_results
    )

    stat_names = sorted({norm(r.get("FIGHTER")) for r in fight_stats if norm(r.get("FIGHTER"))})
    stat_keys = sorted({fight_key(r) for r in fight_stats})

    unmatched_tott = [name for name in stat_names if name not in tott_name_to_urls]
    unmatched_details = [name for name in stat_names if name not in detail_name_to_urls]
    ambiguous_tott_for_stats = {
        name: sorted(tott_name_to_urls[name])
        for name in stat_names
        if name in tott_name_to_urls and len(tott_name_to_urls[name]) != 1
    }
    ambiguous_details_for_stats = {
        name: sorted(detail_name_to_urls[name])
        for name in stat_names
        if name in detail_name_to_urls and len(detail_name_to_urls[name]) != 1
    }

    source_disagreements = []
    for name in stat_names:
        a = tott_name_to_urls.get(name)
        b = detail_name_to_urls.get(name)
        if a and b and len(a) == 1 and len(b) == 1 and a != b:
            source_disagreements.append({"fighter": name, "tott_urls": sorted(a), "detail_urls": sorted(b)})

    unmatched_fight_details = [key for key in stat_keys if key not in fight_key_to_urls]
    ambiguous_fight_details = {
        key: sorted(fight_key_to_urls[key])
        for key in stat_keys
        if key in fight_key_to_urls and len(fight_key_to_urls[key]) != 1
    }
    missing_result_keys = [key for key in stat_keys if key not in result_key_to_urls]

    # Audit per-fight and per-round participant cardinality directly from stats; do not
    # parse participant names out of BOUT text.
    fight_fighters: dict[str, set[str]] = defaultdict(set)
    round_fighters: dict[tuple[str, str], set[str]] = defaultdict(set)
    duplicate_stat_rows: Counter[tuple[str, str, str]] = Counter()
    for r in fight_stats:
        key = fight_key(r)
        fighter = norm(r.get("FIGHTER"))
        round_label = norm(r.get("ROUND"))
        fight_fighters[key].add(fighter)
        round_fighters[(key, round_label)].add(fighter)
        duplicate_stat_rows[(key, round_label, fighter)] += 1

    fight_participant_anomalies = {
        key: sorted(names) for key, names in fight_fighters.items() if len(names) != 2
    }
    round_participant_anomalies = [
        {"fight_key": key, "round": rnd, "fighters": sorted(names), "fighter_count": len(names)}
        for (key, rnd), names in round_fighters.items()
        if len(names) != 2
    ]
    duplicate_fighter_round_rows = [
        {"fight_key": key, "round": rnd, "fighter": fighter, "rows": count}
        for (key, rnd, fighter), count in duplicate_stat_rows.items()
        if count != 1
    ]

    payload = {
        "schema_version": 1,
        "audited_at_utc": now(),
        "source_root": ROOT.as_posix(),
        "row_counts": {
            "fighter_details": len(fighter_details),
            "fighter_tott": len(fighter_tott),
            "fight_details": len(fight_details),
            "fight_results": len(fight_results),
            "fight_stats": len(fight_stats),
        },
        "fighter_identity": {
            "distinct_stat_fighter_names": len(stat_names),
            "tott_distinct_names": len(tott_name_to_urls),
            "details_distinct_names": len(detail_name_to_urls),
            "tott_ambiguous_name_count_all": len(ambiguous(tott_name_to_urls)),
            "details_ambiguous_name_count_all": len(ambiguous(detail_name_to_urls)),
            "stat_names_unmatched_to_tott": unmatched_tott,
            "stat_names_unmatched_to_details": unmatched_details,
            "stat_names_ambiguous_in_tott": ambiguous_tott_for_stats,
            "stat_names_ambiguous_in_details": ambiguous_details_for_stats,
            "unique_source_url_disagreements_between_tott_and_details": source_disagreements,
        },
        "fight_identity": {
            "distinct_stat_fight_keys": len(stat_keys),
            "fight_detail_distinct_keys": len(fight_key_to_urls),
            "fight_result_distinct_keys": len(result_key_to_urls),
            "fight_detail_ambiguous_key_count_all": len(ambiguous(fight_key_to_urls)),
            "fight_result_ambiguous_key_count_all": len(ambiguous(result_key_to_urls)),
            "stat_fight_keys_unmatched_to_fight_details": unmatched_fight_details,
            "stat_fight_keys_ambiguous_in_fight_details": ambiguous_fight_details,
            "stat_fight_keys_missing_from_results": missing_result_keys,
        },
        "round_integrity": {
            "fight_participant_anomaly_count": len(fight_participant_anomalies),
            "fight_participant_anomalies": fight_participant_anomalies,
            "round_participant_anomaly_count": len(round_participant_anomalies),
            "round_participant_anomalies": round_participant_anomalies[:200],
            "duplicate_fighter_round_row_count": len(duplicate_fighter_round_rows),
            "duplicate_fighter_round_rows": duplicate_fighter_round_rows[:200],
        },
        "adapter_gate": {
            "fight_url_join_requires_unique_event_bout_key": True,
            "fighter_url_join_requires_unique_name_within_pinned_source": True,
            "display_name_only_is_not_global_canonical_identity": True,
            "fail_closed_on_listed_ambiguities": True,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "GRECO_IDENTITY_AUDIT_OK "
        f"stat_fighters={len(stat_names)} unmatched_tott={len(unmatched_tott)} "
        f"ambiguous_tott={len(ambiguous_tott_for_stats)} fight_keys={len(stat_keys)} "
        f"unmatched_fights={len(unmatched_fight_details)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
