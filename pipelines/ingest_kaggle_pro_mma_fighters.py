#!/usr/bin/env python3
"""Import pinned Kaggle v1 CC0 UFC/Bellator/ONE fighter-profile companion."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

LOCK = Path("provenance/kaggle_pro_mma_fighters.lock.json")
USER_AGENT = "ufc-edge-data/0.2 (private modeling research)"


def main() -> int:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    owner, slug = lock["dataset_handle"].split("/", 1)
    version = int(lock["dataset_version"])
    params = urllib.parse.urlencode({"datasetVersionNumber": str(version)})
    url = f"https://www.kaggle.com/api/v1/datasets/download/{owner}/{slug}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/zip"})
    with urllib.request.urlopen(req, timeout=180) as response:
        archive = response.read()
        content_type = response.headers.get("content-type", "")
        status = response.status
    if status != 200 or len(archive) < 1000:
        raise RuntimeError(f"Unexpected Kaggle response: status={status} bytes={len(archive)}")

    expected_name = lock["expected"]["archive_file"]
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            names = zf.namelist()
            if expected_name not in names:
                raise RuntimeError(f"Expected {expected_name!r}; archive contains {names}")
            csv_bytes = zf.read(expected_name)
    except zipfile.BadZipFile as exc:
        raise RuntimeError(f"Kaggle response is not ZIP; content-type={content_type!r}") from exc

    text = csv_bytes.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise RuntimeError("Fighter CSV is empty")
    header, data_rows = rows[0], rows[1:]
    expected_rows = int(lock["expected"]["data_rows"])
    if len(data_rows) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} fighter rows, found {len(data_rows)}")

    out_dir = Path(lock["raw_snapshot_directory"])
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / expected_name
    if csv_path.exists() and csv_path.read_bytes() != csv_bytes:
        raise RuntimeError(f"Refusing to overwrite differing immutable file: {csv_path}")
    csv_path.write_bytes(csv_bytes)

    manifest = {
        "schema_version": 1,
        "source_platform": lock["source_platform"],
        "dataset_handle": lock["dataset_handle"],
        "dataset_version": version,
        "dataset_title": lock["dataset_title"],
        "license": lock["license"],
        "upstream_origin": lock["upstream_origin"],
        "canonicalization_status": lock["canonicalization_status"],
        "semantics": lock["semantics"],
        "download_url": url,
        "archive": {
            "bytes": len(archive),
            "sha256": hashlib.sha256(archive).hexdigest(),
            "content_type": content_type
        },
        "file": {
            "path": csv_path.as_posix(),
            "bytes": len(csv_bytes),
            "sha256": hashlib.sha256(csv_bytes).hexdigest(),
            "data_rows": len(data_rows),
            "columns": header
        }
    }
    manifest_path = out_dir / "manifest.json"
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != rendered:
        raise RuntimeError(f"Refusing to overwrite differing immutable manifest: {manifest_path}")
    manifest_path.write_text(rendered, encoding="utf-8")
    print(f"Imported {len(data_rows)} CC0 MMA fighter profiles; columns={len(header)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
