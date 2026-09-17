#!/usr/bin/env python3
"""CLI for M1 regularized shared-feature winner validation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ufc_edge.models.m1 import run_validation


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--f02-dir", type=Path, required=True)
    validate.add_argument("--m0-oof", type=Path, required=True)
    validate.add_argument("--feature-surface", type=Path, default=Path("models/m1/feature_surface_v1.json"))
    validate.add_argument("--output-dir", type=Path, required=True)
    validate.add_argument("--skip-ablations", action="store_true")
    args = parser.parse_args()
    result = run_validation(
        args.f02_dir,
        args.m0_oof,
        args.feature_surface,
        args.output_dir,
        run_ablations=not args.skip_ablations,
    )
    print(json.dumps({
        "status": result["status"],
        "verdict": result["verdict"],
        "oof_rows": result["oof"]["rows"],
        "oof_logical_sha256": result["oof"]["logical_sha256"],
        "aggregate": result["aggregate"],
        "development": result["development"],
        "confirmation": result["confirmation"],
        "stability": result["stability"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
