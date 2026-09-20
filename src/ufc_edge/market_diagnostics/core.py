from __future__ import annotations

from hashlib import sha256
import json
import math
import re
import unicodedata
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score

M0_OOF_ROWS = 5626
M0_OOF_LOGICAL_SHA256 = "708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c"
M0_FREEZE_VERSION = "1.0.0"
M0_FREEZE_STATUS = "M0_EMPIRICAL_WINNER_BASELINE_V1_COMPLETE"
M0_FREEZE_VERDICT = "M0_SIGNAL_CONFIRMED"
F02_PREDICTOR_LOGICAL_SHA256 = "ac55fd6fc1f19be7afac2007fccceb43b5c3f98327554d0c58fbe6cb0b164383"
F02_TARGET_LOGICAL_SHA256 = "02b735aabcb354fa16cd3800f72e5ccd504f5fb6dc9963510987c57438a44956"
BLEND_WEIGHT = 0.5
LOGIT_CLIP = 1e-6
MARKET_SOURCE = "betmma.tips via theGholland public scraper"
MARKET_TIMING_LABEL = "historical_listed_odds_timing_unspecified"


class MarketDiagnosticError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def normalize_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value.casefold().replace("’", "'"))
    return " ".join(value.split())


def american_moneyline_to_raw_implied(odds: float | int) -> float:
    value = float(odds)
    if value == 0:
        raise MarketDiagnosticError("American moneyline cannot be zero")
    return 100.0 / (value + 100.0) if value > 0 else -value / (-value + 100.0)


def decimal_odds_to_raw_implied(odds: float | int) -> float:
    value = float(odds)
    if not math.isfinite(value) or value <= 1.0:
        raise MarketDiagnosticError(f"decimal odds must be finite and > 1, got {odds!r}")
    return 1.0 / value


def proportional_no_vig(raw_p1: float, raw_p2: float) -> tuple[float, float]:
    p1, p2 = float(raw_p1), float(raw_p2)
    if not (math.isfinite(p1) and math.isfinite(p2) and p1 > 0 and p2 > 0):
        raise MarketDiagnosticError("raw implied probabilities must be finite and positive")
    return p1 / (p1 + p2), p2 / (p1 + p2)


def median_no_vig_probability(values: Sequence[float]) -> float:
    clean = np.asarray(list(values), dtype=float)
    if not len(clean) or not np.isfinite(clean).all() or ((clean <= 0) | (clean >= 1)).any():
        raise MarketDiagnosticError("invalid probabilities for median aggregation")
    return float(np.median(clean))


def fixed_blend(m0_probability: Iterable[float], market_probability: Iterable[float]) -> np.ndarray:
    m0, market = np.asarray(list(m0_probability), float), np.asarray(list(market_probability), float)
    if m0.shape != market.shape:
        raise MarketDiagnosticError("blend probability arrays differ in shape")
    return BLEND_WEIGHT * m0 + BLEND_WEIGHT * market


def metric_bundle(target: Iterable[int | bool], prob: Iterable[float]) -> dict[str, float | int | None]:
    y, p = np.asarray(list(target), int), np.clip(np.asarray(list(prob), float), 1e-12, 1 - 1e-12)
    if not len(y) or len(y) != len(p):
        raise MarketDiagnosticError("invalid metric population")
    try:
        auc: float | None = float(roc_auc_score(y, p))
    except ValueError:
        auc = None
    return {"rows": int(len(y)), "log_loss": float(log_loss(y, p, labels=[0, 1])),
            "brier": float(brier_score_loss(y, p)), "accuracy": float(accuracy_score(y, p >= .5)), "auc": auc}


def calibration_table(target: pd.Series, probability: pd.Series) -> tuple[list[dict[str, Any]], float]:
    edges = np.linspace(0, 1, 11)
    labels = [f"{edges[i]:.1f}-{edges[i+1]:.1f}" for i in range(10)]
    bins = pd.cut(probability, edges, labels=labels, include_lowest=True)
    rows, ece, total = [], 0.0, len(target)
    for label in labels:
        mask, n = bins == label, int((bins == label).sum())
        if not n:
            continue
        mp, actual = float(probability[mask].mean()), float(target[mask].astype(int).mean())
        ece += n / total * abs(mp - actual)
        rows.append({"bin": label, "rows": n, "mean_predicted": mp, "actual_win_rate": actual})
    return rows, float(ece)


def m0_oof_logical_hash(oof: pd.DataFrame) -> str:
    columns = ["fight_id", "event_date", "fold_id", "target", "naive_probability", "empirical_probability", "logistic_probability"]
    missing = [c for c in columns if c not in oof]
    if missing:
        raise MarketDiagnosticError(f"M0 OOF missing columns: {missing}")
    digest = sha256()
    for row in oof.sort_values(["event_date", "fight_id"])[columns].itertuples(index=False, name=None):
        payload = list(row); payload[1] = str(payload[1])
        digest.update(canonical_json(payload).encode()); digest.update(b"\n")
    return digest.hexdigest()


def validate_m0_freeze(freeze: dict[str, Any], oof: pd.DataFrame) -> None:
    checks = [
        freeze.get("freeze_version") == M0_FREEZE_VERSION,
        freeze.get("status") == M0_FREEZE_STATUS,
        freeze.get("verdict") == M0_FREEZE_VERDICT,
        freeze.get("oof", {}).get("rows") == M0_OOF_ROWS,
        freeze.get("oof", {}).get("logical_sha256") == M0_OOF_LOGICAL_SHA256,
        freeze.get("f02", {}).get("predictor_logical_sha256") == F02_PREDICTOR_LOGICAL_SHA256,
        freeze.get("f02", {}).get("target_logical_sha256") == F02_TARGET_LOGICAL_SHA256,
        len(oof) == M0_OOF_ROWS,
        not oof["fight_id"].duplicated().any(),
        m0_oof_logical_hash(oof) == M0_OOF_LOGICAL_SHA256,
    ]
    if not all(checks):
        raise MarketDiagnosticError("frozen M0 OOF identity mismatch")
