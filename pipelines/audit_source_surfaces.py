#!/usr/bin/env python3
"""Generate one compact schema/coverage inventory across acquired UFC Edge raw sources.

This is intentionally source-facing. It does not decide canonical mappings; it gives
adapter work one durable place to see what each acquired source actually exposes.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path("data/raw")
OUT_JSON = Path("provenance/audits/source_surface_inventory.json")
OUT_MD = Path("provenance/audits/source_surface_inventory.md")


def latest(paths: list[Path]) -> Path | None:
    return sorted(paths, key=lambda p: p.as_posix())[-1] if paths else None


def csv_surface(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return {"path": path.as_posix(), "rows": 0, "columns": []}
        rows = sum(1 for _ in reader)
    return {"path": path.as_posix(), "rows": rows, "columns": header}


def load_json(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise RuntimeError(f"Expected object: {path}")
    return obj


def add_greco(out: list[dict[str, Any]]) -> None:
    dirs = sorted([p for p in (ROOT / "greco1899").glob("*") if p.is_dir()])
    if not dirs:
        return
    d = dirs[-1]
    for path in sorted(d.glob("*.csv")):
        item = csv_surface(path)
        item.update({"source": "greco1899_ufcstats", "collection": path.stem, "snapshot": d.name})
        out.append(item)


def add_csv_single(out: list[dict[str, Any]], source: str, pattern: str) -> None:
    paths = sorted(ROOT.glob(pattern))
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".csv":
            item = csv_surface(path)
            item.update({"source": source, "collection": path.stem, "snapshot": path.parent.name})
            out.append(item)


def add_fightmetric(out: list[dict[str, Any]]) -> None:
    manifest_path = latest(list((ROOT / "ufc_fightmetric_official").glob("*/manifest.json")))
    if not manifest_path:
        return
    m = load_json(manifest_path)
    for c in m.get("collections", []):
        if not isinstance(c, dict):
            continue
        coverage = c.get("attribute_coverage") or {}
        attrs = sorted(coverage) if isinstance(coverage, dict) else []
        out.append({
            "source": "ufc_fightmetric_official",
            "collection": c.get("collection"),
            "snapshot": manifest_path.parent.name,
            "manifest": manifest_path.as_posix(),
            "rows": c.get("rows"),
            "pages": c.get("pages"),
            "attributes": attrs,
            "relationship_names": [],
            "distinct_nonnull_fightmetric_ids": c.get("distinct_nonnull_fightmetric_ids"),
            "round_value_counts": c.get("round_value_counts"),
            "selected_coverage": {
                k: coverage[k]
                for k in (
                    "fightmetric_id", "round", "color", "knock_down", "sig_str_att", "sig_str_land",
                    "tot_str_att", "tot_str_land", "grap_take_att", "grap_take_land", "grap_sub_att",
                    "grap_rev_land", "grap_stand_land", "standing_time", "distance_time", "clinch_time",
                    "ground_time", "control_time", "ground_ctl_time", "guard_ctl_time", "half_guard_ctl_time",
                    "side_ctl_time", "mount_ctl_time", "back_ctl_time"
                ) if k in coverage
            },
        })


def add_ufc_resources(out: list[dict[str, Any]]) -> None:
    base = ROOT / "ufc_com_resources"
    if not base.exists():
        return
    for collection_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        manifests = [p for p in collection_dir.glob("*/manifest.json") if p.is_file()]
        manifest_path = latest(manifests)
        if not manifest_path:
            continue
        m = load_json(manifest_path)
        out.append({
            "source": "ufc_com_official",
            "collection": collection_dir.name,
            "snapshot": manifest_path.parent.name,
            "manifest": manifest_path.as_posix(),
            "rows": m.get("rows"),
            "pages": m.get("pages"),
            "attributes": m.get("attribute_names") or [],
            "relationship_names": m.get("relationship_names") or [],
            "relationship_linkage_counts": m.get("relationship_linkage_counts"),
            "complete_collection_snapshot": m.get("complete_collection_snapshot", m.get("semantics", {}).get("complete_collection_snapshot")),
        })


def add_manifest_source(out: list[dict[str, Any]], source: str, glob_pattern: str) -> None:
    manifest_path = latest([p for p in ROOT.glob(glob_pattern) if p.is_file()])
    if not manifest_path:
        return
    m = load_json(manifest_path)
    item: dict[str, Any] = {
        "source": source,
        "collection": m.get("collection") or m.get("dataset_handle") or manifest_path.parent.name,
        "snapshot": m.get("snapshot_id") or manifest_path.parent.name,
        "manifest": manifest_path.as_posix(),
    }
    for key in (
        "rows", "pages", "event_count", "competition_count", "events", "competitions",
        "observed_competitor_stat_names", "observed_play_types", "observed_official_positions", "http_status_counts"
    ):
        if key in m:
            item[key] = m[key]
    file_info = m.get("file")
    if isinstance(file_info, dict):
        item["rows"] = item.get("rows", file_info.get("data_rows"))
        item["columns"] = file_info.get("columns") or []
    out.append(item)


def markdown(items: list[dict[str, Any]]) -> str:
    lines = [
        "# Raw Source Surface Inventory",
        "",
        "Generated from files already committed under `data/raw/`. This is an acquisition/schema inventory, **not** a canonical field-selection decision.",
        "",
        "| Source | Collection | Rows | Snapshot | Surface |",
        "|---|---|---:|---|---|",
    ]
    for item in items:
        attrs = item.get("columns") or item.get("attributes") or []
        rels = item.get("relationship_names") or []
        surface_parts = []
        if attrs:
            preview = ", ".join(str(x) for x in attrs[:12])
            if len(attrs) > 12:
                preview += f", … (+{len(attrs)-12})"
            surface_parts.append(preview)
        if rels:
            surface_parts.append(f"rels: {', '.join(str(x) for x in rels[:8])}")
        surface = "<br>".join(surface_parts).replace("|", "\\|")
        lines.append(
            f"| {item.get('source','')} | {item.get('collection','')} | {item.get('rows','')} | "
            f"{item.get('snapshot','')} | {surface} |"
        )
    lines.extend([
        "",
        "## Rules",
        "",
        "- This file reports what sources expose; it does not authorize mappings by name similarity.",
        "- Canonical mappings belong in `schemas/source_field_map_v0.json` and require semantic verification.",
        "- Missing fields remain missing; a provider without a field does not imply zero.",
        "- Raw provider vocabulary never becomes a downstream feature definition directly.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    items: list[dict[str, Any]] = []
    add_greco(items)
    add_fightmetric(items)
    add_ufc_resources(items)
    add_manifest_source(items, "espn_mma", "espn_mma/*/manifest.json")
    add_manifest_source(items, "tidytuesday_ufc_rankings", "tidytuesday_ufc_rankings/*/manifest.json")
    add_manifest_source(items, "kaggle_pro_mma_fights", "kaggle_pro_mma_fights/*/manifest.json")
    add_manifest_source(items, "kaggle_pro_mma_fighters", "kaggle_pro_mma_fighters/*/manifest.json")
    add_manifest_source(items, "ufc_datalab_scorecards", "ufc_datalab_scorecards/*/manifest.json")

    if not items:
        raise RuntimeError("No acquired raw source surfaces found")
    items.sort(key=lambda x: (str(x.get("source")), str(x.get("collection"))))
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({"schema_version": 1, "sources": items}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(markdown(items), encoding="utf-8")
    print(f"SOURCE_SURFACE_INVENTORY_OK sources={len(items)} json={OUT_JSON} md={OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
