#!/usr/bin/env python3
"""Register verified official UFC weigh-in article -> canonical mappings.

Exact/idempotent DATA-PHASE migration. Only fields already accepted by the canonical
weigh-in audit are mapped; unresolved date/attempt/miss/catchweight/penalty semantics remain absent.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "schemas/source_field_map_v0.json"
AUDIT = ROOT / "provenance/audits/canonical_ufc_weigh_ins_v0_latest.json"
SOURCE = "ufc_official_content"
COLLECTION = "weigh_in_articles"

NEW_ROWS = [
    {
        "collection": COLLECTION,
        "mapping_status": "verified",
        "notes": "Deterministic observation ID is minted only after context-clean official article extraction; raw article identity alone is not a fighter/fight identity.",
        "source": SOURCE,
        "source_field": "raw_html",
        "source_role": "primary_candidate",
        "target_field": "weigh_in_observation_id",
        "target_table": "weigh_ins",
        "temporal_class": "historical_observation",
        "transform": "extract_context_clean_bout_observation_then_uuid5",
    },
    {
        "collection": COLLECTION,
        "mapping_status": "verified",
        "notes": "Fight identity requires singleton article-event intersection plus exact contextual canonical participant pair; display name alone is insufficient.",
        "source": SOURCE,
        "source_field": "raw_html",
        "source_role": "primary_candidate",
        "target_field": "fight_id",
        "target_table": "weigh_ins",
        "temporal_class": "historical_observation",
        "transform": "resolve_singleton_event_and_exact_contextual_participant_pair",
    },
    {
        "collection": COLLECTION,
        "mapping_status": "verified",
        "notes": "Fighter identity is accepted only inside the audited exact fight participant context; raw display name alone is not trusted.",
        "source": SOURCE,
        "source_field": "raw_html",
        "source_role": "primary_candidate",
        "target_field": "fighter_id",
        "target_table": "weigh_ins",
        "temporal_class": "historical_observation",
        "transform": "resolve_fighter_within_context_clean_canonical_fight",
    },
    {
        "collection": COLLECTION,
        "mapping_status": "verified",
        "notes": "Official scale weight is parsed from the audited bout-local weigh-in line. Roster/listed weight is never substituted.",
        "source": SOURCE,
        "source_field": "raw_html",
        "source_role": "primary_candidate",
        "target_field": "scale_weight_lbs",
        "target_table": "weigh_ins",
        "temporal_class": "historical_observation",
        "transform": "parse_official_bout_local_scale_weight_lbs",
    },
]


def key(row: dict) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("source") or ""), str(row.get("collection") or ""),
        str(row.get("source_field") or ""), str(row.get("target_table")), str(row.get("target_field")),
    )


def main() -> int:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if audit.get("canonical_weigh_in_rows") != 12890 or audit.get("canonical_fights_covered") != 6445:
        raise RuntimeError("canonical weigh-in audit cardinality drift")
    rules = audit.get("rules") or {}
    if rules.get("scale_weight_promoted") is not True or rules.get("fight_and_fighter_identity_promoted") is not True:
        raise RuntimeError("accepted weigh-in fields are no longer proven")
    for unresolved in (
        "weigh_in_date_promoted", "attempt_number_promoted", "contract_limit_promoted", "missed_weight_promoted",
        "pounds_over_promoted", "catchweight_promoted", "purse_penalty_promoted", "official_status_text_promoted",
    ):
        if rules.get(unresolved) is not False:
            raise RuntimeError(f"unresolved weigh-in semantic unexpectedly promoted: {unresolved}")

    payload = json.loads(MAP.read_text(encoding="utf-8"))
    version = payload.get("map_version")
    if version not in {"0.4.0-draft", "0.5.0-draft"}:
        raise RuntimeError(f"unexpected source map version: {version!r}")
    rows = payload.get("mappings") or []
    by_key = {key(row): row for row in rows}
    for new in NEW_ROWS:
        k = key(new)
        old = by_key.get(k)
        if old is not None:
            if old != new:
                raise RuntimeError(f"existing official weigh-in mapping differs from promoted definition: {k}")
        else:
            rows.append(new)
            by_key[k] = new
    payload["map_version"] = "0.5.0-draft"
    payload.setdefault("rules", {})["official_weigh_in_annotation_semantics_require_observation_level_proof"] = True
    payload["mappings"] = rows
    MAP.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"UFC_OFFICIAL_WEIGH_IN_FIELD_MAP_OK version=0.5.0-draft mappings={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
