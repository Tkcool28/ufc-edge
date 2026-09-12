#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.models.m1 import run_validation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run M1 regularized shared-feature UFC winner validation")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--f02-dir", type=Path, required=True)
    validate.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "validate":
        result = run_validation(args.f02_dir.resolve(), args.output_dir.resolve())
        compact = {
            "status": result["status"],
            "dataset": result["dataset"],
            "aggregate": result["aggregate"],
            "m1_minus_m0": result["m1_minus_m0"],
            "calibration_ece": result["calibration"]["expected_calibration_error"],
            "regularization": result["regularization"],
            "oof": result["oof"],
            "orientation": result["orientation"],
            "verdict": result["verdict"],
        }
        print("M1_FULL_RESULT=" + json.dumps(compact, sort_keys=True, separators=(",", ":")))
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
