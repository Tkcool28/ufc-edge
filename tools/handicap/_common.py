from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ufc_edge.handicap.output import resolve_output_root


def add_repo_output_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help=(
            "Alternate output root. Repo-local destinations are allowed only beneath "
            "<repo>/handicap; paths outside the repo are allowed for isolated tests."
        ),
    )


def output_root(args: argparse.Namespace) -> Path:
    requested = args.output_root if args.output_root is not None else None
    return resolve_output_root(args.repo_root, requested)
