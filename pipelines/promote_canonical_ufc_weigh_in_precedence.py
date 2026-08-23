#!/usr/bin/env python3
"""Promote fight-specific UFC weigh-ins from acquired QA to active canonical precedence.

Exact/idempotent DATA-PHASE migration. Promotion is permitted only after the accepted
canonical weigh-in audit proves context-clean fight/fighter identity plus official scale
weight, while unresolved annotation/date/attempt semantics remain null.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRECEDENCE = ROOT / "schemas/source_precedence_v0.json"
AUDIT = ROOT / "provenance/audits/canonical_ufc_weigh_ins_v0_latest.json"
OLD_EVIDENCE = "data/raw/ufc_official_articles/20260821T210000Z/weigh_in/manifest.json"
NEW_EVIDENCE = "provenance/audits/canonical_ufc_weigh_ins_v0_latest.json"
NEW_GATE = (
    "Canonical scale_weight_lbs requires an official UFC article observation with context-clean exact fight/fighter identity. "
    "Article publication time is not weigh-in date. attempt_number, contract_limit_lbs, missed_weight, pounds_over, "
    "catchweight_bout, purse_penalty_pct and official_status_text remain null unless source-explicit semantics are "
    "independently resolved for that observation; page-local annotation markers are never interpreted globally."
)
NEW_FALLBACK = "No fallback source is canonical-approved; roster/listed weight is never a scale-weight substitute."


def main() -> int:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if audit.get("canonical_contract_version") != "0.4.0-draft":
        raise RuntimeError("canonical weigh-in audit contract drift")
    if audit.get("canonical_weigh_in_rows") != 12890 or audit.get("canonical_fights_covered") != 6445:
        raise RuntimeError("canonical weigh-in audit cardinality drift")
    rules = audit.get("rules") or {}
    required = {
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
    }
    for key, expected in required.items():
        if rules.get(key) is not expected:
            raise RuntimeError(f"canonical weigh-in semantic gate changed: {key}={rules.get(key)!r}")

    payload = json.loads(PRECEDENCE.read_text(encoding="utf-8"))
    version = payload.get("precedence_version")
    if version not in {"0.2.0-draft", "0.3.0-draft"}:
        raise RuntimeError(f"unexpected source precedence version: {version!r}")
    matches = [r for r in payload.get("rules") or [] if r.get("family") == "fight_specific_weigh_ins"]
    if len(matches) != 1:
        raise RuntimeError("fight_specific_weigh_ins precedence family missing/duplicated")
    rule = matches[0]
    if rule.get("priority") != ["ufc_official_content"] or rule.get("canonical_table") != "weigh_ins":
        raise RuntimeError("weigh-in precedence provider/table drift")

    if rule.get("status") == "active":
        if payload.get("precedence_version") != "0.3.0-draft":
            raise RuntimeError("active weigh-in rule exists without expected precedence version")
        if rule.get("evidence") != NEW_EVIDENCE or rule.get("selection_gate") != NEW_GATE or rule.get("fallback_rule") != NEW_FALLBACK:
            raise RuntimeError("active weigh-in rule differs from exact promoted semantics")
    elif rule.get("status") == "acquired_qa_pending":
        if version != "0.2.0-draft" or rule.get("evidence") != OLD_EVIDENCE:
            raise RuntimeError("unexpected pre-promotion weigh-in state")
        rule["status"] = "active"
        rule["selection_gate"] = NEW_GATE
        rule["fallback_rule"] = NEW_FALLBACK
        rule["evidence"] = NEW_EVIDENCE
        rule["notes"] = (
            "Canonical v0 contains 12,890 official UFC scale-weight observations covering 6,445 fights and 2,249 fighters. "
            "Two false Strikeforce-context transports are quarantined; 172 marker-bearing source rows retain raw marker text only."
        )
        payload["precedence_version"] = "0.3.0-draft"
        payload.setdefault("evidence", {})["canonical_ufc_weigh_ins"] = NEW_EVIDENCE
    else:
        raise RuntimeError(f"unexpected weigh-in precedence status: {rule.get('status')!r}")

    if payload.setdefault("evidence", {}).get("canonical_ufc_weigh_ins") != NEW_EVIDENCE:
        payload["evidence"]["canonical_ufc_weigh_ins"] = NEW_EVIDENCE
    PRECEDENCE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("UFC_WEIGH_IN_PRECEDENCE_ACTIVE version=0.3.0-draft rows=12890 fights=6445")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
