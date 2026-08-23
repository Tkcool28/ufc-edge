from __future__ import annotations

import argparse

from _common import add_repo_output_args, output_root
from ufc_edge.handicap.builders import packet_output_guard
from ufc_edge.handicap.cards import build_card_packets
from ufc_edge.handicap.store import CanonicalStore

def main() -> int:
    parser = argparse.ArgumentParser(description="Build H00 packets for every canonical fight in an event.")
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--cutoff", required=True, help="ISO date or timestamp information cutoff.")
    add_repo_output_args(parser)
    args = parser.parse_args()
    store = CanonicalStore(args.repo_root)
    out_root = output_root(args)
    if args.output_root is None:
        packet_output_guard(args.repo_root, out_root)
    manifest = build_card_packets(store, args.event_id, args.cutoff, out_root)
    print(out_root / "v0" / "cards" / args.event_id / "manifest.json")
    print(f"generated {len(manifest['fights'])} fight packets")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
