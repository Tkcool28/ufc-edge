#!/usr/bin/env python3
"""Audit official UFC athlete point-in-time profile field shapes before canonicalization."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = ROOT / "data/raw/ufc_com_resources/athletes"
OUT = ROOT / "provenance/audits/ufc_athlete_profile_semantics_latest.json"
ATTRS = ["stats_weight", "status", "residence", "origin"]
RELS = ["stats_weight_class", "fighting_style", "gym", "athlete_status"]


def latest() -> Path:
    candidates = sorted(p for p in SNAPSHOT_ROOT.iterdir() if p.is_dir() and (p / "manifest.json").is_file())
    if not candidates:
        raise RuntimeError("No athlete snapshot")
    return candidates[-1]


def typename(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, (int, float)):
        return "number"
    return "string"


def rel_ids(item: dict[str, Any], name: str) -> list[tuple[str, str]]:
    rel = (item.get("relationships") or {}).get(name)
    data = rel.get("data") if isinstance(rel, dict) else None
    if isinstance(data, dict) and data.get("id"):
        return [(str(data.get("type") or ""), str(data["id"]))]
    if isinstance(data, list):
        return [(str(x.get("type") or ""), str(x["id"])) for x in data if isinstance(x, dict) and x.get("id")]
    return []


def label(item: dict[str, Any]) -> str | None:
    attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
    for key in ("title", "name", "label"):
        value = attrs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def main() -> int:
    snapshot = latest()
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    pages = [Path(x["path"]) for x in manifest.get("files") or []]
    type_counts = {field: Counter() for field in ATTRS}
    samples: dict[str, dict[str, list[Any]]] = {field: defaultdict(list) for field in ATTRS}
    rel_counts = {name: Counter() for name in RELS}
    rel_label_counts = Counter()
    rel_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    athletes = 0

    for page in pages:
        payload = json.loads(page.read_text(encoding="utf-8"))
        included: dict[tuple[str, str], dict[str, Any]] = {}
        for inc in payload.get("included") or []:
            if isinstance(inc, dict) and inc.get("id"):
                included[(str(inc.get("type") or ""), str(inc["id"]))] = inc
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            athletes += 1
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            for field in ATTRS:
                value = attrs.get(field)
                typ = typename(value)
                type_counts[field][typ] += 1
                if value is not None and len(samples[field][typ]) < 20:
                    samples[field][typ].append(value)
            for rel in RELS:
                ids = rel_ids(item, rel)
                rel_counts[rel]["athletes_with_relationship_ids" if ids else "athletes_without_relationship_ids"] += 1
                for typ, rid in ids:
                    inc = included.get((typ, rid))
                    lab = label(inc) if inc else None
                    rel_counts[rel]["relationship_ids"] += 1
                    if inc:
                        rel_counts[rel]["included_objects_found"] += 1
                    if lab:
                        rel_counts[rel]["labels_found"] += 1
                        rel_label_counts[f"{rel}:{lab}"] += 1
                    if len(rel_examples[rel]) < 30:
                        rel_examples[rel].append({"type": typ, "id": rid, "included": bool(inc), "label": lab})

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "snapshot_id": snapshot.name,
        "snapshot_completed_at_utc": manifest.get("completed_at_utc"),
        "athletes": athletes,
        "attribute_type_counts": {k: dict(v) for k, v in type_counts.items()},
        "attribute_samples": {k: dict(v) for k, v in samples.items()},
        "relationship_counts": {k: dict(v) for k, v in rel_counts.items()},
        "relationship_examples": dict(rel_examples),
        "top_relationship_labels": rel_label_counts.most_common(100),
        "decision": {"canonicalization_promoted": False, "point_in_time_only": True},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "athletes": athletes,
        "attribute_types": {k: dict(v) for k, v in type_counts.items()},
        "relationship_counts": {k: dict(v) for k, v in rel_counts.items()},
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
