from __future__ import annotations
import json, os, time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd, numpy as np, requests
from .core import (MarketDiagnosticError,normalize_name,decimal_odds_to_raw_implied,
                   proportional_no_vig,median_no_vig_probability,fixed_blend,
                   metric_bundle,calibration_table,validate_m0_oof)
from .analysis import chronological_incremental_test,disagreement_report

SPORT_KEY="mma_mixed_martial_arts"
MARKET="h2h"
REGION="us"
HISTORICAL_ENDPOINT=f"https://api.the-odds-api.com/v4/historical/sports/{SPORT_KEY}/odds"
HISTORICAL_START="2020-06-06"
EXPECTED_ELIGIBLE_ROWS=3133
EXPECTED_EVENTS=268
EXPECTED_REQUESTS=268
CREDITS_PER_REQUEST=10
EXPECTED_CREDITS=2680
HARD_REQUEST_CEILING=300
HARD_CREDIT_CEILING=3000
MARKET_SOURCE="The Odds API"
MARKET_TIMING="event_date_0000z_provider_floor_2020_06_06_1005z"

def snapshot_timestamp(event_date:str)->str:
    d=str(pd.Timestamp(event_date).date())
    return "2020-06-06T10:05:00Z" if d=="2020-06-06" else f"{d}T00:00:00Z"

def build_population(oof:pd.DataFrame,fights:pd.DataFrame,events:pd.DataFrame)->tuple[pd.DataFrame,pd.DataFrame]:
    validate_m0_oof(oof)
    ids=fights[["fight_id","event_id","fighter_a_id","fighter_b_id","winner_id","result","promotion"]].copy()
    ev=events[["event_id","event_date","promotion"]].rename(columns={"promotion":"event_promotion"})
    pop=oof.merge(ids,on="fight_id",how="left",validate="one_to_one").merge(ev,on="event_id",how="left",validate="many_to_one")
    if pop[["event_id","event_date_y","fighter_a_id","fighter_b_id"]].isna().any().any(): raise MarketDiagnosticError("canonical identity missing")
    if not pop.promotion.eq("UFC").all() or not pop.event_promotion.eq("UFC").all(): raise MarketDiagnosticError("OOF population not UFC")
    pop["event_date"]=pd.to_datetime(pop.event_date_y).dt.date.astype(str)
    if not pd.to_datetime(pop.event_date_x).dt.date.astype(str).equals(pop.event_date): raise MarketDiagnosticError("OOF/canonical date mismatch")
    eligible=pop[pop.event_date>=HISTORICAL_START].copy()
    event_table=eligible[["event_id","event_date"]].drop_duplicates().sort_values(["event_date","event_id"]).reset_index(drop=True)
    event_table["snapshot_timestamp"]=event_table.event_date.map(snapshot_timestamp)
    if len(eligible)!=EXPECTED_ELIGIBLE_ROWS or len(event_table)!=EXPECTED_EVENTS:
        raise MarketDiagnosticError(f"approved population changed rows={len(eligible)} events={len(event_table)}")
    return eligible,event_table

def preflight(event_table:pd.DataFrame,authorized:bool,approved_ceiling:int)->dict[str,int]:
    requests_expected=len(event_table); credits=requests_expected*CREDITS_PER_REQUEST
    if not authorized: raise MarketDiagnosticError("authorized_pull must be true")
    if requests_expected!=EXPECTED_REQUESTS or credits!=EXPECTED_CREDITS: raise MarketDiagnosticError("request estimate changed")
    if approved_ceiling>HARD_CREDIT_CEILING or credits>approved_ceiling: raise MarketDiagnosticError("approved credit ceiling invalid")
    if requests_expected>HARD_REQUEST_CEILING: raise MarketDiagnosticError("request ceiling exceeded")
    return {"requests_expected":requests_expected,"credits_expected":credits,"approved_credit_ceiling":approved_ceiling,"hard_request_ceiling":HARD_REQUEST_CEILING,"hard_credit_ceiling":HARD_CREDIT_CEILING}

def retrieve(event_table:pd.DataFrame,api_key:str,raw_dir:Path,approved_ceiling:int)->dict[str,Any]:
    if not api_key: raise MarketDiagnosticError("THE_ODDS_API_KEY missing")
    raw_dir.mkdir(parents=True,exist_ok=True)
    made=0; responses=0; failed=[]; usage=[]
    for row in event_table.itertuples(index=False):
        if made>=HARD_REQUEST_CEILING or (made+1)*CREDITS_PER_REQUEST>approved_ceiling:
            raise MarketDiagnosticError("runtime request/credit ceiling reached")
        params={"apiKey":api_key,"regions":REGION,"markets":MARKET,"date":row.snapshot_timestamp,"oddsFormat":"decimal","dateFormat":"iso"}
        try:
            r=requests.get(HISTORICAL_ENDPOINT,params=params,timeout=45)
        except requests.RequestException:
            failed.append({"event_id":row.event_id,"snapshot_timestamp":row.snapshot_timestamp,"error":"request_exception"}); made+=1; continue
        made+=1
        usage.append({"event_id":row.event_id,"x_requests_used":r.headers.get("x-requests-used"),"x_requests_remaining":r.headers.get("x-requests-remaining"),"x_requests_last":r.headers.get("x-requests-last")})
        if r.status_code!=200:
            failed.append({"event_id":row.event_id,"snapshot_timestamp":row.snapshot_timestamp,"status_code":r.status_code}); continue
        payload=r.json(); responses+=1
        (raw_dir/f"{row.event_date}_{row.event_id}.json").write_text(json.dumps(payload,separators=(",",":")),encoding="utf-8")
    return {"request_count":made,"response_count":responses,"failed_requests":failed,"usage_headers":usage}

def parse_snapshot_files(raw_dir:Path,fighters:pd.DataFrame)->pd.DataFrame:
    name_map={}
    for r in fighters[["fighter_id","canonical_name"]].itertuples(index=False):
        k=normalize_name(str(r.canonical_name)); name_map.setdefault(k,set()).add(str(r.fighter_id))
    unique={k:next(iter(v)) for k,v in name_map.items() if len(v)==1}
    rows=[]
    for path in sorted(raw_dir.glob("*.json")):
        payload=json.loads(path.read_text())
        events=payload.get("data",[]) if isinstance(payload,dict) else []
        for ev in events:
            home,away=unique.get(normalize_name(ev.get("home_team",""))),unique.get(normalize_name(ev.get("away_team","")))
            if not home or not away or home==away: continue
            lo,hi=sorted((home,away)); per_book=[]
            for b in ev.get("bookmakers",[]):
                markets=[m for m in b.get("markets",[]) if m.get("key")==MARKET]
                for m in markets:
                    outcomes={normalize_name(o.get("name","")):o.get("price") for o in m.get("outcomes",[])}
                    hp=outcomes.get(normalize_name(ev.get("home_team",""))); ap=outcomes.get(normalize_name(ev.get("away_team","")))
                    if hp is None or ap is None: continue
                    try:
                        hr=decimal_odds_to_raw_implied(hp); ar=decimal_odds_to_raw_implied(ap); hn,an=proportional_no_vig(hr,ar)
                    except Exception: continue
                    per_book.append((b.get("key",""),hn,an))
            if not per_book: continue
            rows.append({"provider_event_id":ev.get("id"),"commence_time":ev.get("commence_time"),"pair_lo":lo,"pair_hi":hi,
                         "home_id":home,"away_id":away,"home_market_probability":median_no_vig_probability([x[1] for x in per_book]),
                         "away_market_probability":median_no_vig_probability([x[2] for x in per_book]),"book_count":len(per_book)})
    return pd.DataFrame(rows)

def match_and_evaluate(eligible:pd.DataFrame,market:pd.DataFrame)->tuple[pd.DataFrame,dict[str,Any]]:
    if market.empty: raise MarketDiagnosticError("no normalized market rows")
    e=eligible.copy(); pairs=[sorted((str(a),str(b))) for a,b in zip(e.fighter_a_id,e.fighter_b_id)]
    e["pair_lo"]=[x[0] for x in pairs]; e["pair_hi"]=[x[1] for x in pairs]
    # one snapshot per canonical event/date; provider rows are conservatively paired by fighter pair
    dup=market.duplicated(["pair_lo","pair_hi"],keep=False)
    ambiguous_pairs=set(map(tuple,market.loc[dup,["pair_lo","pair_hi"]].drop_duplicates().itertuples(index=False,name=None)))
    market=market[[tuple(x) not in ambiguous_pairs for x in market[["pair_lo","pair_hi"]].itertuples(index=False,name=None)]].copy()
    market=market.drop_duplicates(["pair_lo","pair_hi"],keep=False)
    m=e.merge(market,on=["pair_lo","pair_hi"],how="inner",validate="many_to_one")
    p=np.where(m.fighter_a_id.eq(m.home_id),m.home_market_probability,np.where(m.fighter_a_id.eq(m.away_id),m.away_market_probability,np.nan))
    if np.isnan(p).any(): raise MarketDiagnosticError("orientation failure")
    # M0 fighter_1 corresponds to canonical F02 ordering, which in frozen OOF is represented by fight-side target orientation.
    # Canonical fights fighter_a_id is the same fight identity side used by F02 replay contract.
    m["market_probability"]=p.astype(float); m["m0_probability"]=m.logistic_probability.astype(float); m["blend_probability"]=fixed_blend(m.m0_probability,m.market_probability)
    cal,ece=calibration_table(m.target,m.market_probability)
    same={"50_50":metric_bundle(m.target,np.full(len(m),.5)),"m0":metric_bundle(m.target,m.m0_probability),"market":metric_bundle(m.target,m.market_probability),"blend_50_50":metric_bundle(m.target,m.blend_probability),"market_ece":ece,"market_calibration":cal}
    inc=chronological_incremental_test(m[["event_date","target","market_probability","m0_probability"]])
    disagreement=disagreement_report(m.m0_probability,m.market_probability)
    folds=inc["fold_count"]; both=inc["folds_market_plus_m0_better_both"]; pos=inc["m0_logit_coefficient"]["positive_folds"]
    market_stronger=same["market"]["log_loss"]<same["m0"]["log_loss"] and same["market"]["brier"]<same["m0"]["brier"]
    if market_stronger and both>=max(2,int(np.ceil(folds*.6))) and pos==folds and inc["market_plus_m0"]["log_loss"]<inc["market_only"]["log_loss"] and inc["market_plus_m0"]["brier"]<inc["market_only"]["brier"]:
        verdict="MARKET_COMPLEMENTARITY_REPLICATED"; decision="YES — SUPPORTED, BUT MARKET GAP REMAINS LARGE"
    elif both>0 and pos>folds/2:
        verdict="MARKET_COMPLEMENTARITY_WEAK"; decision="UNCERTAIN — COMPLEMENTARITY NOT ROBUST"
    elif len(m)<500:
        verdict="INSUFFICIENT_ODDS_API_MATCHING"; decision="UNCERTAIN — COMPLEMENTARITY NOT ROBUST"
    else:
        verdict="MARKET_COMPLEMENTARITY_NOT_REPLICATED"; decision="NO — CURRENT SIGNAL APPEARS FULLY SUBSUMED BY MARKET"
    return m,{"matched_rows":int(len(m)),"eligible_rows":int(len(e)),"coverage_pct":float(len(m)/len(e)),"ambiguous_provider_pairs":len(ambiguous_pairs),"same_sample_results":same,"correlation":disagreement,"incremental_test":inc,"replication_verdict":verdict,"worth_continuing_decision":decision}
