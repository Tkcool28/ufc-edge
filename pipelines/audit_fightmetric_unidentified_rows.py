#!/usr/bin/env python3
"""Characterize official UFC FightMetric fight_stat rows without fightmetric_id.

Rows lacking a stable fight ID are not eligible for canonical fight/round tables. This
audit records whether they are legacy placeholders, summary/round records, and how much
stat content they contain so missing identity is not mistaken for missing statistics.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("data/raw/ufc_fightmetric_official")
OUT = Path("provenance/audits/fightmetric_unidentified_rows_latest.json")


def latest_manifest() -> Path:
    xs = sorted(ROOT.glob("*/manifest.json"))
    if not xs:
        raise RuntimeError("No FightMetric manifest")
    return xs[-1]


def pages(manifest_path: Path) -> list[Path]:
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    for block in m.get("collections") or []:
        if isinstance(block, dict) and block.get("collection") == "fight_stat":
            out = [Path(str(x.get("path") or x.get("destination"))) for x in block.get("files") or []]
            if out:
                return out
    raise RuntimeError("No fight_stat pages")


def main() -> int:
    total = identified = unidentified = 0
    rounds = Counter(); colors = Counter(); populated_counts = Counter(); ids = []
    examples = []
    for page in pages(latest_manifest()):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            total += 1
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            if attrs.get("fightmetric_id") not in (None, ""):
                identified += 1
                continue
            unidentified += 1
            rounds[str(attrs.get("round"))] += 1
            colors[str(attrs.get("color"))] += 1
            populated = sum(1 for k, v in attrs.items() if k not in {"metatag"} and v not in (None, "", [], {}))
            populated_counts[populated] += 1
            nid = attrs.get("drupal_internal__id")
            try:
                ids.append(int(nid))
            except (TypeError, ValueError):
                pass
            if len(examples) < 20:
                examples.append({
                    "resource_id": item.get("id"),
                    "drupal_internal__id": nid,
                    "round": attrs.get("round"),
                    "color": attrs.get("color"),
                    "populated_attribute_count": populated,
                    "non_null_sample": {k: v for k, v in attrs.items() if v not in (None, "", [], {}) and k != "metatag"},
                })

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_rows": total,
        "identified_rows": identified,
        "unidentified_rows": unidentified,
        "identified_fraction": identified / total if total else None,
        "unidentified_round_counts": dict(rounds),
        "unidentified_color_counts": dict(colors),
        "unidentified_populated_attribute_count_distribution": dict(sorted(populated_counts.items())),
        "unidentified_internal_id_min": min(ids) if ids else None,
        "unidentified_internal_id_max": max(ids) if ids else None,
        "examples": examples,
        "decision": {
            "canonical_eligible": False,
            "rule": "fight_stat rows without fightmetric_id remain raw/QA-only until an independent stable fight identity is proven.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"total": total, "identified": identified, "unidentified": unidentified}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
