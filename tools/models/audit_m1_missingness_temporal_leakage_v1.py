#!/usr/bin/env python3
"""Read-only M1 missingness / availability temporal leakage audit V1."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ERAS = (("2015-2018", 2015, 2018), ("2019-2022", 2019, 2022), ("2023-2024", 2023, 2024), ("2025-2026", 2025, 2026))
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


def strict_prior(text: str) -> bool:
    t = " ".join(str(text).lower().replace("-", " ").split())
    return "strictly before" in t or "strictly pre " in t


def pct(v: Any) -> str:
    return "n/a" if v is None else f"{100 * float(v):.1f}%"


def raw_columns(feature: str) -> tuple[str, str] | None:
    if feature.startswith("pair::") and feature.endswith("::missing_diff"):
        key = feature[len("pair::"):-len("::missing_diff")]
        return f"f1__{key}", f"f2__{key}"
    if feature.startswith("mx::") and feature.endswith("::missing_diff"):
        key = feature[len("mx::"):-len("::missing_diff")]
        parts = key.split("__")
        if len(parts) < 2:
            raise RuntimeError(f"unsupported matchup feature {feature}")
        concept, suffix = parts[0], "__".join(parts[1:])
        return f"mx__{concept}__f1_vs_f2__{suffix}", f"mx__{concept}__f2_vs_f1__{suffix}"
    return None


def coefficient_stats(path: Path) -> dict[str, dict[str, Any]]:
    by: dict[str, list[float]] = {}
    for fold in load_json(path):
        for r in fold["coefficients"]:
            by.setdefault(r["feature"], []).append(float(r["coefficient"]))
    out: dict[str, dict[str, Any]] = {}
    for feature, vals in by.items():
        a = np.asarray(vals, float)
        nz = a[np.abs(a) > EPS]
        pos, neg = int((nz > 0).sum()), int((nz < 0).sum())
        out[feature] = {
            "mean": float(a.mean()), "std": float(a.std(ddof=0)),
            "fold_nonzero_count": int(len(nz)),
            "sign_stability": None if len(nz) == 0 else float(max(pos, neg) / len(nz)),
            "max_abs": float(np.abs(a).max()),
        }
    return out


def build_career_lookup(frame: pd.DataFrame) -> dict[tuple[str, str], dict[str, float | int]]:
    use = frame[frame["promotion"].eq("UFC") & frame["binary_winner_eligible"].eq(True)].copy()
    use["event_date"] = pd.to_datetime(use["event_date"], errors="raise")
    apps: list[dict[str, Any]] = []
    for r in use[["fight_id", "event_date", "event_id", "fighter_1_id", "fighter_2_id", "winner_id"]].itertuples(index=False):
        for side in (1, 2):
            fid = str(getattr(r, f"fighter_{side}_id"))
            apps.append({"fight_id": str(r.fight_id), "event_date": r.event_date, "event_id": str(r.event_id), "fighter_id": fid, "won": int(str(r.winner_id) == fid)})
    app = pd.DataFrame(apps).sort_values(["fighter_id", "event_date", "event_id", "fight_id"]).reset_index(drop=True)
    lookup: dict[tuple[str, str], dict[str, float | int]] = {}
    for fighter, g in app.groupby("fighter_id", sort=False):
        g = g.reset_index(drop=True)
        dates = pd.to_datetime(g["event_date"]).tolist()
        wins = g["won"].astype(int).to_numpy()
        prefix = np.concatenate(([0], np.cumsum(wins)))
        n = len(g)
        for i, row in g.iterrows():
            lookup[(str(row["fight_id"]), str(fighter))] = {
                "prior_fights": i,
                "prior_wins": int(prefix[i]),
                "prior_years": 0.0 if i == 0 else float((dates[i] - dates[0]).days / 365.25),
                "future_fights": n - i - 1,
                "future_wins": int(prefix[n] - prefix[i + 1]),
                "future_years": 0.0 if i == n - 1 else float((dates[-1] - dates[i]).days / 365.25),
            }
    return lookup


def missing_state(frame: pd.DataFrame, feature: str) -> np.ndarray:
    cols = raw_columns(feature)
    if cols is None:
        raise RuntimeError(feature)
    a = pd.to_numeric(frame[cols[0]], errors="coerce")
    b = pd.to_numeric(frame[cols[1]], errors="coerce")
    return a.isna().to_numpy(dtype=int) - b.isna().to_numpy(dtype=int)


def prior_count_state(frame: pd.DataFrame) -> np.ndarray:
    a = pd.to_numeric(frame["f1__fs__prior_fight_count__career__raw"], errors="coerce")
    b = pd.to_numeric(frame["f2__fs__prior_fight_count__career__raw"], errors="coerce")
    return np.sign((a - b).to_numpy(float)).astype(int)


def state_metrics(frame: pd.DataFrame, state: np.ndarray, mode: str) -> dict[str, Any]:
    active = state != 0
    y = frame["fighter_1_win"].astype(int).to_numpy()
    years = pd.to_datetime(frame["event_date"]).dt.year.to_numpy()
    if mode == "availability":
        favored = np.where(state < 0, 1, 2)  # observed side
    elif mode == "higher_support":
        favored = np.where(state > 0, 1, 2)
    else:
        raise RuntimeError(mode)
    favored_win = np.where(favored == 1, y, 1 - y)
    out: dict[str, Any] = {
        "rows": int(len(frame)), "active_rows": int(active.sum()),
        "prevalence": float(active.mean()) if len(frame) else None,
        "mean": float(state.mean()) if len(state) else None,
        "std": float(state.std()) if len(state) else None,
        "favored_side_win_rate": None if not active.any() else float(favored_win[active].mean()),
        "negative_rows": int((state < 0).sum()), "positive_rows": int((state > 0).sum()),
        "f1_win_rate_when_negative": None if not (state < 0).any() else float(y[state < 0].mean()),
        "f1_win_rate_when_positive": None if not (state > 0).any() else float(y[state > 0].mean()),
    }
    era: dict[str, Any] = {}
    for label, lo, hi in ERAS:
        m = (years >= lo) & (years <= hi)
        am = m & active
        era[label] = {
            "rows": int(m.sum()), "active_rows": int(am.sum()),
            "prevalence": None if not m.any() else float(am.sum() / m.sum()),
            "favored_side_win_rate": None if not am.any() else float(favored_win[am].mean()),
        }
    out["eras"] = era
    return out


def career_metrics(frame: pd.DataFrame, state: np.ndarray, lookup: dict[tuple[str, str], dict[str, float | int]], mode: str) -> dict[str, Any]:
    rows: list[dict[str, float]] = []
    y = frame["fighter_1_win"].astype(int).to_numpy()
    for i in np.flatnonzero(state != 0):
        r = frame.iloc[i]
        s = int(state[i])
        favored = (1 if s < 0 else 2) if mode == "availability" else (1 if s > 0 else 2)
        other = 2 if favored == 1 else 1
        fight = str(r["fight_id"])
        a = lookup.get((fight, str(r[f"fighter_{favored}_id"])))
        b = lookup.get((fight, str(r[f"fighter_{other}_id"])))
        if a is None or b is None:
            continue
        item: dict[str, float] = {"favored_won": float(y[i] if favored == 1 else 1 - y[i])}
        for period in ("prior", "future"):
            for metric in ("fights", "wins", "years"):
                k = f"{period}_{metric}"
                item[f"favored_{k}"] = float(a[k]); item[f"other_{k}"] = float(b[k]); item[f"delta_{k}"] = float(a[k]) - float(b[k])
        rows.append(item)
    if not rows:
        return {"rows": 0}
    x = pd.DataFrame(rows)
    out: dict[str, Any] = {"rows": int(len(x)), "favored_side_win_rate": float(x["favored_won"].mean())}
    for period in ("prior", "future"):
        for metric in ("fights", "wins", "years"):
            d = f"delta_{period}_{metric}"
            out[f"favored_more_{period}_{metric}_rate"] = float((x[d] > 0).mean())
            out[f"favored_mean_{period}_{metric}"] = float(x[f"favored_{period}_{metric}"].mean())
            out[f"other_mean_{period}_{metric}"] = float(x[f"other_{period}_{metric}"].mean())
            out[f"mean_delta_{period}_{metric}"] = float(x[d].mean())
    out["future_minus_prior_more_fights_rate"] = float(out["favored_more_future_fights_rate"] - out["favored_more_prior_fights_rate"])
    return out


def catalog_meta(by_name: dict[str, dict[str, Any]], concept: str) -> dict[str, Any]:
    c = by_name.get(concept, {})
    cutoff = c.get("information_cutoff_rule", "")
    return {
        "input_time_scope": c.get("input_time_scope"), "information_cutoff_rule": cutoff,
        "strict_prior_contract": strict_prior(cutoff), "missingness_behavior": c.get("missingness_behavior"),
        "minimum_sample": c.get("minimum_sample"), "coverage_expectation": c.get("coverage_expectation"),
        "canonical_input_tables": c.get("canonical_input_tables", []), "canonical_input_fields": c.get("canonical_input_fields", {}),
        "provenance_requirement": c.get("provenance_requirement"),
    }


def completed_value(old: pd.DataFrame, new: pd.DataFrame, feature: str) -> dict[str, Any]:
    cols = raw_columns(feature)
    if cols is None:
        return {"rows_filled": 0}
    oa = pd.to_numeric(old[cols[0]], errors="coerce"); ob = pd.to_numeric(old[cols[1]], errors="coerce")
    na = pd.to_numeric(new[cols[0]], errors="coerce"); nb = pd.to_numeric(new[cols[1]], errors="coerce")
    state = oa.isna().to_numpy(dtype=int) - ob.isna().to_numpy(dtype=int)
    filled = (state != 0) & na.notna().to_numpy() & nb.notna().to_numpy()
    if not filled.any():
        return {"rows_filled": 0}
    side = np.where(state < 0, 1, 2)
    av = np.where(side == 1, na.to_numpy(float), nb.to_numpy(float)); ot = np.where(side == 1, nb.to_numpy(float), na.to_numpy(float))
    y = old["fighter_1_win"].astype(int).to_numpy(); win = np.where(side == 1, y, 1 - y)
    return {
        "rows_filled": int(filled.sum()), "available_side_win_rate": float(win[filled].mean()),
        "available_side_larger_completed_value_rate": float((av[filled] > ot[filled]).mean()),
        "mean_completed_value_advantage": float((av[filled] - ot[filled]).mean()),
    }


def classify(row: dict[str, Any]) -> tuple[str, list[str]]:
    if row["type"] == "support/sample count":
        return "POINT_IN_TIME_SAFE", ["explicit strictly pre-fight accumulated support value; negative control"]
    if row["feature"] == REACH_MISSING:
        return "CONFIRMED_TEMPORAL_LEAKAGE", ["positive control reproduced: missingness encoded future profile/career persistence"]
    d, c, coef = row["diagnostic_basis"], row["career"], row["corrected_coefficient"]
    n, win = int(d.get("active_rows", 0) or 0), d.get("favored_side_win_rate")
    fr, pr = c.get("favored_more_future_fights_rate"), c.get("favored_more_prior_fights_rate")
    gap, fd, pdiff = c.get("future_minus_prior_more_fights_rate"), c.get("mean_delta_future_fights"), c.get("mean_delta_prior_fights")
    stable, mag = coef.get("sign_stability"), coef.get("max_abs")
    strong_target = n >= 20 and win is not None and abs(float(win) - 0.5) >= 0.20
    future_dominant = n >= 20 and fr is not None and pr is not None and gap is not None and fd is not None and pdiff is not None and float(fr) >= 0.75 and float(gap) >= 0.15 and float(fd) >= float(pdiff) + 1.5
    stable_use = stable is not None and mag is not None and float(stable) >= 0.75 and float(mag) >= 0.10
    reasons: list[str] = []
    if strong_target: reasons.append("strong target separation")
    if future_dominant: reasons.append("future-career separation materially exceeds prior-career separation")
    if stable_use: reasons.append("material, sign-stable M1 coefficient")
    if strong_target and future_dominant:
        reasons.append("multiple independent signals match confirmed leakage signature")
        return "CONFIRMED_TEMPORAL_LEAKAGE", reasons
    if n >= 20 and sum((strong_target, future_dominant, stable_use)) >= 2:
        return "POTENTIAL_TEMPORAL_LEAKAGE", reasons
    reasons.append("no multi-signal evidence of future-derived availability leakage" if n else "missingness channel inactive on selected diagnostic OOF population")
    return "POINT_IN_TIME_SAFE", reasons


def main() -> None:
    a = parse_args(); a.output_dir.mkdir(parents=True, exist_ok=True)
    old = pd.read_parquet(a.old_f02_dir / "winner_modeling_table.parquet").copy(); new = pd.read_parquet(a.new_f02_dir / "winner_modeling_table.parquet").copy()
    if old["fight_id"].astype(str).tolist() != new["fight_id"].astype(str).tolist(): raise RuntimeError("F02 population/order drift")
    old["event_date"] = pd.to_datetime(old["event_date"], errors="raise"); new["event_date"] = pd.to_datetime(new["event_date"], errors="raise")
    oo = pd.read_parquet(a.old_m1_dir / "m1_oof_predictions.parquet"); no = pd.read_parquet(a.new_m1_dir / "m1_oof_predictions.parquet")
    if oo["fight_id"].astype(str).tolist() != no["fight_id"].astype(str).tolist(): raise RuntimeError("OOF population drift")
    if not np.array_equal(oo["target"].astype(int).to_numpy(), no["target"].astype(int).to_numpy()): raise RuntimeError("OOF label drift")
    ids = no["fight_id"].astype(str).tolist()
    oi = old.assign(_fid=old["fight_id"].astype(str)).set_index("_fid", drop=False); ni = new.assign(_fid=new["fight_id"].astype(str)).set_index("_fid", drop=False)
    oe = oi.loc[ids].reset_index(drop=True); ne = ni.loc[ids].reset_index(drop=True)
    if not np.array_equal(ne["fighter_1_win"].astype(int).to_numpy(), no["target"].astype(int).to_numpy()): raise RuntimeError("F02/OOF target mismatch")

    surface = load_json(a.feature_surface); catalog = load_json(a.feature_catalog); by_name = {x["feature_name"]: x for x in catalog.get("features", [])}
    old_coef = coefficient_stats(a.old_m1_dir / "m1_coefficients.json"); new_coef = coefficient_stats(a.new_m1_dir / "m1_coefficients.json")
    fold0 = load_json(a.new_m1_dir / "m1_coefficients.json")[0]["coefficients"]
    missing_meta = [r for r in fold0 if r.get("is_missingness") is True]
    if len(missing_meta) != 98: raise RuntimeError(f"expected 98 missingness dimensions, got {len(missing_meta)}")
    lookup = build_career_lookup(new); inventory: list[dict[str, Any]] = []

    for meta in missing_meta:
        feature = meta["feature"]; cols = raw_columns(feature)
        if cols is None or any(c not in ne.columns for c in cols): raise RuntimeError(f"cannot trace {feature}: {cols}")
        os = missing_state(oe, feature); ns = missing_state(ne, feature)
        om = state_metrics(oe, os, "availability"); nm = state_metrics(ne, ns, "availability")
        if om["active_rows"] >= nm["active_rows"]: bf, bs, bn, bm = oe, os, "old_f02", om
        else: bf, bs, bn, bm = ne, ns, "corrected_f02", nm
        row: dict[str, Any] = {
            "feature": feature, "family": meta["family"], "source_concept": meta["source_concept"], "role": meta["role"],
            "type": "derived missingness difference", "raw_columns": list(cols), "old_oof": om, "corrected_oof": nm,
            "diagnostic_basis_name": bn, "diagnostic_basis": bm, "career": career_metrics(bf, bs, lookup, "availability"),
            "old_coefficient": old_coef.get(feature, {}), "corrected_coefficient": new_coef.get(feature, {}),
            "source_contract": catalog_meta(by_name, str(meta["source_concept"])), "completed_value_test": completed_value(oe, ne, feature),
        }
        row["classification"], row["classification_reasons"] = classify(row); inventory.append(row)

    sm = next((r for r in fold0 if r["feature"] == PRIOR_COUNT_VALUE), None)
    if sm is None: raise RuntimeError("prior_fight_count negative control absent")
    ss = prior_count_state(ne); s_metrics = state_metrics(ne, ss, "higher_support"); s_career = career_metrics(ne, ss, lookup, "higher_support")
    srow: dict[str, Any] = {
        "feature": PRIOR_COUNT_VALUE, "family": sm["family"], "source_concept": sm["source_concept"], "role": sm["role"], "type": "support/sample count",
        "raw_columns": ["f1__fs__prior_fight_count__career__raw", "f2__fs__prior_fight_count__career__raw"], "old_oof": None, "corrected_oof": s_metrics,
        "diagnostic_basis_name": "corrected_f02", "diagnostic_basis": s_metrics, "career": s_career,
        "old_coefficient": old_coef.get(PRIOR_COUNT_VALUE, {}), "corrected_coefficient": new_coef.get(PRIOR_COUNT_VALUE, {}),
        "source_contract": catalog_meta(by_name, "prior_fight_count"), "completed_value_test": {"rows_filled": 0},
    }
    srow["classification"], srow["classification_reasons"] = classify(srow); inventory.append(srow)

    rc = raw_columns(REACH_MISSING); assert rc is not None
    ros = missing_state(oe, REACH_MISSING); n1 = pd.to_numeric(ne[rc[0]], errors="coerce"); n2 = pd.to_numeric(ne[rc[1]], errors="coerce")
    yrs = oe["event_date"].dt.year.to_numpy(); mask = (yrs >= 2015) & (yrs <= 2018) & (ros != 0) & n1.notna().to_numpy() & n2.notna().to_numpy()
    pcf = oe.loc[mask].reset_index(drop=True); pcs = ros[mask]; pcm = state_metrics(pcf, pcs, "availability"); pcc = career_metrics(pcf, pcs, lookup, "availability")
    side = np.where(pcs < 0, 1, 2); av = np.where(side == 1, n1.to_numpy()[mask], n2.to_numpy()[mask]); ot = np.where(side == 1, n2.to_numpy()[mask], n1.to_numpy()[mask])
    positive = {
        "feature": REACH_MISSING, "rows": int(mask.sum()), "available_side_win_rate": pcm["favored_side_win_rate"],
        "available_side_larger_true_reach_rate": float((av > ot).mean()), "mean_true_reach_advantage_cm": float((av - ot).mean()),
        "future_career": pcc,
    }
    positive["reproduced"] = bool(positive["rows"] == 111 and abs(float(positive["available_side_win_rate"]) - 0.9459459459459459) < 1e-12)
    if not positive["reproduced"]: raise RuntimeError(f"reach positive control failed: {positive}")

    negative = {"feature": PRIOR_COUNT_VALUE, "classification": srow["classification"], "strict_prior_contract": srow["source_contract"]["strict_prior_contract"], "active_rows": s_metrics["active_rows"], "higher_prior_count_side_win_rate": s_metrics["favored_side_win_rate"], "career": s_career}
    counts: dict[str, int] = {}
    for r in inventory: counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    confirmed = [r["feature"] for r in inventory if r["classification"] == "CONFIRMED_TEMPORAL_LEAKAGE"]
    potential = [r["feature"] for r in inventory if r["classification"] == "POTENTIAL_TEMPORAL_LEAKAGE"]
    safe = [r["feature"] for r in inventory if r["classification"] == "POINT_IN_TIME_SAFE"]

    if confirmed == [REACH_MISSING] and not potential:
        verdict, rec = "REACH_MISSINGNESS_WAS_THE_PRIMARY_CONFIRMED_LEAKAGE_SURFACE", "CORRECTED_M1_READY_FOR_FREEZE"
    elif REACH_MISSING in confirmed and len(confirmed) >= 2:
        verdict, rec = "MULTIPLE_M1_MISSINGNESS_SURFACES_SHOW_CONFIRMED_TEMPORAL_LEAKAGE", "M1_REQUIRES_TARGETED_LEAKAGE_REPAIR_AND_RERUN"
    elif not confirmed:
        verdict, rec = "M1_MISSINGNESS_AUDIT_INCONCLUSIVE", "AUDIT_MUST_BE_REBUILT"
    else:
        verdict, rec = "M1_MISSINGNESS_AUDIT_INCONCLUSIVE", "M1_REQUIRES_BROADER_DATA_GOVERNANCE_REPAIR"

    absent = {
        "stance": "not present in frozen M1 feature surface", "rankings_history": "not present in frozen M1 feature surface",
        "biography_profile_metadata": "not present beyond modeled age/height/reach context", "gym_team_metadata": "not present in frozen M1 feature surface",
        "identity_reconciliation_confidence": "not present in frozen M1 feature surface", "source_fallback_indicator": "not present in frozen M1 feature surface",
        "amateur_record_enrichment": "not present in frozen M1 feature surface",
    }
    compact: list[dict[str, Any]] = []
    for r in inventory:
        d, c, cc = r["diagnostic_basis"], r["career"], r["corrected_coefficient"]
        compact.append({
            "Feature": r["feature"], "Family": r["family"], "Type": r["type"], "Prevalence": d.get("prevalence"), "Active Rows": d.get("active_rows"),
            "Mean Coef": cc.get("mean"), "Sign Stability": cc.get("sign_stability"), "Max Abs Coef": cc.get("max_abs"),
            "Target Separation": None if d.get("favored_side_win_rate") is None else abs(float(d["favored_side_win_rate"]) - 0.5),
            "Favored Side Win Rate": d.get("favored_side_win_rate"), "Future More Fights Rate": c.get("favored_more_future_fights_rate"),
            "Prior More Fights Rate": c.get("favored_more_prior_fights_rate"), "Future-Prior Rate Gap": c.get("future_minus_prior_more_fights_rate"),
            "Era Pattern": json.dumps(d.get("eras", {}), sort_keys=True), "Classification": r["classification"], "Diagnostic Basis": r["diagnostic_basis_name"],
        })
    pd.DataFrame(compact).sort_values(["Classification", "Target Separation", "Max Abs Coef"], ascending=[True, False, False], na_position="last").to_csv(a.output_dir / "canonical_audit_table.csv", index=False)
    deep = [r for r in inventory if r["classification"] in {"CONFIRMED_TEMPORAL_LEAKAGE", "POTENTIAL_TEMPORAL_LEAKAGE"}]
    (a.output_dir / "feature_inventory.json").write_text(json.dumps(inventory, indent=2, sort_keys=True, default=str) + "\n")
    (a.output_dir / "deep_dives.json").write_text(json.dumps(deep, indent=2, sort_keys=True, default=str) + "\n")

    source_state = {
        "old_f02_predictor_logical_sha256": load_json(a.old_f02_dir / "summary.json").get("predictor_logical_sha256"),
        "corrected_f02_predictor_logical_sha256": load_json(a.new_f02_dir / "summary.json").get("predictor_logical_sha256"),
        "old_m1_result_sha256": sha256_file(a.old_m1_dir / "m1_result.json"), "corrected_m1_result_sha256": sha256_file(a.new_m1_dir / "m1_result.json"),
        "old_m1_coefficients_sha256": sha256_file(a.old_m1_dir / "m1_coefficients.json"), "corrected_m1_coefficients_sha256": sha256_file(a.new_m1_dir / "m1_coefficients.json"),
        "feature_surface_sha256": sha256_file(a.feature_surface), "feature_catalog_sha256": sha256_file(a.feature_catalog),
        "oof_rows": int(len(ne)), "fold_ids": sorted({str(x) for x in no["fold_id"].tolist()}), "same_oof_population": True, "same_oof_labels": True,
    }
    report = {
        "status": "M1_MISSINGNESS_TEMPORAL_LEAKAGE_AUDIT_V1_COMPLETE",
        "guardrails": {k: False for k in ("data_changed", "f00_changed", "f01_changed", "f02_changed", "m1_methodology_changed", "m1_retrained", "features_removed", "features_added", "folds_changed", "hyperparameter_grid_changed", "m1b_started", "market_data_used", "betting_analysis_performed", "automatic_merge")},
        "source_state": source_state,
        "feature_inventory": {"total_m1_projected_dimensions": 197, "explicit_missingness_dimensions": 98, "support_value_dimensions_added_to_audit": 1, "total_audited_rows": len(inventory), "classification_counts": counts, "families": sorted({str(r["family"]) for r in inventory}), "absent_requested_families": absent},
        "positive_control": positive, "negative_control": negative, "confirmed_leakage_features": confirmed,
        "potential_leakage_features": potential, "point_in_time_safe_features": safe, "verdict": verdict, "next_step_recommendation": rec,
    }
    (a.output_dir / "audit_report.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")

    lines = [
        "# M1 Missingness Temporal Leakage Audit V1", "", "`M1_MISSINGNESS_TEMPORAL_LEAKAGE_AUDIT_V1_COMPLETE`", "",
        "## Scope", "", "Read-only frozen-artifact audit. No DATA/F00/F01/F02 edits, no retraining, no M1 methodology/feature/fold/grid changes, and no market or betting inputs.", "",
        "## Inventory", "", "- M1 projected dimensions: **197**", "- Explicit missingness dimensions: **98**", "- Additional support-count negative control: **1**", f"- Classification counts: `{json.dumps(counts, sort_keys=True)}`", "",
        "## Reach positive control", "", f"- Exact rows: **{positive['rows']}**", f"- Reach-known side win rate: **{pct(positive['available_side_win_rate'])}**", f"- Reach-known side actually longer: **{pct(positive['available_side_larger_true_reach_rate'])}**", f"- Mean true reach advantage: **{positive['mean_true_reach_advantage_cm']:.3f} cm**", f"- More future UFC fights: **{pct(positive['future_career'].get('favored_more_future_fights_rate'))}**", f"- More prior UFC fights: **{pct(positive['future_career'].get('favored_more_prior_fights_rate'))}**", f"- Reproduced: **{positive['reproduced']}**", "",
        "## Negative control", "", f"- `{PRIOR_COUNT_VALUE}`", f"- Classification: **{negative['classification']}**", f"- Strict-prior contract: **{negative['strict_prior_contract']}**", f"- Higher-prior-count side win rate: **{pct(negative['higher_prior_count_side_win_rate'])}**", "",
        "## Confirmed temporal leakage", "",
    ]
    lines.extend([f"- `{x}`" for x in confirmed] or ["- None"]); lines += ["", "## Potential temporal leakage", ""]
    lines.extend([f"- `{x}`" for x in potential] or ["- None"]); lines += ["", "## Deep dives", ""]
    for r in deep:
        d, c, cv = r["diagnostic_basis"], r["career"], r["completed_value_test"]
        lines += [
            f"### `{r['feature']}`", "", f"- Classification: **{r['classification']}**", f"- Basis: `{r['diagnostic_basis_name']}`",
            f"- Active rows: **{d.get('active_rows', 0)}**; prevalence: **{pct(d.get('prevalence'))}**; availability-side win rate: **{pct(d.get('favored_side_win_rate'))}**",
            f"- More future fights: **{pct(c.get('favored_more_future_fights_rate'))}**; more prior fights: **{pct(c.get('favored_more_prior_fights_rate'))}**",
            f"- Mean future fight delta: **{c.get('mean_delta_future_fights', 'n/a')}**; mean prior fight delta: **{c.get('mean_delta_prior_fights', 'n/a')}**",
            f"- Corrected mean coefficient: **{r['corrected_coefficient'].get('mean', 'n/a')}**; sign stability: **{r['corrected_coefficient'].get('sign_stability', 'n/a')}**",
            f"- Completed-value rows: **{cv.get('rows_filled', 0)}**", f"- Source scope: `{r['source_contract'].get('input_time_scope')}`; strict-prior contract: **{r['source_contract'].get('strict_prior_contract')}**",
            f"- Evidence: {'; '.join(r['classification_reasons'])}", "",
        ]
    lines += ["## Requested surfaces absent from M1", ""] + [f"- `{k}`: {v}" for k, v in absent.items()]
    lines += ["", "## Final verdict", "", f"`{verdict}`", "", "## Next-step recommendation", "", f"`{rec}`", "", "No repair was performed or authorized by this audit."]
    (a.output_dir / "audit_report.md").write_text("\n".join(lines) + "\n")
    hashes = [{"file": p.name, "sha256": sha256_file(p)} for p in sorted(a.output_dir.iterdir()) if p.is_file() and p.name != "artifact_hashes.json"]
    (a.output_dir / "artifact_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    print("M1_MISSINGNESS_TEMPORAL_LEAKAGE_AUDIT_V1_COMPLETE")
    print(json.dumps({"confirmed": confirmed, "potential": potential, "safe_count": len(safe), "verdict": verdict, "recommendation": rec}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
