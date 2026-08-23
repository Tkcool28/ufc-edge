#!/usr/bin/env python3
"""Append the audited Bellator/ONE external history subset to canonical v0.

DATA PHASE ONLY. This builder is intentionally narrow:
- never uses external data to repair/overwrite UFC-labelled canonical history;
- requires two trusted external fighter URL -> canonical fighter mappings;
- quarantines the known duplicate source fight key;
- excludes any non-UFC source bout within +/-1 day of an existing canonical UFC bout for
  the same trusted unordered participant pair;
- materializes only contract-safe event/fight fields explicitly supported by the source.

The operation is idempotent for the pinned v1 source. Existing generated rows must match
exactly; a conflicting deterministic ID fails closed.
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

PROJECT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Tkcool28/ufc-edge/canonical/v1")
SOURCE_FIGHTS = "kaggle_pro_mma_fights"
SOURCE_FIGHTERS = "kaggle_pro_mma_fighters"
SOURCE_SNAPSHOT = "v1"
UFC_ORG = "Ultimate Fighting Championship (UFC)"

EVENT_FIELDS = ["event_id", "promotion", "event_name", "event_date", "event_start_utc", "location"]
FIGHT_FIELDS = [
    "fight_id", "event_id", "fighter_a_id", "fighter_b_id", "winner_id", "result", "method",
    "finish_round", "finish_time_sec", "scheduled_rounds", "weight_class", "title_bout", "promotion",
]
IDENTITY_FIELDS = [
    "entity_type", "canonical_id", "source_name", "source_entity_type", "source_id", "source_url",
    "match_method", "match_confidence", "review_status", "valid_from", "valid_to",
]
PROV_FIELDS = [
    "table_name", "row_key", "field_name", "source_name", "source_snapshot_id", "source_record_id",
    "source_field_name", "selection_status", "selection_rule", "quality_note",
]
EXCLUSION_FIELDS = [
    "source_event_url", "source_match_nr", "source_organisation", "source_event_title",
    "fighter1_name", "fighter2_name", "reason", "details",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        w.writeheader()
        for row in rows:
            w.writerow({k: "" if row.get(k) is None else row.get(k) for k in fields})


def mint_id(entity_type: str, source_name: str, source_id: str) -> str:
    return str(uuid.uuid5(PROJECT_NAMESPACE, f"{entity_type}|{source_name}|{source_id.strip()}"))


def parse_date(value: str) -> str:
    return datetime.strptime((value or "").strip(), "%b %d, %Y").date().isoformat()


def parse_time(value: str) -> int:
    text = (value or "").strip()
    m = re.fullmatch(r"(\d+):(\d{2})", text)
    if not m or int(m.group(2)) >= 60:
        raise ValueError(f"invalid audited M:SS time: {value!r}")
    return int(m.group(1)) * 60 + int(m.group(2))


def normalize_method(value: str) -> str:
    text = (value or "").strip().lower()
    if text in {"ko", "tko"}:
        return "KO_TKO"
    if text in {"submission", "technical submission", "verbal submission"}:
        return "SUBMISSION"
    if text == "decision":
        return "DECISION"
    if text == "disqualification":
        return "DQ"
    if text == "draw":
        return "DRAW"
    if text in {"no contest", "nc"}:
        return "NO_CONTEST"
    raise ValueError(f"unmapped eligible method: {value!r}")


def result_semantics(r1: str, r2: str, f1: str, f2: str) -> tuple[str | None, str]:
    a, b = (r1 or "").strip().lower(), (r2 or "").strip().lower()
    if (a, b) == ("win", "loss"):
        return f1, "win_loss"
    if (a, b) == ("loss", "win"):
        return f2, "win_loss"
    if (a, b) == ("draw", "draw"):
        return None, "draw"
    if (a, b) == ("nc", "nc"):
        return None, "no_contest"
    raise ValueError(f"unmapped eligible result pair: {(r1, r2)!r}")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_string_row(row: dict[str, Any], fields: list[str]) -> dict[str, str]:
    return {k: "" if row.get(k) is None else str(row.get(k)) for k in fields}


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    if readiness.get("contract_ready_fight_rows") != 483:
        raise RuntimeError("readiness audit no longer proves exactly 483 contract-ready fights")
    if readiness.get("eligible_distinct_event_urls") != 230:
        raise RuntimeError("readiness audit no longer proves exactly 230 eligible event URLs")
    failures = readiness.get("semantic_gate_failures") or {}
    if failures.get("unknown_result_rows") != 0 or failures.get("round_outside_contract_1_to_10_rows") != 0 or failures.get("invalid_time_mmss_rows") != 0:
        raise RuntimeError(f"readiness semantic gate is no longer clean: {failures}")

    raw = read_csv(RAW)
    xwalk = read_csv(XWALK)
    current_events = read_csv(EVENTS)
    current_fights = read_csv(FIGHTS)
    current_identity = read_csv(IDENTITY)
    current_prov = read_csv(PROVENANCE)

    if list(current_events[0]) != EVENT_FIELDS or list(current_fights[0]) != FIGHT_FIELDS:
        raise RuntimeError("canonical event/fight header drift")
    if list(current_identity[0]) != IDENTITY_FIELDS or list(current_prov[0]) != PROV_FIELDS:
        raise RuntimeError("canonical identity/provenance header drift")

    trusted: dict[str, dict[str, str]] = {}
    for row in xwalk:
        if (row.get("review_status") or "").strip() != "trusted":
            continue
        url = (row.get("external_fighter_url") or "").strip()
        fid = (row.get("canonical_fighter_id") or "").strip()
        if not url or not fid:
            continue
        old = trusted.get(url)
        if old and (old.get("canonical_fighter_id") or "").strip() != fid:
            raise RuntimeError(f"trusted fighter URL collision: {url}")
        trusted[url] = row

    ufc_event_date = {
        (r.get("event_id") or "").strip(): (r.get("event_date") or "").strip()
        for r in current_events if (r.get("promotion") or "").strip() == "UFC"
    }
    ufc_by_pair: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for fight in current_fights:
        if (fight.get("promotion") or "").strip() != "UFC":
            continue
        a, b = (fight.get("fighter_a_id") or "").strip(), (fight.get("fighter_b_id") or "").strip()
        if a and b and a != b:
            ufc_by_pair[tuple(sorted((a, b)))].append(fight)

    source_key_counts = Counter(((r.get("url") or "").strip(), (r.get("match_nr") or "").strip()) for r in raw)
    duplicate_keys = {k for k, n in source_key_counts.items() if n > 1}

    generated_events_by_url: dict[str, dict[str, Any]] = {}
    generated_fights: list[dict[str, Any]] = []
    promoted_rows: list[tuple[dict[str, str], str, str, str, str]] = []
    exclusions: list[dict[str, str]] = []
    exclusion_counts = Counter()

    def reject(row: dict[str, str], reason: str, details: str = "") -> None:
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

    for row in raw:
        org = (row.get("organisation") or "").strip()
        url = (row.get("url") or "").strip()
        match_nr = (row.get("match_nr") or "").strip()
        source_key = (url, match_nr)
        if org == UFC_ORG:
            reject(row, "ufc_label_excluded_lower_precedence", "external source is not used to repair/overwrite UFC canonical history")
            continue
        if source_key in duplicate_keys:
            reject(row, "duplicate_source_fight_key_quarantine", "audited duplicate (source event URL, match_nr) key")
            continue

        x1 = trusted.get((row.get("fighter1_url") or "").strip())
        x2 = trusted.get((row.get("fighter2_url") or "").strip())
        f1 = (x1.get("canonical_fighter_id") or "").strip() if x1 else ""
        f2 = (x2.get("canonical_fighter_id") or "").strip() if x2 else ""
        if not f1 or not f2 or f1 == f2:
            reject(row, "unresolved_trusted_fighter_identity", f"fighter1_trusted={bool(f1)};fighter2_trusted={bool(f2)}")
            continue

        source_date = parse_date(row.get("date") or "")
        pair = tuple(sorted((f1, f2)))
        if pair in ufc_by_pair:
            src = datetime.fromisoformat(source_date).date()
            deltas = []
            for fight in ufc_by_pair[pair]:
                cdate = ufc_event_date.get((fight.get("event_id") or "").strip(), "")
                if cdate:
                    deltas.append((src - datetime.fromisoformat(cdate).date()).days)
            if deltas:
                nearest = min(deltas, key=lambda d: (abs(d), d))
                if abs(nearest) <= 1:
                    reject(row, "canonical_ufc_overlap_pair_within_one_day", f"nearest_source_minus_canonical_days={nearest}")
                    continue

        finish_round = int((row.get("round") or "").strip())
        if not 1 <= finish_round <= 10:
            reject(row, "finish_round_outside_contract", f"round={finish_round}")
            continue
        finish_time = parse_time(row.get("time") or "")
        winner, result = result_semantics(row.get("fighter1_result") or "", row.get("fighter2_result") or "", f1, f2)
        method = normalize_method(row.get("win_method") or "")

        event_signature = (
            org,
            (row.get("event_title") or "").strip(),
            source_date,
            (row.get("location") or "").strip(),
        )
        event_id = mint_id("event", SOURCE_FIGHTS, url)
        event_row = {
            "event_id": event_id,
            "promotion": org,
            "event_name": event_signature[1],
            "event_date": source_date,
            "event_start_utc": None,
            "location": event_signature[3] or None,
        }
        prior_event = generated_events_by_url.get(url)
        if prior_event and canonical_string_row(prior_event, EVENT_FIELDS) != canonical_string_row(event_row, EVENT_FIELDS):
            raise RuntimeError(f"eligible source event URL maps to multiple canonical event signatures: {url}")
        generated_events_by_url[url] = event_row

        source_fight_id = f"{url}|{match_nr}"
        fight_id = mint_id("fight", SOURCE_FIGHTS, source_fight_id)
        generated_fights.append({
            "fight_id": fight_id,
            "event_id": event_id,
            "fighter_a_id": f1,
            "fighter_b_id": f2,
            "winner_id": winner,
            "result": result,
            "method": method,
            "finish_round": finish_round,
            "finish_time_sec": finish_time,
            "scheduled_rounds": None,
            "weight_class": None,
            "title_bout": None,
            "promotion": org,
        })
        promoted_rows.append((row, f1, f2, event_id, fight_id))

    generated_events = sorted(generated_events_by_url.values(), key=lambda r: r["event_id"])
    generated_fights.sort(key=lambda r: r["fight_id"])
    exclusions.sort(key=lambda r: (r["source_event_url"], r["source_match_nr"], r["fighter1_name"], r["fighter2_name"]))

    if len(generated_events) != 230 or len(generated_fights) != 483:
        raise RuntimeError(f"materialization gate changed: events={len(generated_events)} fights={len(generated_fights)}")
    if len(exclusions) != len(raw) - len(generated_fights):
        raise RuntimeError("every raw row must be promoted exactly once or excluded exactly once")

    # Idempotent canonical append. Deterministic IDs may already exist only if the row is identical.
    event_by_id = {(r.get("event_id") or "").strip(): r for r in current_events}
    for row in generated_events:
        existing = event_by_id.get(row["event_id"])
        if existing:
            if canonical_string_row(existing, EVENT_FIELDS) != canonical_string_row(row, EVENT_FIELDS):
                raise RuntimeError(f"deterministic external event ID conflicts with existing row: {row['event_id']}")
        else:
            current_events.append(row)
            event_by_id[row["event_id"]] = canonical_string_row(row, EVENT_FIELDS)

    fight_by_id = {(r.get("fight_id") or "").strip(): r for r in current_fights}
    for row in generated_fights:
        existing = fight_by_id.get(row["fight_id"])
        if existing:
            if canonical_string_row(existing, FIGHT_FIELDS) != canonical_string_row(row, FIGHT_FIELDS):
                raise RuntimeError(f"deterministic external fight ID conflicts with existing row: {row['fight_id']}")
        else:
            current_fights.append(row)
            fight_by_id[row["fight_id"]] = canonical_string_row(row, FIGHT_FIELDS)

    # Canonical identity links: promoted fighter mappings plus stable source event/fight identities.
    identity_pk: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in current_identity:
        key = (row.get("entity_type") or "", row.get("canonical_id") or "", row.get("source_name") or "", row.get("source_id") or "")
        if key in identity_pk and identity_pk[key] != row:
            raise RuntimeError(f"duplicate conflicting canonical identity link: {key}")
        identity_pk[key] = row

    new_identity: list[dict[str, Any]] = []
    used_fighter_urls: dict[str, dict[str, str]] = {}
    for raw_row, f1, f2, event_id, fight_id in promoted_rows:
        for side, fid in ((1, f1), (2, f2)):
            u = (raw_row.get(f"fighter{side}_url") or "").strip()
            used_fighter_urls[u] = trusted[u]

    for url, x in sorted(used_fighter_urls.items()):
        new_identity.append({
            "entity_type": "fighter",
            "canonical_id": (x.get("canonical_fighter_id") or "").strip(),
            "source_name": SOURCE_FIGHTERS,
            "source_entity_type": "fighter",
            "source_id": url,
            "source_url": url,
            "match_method": (x.get("match_method") or "").strip(),
            "match_confidence": (x.get("match_confidence") or "").strip() or "1.0",
            "review_status": "trusted",
            "valid_from": None,
            "valid_to": None,
        })
    for url, event in sorted(generated_events_by_url.items()):
        new_identity.append({
            "entity_type": "event", "canonical_id": event["event_id"], "source_name": SOURCE_FIGHTS,
            "source_entity_type": "event", "source_id": url, "source_url": url,
            "match_method": "stable_source_event_url", "match_confidence": "1.0", "review_status": "trusted",
            "valid_from": None, "valid_to": None,
        })
    for raw_row, _f1, _f2, _event_id, fight_id in promoted_rows:
        url = (raw_row.get("url") or "").strip(); match_nr = (raw_row.get("match_nr") or "").strip()
        sid = f"{url}|{match_nr}"
        new_identity.append({
            "entity_type": "fight", "canonical_id": fight_id, "source_name": SOURCE_FIGHTS,
            "source_entity_type": "fight", "source_id": sid, "source_url": url,
            "match_method": "stable_source_event_url_plus_match_nr", "match_confidence": "1.0", "review_status": "trusted",
            "valid_from": None, "valid_to": None,
        })

    for row in new_identity:
        row_s = canonical_string_row(row, IDENTITY_FIELDS)
        key = (row_s["entity_type"], row_s["canonical_id"], row_s["source_name"], row_s["source_id"])
        existing = identity_pk.get(key)
        if existing:
            if canonical_string_row(existing, IDENTITY_FIELDS) != row_s:
                raise RuntimeError(f"external identity link conflicts with existing canonical link: {key}")
        else:
            current_identity.append(row)
            identity_pk[key] = row_s

    # Explicit selected-field provenance for all external event/fight contributions.
    prov_pk: dict[tuple[str, ...], dict[str, str]] = {}
    for row in current_prov:
        key = tuple(row.get(k) or "" for k in PROV_FIELDS[:6])
        if key in prov_pk and prov_pk[key] != row:
            raise RuntimeError(f"duplicate conflicting field provenance: {key}")
        prov_pk[key] = row
    new_prov: list[dict[str, Any]] = []

    def prov(table: str, row_key: str, field: str, record: str, source_field: str, rule: str, note: str = "") -> None:
        new_prov.append({
            "table_name": table, "row_key": row_key, "field_name": field, "source_name": SOURCE_FIGHTS,
            "source_snapshot_id": SOURCE_SNAPSHOT, "source_record_id": record, "source_field_name": source_field,
            "selection_status": "selected", "selection_rule": rule, "quality_note": note or None,
        })

    event_record_by_url = {url: url for url in generated_events_by_url}
    for url, event in sorted(generated_events_by_url.items()):
        rule = "trusted_external_identity_non_ufc_overlap_dedupe"
        prov("events", event["event_id"], "event_id", url, "url", rule, "deterministic UUIDv5 from stable source event URL")
        prov("events", event["event_id"], "promotion", url, "organisation", rule)
        prov("events", event["event_id"], "event_name", url, "event_title", rule)
        prov("events", event["event_id"], "event_date", url, "date", rule, "audited parser %b %d, %Y")
        if event.get("location"):
            prov("events", event["event_id"], "location", url, "location", rule)

    for raw_row, _f1, _f2, event_id, fight_id in promoted_rows:
        url = (raw_row.get("url") or "").strip(); match_nr = (raw_row.get("match_nr") or "").strip()
        record = f"{url}|{match_nr}"
        rule = "trusted_external_fighter_urls_non_ufc_overlap_dedupe"
        prov("fights", fight_id, "fight_id", record, "url+match_nr", rule, "deterministic UUIDv5 from audited stable composite source key")
        prov("fights", fight_id, "event_id", record, "url", rule)
        prov("fights", fight_id, "fighter_a_id", record, "fighter1_url", rule)
        prov("fights", fight_id, "fighter_b_id", record, "fighter2_url", rule)
        prov("fights", fight_id, "result", record, "fighter1_result+fighter2_result", rule)
        if (raw_row.get("fighter1_result") or "").strip().lower() in {"win", "loss"}:
            prov("fights", fight_id, "winner_id", record, "fighter1_result+fighter2_result", rule)
        prov("fights", fight_id, "method", record, "win_method", rule, "normalized to canonical method enum")
        prov("fights", fight_id, "finish_round", record, "round", rule)
        prov("fights", fight_id, "finish_time_sec", record, "time", rule, "source M:SS converted to seconds")
        prov("fights", fight_id, "promotion", record, "organisation", rule)

    for row in new_prov:
        row_s = canonical_string_row(row, PROV_FIELDS)
        key = tuple(row_s.get(k, "") for k in PROV_FIELDS[:6])
        existing = prov_pk.get(key)
        if existing:
            if canonical_string_row(existing, PROV_FIELDS) != row_s:
                raise RuntimeError(f"external provenance conflicts with existing row: {key}")
        else:
            current_prov.append(row)
            prov_pk[key] = row_s

    current_events.sort(key=lambda r: (r.get("event_id") or ""))
    current_fights.sort(key=lambda r: (r.get("fight_id") or ""))
    current_identity.sort(key=lambda r: tuple(r.get(k) or "" for k in ("entity_type", "canonical_id", "source_name", "source_id")))
    current_prov.sort(key=lambda r: tuple(r.get(k) or "" for k in ("table_name", "row_key", "field_name", "source_name", "source_snapshot_id", "source_record_id")))

    write_csv(EVENTS, EVENT_FIELDS, current_events)
    write_csv(FIGHTS, FIGHT_FIELDS, current_fights)
    write_csv(IDENTITY, IDENTITY_FIELDS, current_identity)
    write_csv(PROVENANCE, PROV_FIELDS, current_prov)
    write_csv(EXCLUSIONS, EXCLUSION_FIELDS, exclusions)

    audit = {
        "schema_version": 1,
        "canonical_contract_version": contract.get("contract_version"),
        "source": SOURCE_FIGHTS,
        "source_snapshot_id": SOURCE_SNAPSHOT,
        "canonical_events_added": len(generated_events),
        "canonical_fights_added": len(generated_fights),
        "promoted_organisation_counts": dict(Counter(r[0].get("organisation") or "" for r in promoted_rows)),
        "promoted_method_counts": dict(Counter(r["method"] for r in generated_fights)),
        "promoted_result_counts": dict(Counter(r["result"] for r in generated_fights)),
        "promoted_fighter_identity_links": len(used_fighter_urls),
        "event_identity_links": len(generated_events),
        "fight_identity_links": len(generated_fights),
        "field_provenance_rows_for_external_history": len(new_prov),
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
            "events": str(EVENTS.relative_to(ROOT)), "fights": str(FIGHTS.relative_to(ROOT)),
            "source_identity_links": str(IDENTITY.relative_to(ROOT)), "field_provenance": str(PROVENANCE.relative_to(ROOT)),
            "exclusions": str(EXCLUSIONS.relative_to(ROOT)),
        },
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "# Canonical external MMA history v0\n\n"
        f"- Promoted events: **{len(generated_events)}**\n"
        f"- Promoted fights: **{len(generated_fights)}**\n"
        f"- Bellator/ONE only; UFC-labelled external rows promoted: **0**\n"
        f"- Excluded/quarantined raw rows: **{len(exclusions)}**\n\n"
        "Identity requires stable external fighter URLs with trusted canonical crosswalks. "
        "The external source is not used to repair or overwrite UFC canonical history.\n",
        encoding="utf-8",
    )

    # Mutate the current full manifest rather than replacing it with a core-only manifest.
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("canonical_contract_version") != contract.get("contract_version"):
        raise RuntimeError("canonical manifest contract version mismatch")
    counts = manifest.setdefault("counts", {})
    counts["events"] = len(current_events)
    counts["fights"] = len(current_fights)
    counts["source_identity_links"] = len(current_identity)
    counts["field_provenance"] = len(current_prov)
    counts["external_mma_exclusions"] = len(exclusions)
    manifest.setdefault("source_snapshots", {})[SOURCE_FIGHTS] = SOURCE_SNAPSHOT
    manifest.setdefault("source_snapshots", {})[SOURCE_FIGHTERS] = SOURCE_SNAPSHOT
    manifest.setdefault("rules", {})["external_mma_ufc_labelled_rows_never_repair_higher_precedence_ufc_history"] = True
    manifest.setdefault("rules", {})["external_mma_overlap_requires_trusted_pair_and_excludes_within_one_day_of_canonical_ufc_pair"] = True
    manifest["generated_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    changed = {str(p.relative_to(ROOT)) for p in (EVENTS, FIGHTS, IDENTITY, PROVENANCE, EXCLUSIONS)}
    entries = [x for x in manifest.get("files", []) if x.get("path") not in changed]
    for path in (EVENTS, FIGHTS, IDENTITY, PROVENANCE, EXCLUSIONS):
        entries.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest["files"] = sorted(entries, key=lambda x: x.get("path") or "")
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "canonical_events_total": len(current_events),
        "canonical_fights_total": len(current_fights),
        "external_events": len(generated_events),
        "external_fights": len(generated_fights),
        "external_fighter_links": len(used_fighter_urls),
        "external_provenance_rows": len(new_prov),
        "exclusions": len(exclusions),
        "exclusion_reason_counts": dict(exclusion_counts),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
