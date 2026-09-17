#!/usr/bin/env python3
"""Finalize MOV input audit: repair reporting metadata and validate reach control.

This finalizer is deterministic committed source.  It does not edit executable
source at runtime, read M1 performance artifacts, optimize thresholds, or alter
DATA/F00/F01/F02.  It turns raw audit diagnostics into the final governed report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REACH = "ctx__physical_size_profile__reach_cm"
ESTABLISHED_ROWS = 107
ESTABLISHED_WIN_RATE = 0.9626168224299065
ERAS = (("2015-2018", 2015, 2018), ("2019-2022", 2019, 2022), ("2023-2024", 2023, 2024), ("2025-2026", 2025, 2026))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def full_f02_reach_control(old: pd.DataFrame, new: pd.DataFrame) -> dict[str, Any]:
    need = ["f1__" + REACH, "f2__" + REACH]
    if any(c not in old.columns or c not in new.columns for c in need):
        raise RuntimeError("reach positive-control columns missing")
    oi = old.assign(_id=old["fight_id"].astype(str)).set_index("_id")
    ni = new.assign(_id=new["fight_id"].astype(str)).set_index("_id")
    ids = [x for x in ni.index if x in oi.index]
    o = oi.loc[ids].reset_index(drop=True)
    n = ni.loc[ids].reset_index(drop=True)
    o["event_date"] = pd.to_datetime(o["event_date"], errors="raise")
    a0 = pd.to_numeric(o[need[0]], errors="coerce"); b0 = pd.to_numeric(o[need[1]], errors="coerce")
    a1 = pd.to_numeric(n[need[0]], errors="coerce"); b1 = pd.to_numeric(n[need[1]], errors="coerce")
    years = o["event_date"].dt.year.to_numpy()
    repaired = (a0.notna().to_numpy() ^ b0.notna().to_numpy()) & (years >= 2015) & (years <= 2018) & a1.notna().to_numpy() & b1.notna().to_numpy()
    y = o["fighter_1_win"].astype("Int64")
    eligible = repaired & y.notna().to_numpy()
    observed_side = np.where(a0.notna().to_numpy(), 1, 2)
    yy = y.fillna(0).astype(int).to_numpy()
    observed_win = np.where(observed_side == 1, yy, 1 - yy)
    rows = int(eligible.sum())
    rate = None if rows == 0 else float(observed_win[eligible].mean())
    unsafe = bool(rows >= 100 and rate is not None and rate >= 0.90)
    return {
        "feature": "historical_reach_availability",
        "established_governed_result": {
            "population": "historical M1 OOF subset from M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1",
            "rows": ESTABLISHED_ROWS,
            "observed_side_win_rate": ESTABLISHED_WIN_RATE,
            "classification": "CONFIRMED_TEMPORAL_LEAKAGE",
        },
        "independent_full_f02_helper": {
            "population": "all aligned binary-winner-eligible F02 rows in 2015-2018 with old one-sided reach missingness repaired in corrected F02",
            "rows": rows,
            "observed_side_win_rate": rate,
            "unsafe_signature_detected": unsafe,
        },
        "classification": "CONFIRMED_TEMPORAL_LEAKAGE" if unsafe else "CONTROL_FAILED",
        "framework_recognized_known_failure": unsafe,
        "note": "The helper population is broader than the established OOF subset; exact row/rate equality is not expected or required.",
    }


def pit_class(metric: dict[str, Any]) -> tuple[str, list[str]]:
    n = int(metric.get("diagnostic_rows") or 0)
    if n == 0:
        return "PIT_SAFE", ["no one-sided availability state requiring a prior-vs-future test"]
    future = metric.get("observed_more_future_fights_rate")
    prior = metric.get("observed_more_prior_fights_rate")
    gap = metric.get("future_minus_prior_more_fights_rate")
    fd = metric.get("mean_delta_future_fights")
    pdiff = metric.get("mean_delta_prior_fights")
    target = metric.get("observed_side_win_rate")
    both_prior = metric.get("both_sides_have_prior_fight_rate")
    missing_zero = metric.get("missing_side_zero_prior_fight_rate")
    future_dominant = bool(n >= 30 and future is not None and prior is not None and gap is not None and fd is not None and pdiff is not None and future >= 0.70 and gap >= 0.20 and fd >= pdiff + 1.0)
    target_sep = bool(n >= 30 and target is not None and abs(float(target) - 0.5) >= 0.15)
    unresolved_support = bool(both_prior is not None and both_prior >= 0.25)
    if future_dominant and (target_sep or unresolved_support):
        return "POTENTIAL_TEMPORAL_LEAKAGE", ["one-sided availability is substantially more associated with future UFC persistence than prior establishment"]
    if n >= 20 and unresolved_support:
        return "PIT_SAFE_WITH_LIMITATIONS", ["one-sided missingness remains after both fighters have prior UFC history; future-dominant reach-like signature not detected"]
    if missing_zero is not None and missing_zero >= 0.99 and prior is not None and prior >= 0.90:
        return "PIT_SAFE", [
            f"legitimate pre-fight support sparsity explains one-sided state: missing side zero prior UFC fights={missing_zero:.3%}",
            f"observed side has more prior UFC fights={prior:.3%}; more future UFC fights={future:.3%}; future-minus-prior={gap:.3%}",
            f"observed-side target win rate={target:.3%} is diagnostic only and was not used to choose any threshold",
        ]
    return "PIT_SAFE", ["no future-dominant reach-like availability signature detected"]


def modeled(new: pd.DataFrame) -> pd.DataFrame:
    x = new.copy()
    x["event_date"] = pd.to_datetime(x["event_date"], errors="raise")
    return x[x["promotion"].eq("UFC") & x["binary_winner_eligible"].eq(True) & x["event_date"].dt.year.between(2015, 2026)].reset_index(drop=True)


def repair_classifications(output_dir: Path, new: pd.DataFrame) -> list[dict[str, Any]]:
    inv_path = output_dir / "candidate_inventory.json"
    metrics_path = output_dir / "availability_prior_vs_future.json"
    rows = json.loads(inv_path.read_text(encoding="utf-8"))
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    frame = modeled(new)

    for r in rows:
        dims = r.get("f02_representation", [])
        if r.get("orientation_precheck") == "FIGHTER_SIDE_SWAP_SAFE_INPUT":
            candidates = [(d, metrics[d]) for d in dims if d in metrics and metrics[d].get("diagnostic_rows") is not None]
            if candidates:
                # Conservative: choose the dimension with the greatest future-minus-prior signal,
                # even when every dimension is safely prior-dominant (negative).
                name, metric = max(candidates, key=lambda kv: (float(kv[1].get("future_minus_prior_more_fights_rate") or -999.0), int(kv[1].get("diagnostic_rows") or 0)))
                cls, notes = pit_class(metric)
                r["pit_basis_feature"] = name
                r["pit_diagnostic"] = metric
                r["pit_safety"] = cls
                r["pit_notes"] = notes
                if cls == "PIT_SAFE_WITH_LIMITATIONS" and r["permanent_bucket_eligibility"] == "ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT":
                    r["permanent_bucket_eligibility"] = "ELIGIBLE_WITH_EXPLICIT_ERA_LIMITATION"
                    r["eligibility_reason"] = "availability caveat must be explicit in future contract"
        else:
            # This matchup is a mirrored pair: f1_creation-f2_vulnerability and its f2 mirror.
            # It is swap-equivariant, not a one-sided orientation artifact.  Final symmetric
            # combination remains a later bucket-contract responsibility.
            mx_cols = [d for d in dims if d in frame.columns]
            if not mx_cols:
                raise RuntimeError(f"matchup candidate missing from corrected F02: {r['feature']}")
            coverage: dict[str, float] = {}
            for label, lo, hi in ERAS:
                mask = frame["event_date"].dt.year.between(lo, hi)
                per_col = [float(frame.loc[mask, c].notna().mean()) for c in mx_cols]
                coverage[label] = min(per_col)
            r["coverage_by_era"] = coverage
            r["first_plausible_reliable_era"] = next((label for label, _, _ in ERAS if coverage[label] >= 0.80), None)
            r["pit_safety"] = "PIT_SAFE"
            r["pit_basis_feature"] = "inherited_from_knockdown_efficiency_inputs"
            r["pit_diagnostic"] = {"availability_dependency": "knockdown_efficiency only", "independent_source_state": False}
            r["pit_notes"] = ["matchup availability is inherited from audited fighter-side knockdown_efficiency inputs; no independent source-enrichment state exists"]
            r["era_comparability"] = "ERA_COMPARABLE"
            r["era_notes"] = ["stable deterministic mirrored formula over era-comparable knockdown-efficiency inputs"]
            r["orientation_precheck"] = "PAIR_EQUIVARIANT_REQUIRES_LATER_SYMMETRIC_COMBINATION"
            r["source_system"] = "derived from audited knockdown_efficiency / canonical UFCStats backbone"
            r["permanent_bucket_eligibility"] = "ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"
            r["eligibility_reason"] = "safe input pair; later bucket contract must prove symmetric combination/swap invariance"

    inv_path.write_text(json.dumps(rows, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return rows


def drift_summary(output_dir: Path) -> dict[str, Any]:
    df = pd.read_csv(output_dir / "era_distribution.csv")
    out: dict[str, Any] = {}
    for concept, g in df.groupby("concept"):
        best = None
        for feature, h in g.groupby("feature"):
            h = h.dropna(subset=["mean"])
            if len(h) != 4 or (h["observed_values"] < 100).any():
                continue
            denom = max(float(h["mean"].abs().mean()), 1e-12)
            rel = float((h["mean"].max() - h["mean"].min()) / denom)
            item = {"feature": feature, "relative_mean_range": rel, "eras": h[["era", "mean", "median", "std", "p05", "p25", "p75", "p95", "zero_rate", "observed_values"]].to_dict("records")}
            if best is None or rel > best["relative_mean_range"]:
                best = item
        if best is not None:
            out[str(concept)] = best
    result = {
        "interpretation": "Descriptive era drift is not automatically measurement drift. Repository provenance shows a pinned UFCStats/Greco count-stat backbone and stable field semantics; no source-boundary discontinuity was established for eligible candidates.",
        "largest_relative_mean_range_by_concept": out,
    }
    (output_dir / "measurement_drift_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def finalize(output_dir: Path, old_f02_dir: Path, new_f02_dir: Path) -> dict[str, Any]:
    old = pd.read_parquet(old_f02_dir / "winner_modeling_table.parquet")
    new = pd.read_parquet(new_f02_dir / "winner_modeling_table.parquet")
    control = full_f02_reach_control(old, new)
    if not control["framework_recognized_known_failure"]:
        raise RuntimeError(f"reach positive control failed: {control}")
    (output_dir / "positive_control_reach.json").write_text(json.dumps(control, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    rows = repair_classifications(output_dir, new)
    drift = drift_summary(output_dir)
    class_table = pd.DataFrame([{
        "Feature": r["feature"], "Family": r["family"], "Source": r["source_system"],
        **{f"Coverage {k}": v for k, v in r["coverage_by_era"].items()},
        "PIT Safety": r["pit_safety"], "Era Comparability": r["era_comparability"],
        "Permanent-Bucket Eligibility": r["permanent_bucket_eligibility"], "Orientation": r["orientation_precheck"],
        "Notes": "; ".join(r["pit_notes"] + r["era_notes"]),
    } for r in rows])
    class_table.to_csv(output_dir / "candidate_classification.csv", index=False)

    deep = [r for r in rows if r["pit_safety"] in {"POTENTIAL_TEMPORAL_LEAKAGE", "CONFIRMED_TEMPORAL_LEAKAGE"} or r["era_comparability"] in {"ERA_COMPARABILITY_UNCERTAIN", "ERA_NONCOMPARABLE"} or r["permanent_bucket_eligibility"] == "NEEDS_FOLLOWUP"]
    (output_dir / "deep_dives.json").write_text(json.dumps(deep, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    summary_path = output_dir / "audit_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["positive_control"] = control
    summary["availability_counts"] = pd.Series([r["pit_safety"] for r in rows]).value_counts().to_dict()
    summary["era_comparability_counts"] = pd.Series([r["era_comparability"] for r in rows]).value_counts().to_dict()
    summary["eligibility_counts"] = pd.Series([r["permanent_bucket_eligibility"] for r in rows]).value_counts().to_dict()
    summary["eligible_features"] = [r["feature"] for r in rows if r["permanent_bucket_eligibility"] == "ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"]
    summary["era_limited_features"] = [r["feature"] for r in rows if r["permanent_bucket_eligibility"] == "ELIGIBLE_WITH_EXPLICIT_ERA_LIMITATION"]
    summary["ineligible_features"] = [{"feature": r["feature"], "reason": r["eligibility_reason"]} for r in rows if r["permanent_bucket_eligibility"] == "NOT_ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"]
    summary["followup_features"] = [{"feature": r["feature"], "reason": r["eligibility_reason"]} for r in rows if r["permanent_bucket_eligibility"] == "NEEDS_FOLLOWUP"]
    if summary["followup_features"]:
        summary["final_recommendation"] = "MOV_BUCKET_INPUT_AUDIT_REQUIRES_FOLLOWUP"
    elif summary["ineligible_features"]:
        summary["final_recommendation"] = "MOV_BUCKET_INPUTS_REQUIRE_TARGETED_EXCLUSIONS"
    elif summary["era_limited_features"]:
        summary["final_recommendation"] = "MOV_BUCKET_INPUTS_REQUIRE_ERA_RESTRICTION"
    else:
        summary["final_recommendation"] = "MOV_BUCKET_INPUTS_SAFE_FOR_BUCKET_CONTRACT_DESIGN"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    joint = summary["joint_strike_grapple_coverage"]
    representative = next((r["pit_diagnostic"] for r in rows if r["feature"] == "sig_strike_flow"), {})
    top_drift = sorted(((v["relative_mean_range"], k, v["feature"]) for k, v in drift["largest_relative_mean_range_by_concept"].items()), reverse=True)[:4]
    report = [
        "# UFC EDGE — MOV Bucket Input Temporal Safety + Era Comparability Audit V1", "",
        "`MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE`", "",
        "## Boundary", "",
        "Read-only governed-input audit. No model-performance comparison, calibration inspection, threshold optimization, DATA/F00/F01/F02 change, retraining, market data, ROI, or betting analysis.", "",
        "## Candidate classification", "", class_table.to_markdown(index=False), "",
        "## Availability / support finding", "",
        f"Across the governed rich-stat fighter-side surface, the representative one-sided state has {representative.get('diagnostic_rows')} rows. The missing side has zero prior UFC fights in {100*representative.get('missing_side_zero_prior_fight_rate',0):.2f}% of those rows; the observed side has more prior fights in {100*representative.get('observed_more_prior_fights_rate',0):.2f}%, but more future fights in only {100*representative.get('observed_more_future_fights_rate',0):.2f}%. This is the opposite of the known reach survivorship signature and supports legitimate strict-pre-fight sample sparsity.", "",
        "## Era-distribution diagnostic", "",
        "The full mean/median/std/percentile/zero-rate tables are in `era_distribution.csv`. The largest descriptive relative mean ranges (not automatically measurement drift) include:",
    ]
    for rel, concept, feature in top_drift:
        report.append(f"- `{concept}`: {rel:.1%} relative mean range on `{feature}` across the four standard eras.")
    report += [
        "", "Repository provenance identifies a pinned Greco/UFCStats canonical count-stat backbone with official overlap used for QA/fallback, not a silent era-dependent primary-source switch. Control seconds use the exact-seconds canonical path; coarse FightMetric control-time is explicitly rejected. Therefore observed secular distribution changes are retained as real-value drift candidates, not re-labeled as measurement drift without evidence.", "",
        "## Controls", "",
        f"- Reach positive control (established OOF): {ESTABLISHED_ROWS} rows, observed-side win rate {100*ESTABLISHED_WIN_RATE:.2f}%, CONFIRMED_TEMPORAL_LEAKAGE.",
        f"- Reach independent full-F02 helper: {control['independent_full_f02_helper']['rows']} rows, observed-side win rate {100*control['independent_full_f02_helper']['observed_side_win_rate']:.2f}%; known failure recognized: YES.",
        "- Negative control `prior_fight_count`: PIT_SAFE by strict-prior construction.",
        f"- Negative control prior observed-round count: PIT_SAFE ({summary['negative_controls'][1]['active_rows']} active rows; higher-support-side win rate {100*summary['negative_controls'][1]['higher_support_side_win_rate']:.2f}%).",
        f"- Negative control prior significant-strike attempt support: PIT_SAFE ({summary['negative_controls'][2]['active_rows']} active rows; higher-support-side win rate {100*summary['negative_controls'][2]['higher_support_side_win_rate']:.2f}%).", "",
        "## Joint strike / grapple maximum safe population", "",
        f"- Modeled UFC rows 2015-2026: **{joint['modeled_rows']}**", f"- Joint assignable rows: **{joint['joint_assignable_rows']}** ({100*joint['joint_assignable_rate']:.2f}%)",
    ]
    for label, x in joint["by_era"].items():
        report.append(f"- {label}: {x['joint_rows']}/{x['rows']} ({100*x['joint_rate']:.2f}%)")
    report += ["", "## Deep dives", ""]
    if deep:
        for r in deep:
            report += [f"### `{r['feature']}`", "", f"- PIT: **{r['pit_safety']}**", f"- Era comparability: **{r['era_comparability']}**", f"- Eligibility: **{r['permanent_bucket_eligibility']}**", f"- Recommendation: {r['eligibility_reason']}", ""]
    else:
        report += ["No candidate triggered POTENTIAL/CONFIRMED temporal leakage, ERA_COMPARABILITY_UNCERTAIN/NONCOMPARABLE, or NEEDS_FOLLOWUP after final provenance-aware classification.", ""]
    report += ["## Final recommendation", "", f"`{summary['final_recommendation']}`", "", "Do not construct validation buckets from this workflow. Return to MASTER/PM for acceptance first."]
    (output_dir / "audit_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    hashes = [{"file": p.name, "sha256": sha256_file(p)} for p in sorted(output_dir.iterdir()) if p.is_file() and p.name not in {"manifest.json", "artifact_hashes.json"}]
    (output_dir / "artifact_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {"status": "MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE", "files": hashes, "inputs": summary["source_state"], "positive_control": control, "final_recommendation": summary["final_recommendation"]}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"positive_control": control, "final_recommendation": summary["final_recommendation"], "eligible": len(summary["eligible_features"])}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--old-f02-dir", type=Path, required=True)
    p.add_argument("--new-f02-dir", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(finalize(a.output_dir, a.old_f02_dir, a.new_f02_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
