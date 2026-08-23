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

    # The index is a lookup artifact, not a substitute for a dossier. Keep only
    # compact lookup essentials here; full trusted identity-link rows remain in
    # on-demand fighter/matchup packets where they are actually useful.
    for entry in packet["fighters"]:
        entry.pop("trusted_source_links", None)

    write_json(packet, path, pretty=False)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
