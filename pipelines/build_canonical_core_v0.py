#!/usr/bin/env python3
"""Build the first fail-closed UFC Edge canonical core from pinned historical sources.

DATA PHASE ONLY. No feature engineering occurs here.

The build intentionally starts from the pinned Greco/UFCStats historical backbone because
its round-level transport has been reconciled against official UFC FightMetric. Stable
provider identities are translated into opaque canonical IDs; display names are never
used as canonical IDs. Ambiguous/unresolved participant identities are quarantined rather
than guessed.

Outputs:
  data/canonical/v0/{fighters,events,fights,fighter_round_stats,source_identity_links,field_provenance}.csv
  data/canonical/v0/manifest.json
  data/derived/qa/canonical_core_exclusions_v0.csv
  provenance/audits/canonical_core_v0_latest.{json,md}
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_GRECO = ROOT / "data/raw/greco1899"
ALIGN = ROOT / "data/derived/identity/ufc_greco_fight_alignment_candidate.csv"
CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
OUT = ROOT / "data/canonical/v0"
EXCLUSIONS = ROOT / "data/derived/qa/canonical_core_exclusions_v0.csv"
AUDIT_JSON = ROOT / "provenance/audits/canonical_core_v0_latest.json"
AUDIT_MD = ROOT / "provenance/audits/canonical_core_v0_latest.md"

PROJECT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Tkcool28/ufc-edge/canonical/v1")
SOURCE_GRECO = "greco1899_ufcstats"

FIGHTER_FIELDS = ["fighter_id", "canonical_name", "dob", "height_cm", "reach_cm", "leg_reach_cm", "stance"]
EVENT_FIELDS = ["event_id", "promotion", "event_name", "event_date", "event_start_utc", "location"]
FIGHT_FIELDS = [
    "fight_id", "event_id", "fighter_a_id", "fighter_b_id", "winner_id", "result", "method",
    "finish_round", "finish_time_sec", "scheduled_rounds", "weight_class", "title_bout", "promotion",
]
ROUND_FIELDS = [
    "fight_id", "fighter_id", "opponent_id", "round", "knockdowns", "control_sec", "reversals",
    "submission_attempts", "sig_strikes_landed", "sig_strikes_attempted", "total_strikes_landed",
    "total_strikes_attempted", "takedowns_landed", "takedowns_attempted", "sig_head_landed",
    "sig_head_attempted", "sig_body_landed", "sig_body_attempted", "sig_leg_landed", "sig_leg_attempted",
    "sig_distance_landed", "sig_distance_attempted", "sig_clinch_landed", "sig_clinch_attempted",
    "sig_ground_landed", "sig_ground_attempted",
]
IDENTITY_FIELDS = [
    "entity_type", "canonical_id", "source_name", "source_entity_type", "source_id", "source_url",
    "match_method", "match_confidence", "review_status", "valid_from", "valid_to",
]
PROV_FIELDS = [
    "table_name", "row_key", "field_name", "source_name", "source_snapshot_id", "source_record_id",
    "source_field_name", "selection_status", "selection_rule", "quality_note",
]
EXCLUSION_FIELDS = ["source_table", "source_record_id", "event", "bout", "fighter", "reason", "details"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        w.writeheader()
        for row in rows:
            w.writerow({k: scalar(row.get(k)) for k in fields})


def scalar(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Decimal):
        text = format(value.normalize(), "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    return value


def latest_greco() -> Path:
    dirs = sorted(p for p in RAW_GRECO.iterdir() if p.is_dir())
    if not dirs:
        raise RuntimeError("No Greco snapshot")
    return dirs[-1]


def norm_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def mint_id(entity_type: str, source_name: str, source_id: str) -> str:
    return str(uuid.uuid5(PROJECT_NAMESPACE, f"{entity_type}|{source_name}|{source_id.strip()}"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def parse_date(value: str) -> str | None:
    text = clean(value)
    if not text or text in {"--", "N/A"}:
        return None
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"unrecognized date {value!r}")


def parse_nonnegative(value: str) -> int | None:
    text = clean(value)
    if not text or text == "--":
        return None
    if not re.fullmatch(r"\d+", text):
        raise ValueError(f"expected nonnegative integer: {value!r}")
    return int(text)


def parse_mmss(value: str) -> int | None:
    text = clean(value)
    if not text or text == "--":
        return None
    m = re.fullmatch(r"(\d+):(\d{2})", text)
    if not m or int(m.group(2)) >= 60:
        raise ValueError(f"expected M:SS: {value!r}")
    return int(m.group(1)) * 60 + int(m.group(2))


def parse_pair(value: str) -> tuple[int, int] | None:
    text = clean(value)
    if not text or text == "--":
        return None
    m = re.fullmatch(r"(\d+)\s+of\s+(\d+)", text, flags=re.I)
    if not m:
        raise ValueError(f"expected landed of attempted: {value!r}")
    landed, attempted = int(m.group(1)), int(m.group(2))
    if landed > attempted:
        raise ValueError(f"landed > attempted: {value!r}")
    return landed, attempted


def parse_height_cm(value: str) -> Decimal | None:
    text = clean(value)
    if not text or text == "--":
        return None
    m = re.fullmatch(r"(\d+)\s*'\s*(\d+(?:\.\d+)?)\s*(?:\"|in)?", text, flags=re.I)
    if not m:
        raise ValueError(f"bad height: {value!r}")
    feet, inches = Decimal(m.group(1)), Decimal(m.group(2))
    if inches >= 12:
        raise ValueError(f"bad height inches: {value!r}")
    return (feet * 12 + inches) * Decimal("2.54")


def parse_reach_cm(value: str) -> Decimal | None:
    text = clean(value)
    if not text or text == "--":
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:\"|in|inches?)?", text, flags=re.I)
    if not m:
        raise ValueError(f"bad reach: {value!r}")
    return Decimal(m.group(1)) * Decimal("2.54")


def split_bout(value: str) -> tuple[str, str] | None:
    parts = re.split(r"\s+vs\.?\s+", clean(value), maxsplit=1, flags=re.I)
    if len(parts) != 2 or not all(p.strip() for p in parts):
        return None
    return parts[0].strip(), parts[1].strip()


def normalize_method(value: str) -> str:
    text = clean(value).lower()
    if not text:
        return "UNKNOWN"
    if "ko/tko" in text or text in {"tko", "ko"} or text.startswith("tko"):
        return "KO_TKO"
    if "submission" in text:
        return "SUBMISSION"
    if "decision" in text:
        return "DECISION"
    if text.startswith("dq") or "disqualification" in text:
        return "DQ"
    if "draw" in text:
        return "DRAW"
    if "no contest" in text or "overturned" in text:
        return "NO_CONTEST"
    return "OTHER"


def normalize_weight_class(value: str) -> tuple[str | None, bool | None]:
    raw = clean(value)
    if not raw:
        return None, None
    title = "title bout" in raw.lower()
    text = re.sub(r"^UFC\s+", "", raw, flags=re.I)
    text = re.sub(r"\s+Title\s+Bout$", "", text, flags=re.I)
    text = re.sub(r"\s+Bout$", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text or raw, title


def scheduled_rounds(value: str) -> int | None:
    m = re.match(r"\s*(\d+)\s+Rnd\b", clean(value), flags=re.I)
    return int(m.group(1)) if m else None


def outcome_semantics(value: str, a_id: str, b_id: str) -> tuple[str | None, str]:
    token = clean(value).upper().replace(" ", "")
    if token == "W/L":
        return a_id, "win_loss"
    if token == "L/W":
        return b_id, "win_loss"
    if token in {"D/D", "DRAW", "D"} or (token and set(token.replace("/", "")) == {"D"}):
        return None, "draw"
    if "NC" in token or token in {"N/N", "NC"}:
        return None, "no_contest"
    return None, "unknown"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_exclusion(out: list[dict[str, str]], table: str, source_id: str, reason: str, *, event: str = "", bout: str = "", fighter: str = "", details: str = "") -> None:
    out.append({
        "source_table": table, "source_record_id": source_id, "event": event, "bout": bout,
        "fighter": fighter, "reason": reason, "details": details,
    })


def main() -> int:
    snap = latest_greco()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract_version = contract.get("contract_version")

    details = read_csv(snap / "ufc_fighter_details.csv")
    tott = read_csv(snap / "ufc_fighter_tott.csv")
    event_rows = read_csv(snap / "ufc_event_details.csv")
    fight_detail_rows = read_csv(snap / "ufc_fight_details.csv")
    fight_result_rows = read_csv(snap / "ufc_fight_results.csv")
    stat_rows = read_csv(snap / "ufc_fight_stats.csv")

    exclusions: list[dict[str, str]] = []
    identity_links: list[dict[str, Any]] = []
    identity_pk: set[tuple[str, str, str, str]] = set()

    def identity(entity_type: str, canonical_id: str, source_name: str, source_entity_type: str, source_id: str, source_url: str | None, match_method: str, confidence: float, review: str = "trusted") -> None:
        pk = (entity_type, canonical_id, source_name, source_id)
        if pk in identity_pk:
            return
        identity_pk.add(pk)
        identity_links.append({
            "entity_type": entity_type, "canonical_id": canonical_id, "source_name": source_name,
            "source_entity_type": source_entity_type, "source_id": source_id, "source_url": source_url,
            "match_method": match_method, "match_confidence": confidence, "review_status": review,
            "valid_from": None, "valid_to": None,
        })

    # Fighters: stable Greco fighter URL is the provider identity. Duplicate display names are allowed
    # as distinct people, but name-only links into fights are accepted only when globally unique.
    fighter_rows: list[dict[str, Any]] = []
    fighter_by_url: dict[str, str] = {}
    fighter_name_by_id: dict[str, str] = {}
    ids_by_norm: dict[str, set[str]] = defaultdict(set)
    for i, row in enumerate(details, start=2):
        url = clean(row.get("URL"))
        name = " ".join(x for x in [clean(row.get("FIRST")), clean(row.get("LAST"))] if x).strip()
        if not url or not name:
            add_exclusion(exclusions, "ufc_fighter_details", f"row:{i}", "missing_stable_fighter_identity", fighter=name, details=f"url={url!r}")
            continue
        fid = mint_id("fighter", SOURCE_GRECO, url)
        if url in fighter_by_url and fighter_by_url[url] != fid:
            raise RuntimeError(f"impossible duplicate URL identity: {url}")
        fighter_by_url[url] = fid
        fighter_name_by_id[fid] = name
        ids_by_norm[norm_name(name)].add(fid)
        identity("fighter", fid, SOURCE_GRECO, "fighter", url, url, "stable_provider_url", 1.0)

    tott_by_fid: dict[str, dict[str, str]] = {}
    for i, row in enumerate(tott, start=2):
        url = clean(row.get("URL"))
        fid = fighter_by_url.get(url)
        if not fid:
            n = norm_name(clean(row.get("FIGHTER")))
            candidates = ids_by_norm.get(n, set())
            if len(candidates) == 1:
                fid = next(iter(candidates))
            else:
                add_exclusion(exclusions, "ufc_fighter_tott", url or f"row:{i}", "unresolved_tott_fighter_identity", fighter=clean(row.get("FIGHTER")), details=f"candidate_count={len(candidates)}")
                continue
        if fid in tott_by_fid:
            # Keep no duplicate physical observation silently; exact duplicates are harmless, conflicts are QA.
            prev = tott_by_fid[fid]
            if any(clean(prev.get(k)) != clean(row.get(k)) for k in ["HEIGHT", "REACH", "STANCE", "DOB"]):
                add_exclusion(exclusions, "ufc_fighter_tott", url or f"row:{i}", "conflicting_duplicate_tott", fighter=clean(row.get("FIGHTER")))
            continue
        tott_by_fid[fid] = row

    for fid, name in sorted(fighter_name_by_id.items(), key=lambda x: (norm_name(x[1]), x[0])):
        t = tott_by_fid.get(fid, {})
        try:
            height = parse_height_cm(t.get("HEIGHT", ""))
            reach = parse_reach_cm(t.get("REACH", ""))
            dob = parse_date(t.get("DOB", ""))
        except ValueError as exc:
            add_exclusion(exclusions, "ufc_fighter_tott", clean(t.get("URL")) or fid, "invalid_physical_transport", fighter=name, details=str(exc))
            height = reach = dob = None
        fighter_rows.append({
            "fighter_id": fid, "canonical_name": name, "dob": dob, "height_cm": height,
            "reach_cm": reach, "leg_reach_cm": None, "stance": clean(t.get("STANCE")) or None,
        })

    unique_fighter_by_norm = {k: next(iter(v)) for k, v in ids_by_norm.items() if len(v) == 1}

    # Events.
    canonical_events: list[dict[str, Any]] = []
    event_id_by_name: dict[str, str] = {}
    event_url_by_name: dict[str, str] = {}
    duplicate_event_names: set[str] = set()
    for i, row in enumerate(event_rows, start=2):
        name = clean(row.get("EVENT")); url = clean(row.get("URL"))
        if not name or not url:
            add_exclusion(exclusions, "ufc_event_details", url or f"row:{i}", "missing_event_identity", event=name)
            continue
        key = name
        if key in event_id_by_name:
            duplicate_event_names.add(key)
            add_exclusion(exclusions, "ufc_event_details", url, "duplicate_event_name_transport_key", event=name)
            continue
        eid = mint_id("event", SOURCE_GRECO, url)
        event_id_by_name[key] = eid; event_url_by_name[key] = url
        canonical_events.append({
            "event_id": eid, "promotion": "UFC", "event_name": name,
            "event_date": parse_date(row.get("DATE", "")), "event_start_utc": None,
            "location": clean(row.get("LOCATION")) or None,
        })
        identity("event", eid, SOURCE_GRECO, "event", url, url, "stable_provider_url", 1.0)

    # Fight result rows are keyed by stable fight URL.
    result_by_url: dict[str, dict[str, str]] = {}
    for i, row in enumerate(fight_result_rows, start=2):
        url = clean(row.get("URL"))
        if not url:
            add_exclusion(exclusions, "ufc_fight_results", f"row:{i}", "missing_fight_url", event=clean(row.get("EVENT")), bout=clean(row.get("BOUT")))
            continue
        if url in result_by_url:
            add_exclusion(exclusions, "ufc_fight_results", url, "duplicate_result_url", event=clean(row.get("EVENT")), bout=clean(row.get("BOUT")))
            continue
        result_by_url[url] = row

    canonical_fights: list[dict[str, Any]] = []
    fight_id_by_event_bout: dict[tuple[str, str], str] = {}
    fight_meta_by_id: dict[str, dict[str, Any]] = {}
    greco_fight_url_by_key: dict[tuple[str, str], str] = {}
    for i, row in enumerate(fight_detail_rows, start=2):
        event = clean(row.get("EVENT")); bout = clean(row.get("BOUT")); url = clean(row.get("URL"))
        source_id = url or f"row:{i}"
        if not event or not bout or not url:
            add_exclusion(exclusions, "ufc_fight_details", source_id, "missing_fight_identity", event=event, bout=bout)
            continue
        eid = event_id_by_name.get(event)
        if not eid or event in duplicate_event_names:
            add_exclusion(exclusions, "ufc_fight_details", url, "unresolved_event_identity", event=event, bout=bout)
            continue
        participants = split_bout(bout)
        if not participants:
            add_exclusion(exclusions, "ufc_fight_details", url, "unparseable_bout_participants", event=event, bout=bout)
            continue
        name_a, name_b = participants
        a = unique_fighter_by_norm.get(norm_name(name_a)); b = unique_fighter_by_norm.get(norm_name(name_b))
        if not a or not b or a == b:
            add_exclusion(exclusions, "ufc_fight_details", url, "unresolved_or_ambiguous_participant_identity", event=event, bout=bout, details=f"a_candidates={len(ids_by_norm.get(norm_name(name_a), set()))};b_candidates={len(ids_by_norm.get(norm_name(name_b), set()))}")
            continue
        key = (event, bout)
        if key in fight_id_by_event_bout:
            add_exclusion(exclusions, "ufc_fight_details", url, "duplicate_exact_event_bout_key", event=event, bout=bout)
            continue
        res = result_by_url.get(url)
        if not res:
            add_exclusion(exclusions, "ufc_fight_details", url, "missing_result_row", event=event, bout=bout)
            continue
        fight_id = mint_id("fight", SOURCE_GRECO, url)
        winner, result_class = outcome_semantics(res.get("OUTCOME", ""), a, b)
        method = normalize_method(res.get("METHOD", ""))
        wc, title = normalize_weight_class(res.get("WEIGHTCLASS", ""))
        try:
            finish_round = parse_nonnegative(res.get("ROUND", ""))
            if finish_round == 0:
                finish_round = None
            finish_time = parse_mmss(res.get("TIME", ""))
        except ValueError as exc:
            add_exclusion(exclusions, "ufc_fight_results", url, "invalid_finish_transport", event=event, bout=bout, details=str(exc))
            finish_round = finish_time = None
        canonical_fights.append({
            "fight_id": fight_id, "event_id": eid, "fighter_a_id": a, "fighter_b_id": b,
            "winner_id": winner, "result": result_class, "method": method, "finish_round": finish_round,
            "finish_time_sec": finish_time, "scheduled_rounds": scheduled_rounds(res.get("TIME FORMAT", "")),
            "weight_class": wc, "title_bout": title, "promotion": "UFC",
        })
        fight_id_by_event_bout[key] = fight_id
        greco_fight_url_by_key[key] = url
        fight_meta_by_id[fight_id] = {"a": a, "b": b, "event": event, "bout": bout, "url": url}
        identity("fight", fight_id, SOURCE_GRECO, "fight", url, url, "stable_provider_url", 1.0)

    # Round stats.
    canonical_rounds: list[dict[str, Any]] = []
    seen_round_pk: set[tuple[str, str, int]] = set()
    pair_cols = {
        "SIG.STR.": ("sig_strikes_landed", "sig_strikes_attempted"),
        "TOTAL STR.": ("total_strikes_landed", "total_strikes_attempted"),
        "TD": ("takedowns_landed", "takedowns_attempted"),
        "HEAD": ("sig_head_landed", "sig_head_attempted"),
        "BODY": ("sig_body_landed", "sig_body_attempted"),
        "LEG": ("sig_leg_landed", "sig_leg_attempted"),
        "DISTANCE": ("sig_distance_landed", "sig_distance_attempted"),
        "CLINCH": ("sig_clinch_landed", "sig_clinch_attempted"),
        "GROUND": ("sig_ground_landed", "sig_ground_attempted"),
    }
    for i, row in enumerate(stat_rows, start=2):
        event = clean(row.get("EVENT")); bout = clean(row.get("BOUT")); fighter_name = clean(row.get("FIGHTER"))
        source_record = f"{event}|{bout}|{clean(row.get('ROUND'))}|{fighter_name}|row:{i}"
        fight_id = fight_id_by_event_bout.get((event, bout))
        if not fight_id:
            add_exclusion(exclusions, "ufc_fight_stats", source_record, "fight_not_canonicalized", event=event, bout=bout, fighter=fighter_name)
            continue
        fid = unique_fighter_by_norm.get(norm_name(fighter_name))
        meta = fight_meta_by_id[fight_id]
        if not fid or fid not in {meta["a"], meta["b"]}:
            add_exclusion(exclusions, "ufc_fight_stats", source_record, "unresolved_or_nonparticipant_fighter_identity", event=event, bout=bout, fighter=fighter_name)
            continue
        opponent = meta["b"] if fid == meta["a"] else meta["a"]
        try:
            m = re.fullmatch(r"Round\s+(\d+)", clean(row.get("ROUND")), flags=re.I)
            if not m:
                raise ValueError(f"bad round {row.get('ROUND')!r}")
            rnd = int(m.group(1))
            if rnd < 1:
                raise ValueError("round < 1")
            out: dict[str, Any] = {
                "fight_id": fight_id, "fighter_id": fid, "opponent_id": opponent, "round": rnd,
                "knockdowns": parse_nonnegative(row.get("KD", "")),
                "control_sec": parse_mmss(row.get("CTRL", "")),
                "reversals": parse_nonnegative(row.get("REV.", "")),
                "submission_attempts": parse_nonnegative(row.get("SUB.ATT", "")),
            }
            for source_field, (land_field, att_field) in pair_cols.items():
                pair = parse_pair(row.get(source_field, ""))
                out[land_field] = pair[0] if pair else None
                out[att_field] = pair[1] if pair else None
        except ValueError as exc:
            add_exclusion(exclusions, "ufc_fight_stats", source_record, "invalid_round_stat_transport", event=event, bout=bout, fighter=fighter_name, details=str(exc))
            continue
        pk = (fight_id, fid, rnd)
        if pk in seen_round_pk:
            add_exclusion(exclusions, "ufc_fight_stats", source_record, "duplicate_canonical_fighter_round_key", event=event, bout=bout, fighter=fighter_name)
            continue
        seen_round_pk.add(pk)
        canonical_rounds.append(out)

    # Add direct official UFC/FightMetric identity evidence already proven by exact fight alignment.
    if ALIGN.exists():
        canonical_fight_by_greco_key = fight_id_by_event_bout
        official_fighter_links: dict[str, str] = {}
        for row in read_csv(ALIGN):
            key = (clean(row.get("greco_event")), clean(row.get("greco_bout")))
            fight_id = canonical_fight_by_greco_key.get(key)
            if not fight_id:
                continue
            ufc_fight_uuid = clean(row.get("ufc_fight_uuid"))
            fmid = clean(row.get("fightmetric_id"))
            if ufc_fight_uuid:
                identity("fight", fight_id, "ufc_com", "fight", ufc_fight_uuid, None, "exact_date_pair_direct_fight_alignment", 1.0)
            if fmid:
                identity("fight", fight_id, "ufc_fightmetric_official", "fight", fmid, None, "official_fightmetric_id_bridge", 1.0)
            for corner in ("red", "blue"):
                uid = clean(row.get(f"{corner}_athlete_uuid")); name = clean(row.get(f"{corner}_name"))
                fid = unique_fighter_by_norm.get(norm_name(name))
                if not uid or not fid:
                    continue
                prior = official_fighter_links.get(uid)
                if prior and prior != fid:
                    add_exclusion(exclusions, "ufc_greco_fight_alignment_candidate", uid, "official_athlete_uuid_maps_to_multiple_canonical_fighters", bout=clean(row.get("greco_bout")), fighter=name)
                    continue
                official_fighter_links[uid] = fid
        for uid, fid in sorted(official_fighter_links.items()):
            identity("fighter", fid, "ufc_com", "athlete", uid, None, "repeated_exact_fight_alignment_corner_identity", 1.0)

    # Field provenance is intentionally sparse in v0. The manifest carries default source-selection
    # policy; this table records conflicts/overrides as they arise rather than exploding every cell.
    provenance_rows: list[dict[str, Any]] = []

    # Deterministic order.
    fighter_rows.sort(key=lambda r: r["fighter_id"])
    canonical_events.sort(key=lambda r: (r["event_date"] or "", r["event_id"]))
    canonical_fights.sort(key=lambda r: r["fight_id"])
    canonical_rounds.sort(key=lambda r: (r["fight_id"], r["fighter_id"], int(r["round"])))
    identity_links.sort(key=lambda r: (r["entity_type"], r["canonical_id"], r["source_name"], r["source_id"]))
    exclusions.sort(key=lambda r: (r["source_table"], r["source_record_id"], r["reason"]))

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "fighters.csv", FIGHTER_FIELDS, fighter_rows)
    write_csv(OUT / "events.csv", EVENT_FIELDS, canonical_events)
    write_csv(OUT / "fights.csv", FIGHT_FIELDS, canonical_fights)
    write_csv(OUT / "fighter_round_stats.csv", ROUND_FIELDS, canonical_rounds)
    write_csv(OUT / "source_identity_links.csv", IDENTITY_FIELDS, identity_links)
    write_csv(OUT / "field_provenance.csv", PROV_FIELDS, provenance_rows)
    write_csv(EXCLUSIONS, EXCLUSION_FIELDS, exclusions)

    outputs = [
        OUT / "fighters.csv", OUT / "events.csv", OUT / "fights.csv", OUT / "fighter_round_stats.csv",
        OUT / "source_identity_links.csv", OUT / "field_provenance.csv", EXCLUSIONS,
    ]
    counts = {
        "fighters": len(fighter_rows), "events": len(canonical_events), "fights": len(canonical_fights),
        "fighter_round_stats": len(canonical_rounds), "source_identity_links": len(identity_links),
        "field_provenance": len(provenance_rows), "exclusions": len(exclusions),
    }
    reason_counts: dict[str, int] = defaultdict(int)
    for row in exclusions:
        reason_counts[row["reason"]] += 1
    manifest = {
        "schema_version": 1,
        "canonical_contract_version": contract_version,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "build": "canonical_core_v0",
        "source_snapshots": {SOURCE_GRECO: snap.name},
        "rules": {
            "display_name_only_identity_is_trusted": False,
            "unique_normalized_name_used_only_as_fail_closed_transport_resolution": True,
            "canonical_ids_are_opaque_uuid5_from_first_trusted_source_identity": True,
            "round_zero_allowed": False,
            "missing_is_not_zero": True,
            "greco_is_default_historical_transport_for_shared_round_counts": True,
            "exact_control_seconds_source": SOURCE_GRECO,
            "ambiguous_identity_rows_are_quarantined": True,
            "field_provenance_is_sparse_override_conflict_ledger": True,
        },
        "counts": counts,
        "exclusion_reason_counts": dict(sorted(reason_counts.items())),
        "files": [
            {"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size, "sha256": sha256(p)} for p in outputs
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    audit = dict(manifest)
    audit["manifest"] = str((OUT / "manifest.json").relative_to(ROOT))
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "# Canonical core v0 build\n\n"
        f"- Contract: **{contract_version}**\n"
        f"- Greco snapshot: **{snap.name}**\n"
        f"- Fighters: **{counts['fighters']}**\n"
        f"- Events: **{counts['events']}**\n"
        f"- Fights: **{counts['fights']}**\n"
        f"- Fighter-round rows: **{counts['fighter_round_stats']}**\n"
        f"- Source identity links: **{counts['source_identity_links']}**\n"
        f"- Quarantined source rows/items: **{counts['exclusions']}**\n\n"
        "Ambiguous identities are excluded rather than guessed. See `data/derived/qa/canonical_core_exclusions_v0.csv`.\n",
        encoding="utf-8",
    )
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
