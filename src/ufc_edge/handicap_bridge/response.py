from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Iterable

RESPONSE_SCHEMA = "h01-response-0.1"
CACHE_BRANCH = "handicap-cache"


def file_record(root: Path, path: Path) -> dict[str, object]:
    root_r = root.resolve()
    path_r = path.resolve()
    if root_r not in path_r.parents and path_r != root_r:
        raise ValueError("file is outside response root")
    data = path_r.read_bytes()
    return {
        "path": path_r.relative_to(root_r).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def build_response_manifest(
    *,
    issue_number: int,
    kind: str,
    request_hash: str,
    source_main_sha: str,
    h00_generator_commit: str,
    information_cutoff: str,
    packet_schema_version: str,
    response_root: Path,
    generated_paths: Iterable[Path],
    status: str = "complete",
) -> dict[str, object]:
    files = [file_record(response_root, path) for path in generated_paths]
    return {
        "schema": RESPONSE_SCHEMA,
        "status": status,
        "issue_number": issue_number,
        "kind": kind,
        "request_hash": request_hash,
        "source_main_sha": source_main_sha,
        "h00_generator_commit": h00_generator_commit,
        "information_cutoff": information_cutoff,
        "packet_schema_version": packet_schema_version,
        "cache_branch": CACHE_BRANCH,
        "cache_commit_sha": None,
        "generation_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "files": files,
    }


def write_manifest(manifest: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def success_comment(manifest: dict[str, object], manifest_path: str) -> str:
    lines = [
        "H00_REQUEST_COMPLETE",
        "",
        f"request_issue: {manifest['issue_number']}",
        f"kind: {manifest['kind']}",
        f"source_main: {manifest['source_main_sha']}",
        f"cache_branch: {manifest['cache_branch']}",
        f"cache_commit: {manifest.get('cache_commit_sha') or 'PENDING'}",
        f"cutoff: {manifest['information_cutoff']}",
        "",
        "manifest:",
        manifest_path,
    ]
    for record in manifest["files"]:
        path = record["path"]
        if str(path).endswith(".json"):
            label = "json"
        elif str(path).endswith(".md"):
            label = "markdown"
        else:
            label = "file"
        lines.extend(["", f"{label}:", str(path)])
    return "\n".join(lines)


def failure_comment(issue_number: int, category: str, message: str, source_main_sha: str) -> str:
    safe = " ".join(message.replace("\n", " ").split())[:500]
    return "\n".join([
        "H00_REQUEST_FAILED",
        "",
        f"request_issue: {issue_number}",
        f"failure_category: {category}",
        f"message: {safe}",
        f"source_main: {source_main_sha}",
    ])
