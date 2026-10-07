#!/usr/bin/env python3
"""Hash, chronology, source orientation and independent state reconciliation."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import pandas as pd
from audit_grappling_identity_v1 import R, OUT, OLD, BASE, METRICS, load, state, verify_upstream
MARKER='UFC_EDGE_GRAPPLING_IDENTITY_AND_COMPETING_GROUND_PATHWAY_DIAGNOSTIC_V1_COMPLETE'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest():
 files={str(p.relative_to(OUT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ['EVIDENCE_MANIFEST.json',MARKER+'.json']}
 scripts={str(p.relative_to(R)):sha(p) for p in sorted((R/'tools/audits').glob('*grappling_identity_v1.py'))}
 scripts['.github/workflows/grappling-identity-diagnostic-v1.yml']=sha(R/'.github/workflows/grappling-identity-diagnostic-v1.yml')
 return {'starting_main':BASE,'branch':'audit/grappling-identity-competing-pathways-v1','conclusion':'B — PARTIAL IDENTITY IS SUPPORTABLE','fits':0,'sealed_through':'2026-08-15','upstream_manifest_sha256':sha(OLD/'EVIDENCE_MANIFEST.json'),'artifacts':files,'scripts':scripts}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write-manifest',action='store_true');a=ap.parse_args()
 verify_upstream();s=pd.read_csv(OUT/'identity_states.csv.gz');b=load()
 assert len(s)==11316 and not s.duplicated(['target_fight_id','fighter_id']).any()
 assert ((s.latest_prior_date.isna())|(s.latest_prior_date<s.cutoff)).all()
 checks=0
 # Independent scalar reconstruction across dates, fighters and zero-history states.
 for t in s.iloc[np.linspace(0,len(s)-1,101,dtype=int)].itertuples():
  g=b[(b.fighter_id==t.fighter_id)&(b.event_date<t.cutoff)]
  assert len(g)==t.prior_fights
  for m,(num,den,scale,screen,minb) in METRICS.items():
   pairs=[(n,d) for n,d in zip(g[num],g[den]) if pd.notna(n) and pd.notna(d)]
   n=sum(v[0] for v in pairs) if pairs else np.nan;d=sum(v[1] for v in pairs) if pairs else np.nan
   ratio=scale*n/d if d>0 else np.nan
   for suffix,v in [('_num',n),('_den',d),('',ratio)]:
    saved=getattr(t,m+suffix);assert (pd.isna(saved) and pd.isna(v)) or np.isclose(saved,v,rtol=1e-8,atol=1e-8),(t.target_fight_id,m,suffix)
    checks+=1
 # Actual opponent orientation, no ID guessing.
 pairs=b.set_index(['fight_id','fighter_id'])
 for t in b.iloc[np.linspace(0,len(b)-1,101,dtype=int)].itertuples():
  opp=pairs.loc[(t.fight_id,t.opponent_id)]
  for v,expected in [(t.ground_attempts_allowed,opp.sig_ground_attempted),(t.opponent_td_attempts,opp.takedowns_attempted)]:assert (pd.isna(v) and pd.isna(expected)) or v==expected
 assert not (b.control_sec>b.elapsed_min*60).any()
 assert not (b.takedowns_landed>b.takedowns_attempted).any()
 assert not (b.sig_ground_landed>b.sig_ground_attempted).any()
 assert set(pd.read_csv(OUT/'chronological_support.csv').year)==set(range(2018,2027))
 for name in ['GRAPPLING_IDENTITY_SOURCE_LINEAGE','CONTROL_BEHAVIOR_DIAGNOSTIC','SUBMISSION_ORIENTATION_DIAGNOSTIC','GROUND_AND_POUND_ORIENTATION_DIAGNOSTIC','FINISH_TIMING_DIAGNOSTIC','DECISION_VS_FINISH_CONTROL_ANALYSIS','B3_GRAPPLING_IDENTITY_ANALYSIS','B5_GRAPPLING_IDENTITY_ANALYSIS','EARLY_FOLD_IDENTITY_SUPPORT','TRAINING_BACKGROUND_FEASIBILITY','DIRECTIONAL_MATCHUP_IDENTITY_FEASIBILITY','NEXT_EXPERIMENT_RECOMMENDATION']:assert (OUT/(name+'.md')).is_file()
 m=manifest();p=OUT/'EVIDENCE_MANIFEST.json'
 if a.write_manifest:
  p.write_text(json.dumps(m,sort_keys=True,indent=2,allow_nan=False)+'\n')
  (OUT/(MARKER+'.json')).write_text(json.dumps({'marker':MARKER,'status':'COMPLETE','starting_main':BASE,'branch':m['branch'],'conclusion':m['conclusion'],'evidence_manifest_sha256':sha(p),'fits':0,'independent_state_scalar_checks':checks},sort_keys=True,indent=2)+'\n')
 else:
  assert json.loads(p.read_text())==m,'Manifest differs'
  assert json.loads((OUT/(MARKER+'.json')).read_text())['evidence_manifest_sha256']==sha(p)
 print(json.dumps({'status':'PASS','independent_scalar_checks':checks,'source_opponent_orientation':'PASS','manifest_sha256':sha(p)}))
if __name__=='__main__':main()
