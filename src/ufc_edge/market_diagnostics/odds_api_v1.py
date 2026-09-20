from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from .analysis import chronological_incremental_test, disagreement_report
from .core import (
    MarketDiagnosticError,
    calibration_table,
    decimal_odds_to_raw_implied,
    fixed_blend,
    median_no_vig_probability,
    metric_bundle,
    normalize_name,
    proportional_no_vig,
    validate_m0_oof,
)

SPORT_KEY = "mma_mixed_martial_arts"
MARKET = "h2h"
REGION = "us"
HISTORICAL_ENDPOINT = f"https://api.the-odds-api.com/v4/historical/sports/{SPORT_KEY}/odds"
HISTORICAL_START = "2020-06-06"

EXPECTED_ELIGIBLE_ROWS = 3133
EXPECTED_EVENTS = 268
EXPECTED_REQUESTS = 268
CREDITS_PER_REQUEST = 10
EXPECTED_CREDITS = 2680
HARD_REQUEST_CEILING = 300
HARD_CREDIT_CEILING = 3000

MARKET_SOURCE = "The Odds API"
MARKET_TIMING = "event_date_0000z_provider_floor_2020_06_06_1005z"


def snapshot_timestamp(event_date: str) -> str:
    date = str(pd.Timestamp(event_date).date())
    if date == "2020-06-06":
        return "2020-06-06T10:05:00Z"
    return f"{date}T00:00:00Z"


def build_population(
    oof: pd.DataFrame,
    f02: pd.DataFrame,
    fights: pd.DataFrame,
    events: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reconstruct exactly the authorized post-2020-06-06 M0 OOF population."""
    validate_m0_oof(oof)

    f02_required = {
        "fight_id",
        "event_id",
        "event_date",
        "fighter_1_id",
        "fighter_2_id",
        "promotion",
    }
    if not f02_required.issubset(f02.columns):
        raise MarketDiagnosticError("F02 artifact missing canonical identity columns")

    f02_ids = f02[list(f02_required)].copy()
    if f02_ids["fight_id"].duplicated().any():
        raise MarketDiagnosticError("F02 fight_id is not unique")

    fight_ids = fights[
        [
            "fight_id",
            "event_id",
            "fighter_a_id",
            "fighter_b_id",
            "winner_id",
            "result",
            "promotion",
        ]
    ].copy()
    event_ids = events[["event_id", "event_date", "promotion"]].rename(
        columns={"promotion": "event_promotion", "event_date": "canonical_event_date"}
    )

    pop = (
        oof.merge(f02_ids, on="fight_id", how="left", validate="one_to_one", suffixes=("", "_f02"))
        .merge(fight_ids, on="fight_id", how="left", validate="one_to_one", suffixes=("", "_fight"))
        .merge(event_ids, on="event_id", how="left", validate="many_to_one")
    )

    required_nonnull = ["event_id", "fighter_1_id", "fighter_2_id", "canonical_event_date"]
    if pop[required_nonnull].isna().any().any():
        raise MarketDiagnosticError("canonical/F02 identity missing for frozen M0 row")

    if not pop["promotion"].eq("UFC").all():
        raise MarketDiagnosticError("F02 OOF population contains non-UFC row")
    if not pop["promotion_fight"].eq("UFC").all() or not pop["event_promotion"].eq("UFC").all():
        raise MarketDiagnosticError("canonical UFC identity disagreement")

    oof_dates = pd.to_datetime(pop["event_date"]).dt.date.astype(str)
    f02_dates = pd.to_datetime(pop["event_date_f02"]).dt.date.astype(str)
    canonical_dates = pd.to_datetime(pop["canonical_event_date"]).dt.date.astype(str)
    if not oof_dates.equals(f02_dates) or not oof_dates.equals(canonical_dates):
        raise MarketDiagnosticError("M0/F02/canonical event-date disagreement")

    # Verify unordered fighter pair agreement between F02 orientation and canonical fight identity.
    for row in pop[
        ["fighter_1_id", "fighter_2_id", "fighter_a_id", "fighter_b_id"]
    ].itertuples(index=False):
        if {str(row.fighter_1_id), str(row.fighter_2_id)} != {
            str(row.fighter_a_id),
            str(row.fighter_b_id),
        }:
            raise MarketDiagnosticError("F02/canonical fighter-pair disagreement")

    pop["event_date"] = canonical_dates
    pop["m0_probability"] = pop["logistic_probability"].astype(float)
    eligible = pop[pop["event_date"] >= HISTORICAL_START].copy()

    event_table = (
        eligible[["event_id", "event_date"]]
        .drop_duplicates()
        .sort_values(["event_date", "event_id"])
        .reset_index(drop=True)
    )
    event_table["snapshot_timestamp"] = event_table["event_date"].map(snapshot_timestamp)

    if len(eligible) != EXPECTED_ELIGIBLE_ROWS or len(event_table) != EXPECTED_EVENTS:
        raise MarketDiagnosticError(
            f"approved population changed: rows={len(eligible)} events={len(event_table)}"
        )

    return eligible, event_table


def preflight(event_table: pd.DataFrame, authorized: bool, approved_ceiling: int) -> dict[str, int]:
    requests_expected = int(len(event_table))
    credits_expected = requests_expected * CREDITS_PER_REQUEST

    if not authorized:
        raise MarketDiagnosticError("authorized_pull must be true")
    if requests_expected != EXPECTED_REQUESTS or credits_expected != EXPECTED_CREDITS:
        raise MarketDiagnosticError("approved Stage-1 request estimate changed")
    if approved_ceiling != HARD_CREDIT_CEILING:
        raise MarketDiagnosticError("approved ceiling must equal the authorized 3000 credits")
    if credits_expected > approved_ceiling:
        raise MarketDiagnosticError("expected credits exceed approved ceiling")
    if requests_expected > HARD_REQUEST_CEILING:
        raise MarketDiagnosticError("expected requests exceed hard request ceiling")

    return {
        "requests_expected": requests_expected,
        "credits_expected": credits_expected,
        "approved_credit_ceiling": approved_ceiling,
        "hard_request_ceiling": HARD_REQUEST_CEILING,
        "hard_credit_ceiling": HARD_CREDIT_CEILING,
    }


def retrieve(
    event_table: pd.DataFrame,
    api_key: str,
    raw_dir: Path,
    approved_ceiling: int,
) -> dict[str, Any]:
    if not api_key:
        raise MarketDiagnosticError("THE_ODDS_API_KEY missing")

    raw_dir.mkdir(parents=True, exist_ok=True)
    made = 0
    responses = 0
    failed: list[dict[str, Any]] = []
    usage: list[dict[str, Any]] = []
    actual_credits = 0

    for row in event_table.itertuples(index=False):
        if made >= HARD_REQUEST_CEILING:
            raise MarketDiagnosticError("runtime request ceiling reached before next request")
        if (made + 1) * CREDITS_PER_REQUEST > approved_ceiling:
            raise MarketDiagnosticError("runtime nominal credit ceiling reached before next request")

        params = {
            "apiKey": api_key,
            "regions": REGION,
            "markets": MARKET,
            "date": row.snapshot_timestamp,
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }

        try:
            response = requests.get(HISTORICAL_ENDPOINT, params=params, timeout=45)
        except requests.RequestException:
            made += 1
            failed.append(
                {
                    "event_id": row.event_id,
                    "snapshot_timestamp": row.snapshot_timestamp,
                    "error": "request_exception",
                }
            )
            continue

        made += 1

        last_raw = response.headers.get("x-requests-last")
        try:
            last_cost = int(last_raw) if last_raw is not None else CREDITS_PER_REQUEST
        except ValueError:
            last_cost = CREDITS_PER_REQUEST
        actual_credits += last_cost

        usage.append(
            {
                "event_id": row.event_id,
                "x_requests_used": response.headers.get("x-requests-used"),
                "x_requests_remaining": response.headers.get("x-requests-remaining"),
                "x_requests_last": last_raw,
            }
        )

        if actual_credits > approved_ceiling:
            raise MarketDiagnosticError("provider-reported credit use exceeded approved ceiling")

        if response.status_code != 200:
            failed.append(
                {
                    "event_id": row.event_id,
                    "snapshot_timestamp": row.snapshot_timestamp,
                    "status_code": int(response.status_code),
                }
            )
            continue

        payload = response.json()
        responses += 1

        envelope = {
            "target_event_id": row.event_id,
            "target_event_date": row.event_date,
            "requested_snapshot_timestamp": row.snapshot_timestamp,
            "provider_response": payload,
        }
        output = raw_dir / f"{row.event_date}_{row.event_id}.json"
        output.write_text(json.dumps(envelope, separators=(",", ":")), encoding="utf-8")

    return {
        "request_count": made,
        "response_count": responses,
        "actual_credit_usage_from_headers": actual_credits,
        "failed_requests": failed,
        "usage_headers": usage,
    }


def _unique_fighter_name_index(fighters: pd.DataFrame) -> dict[str, str]:
    grouped: dict[str, set[str]] = {}
    for row in fighters[["fighter_id", "canonical_name"]].itertuples(index=False):
        key = normalize_name(str(row.canonical_name))
        if key:
            grouped.setdefault(key, set()).add(str(row.fighter_id))
    return {key: next(iter(ids)) for key, ids in grouped.items() if len(ids) == 1}


def normalize_snapshot_files(
    raw_dir: Path,
    fighters: pd.DataFrame,
    eligible: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Normalize only provider bouts belonging to each approved target UFC event."""
    name_index = _unique_fighter_name_index(fighters)

    approved_pairs: dict[str, set[tuple[str, str]]] = {}
    for row in eligible[["event_id", "fighter_1_id", "fighter_2_id"]].itertuples(index=False):
        pair = tuple(sorted((str(row.fighter_1_id), str(row.fighter_2_id))))
        approved_pairs.setdefault(str(row.event_id), set()).add(pair)

    normalized: list[dict[str, Any]] = []
    unresolved_names = 0
    non_target_pairs = 0
    invalid_book_quotes = 0
    duplicate_provider_rows = 0

    for path in sorted(raw_dir.glob("*.json")):
        envelope = json.loads(path.read_text(encoding="utf-8"))
        target_event_id = str(envelope["target_event_id"])
        target_event_date = str(envelope["target_event_date"])
        requested_snapshot = str(envelope["requested_snapshot_timestamp"])
        payload = envelope["provider_response"]

        provider_events = payload.get("data", []) if isinstance(payload, dict) else []
        seen_provider_ids: set[str] = set()

        for provider_event in provider_events:
            provider_id = str(provider_event.get("id", ""))
            if provider_id and provider_id in seen_provider_ids:
                duplicate_provider_rows += 1
                continue
            if provider_id:
                seen_provider_ids.add(provider_id)

            home_name = str(provider_event.get("home_team", ""))
            away_name = str(provider_event.get("away_team", ""))
            home_id = name_index.get(normalize_name(home_name))
            away_id = name_index.get(normalize_name(away_name))
            if not home_id or not away_id or home_id == away_id:
                unresolved_names += 1
                continue

            pair = tuple(sorted((home_id, away_id)))
            if pair not in approved_pairs.get(target_event_id, set()):
                non_target_pairs += 1
                continue

            per_book: list[dict[str, Any]] = []
            for bookmaker in provider_event.get("bookmakers", []):
                h2h_markets = [
                    market
                    for market in bookmaker.get("markets", [])
                    if market.get("key") == MARKET
                ]
                for market in h2h_markets:
                    outcome_map = {
                        normalize_name(str(outcome.get("name", ""))): outcome.get("price")
                        for outcome in market.get("outcomes", [])
                    }
                    home_price = outcome_map.get(normalize_name(home_name))
                    away_price = outcome_map.get(normalize_name(away_name))
                    if home_price is None or away_price is None:
                        invalid_book_quotes += 1
                        continue
                    try:
                        home_raw = decimal_odds_to_raw_implied(home_price)
                        away_raw = decimal_odds_to_raw_implied(away_price)
                        home_no_vig, away_no_vig = proportional_no_vig(home_raw, away_raw)
                    except (TypeError, ValueError, MarketDiagnosticError):
                        invalid_book_quotes += 1
                        continue
                    per_book.append(
                        {
                            "bookmaker_key": str(bookmaker.get("key", "")),
                            "home_no_vig": home_no_vig,
                            "away_no_vig": away_no_vig,
                        }
                    )

            if not per_book:
                continue

            normalized.append(
                {
                    "target_event_id": target_event_id,
                    "event_date": target_event_date,
                    "requested_snapshot_timestamp": requested_snapshot,
                    "provider_event_id": provider_id,
                    "commence_time": provider_event.get("commence_time"),
                    "pair_lo": pair[0],
                    "pair_hi": pair[1],
                    "home_id": home_id,
                    "away_id": away_id,
                    "home_market_probability": median_no_vig_probability(
                        [book["home_no_vig"] for book in per_book]
                    ),
                    "away_market_probability": median_no_vig_probability(
                        [book["away_no_vig"] for book in per_book]
                    ),
                    "book_count": len(per_book),
                    "bookmaker_keys": sorted(
                        {book["bookmaker_key"] for book in per_book if book["bookmaker_key"]}
                    ),
                }
            )

    market = pd.DataFrame(normalized)
    if market.empty:
        return market, {
            "normalized_rows": 0,
            "unresolved_provider_name_rows": unresolved_names,
            "non_target_provider_pairs": non_target_pairs,
            "invalid_book_quotes": invalid_book_quotes,
            "duplicate_provider_rows": duplicate_provider_rows,
            "ambiguous_duplicate_groups": 0,
        }

    keys = ["target_event_id", "pair_lo", "pair_hi"]
    ambiguous_groups: set[tuple[str, str, str]] = set()
    for key, group in market.groupby(keys, sort=True):
        if len(group) > 1:
            # Identical duplicate provider payloads may collapse; conflicting IDs/probabilities fail closed.
            signatures = group[
                [
                    "provider_event_id",
                    "home_id",
                    "away_id",
                    "home_market_probability",
                    "away_market_probability",
                ]
            ].drop_duplicates()
            if len(signatures) > 1:
                ambiguous_groups.add(tuple(str(v) for v in key))

    keep_mask = [
        tuple(str(v) for v in row) not in ambiguous_groups
        for row in market[keys].itertuples(index=False, name=None)
    ]
    market = market.loc[keep_mask].drop_duplicates(keys, keep="first").reset_index(drop=True)

    return market, {
        "normalized_rows": int(len(market)),
        "unresolved_provider_name_rows": unresolved_names,
        "non_target_provider_pairs": non_target_pairs,
        "invalid_book_quotes": invalid_book_quotes,
        "duplicate_provider_rows": duplicate_provider_rows,
        "ambiguous_duplicate_groups": len(ambiguous_groups),
    }


def match_and_evaluate(
    eligible: pd.DataFrame,
    market: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if market.empty:
        raise MarketDiagnosticError("no normalized The Odds API rows")

    frame = eligible.copy()
    pairs = [
        tuple(sorted((str(a), str(b))))
        for a, b in zip(frame["fighter_1_id"], frame["fighter_2_id"])
    ]
    frame["pair_lo"] = [pair[0] for pair in pairs]
    frame["pair_hi"] = [pair[1] for pair in pairs]

    keys = ["event_id", "pair_lo", "pair_hi"]
    if frame.duplicated(keys).any():
        raise MarketDiagnosticError("ambiguous canonical fight key")

    market_for_join = market.rename(columns={"target_event_id": "event_id"})
    if market_for_join.duplicated(keys).any():
        raise MarketDiagnosticError("ambiguous normalized provider fight key")

    matched = frame.merge(
        market_for_join,
        on=keys,
        how="inner",
        validate="one_to_one",
        suffixes=("", "_market"),
    )
    if matched.empty:
        raise MarketDiagnosticError("zero market matches")

    market_probability = np.where(
        matched["fighter_1_id"].eq(matched["home_id"]),
        matched["home_market_probability"],
        np.where(
            matched["fighter_1_id"].eq(matched["away_id"]),
            matched["away_market_probability"],
            np.nan,
        ),
    )
    if np.isnan(market_probability).any():
        raise MarketDiagnosticError("F02 fighter_1 market orientation failure")

    matched["market_probability"] = market_probability.astype(float)
    matched["m0_probability"] = matched["logistic_probability"].astype(float)
    matched["blend_probability"] = fixed_blend(
        matched["m0_probability"], matched["market_probability"]
    )

    market_calibration, market_ece = calibration_table(
        matched["target"], matched["market_probability"]
    )
    same_sample = {
        "50_50": metric_bundle(matched["target"], np.full(len(matched), 0.5)),
        "m0": metric_bundle(matched["target"], matched["m0_probability"]),
        "market": metric_bundle(matched["target"], matched["market_probability"]),
        "blend_50_50": metric_bundle(matched["target"], matched["blend_probability"]),
        "market_ece": market_ece,
        "market_calibration": market_calibration,
    }

    incremental = chronological_incremental_test(
        matched[["event_date", "target", "market_probability", "m0_probability"]]
    )
    disagreement = disagreement_report(
        matched["m0_probability"], matched["market_probability"]
    )

    fold_count = incremental["fold_count"]
    both = incremental["folds_market_plus_m0_better_both"]
    positive = incremental["m0_logit_coefficient"]["positive_folds"]
    market_stronger = (
        same_sample["market"]["log_loss"] < same_sample["m0"]["log_loss"]
        and same_sample["market"]["brier"] < same_sample["m0"]["brier"]
    )
    aggregate_increment = (
        incremental["market_plus_m0"]["log_loss"]
        < incremental["market_only"]["log_loss"]
        and incremental["market_plus_m0"]["brier"]
        < incremental["market_only"]["brier"]
    )

    # Predeclared qualitative replication rule. No parameter search is performed.
    if (
        market_stronger
        and aggregate_increment
        and positive == fold_count
        and both >= int(np.ceil(0.60 * fold_count))
    ):
        verdict = "MARKET_COMPLEMENTARITY_REPLICATED"
        decision = "YES — SUPPORTED, BUT MARKET GAP REMAINS LARGE"
    elif aggregate_increment and positive > fold_count / 2 and both > 0:
        verdict = "MARKET_COMPLEMENTARITY_WEAK"
        decision = "UNCERTAIN — COMPLEMENTARITY NOT ROBUST"
    elif len(matched) < 500:
        verdict = "INSUFFICIENT_ODDS_API_MATCHING"
        decision = "UNCERTAIN — COMPLEMENTARITY NOT ROBUST"
    elif (
        abs(same_sample["m0"]["log_loss"] - same_sample["market"]["log_loss"]) <= 0.015
        and abs(same_sample["m0"]["brier"] - same_sample["market"]["brier"]) <= 0.0075
    ):
        verdict = "M0_MARKET_COMPETITIVE_ON_ODDS_API"
        decision = "YES — STRONGLY SUPPORTED"
    else:
        verdict = "MARKET_COMPLEMENTARITY_NOT_REPLICATED"
        decision = "NO — CURRENT SIGNAL APPEARS FULLY SUBSUMED BY MARKET"

    result = {
        "eligible_m0_rows": int(len(frame)),
        "matched_rows": int(len(matched)),
        "coverage_pct": float(len(matched) / len(frame)),
        "same_sample_results": same_sample,
        "correlation": disagreement,
        "incremental_test": incremental,
        "replication_verdict": verdict,
        "worth_continuing_decision": decision,
    }

    output_columns = [
        "fight_id",
        "event_id",
        "event_date",
        "fighter_1_id",
        "fighter_2_id",
        "target",
        "m0_probability",
        "market_probability",
        "blend_probability",
        "provider_event_id",
        "commence_time",
        "requested_snapshot_timestamp",
        "book_count",
    ]
    return (
        matched[output_columns].sort_values(["event_date", "fight_id"]).reset_index(drop=True),
        result,
    )
