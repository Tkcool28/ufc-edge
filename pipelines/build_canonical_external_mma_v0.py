#!/usr/bin/env python3
"""Materialize audited Bellator/ONE history into canonical v0.

DATA PHASE ONLY.

This builder is intentionally fail-closed:
- external data never repairs or overwrites UFC-labelled canonical history;
- both source fighter URLs must have trusted canonical mappings;
- the audited duplicate (event URL, match_nr) key is quarantined;
- same trusted participant pairs within +/-1 day of an existing canonical UFC fight are
  treated as UFC overlap and excluded;
- display names are never used for trusted identity;
- scheduled rounds, weight class, title-bout state, and round statistics are never invented.

The pinned readiness audit must continue to prove exactly 483 contract-ready fights across
230 non-UFC events before this builder will write anything.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data/canonical/v0"
RAW = ROOT / "data/raw/kaggle_pro_mma_fights/v1/pro_mma_fights.csv"
XWALK = ROOT / "data/derived/identity/external_mma_canonical_crosswalk_candidate.csv"
READINESS = ROOT / "provenance/audits/external_mma_canonical_readiness_latest.json"
CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
EVENTS = CANON / "events.csv"
FIGHTS = CANON / "fights.csv"
IDENTITY = CANON / "source_identity_links.csv"
PROVENANCE = CANON / "field_provenance.csv"
MANIFEST = CANON / "manifest.json"
EXCLUSIONS = ROOT / "data/derived/qa/canonical_external_mma_exclusions_v0.csv"
AUDIT_JSON = ROOT / "provenance/audits/canonical_external_mma_v0_latest.json"
AUDIT_MD = ROOT / "provenance/audits/canonical_external_mma_v0_latest.md"

PROJECT_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL,
    "https://github.com/Tkcool28/ufc-edge/canonical/v1",
)
SOURCE_FIGHTS = "kaggle_pro_mma_fights"
SOURCE_FIGHTERS = "kaggle_pro_mma_fighters"
SOURCE_SNAPSHOT = "v1"
UFC_ORG = "Ultimate Fighting Championship (UFC)"

EVENT_FIELDS = [
    "event_id", "promotion", "event_name", "event_date", "event_start_utc", "location"
]
FIGHT_FIELDS = [
    "fight_id", "event_id", "fighter_a_id", "fighter_b_id", "winner_id", "result",
    "method", "finish_round", "finish_time_sec", "scheduled_rounds", "weight_class",
    "title_bout", "promotion",
]
IDENTITY_FIELDS = [
    "entity_type", "canonical_id", "source_name", "source_entity_type", "source_id",
    "source_url", "match_method", "match_confidence", "review_status", "valid_from",
    "valid_to",
]
PROVENANCE_FIELDS = [
    "table_name", "row_key", "field_name", "source_name", "source_snapshot_id",
    "source_record_id", "source_field_name", "selection_status", "selection_rule",
    "quality_note",
]
EXCLUSION_FIELDS = [
    "source_event_url", "source_match_nr", "source_organisation", "source_event_title",
    "fighter1_name", "fighter2_name", "reason", "details",
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = list(reader.fieldnames or [])
        return fields, list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field) for field in fields})


def mint_id(entity_type: str, source_name: str, source_id: str) -> str:
    return str(uuid.uuid5(PROJECT_NAMESPACE, f"{entity_type}|{source_name}|{source_id.strip()}"))


def parse_source_date(value: str) -> str:
    return datetime.strptime((value or "").strip(), "%b %d, %Y").date().isoformat()


def parse_finish_time(value: str) -> int:
    text = (value or "").strip()
    match = re.fullmatch(r"(\d+):(\d{2})", text)
    if not match or int(match.group(2)) >= 60:
        raise RuntimeError(f"eligible source finish time no longer matches audited M:SS: {value!r}")
    return int(match.group(1)) * 60 + int(match.group(2))


def normalize_method(value: str) -> str:
    text = (value or "").strip().lower()
    mapping = {
        "ko": "KO_TKO",
        "tko": "KO_TKO",
        "submission": "SUBMISSION",
        "technical submission": "SUBMISSION",
        "verbal submission": "SUBMISSION",
        "decision": "DECISION",
        "disqualification": "DQ",
        "draw": "DRAW",
        "no contest": "NO_CONTEST",
        "nc": "NO_CONTEST",
    }
    if text not in mapping:
        raise RuntimeError(f"eligible source method is no longer explicitly mapped: {value!r}")
    return mapping[text]


def result_semantics(
    fighter1_result: str,
    fighter2_result: str,
    fighter1_id: str,
    fighter2_id: str,
) -> tuple[str | None, str]:
    pair = ((fighter1_result or "").strip().lower(), (fighter2_result or "").strip().lower())
    if pair == ("win", "loss"):
        return fighter1_id, "win_loss"
    if pair == ("loss", "win"):
        return fighter2_id, "win_loss"
    if pair == ("draw", "draw"):
        return None, "draw"
    if pair == ("nc", "nc"):
        return None, "no_contest"
    raise RuntimeError(f"eligible source result pair is no longer explicitly mapped: {pair!r}")


def string_row(row: dict[str, Any], fields: list[str]) -> dict[str, str]:
    return {field: "" if row.get(field) is None else str(row.get(field)) for field in fields}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_header(label: str, actual: list[str], expected: list[str]) -> None:
    if actual != expected:
        raise RuntimeError(f"{label} header drift: actual={actual!r} expected={expected!r}")


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    if readiness.get("contract_ready_fight_rows") != 483:
        raise RuntimeError("readiness audit no longer proves exactly 483 contract-ready fights")
    if readiness.get("eligible_distinct_event_urls") != 230:
        raise RuntimeError("readiness audit no longer proves exactly 230 eligible event URLs")
    failures = readiness.get("semantic_gate_failures") or {}
    required_clean = (
        "unknown_result_rows",
        "round_outside_contract_1_to_10_rows",
        "invalid_time_mmss_rows",
    )
    if any(failures.get(name) != 0 for name in required_clean):
        raise RuntimeError(f"readiness semantic gate is no longer clean: {failures}")
    if manifest.get("canonical_contract_version") != contract.get("contract_version"):
        raise RuntimeError(
            "canonical manifest contract version does not match current contract after exact workflow migration"
        )

    raw_fields, raw_rows = read_csv(RAW)
    xwalk_fields, xwalk_rows = read_csv(XWALK)
    event_fields, current_events = read_csv(EVENTS)
    fight_fields, current_fights = read_csv(FIGHTS)
    identity_fields, current_identity = read_csv(IDENTITY)
    provenance_fields, current_provenance = read_csv(PROVENANCE)

    required_raw = {
        "url", "event_title", "organisation", "date", "location", "match_nr",
        "fighter1_url", "fighter2_url", "fighter1_name", "fighter2_name",
        "fighter1_result", "fighter2_result", "win_method", "round", "time",
    }
    required_xwalk = {
        "external_fighter_url", "canonical_fighter_id", "match_method",
        "match_confidence", "review_status",
    }
    if not required_raw.issubset(raw_fields):
        raise RuntimeError(f"external fight source header drift: missing={sorted(required_raw - set(raw_fields))}")
    if not required_xwalk.issubset(xwalk_fields):
        raise RuntimeError(f"external fighter crosswalk header drift: missing={sorted(required_xwalk - set(xwalk_fields))}")
    assert_header("events", event_fields, EVENT_FIELDS)
    assert_header("fights", fight_fields, FIGHT_FIELDS)
    assert_header("source_identity_links", identity_fields, IDENTITY_FIELDS)
    assert_header("field_provenance", provenance_fields, PROVENANCE_FIELDS)

    trusted_by_url: dict[str, dict[str, str]] = {}
    for row in xwalk_rows:
        if (row.get("review_status") or "").strip() != "trusted":
            continue
        url = (row.get("external_fighter_url") or "").strip()
        fighter_id = (row.get("canonical_fighter_id") or "").strip()
        if not url or not fighter_id:
            continue
        prior = trusted_by_url.get(url)
        if prior and (prior.get("canonical_fighter_id") or "").strip() != fighter_id:
            raise RuntimeError(f"trusted external fighter URL maps to multiple canonical IDs: {url}")
        trusted_by_url[url] = row

    ufc_event_date = {
        (row.get("event_id") or "").strip(): (row.get("event_date") or "").strip()
        for row in current_events
        if (row.get("promotion") or "").strip() == "UFC"
    }
    ufc_fights_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in current_fights:
        if (row.get("promotion") or "").strip() != "UFC":
            continue
        fighter_a = (row.get("fighter_a_id") or "").strip()
        fighter_b = (row.get("fighter_b_id") or "").strip()
        if fighter_a and fighter_b and fighter_a != fighter_b:
            ufc_fights_by_pair[tuple(sorted((fighter_a, fighter_b)))].append(row)

    source_key_counts = Counter(
        ((row.get("url") or "").strip(), (row.get("match_nr") or "").strip())
        for row in raw_rows
    )
    duplicate_source_keys = {key for key, count in source_key_counts.items() if count > 1}

    generated_events_by_url: dict[str, dict[str, Any]] = {}
    generated_fights: list[dict[str, Any]] = []
    promoted: list[tuple[dict[str, str], str, str, str, str]] = []
    exclusions: list[dict[str, str]] = []
    exclusion_counts: Counter[str] = Counter()

    def exclude(row: dict[str, str], reason: str, details: str = "") -> None:
        exclusion_counts[reason] += 1
        exclusions.append({
            "source_event_url": (row.get("url") or "").strip(),
            "source_match_nr": (row.get("match_nr") or "").strip(),
            "source_organisation": (row.get("organisation") or "").strip(),
            "source_event_title": (row.get("event_title") or "").strip(),
            "fighter1_name": (row.get("fighter1_name") or "").strip(),
            "fighter2_name": (row.get("fighter2_name") or "").strip(),
            "reason": reason,
            "details": details,
        })

    for source in raw_rows:
        organisation = (source.get("organisation") or "").strip()
        event_url = (source.get("url") or "").strip()
        match_nr = (source.get("match_nr") or "").strip()
        source_key = (event_url, match_nr)

        if organisation == UFC_ORG:
            exclude(
                source,
                "ufc_label_excluded_lower_precedence",
                "lower-precedence external source is never used to repair/overwrite UFC canonical history",
            )
            continue
        if source_key in duplicate_source_keys:
            exclude(
                source,
                "duplicate_source_fight_key_quarantine",
                "audited duplicate (source event URL, match_nr) key",
            )
            continue

        mapping1 = trusted_by_url.get((source.get("fighter1_url") or "").strip())
        mapping2 = trusted_by_url.get((source.get("fighter2_url") or "").strip())
        fighter1_id = (mapping1.get("canonical_fighter_id") or "").strip() if mapping1 else ""
        fighter2_id = (mapping2.get("canonical_fighter_id") or "").strip() if mapping2 else ""
        if not fighter1_id or not fighter2_id or fighter1_id == fighter2_id:
            exclude(
                source,
                "unresolved_trusted_fighter_identity",
                f"fighter1_trusted={bool(fighter1_id)};fighter2_trusted={bool(fighter2_id)}",
            )
            continue

        source_date = parse_source_date(source.get("date") or "")
        pair = tuple(sorted((fighter1_id, fighter2_id)))
        if pair in ufc_fights_by_pair:
            source_day = datetime.fromisoformat(source_date).date()
            deltas: list[int] = []
            for canonical_fight in ufc_fights_by_pair[pair]:
                canonical_date = ufc_event_date.get((canonical_fight.get("event_id") or "").strip(), "")
                if canonical_date:
                    deltas.append((source_day - datetime.fromisoformat(canonical_date).date()).days)
            if deltas:
                nearest_delta = min(deltas, key=lambda value: (abs(value), value))
                if abs(nearest_delta) <= 1:
                    exclude(
                        source,
                        "canonical_ufc_overlap_pair_within_one_day",
                        f"nearest_source_minus_canonical_days={nearest_delta}",
                    )
                    continue

        finish_round = int((source.get("round") or "").strip())
        if not 1 <= finish_round <= 10:
            raise RuntimeError(f"readiness drift: eligible finish round outside contract: {finish_round}")
        finish_time_sec = parse_finish_time(source.get("time") or "")
        winner_id, result = result_semantics(
            source.get("fighter1_result") or "",
            source.get("fighter2_result") or "",
            fighter1_id,
            fighter2_id,
        )
        method = normalize_method(source.get("win_method") or "")

        event_id = mint_id("event", SOURCE_FIGHTS, event_url)
        event_row: dict[str, Any] = {
            "event_id": event_id,
            "promotion": organisation,
            "event_name": (source.get("event_title") or "").strip(),
            "event_date": source_date,
            "event_start_utc": None,
            "location": (source.get("location") or "").strip() or None,
        }
        prior_event = generated_events_by_url.get(event_url)
        if prior_event and string_row(prior_event, EVENT_FIELDS) != string_row(event_row, EVENT_FIELDS):
            raise RuntimeError(f"eligible source event URL maps to multiple event signatures: {event_url}")
        generated_events_by_url[event_url] = event_row

        source_fight_key = f"{event_url}|{match_nr}"
        fight_id = mint_id("fight", SOURCE_FIGHTS, source_fight_key)
        fight_row: dict[str, Any] = {
            "fight_id": fight_id,
            "event_id": event_id,
            "fighter_a_id": fighter1_id,
            "fighter_b_id": fighter2_id,
            "winner_id": winner_id,
            "result": result,
            "method": method,
            "finish_round": finish_round,
            "finish_time_sec": finish_time_sec,
            "scheduled_rounds": None,
            "weight_class": None,
            "title_bout": None,
            "promotion": organisation,
        }
        generated_fights.append(fight_row)
        promoted.append((source, fighter1_id, fighter2_id, event_id, fight_id))

    generated_events = sorted(generated_events_by_url.values(), key=lambda row: str(row["event_id"]))
    generated_fights.sort(key=lambda row: str(row["fight_id"]))
    exclusions.sort(
        key=lambda row: (
            row["source_event_url"], row["source_match_nr"], row["fighter1_name"], row["fighter2_name"]
        )
    )

    if len(generated_events) != 230 or len(generated_fights) != 483:
        raise RuntimeError(
            f"materialization gate drift: events={len(generated_events)} fights={len(generated_fights)}"
        )
    if len(exclusions) != len(raw_rows) - len(generated_fights):
        raise RuntimeError(
            f"raw accounting mismatch: raw={len(raw_rows)} promoted={len(generated_fights)} exclusions={len(exclusions)}"
        )
    expected_exclusions = {
        "ufc_label_excluded_lower_precedence": 6212,
        "unresolved_trusted_fighter_identity": 3751,
        "duplicate_source_fight_key_quarantine": 2,
    }
    for reason, expected in expected_exclusions.items():
        if exclusion_counts.get(reason) != expected:
            raise RuntimeError(
                f"readiness accounting drift for {reason}: {exclusion_counts.get(reason, 0)} != {expected}"
            )
    if exclusion_counts.get("canonical_ufc_overlap_pair_within_one_day", 0) != 0:
        raise RuntimeError(
            "non-UFC overlap classification changed from audited readiness; review before canonicalization"
        )

    # Desired-state append: deterministic IDs may preexist only if rows are byte-semantically identical.
    event_by_id = {(row.get("event_id") or "").strip(): row for row in current_events}
    events_added = 0
    for generated in generated_events:
        event_id = str(generated["event_id"])
        existing = event_by_id.get(event_id)
        if existing:
            if string_row(existing, EVENT_FIELDS) != string_row(generated, EVENT_FIELDS):
                raise RuntimeError(f"deterministic external event ID conflicts with existing row: {event_id}")
        else:
            current_events.append(generated)
            event_by_id[event_id] = string_row(generated, EVENT_FIELDS)
            events_added += 1

    fight_by_id = {(row.get("fight_id") or "").strip(): row for row in current_fights}
    fights_added = 0
    for generated in generated_fights:
        fight_id = str(generated["fight_id"])
        existing = fight_by_id.get(fight_id)
        if existing:
            if string_row(existing, FIGHT_FIELDS) != string_row(generated, FIGHT_FIELDS):
                raise RuntimeError(f"deterministic external fight ID conflicts with existing row: {fight_id}")
        else:
            current_fights.append(generated)
            fight_by_id[fight_id] = string_row(generated, FIGHT_FIELDS)
            fights_added += 1

    if len(current_events) != 1014 or len(current_fights) != 9252:
        raise RuntimeError(
            f"canonical totals drift: events={len(current_events)} fights={len(current_fights)} expected=1014/9252"
        )

    # Add trusted source identity links for only identities used by promoted external history.
    identity_pk: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in current_identity:
        key = (
            row.get("entity_type") or "",
            row.get("canonical_id") or "",
            row.get("source_name") or "",
            row.get("source_id") or "",
        )
        if key in identity_pk and string_row(identity_pk[key], IDENTITY_FIELDS) != string_row(row, IDENTITY_FIELDS):
            raise RuntimeError(f"conflicting existing canonical identity link: {key}")
        identity_pk[key] = row

    used_fighter_urls: dict[str, dict[str, str]] = {}
    for source, _fighter1_id, _fighter2_id, _event_id, _fight_id in promoted:
        for side in (1, 2):
            url = (source.get(f"fighter{side}_url") or "").strip()
            used_fighter_urls[url] = trusted_by_url[url]

    desired_identity: list[dict[str, Any]] = []
    for url, mapping in sorted(used_fighter_urls.items()):
        desired_identity.append({
            "entity_type": "fighter",
            "canonical_id": (mapping.get("canonical_fighter_id") or "").strip(),
            "source_name": SOURCE_FIGHTERS,
            "source_entity_type": "fighter",
            "source_id": url,
            "source_url": url,
            "match_method": (mapping.get("match_method") or "").strip(),
            "match_confidence": (mapping.get("match_confidence") or "").strip() or "1.0",
            "review_status": "trusted",
            "valid_from": None,
            "valid_to": None,
        })
    for event_url, event in sorted(generated_events_by_url.items()):
        desired_identity.append({
            "entity_type": "event",
            "canonical_id": event["event_id"],
            "source_name": SOURCE_FIGHTS,
            "source_entity_type": "event",
            "source_id": event_url,
            "source_url": event_url,
            "match_method": "stable_source_event_url",
            "match_confidence": "1.0",
            "review_status": "trusted",
            "valid_from": None,
            "valid_to": None,
        })
    for source, _fighter1_id, _fighter2_id, _event_id, fight_id in promoted:
        event_url = (source.get("url") or "").strip()
        match_nr = (source.get("match_nr") or "").strip()
        source_id = f"{event_url}|{match_nr}"
        desired_identity.append({
            "entity_type": "fight",
            "canonical_id": fight_id,
            "source_name": SOURCE_FIGHTS,
            "source_entity_type": "fight",
            "source_id": source_id,
            "source_url": event_url,
            "match_method": "stable_source_event_url_plus_match_nr",
            "match_confidence": "1.0",
            "review_status": "trusted",
            "valid_from": None,
            "valid_to": None,
        })

    identity_added = 0
    for desired in desired_identity:
        desired_string = string_row(desired, IDENTITY_FIELDS)
        key = (
            desired_string["entity_type"], desired_string["canonical_id"],
            desired_string["source_name"], desired_string["source_id"],
        )
        existing = identity_pk.get(key)
        if existing:
            if string_row(existing, IDENTITY_FIELDS) != desired_string:
                raise RuntimeError(f"external identity link conflicts with existing row: {key}")
        else:
            current_identity.append(desired)
            identity_pk[key] = desired_string
            identity_added += 1

    # Selected-field provenance is explicit for each non-null external contribution.
    provenance_pk: dict[tuple[str, str, str, str, str, str], dict[str, str]] = {}
    for row in current_provenance:
        key = tuple(row.get(field) or "" for field in PROVENANCE_FIELDS[:6])
        if key in provenance_pk and string_row(provenance_pk[key], PROVENANCE_FIELDS) != string_row(row, PROVENANCE_FIELDS):
            raise RuntimeError(f"conflicting existing field provenance row: {key}")
        provenance_pk[key] = row

    desired_provenance: list[dict[str, Any]] = []

    def add_provenance(
        table_name: str,
        row_key: str,
        field_name: str,
        source_record_id: str,
        source_field_name: str,
        selection_rule: str,
        quality_note: str | None = None,
    ) -> None:
        desired_provenance.append({
            "table_name": table_name,
            "row_key": row_key,
            "field_name": field_name,
            "source_name": SOURCE_FIGHTS,
            "source_snapshot_id": SOURCE_SNAPSHOT,
            "source_record_id": source_record_id,
            "source_field_name": source_field_name,
            "selection_status": "selected",
            "selection_rule": selection_rule,
            "quality_note": quality_note,
        })

    event_rule = "trusted_external_identity_non_ufc_overlap_dedupe"
    for event_url, event in sorted(generated_events_by_url.items()):
        event_id = str(event["event_id"])
        add_provenance(
            "events", event_id, "event_id", event_url, "url", event_rule,
            "deterministic UUIDv5 from audited stable source event URL",
        )
        add_provenance("events", event_id, "promotion", event_url, "organisation", event_rule)
        add_provenance("events", event_id, "event_name", event_url, "event_title", event_rule)
        add_provenance(
            "events", event_id, "event_date", event_url, "date", event_rule,
            "audited parser %b %d, %Y",
        )
        if event.get("location"):
            add_provenance("events", event_id, "location", event_url, "location", event_rule)

    fight_rule = "trusted_external_fighter_urls_non_ufc_overlap_dedupe"
    for source, _fighter1_id, _fighter2_id, _event_id, fight_id in promoted:
        event_url = (source.get("url") or "").strip()
        match_nr = (source.get("match_nr") or "").strip()
        source_record = f"{event_url}|{match_nr}"
        add_provenance(
            "fights", fight_id, "fight_id", source_record, "url+match_nr", fight_rule,
            "deterministic UUIDv5 from audited stable composite source key",
        )
        add_provenance("fights", fight_id, "event_id", source_record, "url", fight_rule)
        add_provenance("fights", fight_id, "fighter_a_id", source_record, "fighter1_url", fight_rule)
        add_provenance("fights", fight_id, "fighter_b_id", source_record, "fighter2_url", fight_rule)
        add_provenance(
            "fights", fight_id, "result", source_record,
            "fighter1_result+fighter2_result", fight_rule,
        )
        if (source.get("fighter1_result") or "").strip().lower() in {"win", "loss"}:
            add_provenance(
                "fights", fight_id, "winner_id", source_record,
                "fighter1_result+fighter2_result", fight_rule,
            )
        add_provenance(
            "fights", fight_id, "method", source_record, "win_method", fight_rule,
            "normalized only through explicit audited canonical method mapping",
        )
        add_provenance("fights", fight_id, "finish_round", source_record, "round", fight_rule)
        add_provenance(
            "fights", fight_id, "finish_time_sec", source_record, "time", fight_rule,
            "source M:SS converted to elapsed seconds within finish round",
        )
        add_provenance("fights", fight_id, "promotion", source_record, "organisation", fight_rule)

    provenance_added = 0
    for desired in desired_provenance:
        desired_string = string_row(desired, PROVENANCE_FIELDS)
        key = tuple(desired_string[field] for field in PROVENANCE_FIELDS[:6])
        existing = provenance_pk.get(key)
        if existing:
            if string_row(existing, PROVENANCE_FIELDS) != desired_string:
                raise RuntimeError(f"external provenance conflicts with existing row: {key}")
        else:
            current_provenance.append(desired)
            provenance_pk[key] = desired_string
            provenance_added += 1

    current_events.sort(key=lambda row: row.get("event_id") or "")
    current_fights.sort(key=lambda row: row.get("fight_id") or "")
    current_identity.sort(
        key=lambda row: tuple(row.get(field) or "" for field in ("entity_type", "canonical_id", "source_name", "source_id"))
    )
    current_provenance.sort(
        key=lambda row: tuple(
            row.get(field) or ""
            for field in ("table_name", "row_key", "field_name", "source_name", "source_snapshot_id", "source_record_id")
        )
    )

    write_csv(EVENTS, EVENT_FIELDS, current_events)
    write_csv(FIGHTS, FIGHT_FIELDS, current_fights)
    write_csv(IDENTITY, IDENTITY_FIELDS, current_identity)
    write_csv(PROVENANCE, PROVENANCE_FIELDS, current_provenance)
    write_csv(EXCLUSIONS, EXCLUSION_FIELDS, exclusions)

    promoted_organisations = Counter((source.get("organisation") or "").strip() for source, *_ in promoted)
    promoted_methods = Counter(row["method"] for row in generated_fights)
    promoted_results = Counter(row["result"] for row in generated_fights)
    if promoted_organisations != Counter({"Bellator MMA": 466, "One Championship": 17}):
        raise RuntimeError(f"promoted organisation distribution drift: {dict(promoted_organisations)}")

    audit = {
        "schema_version": 1,
        "canonical_contract_version": contract.get("contract_version"),
        "source": SOURCE_FIGHTS,
        "source_snapshot_id": SOURCE_SNAPSHOT,
        "materialized_external_events": len(generated_events),
        "materialized_external_fights": len(generated_fights),
        "events_added_this_run": events_added,
        "fights_added_this_run": fights_added,
        "canonical_events_total": len(current_events),
        "canonical_fights_total": len(current_fights),
        "promoted_organisation_counts": dict(promoted_organisations),
        "promoted_method_counts": dict(sorted(promoted_methods.items())),
        "promoted_result_counts": dict(sorted(promoted_results.items())),
        "promoted_fighter_identity_links": len(used_fighter_urls),
        "event_identity_links": len(generated_events),
        "fight_identity_links": len(generated_fights),
        "identity_links_added_this_run": identity_added,
        "materialized_field_provenance_rows": len(desired_provenance),
        "field_provenance_rows_added_this_run": provenance_added,
        "exclusions": len(exclusions),
        "exclusion_reason_counts": dict(sorted(exclusion_counts.items())),
        "rules": {
            "ufc_labelled_external_rows_promoted": False,
            "display_name_identity_used": False,
            "trusted_external_fighter_url_required_both_sides": True,
            "duplicate_source_key_quarantined": True,
            "ufc_overlap_pair_date_tolerance_days": 1,
            "scheduled_rounds_invented": False,
            "weight_class_invented": False,
            "title_bout_invented": False,
            "external_round_stats_added": False,
        },
        "outputs": {
            "events": str(EVENTS.relative_to(ROOT)),
            "fights": str(FIGHTS.relative_to(ROOT)),
            "source_identity_links": str(IDENTITY.relative_to(ROOT)),
            "field_provenance": str(PROVENANCE.relative_to(ROOT)),
            "exclusions": str(EXCLUSIONS.relative_to(ROOT)),
        },
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "# Canonical external MMA history v0\n\n"
        f"- Contract: **{contract.get('contract_version')}**\n"
        f"- External events materialized: **{len(generated_events)}**\n"
        f"- External fights materialized: **{len(generated_fights)}**\n"
        f"- Bellator fights: **{promoted_organisations['Bellator MMA']}**\n"
        f"- ONE fights: **{promoted_organisations['One Championship']}**\n"
        f"- UFC-labelled external rows promoted: **0**\n"
        f"- Excluded/quarantined raw rows: **{len(exclusions)}**\n\n"
        "Identity requires stable external fighter URLs with trusted canonical crosswalks. "
        "The external source is not used to repair or overwrite UFC canonical history.\n",
        encoding="utf-8",
    )

    # Extend the current full manifest in place; preserve rankings/profile/position additions.
    manifest["canonical_contract_version"] = contract.get("contract_version")
    manifest["generated_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    counts = manifest.setdefault("counts", {})
    counts["events"] = len(current_events)
    counts["fights"] = len(current_fights)
    counts["source_identity_links"] = len(current_identity)
    counts["field_provenance"] = len(current_provenance)
    counts["external_mma_exclusions"] = len(exclusions)
    source_snapshots = manifest.setdefault("source_snapshots", {})
    source_snapshots[SOURCE_FIGHTS] = SOURCE_SNAPSHOT
    source_snapshots[SOURCE_FIGHTERS] = SOURCE_SNAPSHOT
    rules = manifest.setdefault("rules", {})
    rules["external_mma_ufc_labelled_rows_never_repair_higher_precedence_ufc_history"] = True
    rules["external_mma_overlap_requires_trusted_pair_and_excludes_within_one_day_of_canonical_ufc_pair"] = True

    changed_paths = {
        str(EVENTS.relative_to(ROOT)),
        str(FIGHTS.relative_to(ROOT)),
        str(IDENTITY.relative_to(ROOT)),
        str(PROVENANCE.relative_to(ROOT)),
        str(EXCLUSIONS.relative_to(ROOT)),
    }
    manifest_files = [entry for entry in manifest.get("files", []) if entry.get("path") not in changed_paths]
    for path in (EVENTS, FIGHTS, IDENTITY, PROVENANCE, EXCLUSIONS):
        manifest_files.append({
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest["files"] = sorted(manifest_files, key=lambda entry: entry.get("path") or "")
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "canonical_events_total": len(current_events),
        "canonical_fights_total": len(current_fights),
        "external_events": len(generated_events),
        "external_fights": len(generated_fights),
        "events_added_this_run": events_added,
        "fights_added_this_run": fights_added,
        "external_fighter_urls_used": len(used_fighter_urls),
        "identity_links_added_this_run": identity_added,
        "external_provenance_rows": len(desired_provenance),
        "provenance_rows_added_this_run": provenance_added,
        "exclusions": len(exclusions),
        "exclusion_reason_counts": dict(sorted(exclusion_counts.items())),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
