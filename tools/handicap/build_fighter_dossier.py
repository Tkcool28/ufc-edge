from __future__ import annotations

import argparse

from _common import add_repo_output_args, output_root
from ufc_edge.handicap.builders import build_fighter_dossier, packet_output_guard, write_json
from ufc_edge.handicap.store import CanonicalStore

def main() -> int:
    parser = argparse.ArgumentParser(description="Build one H00 fighter dossier from frozen canonical DATA.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fighter-id")
    group.add_argument("--fighter", help="Canonical ID or uniquely resolvable canonical/trusted name.")
    parser.add_argument("--cutoff", required=True, help="ISO date or timestamp information cutoff.")
    add_repo_output_args(parser)
    args = parser.parse_args()
    store = CanonicalStore(args.repo_root)
    requested = args.fighter_id or args.fighter
    fighter_id = store.resolve_fighter(requested)
    path = output_root(args) / "v0" / "fighters" / f"{fighter_id}.json"
    if args.output_root is None:
        packet_output_guard(args.repo_root, path)
    packet = build_fighter_dossier(store, fighter_id, args.cutoff)
    write_json(packet, path, pretty=True)
    print(path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
