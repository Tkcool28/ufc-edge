from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ufc_edge.handicap_bridge.cache import prune_cache


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune disposable H01 request cache directories.")
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--keep", type=int, default=20)
    args = parser.parse_args()
    removed = prune_cache(Path(args.cache_root), args.keep)
    for item in removed:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
