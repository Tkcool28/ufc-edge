#!/usr/bin/env python3
"""Independent scalar/block/support checks, full lineage hashes and deterministic rerun."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from grappling_identity_separation_v1 import OUT,R,BASE,sha,js,verify_inputs,old,DIMS
MARK='UFC_EDGE_GRAPPLING_IDENTITY_SEPARATION_V1_COMPLETE'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write-manifest',action='store_true');ap.add_argument('--rerun',action='store_true');a=ap.parse_args();verify_inputs()
 s=pd.read_csv(OUT/'fighter_states.csv.gz');blocks=pd.read_csv(OUT/'block_states.csv.gz');b=old.load()
 assert len(s)==11316 and not s.duplicated(['target_fight_id','fighter_id']).any()
 assert ((s.latest_prior_date.isna())|(s.latest_prior_date<s.cutoff)).all()
 checks=0
 def independent(g,t,prefix=''):
  nonlocal checks
  for key,(field,dec,scale) in DIMS.items():
   pairs=[(float(getattr(x,field)),float(x.elapsed_min)) for x in g.itertuples() if (not dec or x.method=='DECISION') and pd.notna(getattr(x,field)) and pd.notna(x.elapsed_min)]
   n=sum(v[0] for v in pairs) if pairs else np.nan;den=sum(v[1] for v in pairs) if pairs else np.nan;v=scale*n/den if den>0 else np.nan
   for suffix,expected in [('_num',n),('_den_min',den),('',v),('_bouts',len(pairs))]:
    got=getattr(t,prefix+key+suffix);assert (pd.isna(got) and pd.isna(expected)) or np.isclose(got,expected,rtol=1e-8,atol=1e-8),(prefix,key,suffix,got,expected);checks+=1
 for t in s.iloc[np.linspace(0,len(s)-1,101,dtype=int)].itertuples():independent(b[(b.fighter_id==t.fighter_id)&(b.event_date<t.cutoff)],t)
 for t in blocks.iloc[np.linspace(0,len(blocks)-1,101,dtype=int)].itertuples():
  g=b[(b.fighter_id==t.fighter_id)&(b.event_date<f'{t.year}-01-01')].sort_values(['event_date','fight_id'])
  assert t.first_ids=='|'.join(g.iloc[:3].fight_id) and t.next_ids=='|'.join(g.iloc[3:6].fight_id)
  assert set(t.first_ids.split('|')).isdisjoint(t.next_ids.split('|'));assert t.first_end<t.next_start
  independent(g.iloc[:3],t,'first_');independent(g.iloc[3:6],t,'next_')
 # Recompute reported scoring shares from exact frozen folds.
 import lzma
 folds=json.loads(lzma.decompress((old.upstream.CON/'ordered_fold_fight_ids.json.xz').read_bytes()))['folds'];support=pd.read_csv(OUT/'support.csv')
 for fold in folds:
  z=s[s.target_fight_id.isin(fold['scoring'])];r=support[(support.year==fold['outer_year'])&support.scope.eq('scoring_prefight')&support.division.eq('ALL')].iloc[0]
  assert r.states==len(z) and np.isclose(r.both_share,(z.control_supported&z.submission_supported&z.access_supported).mean())
 # Cell IDs unchanged and every saved cell state is an identical pre-fight state.
 cell=pd.read_csv(OUT/'cell_states.csv.gz');ids=pd.read_csv(old.OUT/'B3_B5_identity_states.csv.gz',usecols=['target_fight_id','fighter_id','cell'])
 assert cell[['target_fight_id','fighter_id','cell']].sort_values(['cell','target_fight_id','fighter_id']).reset_index(drop=True).equals(ids[['target_fight_id','fighter_id','cell']].sort_values(['cell','target_fight_id','fighter_id']).reset_index(drop=True))
 for key in DIMS:
  matched=cell.merge(s[['target_fight_id','fighter_id',key]],on=['target_fight_id','fighter_id'],suffixes=('','_expected'),validate='many_to_one');assert np.allclose(matched[key],matched[key+'_expected'],equal_nan=True)
 # Focal zero-history never gains support from pooled priors.
 assert not s.loc[s.prior_fights.eq(0),'control_supported'].any();assert s.loc[s.prior_decisions.eq(0),'control'].isna().all()
 required=['GRAPPLING_IDENTITY_EXPERIMENT_PROTOCOL','ACCESS_MATCHING_SPECIFICATION','CONTROL_IDENTITY_MEASUREMENT','SUBMISSION_IDENTITY_MEASUREMENT','GNP_IDENTITY_MEASUREMENT','NONOVERLAPPING_REPLICATION_RESULTS','COMPARABLE_ACCESS_SEPARATION_RESULTS','EARLY_FOLD_SUPPORT','DIVISION_ERA_STABILITY','B3_B5_IDENTITY_DISTRIBUTIONS','DIRECTIONAL_MATCHUP_READINESS','SIMULATOR_IDENTITY_RECOMMENDATION']
 assert all((OUT/(n+'.md')).exists() for n in required)
 if a.rerun:
  with tempfile.TemporaryDirectory(prefix='grappling-replication-') as tmp:
   subprocess.run([sys.executable,str(R/'tools/audits/grappling_identity_separation_v1.py'),'--output-dir',tmp],check=True)
   names=sorted(p.name for p in Path(tmp).iterdir() if p.is_file())
   for n in names:assert (OUT/n).read_bytes()==(Path(tmp)/n).read_bytes(),'Nondeterministic '+n
  reports={p.name:sha(p) for p in OUT.glob('*.md')}
  gates=sha(OUT/'GATE_DECISIONS.json');secondary_hash=sha(OUT/'support_secondary_separation.csv')
  subprocess.run([sys.executable,str(R/'tools/audits/report_grappling_identity_separation_v1.py')],check=True)
  assert all(sha(OUT/n)==v for n,v in reports.items()) and sha(OUT/'GATE_DECISIONS.json')==gates and sha(OUT/'support_secondary_separation.csv')==secondary_hash
  evidence={'status':'PASS','computed_artifacts_rerun_byte_identical':names,'reports_rerun_identical':True,'independent_scalar_checks':checks,'independent_block_selector_checks':101,'frozen_membership_equal':True,'scoring_support_reconciled':True}
  if a.write_manifest:js(OUT/'REPRODUCIBILITY.json',evidence)
  else:assert json.loads((OUT/'REPRODUCIBILITY.json').read_text())==evidence
 gate=json.loads((OUT/'GATE_DECISIONS.json').read_text())
 m={'starting_main':BASE,'protocol_freeze_commit':'8be3a32181ec90471902482161826301ffb74110','branch':'feat/grappling-identity-separation-v1','conclusion':gate['conclusion'],'fits':0,'sealed_through':'2026-08-15','upstream_manifest_sha256':sha(old.OUT/'EVIDENCE_MANIFEST.json'),'artifacts':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['EVIDENCE_MANIFEST.json',MARK+'.json']},'scripts':{str(p.relative_to(R)):sha(p) for p in sorted((R/'tools/audits').glob('*grappling_identity_separation_v1.py'))}}
 m['scripts']['.github/workflows/grappling-identity-separation-v1.yml']=sha(R/'.github/workflows/grappling-identity-separation-v1.yml')
 if a.write_manifest:
  assert a.rerun,'Manifest completion requires full rerun';js(OUT/'EVIDENCE_MANIFEST.json',m);js(OUT/(MARK+'.json'),{'marker':MARK,'status':'COMPLETE','starting_main':BASE,'conclusion':gate['conclusion'],'protocol_freeze_commit':m['protocol_freeze_commit'],'evidence_manifest_sha256':sha(OUT/'EVIDENCE_MANIFEST.json'),'fits':0,'next_milestone':gate['next_milestone']})
 else:
  assert json.loads((OUT/'EVIDENCE_MANIFEST.json').read_text())==m
  assert json.loads((OUT/(MARK+'.json')).read_text())['evidence_manifest_sha256']==sha(OUT/'EVIDENCE_MANIFEST.json')
 print(json.dumps({'status':'PASS','independent_scalar_checks':checks,'manifest_sha256':sha(OUT/'EVIDENCE_MANIFEST.json')}))
if __name__=='__main__':main()
