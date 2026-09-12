#!/usr/bin/env python3
"""Command line entry point for F02 deterministic historical predictor replay."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import resource
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.features.replay import (  # noqa: E402
    CHUNK_POLICY,
    REPLAY_STATUS,
    ReplayEngine,
    ReplayError,
    build_target_row,
    canonical_json,
    deterministic_hash,
    five_year_chunk,
    git_head,
    read_parquet_rows,
    row_hash,
    sha256_file,
    target_ids_hash,
    utc_now,
    write_parquet,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["inspect", "equivalence", "bounded", "full"])
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--attach-targets", action="store_true")
    parser.add_argument("--reference", action="store_true", help="Use the untouched reference path for replay rows")
    parser.add_argument("--equivalence-targets", type=int, default=16)
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def merge_counter_dict(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value)


def merge_coverage(parts: list[dict[str, Any]]) -> dict[str, Any]:
    if not parts:
        return {}
    output: dict[str, Any] = {
        "by_year": {},
        "by_promotion": {},
        "fighter_history_depth": {},
        "slices": {},
        "scheduled_rounds": {},
        "feature_missingness_states": {},
        "elapsed_exposure_feature_states": {},
        "unavailable_requested_slices": parts[0].get("unavailable_requested_slices", {}),
    }
    for part in parts:
        for name in ("by_year", "by_promotion", "fighter_history_depth", "slices", "scheduled_rounds", "elapsed_exposure_feature_states"):
            merge_counter_dict(output[name], part.get(name, {}))
        for column, states in part.get("feature_missingness_states", {}).items():
            merged = output["feature_missingness_states"].setdefault(column, {})
            merge_counter_dict(merged, states)
    for name in ("by_year", "by_promotion", "fighter_history_depth", "slices", "scheduled_rounds", "elapsed_exposure_feature_states"):
        output[name] = dict(sorted(output[name].items()))
    output["feature_missingness_states"] = {
        name: dict(sorted(states.items()))
        for name, states in sorted(output["feature_missingness_states"].items())
    }
    return output


def default_output_dir(engine: ReplayEngine, targets: list[Any]) -> Path:
    source = engine.materializer.manifest(
        prediction_cutoff="f02-per-target",
        row_count=len(targets),
        consumer=None,
        materialized_names=engine.materializer.names(),
        code_commit=git_head(ROOT),
        generated_at_utc="1970-01-01T00:00:00Z",
    ).deterministic
    replay_id = "-".join((
        "f02-v1",
        git_head(ROOT)[:12],
        source["canonical_manifest_sha256"][:12],
        source["feature_catalog_sha256"][:12],
    ))
    return ROOT / "artifacts/features/f02/v1" / replay_id


def target_manifest(engine: ReplayEngine, predictors_manifest: dict[str, Any], target_rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row["target_state"]) for row in target_rows)
    binary = sum(1 for row in target_rows if row["binary_winner_eligible"])
    deterministic = {
        "target_contract": engine.target_contract.to_dict(),
        "predictor_manifest_sha256": predictors_manifest["deterministic_manifest_sha256"],
        "predictor_artifact_logical_sha256": predictors_manifest["deterministic"]["artifact_logical_sha256"],
        "row_count": len(target_rows),
        "binary_label_eligible_rows": binary,
        "target_state_counts": dict(sorted(counts.items())),
        "target_logical_sha256": row_hash(
            target_rows,
            [item["name"] for item in engine.schema.columns]
            + ["target_state", "binary_winner_eligible", "fighter_1_win", "winner_id"],
        ),
    }
    return {
        "deterministic": deterministic,
        "deterministic_manifest_sha256": deterministic_hash(deterministic),
        "runtime": {"created_at_utc": utc_now()},
    }


def run_replay(args: argparse.Namespace) -> int:
    discovery = ReplayEngine(ROOT, optimized=False)
    if args.mode == "bounded":
        start_year = args.start_year if args.start_year is not None else 2024
        end_year = args.end_year if args.end_year is not None else start_year
        limit = args.limit if args.limit is not None else 300
    else:
        start_year, end_year, limit = args.start_year, args.end_year, args.limit
    targets = discovery.targets(start_year=start_year, end_year=end_year, limit=limit)
    if not targets:
        raise ReplayError("selected replay universe is empty")

    fixture = discovery.equivalence_fixture(max_targets=args.equivalence_targets)
    equivalence = discovery.validate_reference_equivalence(fixture)

    if args.reference:
        engine = discovery
    else:
        engine = ReplayEngine(ROOT, optimized=True, target_dates=[item.event_date for item in targets])

    out = (args.output_dir or default_output_dir(engine, targets)).resolve()
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "schema.json", engine.schema.to_dict())
    write_json(out / "target_contract.json", engine.target_contract.to_dict())
    write_json(out / "equivalence.json", equivalence)

    grouped: dict[str, list[Any]] = {}
    for target in targets:
        grouped.setdefault(five_year_chunk(target), []).append(target)

    columns = [item["name"] for item in engine.schema.columns]
    all_rows: list[dict[str, Any]] = []
    chunk_public: list[dict[str, Any]] = []
    coverage_parts: list[dict[str, Any]] = []
    parquet_total_bytes = 0

    for chunk_name in sorted(grouped):
        chunk_targets = grouped[chunk_name]
        parquet_path = out / "chunks" / f"{chunk_name}.parquet"
        sidecar_path = out / "chunks" / f"{chunk_name}.manifest.json"
        expected_ids_hash = target_ids_hash(chunk_targets)
        if args.resume and parquet_path.exists() and sidecar_path.exists():
            sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
            if sidecar.get("target_ids_sha256") != expected_ids_hash:
                raise ReplayError(f"resume target membership mismatch for {chunk_name}")
            if sidecar.get("parquet_sha256") != sha256_file(parquet_path):
                raise ReplayError(f"resume parquet hash mismatch for {chunk_name}")
            rows = read_parquet_rows(parquet_path)
            if row_hash(rows, columns) != sidecar.get("logical_sha256"):
                raise ReplayError(f"resume logical hash mismatch for {chunk_name}")
            coverage = sidecar["coverage"]
        else:
            rows, coverage = engine.replay_rows(chunk_targets)
            write_parquet(parquet_path, rows, engine.schema)
            sidecar = {
                "chunk": chunk_name,
                "chunk_policy": CHUNK_POLICY,
                "row_count": len(rows),
                "first_target": rows[0]["fight_id"] if rows else None,
                "last_target": rows[-1]["fight_id"] if rows else None,
                "target_ids_sha256": expected_ids_hash,
                "logical_sha256": row_hash(rows, columns),
                "parquet_sha256": sha256_file(parquet_path),
                "parquet_bytes": parquet_path.stat().st_size,
                "coverage": coverage,
            }
            write_json(sidecar_path, sidecar)
        parquet_total_bytes += parquet_path.stat().st_size
        all_rows.extend(rows)
        coverage_parts.append(coverage)
        chunk_public.append({
            key: sidecar[key]
            for key in (
                "chunk", "row_count", "first_target", "last_target", "target_ids_sha256",
                "logical_sha256", "parquet_sha256", "parquet_bytes"
            )
        })

    if len(all_rows) != len(targets):
        raise ReplayError(f"row count mismatch expected={len(targets)} actual={len(all_rows)}")
    row_ids = [row["fight_id"] for row in all_rows]
    target_ids = [target.fight_id for target in targets]
    if row_ids != target_ids:
        raise ReplayError("assembled chunk order or membership does not equal deterministic target universe")
    if len(row_ids) != len(set(row_ids)):
        raise ReplayError("duplicate rows after chunk assembly")

    coverage = merge_coverage(coverage_parts)
    artifact_hash = row_hash(all_rows, columns)
    manifest = engine.build_manifest(
        targets=targets,
        rows=all_rows,
        diagnostics=coverage,
        chunks=chunk_public,
        artifact_sha256=artifact_hash,
        parquet_bytes=parquet_total_bytes,
        equivalence=equivalence,
        code_commit=git_head(ROOT),
    )
    # The predictor artifact is frozen before labels are attached.
    write_json(out / "coverage.json", coverage)
    write_json(out / "exclusions.json", {"excluded_targets": []})
    write_json(out / "manifest.json", manifest)

    target_info = None
    target_parquet_bytes = 0
    if args.attach_targets:
        by_id = {target.fight_id: target for target in targets}
        target_rows = [build_target_row(by_id[row["fight_id"]], row) for row in all_rows]
        target_path = out / "winner_modeling_table.parquet"
        write_parquet(target_path, target_rows, engine.schema, include_targets=True)
        target_info = target_manifest(engine, manifest, target_rows)
        target_info["runtime"].update({
            "parquet_sha256": sha256_file(target_path),
            "parquet_bytes": target_path.stat().st_size,
        })
        target_parquet_bytes = target_path.stat().st_size
        write_json(out / "target_manifest.json", target_info)

    elapsed = time.perf_counter() - STARTED
    peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    summary = {
        "status": REPLAY_STATUS,
        "mode": args.mode,
        "engine": "reference" if args.reference else "optimized_exact_equivalence_gated",
        "code_commit": git_head(ROOT),
        "canonical_total_fights": len(discovery.targets()),
        "selected_targets": len(targets),
        "predictor_rows": len(all_rows),
        "predictor_columns": engine.schema.row_predictor_count,
        "table_columns": len(engine.schema.columns),
        "f01_materialized_values": engine.schema.f01_materialized_value_count,
        "years": [min(target.event_date.year for target in targets), max(target.event_date.year for target in targets)],
        "promotions": sorted({target.promotion or "<missing>" for target in targets}),
        "predictor_logical_sha256": artifact_hash,
        "predictor_manifest_sha256": manifest["deterministic_manifest_sha256"],
        "predictor_parquet_bytes": parquet_total_bytes,
        "target_parquet_bytes": target_parquet_bytes,
        "target_summary": target_info["deterministic"] if target_info else None,
        "equivalence": equivalence,
        "runtime_seconds": elapsed,
        "peak_rss_kib": peak_kib,
        "output_dir": str(out),
    }
    if args.mode == "bounded":
        full_count = len(discovery.targets())
        summary["estimated_full_predictor_parquet_bytes"] = int(
            parquet_total_bytes * (full_count / max(1, len(targets)))
        )
    write_json(out / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))
    return 0


def inspect() -> int:
    engine = ReplayEngine(ROOT)
    targets = engine.targets()
    by_year = Counter(str(item.event_date.year) for item in targets)
    by_promotion = Counter(item.promotion or "<missing>" for item in targets)
    payload = {
        "code_commit": git_head(ROOT),
        "canonical_target_count": len(targets),
        "years": [min(by_year), max(by_year)],
        "promotion_count": len(by_promotion),
        "top_promotions": by_promotion.most_common(20),
        "schema": engine.schema.to_dict(),
        "target_contract": engine.target_contract.to_dict(),
        "equivalence_fixture": [item.fight_id for item in engine.equivalence_fixture()],
    }
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0


def equivalence(args: argparse.Namespace) -> int:
    engine = ReplayEngine(ROOT)
    fixture = engine.equivalence_fixture(max_targets=args.equivalence_targets)
    payload = engine.validate_reference_equivalence(fixture)
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0


STARTED = time.perf_counter()


def main() -> int:
    args = parse_args()
    if args.mode == "inspect":
        return inspect()
    if args.mode == "equivalence":
        return equivalence(args)
    return run_replay(args)


if __name__ == "__main__":
    raise SystemExit(main())
