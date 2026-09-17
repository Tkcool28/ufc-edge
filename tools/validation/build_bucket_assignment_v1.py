#!/usr/bin/env python3
"""Stage A only: construct the model-independent validation terrain.

This program deliberately has no prediction or outcome arguments.  It reads a
strict allowlist from the corrected F02 predictor surface and rejects any
outcome/prediction-shaped column before threshold selection.
"""
from __future__ import annotations

import argparse, hashlib, json, re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

VERSION = "MODEL_VALIDATION_BUCKET_CONTRACT_V1"
OUTCOME_RE = re.compile(r"winner|(^|__)result($|__)|outcome|finish_method|(^|__)target($|__)|probab|predict|correct|brier|log.loss|calibr", re.I)
RICH = {
    "strike": ["fs__knockdown_rate__created_per_15__career__shrunk", "fs__sig_strike_flow__landed_per_min__career__shrunk"],
    "grapple": ["fs__submission_attempt_rate__created_per_15__career__shrunk", "fs__takedown_pressure__created_per_15__career__shrunk"],
}
BASE = ["fight_id", "event_id", "event_date", "promotion", "fighter_1_id", "fighter_2_id", "scheduled_rounds", "ctx__title_bout", "ctx__weight_class", "f1__ctx__layoff_days", "f2__ctx__layoff_days", "f1__fs__prior_fight_count__career__raw", "f2__fs__prior_fight_count__career__raw"]

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for x in iter(lambda:f.read(1<<20), b""): h.update(x)
    return h.hexdigest()

def canonical_json(x: Any) -> bytes:
    return (json.dumps(x, sort_keys=True, separators=(",", ":"), default=str)+"\n").encode()

def logical_hash(df: pd.DataFrame) -> str:
    rows=df.where(pd.notna(df), None).to_dict("records")
    return hashlib.sha256(canonical_json(rows)).hexdigest()

def safe_columns(schema: Path) -> list[str]:
    names=[x["name"] for x in json.loads(schema.read_text())["columns"]]
    cols=BASE+[f"f{s}__{n}" for s in (1,2) for group in RICH.values() for n in group]
    missing=sorted(set(cols)-set(names))
    if missing: raise RuntimeError(f"required Stage-A F02 columns missing: {missing}")
    bad=[x for x in cols if OUTCOME_RE.search(x)]
    if bad: raise RuntimeError(f"prohibited Stage-A columns requested: {bad}")
    return cols

def bucket_experience(a: float, b: float) -> str:
    # Symmetric matchup severity: the less-experienced fighter governs.
    x=min(a,b)
    return "0" if x==0 else "1–2" if x<=2 else "3–5" if x<=5 else "6–10" if x<=10 else "11+"

def bucket_layoff(a: float, b: float) -> str:
    # Symmetric matchup disruption: the longer known layoff governs; missing is explicit.
    if pd.isna(a) or pd.isna(b): return "STRUCTURAL_NA_OR_UNKNOWN"
    x=max(float(a),float(b))
    return "< 6 months" if x<183 else "6–12 months" if x<365 else "12–18 months" if x<548 else "18+ months"

def side(value: bool, fighter: str, other: bool) -> str:
    return fighter if value and not other else "BOTH" if value and other else "NONE"

def classify(a: float, b: float, cut: float, prefix: str, f1: str, f2: str) -> tuple[str,str]:
    if pd.isna(a) or pd.isna(b): return "UNASSIGNABLE_BY_CONTRACT", "UNASSIGNABLE"
    x,y=float(a)>=cut,float(b)>=cut
    state="LOW" if not x and not y else "ONE_SIDED" if x!=y else "TWO_SIDED"
    return f"{prefix}_{state}", side(x,f1,y) if x else (f2 if y else "NONE")

def required_mean(values: list[float]) -> float:
    """A family is supported only when every governed component is observed."""
    return float(np.mean(values)) if all(pd.notna(v) for v in values) else float("nan")

def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--f02-dir",type=Path,required=True); ap.add_argument("--audit-marker",type=Path,required=True); ap.add_argument("--output-dir",type=Path,required=True); a=ap.parse_args()
    marker=json.loads(a.audit_marker.read_text())
    if marker.get("final_recommendation")!="MOV_BUCKET_INPUTS_SAFE_FOR_BUCKET_CONTRACT_DESIGN": raise RuntimeError("approved MOV audit recommendation missing")
    cols=safe_columns(a.f02_dir/"schema.json")
    # Explicit column selection is the mechanical Stage-A blindness boundary.
    df=pd.read_parquet(a.f02_dir/"winner_modeling_table.parquet",columns=cols)
    if any(OUTCOME_RE.search(c) for c in df.columns): raise RuntimeError("prohibited column entered Stage A")
    df["event_date"]=pd.to_datetime(df.event_date,errors="raise")
    df=df[df.promotion.eq("UFC") & df.event_date.dt.year.between(2015,2026)].copy()
    if df.fight_id.duplicated().any(): raise RuntimeError("duplicate canonical fight_id")
    if df[["fight_id","event_date","fighter_1_id","fighter_2_id"]].isna().any().any(): raise RuntimeError("malformed identity/date row")
    # Quantiles are computed only from approved pre-fight values.
    cuts={}
    for family, names in RICH.items():
        vals=[]
        for n in names: vals.extend(pd.to_numeric(df[f"f1__{n}"],errors="coerce").dropna()); vals.extend(pd.to_numeric(df[f"f2__{n}"],errors="coerce").dropna())
        cuts[family]=float(pd.Series(vals).quantile(.75))
    evidence={"status":"STAGE_A_THRESHOLD_SELECTION_EVIDENCE_V1","inputs":"allowlisted corrected F02 pre-fight columns only","outcomes_predictions_available":False,"method":"75th percentile of pooled fighter-side approved career-shrunk rate values; fixed once","cuts":cuts,"rich_feature_subset":RICH,"rows":len(df)}
    r=[]
    for x in df.itertuples(index=False):
        d=x._asdict(); f1,f2=str(d["fighter_1_id"]),str(d["fighter_2_id"])
        sp1=required_mean([d[f"f1__{n}"] for n in RICH["strike"]]); sp2=required_mean([d[f"f2__{n}"] for n in RICH["strike"]])
        gp1=required_mean([d[f"f1__{n}"] for n in RICH["grapple"]]); gp2=required_mean([d[f"f2__{n}"] for n in RICH["grapple"]])
        se,ss=classify(sp1,sp2,cuts["strike"],"STRIKE",f1,f2); ge,gs=classify(gp1,gp2,cuts["grapple"],"GRAPPLE",f1,f2)
        joint="UNASSIGNABLE_BY_CONTRACT" if "UNASSIGNABLE" in (se,ge) else se+"__"+ge
        present=sum(pd.notna(d[f"f{s}__{n}"]) for s in (1,2) for n in RICH["strike"]+RICH["grapple"])
        complete="LOW_MISSINGNESS" if present==8 else "MODERATE_MISSINGNESS" if present>=6 else "HIGH_MISSINGNESS"
        rounds=d["scheduled_rounds"]
        if rounds not in (3,5): raise RuntimeError(f"malformed scheduled_rounds for {d['fight_id']}")
        title=d["ctx__title_bout"]
        if title not in (True,False,0,1): raise RuntimeError(f"malformed title status for {d['fight_id']}")
        if pd.isna(d["ctx__weight_class"]): raise RuntimeError(f"unknown weight class for {d['fight_id']}")
        r.append({"fight_id":d["fight_id"],"event_id":d["event_id"],"event_date":d["event_date"].date().isoformat(),"year":int(d["event_date"].year),"fighter_1_id":f1,"fighter_2_id":f2,"experience_bucket":bucket_experience(float(d["f1__fs__prior_fight_count__career__raw"]),float(d["f2__fs__prior_fight_count__career__raw"])),"layoff_bucket":bucket_layoff(d["f1__ctx__layoff_days"],d["f2__ctx__layoff_days"]),"scheduled_duration_bucket":f"{int(rounds)}_ROUND","title_status":"TITLE_BOUT" if bool(title) else "NON_TITLE_BOUT","weight_class":str(d["ctx__weight_class"]),"completeness_tier":complete,"striking_environment":se,"strike_pressure_side":ss,"grappling_environment":ge,"grapple_pressure_side":gs,"joint_mov_environment":joint,"mov_eligibility_status":"ASSIGNABLE" if joint!="UNASSIGNABLE_BY_CONTRACT" else "UNASSIGNABLE_BY_CONTRACT","contract_version":VERSION})
    out=pd.DataFrame(r).sort_values(["event_date","fight_id"],kind="mergesort").reset_index(drop=True)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    contract={"version":VERSION,"canonical_order":"event_date ASC, fight_id ASC","confidence_bins":[[.50,.55],[.55,.60],[.60,.65],[.65,.70],[.70,.75],[.75,.80],[.80,.85],[.85,1.0]],"experience":"minimum fighter strict prior UFC count","layoff":"maximum known strict pre-fight layoff; missing is explicit N/A","completeness":"approved four rich-stat concepts, 8 side-values: 8 low, 6-7 moderate, <=5 high","mov":evidence,"missing_rich_data":"UNASSIGNABLE_BY_CONTRACT; never LOW","version_policy":"V1 is immutable; changed thresholds or sources require V2","sample_size_governance":{"normal":100,"moderate":50,"thin":25,"insufficient_below":25}}
    (a.output_dir/"MODEL_VALIDATION_BUCKET_CONTRACT_V1.json").write_bytes(canonical_json(contract))
    (a.output_dir/"threshold_selection_evidence_v1.json").write_bytes(canonical_json(evidence))
    out.to_csv(a.output_dir/"MODEL_VALIDATION_BUCKET_ASSIGNMENTS_V1.csv",index=False,lineterminator="\n")
    logical=logical_hash(out); physical=sha(a.output_dir/"MODEL_VALIDATION_BUCKET_ASSIGNMENTS_V1.csv")
    manifest={"status":"MODEL_VALIDATION_BUCKET_CONTRACT_V1_COMPLETE","rows":len(out),"assignment_logical_sha256":logical,"assignment_physical_sha256":physical,"contract_sha256":sha(a.output_dir/"MODEL_VALIDATION_BUCKET_CONTRACT_V1.json"),"threshold_evidence_sha256":sha(a.output_dir/"threshold_selection_evidence_v1.json"),"source_f02_logical_sha256":json.loads((a.f02_dir/"summary.json").read_text()).get("predictor_logical_sha256"),"source_f02_table_sha256":sha(a.f02_dir/"winner_modeling_table.parquet"),"audit_marker_sha256":sha(a.audit_marker)}
    (a.output_dir/"manifest.json").write_bytes(canonical_json(manifest)); print("MODEL_VALIDATION_BUCKET_CONTRACT_V1_COMPLETE")
if __name__=="__main__": main()
