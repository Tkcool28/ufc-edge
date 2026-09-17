#!/usr/bin/env python3
"""Read-only diagnostic for the corrected physical-profile M1 experiment.

Consumes frozen old/corrected F02 and M1 artifacts only. No training, tuning,
feature changes, or methodology changes are performed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import log_loss

REACH_MISSING_TERM = "pair::ctx__physical_size_profile__reach_cm::missing_diff"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--old-f02-dir", type=Path, required=True)
    p.add_argument("--new-f02-dir", type=Path, required=True)
    p.add_argument("--old-m1-dir", type=Path, required=True)
    p.add_argument("--new-m1-dir", type=Path, required=True)
    p.add_argument("--feature-surface", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()


def load_json(path):
    return json.loads(path.read_text())


def equal(a, b):
    av, bv = a.to_numpy(), b.to_numpy()
    return (pd.isna(av) & pd.isna(bv)) | np.asarray(av == bv, dtype=bool)


def source_columns(surface):
    cols = []
    for keys in surface["paired_fighter_predictors"]["concepts"].values():
        for key in keys:
            cols += [f"f1__{key}", f"f2__{key}"]
    for item in surface["matchup_predictors"]["review"]:
        if item["accepted"]:
            cols += item["columns"]
    if len(cols) != 197:
        raise RuntimeError(f"expected 197 frozen M1 source columns, got {len(cols)}")
    return cols


def row_log_loss(y, p):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def candidate_margin(fold):
    scores = sorted(fold["inner_scores"], key=lambda x: (float(x["inner_log_loss"]), int(x["grid_index"])))
    return float(scores[1]["inner_log_loss"] - scores[0]["inner_log_loss"])


def coefficient_map(path):
    payload = load_json(path)
    out = {}
    for fold in payload:
        out[str(fold["fold_id"])] = {r["feature"]: float(r["coefficient"]) for r in fold["coefficients"]}
    return out


def main():
    a = parse_args()
    a.output_dir.mkdir(parents=True, exist_ok=True)

    old_f02 = pd.read_parquet(a.old_f02_dir / "winner_modeling_table.parquet")
    new_f02 = pd.read_parquet(a.new_f02_dir / "winner_modeling_table.parquet")
    if old_f02["fight_id"].tolist() != new_f02["fight_id"].tolist():
        raise RuntimeError("F02 fight population/order changed")

    surface = load_json(a.feature_surface)
    changed = np.zeros(len(old_f02), dtype=bool)
    for col in source_columns(surface):
        changed |= ~equal(old_f02[col], new_f02[col])
    changed_map = pd.Series(changed, index=old_f02["fight_id"]).to_dict()

    old_oof = pd.read_parquet(a.old_m1_dir / "m1_oof_predictions.parquet")
    new_oof = pd.read_parquet(a.new_m1_dir / "m1_oof_predictions.parquet")
    old_result = load_json(a.old_m1_dir / "m1_result.json")
    new_result = load_json(a.new_m1_dir / "m1_result.json")

    old = old_oof.rename(columns={"m1_probability": "old_probability"})
    new = new_oof[["fight_id", "event_date", "fold_id", "target", "m1_probability"]].rename(columns={
        "event_date": "new_event_date", "fold_id": "new_fold_id", "target": "new_target", "m1_probability": "new_probability"
    })
    joined = old.merge(new, on="fight_id", validate="one_to_one")
    if len(joined) != len(old_oof) or not np.array_equal(joined["target"], joined["new_target"]):
        raise RuntimeError("M1 OOF population/labels changed")
    joined["year"] = pd.to_datetime(joined["event_date"]).dt.year
    joined["affected"] = joined["fight_id"].map(changed_map).fillna(False).astype(bool)
    joined["old_ll"] = row_log_loss(joined["target"], joined["old_probability"])
    joined["new_ll"] = row_log_loss(joined["target"], joined["new_probability"])
    joined["ll_delta"] = joined["new_ll"] - joined["old_ll"]
    joined["prob_delta"] = joined["new_probability"] - joined["old_probability"]
    joined["toward_truth"] = joined["ll_delta"] < 0

    physical = old_f02[[
        "fight_id", "event_date",
        "f1__ctx__physical_size_profile__reach_cm",
        "f2__ctx__physical_size_profile__reach_cm",
    ]].copy()
    physical["old_reach_missing_diff"] = (
        physical["f1__ctx__physical_size_profile__reach_cm"].isna().astype(int)
        - physical["f2__ctx__physical_size_profile__reach_cm"].isna().astype(int)
    )
    joined = joined.merge(physical[["fight_id", "old_reach_missing_diff"]], on="fight_id", validate="one_to_one")

    years = []
    for year, g in joined.groupby("year", sort=True):
        affected = g[g["affected"]]
        unaffected = g[~g["affected"]]
        def ll(frame, col):
            return None if frame.empty else float(log_loss(frame["target"], frame[col], labels=[0, 1]))
        years.append({
            "year": int(year),
            "n": int(len(g)),
            "affected_n": int(len(affected)),
            "delta_log_loss": float(ll(g, "new_probability") - ll(g, "old_probability")),
            "affected_delta_log_loss": None if affected.empty else float(ll(affected, "new_probability") - ll(affected, "old_probability")),
            "unaffected_delta_log_loss": None if unaffected.empty else float(ll(unaffected, "new_probability") - ll(unaffected, "old_probability")),
            "affected_toward_truth_rate": None if affected.empty else float(affected["toward_truth"].mean()),
            "affected_mean_abs_probability_delta": None if affected.empty else float(affected["prob_delta"].abs().mean()),
            "total_log_loss_contribution_delta": float(g["ll_delta"].sum()),
            "affected_log_loss_contribution_delta": float(affected["ll_delta"].sum()),
            "unaffected_log_loss_contribution_delta": float(unaffected["ll_delta"].sum()),
        })

    eligible = old_f02["binary_winner_eligible"].astype(bool)
    f02_dates = pd.to_datetime(old_f02["event_date"])
    old_folds = {str(f["fold_id"]): f for f in old_result["folds"]}
    new_folds = {str(f["fold_id"]): f for f in new_result["folds"]}
    old_coeff = coefficient_map(a.old_m1_dir / "m1_coefficients.json")
    new_coeff = coefficient_map(a.new_m1_dir / "m1_coefficients.json")
    folds = []
    for fold_id, old_fold in old_folds.items():
        new_fold = new_folds[fold_id]
        train = eligible & f02_dates.between(pd.Timestamp(old_fold["train_start"]), pd.Timestamp(old_fold["train_end"]))
        valid = eligible & f02_dates.between(pd.Timestamp(old_fold["validation_start"]), pd.Timestamp(old_fold["validation_end"]))
        folds.append({
            "fold_id": fold_id,
            "changed_train_rows": int((changed & train.to_numpy()).sum()),
            "changed_validation_rows": int((changed & valid.to_numpy()).sum()),
            "old_selected_candidate": old_fold["selected_candidate"],
            "new_selected_candidate": new_fold["selected_candidate"],
            "selection_changed": old_fold["selected_candidate"] != new_fold["selected_candidate"],
            "old_selection_margin": candidate_margin(old_fold),
            "new_selection_margin": candidate_margin(new_fold),
            "delta_log_loss": float(new_fold["m1"]["log_loss"] - old_fold["m1"]["log_loss"]),
            "old_reach_missing_coefficient": old_coeff[fold_id][REACH_MISSING_TERM],
            "new_reach_missing_coefficient": new_coeff[fold_id][REACH_MISSING_TERM],
        })

    eras = []
    for lo, hi, label in [(2015, 2018, "2015-2018"), (2019, 2024, "2019-2024"), (2025, 2026, "2025-2026")]:
        g = joined[joined["year"].between(lo, hi) & joined["affected"]]
        states = []
        for state, s in g.groupby("old_reach_missing_diff", sort=True):
            states.append({
                "missing_diff": int(state), "n": int(len(s)), "fighter1_win_rate": float(s["target"].mean()),
                "old_mean_probability": float(s["old_probability"].mean()), "new_mean_probability": float(s["new_probability"].mean()),
                "old_log_loss": float(log_loss(s["target"], s["old_probability"], labels=[0, 1])),
                "new_log_loss": float(log_loss(s["target"], s["new_probability"], labels=[0, 1])),
            })
        eras.append({"era": label, "n": int(len(g)), "toward_truth_rate": None if g.empty else float(g["toward_truth"].mean()), "states": states})

    year_df = pd.DataFrame(years)
    diagnosis = {
        "early_2015_2018_contribution_delta": float(year_df.loc[year_df.year.between(2015, 2018), "total_log_loss_contribution_delta"].sum()),
        "middle_2019_2024_contribution_delta": float(year_df.loc[year_df.year.between(2019, 2024), "total_log_loss_contribution_delta"].sum()),
        "recent_2025_2026_contribution_delta": float(year_df.loc[year_df.year.between(2025, 2026), "total_log_loss_contribution_delta"].sum()),
        "affected_rows_contribution_delta": float(joined.loc[joined.affected, "ll_delta"].sum()),
        "unaffected_refit_spillover_contribution_delta": float(joined.loc[~joined.affected, "ll_delta"].sum()),
        "folds_with_candidate_change": [f["fold_id"] for f in folds if f["selection_changed"]],
    }

    worst = joined[joined.affected].nlargest(20, "ll_delta")[["fight_id", "event_date", "year", "target", "old_probability", "new_probability", "ll_delta", "old_reach_missing_diff"]]
    best = joined[joined.affected].nsmallest(20, "ll_delta")[["fight_id", "event_date", "year", "target", "old_probability", "new_probability", "ll_delta", "old_reach_missing_diff"]]
    report = {
        "status": "M1_PHYSICAL_PROFILE_CORRECTION_DIAGNOSTIC_V1_COMPLETE",
        "guardrail": "READ_ONLY_NO_RETRAINING_NO_METHOD_CHANGE",
        "diagnosis": diagnosis,
        "year_decomposition": years,
        "fold_mechanics": folds,
        "missingness_by_era": eras,
        "largest_harmful_direct_shifts": worst.to_dict("records"),
        "largest_helpful_direct_shifts": best.to_dict("records"),
    }
    (a.output_dir / "diagnostic_report.json").write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    year_df.to_csv(a.output_dir / "year_decomposition.csv", index=False)
    pd.DataFrame(folds).to_csv(a.output_dir / "fold_mechanics.csv", index=False)
    joined.to_csv(a.output_dir / "oof_diagnostic_rows.csv", index=False)

    lines = ["# M1 Physical-Profile Correction Diagnostic V1", "", f"Status: `{report['status']}`", "",
             "| Year | Affected | ΔLL | Affected ΔLL | Unaffected ΔLL | Toward truth |", "|---:|---:|---:|---:|---:|---:|"]
    for r in years:
        truth = "n/a" if r["affected_toward_truth_rate"] is None else f"{100*r['affected_toward_truth_rate']:.1f}%"
        ad = "n/a" if r["affected_delta_log_loss"] is None else f"{r['affected_delta_log_loss']:+.6f}"
        ud = "n/a" if r["unaffected_delta_log_loss"] is None else f"{r['unaffected_delta_log_loss']:+.6f}"
        lines.append(f"| {r['year']} | {r['affected_n']}/{r['n']} | {r['delta_log_loss']:+.6f} | {ad} | {ud} | {truth} |")
    lines += ["", "## Contribution totals", "",
              f"- 2015-2018: **{diagnosis['early_2015_2018_contribution_delta']:+.6f}**",
              f"- 2019-2024: **{diagnosis['middle_2019_2024_contribution_delta']:+.6f}**",
              f"- 2025-2026: **{diagnosis['recent_2025_2026_contribution_delta']:+.6f}**",
              f"- Directly affected rows: **{diagnosis['affected_rows_contribution_delta']:+.6f}**",
              f"- Unaffected/refit spillover: **{diagnosis['unaffected_refit_spillover_contribution_delta']:+.6f}**",
              f"- Candidate-selection changes: **{', '.join(diagnosis['folds_with_candidate_change']) or 'none'}**",
              "", "Positive ΔLL is worse; negative ΔLL is better."]
    (a.output_dir / "diagnostic_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
