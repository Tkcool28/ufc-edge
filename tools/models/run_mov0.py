#!/usr/bin/env python3
"""Execute the frozen MOV0 STANDARD_FINISH experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ufc_edge.models.mov0 import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--f02-dir", type=Path, required=True)
    parser.add_argument("--canonical-fights", type=Path, required=True)
    parser.add_argument("--contract-dir", type=Path, required=True)
    parser.add_argument("--terrain-assignment", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_experiment(
        args.f02_dir,
        args.canonical_fights,
        args.contract_dir,
        args.terrain_assignment,
        args.output_dir,
    )
    print("MOV0_STANDARD_FINISH_PROBABILITY_V1_RUN_COMPLETE")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
