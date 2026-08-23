#!/usr/bin/env python3
"""Derive Feature Family A striking-environment features from validated fighter state."""
from __future__ import annotations

import csv, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STATE=ROOT/'features/v0/fighter_state_primitives.csv'
STATE_MAN=ROOT/'features/v0/manifest.json'
FAMILY=ROOT/'features/family_a_striking_v0.json'
OUT=ROOT/'features/v0/striking_environment.csv'
AUDIT=ROOT/'provenance/audits/striking_environment_v0_latest.json'
AUDIT_MD=ROOT/'provenance/audits/striking_environment_v0_latest.md'
MANIFEST=ROOT/'features/v0/striking_environment_manifest.json'

ID_FIELDS=['target_fight_id','target_event_id','target_event_date','fighter_id','opponent_id','recent3_boundary_ambiguous','recent5_boundary_ambiguous','observed_prior_fight_count','observed_prior_loss_count','observed_prior_ko_loss_count']
CAREER_OUTCOME=['ko_tko_loss_per_observed_fight','ko_tko_share_of_observed_losses','ko_tko_win_per_observed_fight']
WINDOW_SUFFIXES=[
'stat_fight_count','sig_exposure_min','head_exposure_min','body_exposure_min','leg_exposure_min','distance_exposure_min','clinch_exposure_min','ground_exposure_min','knockdown_exposure_min',
'sig_attempts_per_min','sig_landed_per_min','sig_absorbed_per_min','opp_sig_attempts_faced_per_min','distance_attempts_per_min','clinch_attempts_per_min','ground_attempts_per_min','exchange_pace_per_min','sig_differential_per_min',
'knockdowns_per_15','knockdowns_per_sig_landed','knockdowns_per_head_landed','head_landed_per_min','head_attempts_per_min','head_accuracy',
'body_landed_per_min','body_attempts_per_min','body_attempt_share','leg_landed_per_min','leg_attempts_per_min','leg_attempt_share',
'distance_landed_per_min','distance_attempt_share','clinch_landed_per_min','clinch_attempt_share','ground_landed_per_min','ground_attempt_share','head_attempt_share','sig_accuracy',
'head_absorbed_per_min','opp_head_accuracy','sig_defense','head_defense','knockdowns_suffered_per_15','knockdowns_suffered_per_head_absorbed','distance_strike_defense','clinch_strike_defense_proxy','ground_strike_defense_proxy']


def read_csv(path):
    with path.open('r',encoding='utf-8-sig',newline='') as fh:return list(csv.DictReader(fh))

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as fh:
        for c in iter(lambda:fh.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def d(raw):
    if raw is None or str(raw).strip()=='':return None
    try:return Decimal(str(raw))
    except InvalidOperation as e:raise RuntimeError(f'bad decimal {raw!r}') from e

def div(num,den,scale=Decimal(1)):
    if num is None or den is None or den<=0:return None
    return scale*num/den

def defense(landed,attempted):
    x=div(landed,attempted)
    return None if x is None else Decimal(1)-x

def same_coverage_ratio(num,den,num_exp,den_exp):
    if num_exp is None or den_exp is None or num_exp<=0 or den_exp<=0 or num_exp!=den_exp:return None
    return div(num,den)

def fmt(v):
    if v is None:return ''
    if isinstance(v,bool):return 'true' if v else 'false'
    if isinstance(v,Decimal):
        if not v.is_finite():raise RuntimeError('non-finite decimal')
        if v==v.to_integral_value():return str(int(v))
        return format(v.normalize(),'f')
    return str(v)

def V(row,p,s):return d(row.get(f'{p}_{s}'))

def derive_window(row,p):
    if V(row,p,'stat_fight_count') is None:return {s:None for s in WINDOW_SUFFIXES}
    sigx=V(row,p,'sig_exposure_sec'); headx=V(row,p,'head_exposure_sec'); bodyx=V(row,p,'body_exposure_sec'); legx=V(row,p,'leg_exposure_sec')
    distx=V(row,p,'distance_exposure_sec'); clinx=V(row,p,'clinch_exposure_sec'); groundx=V(row,p,'ground_exposure_sec'); kdx=V(row,p,'knockdown_exposure_sec')
    sigl=V(row,p,'sig_landed'); siga=V(row,p,'sig_attempted'); osigl=V(row,p,'opp_sig_landed'); osiga=V(row,p,'opp_sig_attempted')
    headl=V(row,p,'head_landed'); heada=V(row,p,'head_attempted'); oheadl=V(row,p,'opp_head_landed'); oheada=V(row,p,'opp_head_attempted')
    bodyl=V(row,p,'body_landed'); bodya=V(row,p,'body_attempted'); legl=V(row,p,'leg_landed'); lega=V(row,p,'leg_attempted')
    distl=V(row,p,'distance_landed'); dista=V(row,p,'distance_attempted'); odistl=V(row,p,'opp_distance_landed'); odista=V(row,p,'opp_distance_attempted')
    clinl=V(row,p,'clinch_landed'); clina=V(row,p,'clinch_attempted'); oclinl=V(row,p,'opp_clinch_landed'); oclina=V(row,p,'opp_clinch_attempted')
    groundl=V(row,p,'ground_landed'); grounda=V(row,p,'ground_attempted'); ogroundl=V(row,p,'opp_ground_landed'); ogrounda=V(row,p,'opp_ground_attempted')
    kd=V(row,p,'knockdowns'); okd=V(row,p,'knockdowns_suffered')
    permin=Decimal(60); per15=Decimal(900)
    out={
      'stat_fight_count':V(row,p,'stat_fight_count'),
      'sig_exposure_min':div(sigx,Decimal(60)),'head_exposure_min':div(headx,Decimal(60)),'body_exposure_min':div(bodyx,Decimal(60)),'leg_exposure_min':div(legx,Decimal(60)),
      'distance_exposure_min':div(distx,Decimal(60)),'clinch_exposure_min':div(clinx,Decimal(60)),'ground_exposure_min':div(groundx,Decimal(60)),'knockdown_exposure_min':div(kdx,Decimal(60)),
      'sig_attempts_per_min':div(siga,sigx,permin),'sig_landed_per_min':div(sigl,sigx,permin),'sig_absorbed_per_min':div(osigl,sigx,permin),'opp_sig_attempts_faced_per_min':div(osiga,sigx,permin),
      'distance_attempts_per_min':div(dista,distx,permin),'clinch_attempts_per_min':div(clina,clinx,permin),'ground_attempts_per_min':div(grounda,groundx,permin),
      'exchange_pace_per_min':div((siga+osiga) if siga is not None and osiga is not None else None,sigx,permin),
      'sig_differential_per_min':div((sigl-osigl) if sigl is not None and osigl is not None else None,sigx,permin),
      'knockdowns_per_15':div(kd,kdx,per15),'knockdowns_per_sig_landed':same_coverage_ratio(kd,sigl,kdx,sigx),'knockdowns_per_head_landed':same_coverage_ratio(kd,headl,kdx,headx),
      'head_landed_per_min':div(headl,headx,permin),'head_attempts_per_min':div(heada,headx,permin),'head_accuracy':div(headl,heada),
      'body_landed_per_min':div(bodyl,bodyx,permin),'body_attempts_per_min':div(bodya,bodyx,permin),'body_attempt_share':same_coverage_ratio(bodya,siga,bodyx,sigx),
      'leg_landed_per_min':div(legl,legx,permin),'leg_attempts_per_min':div(lega,legx,permin),'leg_attempt_share':same_coverage_ratio(lega,siga,legx,sigx),
      'distance_landed_per_min':div(distl,distx,permin),'distance_attempt_share':same_coverage_ratio(dista,siga,distx,sigx),
      'clinch_landed_per_min':div(clinl,clinx,permin),'clinch_attempt_share':same_coverage_ratio(clina,siga,clinx,sigx),
      'ground_landed_per_min':div(groundl,groundx,permin),'ground_attempt_share':same_coverage_ratio(grounda,siga,groundx,sigx),
      'head_attempt_share':same_coverage_ratio(heada,siga,headx,sigx),'sig_accuracy':div(sigl,siga),
      'head_absorbed_per_min':div(oheadl,headx,permin),'opp_head_accuracy':div(oheadl,oheada),'sig_defense':defense(osigl,osiga),'head_defense':defense(oheadl,oheada),
      'knockdowns_suffered_per_15':div(okd,kdx,per15),'knockdowns_suffered_per_head_absorbed':same_coverage_ratio(okd,oheadl,kdx,headx),
      'distance_strike_defense':defense(odistl,odista),'clinch_strike_defense_proxy':defense(oclinl,oclina),'ground_strike_defense_proxy':defense(ogroundl,ogrounda)
    }
    return out

def main():
    sm=json.loads(STATE_MAN.read_text()); fam=json.loads(FAMILY.read_text())
    expected=next((x['sha256'] for x in sm.get('files',[]) if x.get('path')=='features/v0/fighter_state_primitives.csv'),None)
    if expected!=sha256(STATE):raise RuntimeError('fighter state input hash does not match its manifest')
    rows=read_csv(STATE); prefixes=fam['windows']
    fields=ID_FIELDS+CAREER_OUTCOME+[f'{p}_{s}' for p in prefixes for s in WINDOW_SUFFIXES]
    out=[]; null_counts=Counter()
    for row in rows:
        prior=d(row['observed_prior_fight_count']); losses=d(row['observed_prior_loss_count']); kol=d(row['observed_prior_ko_loss_count']); kow=d(row['observed_prior_ko_win_count'])
        r={k:row[k] for k in ID_FIELDS}
        r['ko_tko_loss_per_observed_fight']=div(kol,prior);r['ko_tko_share_of_observed_losses']=div(kol,losses);r['ko_tko_win_per_observed_fight']=div(kow,prior)
        for p in prefixes:
            vals=derive_window(row,p)
            for s,v in vals.items():
                r[f'{p}_{s}']=v
                if v is None:null_counts[f'{p}_{s}']+=1
        out.append(r)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open('w',encoding='utf-8',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=fields,extrasaction='raise');w.writeheader()
        for r in out:w.writerow({k:fmt(r.get(k)) for k in fields})
    man={
      'schema_version':1,'family':'A','family_version':fam['version'],'generated_at_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
      'input':{'path':str(STATE.relative_to(ROOT)),'sha256':sha256(STATE),'state_manifest_sha256':sha256(STATE_MAN)},
      'counts':{'rows':len(out),'columns':len(fields)},'null_counts':dict(null_counts),
      'files':[{'path':str(OUT.relative_to(ROOT)),'bytes':OUT.stat().st_size,'sha256':sha256(OUT)}],
      'rules':fam['rules'],'deferred':fam['deferred_from_family_a_v0']}
    MANIFEST.write_text(json.dumps(man,indent=2,sort_keys=True)+'\n')
    audit={**man,'decision':{'striking_environment_materialized':True,'safe_for_matchup_feature_builders':True,'damage_proxy_defined':False,'round_specific_kd_rates_defined':False,'opponent_adjustment_applied':False,'model_training_started':False}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
    AUDIT_MD.write_text(f"# Striking environment v0\n\n- Rows: **{len(out):,}**\n- Columns: **{len(fields):,}**\n- Windows: career, recent3, recent5, ewm365\n- Input fighter-state SHA-256: `{sha256(STATE)}`\n\nCross-domain ratios require equal observed exposure; zero/missing denominators remain null. No market data, opponent adjustment, arbitrary damage composite, or round-specific early/late KD proxy is present.\n")
    print(json.dumps({'rows':len(out),'columns':len(fields),'output_sha256':sha256(OUT)},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
