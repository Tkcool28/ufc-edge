#!/usr/bin/env python3
"""Stage B only: N-gated corrected-M1 diagnostics on frozen V1 terrain."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

EPS = 1e-15
CONF = [
    (0.50, 0.55, "50–55%"),
    (0.55, 0.60, "55–60%"),
    (0.60, 0.65, "60–65%"),
    (0.65, 0.70, "65–70%"),
    (0.70, 0.75, "70–75%"),
    (0.75, 0.80, "75–80%"),
    (0.80, 0.85, "80–85%"),
    (0.85, 1.0000001, "85%+"),
]
GENERAL_SURFACES = [
    "experience_bucket",
    "layoff_bucket",
    "scheduled_duration_bucket",
    "title_status",
    "weight_class",
    "completeness_tier",
]
MOV_SURFACES = [
    "striking_environment",
    "grappling_environment",
    "joint_mov_environment",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gate(n: int) -> str:
    return (
        "NORMAL"
        if n >= 100
        else "MODERATE_UNCERTAINTY"
        if n >= 50
        else "THIN_EXPLORATORY"
        if n >= 25
        else "INSUFFICIENT_SAMPLE"
    )


def confidence_bucket(value: float) -> str:
    for lo, hi, label in CONF:
        if lo <= value < hi:
            return label
    raise ValueError(f"pick confidence outside permanent bins: {value}")


def auc(y: np.ndarray, p: np.ndarray) -> float | None:
    if len(np.unique(y)) < 2:
        return None
    return float(roc_auc_score(y, p))


def slope_intercept(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    x = np.log(np.clip(p, EPS, 1 - EPS) / (1 - np.clip(p, EPS, 1 - EPS)))
    X = np.c_[np.ones(len(x)), x]
    beta = np.zeros(2)
    for _ in range(40):
        q = 1 / (1 + np.exp(-np.clip(X @ beta, -30, 30)))
        w = np.clip(q * (1 - q), 1e-8, None)
        step = np.linalg.solve(X.T @ (X * w[:, None]), X.T @ (y - q))
        beta += step
        if max(abs(step)) < 1e-10:
            break
    return float(beta[1]), float(beta[0])


def wilson_ci(y: np.ndarray) -> list[float]:
    n = len(y)
    ph = float(np.mean(y))
    z = 1.96
    den = 1 + z * z / n
    root = math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    lo = (ph + z * z / (2 * n) - z * root) / den
    hi = (ph + z * z / (2 * n) + z * root) / den
    return [float(lo), float(hi)]


def metric(
    group: pd.DataFrame, prob: str = "m1_probability", target: str = "target"
) -> dict[str, Any]:
    n = len(group)
    status = gate(n)
    if n < 25:
        return {"N": n, "status": status}
    p = np.clip(group[prob].astype(float).to_numpy(), EPS, 1 - EPS)
    y = group[target].astype(int).to_numpy()
    pick = np.maximum(p, 1 - p)
    picked = np.where(p > 0.5, y, 1 - y)
    return {
        "N": n,
        "status": status,
        "mean_predicted_probability": float(p.mean()),
        "observed_win_rate": float(y.mean()),
        "calibration_gap": float(y.mean() - p.mean()),
        "absolute_calibration_gap": float(abs(y.mean() - p.mean())),
        "pick_accuracy": float(picked.mean()),
        "mean_pick_confidence": float(pick.mean()),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
        "observed_ci95": wilson_ci(y),
        "auc": auc(y, p),
    }


def method_category(value: Any) -> str:
    text = str(value).strip().upper()
    if text == "KO_TKO":
        return "KO_TKO"
    if text == "SUBMISSION":
        return "SUBMISSION"
    if text == "DECISION":
        return "DECISION"
    return "OTHER"


def outcome_descriptives(
    assignment: pd.DataFrame, canonical_fights: Path
) -> list[dict[str, Any]]:
    fights = pd.read_csv(
        canonical_fights, usecols=["fight_id", "promotion", "result", "method"]
    )
    fights = fights[fights.promotion.eq("UFC")].copy()
    if fights.fight_id.duplicated().any():
        raise RuntimeError("duplicate fight_id in canonical fights outcome source")
    merged = assignment.merge(
        fights[["fight_id", "result", "method"]],
        on="fight_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if not merged["_merge"].eq("both").all():
        raise RuntimeError("frozen assignment fight missing from canonical outcome source")
    merged["method_category"] = merged["method"].map(method_category)
    rows: list[dict[str, Any]] = []
    for surface in ["striking_environment", "grappling_environment", "joint_mov_environment"]:
        for key, group in merged.groupby(surface, dropna=False):
            n = len(group)
            counts = group.method_category.value_counts()
            rows.append(
                {
                    "surface": surface,
                    "bucket": str(key),
                    "N": n,
                    "status": gate(n),
                    "ko_tko_rate": float(counts.get("KO_TKO", 0) / n),
                    "submission_rate": float(counts.get("SUBMISSION", 0) / n),
                    "decision_rate": float(counts.get("DECISION", 0) / n),
                    "other_rate": float(counts.get("OTHER", 0) / n),
                    "other_N": int(counts.get("OTHER", 0)),
                }
            )
    return rows


def comparison_template(overall: dict[str, Any], rows: list[dict[str, Any]]) -> pd.DataFrame:
    lookup = {(r.get("surface"), r.get("bucket")): r for r in rows}
    surfaces = [
        ("Overall ECE", None, None, overall.get("ece")),
        ("70–75% calibration gap", "pick_confidence", "70–75%", None),
        ("75–80% calibration gap", "pick_confidence", "75–80%", None),
        ("80–85% calibration gap", "pick_confidence", "80–85%", None),
        ("85%+ calibration gap", "pick_confidence", "85%+", None),
        ("Debut fights", "experience_bucket", "0", None),
        ("High missingness", "completeness_tier", "HIGH_MISSINGNESS", None),
        ("Long layoff", "layoff_bucket", "18+ months", None),
        ("STRIKE_ONE_SIDED", "striking_environment", "STRIKE_ONE_SIDED", None),
        ("STRIKE_TWO_SIDED", "striking_environment", "STRIKE_TWO_SIDED", None),
        ("GRAPPLE_ONE_SIDED", "grappling_environment", "GRAPPLE_ONE_SIDED", None),
        ("GRAPPLE_TWO_SIDED", "grappling_environment", "GRAPPLE_TWO_SIDED", None),
    ]
    out = []
    for name, surface, bucket, direct in surfaces:
        if direct is not None:
            value = direct
        else:
            row = lookup.get((surface, bucket), {})
            value = row.get("calibration_gap")
        out.append(
            {
                "Validation surface": name,
                "Corrected M1": value,
                "M1B": "",
                "Tree": "",
                "Boosted": "",
                "Future MOV": "",
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--assignment", type=Path, required=True)
    ap.add_argument("--m1-oof", type=Path, required=True)
    ap.add_argument("--canonical-fights", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    assignment = pd.read_csv(args.assignment)
    oof = pd.read_parquet(args.m1_oof)
    need = {"fight_id", "target", "m1_probability"}
    if not need.issubset(oof):
        raise RuntimeError("corrected M1 OOF schema missing required columns")
    if oof.fight_id.duplicated().any() or assignment.fight_id.duplicated().any():
        raise RuntimeError("duplicate fight identity")

    merged = oof[["fight_id", "target", "m1_probability"]].merge(
        assignment, on="fight_id", how="left", validate="one_to_one", indicator=True
    )
    if not merged["_merge"].eq("both").all():
        raise RuntimeError("OOF identity missing from frozen assignment")
    merged = merged.drop(columns="_merge")

    overall = metric(merged)
    slope, intercept = slope_intercept(
        merged.target.to_numpy(int), merged.m1_probability.to_numpy(float)
    )
    merged["pick_confidence"] = np.maximum(
        merged.m1_probability, 1 - merged.m1_probability
    )
    merged["selected_side_win"] = np.where(
        merged.m1_probability > 0.5, merged.target, 1 - merged.target
    )
    merged["confidence_bucket"] = merged.pick_confidence.map(confidence_bucket)

    ece = 0.0
    reliability_rows: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for lo, hi, label in CONF:
        group = merged[
            (merged.pick_confidence >= lo) & (merged.pick_confidence < hi)
        ]
        if len(group):
            gap = abs(
                float(group.selected_side_win.mean() - group.pick_confidence.mean())
            )
            ece += len(group) / len(merged) * gap
        r = (
            metric(
                group.assign(
                    m1_probability=group.pick_confidence,
                    target=group.selected_side_win,
                )
            )
            if len(group)
            else {"N": 0, "status": "INSUFFICIENT_SAMPLE"}
        )
        r.update({"surface": "pick_confidence", "bucket": label})
        rows.append(r)
        reliability_rows.append(
            {
                "bucket": label,
                "N": r["N"],
                "status": r["status"],
                "mean_pick_confidence": r.get("mean_pick_confidence"),
                "actual_pick_win_rate": r.get("observed_win_rate"),
                "calibration_gap": r.get("calibration_gap"),
                "observed_ci95": r.get("observed_ci95"),
            }
        )

    overall.update(
        {
            "calibration_slope": slope,
            "calibration_intercept": intercept,
            "ece": float(ece),
        }
    )

    for column in GENERAL_SURFACES + MOV_SURFACES:
        for key, group in merged.groupby(column, dropna=False):
            r = metric(group)
            r.update({"surface": column, "bucket": str(key)})
            rows.append(r)

    # Required confidence calibration inside each assignable striking/grappling
    # environment. N-gating is applied at the final environment×confidence cell.
    for column in ["striking_environment", "grappling_environment"]:
        for env, env_group in merged.groupby(column, dropna=False):
            if str(env) == "UNASSIGNABLE_BY_CONTRACT":
                continue
            for _, _, label in CONF:
                group = env_group[env_group.confidence_bucket.eq(label)]
                r = (
                    metric(
                        group.assign(
                            m1_probability=group.pick_confidence,
                            target=group.selected_side_win,
                        )
                    )
                    if len(group)
                    else {"N": 0, "status": "INSUFFICIENT_SAMPLE"}
                )
                r.update(
                    {
                        "surface": f"pick_confidence_within_{column}",
                        "bucket": f"{env}::{label}",
                    }
                )
                rows.append(r)

    mov_outcomes = outcome_descriptives(assignment, args.canonical_fights)
    template = comparison_template(overall, rows)

    report = {
        "status": "M1_CALIBRATION_DIAGNOSTIC_V1_COMPLETE",
        "overall": overall,
        "rows": rows,
        "historical_mov_outcomes": mov_outcomes,
        "formulas": {
            "calibration_gap": "observed_win_rate - mean_predicted_probability",
            "brier": "mean((p-y)^2)",
            "log_loss": "-mean(y log(p)+(1-y)log(1-p)); epsilon=1e-15",
            "calibration_slope_intercept": "logistic regression of target on logit(p)",
            "auc": "sklearn.metrics.roc_auc_score; suppressed for single-class cells",
            "confidence_interval": "95% Wilson interval for observed proportion",
            "sample_gate": "N<25 returns only N/status for model-performance cells",
            "ece": "confidence-bin weighted absolute pick-calibration gap",
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "M1_CALIBRATION_DIAGNOSTIC_V1.json"
    csv_path = args.output_dir / "M1_CALIBRATION_DIAGNOSTIC_V1.csv"
    reliability_path = args.output_dir / "M1_RELIABILITY_CURVE_V1.csv"
    mov_path = args.output_dir / "HISTORICAL_MOV_OUTCOME_DESCRIPTIVES_V1.csv"
    template_path = args.output_dir / "MODEL_COMPARISON_TEMPLATE_V1.csv"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    pd.DataFrame(reliability_rows).to_csv(reliability_path, index=False)
    pd.DataFrame(mov_outcomes).to_csv(mov_path, index=False)
    template.to_csv(template_path, index=False)

    manifest = {
        "status": "M1_CALIBRATION_DIAGNOSTIC_V1_COMPLETE",
        "assignment_sha256": sha(args.assignment),
        "m1_oof_sha256": sha(args.m1_oof),
        "canonical_fights_sha256": sha(args.canonical_fights),
        "report_sha256": sha(json_path),
        "rows": len(merged),
        "outputs": {
            json_path.name: sha(json_path),
            csv_path.name: sha(csv_path),
            reliability_path.name: sha(reliability_path),
            mov_path.name: sha(mov_path),
            template_path.name: sha(template_path),
        },
        "generator_code_sha256": sha(Path(__file__)),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print("M1_CALIBRATION_DIAGNOSTIC_V1_COMPLETE")


if __name__ == "__main__":
    main()
