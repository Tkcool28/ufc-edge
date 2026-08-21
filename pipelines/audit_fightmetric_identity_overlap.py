#!/usr/bin/env python3
"""Audit the direct official UFC fight-node <-> FightMetric identity bridge.

This is data-phase QA only. It proves cardinality/coverage before any canonical
crosswalk is emitted. The direct `fightmetric_id` on UFC fight nodes is compared with
the IDs present in the official UFC FightMetric `fight_stat` archive.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UFC_FIGHTS_ROOT = Path("data/raw/ufc_com_resources/fights")
FM_ROOT = Path("data/raw/ufc_fightmetric_official")
OUT_JSON = Path("provenance/audits/fightmetric_identity_overlap_latest.json")
OUT_MD = Path("provenance/audits/fightmetric_identity_overlap_latest.md")
OUT_CSV = Path("data/derived/identity/ufc_fightmetric_fight_crosswalk_candidate.csv")


def latest_complete_fights() -> Path:
    candidates = sorted(p for p in UFC_FIGHTS_ROOT.iterdir() if p.is_dir() and (p / "manifest.json").exists())
    if not candidates:
        raise RuntimeError("No complete UFC fight resource snapshot")
    return candidates[-1]


def latest_fightmetric_manifest() -> Path:
    candidates = sorted(FM_ROOT.glob("*/manifest.json"))
    if not candidates:
        raise RuntimeError("No official UFC FightMetric manifest")
    return candidates[-1]


def fight_pages(snapshot: Path) -> list[Path]:
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("complete_collection_snapshot") is not True:
        raise RuntimeError("UFC fight snapshot is not complete")
    pages: list[Path] = []
    for chunk_manifest_raw in manifest.get("chunk_manifests") or []:
        chunk_manifest = Path(str(chunk_manifest_raw))
        chunk = json.loads(chunk_manifest.read_text(encoding="utf-8"))
        for info in chunk.get("files") or []:
            page = Path(str(info["path"]))
            if not page.exists():
                raise RuntimeError(f"Missing declared UFC fight page: {page}")
            pages.append(page)
    if len(pages) != int(manifest.get("pages") or 0):
        raise RuntimeError(f"UFC fight page-count mismatch: {len(pages)} vs {manifest.get('pages')}")
    return pages


def fm_pages(manifest_path: Path, collection: str) -> list[Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages: list[Path] = []
    for info in manifest.get("files") or []:
        if not isinstance(info, dict) or info.get("collection") != collection:
            continue
        raw = info.get("path") or info.get("destination")
        if not raw:
            raise RuntimeError(f"FightMetric file entry missing path for {collection}")
        page = Path(str(raw))
        if not page.exists():
            raise RuntimeError(f"Missing declared FightMetric page: {page}")
        pages.append(page)
    if not pages:
        # Older manifest variants may store files inside collection blocks.
        for block in manifest.get("collections") or []:
            if not isinstance(block, dict) or block.get("collection") != collection:
                continue
            for info in block.get("files") or []:
                raw = info.get("path") or info.get("destination")
                if raw:
                    pages.append(Path(str(raw)))
    if not pages:
        raise RuntimeError(f"No raw pages resolved for FightMetric collection {collection}")
    return pages


def relationship_id(item: dict[str, Any], name: str) -> str | None:
    rel = (item.get("relationships") or {}).get(name)
    data = rel.get("data") if isinstance(rel, dict) else None
    return str(data.get("id")) if isinstance(data, dict) and data.get("id") is not None else None


def as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    fight_snapshot = latest_complete_fights()
    fm_manifest = latest_fightmetric_manifest()

    ufc_by_fmid: dict[int, list[dict[str, Any]]] = defaultdict(list)
    ufc_rows = 0
    both_corners = 0
    red_only = blue_only = neither_corner = 0
    for page in fight_pages(fight_snapshot):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            ufc_rows += 1
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            fmid = as_int(attrs.get("fightmetric_id"))
            red = relationship_id(item, "red_corner")
            blue = relationship_id(item, "blue_corner")
            if red and blue:
                both_corners += 1
            elif red:
                red_only += 1
            elif blue:
                blue_only += 1
            else:
                neither_corner += 1
            if fmid is not None:
                ufc_by_fmid[fmid].append({
                    "ufc_fight_uuid": str(item.get("id")),
                    "drupal_internal_nid": as_int(attrs.get("drupal_internal__nid")),
                    "fightmetric_id": fmid,
                    "red_athlete_uuid": red,
                    "blue_athlete_uuid": blue,
                    "winner_athlete_uuid": relationship_id(item, "fight_final_winner"),
                    "title": attrs.get("title"),
                    "final_method": attrs.get("fight_final_method"),
                    "final_round": attrs.get("fight_final_round"),
                    "final_time": attrs.get("fight_final_time"),
                })

    fm_ids: set[int] = set()
    fm_rows = 0
    fm_rows_with_id = 0
    fm_round_counts: Counter[int] = Counter()
    for page in fm_pages(fm_manifest, "fight_stat"):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            fm_rows += 1
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            fmid = as_int(attrs.get("fightmetric_id"))
            rnd = as_int(attrs.get("round"))
            if rnd is not None:
                fm_round_counts[rnd] += 1
            if fmid is not None:
                fm_rows_with_id += 1
                fm_ids.add(fmid)

    ufc_ids = set(ufc_by_fmid)
    overlap = ufc_ids & fm_ids
    duplicate_ufc = {k: v for k, v in ufc_by_fmid.items() if len(v) != 1}
    unique_bridge_ids = sorted(fmid for fmid in overlap if len(ufc_by_fmid[fmid]) == 1)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "fightmetric_id", "ufc_fight_uuid", "drupal_internal_nid", "red_athlete_uuid",
            "blue_athlete_uuid", "winner_athlete_uuid", "title", "final_method", "final_round", "final_time",
        ])
        writer.writeheader()
        for fmid in unique_bridge_ids:
            row = dict(ufc_by_fmid[fmid][0])
            writer.writerow(row)

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "ufc_fight_snapshot": fight_snapshot.as_posix(),
        "fightmetric_manifest": fm_manifest.as_posix(),
        "ufc_fight_rows": ufc_rows,
        "ufc_fightmetric_nonnull_rows": sum(len(v) for v in ufc_by_fmid.values()),
        "ufc_distinct_fightmetric_ids": len(ufc_ids),
        "ufc_duplicate_fightmetric_id_count": len(duplicate_ufc),
        "ufc_duplicate_fightmetric_ids_sample": sorted(duplicate_ufc)[:50],
        "fightmetric_stat_rows": fm_rows,
        "fightmetric_stat_rows_with_id": fm_rows_with_id,
        "fightmetric_distinct_ids": len(fm_ids),
        "fightmetric_round_counts": dict(sorted(fm_round_counts.items())),
        "overlap_distinct_ids": len(overlap),
        "official_ufc_ids_without_stat_rows": len(ufc_ids - fm_ids),
        "stat_ids_without_official_ufc_fight": len(fm_ids - ufc_ids),
        "unique_one_to_one_overlap_ids": len(unique_bridge_ids),
        "corner_linkage": {
            "both": both_corners,
            "red_only": red_only,
            "blue_only": blue_only,
            "neither": neither_corner,
        },
        "candidate_crosswalk_csv": OUT_CSV.as_posix(),
        "decision": {
            "canonical_crosswalk_promoted": False,
            "direct_bridge_safe_for_next_audit": len(duplicate_ufc) == 0 and len(unique_bridge_ids) > 0,
            "rule": "Candidate CSV contains only direct unique UFC fightmetric_id joins present in the official FightMetric archive. It remains derived QA evidence until event/date and source reconciliation gates pass.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# Official UFC ↔ FightMetric identity overlap\n\n"
        f"- UFC fight rows: **{ufc_rows}**\n"
        f"- UFC fights with FightMetric ID: **{report['ufc_fightmetric_nonnull_rows']}**\n"
        f"- Distinct UFC FightMetric IDs: **{len(ufc_ids)}**\n"
        f"- Distinct IDs in official fight_stat: **{len(fm_ids)}**\n"
        f"- Direct overlap: **{len(overlap)}**\n"
        f"- One-to-one overlap candidates: **{len(unique_bridge_ids)}**\n"
        f"- Duplicate FightMetric IDs on UFC fight nodes: **{len(duplicate_ufc)}**\n"
        f"- UFC IDs without stat rows: **{len(ufc_ids - fm_ids)}**\n"
        f"- Stat IDs without UFC fight node: **{len(fm_ids - ufc_ids)}**\n\n"
        "The candidate CSV is derived identity evidence only. It is not a canonical crosswalk until event/date and cross-source validation pass.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "ufc_rows": ufc_rows,
        "ufc_ids": len(ufc_ids),
        "fm_ids": len(fm_ids),
        "overlap": len(overlap),
        "one_to_one": len(unique_bridge_ids),
        "ufc_duplicate_ids": len(duplicate_ufc),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
