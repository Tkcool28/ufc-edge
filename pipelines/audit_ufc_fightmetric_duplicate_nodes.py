#!/usr/bin/env python3
"""Characterize official UFC fight nodes that share the same FightMetric ID.

No dedupe is performed. The goal is to determine whether repeated FightMetric IDs are
identical/revised Drupal content nodes or genuinely conflicting fight identities.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("data/raw/ufc_com_resources/fights")
OUT_JSON = Path("provenance/audits/ufc_fightmetric_duplicate_nodes_latest.json")
OUT_MD = Path("provenance/audits/ufc_fightmetric_duplicate_nodes_latest.md")

COMPARE_ATTRS = [
    "title", "fight_final_method", "fight_final_round", "fight_final_time",
    "fight_final_time_format", "red_corner_fight_weight", "blue_corner_fight_weight",
    "created", "changed", "drupal_internal__nid", "drupal_internal__vid",
]
COMPARE_RELS = ["red_corner", "blue_corner", "fight_final_winner", "red_corner_weightclass", "blue_corner_weightclass"]


def latest_complete() -> Path:
    for p in reversed(sorted(x for x in ROOT.iterdir() if x.is_dir() and (x / "manifest.json").exists())):
        m = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
        if m.get("complete_collection_snapshot") is True:
            return p
    raise RuntimeError("No complete UFC fight snapshot")


def pages(snapshot: Path) -> list[Path]:
    m = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    out: list[Path] = []
    for cm_raw in m.get("chunk_manifests") or []:
        cm = json.loads(Path(str(cm_raw)).read_text(encoding="utf-8"))
        out.extend(Path(str(f["path"])) for f in cm.get("files") or [])
    return out


def rel_id(item: dict[str, Any], name: str) -> str | None:
    rel = (item.get("relationships") or {}).get(name)
    data = rel.get("data") if isinstance(rel, dict) else None
    return str(data.get("id")) if isinstance(data, dict) and data.get("id") is not None else None


def norm_record(item: dict[str, Any]) -> dict[str, Any]:
    attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
    return {
        "ufc_fight_uuid": str(item.get("id")),
        "attributes": {k: attrs.get(k) for k in COMPARE_ATTRS},
        "relationships": {k: rel_id(item, k) for k in COMPARE_RELS},
    }


def meaningful_signature(r: dict[str, Any]) -> tuple[Any, ...]:
    a = r["attributes"]
    rel = r["relationships"]
    # Exclude Drupal revision/timestamp/node IDs from semantic equivalence.
    return (
        a.get("title"), a.get("fight_final_method"), a.get("fight_final_round"), a.get("fight_final_time"),
        a.get("fight_final_time_format"), a.get("red_corner_fight_weight"), a.get("blue_corner_fight_weight"),
        rel.get("red_corner"), rel.get("blue_corner"), rel.get("fight_final_winner"),
        rel.get("red_corner_weightclass"), rel.get("blue_corner_weightclass"),
    )


def main() -> int:
    snapshot = latest_complete()
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for page in pages(snapshot):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            raw = attrs.get("fightmetric_id")
            try:
                fmid = int(raw)
            except (TypeError, ValueError):
                continue
            groups[fmid].append(norm_record(item))

    dup = {k: v for k, v in groups.items() if len(v) > 1}
    identical_semantics = 0
    conflicting_semantics = 0
    cardinalities = Counter()
    conflicts_by_component = Counter()
    details = []

    for fmid, records in sorted(dup.items()):
        cardinalities[len(records)] += 1
        sigs = {meaningful_signature(r) for r in records}
        semantic_equal = len(sigs) == 1
        if semantic_equal:
            identical_semantics += 1
        else:
            conflicting_semantics += 1
            for attr in ["title", "fight_final_method", "fight_final_round", "fight_final_time", "fight_final_time_format", "red_corner_fight_weight", "blue_corner_fight_weight"]:
                if len({r["attributes"].get(attr) for r in records}) > 1:
                    conflicts_by_component[f"attr:{attr}"] += 1
            for rel in COMPARE_RELS:
                if len({r["relationships"].get(rel) for r in records}) > 1:
                    conflicts_by_component[f"rel:{rel}"] += 1
        details.append({
            "fightmetric_id": fmid,
            "node_count": len(records),
            "semantically_identical_on_compared_fields": semantic_equal,
            "records": records,
        })

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "snapshot": snapshot.as_posix(),
        "distinct_fightmetric_ids": len(groups),
        "duplicate_fightmetric_id_groups": len(dup),
        "duplicate_group_cardinalities": dict(sorted(cardinalities.items())),
        "semantically_identical_groups": identical_semantics,
        "semantically_conflicting_groups": conflicting_semantics,
        "conflicts_by_component": dict(conflicts_by_component.most_common()),
        "groups": details,
        "decision": {
            "automatic_dedupe_rule_created": False,
            "rule": "Do not choose a UFC node solely by newer nid/vid/timestamp. Semantic conflicts and event membership must be reconciled first.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# Duplicate official UFC fight nodes by FightMetric ID\n\n"
        f"- Duplicate FightMetric-ID groups: **{len(dup)}**\n"
        f"- Semantically identical on compared fight fields: **{identical_semantics}**\n"
        f"- Semantically conflicting: **{conflicting_semantics}**\n\n"
        "No automatic dedupe rule is created by this audit.\n",
        encoding="utf-8",
    )
    print(json.dumps({"duplicate_groups": len(dup), "identical": identical_semantics, "conflicting": conflicting_semantics}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
