#!/usr/bin/env python3
"""Import the exact pinned Greco1899 UFCStats raw snapshot.

This script intentionally does no normalization. Its only job is to fetch the six
selected upstream CSVs from the locked commit, verify Git blob identity, and
store source-faithful bytes under data/raw/.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


SOURCE_REPO = "Greco1899/scrape_ufc_stats"
SOURCE_COMMIT = "8e40eb945e1127bf0ef172ab211a34787948f312"
SNAPSHOT_ID = SOURCE_COMMIT[:12]
RAW_DIR = Path("data/raw/greco1899") / SNAPSHOT_ID
LOCK_PATH = Path("provenance/greco1899.lock.json")


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def fetch_bytes(path: str) -> bytes:
    url = (
        "https://raw.githubusercontent.com/"
        f"{SOURCE_REPO}/{SOURCE_COMMIT}/{path}"
    )
    req = Request(url, headers={"User-Agent": "ufc-edge-pinned-ingest/1.0"})
    with urlopen(req, timeout=60) as response:
        return response.read()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def main() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock["source_commit"] != SOURCE_COMMIT:
        raise RuntimeError("Source commit differs between ingestion code and lock file")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest_files: list[dict[str, object]] = []

    for item in lock["selected_files"]:
        path = item["path"]
        expected_blob = item["git_blob_sha"]
        data = fetch_bytes(path)
        actual_blob = git_blob_sha(data)
        if actual_blob != expected_blob:
            raise RuntimeError(
                f"Git blob mismatch for {path}: expected {expected_blob}, got {actual_blob}"
            )

        destination = RAW_DIR / path
        atomic_write(destination, data)
        manifest_files.append(
            {
                "path": path,
                "bytes": len(data),
                "git_blob_sha": actual_blob,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
        print(f"verified {path}: {len(data):,} bytes | git {actual_blob}")

    manifest = {
        "source_repository": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "snapshot_id": SNAPSHOT_ID,
        "files": manifest_files,
    }
    atomic_write(
        RAW_DIR / "manifest.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    print(f"snapshot complete: {RAW_DIR}")


if __name__ == "__main__":
    main()
