#!/usr/bin/env python3
"""Determine official FightMetric numeric ``color`` semantics from aligned fight evidence.

The raw Drupal fight_stat surface stores corner as numeric 0/1, not canonical red/blue.
We do not guess the mapping.  This audit scores both possible global orientations against
exactly aligned Greco/UFCStats fighter-round observations and promotes a mapping only if
one orientation dominates by a strict evidence gate.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.data.manifest_readers import latest_manifest, manifest_page_paths  # noqa: E402
from ufc_edge.data.parsing import landed_attempted, nonnegative_int, round_number  # noqa: E402

ALIGN = ROOT / "data/derived/identity/ufc_greco_fight_alignment_candidate.csv"
GRECO_ROOT = ROOT / "data/raw/greco1899"
FM_ROOT = ROOT / "data/raw/ufc_fightmetric_official"
OUT = ROOT / "provenance/audits/fightmetric_color_semantics_latest.json"

FIELDS = {
    "sig_str_land": "SIG.STR.",
    "sig_str_att": "SIG.STR.",
    "tot_str_land": "TOTAL STR.",
    "tot_str_att": "TOTAL STR.",
    "grap_take_land": "TD",
    "grap_take_att": "TD",
    "head_sig_str_land": "HEAD",
    "head_sig_str_att": "HEAD",
}


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def greco_component(field: str, raw: str | None) -> int | None:
    pair = landed_attempted(raw)
    if pair is None:
        return None
    landed, attempted = pair
    return landed if field.endswith("_land") else attempted


def main() -> int:
    if not ALIGN.is_file():
        raise RuntimeError(f"Missing aligned-fight evidence: {ALIGN}")

    alignments = read_csv(ALIGN)
    if not alignments:
        raise RuntimeError("Empty aligned-fight evidence")

    greco_dir = sorted(p for p in GRECO_ROOT.iterdir() if p.is_dir())[-1]
    bout_rows: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(greco_dir / "ufc_fight_stats.csv"):
        if row.get("EVENT") and row.get("BOUT"):
            bout_rows[(row["EVENT"], row["BOUT"])].append(row)

    # Canonical red/blue Greco lookup derived only from official aligned fighter names.
    greco: dict[tuple[int, str, int], dict[str, str]] = {}
    for a in alignments:
        fmid = int(a["fightmetric_id"])
        key = (a["greco_event"], a["greco_bout"])
        semantic = {
            normalize_name(a["red_name"]): "red",
            normalize_name(a["blue_name"]): "blue",
        }
        for row in bout_rows.get(key, []):
            corner = semantic.get(normalize_name(str(row.get("FIGHTER") or "")))
            if not corner:
                continue
            try:
                rnd = round_number(row.get("ROUND"))
            except ValueError:
                continue
            if rnd is None:
                continue
            greco[(fmid, corner, int(rnd))] = row

    fm: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    color_counts: Counter[int] = Counter()
    manifest = latest_manifest(FM_ROOT)
    for page in manifest_page_paths(manifest, collection="fight_stat"):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            fmid = nonnegative_int(attrs.get("fightmetric_id"))
            try:
                rnd = round_number(attrs.get("round"))
            except ValueError:
                continue
            raw_color = attrs.get("color")
            if isinstance(raw_color, bool):
                continue
            try:
                color = int(raw_color)
            except (TypeError, ValueError):
                continue
            if fmid is None or rnd is None:
                continue
            color_counts[color] += 1
            fm[(int(fmid), color, int(rnd))].append(attrs)

    observed_colors = sorted(color_counts)
    if observed_colors != [0, 1]:
        raise RuntimeError(f"Expected exactly numeric FightMetric colors [0,1], got {observed_colors}")

    orientations = {
        "0_red_1_blue": {0: "red", 1: "blue"},
        "0_blue_1_red": {0: "blue", 1: "red"},
    }
    results: dict[str, dict[str, int | float | None]] = {}

    for name, mapping in orientations.items():
        exact = compared = abs_error = keys = 0
        for (fmid, numeric_color, rnd), versions in fm.items():
            # Duplicate source versions are excluded from this semantic audit.
            if len(versions) != 1:
                continue
            grow = greco.get((fmid, mapping[numeric_color], rnd))
            if grow is None:
                continue
            keys += 1
            attrs = versions[0]
            for field, source in FIELDS.items():
                oval = nonnegative_int(attrs.get(field))
                try:
                    gval = greco_component(field, grow.get(source))
                except ValueError:
                    continue
                if oval is None or gval is None:
                    continue
                compared += 1
                exact += int(int(oval) == gval)
                abs_error += abs(int(oval) - gval)
        results[name] = {
            "fighter_round_keys": keys,
            "field_comparisons": compared,
            "exact": exact,
            "exact_fraction": exact / compared if compared else None,
            "absolute_error_sum": abs_error,
        }

    first, second = results["0_red_1_blue"], results["0_blue_1_red"]
    candidates = sorted(
        results,
        key=lambda name: (
            float(results[name]["exact_fraction"] or -1),
            -int(results[name]["absolute_error_sum"] or 0),
        ),
        reverse=True,
    )
    winner, loser = candidates[0], candidates[1]
    winner_fraction = float(results[winner]["exact_fraction"] or 0.0)
    loser_fraction = float(results[loser]["exact_fraction"] or 0.0)
    comparisons = int(results[winner]["field_comparisons"] or 0)

    # Require a large sample and an unmistakable orientation gap.
    promoted = comparisons >= 10000 and winner_fraction >= 0.95 and (winner_fraction - loser_fraction) >= 0.25
    mapping = orientations[winner] if promoted else None

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "observed_numeric_color_counts": dict(sorted(color_counts.items())),
        "aligned_fights_input": len(alignments),
        "greco_semantic_fighter_round_keys": len(greco),
        "orientations": results,
        "decision": {
            "mapping_promoted": promoted,
            "winner": winner if promoted else None,
            "numeric_to_corner": {str(k): v for k, v in mapping.items()} if mapping else None,
            "gate": "winner comparisons>=10000, exact_fraction>=0.95, and exact_fraction gap>=0.25",
            "note": "Numeric color is transport syntax. Canonical adapters must emit red/blue only after this audit passes.",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], sort_keys=True))
    if not promoted:
        raise RuntimeError("FightMetric numeric color semantics did not pass promotion gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
