"""Fail-closed helpers for locating immutable raw pages from UFC Edge manifests.

Raw providers currently use two physical layouts:
- flat snapshots with a top-level ``files`` list;
- chunked snapshots whose final manifest points to immutable chunk manifests.

Some provider manifests also keep collection summaries under ``collections`` while the
actual page list remains top-level.  Consumers must not assume one layout from another.
These helpers centralize that distinction so every audit/adapter reads the same evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return payload


def _entry_path(entry: Any) -> Path | None:
    if not isinstance(entry, dict):
        return None
    value = entry.get("path") or entry.get("destination")
    if not value:
        return None
    return Path(str(value))


def manifest_page_paths(manifest_path: Path, *, collection: str | None = None) -> list[Path]:
    """Return declared raw page files, preserving manifest order.

    If ``collection`` is supplied, only entries explicitly labeled with that collection
    are accepted.  A nested collection-local ``files`` list is supported as a fallback.
    Missing or nonexistent paths fail closed.
    """
    manifest = load_json(manifest_path)
    pages: list[Path] = []

    for entry in manifest.get("files") or []:
        if not isinstance(entry, dict):
            continue
        if collection is not None and entry.get("collection") != collection:
            continue
        path = _entry_path(entry)
        if path is not None:
            pages.append(path)

    if not pages:
        for block in manifest.get("collections") or []:
            if not isinstance(block, dict):
                continue
            if collection is not None and block.get("collection") != collection:
                continue
            for entry in block.get("files") or []:
                path = _entry_path(entry)
                if path is not None:
                    pages.append(path)

    if not pages and collection is not None:
        raise RuntimeError(f"No page files declared for collection={collection!r} in {manifest_path}")
    if not pages:
        raise RuntimeError(f"No page files declared in {manifest_path}")

    missing = [p.as_posix() for p in pages if not p.is_file()]
    if missing:
        raise RuntimeError(f"Manifest references missing raw pages: {missing[:10]}")
    return pages


def chunked_snapshot_page_paths(snapshot_dir: Path) -> list[Path]:
    """Resolve pages from a finalized chunked snapshot, with gap evidence in manifests."""
    manifest_path = snapshot_dir / "manifest.json"
    manifest = load_json(manifest_path)
    chunk_refs = manifest.get("chunk_manifests") or []
    if not chunk_refs:
        return manifest_page_paths(manifest_path)

    pages: list[Path] = []
    for raw_ref in chunk_refs:
        chunk_path = Path(str(raw_ref))
        if not chunk_path.is_file():
            raise RuntimeError(f"Missing declared chunk manifest: {chunk_path}")
        chunk = load_json(chunk_path)
        for entry in chunk.get("files") or []:
            path = _entry_path(entry)
            if path is not None:
                pages.append(path)
    if not pages:
        raise RuntimeError(f"Finalized chunked snapshot has no raw pages: {snapshot_dir}")
    missing = [p.as_posix() for p in pages if not p.is_file()]
    if missing:
        raise RuntimeError(f"Chunk manifests reference missing pages: {missing[:10]}")
    return pages


def latest_manifest(root: Path) -> Path:
    manifests = sorted(root.glob("*/manifest.json"))
    if not manifests:
        raise RuntimeError(f"No snapshot manifest under {root}")
    return manifests[-1]


def latest_complete_snapshot(root: Path) -> Path:
    candidates = sorted(p for p in root.iterdir() if p.is_dir() and (p / "manifest.json").is_file())
    for snapshot in reversed(candidates):
        manifest = load_json(snapshot / "manifest.json")
        if manifest.get("complete_collection_snapshot") is True:
            return snapshot
        semantics = manifest.get("semantics")
        if isinstance(semantics, dict) and semantics.get("complete_collection_snapshot") is True:
            return snapshot
    raise RuntimeError(f"No complete snapshot under {root}")
