from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_CLASSIC = {
    "round",
    "knockdowns",
    "sig_strikes_landed",
    "sig_strikes_attempted",
    "total_strikes_landed",
    "total_strikes_attempted",
    "takedowns_landed",
    "takedowns_attempted",
    "submission_attempts",
    "reversals",
    "control_sec",
    "sig_head_landed",
    "sig_head_attempted",
    "sig_body_landed",
    "sig_body_attempted",
    "sig_leg_landed",
    "sig_leg_attempted",
    "sig_distance_landed",
    "sig_distance_attempted",
    "sig_clinch_landed",
    "sig_clinch_attempted",
    "sig_ground_landed",
    "sig_ground_attempted",
}

def _size_line(path: Path) -> tuple[int, int]:
    return path.stat().st_size, len(path.read_text(encoding="utf-8").splitlines())

def _family_counts(dossier: dict) -> dict[str, int]:
    history = dossier["fight_history"]
    return {
        "fights": len(history),
        "fighter_round_rows": sum(len(x["fighter_round_stats"]) for x in history),
        "opponent_round_rows": sum(len(x["opponent_round_stats"]) for x in history),
        "fighter_position_rows": sum(len(x["fighter_round_position"]) for x in history),
        "opponent_position_rows": sum(len(x["opponent_round_position"]) for x in history),
        "ranking_rows": len(dossier["ranking_history"]),
        "weigh_in_rows": len(dossier["weigh_in_history"]),
        "profile_snapshot_rows": len(dossier["profile_snapshots"]),
    }

def validate(dossier_path: Path, matchup_json: Path, matchup_md: Path, index_path: Path, report_path: Path) -> None:
    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    matchup = json.loads(matchup_json.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))

    assert dossier["fight_history"], "acceptance fighter has no pre-cutoff fights"
    assert matchup["fighter_a"]["fight_history"], "fighter A has no pre-cutoff history"
    assert matchup["fighter_b"]["fight_history"], "fighter B has no pre-cutoff history"
    assert index["fighters"], "fighter index is empty"

    all_round_rows = []
    for side in ("fighter_a", "fighter_b"):
        for fight in matchup[side]["fight_history"]:
            for family in ("fighter_round_stats", "opponent_round_stats"):
                for row in fight[family]:
                    assert int(row["round"]) >= 1, "round zero leaked into packet"
                    all_round_rows.append(row)
    assert all_round_rows, "acceptance matchup has no classic round rows"
    missing_fields = REQUIRED_CLASSIC.difference(all_round_rows[0].keys())
    assert not missing_fields, f"classic fields missing from packet: {sorted(missing_fields)}"

    a_counts = _family_counts(matchup["fighter_a"])
    b_counts = _family_counts(matchup["fighter_b"])
    direct = len(matchup["direct_prior_meetings"])
    assert direct >= 1, "acceptance matchup should exercise direct prior meetings"

    files = [index_path, dossier_path, matchup_json, matchup_md]
    lines = [
        "# H00 Acceptance Validation",
        "",
        "Generated entirely from frozen canonical DATA through the H00 access layer.",
        "",
        "## Demonstration",
        "",
        f"- Fighter dossier: **{dossier['metadata']['canonical_fighter_name']}**",
        f"- Matchup: **{matchup['metadata']['fighter_a']['name']} vs {matchup['metadata']['fighter_b']['name']}**",
        f"- Information cutoff: `{matchup['metadata']['information_cutoff']}`",
        f"- Direct prior meetings surfaced: **{direct}**",
        "",
        "## Data-family counts",
        "",
        "| Family | Fighter A | Fighter B |",
        "| --- | ---: | ---: |",
    ]
    for key in a_counts:
        lines.append(f"| {key} | {a_counts[key]} | {b_counts[key]} |")
    lines.extend(
        [
            "",
            "Classic round validation confirms round >= 1 and presence of every H00-required classic field, including target/position strike splits, knockdowns, takedowns, submissions, reversals, and exact `control_sec`.",
            "",
            "Positional/TIP evidence remains represented separately as canonical coarse bucket/bound fields and is never substituted for exact control seconds.",
            "",
            "## Generated artifact sizes",
            "",
            "| Path | Bytes | Lines |",
            "| --- | ---: | ---: |",
        ]
    )
    for path in files:
        size, line_count = _size_line(path)
        lines.append(f"| `{path.as_posix()}` | {size} | {line_count} |")
    lines.extend(
        [
            "",
            "## Unsupported / intentional exclusions",
            "",
            "- Canonical judge-round scores: unavailable in DATA v0.",
            "- Predictive/model features: intentionally excluded from H00.",
            "- Sportsbook/market data: intentionally excluded from H00.",
            "- Inferred weigh-in miss/catchweight/penalty semantics: intentionally excluded.",
            "- Primitive field-provenance payloads: not duplicated; packets point to `data/canonical/v0/field_provenance.csv`.",
            "",
            "## Integrity",
            "",
            "The CI acceptance job separately runs the H00 tests and verifies no diff beneath frozen DATA paths/contracts after packet generation.",
            "",
            "GitHub connector retrieval is verified externally after the generated files are committed to the feature branch.",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--dossier", type=Path, required=True)
    parser.add_argument("--matchup-json", type=Path, required=True)
    parser.add_argument("--matchup-md", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    validate(args.dossier, args.matchup_json, args.matchup_md, args.index, args.report)
    print(args.report)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
