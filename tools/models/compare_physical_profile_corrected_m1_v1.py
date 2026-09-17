#!/usr/bin/env python3
"""Controlled old-vs-corrected physical-profile F02/M1 comparison.

This script intentionally does not alter M1 methodology. It:
1) validates the corrected F02 schema/target contract against the frozen surface,
2) swaps only the expected F02 artifact identity at the M1 input-validation boundary,
3) runs the imported frozen M1 implementation unchanged,
4) compares old and corrected artifacts deterministically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score

import ufc_edge.models.m1 as m1


OLD_M1_EXPECTED = {
    "log_loss": 0.6447214815344309,
    "brier": 0.22678021573492263,
    "accuracy": 0.6267330252399573,
    "auc": 0.6736960708977484,
}
OLD_F02_EXPECTED = {
    "rows": 9252,
    "predictors": 200,
    "schema_version": "1.0.1",
    "predictor_logical_sha256": "ac55fd6fc1f19be7afac2007fccceb43b5c3f98327554d0c58fbe6cb0b164383",
    "schema_sha256": "488c96eed4d86a75da8b763c879a65d6b85959393ec7b6c59f7051b0c03836a8",
    "target_contract_sha256": "fe34f7fd2b70611ec0602d9c9208debf8ec11d7eb8ea1adc0a4104ddb46ffd52",
}
REACH_MISSING_TERM = "pair::ctx__physical_size_profile__reach_cm::missing_diff"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--old-f02-dir", type=Path, required=True)
    p.add_argument("--new-f02-dir", type=Path, required=True)
    p.add_argument("--m0-oof", type=Path, required=True)
    p.add_argument("--old-m1-dir", type=Path, required=True)
    p.add_argument("--old-control-dir", type=Path, required=True)
    p.add_argument("--canonical-v0-dir", type=Path, required=True)
    p.add_argument("--canonical-v1-dir", type=Path, required=True)
    p.add_argument("--feature-surface", type=Path, required=True)
    p.add_argument("--model-contract", type=Path, required=True)
    p.add_argument("--validation-plan", type=Path, required=True)
    p.add_argument("--acceptance-gates", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--stub-new-m1-from", type=Path, help="Preflight-only: monkeypatch M1 validation by copying a frozen artifact.")
    return p.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def metric_bundle(frame: pd.DataFrame, probability: str) -> dict[str, Any]:
    y = frame["target"].astype(int)
    p = frame[probability].astype(float)
    return {
        "n": int(len(frame)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "accuracy": float(accuracy_score(y, p >= 0.5)),
        "auc": None if y.nunique() < 2 else float(roc_auc_score(y, p)),
    }


def delta_metrics(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    return {
        k: None if old.get(k) is None or new.get(k) is None else float(new[k] - old[k])
        for k in ("log_loss", "brier", "accuracy", "auc")
    }


def rel_delta(old: float | None, new: float | None) -> float | None:
    if old is None or new is None or old == 0:
        return None
    return float((new - old) / abs(old))


def equal_series(a: pd.Series, b: pd.Series) -> np.ndarray:
    # Robust exact semantic comparison with NaN==NaN and normalized datetime/string behavior.
    av = a.to_numpy()
    bv = b.to_numpy()
    if len(av) != len(bv):
        raise RuntimeError("series length mismatch")
    both_na = pd.isna(av) & pd.isna(bv)
    try:
        eq = av == bv
        if np.isscalar(eq):
            eq = np.full(len(av), bool(eq))
        eq = np.asarray(eq, dtype=bool)
    except Exception:
        eq = np.asarray([x == y for x, y in zip(av, bv)], dtype=bool)
    return both_na | eq


def predictor_columns(schema: dict[str, Any]) -> list[str]:
    return [c["name"] for c in schema["columns"] if c.get("predictor") is True]


def m1_source_columns(surface: dict[str, Any]) -> list[str]:
    cols: list[str] = []
    for keys in surface["paired_fighter_predictors"]["concepts"].values():
        for key in keys:
            cols += [f"f1__{key}", f"f2__{key}"]
    for item in surface["matchup_predictors"]["review"]:
        if item["accepted"]:
            cols += list(item["columns"])
    # Frozen contract: 96 fighter pairs plus five accepted matchup predictors.
    if len(cols) != 197:
        raise RuntimeError(f"unexpected raw M1 source column count {len(cols)}")
    return cols


def json_safe(value: Any) -> Any:
    """Return canonical-JSON-safe analytical output, mapping non-finite values to null."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if value is pd.NA:
        return None
    return value


def markdown_number(value: Any, spec: str = ".9f") -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "n/a"
    return format(float(value), spec)


def coeff_summary(payload: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for fold in payload:
        fold_id = str(fold["fold_id"])
        for c in fold["coefficients"]:
            rows.append({
                "fold_id": fold_id,
                "feature": c["feature"],
                "source_concept": c.get("source_concept"),
                "family": c.get("family"),
                "role": c.get("role"),
                "is_missingness": bool(c.get("is_missingness")),
                "coefficient": float(c["coefficient"]),
            })
    df = pd.DataFrame(rows)
    out = df.groupby(["feature","source_concept","family","role","is_missingness"], dropna=False)["coefficient"].agg(
        mean="mean", std=lambda s: float(np.std(s.to_numpy(), ddof=0)),
        min="min", max="max",
        nonzero=lambda s: int(np.sum(np.abs(s.to_numpy()) > 1e-12)),
        positive=lambda s: int(np.sum(s.to_numpy() > 1e-12)),
        negative=lambda s: int(np.sum(s.to_numpy() < -1e-12)),
    ).reset_index()
    return out


def fold_coefficients(payload: list[dict[str, Any]], feature: str) -> list[dict[str, Any]]:
    out = []
    for fold in payload:
        row = next((x for x in fold["coefficients"] if x["feature"] == feature), None)
        if row is None:
            raise RuntimeError(f"missing coefficient {feature} in fold {fold['fold_id']}")
        out.append({"fold_id": str(fold["fold_id"]), "coefficient": float(row["coefficient"])})
    return out


def calibration_from_result(result: dict[str, Any]) -> dict[str, Any]:
    c = result.get("calibration", {})
    return {
        "expected_calibration_error": c.get("m1_expected_calibration_error"),
        "bins": c.get("m1_bins", []),
        "intercept": None,
        "slope": None,
        "note": "Frozen M1 V1 governs ECE/probability bins; calibration intercept/slope are not emitted by the frozen procedure.",
    }


def main() -> int:
    args = parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    old_schema = read_json(args.old_f02_dir / "schema.json")
    new_schema = read_json(args.new_f02_dir / "schema.json")
    old_summary = read_json(args.old_f02_dir / "summary.json")
    new_summary = read_json(args.new_f02_dir / "summary.json")
    read_json(args.old_f02_dir / "manifest.json")
    new_manifest = read_json(args.new_f02_dir / "manifest.json")
    old_target_manifest = read_json(args.old_f02_dir / "target_manifest.json")
    new_target_manifest = read_json(args.new_f02_dir / "target_manifest.json")
    surface = read_json(args.feature_surface)

    # Frozen old evidence must reproduce repository truth before comparison.
    if old_summary["predictor_rows"] != OLD_F02_EXPECTED["rows"]:
        raise RuntimeError("old F02 row count mismatch")
    if old_summary["predictor_columns"] != OLD_F02_EXPECTED["predictors"]:
        raise RuntimeError("old F02 predictor count mismatch")
    if old_summary["predictor_logical_sha256"] != OLD_F02_EXPECTED["predictor_logical_sha256"]:
        raise RuntimeError("old F02 logical identity mismatch")
    if old_schema["schema_sha256"] != OLD_F02_EXPECTED["schema_sha256"]:
        raise RuntimeError("old F02 schema mismatch")

    # STOP CONDITIONS: population/schema/labels must be unchanged.
    if new_summary["predictor_rows"] != old_summary["predictor_rows"]:
        raise RuntimeError("STOP: corrected F02 changed fight population unexpectedly")
    if new_schema != old_schema:
        raise RuntimeError("STOP: corrected F02 schema/feature universe changed unexpectedly")
    old_contract = old_target_manifest["deterministic"]["target_contract"]["contract_sha256"]
    new_contract = new_target_manifest["deterministic"]["target_contract"]["contract_sha256"]
    if old_contract != new_contract or new_contract != OLD_F02_EXPECTED["target_contract_sha256"]:
        raise RuntimeError("STOP: corrected F02 target contract changed unexpectedly")

    old_f02 = pd.read_parquet(args.old_f02_dir / "winner_modeling_table.parquet")
    new_f02 = pd.read_parquet(args.new_f02_dir / "winner_modeling_table.parquet")
    if old_f02["fight_id"].tolist() != new_f02["fight_id"].tolist():
        raise RuntimeError("STOP: corrected F02 fight order differs")
    identity_cols = ["fight_id","event_id","event_date","prediction_as_of","promotion","fighter_1_id","fighter_2_id",
                     "target_state","binary_winner_eligible","fighter_1_win","winner_id"]
    for col in identity_cols:
        if col not in old_f02.columns or col not in new_f02.columns:
            raise RuntimeError(f"STOP: corrected F02 required identity/label column absent: {col}")
        if not bool(equal_series(old_f02[col], new_f02[col]).all()):
            raise RuntimeError(f"STOP: corrected F02 identity/label column changed: {col}")
    if int(old_f02["binary_winner_eligible"].sum()) != int(new_f02["binary_winner_eligible"].sum()):
        raise RuntimeError("STOP: corrected F02 binary-label eligible population changed")
    if old_f02["target_state"].value_counts(dropna=False).to_dict() != new_f02["target_state"].value_counts(dropna=False).to_dict():
        raise RuntimeError("STOP: corrected F02 target-state counts changed")

    pred_cols = predictor_columns(old_schema)
    changed_by_col: dict[str, int] = {}
    miss_changed_by_col: dict[str, int] = {}
    row_changed = np.zeros(len(old_f02), dtype=bool)
    total_changed_cells = 0
    for col in pred_cols:
        eq = equal_series(old_f02[col], new_f02[col])
        diff = ~eq
        n = int(diff.sum())
        if n:
            changed_by_col[col] = n
            total_changed_cells += n
            row_changed |= diff
        missdiff = old_f02[col].isna().to_numpy() != new_f02[col].isna().to_numpy()
        if missdiff.any():
            miss_changed_by_col[col] = int(missdiff.sum())

    raw_m1_cols = m1_source_columns(surface)
    m1_row_changed = np.zeros(len(old_f02), dtype=bool)
    for col in raw_m1_cols:
        m1_row_changed |= ~equal_series(old_f02[col], new_f02[col])

    physical_cols = [c for c in changed_by_col if "physical_size_profile" in c or "reach_difference_cm" in c]
    physical_missing_cols = {c:n for c,n in miss_changed_by_col.items() if "physical_size_profile" in c or "reach_difference_cm" in c}
    downstream_cols = [c for c in changed_by_col if c not in physical_cols]

    # Canonical DATA diff and provenance/temporal safety.
    v0_fighters = pd.read_csv(args.canonical_v0_dir / "fighters.csv", dtype=str).fillna("")
    v1_fighters = pd.read_csv(args.canonical_v1_dir / "fighters.csv", dtype=str).fillna("")
    if v0_fighters["fighter_id"].tolist() != v1_fighters["fighter_id"].tolist():
        raise RuntimeError("STOP: canonical fighter population/order changed")
    data_changes = []
    for field in ("height_cm","reach_cm"):
        a = v0_fighters[field]
        b = v1_fighters[field]
        diff = a.ne(b)
        for i in np.flatnonzero(diff.to_numpy()):
            data_changes.append({
                "fighter_id": v0_fighters.iloc[i]["fighter_id"],
                "fighter_name": v0_fighters.iloc[i]["canonical_name"],
                "field": field,
                "old": a.iloc[i] or None,
                "new": b.iloc[i] or None,
            })
    prov = pd.read_csv(args.canonical_v1_dir / "field_provenance.csv", dtype=str).fillna("")
    for change in data_changes:
        hit = prov[(prov["row_key"] == change["fighter_id"]) & (prov["field_name"] == change["field"])]
        if hit.empty:
            raise RuntimeError(f"STOP: corrected physical field lacks provenance {change}")
    data_manifest = read_json(args.canonical_v1_dir / "manifest.json")
    if "static athlete attributes" not in str(data_manifest.get("temporal_semantics","")).lower():
        raise RuntimeError("STOP: corrected DATA manifest lacks governed static-attribute temporal semantics")

    # Verify old M1 and exact old-control rerun.
    old_result = read_json(args.old_m1_dir / "m1_result.json")
    control_result = read_json(args.old_control_dir / "m1_result.json")
    for k,v in OLD_M1_EXPECTED.items():
        if abs(float(old_result["aggregate"]["m1"][k]) - v) > 1e-12:
            raise RuntimeError(f"old M1 expected {k} mismatch")
    old_oof = pd.read_parquet(args.old_m1_dir / "m1_oof_predictions.parquet").sort_values("fight_id").reset_index(drop=True)
    ctrl_oof = pd.read_parquet(args.old_control_dir / "m1_oof_predictions.parquet").sort_values("fight_id").reset_index(drop=True)
    old_control_columns = ["fight_id", "event_date", "fold_id", "target", "m0_probability", "m1_probability", "chosen_spec"]
    if any(c not in old_oof.columns or c not in ctrl_oof.columns for c in old_control_columns) or len(old_oof) != len(ctrl_oof):
        raise RuntimeError("STOP: frozen M1 old-control OOF shape/schema did not reproduce")
    old_control_max = 0.0
    for col in old_control_columns:
        if col in {"m0_probability", "m1_probability"}:
            delta = np.abs(old_oof[col].to_numpy(dtype=float) - ctrl_oof[col].to_numpy(dtype=float))
            observed = float(np.nanmax(delta)) if len(delta) else 0.0
            old_control_max = max(old_control_max, observed)
            equal = np.isclose(old_oof[col].to_numpy(dtype=float), ctrl_oof[col].to_numpy(dtype=float), rtol=0.0, atol=1e-15, equal_nan=True)
        else:
            equal = equal_series(old_oof[col], ctrl_oof[col])
        if not bool(equal.all()):
            raise RuntimeError(f"STOP: frozen M1 old-control OOF values did not reproduce: {col}")

    # Corrected M1 uses the same imported model code. Only the expected F02 identity changes.
    new_identity = dict(m1.F02_IDENTITY)
    new_identity.update({
        "replay_schema_version": new_schema["replay_schema_version"],
        "schema_sha256": new_schema["schema_sha256"],
        "predictor_logical_sha256": new_summary["predictor_logical_sha256"],
        "predictor_manifest_sha256": new_summary["predictor_manifest_sha256"],
        "target_contract_sha256": new_target_manifest["deterministic"]["target_contract"]["contract_sha256"],
        "target_logical_sha256": new_target_manifest["deterministic"]["target_logical_sha256"],
    })
    if new_identity["schema_sha256"] != OLD_F02_EXPECTED["schema_sha256"]:
        raise RuntimeError("STOP: corrected F02 schema hash differs")
    if new_identity["target_contract_sha256"] != OLD_F02_EXPECTED["target_contract_sha256"]:
        raise RuntimeError("STOP: corrected F02 target contract differs")
    m1.F02_IDENTITY = new_identity
    new_m1_dir = out / "m1_corrected"
    if args.stub_new_m1_from:
        # The CI preflight deliberately exercises the whole comparison/reporting path without fitting M1.
        # This does not alter the production M1 path and is only reachable through an explicit preflight flag.
        frozen_dir = args.stub_new_m1_from
        def _preflight_stub_run_validation(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
            shutil.copytree(frozen_dir, new_m1_dir, dirs_exist_ok=True)
            return read_json(new_m1_dir / "m1_result.json")
        m1.run_validation = _preflight_stub_run_validation
    new_result = m1.run_validation(
        args.new_f02_dir, args.m0_oof, args.feature_surface, new_m1_dir, run_ablations=False
    )
    if new_result["feature_surface"]["projected_dimensions"] != old_result["feature_surface"]["projected_dimensions"]:
        raise RuntimeError("STOP: M1 modeled dimensionality changed")
    if new_result["population"]["outer_years"] != old_result["population"]["outer_years"]:
        raise RuntimeError("STOP: M1 fold plan changed")
    if new_result["model"] != old_result["model"]:
        raise RuntimeError("STOP: M1 model/preprocessing/grid/seed contract changed")

    new_oof = pd.read_parquet(new_m1_dir / "m1_oof_predictions.parquet")
    old_oof2 = pd.read_parquet(args.old_m1_dir / "m1_oof_predictions.parquet")
    joined = old_oof2.rename(columns={"m1_probability":"old_probability","chosen_spec":"old_chosen_spec"}).merge(
        new_oof[["fight_id","event_date","fold_id","target","m1_probability","chosen_spec"]].rename(
            columns={"m1_probability":"new_probability","chosen_spec":"new_chosen_spec","target":"new_target",
                     "event_date":"new_event_date","fold_id":"new_fold_id"}),
        on="fight_id", how="inner", validate="one_to_one"
    )
    if len(joined) != len(old_oof2):
        raise RuntimeError("STOP: M1 OOF population changed")
    if not np.array_equal(joined["target"].to_numpy(), joined["new_target"].to_numpy()):
        raise RuntimeError("STOP: M1 OOF labels changed")
    if not np.array_equal(joined["fold_id"].astype(str).to_numpy(), joined["new_fold_id"].astype(str).to_numpy()):
        raise RuntimeError("STOP: M1 fold assignment changed")
    if not bool(equal_series(joined["event_date"], joined["new_event_date"]).all()):
        raise RuntimeError("STOP: M1 OOF event dates changed")

    # Attach raw F02 affected/control classification.
    affected_map = pd.Series(m1_row_changed, index=old_f02["fight_id"]).to_dict()
    f02_row_changed_map = pd.Series(row_changed, index=old_f02["fight_id"]).to_dict()
    for name, mapping in (("m1_input_affected", affected_map), ("f02_predictor_affected", f02_row_changed_map)):
        mapped = joined["fight_id"].map(mapping)
        if mapped.isna().any():
            missing = joined.loc[mapped.isna(), "fight_id"].head(5).tolist()
            raise RuntimeError(f"STOP: OOF fight missing from F02 affected-row map ({name}): {missing}")
        joined[name] = mapped.astype(bool)
    joined["abs_probability_delta"] = np.abs(joined["new_probability"] - joined["old_probability"])
    joined["probability_delta"] = joined["new_probability"] - joined["old_probability"]
    joined["event_year"] = pd.to_datetime(joined["event_date"]).dt.year

    # Aggregate and fold/year tables.
    old_agg = old_result["aggregate"]["m1"]
    new_agg = new_result["aggregate"]["m1"]
    aggregate = {
        "old": old_agg,
        "corrected": new_agg,
        "absolute_delta_corrected_minus_old": delta_metrics(old_agg, new_agg),
        "relative_delta": {k: rel_delta(old_agg.get(k), new_agg.get(k)) for k in ("log_loss","brier","accuracy","auc")},
    }
    old_folds = {str(x["fold_id"]):x for x in old_result["folds"]}
    new_folds = {str(x["fold_id"]):x for x in new_result["folds"]}
    fold_rows = []
    for y in old_result["population"]["outer_years"]:
        key = str(y)
        a = old_folds[key]
        b = new_folds[key]
        if a["validation_rows"] != b["validation_rows"] or a["validation_start"] != b["validation_start"] or a["validation_end"] != b["validation_end"]:
            raise RuntimeError(f"STOP: fold population/window changed {key}")
        fold_rows.append({
            "fold_id": key,
            "validation_start": a["validation_start"], "validation_end": a["validation_end"],
            "observations": a["validation_rows"],
            "old": a["m1"], "corrected": b["m1"],
            "delta": delta_metrics(a["m1"], b["m1"]),
            "old_selected_candidate": a["selected_candidate"],
            "corrected_selected_candidate": b["selected_candidate"],
            "old_selected_spec": a["selected_spec"],
            "corrected_selected_spec": b["selected_spec"],
        })

    year_rows = []
    for year, g in joined.groupby("event_year", sort=True):
        oldm = metric_bundle(g, "old_probability")
        newm = metric_bundle(g, "new_probability")
        year_rows.append({"year":int(year),"old":oldm,"corrected":newm,"delta":delta_metrics(oldm,newm)})

    def group_analysis(g: pd.DataFrame) -> dict[str, Any]:
        if g.empty:
            return {"n":0}
        oldm = metric_bundle(g, "old_probability")
        newm = metric_bundle(g, "new_probability")
        return {
            "n": int(len(g)), "old":oldm, "corrected":newm, "delta":delta_metrics(oldm,newm),
            "mean_absolute_probability_shift": float(g["abs_probability_delta"].mean()),
            "median_absolute_probability_shift": float(g["abs_probability_delta"].median()),
            "max_absolute_probability_shift": float(g["abs_probability_delta"].max()),
        }

    affected = group_analysis(joined[joined["m1_input_affected"]])
    unaffected = group_analysis(joined[~joined["m1_input_affected"]])
    # Unaffected raw validation rows may still move after refit because corrected training rows change coefficients.
    unaffected["explanation_if_probabilities_move"] = (
        "Raw M1 inputs for these validation rows are identical old/new. Nonzero probability shifts are expected only "
        "through fold-model refitting when corrected rows exist in that fold's training history; old-control rerun proves determinism."
    )

    dist = {
        "all_oof": {q:float(v) for q,v in zip(["mean","median","p90","p95","max"],[
            joined["abs_probability_delta"].mean(), joined["abs_probability_delta"].median(),
            joined["abs_probability_delta"].quantile(.90), joined["abs_probability_delta"].quantile(.95),
            joined["abs_probability_delta"].max()])},
    }
    for label,mask in [("m1_input_affected",joined["m1_input_affected"]),("m1_input_unaffected",~joined["m1_input_affected"])]:
        s=joined.loc[mask,"abs_probability_delta"]
        dist[label]={q:float(v) for q,v in zip(["mean","median","p90","p95","max"],[
            s.mean(),s.median(),s.quantile(.90),s.quantile(.95),s.max()])} if len(s) else {}

    # Missingness source and projected reach-missingness term.
    missingness = {"source_columns":{}}
    for base in ("height_cm","reach_cm"):
        cols=[f"f1__ctx__physical_size_profile__{base}", f"f2__ctx__physical_size_profile__{base}"]
        old_missing=sum(int(old_f02[c].isna().sum()) for c in cols)
        new_missing=sum(int(new_f02[c].isna().sum()) for c in cols)
        old_rows=(old_f02[cols[0]].isna() | old_f02[cols[1]].isna())
        new_rows=(new_f02[cols[0]].isna() | new_f02[cols[1]].isna())
        missingness["source_columns"][base]={
            "old_missing_fighter_sides": old_missing, "corrected_missing_fighter_sides": new_missing,
            "old_rows_either_side_missing": int(old_rows.sum()), "corrected_rows_either_side_missing": int(new_rows.sum()),
            "old_row_prevalence": float(old_rows.mean()), "corrected_row_prevalence": float(new_rows.mean()),
        }
    # OOF projected missing_diff can be read directly from source missingness.
    oof_ids=set(joined["fight_id"])
    old_oof_f02=old_f02[old_f02["fight_id"].isin(oof_ids)].set_index("fight_id").loc[joined["fight_id"]]
    new_oof_f02=new_f02[new_f02["fight_id"].isin(oof_ids)].set_index("fight_id").loc[joined["fight_id"]]
    def missdiff_stats(df: pd.DataFrame, field: str)->dict[str,Any]:
        a=df[f"f1__ctx__physical_size_profile__{field}"].isna().astype(float)
        b=df[f"f2__ctx__physical_size_profile__{field}"].isna().astype(float)
        x=(a-b).to_numpy()
        return {"nonzero_count":int(np.sum(x!=0)), "prevalence":float(np.mean(x!=0)),
                "mean":float(np.mean(x)), "std":float(np.std(x,ddof=0))}
    missingness["reach_missing_diff_oof"]={"old":missdiff_stats(old_oof_f02,"reach_cm"),"corrected":missdiff_stats(new_oof_f02,"reach_cm")}
    missingness["height_missing_diff_oof"]={"old":missdiff_stats(old_oof_f02,"height_cm"),"corrected":missdiff_stats(new_oof_f02,"height_cm")}

    old_coeff_payload=read_json(args.old_m1_dir/"m1_coefficients.json")
    new_coeff_payload=read_json(new_m1_dir/"m1_coefficients.json")
    old_cs = coeff_summary(old_coeff_payload)
    new_cs = coeff_summary(new_coeff_payload)
    reach_old_rows = old_cs[old_cs["feature"] == REACH_MISSING_TERM]
    reach_new_rows = new_cs[new_cs["feature"] == REACH_MISSING_TERM]
    if len(reach_old_rows) != 1 or len(reach_new_rows) != 1:
        raise RuntimeError(
            "STOP: expected exactly one governed reach-missingness coefficient row "
            f"(old={len(reach_old_rows)}, corrected={len(reach_new_rows)})"
        )
    reach_old=reach_old_rows.iloc[0].to_dict()
    reach_new=reach_new_rows.iloc[0].to_dict()
    missingness["reach_missing_diff_coefficient"]={
        "old_summary":reach_old,"corrected_summary":reach_new,
        "old_by_fold":fold_coefficients(old_coeff_payload,REACH_MISSING_TERM),
        "corrected_by_fold":fold_coefficients(new_coeff_payload,REACH_MISSING_TERM),
    }

    # Physical coefficient table and global stability.
    merged_cs=old_cs.merge(new_cs,on=["feature","source_concept","family","role","is_missingness"],suffixes=("_old","_new"),validate="one_to_one")
    merged_cs["abs_mean_change"]=np.abs(merged_cs["mean_new"]-merged_cs["mean_old"])
    physical_mask=(merged_cs["source_concept"].astype(str).eq("physical_size_profile") |
                   merged_cs["source_concept"].astype(str).eq("reach_difference_cm") |
                   merged_cs["feature"].str.contains("physical_size_profile|reach_difference",regex=True))
    physical_coeffs=merged_cs.loc[physical_mask].sort_values("abs_mean_change",ascending=False).to_dict("records")
    all_other=merged_cs.loc[~physical_mask].copy()
    pearson=float(merged_cs["mean_old"].corr(merged_cs["mean_new"],method="pearson"))
    spearman=float(merged_cs["mean_old"].corr(merged_cs["mean_new"],method="spearman"))
    sign_old = np.sign(merged_cs["mean_old"].to_numpy())
    sign_new = np.sign(merged_cs["mean_new"].to_numpy())
    global_coeff={
        "pearson_mean_vector_correlation":pearson,
        "spearman_mean_vector_correlation":spearman,
        "sign_changed_count":int(np.sum(sign_old!=sign_new)),
        "newly_nonzero_count":int(np.sum((np.abs(merged_cs["mean_old"])<=1e-12)&(np.abs(merged_cs["mean_new"])>1e-12))),
        "newly_zero_count":int(np.sum((np.abs(merged_cs["mean_old"])>1e-12)&(np.abs(merged_cs["mean_new"])<=1e-12))),
        "largest_absolute_mean_changes":merged_cs.sort_values("abs_mean_change",ascending=False).head(25).to_dict("records"),
        "physical_profile":physical_coeffs,
        "non_physical_mean_abs_change_mean":float(all_other["abs_mean_change"].mean()),
        "non_physical_mean_abs_change_max":float(all_other["abs_mean_change"].max()),
    }

    # 2026 deep dive and fighter labels.
    fighters=v1_fighters.set_index("fighter_id")["canonical_name"].to_dict()
    old_by_id = old_f02.set_index("fight_id")
    new_by_id = new_f02.set_index("fight_id")
    g26=joined[joined["event_year"]==2026].copy()
    expected_2026_oof = int((pd.to_datetime(old_oof2["event_date"]).dt.year == 2026).sum())
    if len(g26) != expected_2026_oof or expected_2026_oof == 0:
        raise RuntimeError(f"STOP: expected 2026 OOF population unavailable (expected={expected_2026_oof}, actual={len(g26)})")
    top26=[]
    for _,r in g26.sort_values("abs_probability_delta",ascending=False).head(20).iterrows():
        fid = r["fight_id"]
        ro = old_by_id.loc[fid]
        rn = new_by_id.loc[fid]
        changed=[]
        for c in physical_cols:
            if not bool(equal_series(pd.Series([ro[c]]), pd.Series([rn[c]]))[0]):
                changed.append({"column":c,"old":None if pd.isna(ro[c]) else ro[c],"corrected":None if pd.isna(rn[c]) else rn[c]})
        top26.append({
            "fight_id":fid,
            "fighters":[fighters.get(ro["fighter_1_id"],ro["fighter_1_id"]),fighters.get(ro["fighter_2_id"],ro["fighter_2_id"])],
            "old_probability":float(r["old_probability"]),"corrected_probability":float(r["new_probability"]),
            "delta":float(r["probability_delta"]),"abs_delta":float(r["abs_probability_delta"]),
            "corrected_physical_profile_features":changed,
        })
    deep2026={
        **group_analysis(g26),
        "evaluated_fights":int(len(g26)),
        "predictor_rows_changed":int(g26["f02_predictor_affected"].sum()),
        "m1_input_rows_changed":int(g26["m1_input_affected"].sum()),
        "model_probability_changed_gt_1e12":int((g26["abs_probability_delta"]>1e-12).sum()),
        "largest_absolute_prediction_shifts":top26,
    }

    regularization={
        "old":{str(f["fold_id"]):{"candidate":f["selected_candidate"],"spec":f["selected_spec"]} for f in old_result["folds"]},
        "corrected":{str(f["fold_id"]):{"candidate":f["selected_candidate"],"spec":f["selected_spec"]} for f in new_result["folds"]},
        "old_elasticnet_wins":sum(f["selected_spec"]["family"]=="elasticnet" for f in old_result["folds"]),
        "corrected_elasticnet_wins":sum(f["selected_spec"]["family"]=="elasticnet" for f in new_result["folds"]),
    }

    # Fold summaries.
    fold_summary={
        "log_loss_improved":sum(x["delta"]["log_loss"] < -1e-12 for x in fold_rows),
        "log_loss_worsened":sum(x["delta"]["log_loss"] > 1e-12 for x in fold_rows),
        "log_loss_materially_unchanged":sum(abs(x["delta"]["log_loss"]) <= 1e-12 for x in fold_rows),
        "brier_improved":sum(x["delta"]["brier"] < -1e-12 for x in fold_rows),
        "brier_worsened":sum(x["delta"]["brier"] > 1e-12 for x in fold_rows),
        "m1_vs_m0_old_ll_wins":old_result["stability"]["log_loss_fold_wins"],
        "m1_vs_m0_old_brier_wins":old_result["stability"]["brier_fold_wins"],
        "m1_vs_m0_corrected_ll_wins":new_result["stability"]["log_loss_fold_wins"],
        "m1_vs_m0_corrected_brier_wins":new_result["stability"]["brier_fold_wins"],
    }

    # Config/run identities.
    config_parts={
        "feature_surface_sha256":sha256_file(args.feature_surface),
        "model_contract_sha256":sha256_file(args.model_contract),
        "validation_plan_sha256":sha256_file(args.validation_plan),
        "acceptance_gates_sha256":sha256_file(args.acceptance_gates),
    }
    config_hash=stable_hash(config_parts)
    fold_plan_identity=stable_hash({
        "outer_years":new_result["population"]["outer_years"],
        "development_years":new_result["population"]["development_years"],
        "confirmation_years":new_result["population"]["confirmation_years"],
        "inner_validation_years_per_outer_fold":new_result["model"]["inner_validation_years_per_outer_fold"],
    })
    f01_identity={
        "methodology_changed":False,
        "feature_contract_version":new_manifest["deterministic"]["feature_contract_version"],
        "feature_catalog_sha256":new_manifest["deterministic"]["feature_catalog_sha256"],
        "canonical_manifest_sha256":new_manifest["deterministic"]["canonical_manifest_sha256"],
        "canonical_manifest_build":new_manifest["deterministic"]["canonical_manifest_build"],
        "identity_sha256":stable_hash({
            "feature_contract_version":new_manifest["deterministic"]["feature_contract_version"],
            "feature_catalog_sha256":new_manifest["deterministic"]["feature_catalog_sha256"],
            "canonical_manifest_sha256":new_manifest["deterministic"]["canonical_manifest_sha256"],
            "materialized_feature_names":new_manifest["deterministic"]["f01_materialized_feature_names"],
        }),
        "note":"F01 governance does not persist a historical matrix; this identity is the deterministic F01 dependency manifest embedded in corrected F02.",
    }

    # Evidence-based verdict. Aggregate primary scoring drives the coarse class, with 2026 used to distinguish minimal effect vs explanation.
    d = aggregate["absolute_delta_corrected_minus_old"]
    d26 = deep2026["delta"]
    if d["log_loss"] <= -0.005 and d["brier"] <= -0.0025 and d26["log_loss"] < 0 and d26["brier"] < 0:
        verdict="PHYSICAL_PROFILE_MISSINGNESS_WAS_MATERIALLY_DRAGGING_M1"
    elif d["log_loss"] < -1e-5 and d["brier"] < -1e-5 and d26["log_loss"] <= 0 and d26["brier"] <= 0:
        verdict="PHYSICAL_PROFILE_MISSINGNESS_WAS_A_SMALL_BUT_REAL_M1_DRAG"
    elif abs(d["log_loss"]) < .001 and abs(d["brier"]) < .0005 and abs(d26["log_loss"]) < .005:
        verdict="PHYSICAL_PROFILE_CORRECTION_IMPROVED_DATA_QUALITY_WITH_MINIMAL_M1_EFFECT"
    else:
        verdict="PHYSICAL_PROFILE_CORRECTION_DID_NOT_EXPLAIN_M1_WEAKNESS"

    # Freeze recommendation is conservative: require valid determinism/method-equivalence; follow-up only if severe regression or 2026 remains concerning.
    if verdict == "PHYSICAL_PROFILE_CORRECTION_DID_NOT_EXPLAIN_M1_WEAKNESS" and (d["log_loss"] > .002 or d26["log_loss"] > .005):
        recommendation="M1_REQUIRES_DIAGNOSTIC_FOLLOWUP_BEFORE_FREEZE"
    else:
        recommendation="M1_CORRECTED_BASELINE_READY_FOR_FREEZE"

    report={
        "status":"PHYSICAL_PROFILE_CORRECTED_M1_RERUN_V1_COMPLETE",
        "source_state":{
            "authoritative_start_main":"b58a9f2d977cb054c8d0428af22c99c71c879423",
            "corrected_data_status":"RECENT_PHYSICAL_PROFILE_COMPLETE_FROM_GOVERNED_PRIMARY_SOURCES",
            "canonical_v1_manifest_sha256":sha256_file(args.canonical_v1_dir/"manifest.json"),
            "canonical_v1_manifest":data_manifest,
        },
        "controlled_experiment":{
            "f00_methodology_changed":False,"f01_methodology_changed":False,"f02_methodology_changed":False,
            "m1_methodology_changed":False,"m1_feature_pruning_performed":False,"new_features_added":False,
            "hyperparameter_grid_changed":False,"fold_plan_changed":False,"m0_redesigned":False,
            "m1b_started":False,"market_data_used_as_target":False,
            "technical_runtime_adaptation":"Corrected canonical v1 is mounted at the legacy canonical/v0 read path only inside an isolated runner scratch copy; F01/F02 source code and semantics are unchanged. The artifact manifest itself carries the corrected canonical v1 manifest hash/build. Missing unchanged canonical files required by F01 are copied byte-for-byte from v0 into the v1 runtime package.",
        },
        "f01_rebuild":f01_identity,
        "f02_rebuild":{
            "old":{"rows":old_summary["predictor_rows"],"predictors":old_summary["predictor_columns"],"eligible_predictors":len(pred_cols),
                   "schema_version":old_schema["replay_schema_version"],"logical_sha256":old_summary["predictor_logical_sha256"]},
            "corrected":{"rows":new_summary["predictor_rows"],"predictors":new_summary["predictor_columns"],"eligible_predictors":len(pred_cols),
                         "schema_version":new_schema["replay_schema_version"],"logical_sha256":new_summary["predictor_logical_sha256"]},
            "changed_predictor_cells":total_changed_cells,
            "changed_fight_rows":int(row_changed.sum()),
            "changed_predictor_columns":len(changed_by_col),
            "changed_columns":changed_by_col,
            "physical_profile_changed_columns":{c:changed_by_col[c] for c in physical_cols},
            "missingness_changed_columns":physical_missing_cols,
            "downstream_changed_columns":{c:changed_by_col[c] for c in downstream_cols},
        },
        "temporal_safety":{
            "manifest_temporal_semantics":data_manifest.get("temporal_semantics"),
            "corrected_fields_with_provenance":len(data_changes),
            "all_corrected_fields_have_provenance":True,
            "historical_observation_claim":False,
            "static_attribute_policy":"Existing F01 static physical-attribute treatment applied unchanged; corrected values may backfill historical rows as static attributes, while actual source snapshot/retrieval evidence remains in canonical v1 field_provenance.csv.",
        },
        "m1_methodology_equivalence":{
            "feature_set_identical":True,"projected_dimensions":new_result["feature_surface"]["projected_dimensions"],
            "folds_identical":True,"hyperparameter_grid_identical":True,"selection_rule_identical":True,
            "preprocessing_identical":True,"seeds_identical":True,
            "old_control_oof_logical_sha256":control_result["oof"]["logical_sha256"],
            "old_authoritative_oof_logical_sha256":old_result["oof"]["logical_sha256"],
            "old_control_max_abs_probability_error":old_control_max,
        },
        "aggregate_m1_comparison":aggregate,
        "fold_comparison":fold_rows,
        "fold_summary":fold_summary,
        "year_comparison":year_rows,
        "deep_dive_2026":deep2026,
        "affected_vs_unaffected":{"affected":affected,"unaffected":unaffected},
        "missingness_analysis":missingness,
        "coefficient_analysis":global_coeff,
        "regularization_selection":regularization,
        "calibration":{"old":calibration_from_result(old_result),"corrected":calibration_from_result(new_result)},
        "prediction_delta_distribution":dist,
        "determinism":{
            "same_fight_order":True,"same_labels":True,"same_fold_assignment":True,"same_feature_ordering":True,
            "same_transformation_contract":True,"same_model_seed_config":True,
            "old_control_exact_reproduction":True,
            "unaffected_f02_rows_exact":int((~m1_row_changed).sum()),
        },
        "artifact_identity":{
            "data":{"manifest_sha256":sha256_file(args.canonical_v1_dir/"manifest.json")},
            "f01":f01_identity,
            "f02":{"schema_version":new_schema["replay_schema_version"],"rows":new_summary["predictor_rows"],
                   "predictor_count":new_summary["predictor_columns"],"logical_sha256":new_summary["predictor_logical_sha256"],
                   "manifest_sha256":new_summary["predictor_manifest_sha256"],
                   "target_logical_sha256":new_target_manifest["deterministic"]["target_logical_sha256"]},
            "m1":{"run_identity":stable_hash({"f02":new_summary["predictor_logical_sha256"],"config":config_hash,"fold_plan":fold_plan_identity}),
                  "config_hash":config_hash,"config_parts":config_parts,"fold_plan_identity":fold_plan_identity,
                  "prediction_artifact_sha256":sha256_file(new_m1_dir/"m1_oof_predictions.parquet"),
                  "coefficient_artifact_sha256":sha256_file(new_m1_dir/"m1_coefficients.json"),
                  "evaluation_artifact_sha256":sha256_file(new_m1_dir/"m1_result.json"),
                  "oof_logical_sha256":new_result["oof"]["logical_sha256"]},
        },
        "data_drag_conclusion":verdict,
        "next_step_recommendation":recommendation,
        "guardrails":{"authoritative_corrected_data_used":True,"automatic_merge":False},
    }

    # Human-readable compact report; JSON remains canonical full evidence.
    report = json_safe(report)
    (out/"comparison_report.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    md=[]
    md.append("# PHYSICAL_PROFILE_CORRECTED_M1_RERUN_V1_COMPLETE")
    md.append("")
    md.append(f"- DATA-drag conclusion: **{verdict}**")
    md.append(f"- Next step: **{recommendation}**")
    md.append(f"- Corrected F02 logical SHA: `{new_summary['predictor_logical_sha256']}`")
    md.append(f"- F02 changed rows/cells/columns: **{int(row_changed.sum())} / {total_changed_cells} / {len(changed_by_col)}**")
    md.append("")
    md.append("## Aggregate M1")
    md.append("")
    md.append("| Metric | Old M1 | Corrected-DATA M1 | Absolute Δ | Relative Δ |")
    md.append("|---|---:|---:|---:|---:|")
    for k in ("log_loss","brier","accuracy","auc"):
        relative = aggregate["relative_delta"][k]
        md.append(
            f"| {k} | {markdown_number(old_agg.get(k))} | {markdown_number(new_agg.get(k))} | "
            f"{markdown_number(d.get(k), '+.9f')} | {markdown_number(relative, '+.4%')} |"
        )
    md.append("")
    md.append("## 2026 partial")
    md.append("")
    md.append(f"- n: {deep2026['n']}")
    md.append(f"- LL: {markdown_number(deep2026['old'].get('log_loss'))} → {markdown_number(deep2026['corrected'].get('log_loss'))} ({markdown_number(deep2026['delta'].get('log_loss'), '+.9f')})")
    md.append(f"- Brier: {markdown_number(deep2026['old'].get('brier'))} → {markdown_number(deep2026['corrected'].get('brier'))} ({markdown_number(deep2026['delta'].get('brier'), '+.9f')})")
    md.append(f"- Accuracy: {markdown_number(deep2026['old'].get('accuracy'), '.4%')} → {markdown_number(deep2026['corrected'].get('accuracy'), '.4%')}")
    md.append(f"- AUC: {markdown_number(deep2026['old'].get('auc'))} → {markdown_number(deep2026['corrected'].get('auc'))}")
    md.append(f"- Predictor rows changed: {deep2026['predictor_rows_changed']}")
    md.append(f"- Mean/median/max |Δp|: {deep2026['mean_absolute_probability_shift']:.6f} / {deep2026['median_absolute_probability_shift']:.6f} / {deep2026['max_absolute_probability_shift']:.6f}")
    md.append("")
    md.append("## Reach missingness term")
    md.append("")
    md.append(f"- Old mean coefficient: {reach_old['mean']:.9f}; corrected: {reach_new['mean']:.9f}")
    md.append(f"- Old nonzero prevalence: {missingness['reach_missing_diff_oof']['old']['prevalence']:.4%}; corrected: {missingness['reach_missing_diff_oof']['corrected']['prevalence']:.4%}")
    md.append("")
    md.append("Full fold/year/affected-row/coefficient/calibration evidence is in `comparison_report.json`.")
    (out/"comparison_report.md").write_text("\n".join(md)+"\n",encoding="utf-8")

    print(json.dumps(json_safe({
        "status":report["status"],
        "data_drag_conclusion":verdict,
        "next_step_recommendation":recommendation,
        "aggregate":aggregate,
        "deep_2026":{k:deep2026[k] for k in ("n","old","corrected","delta","predictor_rows_changed","m1_input_rows_changed","mean_absolute_probability_shift","median_absolute_probability_shift","max_absolute_probability_shift")},
        "f02_changed_rows":int(row_changed.sum()),
        "f02_changed_cells":total_changed_cells,
        "f02_changed_columns":len(changed_by_col),
        "corrected_f02_sha":new_summary["predictor_logical_sha256"],
        "corrected_m1_oof_sha":new_result["oof"]["logical_sha256"],
    }),indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
