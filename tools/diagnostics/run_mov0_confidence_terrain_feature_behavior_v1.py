#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from ufc_edge.models.mov0 import (
    FittedSurface,
    build_population,
    fold_frames,
    load_terrain_assignment,
)

STATUS = "MOV0_CONFIDENCE_TERRAIN_FEATURE_BEHAVIOR_DIAGNOSTIC_V1_COMPLETE"
RECOVERY_STATUS = "COEFFICIENT_RECOVERY_VALIDATED"
SOURCE_HEAD = "dd4e7de7de4baa24090388fcf845c996564f2bf8"
WORKFLOW_RUN = 35376956316
ARTIFACT_ID = 10561085362
ARTIFACT_NAME = "mov0-standard-finish-probability-v1"
OOF_SHA = {
    "MOV0_MIN": "786bee7cce8a41eed6a8e7f82fe031a592ed081a10b3a97f85afc31be61d1c57",
    "MOV0_FULL": "9d543356b157fefaabe27f7f4d1b5663536e4cf659fdf11fedd8531c4b13faa0",
    "B1": "6f2f082e276f69a7cac8e527d7a9697f8e5d4b83931717aefc3e8c84e2f127a6",
}
F02_SHA = "d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580"
TERRAIN_COMPRESSED_SHA = "d3358cfc468a791861ee6fb87473f119f949d705c54abfcb504d9ebbecdcb5d2"
TOL = 1e-12
OUTER_YEARS = tuple(range(2018, 2027))
SURFACES = ("B1", "MOV0_MIN", "MOV0_FULL")
BUCKETS = [
    ("<0.30", -np.inf, 0.30),
    ("0.30–<0.40", 0.30, 0.40),
    ("0.40–<0.50", 0.40, 0.50),
    ("0.50–<0.60", 0.50, 0.60),
    ("0.60–<0.70", 0.60, 0.70),
    (">=0.70", 0.70, np.inf),
]
MIGRATION = [
    ("delta_p <= -0.10", -np.inf, -0.10, True, True),
    ("-0.10 < delta_p <= -0.05", -0.10, -0.05, False, True),
    ("-0.05 < delta_p < +0.05", -0.05, 0.05, False, False),
    ("+0.05 <= delta_p < +0.10", 0.05, 0.10, True, False),
    ("delta_p >= +0.10", 0.10, np.inf, True, True),
]
TERRAIN_COLS = (
    "experience_bucket",
    "layoff_bucket",
    "scheduled_duration_bucket",
    "title_status",
    "weight_class",
    "completeness_tier",
    "striking_environment",
    "grappling_environment",
    "joint_mov_environment",
)
WEIGHT_CLASSES = ("Heavyweight", "Light Heavyweight", "Flyweight")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def sample_gate(n: int) -> str:
    if n >= 100:
        return "NORMAL"
    if n >= 50:
        return "MODERATE_UNCERTAINTY"
    if n >= 25:
        return "THIN_EXPLORATORY"
    return "INSUFFICIENT"


def wilson95(k: int, n: int) -> list[float]:
    z = 1.959963984540054
    p = k / n
    den = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / den
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / den
    return [float(center - half), float(center + half)]


def prob_bucket(p: float) -> str:
    for label, lo, hi in BUCKETS:
        if lo <= p < hi:
            return label
    raise AssertionError(p)


def migration_bucket(d: float) -> str:
    for label, lo, hi, incl_lo, incl_hi in MIGRATION:
        left = d >= lo if incl_lo else d > lo
        right = d <= hi if incl_hi else d < hi
        if left and right:
            return label
    raise AssertionError(d)


def metric_bundle(target: pd.Series, probability: pd.Series) -> dict[str, Any]:
    y = target.to_numpy(int)
    p = probability.to_numpy(float)
    safe = np.clip(p, 1e-15, 1 - 1e-15)
    return {
        "N": int(len(y)),
        "finish_prevalence": float(y.mean()),
        "mean_prediction": float(p.mean()),
        "calibration_gap": float(y.mean() - p.mean()),
        "log_loss": float(log_loss(y, safe, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "roc_auc": None if len(np.unique(y)) < 2 else float(roc_auc_score(y, p)),
    }


def model_feature_names(fitted: FittedSurface) -> list[str]:
    pre = fitted.preprocessor
    names = list(pre.numeric_names)
    if "ctx__title_bout" in pre.requested:
        names.append("ctx__title_bout")
    if "ctx__weight_class" in pre.requested:
        names.extend([f"ctx__weight_class=={x}" for x in pre.encoder.categories_[0]])
    if len(names) != fitted.model.coef_.shape[1]:
        raise RuntimeError("model-facing feature-name count mismatch")
    return names


def load_oof(run_dir: Path, surface: str) -> pd.DataFrame:
    path = run_dir / f"oof_{surface}.csv"
    if file_sha256(path) != OOF_SHA[surface]:
        raise RuntimeError(f"{surface} frozen OOF SHA mismatch")
    frame = pd.read_csv(path)
    frame["probability_bucket"] = frame["probability"].astype(float).map(prob_bucket)
    return frame


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--f02-dir", type=Path, required=True)
    ap.add_argument("--mov0-run-dir", type=Path, required=True)
    ap.add_argument("--canonical-fights", type=Path, required=True)
    ap.add_argument("--terrain-assignment", type=Path, required=True)
    ap.add_argument("--feature-contract", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    f02_table = args.f02_dir / "winner_modeling_table.parquet"
    if file_sha256(f02_table) != F02_SHA:
        raise SystemExit("COEFFICIENT_RECOVERY_VALIDATION_FAILED: F02 physical SHA mismatch")
    if file_sha256(args.terrain_assignment) != TERRAIN_COMPRESSED_SHA:
        raise SystemExit("COEFFICIENT_RECOVERY_VALIDATION_FAILED: terrain compressed SHA mismatch")

    feature_contract = json.loads(args.feature_contract.read_text(encoding="utf-8"))
    selected = pd.read_csv(args.mov0_run_dir / "selected_C_by_surface_year.csv")
    frozen_oof = {s: load_oof(args.mov0_run_dir, s) for s in SURFACES}
    population = build_population(args.f02_dir, args.canonical_fights)
    terrain = load_terrain_assignment(args.terrain_assignment)

    coefficient_rows: list[dict[str, Any]] = []
    recovery_rows: list[dict[str, Any]] = []
    transformed_parts: dict[str, list[pd.DataFrame]] = {"MOV0_MIN": [], "MOV0_FULL": []}

    for surface in SURFACES:
        for year in OUTER_YEARS:
            train, valid = fold_frames(population, year)
            row = selected[(selected["surface"] == surface) & (selected["outer_year"] == year)]
            if len(row) != 1:
                raise SystemExit(f"COEFFICIENT_RECOVERY_VALIDATION_FAILED: selected C missing {surface} {year}")
            c = float(row.iloc[0]["selected_C"])
            fitted = FittedSurface.fit(train, feature_contract, surface, c)
            pred = fitted.predict(valid)
            frozen = frozen_oof[surface][frozen_oof[surface]["year"] == year].copy()
            aligned = valid[["fight_id"]].copy()
            aligned["recovered_probability"] = pred
            aligned = aligned.merge(
                frozen[["fight_id", "probability"]], on="fight_id", how="outer", validate="one_to_one", indicator=True
            )
            identity_ok = bool(aligned["_merge"].eq("both").all() and len(aligned) == len(valid) == len(frozen))
            if not identity_ok:
                raise SystemExit(f"COEFFICIENT_RECOVERY_VALIDATION_FAILED: identity mismatch {surface} {year}")
            max_abs = float(np.max(np.abs(aligned["recovered_probability"] - aligned["probability"])))
            recovery_rows.append({
                "surface": surface,
                "outer_year": year,
                "selected_C": c,
                "N": int(len(valid)),
                "identity_and_count_match": identity_ok,
                "max_abs_probability_difference": max_abs,
                "tolerance": TOL,
                "within_tolerance": bool(max_abs <= TOL),
            })
            if max_abs > TOL:
                write_json(out / "coefficient_recovery_validation.json", {
                    "status": "COEFFICIENT_RECOVERY_VALIDATION_FAILED",
                    "tolerance": TOL,
                    "rows": recovery_rows,
                })
                raise SystemExit(f"COEFFICIENT_RECOVERY_VALIDATION_FAILED: {surface} {year} max_abs={max_abs:.17g}")

            names = model_feature_names(fitted)
            coef = fitted.model.coef_[0]
            for name, value in zip(names, coef):
                coefficient_rows.append({
                    "surface": surface,
                    "outer_year": year,
                    "selected_C": c,
                    "predictor": name,
                    "coefficient": float(value),
                    "model_facing_scale": "standardized_numeric" if name in fitted.preprocessor.numeric_names else "native_binary_or_one_hot",
                })

            if surface in transformed_parts:
                x = fitted.preprocessor.transform(valid)
                t = pd.DataFrame(x, columns=names)
                t.insert(0, "fight_id", valid["fight_id"].astype(str).to_numpy())
                t.insert(1, "year", year)
                transformed_parts[surface].append(t)

    write_json(out / "coefficient_recovery_validation.json", {
        "status": RECOVERY_STATUS,
        "label": "COEFFICIENT_RECOVERY_REFIT_ONLY",
        "tolerance": TOL,
        "max_abs_probability_difference_overall": max(r["max_abs_probability_difference"] for r in recovery_rows),
        "all_surface_years_within_tolerance": True,
        "rows": recovery_rows,
    })

    coeff_df = pd.DataFrame(coefficient_rows)
    stability = []
    min_predictors = set(coeff_df[coeff_df.surface == "MOV0_MIN"].predictor)
    for (surface, predictor), g in coeff_df.groupby(["surface", "predictor"], sort=True):
        vals = g.sort_values("outer_year")["coefficient"].to_numpy(float)
        eps = 1e-12
        pos = int((vals > eps).sum())
        neg = int((vals < -eps).sum())
        zero = int((np.abs(vals) <= eps).sum())
        if pos == len(vals):
            label = "CONSISTENTLY_FINISH_INCREASING"
        elif neg == len(vals):
            label = "CONSISTENTLY_DECISION_INCREASING"
        elif pos == 0 and neg == 0:
            label = "APPROXIMATELY_ZERO"
        elif pos == 0 or neg == 0:
            label = "DIRECTIONALLY_STABLE_WITH_ZERO"
        else:
            label = "SIGN_UNSTABLE"
        stability.append({
            "surface": surface,
            "predictor": predictor,
            "years": g.sort_values("outer_year")["outer_year"].astype(int).tolist(),
            "coefficients": [float(x) for x in vals],
            "mean": float(vals.mean()),
            "median": float(np.median(vals)),
            "minimum": float(vals.min()),
            "maximum": float(vals.max()),
            "range": float(vals.max() - vals.min()),
            "positive_years": pos,
            "negative_years": neg,
            "approximately_zero_years": zero,
            "sign_consistency": float(max(pos, neg, zero) / len(vals)),
            "descriptive_group": label,
            "only_present_in_full": bool(surface == "MOV0_FULL" and predictor not in min_predictors),
        })
    write_json(out / "coefficient_stability.json", {"rows": stability})
    write_json(out / "coefficients_by_year.json", {"rows": coefficient_rows})

    joined: dict[str, pd.DataFrame] = {}
    for surface in ("MOV0_MIN", "MOV0_FULL"):
        d = frozen_oof[surface].merge(terrain, on="fight_id", how="left", validate="one_to_one", indicator=True)
        if not d["_merge"].eq("both").all():
            raise RuntimeError(f"terrain join incomplete {surface}")
        joined[surface] = d.drop(columns="_merge")

    composition = []
    for surface, d in joined.items():
        for pb in [x[0] for x in BUCKETS]:
            bd = d[d.probability_bucket == pb]
            for dim in TERRAIN_COLS:
                terrain_totals = d.groupby(dim, dropna=False).size()
                for cat, g in bd.groupby(dim, dropna=False):
                    total_cat = int(terrain_totals.loc[cat])
                    composition.append({
                        "model": surface,
                        "probability_bucket": pb,
                        "terrain_dimension": dim,
                        "terrain_category": str(cat),
                        "N": int(len(g)),
                        "percent_of_probability_bucket": float(len(g) / len(bd)),
                        "percent_of_terrain_category_in_probability_bucket": float(len(g) / total_cat),
                    })
    write_json(out / "bucket_terrain_composition.json", {"rows": composition})

    perf = []
    for surface, d in joined.items():
        for pb in [x[0] for x in BUCKETS]:
            bd = d[d.probability_bucket == pb]
            for dim in TERRAIN_COLS:
                for cat, g in bd.groupby(dim, dropna=False):
                    n = len(g)
                    k = int(g.target.sum())
                    perf.append({
                        "model": surface,
                        "probability_bucket": pb,
                        "terrain_dimension": dim,
                        "terrain_category": str(cat),
                        "N": int(n),
                        "mean_predicted_finish_probability": float(g.probability.mean()),
                        "observed_finish_rate": float(g.target.mean()),
                        "calibration_gap": float(g.target.mean() - g.probability.mean()),
                        "standard_finish": k,
                        "decision": int(n-k),
                        "wilson_95": wilson95(k,n),
                        "sample_size_governance": sample_gate(n),
                    })
    write_json(out / "bucket_terrain_performance.json", {"rows": perf})

    pair = frozen_oof["MOV0_MIN"][["fight_id","event_id","year","target","probability"]].rename(columns={"probability":"p_min"})
    pair = pair.merge(frozen_oof["MOV0_FULL"][["fight_id","probability"]].rename(columns={"probability":"p_full"}), on="fight_id", validate="one_to_one")
    pair = pair.merge(terrain, on="fight_id", validate="one_to_one")
    pair["delta_p"] = pair.p_full - pair.p_min
    pair["migration_group"] = pair.delta_p.map(migration_bucket)
    q = pair.delta_p.quantile([0, .01, .05, .10, .25, .50, .75, .90, .95, .99, 1]).to_dict()
    migration_groups = []
    for group_name, g in pair.groupby("migration_group", sort=False):
        terrain_comp = {}
        for dim in TERRAIN_COLS:
            terrain_comp[dim] = {str(k): int(v) for k,v in g[dim].value_counts(dropna=False).items()}
        migration_groups.append({
            "group": group_name,
            "N": int(len(g)),
            "mean_delta_p": float(g.delta_p.mean()),
            "median_delta_p": float(g.delta_p.median()),
            "observed_finish_rate": float(g.target.mean()),
            "terrain_counts": terrain_comp,
        })
    write_json(out / "min_to_full_migration.json", {
        "N": int(len(pair)),
        "mean_delta_p": float(pair.delta_p.mean()),
        "median_delta_p": float(pair.delta_p.median()),
        "quantiles": {str(k): float(v) for k,v in q.items()},
        "moved_up": int((pair.delta_p > 1e-12).sum()),
        "moved_down": int((pair.delta_p < -1e-12).sum()),
        "effectively_unchanged_at_1e_12": int((pair.delta_p.abs() <= 1e-12).sum()),
        "fixed_groups": migration_groups,
    })

    both = pair[(pair.p_min >= .70) & (pair.p_full >= .70)]
    promoted = pair[(pair.p_min < .70) & (pair.p_full >= .70)]
    demoted = pair[(pair.p_min >= .70) & (pair.p_full < .70)]
    high_groups = []
    for label, g in (("BOTH_GE_0_70",both),("PROMOTED_BY_FULL",promoted),("DEMOTED_BY_FULL",demoted)):
        terrain_comp = {dim:{str(k):int(v) for k,v in g[dim].value_counts(dropna=False).items()} for dim in TERRAIN_COLS}
        high_groups.append({
            "group": label,
            "N": int(len(g)),
            "observed_finish_rate": None if len(g)==0 else float(g.target.mean()),
            "mean_MIN_probability": None if len(g)==0 else float(g.p_min.mean()),
            "mean_FULL_probability": None if len(g)==0 else float(g.p_full.mean()),
            "mean_delta_p": None if len(g)==0 else float(g.delta_p.mean()),
            "terrain_counts": terrain_comp,
        })
    write_json(out / "high_confidence_migration.json", {"rows":high_groups})

    weight_rows = []
    for wc in WEIGHT_CLASSES:
        ids = set(terrain.loc[terrain.weight_class == wc, "fight_id"].astype(str))
        for surface in ("MOV0_MIN","MOV0_FULL"):
            d = frozen_oof[surface][frozen_oof[surface].fight_id.astype(str).isin(ids)].copy()
            base = metric_bundle(d.target,d.probability)
            bucket_rows=[]
            for pb in [x[0] for x in BUCKETS]:
                g=d[d.probability_bucket==pb]
                bucket_rows.append({
                    "bucket":pb,
                    "N":int(len(g)),
                    "observed_finish_rate":None if len(g)==0 else float(g.target.mean()),
                    "mean_prediction":None if len(g)==0 else float(g.probability.mean()),
                    "governance":sample_gate(len(g)),
                })
            weight_rows.append({"weight_class":wc,"surface":surface,"aggregate":base,"bucket_distribution":bucket_rows})
        wp = pair[pair.fight_id.astype(str).isin(ids)]
        weight_rows.append({
            "weight_class":wc,
            "surface":"MIN_TO_FULL_MIGRATION",
            "N":int(len(wp)),
            "mean_delta_p":float(wp.delta_p.mean()),
            "median_delta_p":float(wp.delta_p.median()),
            "up":int((wp.delta_p>1e-12).sum()),
            "down":int((wp.delta_p<-1e-12).sum()),
        })
    selected_ids=set(terrain.loc[terrain.weight_class.isin(WEIGHT_CLASSES),"fight_id"].astype(str))
    for surface in ("MOV0_MIN","MOV0_FULL"):
        d=frozen_oof[surface][~frozen_oof[surface].fight_id.astype(str).isin(selected_ids)]
        weight_rows.append({"weight_class":"REMAINING_OOF","surface":surface,"aggregate":metric_bundle(d.target,d.probability)})
    write_json(out / "weight_class_diagnostic.json", {"rows":weight_rows})

    feature_profiles = []
    transformed_all: dict[str,pd.DataFrame] = {}
    for surface, parts in transformed_parts.items():
        tx = pd.concat(parts, ignore_index=True)
        tx = tx.merge(frozen_oof[surface][["fight_id","probability_bucket"]], on="fight_id", validate="one_to_one")
        transformed_all[surface]=tx
        feature_cols=[c for c in tx.columns if c not in {"fight_id","year","probability_bucket"}]
        for pb in [x[0] for x in BUCKETS]:
            g=tx[tx.probability_bucket==pb]
            for col in feature_cols:
                s=g[col].astype(float)
                feature_profiles.append({
                    "surface":surface,
                    "probability_bucket":pb,
                    "predictor":col,
                    "N":int(len(s)),
                    "mean":float(s.mean()),
                    "median":float(s.median()),
                    "q25":float(s.quantile(.25)),
                    "q75":float(s.quantile(.75)),
                })
    write_json(out / "feature_by_bucket_profiles.json", {"rows":feature_profiles})

    migration_features=[]
    full_x=transformed_all["MOV0_FULL"].merge(pair[["fight_id","p_min","p_full","delta_p"]],on="fight_id",validate="one_to_one")
    full_x["hc_group"]="OTHER"
    full_x.loc[(full_x.p_min>=.70)&(full_x.p_full>=.70),"hc_group"]="BOTH_GE_0_70"
    full_x.loc[(full_x.p_min<.70)&(full_x.p_full>=.70),"hc_group"]="PROMOTED_BY_FULL"
    full_x.loc[(full_x.p_min>=.70)&(full_x.p_full<.70),"hc_group"]="DEMOTED_BY_FULL"
    fcols=[c for c in full_x.columns if c not in {"fight_id","year","probability_bucket","p_min","p_full","delta_p","hc_group"}]
    for grp in ("BOTH_GE_0_70","PROMOTED_BY_FULL","DEMOTED_BY_FULL"):
        g=full_x[full_x.hc_group==grp]
        for col in fcols:
            if len(g):
                migration_features.append({
                    "group":grp,
                    "predictor":col,
                    "N":int(len(g)),
                    "mean":float(g[col].mean()),
                    "median":float(g[col].median()),
                })
    write_json(out / "high_confidence_feature_profiles.json", {"rows":migration_features})

    normal_perf=[r for r in perf if r["sample_size_governance"]=="NORMAL"]
    worst_over=sorted(normal_perf,key=lambda r:r["calibration_gap"])[:20]
    worst_under=sorted(normal_perf,key=lambda r:r["calibration_gap"],reverse=True)[:20]
    write_json(out / "normal_cell_calibration_extremes.json", {
        "most_overpredicting":worst_over,
        "most_underpredicting":worst_under,
    })

    marker={
        "status":STATUS,
        "coefficient_recovery_status":RECOVERY_STATUS,
        "coefficient_recovery_label":"COEFFICIENT_RECOVERY_REFIT_ONLY",
        "authoritative_source":{
            "run_source_head":SOURCE_HEAD,
            "workflow_run":WORKFLOW_RUN,
            "artifact":ARTIFACT_NAME,
            "artifact_id":ARTIFACT_ID,
            "oof_sha256":OOF_SHA,
            "f02_sha256":F02_SHA,
            "terrain_compressed_sha256":TERRAIN_COMPRESSED_SHA,
        },
        "predictions_regenerated":False,
        "original_frozen_oof_remains_authoritative":True,
        "models_refit_only_for_coefficients":True,
        "modeling_methodology_changed":False,
        "recalibrated":False,
        "thresholds_optimized":False,
        "sportsbook_data_used":False,
        "roi_ev_analyzed":False,
        "mov1_started":False,
        "specialized_models_built":False,
        "simulator_code_built":False,
    }
    write_json(out / "MOV0_CONFIDENCE_TERRAIN_FEATURE_BEHAVIOR_DIAGNOSTIC_V1_COMPLETE.json", marker)
    print(json.dumps(marker,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
