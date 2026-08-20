#!/usr/bin/env python3
"""Import the pinned TidyTuesday/fightr historical UFC rankings snapshot verbatim."""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

LOCK_PATH = Path("provenance/tidytuesday_ufc_rankings.lock.json")
RAW_HOST = "https://raw.githubusercontent.com"
USER_AGENT = "ufc-edge-data/0.1"


def blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    repo = lock["source_repository"]
    commit = lock["source_commit"]
    out_dir = Path(lock["raw_snapshot_directory"])
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_files = []
    for spec in lock["files"]:
        url = f"{RAW_HOST}/{repo}/{commit}/{spec['source_path']}"
        data = fetch(url)
        actual_blob = blob_sha1(data)
        if len(data) != int(spec["size_bytes"]):
            raise RuntimeError(f"Size mismatch: {spec['source_path']}")
        if actual_blob != spec["git_blob_sha1"]:
            raise RuntimeError(
                f"Git blob mismatch for {spec['source_path']}: "
                f"expected={spec['git_blob_sha1']} actual={actual_blob}"
            )

        destination = out_dir / spec["destination_name"]
        if destination.exists() and destination.read_bytes() != data:
            raise RuntimeError(f"Refusing to overwrite differing raw file: {destination}")
        destination.write_bytes(data)
        manifest_files.append(
            {
                "source_path": spec["source_path"],
                "destination": destination.as_posix(),
                "bytes": len(data),
                "git_blob_sha1": actual_blob,
                "sha256": hashlib.sha256(data).hexdigest(),
                "role": spec["role"],
            }
        )

    manifest = {
        "schema_version": 1,
        "source_repository": repo,
        "source_commit": commit,
        "source_commit_date": lock["source_commit_date"],
        "source_provenance": lock["source_provenance"],
        "semantics": lock["semantics"],
        "canonicalization_status": lock["canonicalization_status"],
        "files": manifest_files,
    }
    manifest_path = out_dir / "manifest.json"
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"Refusing to overwrite differing manifest: {manifest_path}")
    manifest_path.write_text(rendered, encoding="utf-8")
    print(f"Imported historical UFC rankings to {out_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
