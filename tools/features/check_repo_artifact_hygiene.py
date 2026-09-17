#!/usr/bin/env python3
"""Repository artifact-hygiene guard used by the F01 validation workflow.

Generated/run/output directory names are rejected everywhere. Matrix-like files are
allowed only in the existing governed DATA source/evidence namespaces and in the
permanent model-validation bucket namespace.
"""
from __future__ import annotations

import sys
from pathlib import PurePosixPath

GENERATED_DIR_NAMES = {"run", "runs", "output", "generated", "feature_store"}
MATRIX_EXTENSIONS = {".csv", ".parquet", ".feather"}
ALLOWED_MATRIX_PREFIXES = (
    "data/raw/",
    "data/supplemental/",
    "governance/model_validation_bucket_v1/",
)


def violation(path: str) -> str | None:
    normalized = path.strip().lstrip("./")
    if not normalized:
        return None

    parts = PurePosixPath(normalized).parts
    if any(part in GENERATED_DIR_NAMES for part in parts[:-1]):
        return "generated/run/output directory"

    if PurePosixPath(normalized).suffix.lower() in MATRIX_EXTENSIONS:
        if not normalized.startswith(ALLOWED_MATRIX_PREFIXES):
            return "matrix-like file outside governed namespace"

    return None


def find_violations(paths: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in paths:
        reason = violation(path)
        if reason:
            out.append((path.strip(), reason))
    return out


def main() -> int:
    paths = [line.rstrip("\n") for line in sys.stdin]
    bad = find_violations(paths)
    if bad:
        for path, reason in bad:
            print(f"{path}: {reason}")
        print(
            "F01 must not commit generated run/output directories or matrix-like "
            "files outside explicit governed namespaces.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
