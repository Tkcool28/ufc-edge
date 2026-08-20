#!/usr/bin/env python3
"""Import the pinned UFC-DataLab OCR scorecard snapshot verbatim.

The imported CSV is raw derived-source material. It is not canonical scorecard truth;
identity and score QA against UFC Edge's fight history is required later.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

LOCK_PATH = Path("provenance/ufc_datalab_scorecards.lock.json")
RAW_HOST = "https://raw.githubusercontent.com"
USER_AGENT = "ufc-edge-data/0.1"


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    repo = lock["source_repository"]
    commit = lock["source_commit"]
    out_dir = Path(lock["raw_snapshot_directory"])
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_files = []
    for spec in lock["files"]:
        source_path = spec["source_path"]
        url = f"{RAW_HOST}/{repo}/{commit}/{source_path}"
        print(f"Fetching {source_path}", flush=True)
        data = fetch(url)

        actual_size = len(data)
        actual_blob = git_blob_sha1(data)
        expected_size = int(spec["size_bytes"])
        expected_blob = spec["git_blob_sha1"]
        if actual_size != expected_size:
            raise RuntimeError(
                f"Size mismatch for {source_path}: expected={expected_size} actual={actual_size}"
            )
        if actual_blob != expected_blob:
            raise RuntimeError(
                f"Git blob mismatch for {source_path}: expected={expected_blob} actual={actual_blob}"
            )

        destination = out_dir / spec["destination_name"]
        if destination.exists():
            existing = destination.read_bytes()
            if existing != data:
                raise RuntimeError(f"Refusing to overwrite differing immutable raw file: {destination}")
        else:
            destination.write_bytes(data)

        manifest_files.append(
            {
                "source_path": source_path,
                "destination": destination.as_posix(),
                "bytes": actual_size,
                "git_blob_sha1": actual_blob,
                "sha256": sha256(data),
                "role": spec["role"],
            }
        )

    manifest = {
        "schema_version": 1,
        "source_repository": repo,
        "source_commit": commit,
        "source_commit_date_utc": lock["source_commit_date_utc"],
        "upstream_license": lock["upstream_license"],
        "canonicalization_status": lock["canonicalization_status"],
        "semantics": lock["semantics"],
        "files": manifest_files,
    }
    manifest_path = out_dir / "manifest.json"
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"Refusing to overwrite differing immutable manifest: {manifest_path}")
    manifest_path.write_text(rendered, encoding="utf-8")

    print(f"Imported pinned UFC-DataLab scorecard snapshot to {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
