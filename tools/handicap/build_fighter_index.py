from __future__ import annotations

import argparse

from _common import add_repo_output_args, output_root
from ufc_edge.handicap.builders import build_fighter_index, packet_output_guard, write_json
from ufc_edge.handicap.store import CanonicalStore

def main() -> int:
    parser = argparse.ArgumentParser(description="Build the H00 trusted canonical fighter index.")
    add_repo_output_args(parser)
    args = parser.parse_args()
    store = CanonicalStore(args.repo_root)
    out_root = output_root(args)
    path = out_root / "v0" / "index" / "fighters.json"
    if args.output_root is None:
        packet_output_guard(args.repo_root, path)
    packet = build_fighter_index(store)
    write_json(packet, path, pretty=True)
    print(path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
