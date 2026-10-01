"""Offline, zero-fit independent validation of audit evidence against frozen source scores."""
from pathlib import Path
import hashlib,io,json,tarfile
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
AUDIT=ROOT/'docs/model_diagnostics/mov1_three_family_finish_pathways_v1'
RUN=ROOT/'models/challengers/mov1_boosted_v1/run_v1'
PINNED={
 'models/mov1/run_v1/EVIDENCE_MANIFEST.json':'cb21ff773489f23f4583a6487942e3edb05c817493aa04eff71a470f7b1086c6',
 'models/challengers/mov1_boosted_v1/CONTRACT_MANIFEST.json':'4593dc0056455356ea9e28191acd2fda109124ca9e18ccb07c09319e99a2849b',
 'models/challengers/mov1_boosted_v1/run_v1/EVIDENCE_MANIFEST.json':'2b6c223e31000a0ff2c4c35c8c82006c92767b49e42fd080ef012459602fe410'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def require(v,msg):
 if not v:raise ValueError(msg)
def verify(directory=AUDIT):
 directory=Path(directory);manifest=load(directory/'EVIDENCE_MANIFEST.json')
 require(set(manifest['files'])=={p.name for p in directory.iterdir() if p.is_file() and p.name!='EVIDENCE_MANIFEST.json'},'Audit artifact inventory mismatch')
 for name,r in manifest['files'].items():require(sha(directory/name)==r['sha256'] and (directory/name).stat().st_size==r['bytes'],'Audit member drift '+name)
 for path,h in manifest.get('code_files',{}).items():require(sha(ROOT/path)==h,'Audit verification code drift '+path)
 require(sha(ROOT/manifest['runner']['path'])==manifest['runner']['sha256'],'Audit runner drift')
 for path,h in PINNED.items():require(sha(ROOT/path)==h,'Frozen source manifest drift '+path)
 for name,r in load(RUN/'EVIDENCE_MANIFEST.json')['files'].items():require(sha(RUN/name)==r['sha256'],'Boosted source artifact drift '+name)
 for r in load(directory/'SOURCE_MANIFEST.json')['all_source_files']:require(sha(ROOT/r['path'])==r['sha256'],'Source reference drift '+r['path'])
 with tarfile.open(RUN/'EVALUATION_TABLES.tar.xz') as t:
  expected=load(RUN/'EVALUATION_TABLE_MANIFEST.json')['files'];tables={}
  require(set(t.getnames())==set(expected),'Source table member inventory')
  for member in t:
   b=t.extractfile(member).read();require(hashlib.sha256(b).hexdigest()==expected[member.name]['sha256'],'Source table member drift')
   tables[member.name]=pd.read_csv(io.BytesIO(b),float_precision='round_trip')
 pop=pd.read_csv(ROOT/'governance/finish_method_target_structure_v1/population_manifest.csv.gz');x=pop[pop.event_date.ge('2018-01-01')].copy();x['outer_year']=x.event_date.str[:4].astype(int);x=x.sort_values(['event_date','event_id','fight_id']).reset_index(drop=True)
 source=tables['conditional_oof_all_eligible.csv'];linear=pd.read_csv(ROOT/'models/mov1/run_v1/oof_MOV1_MIN.csv',float_precision='round_trip');source=pd.concat([source,linear])
 modelmap={'LINEAR_MIN':'MOV1_MIN','XGB':'MOV1-XGB','LGBM':'MOV1-LGBM','CAT':'MOV1-CAT','SELECT':'MOV1-BOOST-SELECT'}
 for model,surface in modelmap.items():
  z=source[source.surface.eq(surface)];require(len(z)==4260 and not z.fight_id.duplicated().any() and set(z.fight_id)==set(x.fight_id),'Shared scoring IDs')
  x[model]=z.set_index('fight_id').loc[x.fight_id].P_KO_given_finish.to_numpy()
 finish=x[x.method.ne('DECISION')];require(len(finish)==2115,'Finish count')
 def loss(q,model):
  y=q.method.eq('KO_TKO').to_numpy();p=np.clip(q[model].to_numpy(),1e-15,1-1e-15)
  return -np.where(y,np.log(p),np.log1p(-p)),(q[model].to_numpy()-y)**2
 def check(q,r):
  z=q[q.method.ne('DECISION')];m=r.model;ll,b=loss(z,m);bl,bb=loss(z,'LINEAR_MIN');n=len(z)
  require(r.all_N==len(q) and r.finish_N==n,'Cell counts')
  for col,value in [('mean_KO',z[m].mean()),('actual_KO',z.method.eq('KO_TKO').mean())]:
   if n:require(abs(getattr(r,col)-value)<=1e-12,'Cell mean drift '+col)
  if n>=25:
   for col,value in [('log_loss',ll.mean()),('brier',b.mean()),('ll_delta_MIN',(ll-bl).mean()),('brier_delta_MIN',(b-bb).mean())]:require(abs(getattr(r,col)-value)<=1e-12,'Independent matched metric drift '+col)
  else:require(pd.isna(r.log_loss) and pd.isna(r.brier),'Insufficient performance gate')
 agg=pd.read_csv(directory/'AGGREGATE_CONDITIONAL_COMPARISON.csv',float_precision='round_trip')
 for r in agg.itertuples():check(x,r)
 annual=pd.read_csv(directory/'ANNUAL_CONDITIONAL_COMPARISON.csv',float_precision='round_trip')
 require(len(annual)==45 and set(annual.year)==set(range(2018,2027)),'All annual coverage')
 for r in annual.itertuples():check(x[x.outer_year.eq(r.year)],r)
 cells=0
 for filename,kind in [('ALL_15_ARCHETYPE_COMPARISON.csv','archetype'),('ALL_DIVISION_COMPARISON.csv','division'),('VALIDATION_TERRAIN_COMPARISON.csv','terrain')]:
  d=pd.read_csv(directory/filename,float_precision='round_trip')
  if kind=='archetype':require(len(d)==225 and all(set(g.cell.str.split('::').str[1])=={'MATCH','NO_MATCH','UNASSIGNABLE'} for _,g in d.groupby(d.cell.str.split('::').str[0])),'All15 statuses')
  if kind=='division':require(len(d)==65,'All division cells')
  if kind=='terrain':require(len(d[d.cell.eq('completeness_tier::MODERATE_MISSINGNESS')])==5,'Governed empty completeness tier')
  for r in d.itertuples():
   if kind=='archetype':name,status=r.cell.split('::');q=x[x[name].eq(status)]
   elif kind=='division':q=x[x.division.eq(r.cell)]
   else:name,value=r.cell.split('::');q=x[x[name].astype(str).eq(value)]
   check(q,r);cells+=1
 comp=tables['composed_oof_all_eligible.csv'];F=comp[comp.system.eq('S2')].set_index('fight_id').loc[x.fight_id].F.to_numpy();systems={'LINEAR_MIN':'S2','XGB':'SB-XGB','LGBM':'SB-LGBM','CAT':'SB-CAT','SELECT':'SB'}
 outcome=pd.Categorical(x.method,categories=['KO_TKO','SUBMISSION','DECISION']).codes;actual=np.eye(3)[outcome]
 baseline=np.c_[F*x.LINEAR_MIN,F*(1-x.LINEAR_MIN),1-F];baseLL=-np.log(baseline[np.arange(4260),outcome]);baseB=((baseline-actual)**2).sum(axis=1)
 for r in pd.read_csv(directory/'COMPOSED_SYSTEM_COMPARISON.csv').itertuples():
  p=np.c_[F*x[r.model],F*(1-x[r.model]),1-F];saved=comp[comp.system.eq(systems[r.model])].set_index('fight_id').loc[x.fight_id]
  np.testing.assert_allclose(saved[['P_KO_TKO','P_SUBMISSION','P_DECISION']],p,atol=1e-12,rtol=0)
  np.testing.assert_array_equal(saved.P_DECISION,1-F)
  ll=-np.log(p[np.arange(4260),outcome]);b=((p-actual)**2).sum(axis=1)
  for col,value in [('multiclass_log_loss',ll.mean()),('summed_brier',b.mean()),('ll_delta_S2',(ll-baseLL).mean()),('brier_delta_S2',(b-baseB).mean())]:require(abs(getattr(r,col)-value)<=1e-12,'Composed metric drift')
 selected=pd.read_csv(directory/'SELECT_VS_SHADOW_BY_YEAR.csv');require(len(selected)==27 and selected.selected_by_SELECT.sum()==9,'Selected family accounting')
 for r in selected.itertuples():
  q=finish[finish.outer_year.eq(r.year)];ll,_=loss(q,r.family);sl,_=loss(q,'SELECT');require(abs(r.SELECT_minus_family_LL-(sl-ll).mean())<1e-12,'Selection decomposition')
  if r.selected_by_SELECT:np.testing.assert_array_equal(q[r.family],q.SELECT)
 # Recompute the aggregate paired intervals independently in chunks using frozen RNG chronology.
 u=load(directory/'PAIRED_UNCERTAINTY.json');require(u['procedure']['replicates']==2000 and u['procedure']['seed']==17,'Frozen bootstrap procedure')
 for r in u['aggregate_and_composed']:
  if r['scope']!='aggregate':continue
  a,b=loss(finish,r['model']);al,bl=loss(finish,'LINEAR_MIN');delta=a-al if r['metric']=='log_loss' else b-bl
  for kind in ['fight','event']:
   rng=np.random.default_rng(17);rep=[]
   if kind=='fight':
    for _ in range(2000):rep.append(delta[rng.integers(0,len(delta),len(delta))].mean())
   else:
    ev=finish.event_id.to_numpy();events=np.array(sorted(set(ev)));sums=np.array([delta[ev==e].sum() for e in events]);counts=np.array([(ev==e).sum() for e in events])
    for _ in range(2000):
     ix=rng.choice(len(events),len(events),replace=True);rep.append(sums[ix].sum()/counts[ix].sum())
   np.testing.assert_allclose(np.quantile(rep,[.025,.975],method='linear'),r[kind+'_paired_95'],atol=1e-12,rtol=0)
 examples=pd.read_csv(directory/'REPRESENTATIVE_FIGHT_DISAGREEMENTS.csv');require(len(examples)==32,'All prediction-pattern examples')
 for r in examples.itertuples():
  q=finish[finish.fight_id.eq(r.fight_id)].iloc[0];require(q.method==r.actual_method,'Example label')
  for m in modelmap:require(abs(getattr(r,m)-q[m])<1e-12,'Example probability')
 require(load(directory/'AUDIT_IDENTITY.json')['prediction_models_fit']==0,'No-fit identity')
 marker=load(directory/'MOV1_THREE_FAMILY_FINISH_PATHWAY_COMPARATIVE_AUDIT_V1_COMPLETE.json');require(marker['source_verification']=='PASSED' and marker['BOOST_SELECT']=='INCONCLUSIVE','Completion/classification')
 return {'status':'AUDIT_EVIDENCE_VERIFIED','artifacts':len(manifest['files']),'matched_cells_checked':cells,'conditional_finishes':2115,'all_fights':4260,'bootstrap_reproduction':'aggregate LL/Brier, both kinds, all three families','additional_predictive_fits':0,'manifest_sha256':sha(directory/'EVIDENCE_MANIFEST.json')}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
