from __future__ import annotations

import argparse

from _common import add_repo_output_args, output_root
from ufc_edge.handicap.builders import build_matchup_packet, packet_output_guard, write_json
from ufc_edge.handicap.render import render_matchup_markdown
from ufc_edge.handicap.store import CanonicalStore

def main() -> int:
    parser = argparse.ArgumentParser(description="Build H00 JSON and Markdown matchup packets.")
    parser.add_argument("--fighter-a", required=True, help="Canonical ID or uniquely resolvable name.")
    parser.add_argument("--fighter-b", required=True, help="Canonical ID or uniquely resolvable name.")
    parser.add_argument("--cutoff", required=True, help="ISO date or timestamp information cutoff.")
    add_repo_output_args(parser)
    args = parser.parse_args()
    store = CanonicalStore(args.repo_root)
    a_id = store.resolve_fighter(args.fighter_a)
    b_id = store.resolve_fighter(args.fighter_b)
    base = output_root(args) / "v0" / "matchups" / f"{a_id}__{b_id}"
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")
    if args.output_root is None:
        packet_output_guard(args.repo_root, json_path)
        packet_output_guard(args.repo_root, md_path)
    packet = build_matchup_packet(store, a_id, b_id, args.cutoff)
    write_json(packet, json_path, pretty=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_matchup_markdown(packet), encoding="utf-8")
    print(json_path)
    print(md_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
