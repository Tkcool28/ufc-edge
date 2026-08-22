#!/usr/bin/env python3
"""Materialize source-neutral UFC FightMetric position buckets into canonical v0.

DATA PHASE ONLY.  This builder consumes only already-audited identities and semantics:
- canonical fight/fighter IDs from data/canonical/v0/source_identity_links.csv;
- exact UFC↔Greco alignment evidence for red/blue athlete UUIDs;
- FightMetric numeric corner mapping 0=red, 1=blue;
- round=0 is a summary and is excluded;
- archived position `_time` values are floor-whole-minute buckets, not exact seconds.

Any unresolved duplicate source-version key, unknown identity, non-0..5 bucket value, or
other semantic defect is quarantined rather than guessed.  Raw source bytes are untouched.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.data.manifest_readers import latest_manifest, manifest_page_paths  # noqa: E402

CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
FM_ROOT = ROOT / "data/raw/ufc_fightmetric_official"
ALIGN = ROOT / "data/derived/identity/ufc_greco_fight_alignment_candidate.csv"
CANON = ROOT / "data/canonical/v0"
IDENTITY = CANON / "source_identity_links.csv"
FIGHTS = CANON / "fights.csv"
OUT = CANON / "fighter_round_position.csv"
EXCLUSIONS = ROOT / "data/derived/qa/canonical_fightmetric_position_exclusions_v0.csv"
AUDIT_JSON = ROOT / "provenance/audits/canonical_fightmetric_position_v0_latest.json"
AUDIT_MD = ROOT / "provenance/audits/canonical_fightmetric_position_v0_latest.md"

SOURCE = "ufc_fightmetric_official"
COLOR_MAP = {0: "red", 1: "blue"}
POSITION_MAP = {
    "standing_time": "standing",
    "neutral_time": "neutral",
    "distance_time": "distance",
    "clinch_time": "clinch",
    "ground_time": "ground",
    "ground_ctl_time": "ground_control",
    "guard_ctl_time": "guard_control",
    "half_guard_ctl_time": "half_guard_control",
    "side_ctl_time": "side_control",
    "mount_ctl_time": "mount_control",
    "back_ctl_time": "back_control",
    "msc_ground_ctl__time": "misc_ground_control",
}
EXCLUSION_FIELDS = [
    "fightmetric_id", "raw_color", "round", "resource_id", "drupal_internal_id",
    "reason", "field", "raw_value", "details",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row.get(field) is None else row.get(field) for field in fields})


def as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if text.startswith("+"):
        text = text[1:]
    if not text or not text.isdigit():
        return None
    return int(text)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def exclusion(
    rows: list[dict[str, Any]], attrs: dict[str, Any], item: dict[str, Any], reason: str,
    *, field: str = "", raw_value: Any = "", details: str = "",
) -> None:
    rows.append({
        "fightmetric_id": attrs.get("fightmetric_id"),
        "raw_color": attrs.get("color"),
        "round": attrs.get("round"),
        "resource_id": item.get("id"),
        "drupal_internal_id": attrs.get("drupal_internal__id"),
        "reason": reason,
        "field": field,
        "raw_value": raw_value,
        "details": details,
    })


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    table = contract["tables"]["fighter_round_position"]
    fields = list(table["fields"])

    core_manifest_path = CANON / "manifest.json"
    core_manifest = json.loads(core_manifest_path.read_text(encoding="utf-8"))
    if core_manifest.get("canonical_contract_version") != contract.get("contract_version"):
        raise RuntimeError("canonical v0 manifest contract version is stale")

    # Canonical fight IDs by stable FightMetric source ID and fighter IDs by official athlete UUID.
    fight_id_by_fmid: dict[int, str] = {}
    fighter_id_by_athlete_uuid: dict[str, str] = {}
    for row in read_csv(IDENTITY):
        if row.get("review_status") != "trusted":
            continue
        source = row.get("source_name") or ""
        entity = row.get("entity_type") or ""
        sid = row.get("source_id") or ""
        cid = row.get("canonical_id") or ""
        if entity == "fight" and source == SOURCE and sid.isdigit():
            fmid = int(sid)
            prior = fight_id_by_fmid.get(fmid)
            if prior and prior != cid:
                raise RuntimeError(f"FightMetric ID maps to multiple canonical fights: {fmid}")
            fight_id_by_fmid[fmid] = cid
        elif entity == "fighter" and source == "ufc_com" and sid:
            prior = fighter_id_by_athlete_uuid.get(sid)
            if prior and prior != cid:
                raise RuntimeError(f"UFC athlete UUID maps to multiple canonical fighters: {sid}")
            fighter_id_by_athlete_uuid[sid] = cid

    # Alignment supplies audited corner athlete UUIDs for each FightMetric fight ID.
    corner_fighter: dict[tuple[int, str], str] = {}
    for row in read_csv(ALIGN):
        raw_fmid = (row.get("fightmetric_id") or "").strip()
        if not raw_fmid.isdigit():
            continue
        fmid = int(raw_fmid)
        if fmid not in fight_id_by_fmid:
            continue
        for corner in ("red", "blue"):
            athlete_uuid = (row.get(f"{corner}_athlete_uuid") or "").strip()
            fighter_id = fighter_id_by_athlete_uuid.get(athlete_uuid)
            if not fighter_id:
                continue
            key = (fmid, corner)
            prior = corner_fighter.get(key)
            if prior and prior != fighter_id:
                raise RuntimeError(f"FightMetric corner maps to multiple canonical fighters: {key}")
            corner_fighter[key] = fighter_id

    fight_participants: dict[str, set[str]] = {}
    for row in read_csv(FIGHTS):
        fight_participants[row["fight_id"]] = {row["fighter_a_id"], row["fighter_b_id"]}

    fm_manifest = latest_manifest(FM_ROOT)
    snapshot_id = fm_manifest.parent.name
    versions: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    raw_rows = 0
    for page in manifest_page_paths(fm_manifest, collection="fight_stat"):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            raw_rows += 1
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            fmid = as_int(attrs.get("fightmetric_id"))
            color = as_int(attrs.get("color"))
            rnd = as_int(attrs.get("round"))
            if fmid is None or color not in COLOR_MAP or rnd is None or rnd < 1:
                continue
            versions[(fmid, color, rnd)].append(item)

    rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    seen_pk: set[tuple[str, str, int]] = set()
    stats = Counter()

    for (fmid, color, rnd), items in sorted(versions.items()):
        stats["actual_round_source_keys"] += 1
        if len(items) != 1:
            stats["duplicate_version_keys"] += 1
            for item in items:
                attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
                exclusion(exclusions, attrs, item, "unresolved_duplicate_source_version", details=f"version_count={len(items)}")
            continue

        item = items[0]
        attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
        fight_id = fight_id_by_fmid.get(fmid)
        corner = COLOR_MAP[color]
        fighter_id = corner_fighter.get((fmid, corner))
        if not fight_id:
            stats["missing_canonical_fight"] += 1
            exclusion(exclusions, attrs, item, "missing_canonical_fight_identity")
            continue
        if not fighter_id:
            stats["missing_canonical_fighter"] += 1
            exclusion(exclusions, attrs, item, "missing_canonical_corner_fighter_identity")
            continue
        if fighter_id not in fight_participants.get(fight_id, set()):
            stats["nonparticipant_identity"] += 1
            exclusion(exclusions, attrs, item, "canonical_corner_fighter_not_fight_participant")
            continue

        out: dict[str, Any] = {"fight_id": fight_id, "fighter_id": fighter_id, "round": rnd}
        nonnull = 0
        for source_field, prefix in POSITION_MAP.items():
            raw = attrs.get(source_field)
            val = as_int(raw)
            if raw not in (None, "") and val is None:
                stats["invalid_bucket_transport"] += 1
                exclusion(exclusions, attrs, item, "invalid_position_bucket_transport", field=source_field, raw_value=raw)
                val = None
            if val is not None and not 0 <= val <= 5:
                stats["bucket_anomalies_gt5"] += 1
                exclusion(exclusions, attrs, item, "position_bucket_outside_audited_0_5_range", field=source_field, raw_value=raw)
                val = None
            out[f"{prefix}_bucket_min"] = val
            out[f"{prefix}_lower_sec"] = None if val is None else val * 60
            out[f"{prefix}_upper_sec"] = None if val is None else val * 60 + 59
            nonnull += val is not None

        standups_raw = attrs.get("grap_stand_land")
        standups = as_int(standups_raw)
        if standups_raw not in (None, "") and standups is None:
            stats["invalid_standup_transport"] += 1
            exclusion(exclusions, attrs, item, "invalid_standup_count_transport", field="grap_stand_land", raw_value=standups_raw)
            standups = None
        out["standups"] = standups
        nonnull += standups is not None

        if nonnull == 0:
            stats["empty_after_qa"] += 1
            exclusion(exclusions, attrs, item, "no_canonical_eligible_position_or_standup_values")
            continue

        pk = (fight_id, fighter_id, rnd)
        if pk in seen_pk:
            raise RuntimeError(f"duplicate canonical fighter_round_position PK after source gates: {pk}")
        seen_pk.add(pk)
        rows.append(out)

    # Fail-closed row validation against the contract and canonical participants.
    for row in rows:
        if int(row["round"]) < 1:
            raise RuntimeError("round zero leaked into fighter_round_position")
        for prefix in POSITION_MAP.values():
            bucket = row.get(f"{prefix}_bucket_min")
            lo = row.get(f"{prefix}_lower_sec")
            hi = row.get(f"{prefix}_upper_sec")
            if bucket is None:
                if lo is not None or hi is not None:
                    raise RuntimeError(f"interval bound exists without bucket: {prefix}")
                continue
            if not 0 <= int(bucket) <= 5:
                raise RuntimeError(f"canonical bucket outside 0..5: {prefix}={bucket}")
            if lo != int(bucket) * 60 or hi != int(bucket) * 60 + 59:
                raise RuntimeError(f"bad quantization interval: {prefix}={bucket}/{lo}/{hi}")

    rows.sort(key=lambda r: (r["fight_id"], r["fighter_id"], int(r["round"])))
    exclusions.sort(key=lambda r: (
        str(r.get("fightmetric_id") or ""), str(r.get("raw_color") or ""),
        str(r.get("round") or ""), str(r.get("resource_id") or ""),
        str(r.get("reason") or ""), str(r.get("field") or ""),
    ))
    write_csv(OUT, fields, rows)
    write_csv(EXCLUSIONS, EXCLUSION_FIELDS, exclusions)

    reason_counts = Counter(str(r["reason"]) for r in exclusions)
    populated_counts = {
        prefix: sum(r.get(f"{prefix}_bucket_min") is not None for r in rows)
        for prefix in POSITION_MAP.values()
    }
    populated_counts["standups"] = sum(r.get("standups") is not None for r in rows)

    audit = {
        "schema_version": 1,
        "canonical_contract_version": contract.get("contract_version"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": SOURCE,
        "source_snapshot_id": snapshot_id,
        "raw_fight_stat_rows": raw_rows,
        "canonical_rows": len(rows),
        "canonical_fights_with_position_rows": len({r["fight_id"] for r in rows}),
        "canonical_fighters_with_position_rows": len({r["fighter_id"] for r in rows}),
        "source_key_counts": dict(sorted(stats.items())),
        "populated_field_counts": populated_counts,
        "exclusions": len(exclusions),
        "exclusion_reason_counts": dict(sorted(reason_counts.items())),
        "rules": {
            "round_zero_excluded": True,
            "numeric_color_map": {"0": "red", "1": "blue"},
            "display_name_matching_used": False,
            "duplicate_source_versions_fail_closed": True,
            "position_bucket_allowed_range": [0, 5],
            "position_bucket_semantics": "floor_whole_minutes_with_explicit_interval_bounds",
            "exact_seconds_fabricated": False,
            "raw_anomalies_preserved_only_in_raw_and_exclusion_ledger": True,
        },
        "outputs": {
            "table": str(OUT.relative_to(ROOT)),
            "exclusions": str(EXCLUSIONS.relative_to(ROOT)),
        },
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "# Canonical FightMetric position v0\n\n"
        f"- Source snapshot: **{snapshot_id}**\n"
        f"- Canonical fighter-round rows: **{len(rows)}**\n"
        f"- Canonical fights represented: **{audit['canonical_fights_with_position_rows']}**\n"
        f"- Canonical fighters represented: **{audit['canonical_fighters_with_position_rows']}**\n"
        f"- Quarantined source items/field anomalies: **{len(exclusions)}**\n\n"
        "Only audited 0–5 floor-minute buckets are materialized. Interval second fields are quantization bounds, not exact observed duration.\n",
        encoding="utf-8",
    )

    # Extend canonical v0 manifest only after the table and audit are valid.
    manifest = json.loads(core_manifest_path.read_text(encoding="utf-8"))
    manifest.setdefault("counts", {})["fighter_round_position"] = len(rows)
    manifest.setdefault("counts", {})["fighter_round_position_exclusions"] = len(exclusions)
    manifest.setdefault("source_snapshots", {})[SOURCE] = snapshot_id
    file_entries = [x for x in manifest.get("files", []) if x.get("path") not in {
        str(OUT.relative_to(ROOT)), str(EXCLUSIONS.relative_to(ROOT)),
    }]
    for path in (OUT, EXCLUSIONS):
        file_entries.append({
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest["files"] = sorted(file_entries, key=lambda x: x["path"])
    manifest["generated_at_utc"] = audit["generated_at_utc"]
    manifest.setdefault("rules", {})["fightmetric_position_uses_quantized_buckets_only"] = True
    core_manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "canonical_rows": len(rows),
        "fights": audit["canonical_fights_with_position_rows"],
        "fighters": audit["canonical_fighters_with_position_rows"],
        "exclusions": len(exclusions),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
