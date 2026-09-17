#!/usr/bin/env python3
"""Read-only M1 missingness / availability temporal leakage audit V1.

This diagnostic consumes frozen old/corrected F02 and M1 artifacts. It does not
modify DATA/F00/F01/F02, retrain M1, change the feature surface, tune models, or
repair any discovered defect.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ERAS = (
    ("2015-2018", 2015, 2018),
    ("2019-2022", 2019, 2022),
    ("2023-2024", 2023, 2024),
    ("2025-2026", 2025, 2026),
)
EPS = 1e-12
REACH_MISSING = "pair::ctx__physical_size_profile__reach_cm::missing_diff"
HEIGHT_MISSING = "pair::ctx__physical_size_profile__height_cm::missing_diff"
PRIOR_COUNT_VALUE = "pair::fs__prior_fight_count__career__raw::diff"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--old-f02-dir", type=Path, required=True)
    p.add_argument("--new-f02-dir", type=Path, required=True)
    p.add_argument("--old-m1-dir", type=Path, required=True)
    p.add_argument("--new-m1-dir", type=Path, required=True)
    p.add_argument("--feature-surface", type=Path, required=True)
    p.add_argument("--feature-catalog", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_cutoff(text: str) -> str:
    return " ".join(str(text).lower().replace("-", " ").split())


def strict_prior(text: str) -> bool:
    t = normalize_cutoff(text)
    return "strictly before" in t or "strictly pre " in t


def source_columns(feature: str) -> tuple[str, str] | None:
    if feature.startswith("pair::") and feature.endswith("::missing_diff"):
        key = feature[len("pair::") : -len("::missing_diff")]
        return f"f1__{key}", f"f2__{key}"
    if feature.startswith("mx::") and feature.endswith("::missing_diff"):
        key = feature[len("mx::") : -len("::missing_diff")]
        parts = key.split("__")
        if len(parts) < 2:
            raise ValueError(f"unsupported matchup missingness feature: {feature}")
        concept, suffix = parts[0], "__".join(parts[1:])
        return (
            f"mx__{concept}__f1_vs_f2__{suffix}",
            f"mx__{concept}__f2_vs_f1__{suffix}",
        )
    return None


def coefficient_stats(path: Path) -> dict[str, dict[str, float | int | None]]:
    folds = load_json(path)
    by_feature: dict[str, list[float]] = {}
    for fold in folds:
        for row in fold["coefficients"]:
            by_feature.setdefault(row["feature"], []).append(float(row["coefficient"]))
    out: dict[str, dict[str, float | int | None]] = {}
    for feature, vals in by_feature.items():
        a = np.asarray(vals, dtype=float)
        nz = a[np.abs(a) > EPS]
        pos = int((nz > 0).sum())
        neg = int((nz < 0).sum())
        out[feature] = {
            "mean": float(a.mean()),
            "std": float(a.std(ddof=0)),
            "fold_nonzero_count": int(len(nz)),
            "sign_stability": None if len(nz) == 0 else float(max(pos, neg) / len(nz)),
            "max_abs": float(np.max(np.abs(a))),
        }
    return out


def build_career_lookup(frame: pd.DataFrame) -> dict[tuple[str, str], dict[str, float | int]]:
    """Compute prior/future UFC career facts around each fight for both fighters."""
    mask = frame["promotion"].eq("UFC") & frame["binary_winner_eligible"].eq(True)
    base = frame.loc[mask, ["fight_id", "event_date", "event_id", "fighter_1_id", "fighter_2_id", "winner_id"]].copy()
    base["event_date"] = pd.to_datetime(base["event_date"], errors="raise")
    appearances: list[dict[str, Any]] = []
    for r in base.itertuples(index=False):
        appearances.append({"fight_id": str(r.fight_id), "event_date": r.event_date, "event_id": str(r.event_id), "fighter_id": str(r.fighter_1_id), "won": int(str(r.winner_id) == str(r.fighter_1_id))})
        appearances.append({"fight_id": str(r.fight_id), "event_date": r.event_date, "event_id": str(r.event_id), "fighter_id": str(r.fighter_2_id), "won": int(str(r.winner_id) == str(r.fighter_2_id))})
    app = pd.DataFrame(appearances).sort_values(["fighter_id", "event_date", "event_id", "fight_id"]).reset_index(drop=True)
    lookup: dict[tuple[str, str], dict[str, float | int]] = {}
    for fighter, g in app.groupby("fighter_id", sort=False):
        g = g.reset_index(drop=True)
        dates = pd.to_datetime(g["event_date"]).tolist()
        wins = g["won"].astype(int).to_numpy()
        prefix = np.concatenate(([0], np.cumsum(wins)))
        n = len(g)
        first = dates[0]
        last = dates[-1]
        for i, row in g.iterrows():
            current = dates[i]
            prior_fights = i
            future_fights = n - i - 1
            prior_wins = int(prefix[i])
            future_wins = int(prefix[n] - prefix[i + 1])
            prior_years = 0.0 if i == 0 else float((current - first).days / 365.25)
            future_years = 0.0 if i == n - 1 else float((last - current).days / 365.25)
            lookup[(str(row["fight_id"]), str(fighter))] = {
                "prior_fights": int(prior_fights),
                "prior_wins": int(prior_wins),
                "prior_years": prior_years,
                "future_fights": int(future_fights),
                "future_wins": int(future_wins),
                "future_years": future_years,
            }
    return lookup


def feature_state(frame: pd.DataFrame, feature: str) -> np.ndarray:
    cols = source_columns(feature)
    if cols is None:
        raise ValueError(feature)
    a = pd.to_numeric(frame[cols[0]], errors="coerce")
    b = pd.to_numeric(frame[cols[1]], errors="coerce")
    return a.isna().to_numpy(dtype=int) - b.isna().to_numpy(dtype=int)


def support_state(frame: pd.DataFrame) -> np.ndarray:
    a = pd.to_numeric(frame["f1__fs__prior_fight_count__career__raw"], errors="coerce")
    b = pd.to_numeric(frame["f2__fs__prior_fight_count__career__raw"], errors="coerce")
    delta = (a - b).to_numpy(dtype=float)
    return np.sign(delta).astype(int)


def state_target_metrics(frame: pd.DataFrame, state: np.ndarray, *, mode: str) -> dict[str, Any]:
    active = state != 0
    n = int(active.sum())
    y = frame["fighter_1_win"].astype(int).to_numpy()
    years = pd.to_datetime(frame["event_date"]).dt.year.to_numpy()
    if mode == "availability":
        # +1 means f1 missing / f2 available; -1 means f1 available / f2 missing.
        favored_side = np.where(state < 0, 1, 2)
    elif mode == "higher_support":
        # +1 means f1 has greater prior support; -1 means f2 has greater prior support.
        favored_side = np.where(state > 0, 1, 2)
    else:
        raise ValueError(mode)
    favored_win = np.where(favored_side == 1, y, 1 - y)
    out: dict[str, Any] = {
        "rows": int(len(frame)),
        "active_rows": n,
        "prevalence": float(n / len(frame)) if len(frame) else None,
        "mean": float(np.mean(state)) if len(state) else None,
        "std": float(np.std(state)) if len(state) else None,
        "favored_side_win_rate": None if n == 0 else float(favored_win[active].mean()),
        "f1_win_rate_when_state_negative": None if int((state < 0).sum()) == 0 else float(y[state < 0].mean()),
        "f1_win_rate_when_state_positive": None if int((state > 0).sum()) == 0 else float(y[state > 0].mean()),
        "negative_rows": int((state < 0).sum()),
        "positive_rows": int((state > 0).sum()),
    }
    era: dict[str, Any] = {}
    for label, lo, hi in ERAS:
        m = (years >= lo) & (years <= hi)
        am = m & active
        era[label] = {
            "rows": int(m.sum()),
            "active_rows": int(am.sum()),
            "prevalence": None if int(m.sum()) == 0 else float(am.sum() / m.sum()),
            "favored_side_win_rate": None if int(am.sum()) == 0 else float(favored_win[am].mean()),
        }
    out["eras"] = era
    return out


def career_comparison(frame: pd.DataFrame, state: np.ndarray, lookup: dict[tuple[str, str], dict[str, float | int]], *, mode: str) -> dict[str, Any]:
    y = frame["fighter_1_win"].astype(int).to_numpy()
    active_idx = np.flatnonzero(state != 0)
    rows: list[dict[str, float | int]] = []
    for i in active_idx:
        r = frame.iloc[i]
        s = int(state[i])
        if mode == "availability":
            favored_side = 1 if s < 0 else 2
        elif mode == "higher_support":
            favored_side = 1 if s > 0 else 2
        else:
            raise ValueError(mode)
        other_side = 2 if favored_side == 1 else 1
        fid = str(r[f"fighter_{favored_side}_id"])
        oid = str(r[f"fighter_{other_side}_id"])
        fight_id = str(r["fight_id"])
        a = lookup.get((fight_id, fid))
        b = lookup.get((fight_id, oid))
        if a is None or b is None:
            continue
        d: dict[str, float | int] = {"favored_won": int(y[i] if favored_side == 1 else 1 - y[i])}
        for k in ("prior_fights", "prior_wins", "prior_years", "future_fights", "future_wins", "future_years"):
            d[f"favored_{k}"] = a[k]
            d[f"other_{k}"] = b[k]
            d[f"delta_{k}"] = float(a[k]) - float(b[k])
        rows.append(d)
    if not rows:
        return {"rows": 0}
    x = pd.DataFrame(rows)
    out: dict[str, Any] = {"rows": int(len(x)), "favored_side_win_rate": float(x["favored_won"].mean())}
    for period in ("prior", "future"):
        for metric in ("fights", "wins", "years"):
            dcol = f"delta_{period}_{metric}"
            out[f"favored_more_{period}_{metric}_rate"] = float((x[dcol] > 0).mean())
            out[f"favored_mean_{period}_{metric}"] = float(x[f"favored_{period}_{metric}"].mean())
            out[f"other_mean_{period}_{metric}"] = float(x[f"other_{period}_{metric}"].mean())
            out[f"mean_delta_{period}_{metric}"] = float(x[dcol].mean())
    out["future_minus_prior_more_fights_rate"] = float(out["favored_more_future_fights_rate"] - out["favored_more_prior_fights_rate"])
    return out


def concept_meta(catalog_by_name: dict[str, dict[str, Any]], source_concept: str) -> dict[str, Any]:
    c = catalog_by_name.get(source_concept, {})
    return {
        "input_time_scope": c.get("input_time_scope"),
        "information_cutoff_rule": c.get("information_cutoff_rule"),
        "strict_prior_contract": strict_prior(c.get("information_cutoff_rule", "")),
        "missingness_behavior": c.get("missingness_behavior"),
        "minimum_sample": c.get("minimum_sample"),
        "coverage_expectation": c.get("coverage_expectation"),
        "canonical_input_tables": c.get("canonical_input_tables", []),
        "canonical_input_fields": c.get("canonical_input_fields", {}),
        "provenance_requirement": c.get("provenance_requirement"),
    }


def completed_value_test(old: pd.DataFrame, new: pd.DataFrame, feature: str) -> dict[str, Any]:
    cols = source_columns(feature)
    if cols is None:
        return {"rows_filled": 0}
    oa = pd.to_numeric(old[cols[0]], errors="coerce")
    ob = pd.to_numeric(old[cols[1]], errors="coerce")
    na = pd.to_numeric(new[cols[0]], errors="coerce")
    nb = pd.to_numeric(new[cols[1]], errors="coerce")
    old_state = oa.isna().to_numpy(dtype=int) - ob.isna().to_numpy(dtype=int)
    filled = (old_state != 0) & na.notna().to_numpy() & nb.notna().to_numpy()
    n = int(filled.sum())
    if n == 0:
        return {"rows_filled": 0}
    available_side = np.where(old_state < 0, 1, 2)
    available_value = np.where(available_side == 1, na.to_numpy(dtype=float), nb.to_numpy(dtype=float))
    other_value = np.where(available_side == 1, nb.to_numpy(dtype=float), na.to_numpy(dtype=float))
    delta = available_value - other_value
    y = old["fighter_1_win"].astype(int).to_numpy()
    avail_win = np.where(available_side == 1, y, 1 - y)
    return {
        "rows_filled": n,
        "available_side_win_rate": float(avail_win[filled].mean()),
        "available_side_larger_completed_value_rate": float((delta[filled] > 0).mean()),
        "mean_completed_value_advantage": float(np.mean(delta[filled])),
    }


def classify(row: dict[str, Any]) -> tuple[str, list[str]]:
    feature = row["feature"]
    if row["type"] == "support/sample count":
        return "POINT_IN_TIME_SAFE", ["value is an explicitly pre-fight accumulated support count; used as negative control"]
    if feature == REACH_MISSING:
        return "CONFIRMED_TEMPORAL_LEAKAGE", ["reproduced positive control: future-derived profile availability/survivorship proxy"]

    evidence = row["diagnostic_basis"]
    n = int(evidence.get("active_rows", 0) or 0)
    win = evidence.get("favored_side_win_rate")
    career = row.get("career", {})
    future_rate = career.get("favored_more_future_fights_rate")
    prior_rate = career.get("favored_more_prior_fights_rate")
    gap = career.get("future_minus_prior_more_fights_rate")
    future_delta = career.get("mean_delta_future_fights")
    prior_delta = career.get("mean_delta_prior_fights")
    coeff = row.get("corrected_coefficient", {})
    sign_stability = coeff.get("sign_stability")
    max_abs = coeff.get("max_abs")

    reasons: list[str] = []
    strong_target = n >= 20 and win is not None and abs(float(win) - 0.5) >= 0.20
    future_dominant = (
        n >= 20 and future_rate is not None and prior_rate is not None and gap is not None
        and float(future_rate) >= 0.75 and float(gap) >= 0.15
        and future_delta is not None and prior_delta is not None
        and float(future_delta) >= float(prior_delta) + 1.5
    )
    stable_model_use = sign_stability is not None and max_abs is not None and float(sign_stability) >= 0.75 and float(max_abs) >= 0.10

    if strong_target:
        reasons.append("availability/support state has strong target separation")
    if future_dominant:
        reasons.append("future-career separation materially exceeds prior-career separation")
    if stable_model_use:
        reasons.append("missingness coefficient is materially nonzero with stable sign across folds")

    # Confirmation requires multiple independent signals, not a single threshold.
    if strong_target and future_dominant:
        reasons.append("combined target + future-dominant pattern matches the leakage signature")
        return "CONFIRMED_TEMPORAL_LEAKAGE", reasons

    suspicious_count = int(strong_target) + int(future_dominant) + int(stable_model_use)
    if n >= 20 and suspicious_count >= 2:
        return "POTENTIAL_TEMPORAL_LEAKAGE", reasons

    # No active state on corrected OOF cannot contaminate the corrected OOF via this channel.
    # If old data had active rows, retain the historical evidence classification above.
    if n == 0:
        reasons.append("missingness state is inactive on the selected diagnostic OOF population")
    else:
        reasons.append("no multi-signal evidence of future-derived availability leakage")
    return "POINT_IN_TIME_SAFE", reasons


def main() -> None:
    a = parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)

    old = pd.read_parquet(a.old_f02_dir / "winner_modeling_table.parquet").copy()
    new = pd.read_parquet(a.new_f02_dir / "winner_modeling_table.parquet").copy()
    if old["fight_id"].astype(str).tolist() != new["fight_id"].astype(str).tolist():
        raise RuntimeError("old/corrected F02 fight population or ordering changed")
    old["event_date"] = pd.to_datetime(old["event_date"], errors="raise")
    new["event_date"] = pd.to_datetime(new["event_date"], errors="raise")

    old_oof = pd.read_parquet(a.old_m1_dir / "m1_oof_predictions.parquet").copy()
    new_oof = pd.read_parquet(a.new_m1_dir / "m1_oof_predictions.parquet").copy()
    if old_oof["fight_id"].astype(str).tolist() != new_oof["fight_id"].astype(str).tolist():
        raise RuntimeError("old/corrected M1 OOF population or ordering changed")
    if not np.array_equal(old_oof["target"].astype(int).to_numpy(), new_oof["target"].astype(int).to_numpy()):
        raise RuntimeError("old/corrected M1 OOF labels changed")

    oof_ids = new_oof["fight_id"].astype(str).tolist()
    old_idx = old.assign(_fid=old["fight_id"].astype(str)).set_index("_fid", drop=False)
    new_idx = new.assign(_fid=new["fight_id"].astype(str)).set_index("_fid", drop=False)
    old_eval = old_idx.loc[oof_ids].reset_index(drop=True)
    new_eval = new_idx.loc[oof_ids].reset_index(drop=True)
    if not np.array_equal(new_eval["fighter_1_win"].astype(int).to_numpy(), new_oof["target"].astype(int).to_numpy()):
        raise RuntimeError("F02/M1 OOF target mapping mismatch")

    surface = load_json(a.feature_surface)
    catalog = load_json(a.feature_catalog)
    catalog_by_name = {x["feature_name"]: x for x in catalog.get("features", [])}
    old_coef = coefficient_stats(a.old_m1_dir / "m1_coefficients.json")
    new_coef = coefficient_stats(a.new_m1_dir / "m1_coefficients.json")

    fold0 = load_json(a.new_m1_dir / "m1_coefficients.json")[0]["coefficients"]
    missing_meta = [r for r in fold0 if r.get("is_missingness") is True]
    if len(missing_meta) != 98:
        raise RuntimeError(f"expected 98 M1 missingness dimensions, got {len(missing_meta)}")

    career_lookup = build_career_lookup(new)
    inventory: list[dict[str, Any]] = []

    for meta in missing_meta:
        feature = meta["feature"]
        cols = source_columns(feature)
        if cols is None or any(c not in new_eval.columns for c in cols):
            raise RuntimeError(f"cannot trace raw columns for {feature}: {cols}")
        old_state = feature_state(old_eval, feature)
        new_state = feature_state(new_eval, feature)
        old_metrics = state_target_metrics(old_eval, old_state, mode="availability")
        new_metrics = state_target_metrics(new_eval, new_state, mode="availability")

        # Use the population with more active rows for leakage detection so a correction
        # that already removed the bad missingness cannot hide its historical behavior.
        if old_metrics["active_rows"] >= new_metrics["active_rows"]:
            basis_frame, basis_state, basis_name, basis_metrics = old_eval, old_state, "old_f02", old_metrics
        else:
            basis_frame, basis_state, basis_name, basis_metrics = new_eval, new_state, "corrected_f02", new_metrics
        career = career_comparison(basis_frame, basis_state, career_lookup, mode="availability")
        cmeta = concept_meta(catalog_by_name, str(meta["source_concept"]))
        row: dict[str, Any] = {
            "feature": feature,
            "family": meta["family"],
            "source_concept": meta["source_concept"],
            "role": meta["role"],
            "type": "derived missingness difference",
            "raw_columns": list(cols),
            "old_oof": old_metrics,
            "corrected_oof": new_metrics,
            "diagnostic_basis_name": basis_name,
            "diagnostic_basis": basis_metrics,
            "career": career,
            "old_coefficient": old_coef.get(feature, {}),
            "corrected_coefficient": new_coef.get(feature, {}),
            "source_contract": cmeta,
            "completed_value_test": completed_value_test(old_eval, new_eval, feature),
        }
        classification, reasons = classify(row)
        row["classification"] = classification
        row["classification_reasons"] = reasons
        inventory.append(row)

    # Explicit support/sample-count negative control. This is a modeled value dimension,
    # not a missingness channel, but is in audit scope because support counts were requested.
    support_meta = next((r for r in fold0 if r["feature"] == PRIOR_COUNT_VALUE), None)
    if support_meta is None:
        raise RuntimeError("prior_fight_count negative-control value dimension missing from M1")
    s_state = support_state(new_eval)
    s_metrics = state_target_metrics(new_eval, s_state, mode="higher_support")
    s_career = career_comparison(new_eval, s_state, career_lookup, mode="higher_support")
    s_row: dict[str, Any] = {
        "feature": PRIOR_COUNT_VALUE,
        "family": support_meta["family"],
        "source_concept": support_meta["source_concept"],
        "role": support_meta["role"],
        "type": "support/sample count",
        "raw_columns": ["f1__fs__prior_fight_count__career__raw", "f2__fs__prior_fight_count__career__raw"],
        "old_oof": None,
        "corrected_oof": s_metrics,
        "diagnostic_basis_name": "corrected_f02",
        "diagnostic_basis": s_metrics,
        "career": s_career,
        "old_coefficient": old_coef.get(PRIOR_COUNT_VALUE, {}),
        "corrected_coefficient": new_coef.get(PRIOR_COUNT_VALUE, {}),
        "source_contract": concept_meta(catalog_by_name, "prior_fight_count"),
        "completed_value_test": {"rows_filled": 0},
    }
    s_row["classification"], s_row["classification_reasons"] = classify(s_row)
    inventory.append(s_row)

    # Positive-control exact subset: 2015-2018 rows where old reach had exactly one side
    # missing and corrected replay filled it.
    reach_cols = source_columns(REACH_MISSING)
    assert reach_cols is not None
    reach_old_state = feature_state(old_eval, REACH_MISSING)
    rn1 = pd.to_numeric(new_eval[reach_cols[0]], errors="coerce")
    rn2 = pd.to_numeric(new_eval[reach_cols[1]], errors="coerce")
    yrs = old_eval["event_date"].dt.year.to_numpy()
    reach_mask = (yrs >= 2015) & (yrs <= 2018) & (reach_old_state != 0) & rn1.notna().to_numpy() & rn2.notna().to_numpy()
    reach_pc_frame = old_eval.loc[reach_mask].reset_index(drop=True)
    reach_pc_state = reach_old_state[reach_mask]
    reach_target = state_target_metrics(reach_pc_frame, reach_pc_state, mode="availability")
    reach_career = career_comparison(reach_pc_frame, reach_pc_state, career_lookup, mode="availability")
    avail_side = np.where(reach_pc_state < 0, 1, 2)
    av = np.where(avail_side == 1, rn1.to_numpy()[reach_mask], rn2.to_numpy()[reach_mask])
    ot = np.where(avail_side == 1, rn2.to_numpy()[reach_mask], rn1.to_numpy()[reach_mask])
    positive_control = {
        "feature": REACH_MISSING,
        "rows": int(reach_mask.sum()),
        "available_side_win_rate": reach_target["favored_side_win_rate"],
        "available_side_larger_true_reach_rate": float((av > ot).mean()) if len(av) else None,
        "mean_true_reach_advantage_cm": float(np.mean(av - ot)) if len(av) else None,
        "future_career": reach_career,
        "reproduced": bool(
            int(reach_mask.sum()) == 111
            and reach_target["favored_side_win_rate"] is not None
            and abs(float(reach_target["favored_side_win_rate"]) - 0.9459459459459459) < 1e-12
        ),
    }
    if not positive_control["reproduced"]:
        raise RuntimeError(f"reach positive control did not reproduce: {positive_control}")

    negative_control = {
        "feature": PRIOR_COUNT_VALUE,
        "classification": s_row["classification"],
        "strict_prior_contract": s_row["source_contract"]["strict_prior_contract"],
        "active_rows": s_metrics["active_rows"],
        "higher_prior_count_side_win_rate": s_metrics["favored_side_win_rate"],
        "career": s_career,
    }

    # Classification summary.
    counts: dict[str, int] = {}
    for r in inventory:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    confirmed = [r["feature"] for r in inventory if r["classification"] == "CONFIRMED_TEMPORAL_LEAKAGE"]
    potential = [r["feature"] for r in inventory if r["classification"] == "POTENTIAL_TEMPORAL_LEAKAGE"]
    safe = [r["feature"] for r in inventory if r["classification"] == "POINT_IN_TIME_SAFE"]

    missing_confirmed = [f for f in confirmed if f != PRIOR_COUNT_VALUE]
    if not missing_confirmed:
        verdict = "M1_MISSINGNESS_AUDIT_INCONCLUSIVE"
        recommendation = "AUDIT_MUST_BE_REBUILT"
    elif missing_confirmed == [REACH_MISSING] and not potential:
        verdict = "REACH_MISSINGNESS_WAS_THE_PRIMARY_CONFIRMED_LEAKAGE_SURFACE"
        recommendation = "CORRECTED_M1_READY_FOR_FREEZE"
    elif REACH_MISSING in missing_confirmed and len(missing_confirmed) >= 2:
        verdict = "MULTIPLE_M1_MISSINGNESS_SURFACES_SHOW_CONFIRMED_TEMPORAL_LEAKAGE"
        recommendation = "M1_REQUIRES_TARGETED_LEAKAGE_REPAIR_AND_RERUN"
    else:
        verdict = "M1_MISSINGNESS_AUDIT_INCONCLUSIVE"
        recommendation = "M1_REQUIRES_BROADER_DATA_GOVERNANCE_REPAIR"

    absent = {
        "stance": "not present in frozen M1 feature surface",
        "rankings_history": "not present in frozen M1 feature surface",
        "biography_profile_metadata": "not present beyond modeled age/height/reach context",
        "gym_team_metadata": "not present in frozen M1 feature surface",
        "identity_reconciliation_confidence": "not present in frozen M1 feature surface",
        "source_fallback_indicator": "not present in frozen M1 feature surface",
        "amateur_record_enrichment": "not present in frozen M1 feature surface",
    }

    compact_rows: list[dict[str, Any]] = []
    for r in inventory:
        d = r["diagnostic_basis"]
        c = r["career"]
        cc = r["corrected_coefficient"]
        compact_rows.append({
            "Feature": r["feature"],
            "Family": r["family"],
            "Type": r["type"],
            "Prevalence": d.get("prevalence"),
            "Active Rows": d.get("active_rows"),
            "Mean Coef": cc.get("mean"),
            "Sign Stability": cc.get("sign_stability"),
            "Max Abs Coef": cc.get("max_abs"),
            "Target Separation": None if d.get("favored_side_win_rate") is None else abs(float(d["favored_side_win_rate"]) - 0.5),
            "Favored Side Win Rate": d.get("favored_side_win_rate"),
            "Future More Fights Rate": c.get("favored_more_future_fights_rate"),
            "Prior More Fights Rate": c.get("favored_more_prior_fights_rate"),
            "Future-Prior Rate Gap": c.get("future_minus_prior_more_fights_rate"),
            "Era Pattern": json.dumps(d.get("eras", {}), sort_keys=True),
            "Classification": r["classification"],
            "Diagnostic Basis": r["diagnostic_basis_name"],
        })
    table = pd.DataFrame(compact_rows).sort_values(
        ["Classification", "Target Separation", "Max Abs Coef"],
        ascending=[True, False, False], na_position="last"
    )
    table.to_csv(a.output_dir / "canonical_audit_table.csv", index=False)

    deep_dives = [r for r in inventory if r["classification"] in {"CONFIRMED_TEMPORAL_LEAKAGE", "POTENTIAL_TEMPORAL_LEAKAGE"}]
    (a.output_dir / "feature_inventory.json").write_text(json.dumps(inventory, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    (a.output_dir / "deep_dives.json").write_text(json.dumps(deep_dives, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    source_state = {
        "old_f02_predictor_logical_sha256": load_json(a.old_f02_dir / "summary.json").get("predictor_logical_sha256"),
        "corrected_f02_predictor_logical_sha256": load_json(a.new_f02_dir / "summary.json").get("predictor_logical_sha256"),
        "old_m1_result_sha256": sha256_file(a.old_m1_dir / "m1_result.json"),
        "corrected_m1_result_sha256": sha256_file(a.new_m1_dir / "m1_result.json"),
        "old_m1_coefficients_sha256": sha256_file(a.old_m1_dir / "m1_coefficients.json"),
        "corrected_m1_coefficients_sha256": sha256_file(a.new_m1_dir / "m1_coefficients.json"),
        "feature_surface_sha256": sha256_file(a.feature_surface),
        "feature_catalog_sha256": sha256_file(a.feature_catalog),
        "oof_rows": int(len(new_eval)),
        "fold_ids": sorted({str(x) for x in new_oof["fold_id"].tolist()}),
        "same_oof_population": True,
        "same_oof_labels": True,
    }

    report = {
        "status": "M1_MISSINGNESS_TEMPORAL_LEAKAGE_AUDIT_V1_COMPLETE",
        "guardrails": {
            "data_changed": False,
            "f00_changed": False,
            "f01_changed": False,
            "f02_changed": False,
            "m1_methodology_changed": False,
            "m1_retrained": False,
            "features_removed": False,
            "features_added": False,
            "folds_changed": False,
            "hyperparameter_grid_changed": False,
            "m1b_started": False,
            "market_data_used": False,
            "betting_analysis_performed": False,
            "automatic_merge": False,
        },
        "source_state": source_state,
        "feature_inventory": {
            "total_m1_projected_dimensions": 197,
            "explicit_missingness_dimensions": 98,
            "support_value_dimensions_added_to_audit": 1,
            "total_audited_rows": len(inventory),
            "classification_counts": counts,
            "families": sorted({str(r["family"]) for r in inventory}),
            "absent_requested_families": absent,
        },
        "positive_control": positive_control,
        "negative_control": negative_control,
        "confirmed_leakage_features": confirmed,
        "potential_leakage_features": potential,
        "point_in_time_safe_features": safe,
        "verdict": verdict,
        "next_step_recommendation": recommendation,
    }
    (a.output_dir / "audit_report.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    # Human-readable report.
    lines: list[str] = [
        "# M1 Missingness Temporal Leakage Audit V1",
        "",
        "`M1_MISSINGNESS_TEMPORAL_LEAKAGE_AUDIT_V1_COMPLETE`",
        "",
        "## Scope and guardrails",
        "",
        "Read-only audit of the frozen M1 surface. No DATA/F00/F01/F02 edits, no retraining, no feature changes, no fold/grid changes, no market/betting inputs.",
        "",
        "## Feature inventory",
        "",
        f"- M1 projected dimensions: **197**",
        f"- Explicit missingness dimensions: **98**",
        f"- Additional support/sample-count negative-control dimension: **1**",
        f"- Total audited dimensions: **{len(inventory)}**",
        f"- Classification counts: `{json.dumps(counts, sort_keys=True)}`",
        "",
        "## Reach positive control",
        "",
        f"- Exact correction-specific 2015-2018 rows: **{positive_control['rows']}**",
        f"- Reach-known side win rate: **{100*float(positive_control['available_side_win_rate']):.1f}%**",
        f"- Reach-known side actually longer: **{100*float(positive_control['available_side_larger_true_reach_rate']):.1f}%**",
        f"- Mean true reach advantage: **{float(positive_control['mean_true_reach_advantage_cm']):.3f} cm**",
        f"- More future UFC fights: **{100*float(positive_control['future_career']['favored_more_future_fights_rate']):.1f}%**",
        f"- More prior UFC fights: **{100*float(positive_control['future_career']['favored_more_prior_fights_rate']):.1f}%**",
        f"- Reproduced: **{positive_control['reproduced']}**",
        "",
        "## Negative control",
        "",
        f"- Feature: `{PRIOR_COUNT_VALUE}`",
        f"- Classification: **{negative_control['classification']}**",
        f"- Strict-prior contract: **{negative_control['strict_prior_contract']}**",
        f"- Higher-prior-count side win rate: **{100*float(negative_control['higher_prior_count_side_win_rate']):.1f}%**",
        "",
        "## Confirmed temporal leakage",
        "",
    ]
    if confirmed:
        lines += [f"- `{x}`" for x in confirmed]
    else:
        lines.append("- None")
    lines += ["", "## Potential temporal leakage", ""]
    if potential:
        lines += [f"- `{x}`" for x in potential]
    else:
        lines.append("- None")
    lines += ["", "## Deep dives", ""]
    for r in deep_dives:
        d = r["diagnostic_basis"]; c = r["career"]; cv = r["completed_value_test"]
        lines += [
            f"### `{r['feature']}`",
            "",
            f"- Classification: **{r['classification']}**",
            f"- Basis: `{r['diagnostic_basis_name']}`; active rows **{d.get('active_rows', 0)}**; prevalence **{100*float(d.get('prevalence') or 0):.2f}%**",
            f"- Availability-side win rate: **{'n/a' if d.get('favored_side_win_rate') is None else f'{100*float(d[\"favored_side_win_rate\"]):.1f}%'}**",
            f"- More future fights: **{'n/a' if c.get('favored_more_future_fights_rate') is None else f'{100*float(c[\"favored_more_future_fights_rate\"]):.1f}%'}**",
            f"- More prior fights: **{'n/a' if c.get('favored_more_prior_fights_rate') is None else f'{100*float(c[\"favored_more_prior_fights_rate\"]):.1f}%'}**",
            f"- Mean future fight delta: **{c.get('mean_delta_future_fights', 'n/a')}**; mean prior fight delta: **{c.get('mean_delta_prior_fights', 'n/a')}**",
            f"- Corrected mean coefficient: **{r['corrected_coefficient'].get('mean', 'n/a')}**; sign stability: **{r['corrected_coefficient'].get('sign_stability', 'n/a')}**",
            f"- Completed-value rows available for direct value-vs-availability check: **{cv.get('rows_filled', 0)}**",
            f"- Source time scope: `{r['source_contract'].get('input_time_scope')}`; strict-prior contract: **{r['source_contract'].get('strict_prior_contract')}**",
            f"- Reasons: {'; '.join(r['classification_reasons'])}",
            "",
        ]
    lines += [
        "## Requested-but-absent surfaces",
        "",
    ] + [f"- `{k}`: {v}" for k, v in absent.items()]
    lines += [
        "",
        "## Final verdict",
        "",
        f"`{verdict}`",
        "",
        "## Next-step recommendation",
        "",
        f"`{recommendation}`",
        "",
        "This diagnostic does not perform or authorize repair.",
    ]
    (a.output_dir / "audit_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Artifact hashes over generated evidence.
    hash_rows = []
    for path in sorted(a.output_dir.iterdir()):
        if path.is_file() and path.name != "artifact_hashes.json":
            hash_rows.append({"file": path.name, "sha256": sha256_file(path)})
    (a.output_dir / "artifact_hashes.json").write_text(json.dumps(hash_rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("M1_MISSINGNESS_TEMPORAL_LEAKAGE_AUDIT_V1_COMPLETE")
    print(json.dumps({
        "confirmed": confirmed,
        "potential": potential,
        "safe_count": len(safe),
        "verdict": verdict,
        "recommendation": recommendation,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
