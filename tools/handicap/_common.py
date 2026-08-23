from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

def add_repo_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Explicit alternate output root (primarily for tests); default is <repo>/handicap.",
    )

def output_root(args: argparse.Namespace) -> Path:
    return args.output_root if args.output_root is not None else args.repo_root / "handicap"
