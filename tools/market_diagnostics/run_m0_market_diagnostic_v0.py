#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.market_diagnostics.m0_v0 import run_diagnostic  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run M0-MD0 bare-bones market diagnostic V0")
    parser.add_argument("--m0-oof", type=Path, required=True)
    parser.add_argument("--m0-freeze", type=Path, required=True)
    parser.add_argument("--f02-modeling", type=Path, required=True)
    parser.add_argument("--canonical-fighters", type=Path, required=True)
    parser.add_argument("--market-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_diagnostic(
        m0_oof_path=args.m0_oof.resolve(),
        m0_freeze_path=args.m0_freeze.resolve(),
        f02_modeling_path=args.f02_modeling.resolve(),
        canonical_fighters_path=args.canonical_fighters.resolve(),
        market_csv_path=args.market_csv.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    compact = {
        "status": result["status"],
        "matching": result["matching"],
        "same_sample_metrics": result["same_sample_metrics"],
        "correlation_and_disagreement": result["correlation_and_disagreement"],
        "incremental_information": result["incremental_information"],
        "diagnostic_table": result["diagnostic_table"],
        "verdict": result["verdict"],
    }
    print("M0_MARKET_V0_RESULT=" + json.dumps(compact, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
