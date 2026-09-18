from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import pandas as pd

from ufc_edge.market_diagnostics.odds_api_v1 import (
    EXPECTED_CREDITS,
    HISTORICAL_ENDPOINT,
    MARKET,
    MARKET_SOURCE,
    MARKET_TIMING,
    REGION,
    SPORT_KEY,
    build_population,
    match_and_evaluate,
    normalize_snapshot_files,
    preflight,
    retrieve,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m0-dir", type=Path, required=True)
    parser.add_argument("--f02-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--authorized-pull", choices=("true", "false"), required=True)
    parser.add_argument("--approved-credit-ceiling", type=int, required=True)
    return parser.parse_args()


def raw_hash(raw_dir: Path) -> str:
    digest = sha256()
    for path in sorted(raw_dir.glob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw"
    normalized_dir = args.output_dir / "normalized"
    reports_dir = args.output_dir / "reports"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    oof = pd.read_parquet(args.m0_dir / "m0_oof_predictions.parquet")
    f02 = pd.read_parquet(args.f02_dir / "winner_modeling_table.parquet")
    fights = pd.read_csv("data/canonical/v0/fights.csv")
    events = pd.read_csv("data/canonical/v0/events.csv")
    fighters = pd.read_csv("data/canonical/v0/fighters.csv")

    eligible, event_table = build_population(oof, f02, fights, events)
    authorization = preflight(
        event_table,
        authorized=args.authorized_pull == "true",
        approved_ceiling=args.approved_credit_ceiling,
    )

    retrieval = retrieve(
        event_table,
        api_key=args.api_key,
        raw_dir=raw_dir,
        approved_ceiling=args.approved_credit_ceiling,
    )

    market_rows, normalization = normalize_snapshot_files(raw_dir, fighters, eligible)
    matched, diagnostic = match_and_evaluate(eligible, market_rows)

    market_rows.to_parquet(normalized_dir / "market_rows.parquet", index=False)
    matched.to_parquet(normalized_dir / "matched_rows.parquet", index=False)

    bookmaker_keys = sorted(
        {
            key
            for keys in market_rows.get("bookmaker_keys", pd.Series(dtype=object))
            for key in (keys if isinstance(keys, list) else [])
        }
    )
    book_counts = market_rows.get("book_count", pd.Series(dtype=int))
    timestamps = event_table["snapshot_timestamp"].tolist()

    retrieval_manifest = {
        "provider": MARKET_SOURCE,
        "endpoint": HISTORICAL_ENDPOINT,
        "sport_key": SPORT_KEY,
        "market": MARKET,
        "regions": [REGION],
        "bookmaker_keys_observed": bookmaker_keys,
        "bookmaker_count_observed": len(bookmaker_keys),
        "requested_snapshot_timestamps": timestamps,
        "snapshot_policy": {
            "default": "00:00:00Z on canonical UFC event date",
            "provider_floor_exception": "2020-06-06T10:05:00Z for 2020-06-06",
            "timing_label": MARKET_TIMING,
        },
        "authorized_budget": authorization,
        "request_count": retrieval["request_count"],
        "response_count": retrieval["response_count"],
        "actual_credit_usage_from_headers": retrieval["actual_credit_usage_from_headers"],
        "usage_headers": retrieval["usage_headers"],
        "failed_requests": retrieval["failed_requests"],
        "retry_count": 0,
        "duplicate_handling": "identical provider event IDs collapse within a snapshot; conflicting target-event fighter-pair groups fail closed",
        "raw_logical_sha256": raw_hash(raw_dir),
        "earliest_requested_snapshot": min(timestamps),
        "latest_requested_snapshot": max(timestamps),
        "earliest_market_observation": (
            str(market_rows["requested_snapshot_timestamp"].min()) if not market_rows.empty else None
        ),
        "latest_market_observation": (
            str(market_rows["requested_snapshot_timestamp"].max()) if not market_rows.empty else None
        ),
        "book_count_min": int(book_counts.min()) if len(book_counts) else 0,
        "book_count_median": float(book_counts.median()) if len(book_counts) else 0.0,
        "book_count_max": int(book_counts.max()) if len(book_counts) else 0,
        "retrieval_date_utc": pd.Timestamp.utcnow().isoformat(),
        "api_key_recorded": False,
    }

    matching_report = {
        "eligible_m0_rows": int(len(eligible)),
        "eligible_ufc_events": int(len(event_table)),
        "normalized_market_rows": int(len(market_rows)),
        "matched_rows": diagnostic["matched_rows"],
        "coverage_pct": diagnostic["coverage_pct"],
        **normalization,
    }

    v0_reference = {
        "matched_rows": 3363,
        "market": {
            "log_loss": 0.616480,
            "brier": 0.214158,
            "accuracy": 0.6533,
            "auc": 0.717391,
        },
        "market_plus_m0": {
            "log_loss": 0.611564,
            "brier": 0.211733,
            "accuracy": 0.6664,
            "auc": 0.725722,
        },
        "m0_positive_folds": "8/8",
        "both_primary_metrics_improved_folds": "6/8",
    }
    diagnostic_result = {
        "status": "M0_MD0R_ODDS_API_REPLICATION_COMPLETE",
        "authorized_expected_credits": EXPECTED_CREDITS,
        "retrieval_manifest_file": "retrieval_manifest.json",
        "matching_report_file": "matching_report.json",
        **diagnostic,
        "v0_reference": v0_reference,
        "guardrails": {
            "m0_changed_or_retrained": False,
            "features_changed": False,
            "roi_performed": False,
            "thresholds_optimized": False,
            "market_used_only_diagnostically": True,
            "fixed_blend_weight": 0.5,
        },
    }

    for name, payload in (
        ("retrieval_manifest.json", retrieval_manifest),
        ("matching_report.json", matching_report),
        ("diagnostic_result.json", diagnostic_result),
    ):
        (reports_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print("M0_MD0R_ODDS_API_REPLICATION_COMPLETE")
    print(json.dumps({
        "requests": retrieval["request_count"],
        "actual_credits": retrieval["actual_credit_usage_from_headers"],
        "matched_rows": diagnostic["matched_rows"],
        "coverage_pct": diagnostic["coverage_pct"],
        "replication_verdict": diagnostic["replication_verdict"],
        "worth_continuing_decision": diagnostic["worth_continuing_decision"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
