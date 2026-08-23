#!/usr/bin/env python3
"""Bounded CLI for the F01 V1 point-in-time materializer.

No default output directory is created. Results go to stdout unless --output is
explicitly supplied by the caller; generated files are runtime artifacts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.features.materializer import V1Materializer  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fighter-id")
    parser.add_argument("--fight-id", help="Target canonical fight; materializes both participants when fighter-id is omitted")
    parser.add_argument("--prediction-as-of")
    parser.add_argument("--consumer", choices=["model0", "model1", "tree"])
    parser.add_argument("--validate-bounded", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    materializer = V1Materializer(ROOT)
    if args.validate_bounded:
        payload = materializer.bounded_real_validation()
    else:
        if not args.prediction_as_of:
            raise SystemExit("--prediction-as-of is required unless --validate-bounded is used")
        if args.fighter_id:
            state = materializer.materialize_fighter(
                args.fighter_id,
                args.prediction_as_of,
                target_fight_id=args.fight_id,
                consumer=args.consumer,
            )
            payload = {
                "kind": "fighter_state",
                "fighter_id": state.fighter_id,
                "prediction_as_of": state.prediction_as_of,
                "target_fight_id": state.target_fight_id,
                "state": state.audit_projection(),
            }
            row_count = 1
            names = sorted(state.values)
        elif args.fight_id:
            fight = materializer.store.require_fight(args.fight_id)
            matchup = materializer.materialize_matchup(
                fight.fighter_a_id,
                fight.fighter_b_id,
                args.prediction_as_of,
                target_fight_id=args.fight_id,
                consumer=args.consumer,
            )
            payload = {
                "kind": "matchup_state",
                "fighter_1_id": matchup.fighter_1_id,
                "fighter_2_id": matchup.fighter_2_id,
                "prediction_as_of": matchup.prediction_as_of,
                "target_fight_id": matchup.target_fight_id,
                "fighter_1_state": matchup.fighter_1.audit_projection(),
                "fighter_2_state": matchup.fighter_2.audit_projection(),
                "interactions": {name: value.to_dict() for name, value in sorted(matchup.interactions.items())},
            }
            row_count = 1
            names = sorted(set(matchup.fighter_1.values) | set(matchup.fighter_2.values) | set(matchup.interactions))
        else:
            raise SystemExit("provide --fighter-id or --fight-id")

        manifest = materializer.manifest(
            prediction_cutoff=args.prediction_as_of,
            row_count=row_count,
            consumer=args.consumer,
            materialized_names=names,
        )
        payload["provenance"] = manifest.to_dict()

    rendered = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
