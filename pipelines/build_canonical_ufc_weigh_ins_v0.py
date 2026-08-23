#!/usr/bin/env python3
"""Materialize context-clean official UFC scale-weight observations into canonical v0.

DATA PHASE ONLY.

Only the audited v2 candidate set is eligible. This builder intentionally promotes only
fight identity, fighter identity, and explicit official scale weight. Article publication
time is not treated as weigh-in date. Attempt, miss, contract-limit, pounds-over,
catchweight, purse-penalty, and status semantics remain null unless separately proven.
"""
from __future__ import annotations

import csv
import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data/canonical/v0"
CANDIDATE = ROOT / "data/derived/identity/ufc_weigh_in_canonical_candidate_v2.csv"
CANDIDATE_AUDIT = ROOT / "provenance/audits/ufc_weigh_in_canonical_candidate_v2_latest.json"
CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
FIGHTS = CANON / "fights.csv"
WEIGH_INS = CANON / "weigh_ins.csv"
PROVENANCE = CANON / "field_provenance.csv"
MANIFEST = CANON / "manifest.json"
EXCLUSIONS = ROOT / "data/derived/qa/canonical_ufc_weigh_in_exclusions_v0.csv"
AUDIT_JSON = ROOT / "provenance/audits/canonical_ufc_weigh_ins_v0_latest.json"
AUDIT_MD = ROOT / "provenance/audits/canonical_ufc_weigh_ins_v0_latest.md"

PROJECT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/Tkcool28/ufc-edge/canonical/v1")
SOURCE = "ufc_official_content"
SOURCE_SNAPSHOT = "20260821T210000Z"
EXCLUSION_FIELDS = ["article_url", "article_title", "fight_id", "fighter_id", "reason"]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row.get(k) is None else row.get(k) for k in fields})


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def mint_observation_id(row: dict[str, str]) -> str:
    stable = "|".join([
        (row.get("article_url") or "").strip(),
        f"bout:{(row.get('bout_ordinal_in_article') or '').strip()}",
        f"side:{(row.get('source_side') or '').strip()}",
        (row.get("fight_id") or "").strip(),
        (row.get("fighter_id") or "").strip(),
    ])
    return str(uuid.uuid5(PROJECT_NAMESPACE, f"weigh_in|{SOURCE}|{stable}"))


def canonical_row(row: dict[str, Any], fields: list[str]) -> dict[str, str]:
    return {field: "" if row.get(field) is None else str(row.get(field)) for field in fields}


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    candidate_audit = json.loads(CANDIDATE_AUDIT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    if contract.get("contract_version") != "0.4.0-draft":
        raise RuntimeError(f"unexpected canonical contract: {contract.get('contract_version')}")
    if manifest.get("canonical_contract_version") != contract.get("contract_version"):
        raise RuntimeError("canonical manifest/contract version mismatch")
    decision = candidate_audit.get("decision") or {}
    required_truths = {
        "identity_promotable": True,
        "scale_weight_promotable": True,
        "exact_two_observations_per_fight": True,
        "explicit_non_ufc_article_context_excluded": True,
        "weigh_in_date_promoted": False,
        "attempt_number_promoted": False,
        "marker_semantics_promoted": False,
    }
    for key, expected in required_truths.items():
        if decision.get(key) is not expected:
            raise RuntimeError(f"candidate decision gate changed: {key}={decision.get(key)!r}")
    if candidate_audit.get("canonical_candidate_rows") != 12890 or candidate_audit.get("canonical_candidate_fights") != 6445:
        raise RuntimeError("candidate cardinality gate changed")
    if candidate_audit.get("excluded_rows") != 2:
        raise RuntimeError("candidate exclusion gate changed")

    candidate_fields, candidates = read_csv(CANDIDATE)
    _fight_fields, fights = read_csv(FIGHTS)
    prov_fields, current_prov = read_csv(PROVENANCE)
    weigh_fields = list(contract["tables"]["weigh_ins"]["fields"])
    contract_prov_fields = list(contract["tables"]["field_provenance"]["fields"])
    if set(prov_fields) != set(contract_prov_fields):
        raise RuntimeError("field_provenance header drift")
    if len(candidates) != 12890:
        raise RuntimeError(f"candidate rows changed: {len(candidates)}")

    fight_by_id = {(r.get("fight_id") or "").strip(): r for r in fights}
    desired: list[dict[str, Any]] = []
    seen_pair: set[tuple[str, str]] = set()
    seen_obs: set[str] = set()
    marker_rows = 0

    for row in candidates:
        fight_id = (row.get("fight_id") or "").strip()
        fighter_id = (row.get("fighter_id") or "").strip()
        opponent_id = (row.get("opponent_id") or "").strip()
        fight = fight_by_id.get(fight_id)
        if not fight or (fight.get("promotion") or "").strip() != "UFC":
            raise RuntimeError(f"candidate references non-UFC/missing fight: {fight_id}")
        participants = {(fight.get("fighter_a_id") or "").strip(), (fight.get("fighter_b_id") or "").strip()}
        if {fighter_id, opponent_id} != participants or fighter_id == opponent_id:
            raise RuntimeError(f"candidate participant integrity failure: {fight_id}/{fighter_id}")
        pair = (fight_id, fighter_id)
        if pair in seen_pair:
            raise RuntimeError(f"duplicate candidate fight/fighter pair: {pair}")
        seen_pair.add(pair)
        try:
            weight = Decimal((row.get("scale_weight_lbs") or "").strip())
        except InvalidOperation as exc:
            raise RuntimeError(f"invalid scale weight: {row.get('scale_weight_lbs')!r}") from exc
        if weight < Decimal("80") or weight > Decimal("400"):
            raise RuntimeError(f"scale weight outside contract: {weight}")
        obs_id = mint_observation_id(row)
        if obs_id in seen_obs:
            raise RuntimeError(f"duplicate minted observation id: {obs_id}")
        seen_obs.add(obs_id)
        if (row.get("marker") or "").strip():
            marker_rows += 1

        desired.append({
            "weigh_in_observation_id": obs_id,
            "fight_id": fight_id,
            "fighter_id": fighter_id,
            "weigh_in_date": None,
            "attempt_number": None,
            "scale_weight_lbs": format(weight.normalize(), "f"),
            "contract_limit_lbs": None,
            "missed_weight": None,
            "pounds_over": None,
            "catchweight_bout": None,
            "purse_penalty_pct": None,
            "official_status_text": None,
        })

    if len(desired) != 12890 or len(seen_pair) != 12890 or marker_rows != 172:
        raise RuntimeError(f"weigh-in materialization gate changed rows={len(desired)} pairs={len(seen_pair)} markers={marker_rows}")
    desired.sort(key=lambda r: (str(r["fight_id"]), str(r["fighter_id"]), str(r["weigh_in_observation_id"])))

    if WEIGH_INS.exists():
        existing_fields, existing_rows = read_csv(WEIGH_INS)
        if set(existing_fields) != set(weigh_fields):
            raise RuntimeError("existing weigh_ins header drift")
        existing = sorted((canonical_row(r, weigh_fields) for r in existing_rows), key=lambda r: r["weigh_in_observation_id"])
        wanted = sorted((canonical_row(r, weigh_fields) for r in desired), key=lambda r: r["weigh_in_observation_id"])
        if existing != wanted:
            raise RuntimeError("existing weigh_ins differ from pinned desired-state build; refusing overwrite")
    write_csv(WEIGH_INS, weigh_fields, desired)

    # Preserve the two explicitly diagnosed false-transport rows as QA exclusions.
    exclusions = []
    for item in candidate_audit.get("exclusion_examples") or []:
        exclusions.append({field: item.get(field) or "" for field in EXCLUSION_FIELDS})
    exclusions.sort(key=lambda r: (r["article_url"], r["fighter_id"]))
    if len(exclusions) != 2 or {r["reason"] for r in exclusions} != {"explicit_strikeforce_article_context"}:
        raise RuntimeError("canonical weigh-in exclusion evidence changed")
    write_csv(EXCLUSIONS, EXCLUSION_FIELDS, exclusions)

    # Add selected-field lineage without promoting unresolved annotation semantics.
    pk_fields = contract["tables"]["field_provenance"]["primary_key"]
    prov_by_pk: dict[tuple[str, ...], dict[str, str]] = {}
    for row in current_prov:
        key = tuple(row.get(k) or "" for k in pk_fields)
        row_s = {k: row.get(k) or "" for k in prov_fields}
        if key in prov_by_pk and prov_by_pk[key] != row_s:
            raise RuntimeError(f"conflicting existing provenance key: {key}")
        prov_by_pk[key] = row_s

    added_prov = 0
    candidate_by_pair = {
        ((r.get("fight_id") or "").strip(), (r.get("fighter_id") or "").strip()): r for r in candidates
    }
    for record in desired:
        src = candidate_by_pair[(str(record["fight_id"]), str(record["fighter_id"]))]
        source_record_id = "|".join([
            (src.get("article_url") or "").strip(),
            f"bout:{(src.get('bout_ordinal_in_article') or '').strip()}",
            f"side:{(src.get('source_side') or '').strip()}",
        ])
        rule = "official_ufc_article_context+singleton_event_intersection+unique_contextual_participant_pair"
        marker = (src.get("marker") or "").strip()
        line_note = f"official article source line {src.get('source_line_number') or ''}".strip()
        if marker:
            line_note += f"; inline marker {marker!r} preserved raw only; marker semantics not promoted"
        rows = [
            ("weigh_in_observation_id", "article_url+bout_ordinal+source_side", "deterministic UUIDv5 observation identity"),
            ("fight_id", "candidate_event_id+participant_pair", "audited contextual fight identity"),
            ("fighter_id", "fighter_text+contextual participant pair", "audited contextual fighter identity"),
            ("scale_weight_lbs", "scale_weight_lbs", line_note),
        ]
        for field_name, source_field, note in rows:
            prov = {
                "table_name": "weigh_ins",
                "row_key": record["weigh_in_observation_id"],
                "field_name": field_name,
                "source_name": SOURCE,
                "source_snapshot_id": SOURCE_SNAPSHOT,
                "source_record_id": source_record_id,
                "source_field_name": source_field,
                "selection_status": "selected",
                "selection_rule": rule,
                "quality_note": note,
            }
            prov_s = {k: "" if prov.get(k) is None else str(prov.get(k)) for k in prov_fields}
            key = tuple(prov_s.get(k, "") for k in pk_fields)
            existing = prov_by_pk.get(key)
            if existing and existing != prov_s:
                raise RuntimeError(f"canonical weigh-in provenance conflict: {key}")
            if not existing:
                current_prov.append(prov)
                prov_by_pk[key] = prov_s
                added_prov += 1

    if added_prov not in {0, 51560}:
        raise RuntimeError(f"unexpected partial provenance append: {added_prov}")
    current_prov.sort(key=lambda r: tuple(str(r.get(k) or "") for k in pk_fields))
    write_csv(PROVENANCE, prov_fields, current_prov)

    audit = {
        "schema_version": 1,
        "canonical_contract_version": contract.get("contract_version"),
        "source": SOURCE,
        "source_snapshot_id": SOURCE_SNAPSHOT,
        "canonical_weigh_in_rows": len(desired),
        "canonical_fights_covered": len({str(r["fight_id"]) for r in desired}),
        "canonical_fighters_covered": len({str(r["fighter_id"]) for r in desired}),
        "raw_marker_rows_not_semantically_promoted": marker_rows,
        "qa_exclusions": len(exclusions),
        "field_provenance_rows_added_this_run": added_prov,
        "rules": {
            "scale_weight_promoted": True,
            "fight_and_fighter_identity_promoted": True,
            "weigh_in_date_promoted": False,
            "attempt_number_promoted": False,
            "contract_limit_promoted": False,
            "missed_weight_promoted": False,
            "pounds_over_promoted": False,
            "catchweight_promoted": False,
            "purse_penalty_promoted": False,
            "official_status_text_promoted": False,
            "article_publication_time_used_as_weigh_in_date": False,
            "marker_global_semantics_used": False,
            "roster_weight_used": False,
        },
        "outputs": {
            "weigh_ins": str(WEIGH_INS.relative_to(ROOT)),
            "field_provenance": str(PROVENANCE.relative_to(ROOT)),
            "exclusions": str(EXCLUSIONS.relative_to(ROOT)),
        },
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "# Canonical UFC weigh-ins v0\n\n"
        f"- Canonical observations: **{len(desired)}**\n"
        f"- UFC fights covered: **{audit['canonical_fights_covered']}**\n"
        f"- Fighters covered: **{audit['canonical_fighters_covered']}**\n"
        f"- Marker-bearing source rows retained raw-only: **{marker_rows}**\n"
        f"- Context QA exclusions: **{len(exclusions)}**\n\n"
        "Only official scale weight and audited fight/fighter identity are promoted. "
        "Date, attempt, miss, contract-limit, catchweight and penalty semantics remain null unless source-explicit and separately resolved.\n",
        encoding="utf-8",
    )

    counts = manifest.setdefault("counts", {})
    counts["weigh_ins"] = len(desired)
    counts["canonical_ufc_weigh_in_exclusions"] = len(exclusions)
    counts["field_provenance"] = len(current_prov)
    manifest.setdefault("source_snapshots", {})["ufc_official_weigh_in_articles"] = SOURCE_SNAPSHOT
    rules = manifest.setdefault("rules", {})
    rules["official_ufc_weigh_in_scale_weight_requires_context_clean_fight_fighter_identity"] = True
    rules["weigh_in_annotation_semantics_are_null_unless_source_explicit"] = True
    rules["article_publication_time_is_not_weigh_in_date"] = True
    manifest["generated_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    changed = {str(p.relative_to(ROOT)) for p in (WEIGH_INS, PROVENANCE, EXCLUSIONS)}
    entries = [x for x in manifest.get("files", []) if x.get("path") not in changed]
    for path in (WEIGH_INS, PROVENANCE, EXCLUSIONS):
        entries.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest["files"] = sorted(entries, key=lambda x: x.get("path") or "")
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "canonical_weigh_ins": len(desired),
        "fights_covered": audit["canonical_fights_covered"],
        "fighters_covered": audit["canonical_fighters_covered"],
        "marker_rows_raw_only": marker_rows,
        "qa_exclusions": len(exclusions),
        "provenance_rows_added": added_prov,
        "provenance_rows_total": len(current_prov),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
