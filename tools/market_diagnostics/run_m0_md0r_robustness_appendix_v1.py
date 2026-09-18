from __future__ import annotations

import argparse
import json
from math import ceil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from ufc_edge.market_diagnostics.analysis import logit_probability


BUCKETS = (
    ("<0.05", lambda d: d < 0.05),
    ("0.05-0.10", lambda d: (d >= 0.05) & (d < 0.10)),
    ("0.10-0.15", lambda d: (d >= 0.10) & (d < 0.15)),
    (">=0.15", lambda d: d >= 0.15),
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Diagnostic robustness appendix for M0-MD0-R")
    p.add_argument("--matched-parquet", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()


def binary_log_loss(y: np.ndarray, p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-12, 1 - 1e-12)
    y = np.asarray(y, dtype=int)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def build_incremental_oof(matched: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    f = matched.copy()
    f["year"] = pd.to_datetime(f["event_date"]).dt.year
    parts: list[pd.DataFrame] = []
    folds: list[dict] = []

    for year in sorted(f["year"].unique())[1:]:
        tr = f[f["year"] < year].copy()
        va = f[f["year"] == year].copy()
        if len(tr) < 50 or va.empty or tr["target"].nunique() < 2:
            continue

        xmtr = logit_probability(tr["market_probability"]).reshape(-1, 1)
        xmva = logit_probability(va["market_probability"]).reshape(-1, 1)
        xbtr = np.column_stack([
            logit_probability(tr["market_probability"]),
            logit_probability(tr["m0_probability"]),
        ])
        xbva = np.column_stack([
            logit_probability(va["market_probability"]),
            logit_probability(va["m0_probability"]),
        ])

        yt = tr["target"].astype(int).to_numpy()
        yv = va["target"].astype(int).to_numpy()

        market_only = LogisticRegression(
            penalty=None, solver="lbfgs", max_iter=2000
        ).fit(xmtr, yt)
        market_plus_m0 = LogisticRegression(
            penalty=None, solver="lbfgs", max_iter=2000
        ).fit(xbtr, yt)

        pm = market_only.predict_proba(xmva)[:, 1]
        pb = market_plus_m0.predict_proba(xbva)[:, 1]

        part = va[
            ["fight_id", "event_date", "target", "market_probability", "m0_probability"]
        ].copy()
        part["fold_year"] = int(year)
        part["market_only_probability"] = pm
        part["market_plus_m0_probability"] = pb
        parts.append(part)

        folds.append({
            "fold_year": str(year),
            "train_rows": int(len(tr)),
            "validation_rows": int(len(va)),
            "market_plus_m0_m0_logit_coefficient": float(market_plus_m0.coef_[0][1]),
        })

    if not parts:
        raise RuntimeError("no evaluable chronological folds")
    return pd.concat(parts, ignore_index=True), folds


def main() -> int:
    args = parse_args()
    matched = pd.read_parquet(args.matched_parquet)

    required = {
        "fight_id", "event_date", "target", "market_probability", "m0_probability"
    }
    missing = sorted(required - set(matched.columns))
    if missing:
        raise RuntimeError(f"matched artifact missing columns: {missing}")

    matched["year"] = pd.to_datetime(matched["event_date"]).dt.year
    rows_by_year = {
        str(int(year)): int(count)
        for year, count in matched.groupby("year").size().items()
    }

    oof, folds = build_incremental_oof(matched)

    y = oof["target"].astype(int).to_numpy()
    p_market = oof["market_only_probability"].to_numpy(dtype=float)
    p_both = oof["market_plus_m0_probability"].to_numpy(dtype=float)

    ll_market = binary_log_loss(y, p_market)
    ll_both = binary_log_loss(y, p_both)
    brier_market = (p_market - y) ** 2
    brier_both = (p_both - y) ** 2

    oof["delta_log_loss"] = ll_market - ll_both
    oof["delta_brier"] = brier_market - brier_both
    oof["abs_m0_market_disagreement"] = (
        oof["m0_probability"].astype(float) - oof["market_probability"].astype(float)
    ).abs()

    net_ll_sum = float(oof["delta_log_loss"].sum())
    net_brier_sum = float(oof["delta_brier"].sum())
    gross_positive_ll = float(oof.loc[oof["delta_log_loss"] > 0, "delta_log_loss"].sum())
    gross_negative_ll = float(oof.loc[oof["delta_log_loss"] < 0, "delta_log_loss"].sum())

    bucket_rows = []
    for label, selector in BUCKETS:
        mask = selector(oof["abs_m0_market_disagreement"])
        s = oof.loc[mask]
        bucket_ll_sum = float(s["delta_log_loss"].sum())
        bucket_brier_sum = float(s["delta_brier"].sum())
        bucket_rows.append({
            "bucket": label,
            "rows": int(len(s)),
            "mean_delta_log_loss": float(s["delta_log_loss"].mean()),
            "median_delta_log_loss": float(s["delta_log_loss"].median()),
            "mean_delta_brier": float(s["delta_brier"].mean()),
            "median_delta_brier": float(s["delta_brier"].median()),
            "pct_fights_improved_log_loss": float((s["delta_log_loss"] > 0).mean()),
            "net_log_loss_contribution_sum": bucket_ll_sum,
            "share_of_net_log_loss_improvement": (
                float(bucket_ll_sum / net_ll_sum) if net_ll_sum != 0 else None
            ),
            "net_brier_contribution_sum": bucket_brier_sum,
            "share_of_net_brier_improvement": (
                float(bucket_brier_sum / net_brier_sum) if net_brier_sum != 0 else None
            ),
        })

    ranked = oof.sort_values("delta_log_loss", ascending=False).reset_index(drop=True)
    concentration = {}
    for pct in (0.01, 0.05, 0.10):
        n = max(1, ceil(len(ranked) * pct))
        contribution = float(ranked.head(n)["delta_log_loss"].sum())
        concentration[f"top_{int(pct * 100)}pct"] = {
            "rows": int(n),
            "log_loss_contribution_sum": contribution,
            "share_of_net_log_loss_improvement": (
                float(contribution / net_ll_sum) if net_ll_sum != 0 else None
            ),
            "share_of_gross_positive_log_loss_improvement": (
                float(contribution / gross_positive_ll) if gross_positive_ll != 0 else None
            ),
        }

    payload = {
        "status": "M0_MD0R_ROBUSTNESS_APPENDIX_V1_COMPLETE",
        "scope": {
            "purpose": "diagnostic decomposition only",
            "new_bucket_boundaries_introduced": False,
            "predeclared_disagreement_buckets": [x[0] for x in BUCKETS],
            "verdict_changed": False,
            "roi_performed": False,
            "thresholds_optimized": False,
            "new_market_requests": 0,
        },
        "matched_rows_by_year": rows_by_year,
        "early_fold_context": {
            "note": "2020 is the initial matched training pool; first incremental validation fold is 2021.",
            "folds": folds,
        },
        "incremental_evaluation_rows": int(len(oof)),
        "aggregate_contribution": {
            "mean_delta_log_loss": float(oof["delta_log_loss"].mean()),
            "net_log_loss_contribution_sum": net_ll_sum,
            "gross_positive_log_loss_contribution_sum": gross_positive_ll,
            "gross_negative_log_loss_contribution_sum": gross_negative_ll,
            "mean_delta_brier": float(oof["delta_brier"].mean()),
            "net_brier_contribution_sum": net_brier_sum,
        },
        "predeclared_disagreement_bucket_decomposition": bucket_rows,
        "log_loss_concentration": concentration,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("M0_MD0R_ROBUSTNESS_APPENDIX_V1_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
