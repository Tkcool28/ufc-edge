#!/usr/bin/env python3
"""Inventory the official UFC fight-node identity surface after a complete raw snapshot.

The output is an evidence artifact, not a crosswalk. It searches the full collection
for stable identifiers/relationships that can bridge official FightMetric records to
UFC fight/athlete/event identities without relying on display-name-only matching.

The complete snapshot manifest is authoritative. Raw pages may be stored flat or in
immutable acquisition chunks; this audit follows the manifest's declared file list
instead of assuming a directory layout.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path("data/raw/ufc_com_resources/fights")
OUT_JSON = Path("provenance/audits/ufc_fight_identity_surface_latest.json")
OUT_MD = Path("provenance/audits/ufc_fight_identity_surface_latest.md")
TOKENS = ("fightmetric", "fight_metric", "event", "date", "time", "corner", "winner", "athlete", "bout", "weight", "id")


def latest_complete() -> Path:
    candidates = sorted(p for p in ROOT.iterdir() if p.is_dir() and (p / "manifest.json").exists())
    if not candidates:
        raise RuntimeError("No complete official UFC fight resource snapshot")
    return candidates[-1]


def manifest_pages(snapshot: Path) -> list[Path]:
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("complete_collection_snapshot") is not True:
        raise RuntimeError(f"Snapshot is not marked complete: {manifest_path}")

    pages: list[Path] = []
    chunk_manifests = manifest.get("chunk_manifests") or []
    if chunk_manifests:
        for chunk_manifest_raw in chunk_manifests:
            chunk_manifest_path = Path(str(chunk_manifest_raw))
            if not chunk_manifest_path.exists():
                raise RuntimeError(f"Missing declared chunk manifest: {chunk_manifest_path}")
            chunk = json.loads(chunk_manifest_path.read_text(encoding="utf-8"))
            for file_info in chunk.get("files") or []:
                raw_path = file_info.get("path") if isinstance(file_info, dict) else None
                if not raw_path:
                    raise RuntimeError(f"Chunk manifest has file without path: {chunk_manifest_path}")
                page = Path(str(raw_path))
                if not page.exists():
                    raise RuntimeError(f"Missing declared raw page: {page}")
                pages.append(page)
    else:
        # Compatibility with older flat snapshots, if retained.
        pages = sorted(snapshot.glob("page_*.json"))

    if not pages:
        raise RuntimeError(f"Complete snapshot declares no readable raw pages: {manifest_path}")
    if len(pages) != int(manifest.get("pages") or 0):
        raise RuntimeError(
            f"Manifest page-count mismatch: declared={manifest.get('pages')} resolved={len(pages)}"
        )
    return pages


def nonempty(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def main() -> int:
    snapshot = latest_complete()
    pages = manifest_pages(snapshot)
    primary_rows = 0
    attr_seen = Counter()
    attr_nonnull = Counter()
    rel_seen = Counter()
    rel_nonnull = Counter()
    primary_types = Counter()
    included_types = Counter()
    included_attr_keys: dict[str, Counter[str]] = defaultdict(Counter)
    included_rel_keys: dict[str, Counter[str]] = defaultdict(Counter)
    samples: list[dict[str, Any]] = []
    candidate_attr_examples: dict[str, list[Any]] = defaultdict(list)

    for page in pages:
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data", []):
            if not isinstance(item, dict):
                continue
            primary_rows += 1
            primary_types[str(item.get("type"))] += 1
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            rels = item.get("relationships") if isinstance(item.get("relationships"), dict) else {}
            for key, value in attrs.items():
                attr_seen[str(key)] += 1
                if nonempty(value):
                    attr_nonnull[str(key)] += 1
                if any(token in str(key).lower() for token in TOKENS) and nonempty(value) and len(candidate_attr_examples[str(key)]) < 8:
                    candidate_attr_examples[str(key)].append(value)
            for key, rel in rels.items():
                rel_seen[str(key)] += 1
                data = rel.get("data") if isinstance(rel, dict) else None
                if nonempty(data):
                    rel_nonnull[str(key)] += 1
            if len(samples) < 8:
                samples.append({
                    "type": item.get("type"),
                    "id": item.get("id"),
                    "candidate_attributes": {k: v for k, v in attrs.items() if any(t in k.lower() for t in TOKENS)},
                    "relationships": {
                        k: (v.get("data") if isinstance(v, dict) else None)
                        for k, v in rels.items()
                        if any(t in k.lower() for t in TOKENS)
                    },
                })
        for item in payload.get("included", []):
            if not isinstance(item, dict):
                continue
            typ = str(item.get("type"))
            included_types[typ] += 1
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            rels = item.get("relationships") if isinstance(item.get("relationships"), dict) else {}
            included_attr_keys[typ].update(str(k) for k in attrs)
            included_rel_keys[typ].update(str(k) for k in rels)

    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    declared_rows = int(manifest.get("rows") or 0)
    if primary_rows != declared_rows:
        raise RuntimeError(f"Fight row-count mismatch: manifest={declared_rows} audited={primary_rows}")

    candidate_keys = sorted(k for k in attr_seen if any(token in k.lower() for token in TOKENS))
    fightmetric_keys = sorted(k for k in attr_seen if "fightmetric" in k.lower() or "fight_metric" in k.lower())
    report = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "snapshot": snapshot.as_posix(),
        "manifest": (snapshot / "manifest.json").as_posix(),
        "raw_pages_read": len(pages),
        "primary_rows": primary_rows,
        "primary_types": dict(primary_types),
        "attribute_coverage": {
            k: {
                "seen": int(attr_seen[k]),
                "nonnull": int(attr_nonnull[k]),
                "nonnull_fraction": attr_nonnull[k] / primary_rows if primary_rows else None,
            }
            for k in sorted(attr_seen)
        },
        "relationship_coverage": {
            k: {
                "seen": int(rel_seen[k]),
                "nonnull": int(rel_nonnull[k]),
                "nonnull_fraction": rel_nonnull[k] / primary_rows if primary_rows else None,
            }
            for k in sorted(rel_seen)
        },
        "candidate_identity_attribute_keys": candidate_keys,
        "direct_fightmetric_attribute_keys": fightmetric_keys,
        "candidate_attribute_examples": dict(candidate_attr_examples),
        "included_type_counts": dict(included_types),
        "included_attribute_keys": {k: sorted(v) for k, v in included_attr_keys.items()},
        "included_relationship_keys": {k: sorted(v) for k, v in included_rel_keys.items()},
        "primary_samples": samples,
        "decision": {
            "stable_bridge_proven": bool(fightmetric_keys),
            "note": "A direct FightMetric-named field is strong bridge evidence but still requires uniqueness/cardinality/overlap validation before a canonical crosswalk is created.",
            "name_only_matching_allowed": False,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    lines = [
        "# Official UFC fight identity surface audit",
        "",
        f"Snapshot: `{snapshot}`",
        f"Raw pages read: **{len(pages)}**",
        f"Fight rows: **{primary_rows}**",
        "",
        f"Direct FightMetric-named fields: **{', '.join(fightmetric_keys) if fightmetric_keys else 'none'}**",
        "",
        "## Candidate identity attributes",
        "",
    ]
    for key in candidate_keys:
        coverage = report["attribute_coverage"][key]
        lines.append(f"- `{key}`: {coverage['nonnull']}/{primary_rows} non-null")
    lines += ["", "## Relationships", ""]
    for key, coverage in report["relationship_coverage"].items():
        lines.append(f"- `{key}`: {coverage['nonnull']}/{primary_rows} non-null")
    lines += [
        "",
        "## Crosswalk gate",
        "",
        "No canonical crosswalk is created by this inventory. Uniqueness, cardinality, and overlap with the FightMetric raw IDs must be measured next. Display-name-only matching remains prohibited.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote identity surface audit; rows={primary_rows}; pages={len(pages)}; direct_fightmetric_keys={fightmetric_keys}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
