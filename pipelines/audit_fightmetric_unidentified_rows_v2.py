#!/usr/bin/env python3
"""Characterize official FightMetric rows that lack a stable fightmetric_id.

This version uses the shared raw-manifest reader so it works with the actual official
FightMetric manifest layout. Rows without stable fight identity remain raw/QA-only.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.data.manifest_readers import latest_manifest, manifest_page_paths  # noqa: E402

FM_ROOT = ROOT / "data/raw/ufc_fightmetric_official"
OUT = ROOT / "provenance/audits/fightmetric_unidentified_rows_latest.json"


def main() -> int:
    manifest_path = latest_manifest(FM_ROOT)
    pages = manifest_page_paths(manifest_path, collection="fight_stat")

    total = identified = unidentified = 0
    rounds: Counter[str] = Counter()
    colors: Counter[str] = Counter()
    populated_counts: Counter[int] = Counter()
    internal_ids: list[int] = []
    examples: list[dict[str, object]] = []
    nonnull_field_counts: Counter[str] = Counter()

    for page in pages:
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
            populated = 0
            for key, value in attrs.items():
                if key == "metatag" or value in (None, "", [], {}):
                    continue
                populated += 1
                nonnull_field_counts[str(key)] += 1
            populated_counts[populated] += 1

            try:
                internal_ids.append(int(attrs.get("drupal_internal__id")))
            except (TypeError, ValueError):
                pass

            if len(examples) < 20:
                examples.append(
                    {
                        "resource_id": item.get("id"),
                        "drupal_internal__id": attrs.get("drupal_internal__id"),
                        "round": attrs.get("round"),
                        "color": attrs.get("color"),
                        "populated_attribute_count": populated,
                        "non_null_sample": {
                            k: v
                            for k, v in attrs.items()
                            if k != "metatag" and v not in (None, "", [], {})
                        },
                    }
                )

    report = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest": manifest_path.relative_to(ROOT).as_posix(),
        "page_count": len(pages),
        "total_rows": total,
        "identified_rows": identified,
        "unidentified_rows": unidentified,
        "identified_fraction": identified / total if total else None,
        "unidentified_round_counts": dict(sorted(rounds.items())),
        "unidentified_color_counts": dict(sorted(colors.items())),
        "unidentified_populated_attribute_count_distribution": {
            str(k): v for k, v in sorted(populated_counts.items())
        },
        "unidentified_nonnull_field_counts": dict(nonnull_field_counts.most_common()),
        "unidentified_internal_id_min": min(internal_ids) if internal_ids else None,
        "unidentified_internal_id_max": max(internal_ids) if internal_ids else None,
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
