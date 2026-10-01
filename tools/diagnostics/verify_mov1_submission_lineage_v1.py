"""Independent four-family component replay from frozen canonical round stats.

F01 StateBuilder and shrink_component are deliberately not imported. Shares only the
pre-frozen elapsed rules resolver, necessary to avoid inventing duration eligibility.
No model imports, no outcomes beyond pre-cutoff history, no future data.
"""
import argparse,hashlib,json,math,pathlib
from collections import defaultdict
import numpy as np,pandas as pd
from ufc_edge.features.elapsed_exposure import infer_round_exposure,load_registry
R=pathlib.Path(__file__).resolve().parents[2]
TARGETS={
 'submission_attempt_rate': [('created_per_15','submission_attempts','self',15.0),('faced_per_15','submission_attempts','opponent',15.0)],
 'takedown_pressure':[('created_per_15','takedowns_attempted','self',15.0)],
 'takedown_conversion':[('defense','takedowns_attempted','opponent',1.0)]}
def val(v):
 if v is None or pd.isna(v) or str(v).strip()=='':return None
 return int(v)
def run(path):
 f=pd.read_parquet(path)
 assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()=='d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580'
 events=pd.read_csv(R/'data/canonical/v0/events.csv',dtype=str)[['event_id','event_date']]
 fights=pd.read_csv(R/'data/canonical/v0/fights.csv',dtype=str).merge(events,on='event_id',validate='many_to_one')
 fights=fights.set_index('fight_id',drop=False)
 rounds=pd.read_csv(R/'data/canonical/v0/fighter_round_stats.csv',dtype=str)
 fighters={(r.fight_id,r.fighter_id,val(r['round'])):r for _,r in rounds.iterrows()}
 registry=load_registry(R)
 date_min='2015-01-01'
 # Outcome-blind target selection, two complete historical fights from three fixed eras.
 cols=[f'{s}__fs__{fam}__{comp}__career__shrunk' for s in ('f1','f2') for fam,cs in TARGETS.items() for comp,*_ in cs]
 chosen=[]
 for year in (2018,2022,2025):
  q=f[(f.event_date>=f'{year}-01-01')&(f.event_date<f'{year+1}-01-01')].dropna(subset=cols).sort_values('fight_id')
  assert len(q)>=2
  chosen.extend(q.head(2).to_dict('records'))
 # Precompute raw sufficient statistics for four target components per fighter-fight.
 stats=defaultdict(lambda:defaultdict(lambda:[0.,0.]))
 obs=defaultdict(int)
 for (fid,who,rnd),row in fighters.items():
  if fid not in fights.index:continue
  bout=fights.loc[fid]; payload={k:bout.get(k) for k in ['fight_id','promotion','method','finish_round','finish_time_sec','scheduled_rounds']}
  elapsed=infer_round_exposure(payload,bout.event_date,rnd,registry)
  # Attempt-ratio defense uses observed compatible rounds even if elapsed exposure is unavailable.
  # Only per-15 rate families require governed positive elapsed minutes.
  minutes=elapsed/60. if elapsed is not None and elapsed>0 else None
  a,b=bout.fighter_a_id,bout.fighter_b_id
  opp=b if who==a else a if who==b else None
  other=fighters.get((fid,opp,rnd)) if opp else None
  for family,cs in TARGETS.items():
   if family!='takedown_conversion' and minutes is None:continue
   for component,field,side,mult in cs:
    source=row if side=='self' else other
    if source is None:continue
    value=val(source.get(field))
    if value is None:continue
    if family=='takedown_conversion':
     landed=val(source.get('takedowns_landed'))
     if landed is None:continue
     num=value-landed;den=value
    else:num=mult*value;den=minutes
    item=stats[(fid,who)][(family,component)];item[0]+=num;item[1]+=den
    obs[(fid,who,family,component)]+=1
 # Independent contribution rows are complete before selecting any target.
 checks=[];maxerr=0.
 for target in chosen:
  date=target['event_date'];fid=target['fight_id'];bout=fights.loc[fid]
  before=fights[fights.event_date<date]
  assert fid not in before.index and not (before.event_date==date).any()
  prior_fight_class=int(before.weight_class.eq(bout.weight_class).sum())
  scope=bout.weight_class if prior_fight_class>=100 else None
  for side,who in [('f1',target['fighter_1_id']),('f2',target['fighter_2_id'])]:
   history=before[(before.fighter_a_id==who)|(before.fighter_b_id==who)]
   for family,cs in TARGETS.items():
    strength=20. if family=='takedown_conversion' else 15.
    for component,*_ in cs:
     key=(family,component)
     own=np.array([stats[(otherid,who)][key] for otherid in history.index],float).sum(axis=0) if len(history) else np.zeros(2)
     pop=before if scope is None else before[before.weight_class==scope]
     pri=np.zeros(2)
     for otherid,priorbout in pop.iterrows():
      for actor in (priorbout.fighter_a_id,priorbout.fighter_b_id):
       v=stats[(otherid,actor)][key];pri+=v
     expected=None
     # F01 explicit zero-history policy: no unproven-debutant population substitution.
     if len(history)>0 and pri[1]>0:
      expected=(own[0]+strength*(pri[0]/pri[1]))/(own[1]+strength)
     column=f'{side}__fs__{family}__{component}__career__shrunk'
     actual=target[column]
     if expected is None:assert pd.isna(actual),(fid,column,actual)
     else:
      assert pd.notna(actual),(fid,column,'unexpected null')
      err=abs(float(actual)-float(expected));maxerr=max(maxerr,err)
      assert math.isclose(float(actual),float(expected),rel_tol=1e-10,abs_tol=1e-10),(fid,column,actual,expected,err)
     checks.append({'target_fight_id':fid,'target_date':date,'fighter_side':side,'feature':column,'prior_fighter_fights':len(history),'prior_population_fights':len(pop),'prior_scope':'global' if scope is None else 'division','prior_population_denominator':float(pri[1]),'personal_denominator':float(own[1]),'F02_value':None if pd.isna(actual) else float(actual),'independent_value':expected,'null_semantics_match':pd.isna(actual)==(expected is None)})
 return {'status':'PASS','F02_sha256':hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(),'independent_reconstructions':len(checks),'target_fights':len(chosen),'max_absolute_numeric_error':maxerr,'strict_prior_no_same_date':True,'zero_history_prior_withheld':True,'sources':'canonical fighter_round_stats + canonical fight dates + frozen elapsed registry; manual sums and shrinkage','rows':checks}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--f02',required=True);q=a.parse_args();print('PR123_LINEAGE_BEGIN');print(json.dumps(run(q.f02),sort_keys=True,allow_nan=False));print('PR123_LINEAGE_END')
