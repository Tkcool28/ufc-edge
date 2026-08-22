#!/usr/bin/env python3
"""Materialize official UFC point-in-time athlete profiles into canonical v0.

Only already-trusted official athlete UUID -> canonical fighter links are used. The table is
a dated snapshot, not historical backfill. Mutable fields must never be projected backward
onto older fights by this data-layer builder.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data/raw/ufc_com_resources/athletes"
CANON = ROOT / "data/canonical/v0"
IDENTITY = CANON / "source_identity_links.csv"
CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
SEMANTICS = ROOT / "provenance/audits/ufc_athlete_profile_semantics_latest.json"
OUT = CANON / "fighter_profile_snapshots.csv"
EXCLUSIONS = ROOT / "data/derived/qa/canonical_ufc_profile_snapshot_exclusions_v0.csv"
AUDIT_JSON = ROOT / "provenance/audits/canonical_ufc_profile_snapshots_v0_latest.json"
AUDIT_MD = ROOT / "provenance/audits/canonical_ufc_profile_snapshots_v0_latest.md"
EXCLUSION_FIELDS = ["athlete_uuid", "canonical_fighter_id", "reason", "field", "raw_value", "details"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def latest_snapshot() -> Path:
    candidates = sorted(p for p in RAW_ROOT.iterdir() if p.is_dir() and (p / "manifest.json").is_file())
    for path in reversed(candidates):
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("complete_collection_snapshot") is True or manifest.get("semantics", {}).get("complete_collection_snapshot") is True:
            return path
    raise RuntimeError("No complete official UFC athlete snapshot")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def label(item: dict[str, Any] | None) -> str | None:
    if not item:
        return None
    attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
    for key in ("title", "name", "label"):
        value = attrs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def relationship_keys(item: dict[str, Any], name: str) -> list[tuple[str, str]]:
    rel = (item.get("relationships") or {}).get(name)
    data = rel.get("data") if isinstance(rel, dict) else None
    if isinstance(data, dict) and data.get("id"):
        return [(str(data.get("type") or ""), str(data["id"]))]
    if isinstance(data, list):
        return [(str(x.get("type") or ""), str(x["id"])) for x in data if isinstance(x, dict) and x.get("id")]
    return []


def relationship_labels(item: dict[str, Any], name: str, included: dict[tuple[str, str], dict[str, Any]]) -> list[str]:
    values = []
    for key in relationship_keys(item, name):
        lab = label(included.get(key))
        if lab:
            values.append(lab)
    return sorted(set(values), key=lambda x: x.casefold())


def address_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"expected structured address object, got {type(value).__name__}")
    parts: list[str] = []
    for key in ("locality", "administrative_area", "country_code"):
        raw = value.get(key)
        if raw is None:
            continue
        text = str(raw).strip()
        if text and text not in parts:
            parts.append(text)
    return ", ".join(parts) if parts else None


def profile_weight(value: Any) -> str | None:
    if value is None or value == "":
        return None
    try:
        dec = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ValueError(f"invalid profile weight {value!r}") from exc
    if dec == 0:
        return None
    if dec < 80 or dec > 400:
        raise ValueError(f"profile weight outside contract range: {value!r}")
    # Decimal normal form without exponent; retain half-pound precision if present.
    return format(dec.normalize(), "f")


def main() -> int:
    semantics = json.loads(SEMANTICS.read_text(encoding="utf-8"))
    if semantics.get("decision", {}).get("point_in_time_only") is not True:
        raise RuntimeError("Athlete profile point-in-time semantic is not audited")

    snapshot = latest_snapshot()
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    observed_at = manifest.get("completed_at_utc")
    if not observed_at:
        raise RuntimeError("Athlete snapshot lacks completed_at_utc")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fields = list(contract["tables"]["fighter_profile_snapshots"]["fields"])

    # Only trusted official athlete UUID links are eligible.
    canonical_by_athlete: dict[str, str] = {}
    for row in read_csv(IDENTITY):
        if row.get("entity_type") != "fighter" or row.get("source_name") != "ufc_com" or row.get("review_status") != "trusted":
            continue
        sid, cid = row.get("source_id") or "", row.get("canonical_id") or ""
        if not sid or not cid:
            continue
        prior = canonical_by_athlete.get(sid)
        if prior and prior != cid:
            raise RuntimeError(f"Official athlete UUID maps to multiple canonical fighters: {sid}")
        canonical_by_athlete[sid] = cid

    records_by_canonical: dict[str, list[dict[str, Any]]] = defaultdict(list)
    exclusions: list[dict[str, Any]] = []
    stats = Counter()

    def reject(uid: str, cid: str, reason: str, field: str = "", raw: Any = "", details: str = "") -> None:
        exclusions.append({
            "athlete_uuid": uid,
            "canonical_fighter_id": cid,
            "reason": reason,
            "field": field,
            "raw_value": json.dumps(raw, sort_keys=True) if isinstance(raw, (dict, list)) else str(raw or ""),
            "details": details,
        })

    pages = [Path(x["path"]) for x in manifest.get("files") or [] if x.get("path")]
    raw_athletes = 0
    for page in pages:
        payload = json.loads(page.read_text(encoding="utf-8"))
        included = {
            (str(x.get("type") or ""), str(x["id"])): x
            for x in payload.get("included") or []
            if isinstance(x, dict) and x.get("id")
        }
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or not item.get("id"):
                continue
            raw_athletes += 1
            uid = str(item["id"])
            cid = canonical_by_athlete.get(uid)
            if not cid:
                stats["unlinked_official_athlete"] += 1
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}

            row: dict[str, Any] = {"fighter_id": cid, "observed_at_utc": observed_at}
            try:
                row["listed_weight_lbs"] = profile_weight(attrs.get("stats_weight"))
            except ValueError as exc:
                reject(uid, cid, "invalid_listed_weight", "stats_weight", attrs.get("stats_weight"), str(exc))
                row["listed_weight_lbs"] = None

            wc = relationship_labels(item, "stats_weight_class", included)
            gym = relationship_labels(item, "gym", included)
            style = relationship_labels(item, "fighting_style", included)
            status = relationship_labels(item, "athlete_status", included)
            if len(wc) > 1:
                reject(uid, cid, "multiple_weight_class_labels", "relationships.stats_weight_class", wc)
                row["listed_weight_class"] = None
            else:
                row["listed_weight_class"] = wc[0] if wc else None
            if len(gym) > 1:
                reject(uid, cid, "multiple_gym_labels", "relationships.gym", gym)
                row["gym_text"] = None
            else:
                row["gym_text"] = gym[0] if gym else None
            row["fighting_style_text"] = "; ".join(style) if style else None
            if len(status) > 1:
                reject(uid, cid, "multiple_athlete_status_labels", "relationships.athlete_status", status)
                row["status_text"] = None
            else:
                row["status_text"] = status[0] if status else None

            for source_field, target_field in (("residence", "residence_text"), ("origin", "origin_text")):
                try:
                    row[target_field] = address_text(attrs.get(source_field))
                except ValueError as exc:
                    reject(uid, cid, "invalid_structured_address", source_field, attrs.get(source_field), str(exc))
                    row[target_field] = None

            records_by_canonical[cid].append({"uid": uid, "row": row})

    rows: list[dict[str, Any]] = []
    for cid, group in sorted(records_by_canonical.items()):
        if len(group) != 1:
            stats["multiple_official_athlete_nodes_per_canonical_fighter"] += 1
            for record in group:
                reject(record["uid"], cid, "multiple_official_athlete_nodes_per_canonical_fighter", details=f"node_count={len(group)}")
            continue
        row = group[0]["row"]
        if all(row.get(field) in (None, "") for field in fields if field not in {"fighter_id", "observed_at_utc"}):
            stats["empty_profile_after_normalization"] += 1
            reject(group[0]["uid"], cid, "empty_profile_after_normalization")
            continue
        rows.append(row)

    rows.sort(key=lambda r: (r["fighter_id"], r["observed_at_utc"]))
    exclusions.sort(key=lambda r: (r["canonical_fighter_id"], r["athlete_uuid"], r["reason"], r["field"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        w.writeheader()
        for row in rows:
            w.writerow({k: "" if row.get(k) is None else row.get(k) for k in fields})
    EXCLUSIONS.parent.mkdir(parents=True, exist_ok=True)
    with EXCLUSIONS.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=EXCLUSION_FIELDS)
        w.writeheader(); w.writerows(exclusions)

    populated = {
        field: sum(bool(str(r.get(field) or "").strip()) for r in rows)
        for field in fields if field not in {"fighter_id", "observed_at_utc"}
    }
    audit = {
        "schema_version": 1,
        "canonical_contract_version": contract.get("contract_version"),
        "source": "ufc_com_official",
        "source_snapshot_id": snapshot.name,
        "observed_at_utc": observed_at,
        "raw_official_athletes": raw_athletes,
        "trusted_official_athlete_links": len(canonical_by_athlete),
        "canonical_profile_rows": len(rows),
        "exclusions": len(exclusions),
        "qa_counts": dict(sorted(stats.items())),
        "populated_field_counts": populated,
        "rules": {
            "point_in_time_only": True,
            "historical_backfill_performed": False,
            "display_name_matching_used": False,
            "node_status_boolean_used_as_athlete_status": False,
            "stats_weight_zero_is_missing": True,
            "multi_relationship_style_labels_sorted_joined": True,
        },
        "outputs": {"table": str(OUT.relative_to(ROOT)), "exclusions": str(EXCLUSIONS.relative_to(ROOT))},
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "# Canonical official UFC profile snapshots v0\n\n"
        f"- Snapshot: **{snapshot.name}** at **{observed_at}**\n"
        f"- Trusted athlete UUID links: **{len(canonical_by_athlete)}**\n"
        f"- Canonical profile rows: **{len(rows)}**\n"
        f"- QA/exclusion records: **{len(exclusions)}**\n\n"
        "These are point-in-time profile observations. They are not historical backfill.\n",
        encoding="utf-8",
    )

    manifest_path = CANON / "manifest.json"
    canonical_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if canonical_manifest.get("canonical_contract_version") != contract.get("contract_version"):
        raise RuntimeError("canonical manifest contract version mismatch")
    canonical_manifest.setdefault("counts", {})["fighter_profile_snapshots"] = len(rows)
    canonical_manifest.setdefault("counts", {})["fighter_profile_snapshot_exclusions"] = len(exclusions)
    canonical_manifest.setdefault("source_snapshots", {})["ufc_com_official_athletes"] = snapshot.name
    changed_paths = {str(OUT.relative_to(ROOT)), str(EXCLUSIONS.relative_to(ROOT))}
    entries = [x for x in canonical_manifest.get("files", []) if x.get("path") not in changed_paths]
    for path in (OUT, EXCLUSIONS):
        entries.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    canonical_manifest["files"] = sorted(entries, key=lambda x: x["path"])
    canonical_manifest["generated_at_utc"] = observed_at
    canonical_manifest.setdefault("rules", {})["ufc_profiles_are_point_in_time_snapshots"] = True
    manifest_path.write_text(json.dumps(canonical_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "raw_athletes": raw_athletes,
        "trusted_links": len(canonical_by_athlete),
        "canonical_profiles": len(rows),
        "exclusions": len(exclusions),
        "populated": populated,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
