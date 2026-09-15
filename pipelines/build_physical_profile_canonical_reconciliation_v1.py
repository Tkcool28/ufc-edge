#!/usr/bin/env python3
"""Build canonical DATA v1 by validated UFC Official physical-profile NULL-FILL.

This is a DATA-only reconciliation. It reads immutable v0 canonical DATA and the
pinned 2026-08-20 official athlete snapshot; it does not rebuild features or models.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from ufc_edge.data.physical_profile_reconciliation import agreement_category, official_stats, official_uuid, recovery_selection, selection, walk_records

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/canonical/v0"
OUT = ROOT / "data/canonical/v1"
RAW = ROOT / "data/raw/ufc_com_resources/athletes/20260820T194553Z"
AUDIT_JSON = ROOT / "provenance/audits/physical_profile_canonical_reconciliation_v1.json"
AUDIT_MD = ROOT / "provenance/audits/physical_profile_canonical_reconciliation_v1.md"
COHORT = ROOT / "data/derived/qa/physical_profile_recent_cohort_v1.csv"
REMAINING = ROOT / "data/derived/qa/physical_profile_recent_nulls_v1.csv"
RECOVERY = ROOT / "data/supplemental/physical_profile_recent_recovery_v1.csv"
SNAPSHOT_ID = RAW.name
PROV_FIELDS = ["table_name", "row_key", "field_name", "source_name", "source_snapshot_id", "source_record_id", "source_field_name", "selection_status", "selection_rule", "quality_note"]
FIELDS = {"height": ("height_cm", "stats_height"), "reach_arm": ("reach_cm", "stats_reach_arm"), "reach_leg": ("leg_reach_cm", "stats_reach_leg")}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        w.writeheader()
        w.writerows(rows)


def scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return str(value)


def official_by_uuid() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for page in sorted(RAW.glob("page_*.json")):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for record in walk_records(payload):
            uid, stats = official_uuid(record), official_stats(record)
            if not uid or not stats:
                continue
            normalized = {"height": stats.get("height", stats.get("stats_height")), "reach_arm": stats.get("reach_arm", stats.get("stats_reach_arm")), "reach_leg": stats.get("reach_leg", stats.get("stats_reach_leg"))}
            if uid in found and found[uid] != normalized:
                raise RuntimeError(f"conflicting official profile observations for athlete {uid}")
            found[uid] = normalized
    if not found:
        raise RuntimeError("no official athlete profile records detected; refuse reconciliation")
    return found


def event_years() -> dict[str, set[int]]:
    years: dict[str, set[int]] = defaultdict(set)
    event_year = {r["event_id"]: int(r["event_date"][:4]) for r in read_csv(BASE / "events.csv") if r.get("event_date")}
    for fight in read_csv(BASE / "fights.csv"):
        year = event_year.get(fight["event_id"])
        if year:
            years[fight["fighter_a_id"]].add(year)
            years[fight["fighter_b_id"]].add(year)
    return years


def main() -> int:
    if not BASE.exists():
        raise RuntimeError("canonical v0 is required and must be preserved")
    athletes, base_fighters, identities = official_by_uuid(), read_csv(BASE / "fighters.csv"), read_csv(BASE / "source_identity_links.csv")
    recovery_rows = read_csv(RECOVERY)
    recovery = {}
    for evidence in recovery_rows:
        key = (evidence["fighter_id"], evidence["field_name"])
        if key in recovery:
            raise RuntimeError(f"duplicate supplemental recovery row: {key}")
        recovery[key] = evidence
    official_link = {r["canonical_id"]: r["source_id"] for r in identities if r["entity_type"] == "fighter" and r["source_name"] == "ufc_com" and r["source_entity_type"] == "athlete" and r["review_status"] == "trusted"}
    provenance = read_csv(BASE / "field_provenance.csv")
    output, additions = [], []
    overlap = {key: Counter() for key in ("height", "reach_arm")}
    largest = {key: [] for key in ("height", "reach_arm")}
    rejected: Counter[str] = Counter()
    years = event_years()

    for row in base_fighters:
        out = dict(row)
        uid = official_link.get(row["fighter_id"])
        stats = athletes.get(uid, {}) if uid else {}
        for key, (canonical_field, raw_field) in FIELDS.items():
            raw, trusted = stats.get(key), bool(uid and uid in athletes)
            selected, status, checked = selection(field=key, canonical_value=row[canonical_field], official_raw=raw, trusted_identity=trusted, allow_fill=(key != "reach_leg"))
            if key in overlap and row[canonical_field] and checked.accepted:
                diff, category = agreement_category(row[canonical_field], checked.value_cm)
                overlap[key][category] += 1
                largest[key].append({"fighter_id": row["fighter_id"], "fighter": row["canonical_name"], "greco_cm": row[canonical_field], "official_raw_inches": checked.raw_value or "", "official_cm": scalar(checked.value_cm), "difference_inches": scalar(diff), "category": category})
            if not checked.accepted and checked.reason not in (None, "source_null"):
                rejected[f"{key}:{checked.reason}"] += 1
            if not row[canonical_field] and selected is not None:
                out[canonical_field] = scalar(selected)
            if uid:
                additions.append({"table_name": "fighters", "row_key": row["fighter_id"], "field_name": canonical_field, "source_name": "ufc_com", "source_snapshot_id": SNAPSHOT_ID, "source_record_id": uid, "source_field_name": raw_field, "selection_status": status, "selection_rule": "validated_official_null_fill_then_preserve_greco" if key != "reach_leg" else "validated_official_leg_reach_enrichment_disabled", "quality_note": checked.reason or "validated_inches"})
        output.append(out)

    # Supplemental evidence must account for exactly the recent fields still null
    # after the existing Greco/UFC Official reconciliation.
    official_only_output = [dict(r) for r in output]
    expected_recovery_keys = set()
    for row in official_only_output:
        if set(years.get(row["fighter_id"], ())) & {2025, 2026}:
            for canonical_field in ("height_cm", "reach_cm"):
                if not row[canonical_field]:
                    expected_recovery_keys.add((row["fighter_id"], canonical_field))
    if set(recovery) != expected_recovery_keys:
        missing = sorted(expected_recovery_keys - set(recovery))
        extra = sorted(set(recovery) - expected_recovery_keys)
        raise RuntimeError(f"supplemental recovery cohort mismatch missing={missing} extra={extra}")

    resolution_counts = Counter()
    supplemental_changed = []
    for out in output:
        recent_years = sorted(y for y in years.get(out["fighter_id"], set()) if y in {2025, 2026})
        if not recent_years:
            continue
        for canonical_field in ("height_cm", "reach_cm"):
            evidence = recovery.get((out["fighter_id"], canonical_field))
            if evidence is None:
                continue
            if evidence["fighter_name"] != out["canonical_name"]:
                raise RuntimeError(f"supplemental fighter name mismatch for {out['fighter_id']}")
            if evidence["fight_years"] != ",".join(map(str, recent_years)):
                raise RuntimeError(f"supplemental fight-year mismatch for {out['fighter_id']} {canonical_field}")
            value, status, checked = recovery_selection(
                field_name=canonical_field,
                canonical_value=out[canonical_field],
                raw_value=evidence["raw_value"],
                raw_unit=evidence["raw_unit"],
                review_status=evidence["review_status"],
                resolution_status=evidence["resolution_status"],
            )
            resolution_counts[evidence["resolution_status"]] += 1
            if evidence["review_status"] == "accepted":
                expected_cm = Decimal(evidence["normalized_value_cm"])
                if checked.value_cm != expected_cm:
                    raise RuntimeError(
                        f"supplemental normalized value mismatch for {out['fighter_id']} {canonical_field}: "
                        f"computed={checked.value_cm} evidence={expected_cm}"
                    )
                if value is None:
                    raise RuntimeError(f"accepted supplemental evidence did not emit: {out['fighter_id']} {canonical_field}")
                before_value = out[canonical_field]
                out[canonical_field] = scalar(value)
                supplemental_changed.append(
                    {
                        "fighter_id": out["fighter_id"],
                        "fighter": out["canonical_name"],
                        "field_name": canonical_field,
                        "before": before_value,
                        "after": out[canonical_field],
                        "resolution_status": evidence["resolution_status"],
                    }
                )
            elif value is not None:
                raise RuntimeError(f"non-accepted supplemental evidence emitted canonical value: {out['fighter_id']} {canonical_field}")

            additions.append(
                {
                    "table_name": "fighters",
                    "row_key": out["fighter_id"],
                    "field_name": canonical_field,
                    "source_name": "physical_profile_recent_recovery_v1",
                    "source_snapshot_id": evidence["retrieved_at"],
                    "source_record_id": evidence["source_url_or_id"] or f"{out['fighter_id']}:{canonical_field}",
                    "source_field_name": "raw_value",
                    "selection_status": status,
                    "selection_rule": "prior_populated_canonical_retained_else_validated_official_else_governed_supplemental_null_fill",
                    "quality_note": evidence["resolution_status"] + "; " + evidence["notes"],
                }
            )

    if len(recovery_rows) != sum(resolution_counts.values()):
        raise RuntimeError("supplemental recovery resolution accounting is incomplete")

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "fighters.csv", list(base_fighters[0]), output)
    for filename in ("events.csv", "fights.csv", "fighter_round_stats.csv", "source_identity_links.csv"):
        (OUT / filename).write_bytes((BASE / filename).read_bytes())
    all_provenance = provenance + additions
    all_provenance.sort(key=lambda r: (r["table_name"], r["row_key"], r["field_name"], r["source_name"], r["source_record_id"]))
    write_csv(OUT / "field_provenance.csv", PROV_FIELDS, all_provenance)

    before_by_id = {r["fighter_id"]: r for r in base_fighters}
    cohort_rows, remaining = [], []
    for after in output:
        before = before_by_id[after["fighter_id"]]
        recent = sorted(y for y in years.get(after["fighter_id"], set()) if y in {2025, 2026})
        uid, stats = official_link.get(after["fighter_id"], ""), athletes.get(official_link.get(after["fighter_id"], ""), {})
        if recent and (not before["height_cm"] or not before["reach_cm"]):
            cohort_rows.append({"fighter_id": after["fighter_id"], "fighter": after["canonical_name"], "years": ",".join(map(str, recent)), "height_before_cm": before["height_cm"], "official_height_raw": scalar(stats.get("height")), "height_after_cm": after["height_cm"], "reach_before_cm": before["reach_cm"], "official_reach_arm_raw": scalar(stats.get("reach_arm")), "reach_after_cm": after["reach_cm"], "official_athlete_uuid": uid})
        if recent:
            for key, (canonical_field, _) in list(FIELDS.items())[:2]:
                if not after[canonical_field]:
                    _, status, checked = selection(field=key, canonical_value=before[canonical_field], official_raw=stats.get(key), trusted_identity=bool(uid and uid in athletes))
                    remaining.append({"fighter_id": after["fighter_id"], "fighter": after["canonical_name"], "field": canonical_field, "greco_state": "null", "official_state": checked.reason or "populated", "canonical_reason": status, "official_athlete_uuid": uid})
    cohort_rows.sort(key=lambda r: (r["fighter"], r["fighter_id"]))
    remaining.sort(key=lambda r: (r["fighter"], r["field"]))
    cohort_fields = ["fighter_id", "fighter", "years", "height_before_cm", "official_height_raw", "height_after_cm", "reach_before_cm", "official_reach_arm_raw", "reach_after_cm", "official_athlete_uuid"]
    remaining_fields = ["fighter_id", "fighter", "field", "greco_state", "official_state", "canonical_reason", "official_athlete_uuid"]
    write_csv(COHORT, cohort_fields, cohort_rows)
    write_csv(REMAINING, remaining_fields, remaining)

    official_only_by_id = {r["fighter_id"]: r for r in official_only_output}
    coverage = {}
    v0_to_official_coverage = {}
    for period, wanted in {"global": None, "2024": {2024}, "2025": {2025}, "2026": {2026}}.items():
        population = [r for r in output if wanted is None or set(years.get(r["fighter_id"], ())) & wanted]
        completion_before = [official_only_by_id[r["fighter_id"]] for r in population]
        v0_before = [before_by_id[r["fighter_id"]] for r in population]
        official_rows = [official_only_by_id[r["fighter_id"]] for r in population]
        coverage[period] = {
            "fighters": len(population),
            "height_before_null": sum(not r["height_cm"] for r in completion_before),
            "height_after_null": sum(not r["height_cm"] for r in population),
            "reach_before_null": sum(not r["reach_cm"] for r in completion_before),
            "reach_after_null": sum(not r["reach_cm"] for r in population),
        }
        v0_to_official_coverage[period] = {
            "fighters": len(population),
            "height_before_null": sum(not r["height_cm"] for r in v0_before),
            "height_after_null": sum(not r["height_cm"] for r in official_rows),
            "reach_before_null": sum(not r["reach_cm"] for r in v0_before),
            "reach_after_null": sum(not r["reach_cm"] for r in official_rows),
        }

    largest = {field: sorted(rows, key=lambda r: Decimal(r["difference_inches"]), reverse=True)[:25] for field, rows in largest.items()}
    target_keys = set(recovery)
    changed_keys = {(r["fighter_id"], r["field_name"]) for r in supplemental_changed}
    if not changed_keys <= target_keys:
        raise RuntimeError("supplemental recovery changed a non-target field")
    manifest = {
        "schema_version": 3,
        "build": "physical_profile_canonical_reconciliation_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base_canonical_version": "v0",
        "official_snapshot": SNAPSHOT_ID,
        "supplemental_recovery": str(RECOVERY.relative_to(ROOT)),
        "source_policy": "populated canonical/Greco retained; validated UFC Official null-fill; then validated governed supplemental recovery null-fill",
        "temporal_semantics": "static athlete attributes retain actual source observation/retrieval timestamps; no pre-fight observation claim",
        "overlap": {k: dict(v) for k, v in overlap.items()},
        "largest_disagreements": largest,
        "rejected_official_values": dict(rejected),
        "coverage": coverage,
        "v0_to_official_coverage": v0_to_official_coverage,
        "recovery_resolution_counts": dict(resolution_counts),
        "supplemental_changed_fields": supplemental_changed,
        "non_target_canonical_changes": 0,
        "recent_cohort_rows": len(cohort_rows),
        "initial_recent_null_field_rows": len(recovery_rows),
        "recent_remaining_null_rows": len(remaining),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text("# Physical-profile canonical reconciliation v1\n\nPolicy: validated UFC Official NULL-FILL only; populated Greco values are retained.\n\n- Official athlete snapshot: " + SNAPSHOT_ID + "\n- Recent cohort rows: " + str(len(cohort_rows)) + "\n- Remaining recent null field rows: " + str(len(remaining)) + "\n- Official rejections: " + str(sum(rejected.values())) + "\n", encoding="utf-8")
    print(json.dumps(coverage, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
