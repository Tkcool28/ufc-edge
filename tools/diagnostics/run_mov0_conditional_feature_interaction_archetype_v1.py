#!/usr/bin/env python3
"""Post-freeze descriptive interaction diagnostic over immutable MOV0 OOFs.

This program deliberately never imports, fits, or calls the MOV0 estimator.  It
only verifies the two frozen OOF files, joins pre-fight F02 predictor states and
the permanent terrain, then describes preregistered fight-level archetypes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

STATUS = "MOV0_CONDITIONAL_FEATURE_INTERACTION_ARCHETYPE_DIAGNOSTIC_V1_COMPLETE"
SOURCE_HEAD = "dd4e7de7de4baa24090388fcf845c996564f2bf8"
WORKFLOW_RUN = 35376956316
ARTIFACT_ID = 10561085362
F02_SHA = "d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580"
TERRAIN_SHA = "d3358cfc468a791861ee6fb87473f119f949d705c54abfcb504d9ebbecdcb5d2"
OOF_SHA = {
    "MOV0_MIN": "786bee7cce8a41eed6a8e7f82fe031a592ed081a10b3a97f85afc31be61d1c57",
    "MOV0_FULL": "9d543356b157fefaabe27f7f4d1b5663536e4cf659fdf11fedd8531c4b13faa0",
}
BUCKETS = [("<0.30", -np.inf, .30), ("0.30–<0.40", .30, .40), ("0.40–<0.50", .40, .50), ("0.50–<0.60", .50, .60), ("0.60–<0.70", .60, .70), (">=0.70", .70, np.inf)]
TERRAIN_COLS = ["weight_class", "scheduled_duration_bucket", "striking_environment", "grappling_environment", "experience_bucket", "layoff_bucket", "completeness_tier"]
WEIGHT_CLASSES = ["Heavyweight", "Light Heavyweight", "Flyweight"]

# The values are selected solely by pre-fight predictor semantics, before any
# OOF outcome is joined.  All use the complete 2015+ corrected F02 predictor
# table, pooled across both fighters, and fixed 33rd/67th percentiles.
CONCEPTS = {
    "kd_creation": "fs__knockdown_rate__created_per_15__career__shrunk",
    "kd_vulnerability": "fs__knockdown_rate__allowed_per_15__career__shrunk",
    "strike_defense": "fs__sig_strike_efficiency__defense__career__shrunk",
    "strike_accuracy": "fs__sig_strike_efficiency__accuracy__career__shrunk",
    "strike_absorbed": "fs__sig_strike_flow__absorbed_per_min__career__shrunk",
    "strike_flow": "fs__sig_strike_flow__landed_per_min__career__shrunk",
    "early_finish": "fs__early_finish_profile__r1_finish_win__career__shrunk",
    "ko_win_history": "fs__finish_method_win_profile__ko_tko__career__shrunk",
    "ko_loss_history": "fs__finish_method_loss_profile__ko_tko__career__shrunk",
    "td_pressure": "fs__takedown_pressure__created_per_15__career__shrunk",
    "td_conversion": "fs__takedown_conversion__success__career__shrunk",
    "td_defense": "fs__takedown_conversion__defense__career__shrunk",
    "sub_pressure": "fs__submission_attempt_rate__created_per_15__career__shrunk",
    "sub_vulnerability": "fs__submission_attempt_rate__faced_per_15__career__shrunk",
    "sub_win_history": "fs__finish_method_win_profile__submission__career__shrunk",
    "ground_share": "fs__sig_environment_mix__ground_share__career__shrunk",
    "experience": "fs__prior_fight_count__career__raw",
}

ARCHETYPES = [
    ("A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE", "striking", "A side has HIGH KD creation and opponent LOW strike defense."),
    ("A2_BOTH_HIGH_DAMAGE_EXCHANGE", "striking", "Both fighters have HIGH KD creation and HIGH significant-strike flow."),
    ("A3_ACCURACY_VS_ABSORPTION", "striking", "A side has HIGH striking accuracy and opponent HIGH significant-strike absorption."),
    ("A4_KO_HISTORY_VS_KO_VULNERABILITY", "striking", "A side has HIGH KO/TKO win history and opponent HIGH KO/TKO loss history."),
    ("B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE", "grappling", "A side has HIGH takedown pressure and opponent LOW takedown defense."),
    ("B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE", "grappling", "A side has HIGH takedown conversion and opponent LOW takedown defense."),
    ("B3_TD_ACCESS_PLUS_SUB_PRESSURE", "grappling", "A side has HIGH takedown pressure, HIGH takedown conversion, and HIGH submission pressure."),
    ("B4_SUB_PRESSURE_POOR_TD_ACCESS", "grappling", "A side has HIGH submission pressure but not HIGH takedown access (pressure and conversion are not both HIGH)."),
    ("B5_SUB_PRESSURE_VS_SUB_VULNERABILITY", "grappling", "A side has HIGH submission pressure and opponent HIGH submission attempts faced."),
    ("C1_DAMAGE_PLUS_SUBMISSION_ACCESS", "mixed", "A side has HIGH damaging-exchange creation and HIGH takedown access plus HIGH submission pressure."),
    ("C2_BOTH_HIGH_FINISH_HISTORY", "mixed", "Both fighters have HIGH finish history: HIGH KO/TKO or submission win history or HIGH early-finish history."),
    ("C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS", "mixed", "At least one side has HIGH finish history and the bout is scheduled for five rounds."),
    ("D1_LOW_DAMAGE_STRONG_DEFENSE", "survival", "Both fighters are LOW KD creation and HIGH striking defense."),
    ("D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE", "survival", "Both fighters lack HIGH takedown access and are LOW submission pressure."),
    ("D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE", "survival", "Both fighters are HIGH prior-fight experience and HIGH striking defense."),
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def gate(n: int) -> str:
    return "NORMAL" if n >= 100 else "MODERATE_UNCERTAINTY" if n >= 50 else "THIN_EXPLORATORY" if n >= 25 else "INSUFFICIENT"


def wilson(k: int, n: int) -> list[float]:
    z = 1.959963984540054
    p = k / n
    den = 1 + z*z/n
    c = (p + z*z/(2*n))/den
    d = z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return [float(c-d), float(c+d)]


def bucket(p: float) -> str:
    return next(label for label, lo, hi in BUCKETS if lo <= p < hi)


def side_state(frame: pd.DataFrame, f: int, thresholds: dict[str, dict[str, float]]) -> dict[str, pd.Series]:
    result: dict[str, pd.Series] = {}
    for name, suffix in CONCEPTS.items():
        col = f"f{f}__{suffix}"
        x = frame[col].astype(float)
        result[f"{name}_high"] = x >= thresholds[name]["high_p67"]
        result[f"{name}_low"] = x <= thresholds[name]["low_p33"]
    result["td_access_high"] = result["td_pressure_high"] & result["td_conversion_high"]
    result["damage_creation_high"] = result["kd_creation_high"] & result["strike_flow_high"]
    result["finish_history_high"] = result["ko_win_history_high"] | result["sub_win_history_high"] | result["early_finish_high"]
    return result


def qualify(frame: pd.DataFrame, a: dict[str, pd.Series], b: dict[str, pd.Series]) -> dict[str, pd.Series]:
    five = frame["scheduled_rounds"].astype(float).eq(5)
    directional = {
        "A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE": (a["kd_creation_high"] & b["strike_defense_low"], b["kd_creation_high"] & a["strike_defense_low"]),
        "A2_BOTH_HIGH_DAMAGE_EXCHANGE": (a["damage_creation_high"] & b["damage_creation_high"],) * 2,
        "A3_ACCURACY_VS_ABSORPTION": (a["strike_accuracy_high"] & b["strike_absorbed_high"], b["strike_accuracy_high"] & a["strike_absorbed_high"]),
        "A4_KO_HISTORY_VS_KO_VULNERABILITY": (a["ko_win_history_high"] & b["ko_loss_history_high"], b["ko_win_history_high"] & a["ko_loss_history_high"]),
        "B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE": (a["td_pressure_high"] & b["td_defense_low"], b["td_pressure_high"] & a["td_defense_low"]),
        "B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE": (a["td_conversion_high"] & b["td_defense_low"], b["td_conversion_high"] & a["td_defense_low"]),
        "B3_TD_ACCESS_PLUS_SUB_PRESSURE": (a["td_access_high"] & a["sub_pressure_high"], b["td_access_high"] & b["sub_pressure_high"]),
        "B4_SUB_PRESSURE_POOR_TD_ACCESS": (a["sub_pressure_high"] & ~a["td_access_high"], b["sub_pressure_high"] & ~b["td_access_high"]),
        "B5_SUB_PRESSURE_VS_SUB_VULNERABILITY": (a["sub_pressure_high"] & b["sub_vulnerability_high"], b["sub_pressure_high"] & a["sub_vulnerability_high"]),
        "C1_DAMAGE_PLUS_SUBMISSION_ACCESS": (a["damage_creation_high"] & a["td_access_high"] & a["sub_pressure_high"], b["damage_creation_high"] & b["td_access_high"] & b["sub_pressure_high"]),
        "C2_BOTH_HIGH_FINISH_HISTORY": (a["finish_history_high"] & b["finish_history_high"],) * 2,
        "C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS": (a["finish_history_high"] & five, b["finish_history_high"] & five),
        "D1_LOW_DAMAGE_STRONG_DEFENSE": (a["kd_creation_low"] & a["strike_defense_high"] & b["kd_creation_low"] & b["strike_defense_high"],) * 2,
        "D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE": (~a["td_access_high"] & a["sub_pressure_low"] & ~b["td_access_high"] & b["sub_pressure_low"],) * 2,
        "D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE": (a["experience_high"] & a["strike_defense_high"] & b["experience_high"] & b["strike_defense_high"],) * 2,
    }
    out = {}
    for name, (left, right) in directional.items():
        out[name] = left | right
        out[f"{name}__qualification"] = np.select([left & right, left | right], ["BOTH_SIDES", "ONE_SIDE"], default="NEITHER")
    return out


def composition(frame: pd.DataFrame, col: str) -> dict[str, Any]:
    return {str(k): {"N": int(v), "proportion": float(v / len(frame))} for k, v in frame[col].value_counts(dropna=False).sort_index().items()}


def archetype_record(frame: pd.DataFrame, name: str, family: str, definition: str) -> dict[str, Any]:
    x = frame[frame[name]].copy(); n = len(x); k = int(x.target.sum())
    if not n:
        return {"name": name, "family": family, "definition": definition, "N": 0, "sample_size_governance": gate(0)}
    mins, fulls = x.p_min.astype(float), x.p_full.astype(float)
    terrain = {c: composition(x, c) for c in TERRAIN_COLS}
    return {
        "name": name, "family": family, "definition": definition, "N": int(n), "finishes": k, "decisions": int(n-k), "finish_prevalence": float(k/n), "observed_finish_rate": float(k/n), "wilson_95": wilson(k, n), "sample_size_governance": gate(n),
        "mean_mov0_min_probability": float(mins.mean()), "mean_mov0_full_probability": float(fulls.mean()), "min_calibration_gap_observed_minus_predicted": float(x.target.mean()-mins.mean()), "full_calibration_gap_observed_minus_predicted": float(x.target.mean()-fulls.mean()),
        "dominant_mov0_confidence_bucket": str(x.full_bucket.value_counts().idxmax()), "full_probability_bucket_distribution": composition(x, "full_bucket"), "oof_year_coverage": sorted(map(int, x.year.unique())),
        "mean_delta_full_minus_min": float((fulls-mins).mean()), "median_delta_full_minus_min": float((fulls-mins).median()), "fraction_full_moved_upward": float((fulls > mins).mean()), "fraction_full_moved_downward": float((fulls < mins).mean()),
        "qualification_distribution": composition(x, f"{name}__qualification"), "terrain_composition": terrain,
        "weight_class_interactions": {wc: _simple_metrics(x[x.weight_class.eq(wc)]) for wc in WEIGHT_CLASSES if len(x[x.weight_class.eq(wc)])},
    }


def _simple_metrics(x: pd.DataFrame) -> dict[str, Any]:
    n=len(x); return {"N": int(n), "sample_size_governance": gate(n), "actual_finish_rate": float(x.target.mean()), "mean_min_probability": float(x.p_min.mean()), "mean_full_probability": float(x.p_full.mean())}


def report(records: list[dict[str, Any]], bucket_map: dict[str, Any], thresholds: dict[str, Any], source: dict[str, Any]) -> str:
    lines=["# MOV0 CONDITIONAL FEATURE INTERACTION + FIGHT ARCHETYPE DIAGNOSTIC V1", "", f"Status: **{STATUS}**", "", "## Scope and immutability", "", "This is a descriptive join over checked frozen OOF files. It does not import, fit, select, calibrate, or predict with MOV0. The F02 table supplies only pre-fight state labels; thresholds are predictor-only pooled 2015+ percentiles, set before OOF outcomes are joined.", "", "## Sources", ""]
    lines += [f"- {k}: `{v}`" for k,v in source.items()]
    lines += ["", "## Fixed state thresholds", "", "LOW is <= p33; HIGH is >= p67; MID is between. Thresholds are written in `feature_state_thresholds.json`.", "", "## Model says X / reality says Y", "", "| Fight archetype | N | Mean MIN p(finish) | Mean FULL p(finish) | Actual finish rate | Interpretation |", "|---|---:|---:|---:|---:|---|"]
    for r in records:
        if r["N"] >= 50:
            gap=r["full_calibration_gap_observed_minus_predicted"]
            interp="FULL aligned within 5pp" if abs(gap)<=.05 else ("FULL overpredicts" if gap < 0 else "FULL underpredicts")
            lines.append(f"| {r['name']} | {r['N']} | {r['mean_mov0_min_probability']:.1%} | {r['mean_mov0_full_probability']:.1%} | {r['observed_finish_rate']:.1%} | {interp}; {r['sample_size_governance']} |")
    lines += ["", "## All preregistered archetypes", ""]
    for r in records:
        lines += [f"### {r['name']}", "", f"{r['definition']}", "", f"N={r['N']} ({r['sample_size_governance']})."]
        if r["N"]: lines += [f"Observed {r['observed_finish_rate']:.1%} (Wilson 95% {r['wilson_95'][0]:.1%}–{r['wilson_95'][1]:.1%}); MIN {r['mean_mov0_min_probability']:.1%} (gap {r['min_calibration_gap_observed_minus_predicted']:+.1%}); FULL {r['mean_mov0_full_probability']:.1%} (gap {r['full_calibration_gap_observed_minus_predicted']:+.1%}). FULL−MIN mean {r['mean_delta_full_minus_min']:+.1%}, median {r['median_delta_full_minus_min']:+.1%}, up/down {r['fraction_full_moved_upward']:.1%}/{r['fraction_full_moved_downward']:.1%}.", ""]
    lines += ["## Broad bucket → archetype composition", "", "The JSON mapping reports overlapping family coverage for each immutable FULL probability bucket; a fight may match more than one pathway family.", ""]
    for b,v in bucket_map.items(): lines.append(f"- {b}: N={v['N']}; striking {v['family_match_proportion']['striking']:.1%}, grappling {v['family_match_proportion']['grappling']:.1%}, mixed {v['family_match_proportion']['mixed']:.1%}, survival {v['family_match_proportion']['survival']:.1%}.")
    lines += ["", "## PATHWAYS_TO_FINISH_FOR_FUTURE_SIMULATOR", "", "Striking: the diagnostic tests pre-fight offensive damage access against defensive vulnerability, not causal event transitions. Grappling: it keeps takedown access, opponent resistance, and submission pressure separate; any future round model should preserve that ordering. Exposure: five-round scheduling supplies additional opportunity but is not a causal hazard estimate. These archetypes are a stable comparison panel for MOV1, hierarchical challengers, and a future coarse simulator—not model features or optimized rules.", "", "## Limitations", "", "Overlapping, non-causal descriptive archetypes; percentile state loss of information; historical F02 coverage/missingness; small weight-class cross-cells; OOF years 2018–2026 only. No odds, ROI, EV, threshold optimization, new model feature, or prediction regeneration is present.", "", f"**{STATUS}**", ""]
    return "\n".join(lines)


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--f02-table", type=Path, required=True); ap.add_argument("--mov0-run-dir", type=Path, required=True); ap.add_argument("--terrain-assignment", type=Path, required=True); ap.add_argument("--output-dir", type=Path, required=True); args=ap.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    if sha(args.f02_table)!=F02_SHA: raise SystemExit("FROZEN_F02_SHA_MISMATCH")
    if sha(args.terrain_assignment)!=TERRAIN_SHA: raise SystemExit("FROZEN_TERRAIN_SHA_MISMATCH")
    oof={}
    for surface, expected in OOF_SHA.items():
        p=args.mov0_run_dir/f"oof_{surface}.csv"
        if sha(p)!=expected: raise SystemExit(f"FROZEN_{surface}_OOF_SHA_MISMATCH")
        oof[surface]=pd.read_csv(p)
    if not oof["MOV0_MIN"]["fight_id"].equals(oof["MOV0_FULL"]["fight_id"]): raise SystemExit("OOF_IDENTITY_MISMATCH")
    f02=pd.read_parquet(args.f02_table); f02["event_date"]=pd.to_datetime(f02.event_date); ref=f02[f02.event_date.dt.year.ge(2015)].copy()
    thresholds={}
    for name,suffix in CONCEPTS.items():
        vals=pd.concat([ref[f"f1__{suffix}"], ref[f"f2__{suffix}"]]).dropna().astype(float)
        thresholds[name]={"f02_suffix":suffix,"reference_population":"pooled fighter states, all corrected F02 rows dated 2015+; target unavailable/unread","N":int(len(vals)),"low_p33":float(vals.quantile(1/3)),"high_p67":float(vals.quantile(2/3))}
    x=oof["MOV0_MIN"][["fight_id","event_date","target","year","probability"]].rename(columns={"probability":"p_min"}).merge(oof["MOV0_FULL"][["fight_id","probability"]].rename(columns={"probability":"p_full"}),on="fight_id",validate="one_to_one")
    x=x.merge(f02,on="fight_id",how="inner",validate="one_to_one"); terrain=pd.read_csv(args.terrain_assignment); x=x.merge(terrain[["fight_id"]+TERRAIN_COLS],on="fight_id",how="left",validate="one_to_one")
    if len(x)!=len(oof["MOV0_MIN"]): raise SystemExit("OOF_JOIN_LOSS")
    x["full_bucket"]=x.p_full.map(bucket)
    a,b=side_state(x,1,thresholds),side_state(x,2,thresholds); flags=qualify(x,a,b)
    for k,v in flags.items(): x[k]=v
    records=[archetype_record(x,n,f,d) for n,f,d in ARCHETYPES]
    families={f:[n for n,ff,_ in ARCHETYPES if ff==f] for f in ["striking","grappling","mixed","survival"]}
    bucket_map={}
    for label,_,_ in BUCKETS:
        z=x[x.full_bucket.eq(label)]; bucket_map[label]={"N":int(len(z)),"family_match_proportion":{f:float(z[names].any(axis=1).mean()) for f,names in families.items()},"archetype_match_proportion":{n:float(z[n].mean()) for n,_,_ in ARCHETYPES}}
    source={"frozen_MOV0_source_HEAD":SOURCE_HEAD,"workflow_run":WORKFLOW_RUN,"artifact_id":ARTIFACT_ID,"artifact_name":"mov0-standard-finish-probability-v1","MOV0_MIN_OOF_SHA256":OOF_SHA["MOV0_MIN"],"MOV0_FULL_OOF_SHA256":OOF_SHA["MOV0_FULL"],"corrected_F02_SHA256":F02_SHA,"terrain_SHA256":TERRAIN_SHA,"proof_predictions_not_regenerated":"program imports no MOV0 training/prediction code; only reads and SHA-verifies frozen OOF CSVs"}
    write_json(args.output_dir/"feature_state_thresholds.json",thresholds); write_json(args.output_dir/"archetype_results.json",records); write_json(args.output_dir/"bucket_to_archetype_mapping.json",bucket_map); write_json(args.output_dir/"MOV0_CONDITIONAL_FEATURE_INTERACTION_ARCHETYPE_DIAGNOSTIC_V1_COMPLETE.json",{"status":STATUS,"sources":source,"archetypes":records,"bucket_to_archetype_mapping":bucket_map})
    (args.output_dir/"MOV0_CONDITIONAL_FEATURE_INTERACTION_ARCHETYPE_DIAGNOSTIC_V1_REPORT.md").write_text(report(records,bucket_map,thresholds,source),encoding="utf-8")
    write_json(args.output_dir/"EVIDENCE_MANIFEST.json",{"status":STATUS,"publication_mode":"FROZEN_OOF_READ_ONLY_DIAGNOSTIC","files":{p.name:{"sha256":sha(p),"bytes":p.stat().st_size} for p in sorted(args.output_dir.iterdir()) if p.is_file()}})
    print(STATUS); return 0

if __name__ == "__main__": raise SystemExit(main())
