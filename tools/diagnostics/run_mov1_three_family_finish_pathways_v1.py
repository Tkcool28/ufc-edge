"""Read-only audit of pinned MOV1 OOF evidence. No estimator imports, fit or predict calls.

Metrics/bootstrap functions are loaded by AST from the frozen evaluation module, without
importing its modeling implementation. Calibration here is an evaluation diagnostic only.
"""
from pathlib import Path
import ast, gzip, hashlib, io, json, platform, sys, tarfile, tempfile
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'models/challengers/mov1_boosted_v1/run_v1'
CON=RUN.parent
LIN=ROOT/'models/mov1/run_v1'
OUT=ROOT/'docs/model_diagnostics/mov1_three_family_finish_pathways_v1'
SOURCE_HEAD='859be9fad8a1a95cf35f3e5bb99107205734ddce'
MAIN='4ec01227a4a35872eed51ce7ce67c45b02e46ebd'
F02=ROOT.parent/'attachments/f02/winner_modeling_table.parquet'
MOV0=ROOT.parent/'attachments/mov0/ufc-edge/ufc-edge/models/mov0/run_v1/oof_MOV0_MIN.csv'
EXPECTED={LIN/'EVIDENCE_MANIFEST.json':'cb21ff773489f23f4583a6487942e3edb05c817493aa04eff71a470f7b1086c6',CON/'CONTRACT_MANIFEST.json':'4593dc0056455356ea9e28191acd2fda109124ca9e18ccb07c09319e99a2849b',RUN/'EVIDENCE_MANIFEST.json':'2b6c223e31000a0ff2c4c35c8c82006c92767b49e42fd080ef012459602fe410'}
NAMES={'MOV1_MIN':'LINEAR_MIN','MOV1-XGB':'XGB','MOV1-LGBM':'LGBM','MOV1-CAT':'CAT','MOV1-BOOST-SELECT':'SELECT'}
MODELS=['LINEAR_MIN','XGB','LGBM','CAT','SELECT']
FAMILIES=['XGB','LGBM','CAT']
PRIMARY=['A1','A2','A4','B1','B2','B3','B4','B5']
METHODS=['KO_TKO','SUBMISSION','DECISION']

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def require(v,msg):
 if not v:raise ValueError(msg)
def load(p):return json.loads(Path(p).read_text())
def writej(name,d): (OUT/name).write_text(json.dumps(d,indent=2,sort_keys=True,allow_nan=False)+'\n')
def csv(name,d):d.to_csv(OUT/name,index=False,float_format='%.17g',lineterminator='\n')
def md(name,s):(OUT/name).write_text(s.rstrip()+'\n')
def table(df,cols=None):
 d=df[cols] if cols else df
 def fmt(v):
  if isinstance(v,(float,np.floating)):return f'{v:.6f}' if np.isfinite(v) else '—'
  if v is None:return '—'
  return str(v).replace('|','\\|').replace('\n',' ')
 return '\n'.join(['| '+' | '.join(map(str,d.columns))+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(fmt(v) for v in r)+' |' for r in d.itertuples(index=False,name=None)])
def pct(v):return f'{v*100:.1f}%' if pd.notna(v) else '—'
def ev_functions():
 tree=ast.parse((ROOT/'models/mov1/evaluation_v1.py').read_text())
 keep={'gate','wilson','calibration','reliability','binary_metrics','multiclass_losses','multiclass_metrics','bootstraps','comparison'}
 tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in keep]
 ns={'np':np,'pd':pd,'roc_auc_score':roc_auc_score,'METHODS':METHODS,'require':require,
 'binary_loss':lambda y,p:-(np.asarray(y)*np.log(np.clip(np.asarray(p),1e-15,1-1e-15))+(1-np.asarray(y))*np.log(1-np.clip(np.asarray(p),1e-15,1-1e-15)))}
 exec(compile(tree,'frozen_evaluation_functions','exec'),ns)
 return ns
EV=ev_functions()

def verify():
 records=[]
 for p,expected in EXPECTED.items():require(sha(p)==expected,'Required manifest mismatch '+str(p))
 for manifest,base in [(LIN/'EVIDENCE_MANIFEST.json',LIN),(RUN/'EVIDENCE_MANIFEST.json',RUN),(CON/'CONTRACT_MANIFEST.json',ROOT),(ROOT/'governance/finish_method_target_structure_v1/EVIDENCE_MANIFEST.json',ROOT/'governance/finish_method_target_structure_v1')]:
  for name,r in load(manifest)['files'].items():
   p=base/name;expected=r['sha256'] if isinstance(r,dict) else r
   require(sha(p)==expected,'Source member drift '+str(p));records.append({'path':str(p.relative_to(ROOT)),'sha256':expected})
 for name,expected in load(ROOT/'governance/finish_method_target_structure_v1/AUDIT_CONTRACT_V1.json')['source_sha256'].items():
  require(sha(ROOT/name)==expected,'Structural foundation drift '+name);records.append({'path':name,'sha256':expected})
 require(load(RUN/'FOLD_IDENTITIES.json')==load(LIN/'FOLD_IDENTITIES.json'),'Linear/boosted exact fold identities')
 for name,expected in load(RUN/'EVIDENCE_MANIFEST.json')['code_files'].items():require(sha(ROOT/name)==expected,'Frozen code drift '+name)
 f02=F02
 require(sha(f02)==load(RUN/'INPUT_VALIDATION.json')['F02_sha256'],'Corrected F02 identity')
 tabledata={}
 with tarfile.open(RUN/'EVALUATION_TABLES.tar.xz') as t:
  wanted=load(RUN/'EVALUATION_TABLE_MANIFEST.json')['files']
  require(set(t.getnames())==set(wanted),'Evaluation archive member set')
  for member in t:
   raw=t.extractfile(member).read();require(hashlib.sha256(raw).hexdigest()==wanted[member.name]['sha256'],'Evaluation member drift '+member.name)
   tabledata[member.name]=pd.read_csv(io.BytesIO(raw),float_precision='round_trip')
 # Stream all native members for identity only; no loading estimators or generating predictions.
 with tempfile.TemporaryDirectory() as temp:
  p=Path(temp)/'native.tar.xz'
  with p.open('wb') as output:
   for part in sorted(RUN.glob('NATIVE_MODELS.tar.xz.part*')):
    with part.open('rb') as s:
     for b in iter(lambda:s.read(1048576),b''):output.write(b)
  wanted=load(RUN/'NATIVE_MODEL_MANIFEST.json')['files'];seen=set()
  with tarfile.open(p) as archive:
   for member in archive:
    if not member.isfile():continue
    name=member.name.removeprefix('MODELS/');require(name in wanted,'Unexpected native member '+name)
    h=hashlib.sha256()
    s=archive.extractfile(member)
    for b in iter(lambda:s.read(1048576),b''):h.update(b)
    require(h.hexdigest()==wanted[name]['sha256'],'Native member drift '+name);seen.add(name)
  require(seen==set(wanted),'Native archive incomplete')
 spec=load(CON/'terrain_archetype_evaluation.json');d=ROOT/'governance/model_validation_bucket_v1'
 require(sha(d/'MODEL_VALIDATION_BUCKET_CONTRACT_V1.json')==spec['terrain']['contract_sha256'],'Terrain contract')
 require(sha(d/'MODEL_VALIDATION_PERCENTILE_REFERENCE_V1.json')==spec['terrain']['percentile_reference_sha256'],'Terrain reference')
 with gzip.open(d/'MODEL_VALIDATION_BUCKET_ASSIGNMENTS_V1.csv.gz','rb') as s:raw=s.read()
 require(hashlib.sha256(raw).hexdigest()==spec['terrain']['assignment_physical_sha256'],'Terrain assignments')
 pop=pd.read_csv(ROOT/'governance/finish_method_target_structure_v1/population_manifest.csv.gz')
 require(len(pop)==5658 and pop.method.ne('DECISION').sum()==2822 and not pop.fight_id.duplicated().any(),'Population counts/IDs')
 terrain=pd.read_csv(io.BytesIO(raw));z=pop.merge(terrain,on='fight_id',suffixes=('','_terrain'),validate='one_to_one')
 for col in spec['terrain']['diagnostics']:require(z[col].eq(z[col+'_terrain']).all(),'Immutable terrain drift '+col)
 x=pop[pop.event_date.ge('2018-01-01')].copy();x['outer_year']=x.event_date.str[:4].astype(int)
 x=x.sort_values(['event_date','event_id','fight_id']).reset_index(drop=True)
 require(len(x)==4260 and x.method.ne('DECISION').sum()==2115,'Outer counts')
 for fold in load(RUN/'FOLD_IDENTITIES.json')['folds']:
  year=fold.get('outer_year',fold.get('year'));q=x[x.outer_year.eq(year)]
  for key,z in [('all_eligible_scoring',q),('conditional_validation',q[q.method.ne('DECISION')])]:
   require(len(z)==fold[key]['N'],'Fold row count')
   require(hashlib.sha256(''.join(z.fight_id.astype(str)+'\n').encode()).hexdigest()==fold[key]['ordered_fight_id_sha256'],'Ordered fold identity')
 scores=tabledata['conditional_oof_all_eligible.csv']
 linear=pd.read_csv(LIN/'oof_MOV1_MIN.csv',float_precision='round_trip');scores=pd.concat([scores,linear],ignore_index=True)
 for surface,model in NAMES.items():
  q=scores[scores.surface.eq(surface)];require(len(q)==4260 and not q.fight_id.duplicated().any() and set(q.fight_id)==set(x.fight_id),'Exact scoring IDs '+surface)
  q=q.set_index('fight_id').loc[x.fight_id]
  require(np.isfinite(q.P_KO_given_finish).all() and q.P_KO_given_finish.between(0,1).all(),'Probability validity')
  require(np.allclose(q.P_SUB_given_finish,1-q.P_KO_given_finish,atol=1e-12,rtol=0),'Conditional complement')
  for col in ['event_id','event_date','outer_year']:require(np.array_equal(q[col],x[col]),'Metadata mismatch '+col)
  x[model]=q.P_KO_given_finish.to_numpy()
 comp=tabledata['composed_oof_all_eligible.csv'];F=comp[comp.system.eq('S2')].set_index('fight_id').loc[x.fight_id].F.to_numpy();x['F']=F
 sysmap={'LINEAR_MIN':'S2','XGB':'SB-XGB','LGBM':'SB-LGBM','CAT':'SB-CAT','SELECT':'SB'}
 require(set(comp.system)==set(sysmap.values()),'Composition systems')
 mov0=MOV0
 require(sha(mov0)==load(RUN/'INPUT_VALIDATION.json')['MOV0_sha256'],'MOV0 source hash')
 f=pd.read_csv(mov0,float_precision='round_trip').set_index('fight_id').loc[x.fight_id].probability.to_numpy()
 np.testing.assert_array_equal(F,f)
 for model,system in sysmap.items():
  q=comp[comp.system.eq(system)];require(len(q)==4260 and not q.fight_id.duplicated().any(),'Composed IDs')
  q=q.set_index('fight_id').loc[x.fight_id];p=np.c_[F*x[model],F*(1-x[model]),1-F]
  np.testing.assert_allclose(q[['P_'+m for m in METHODS]],p,atol=1e-12,rtol=0)
  np.testing.assert_allclose(p.sum(axis=1),1,atol=1e-12,rtol=0)
  require(np.array_equal(q.actual_method,x.method),'Composed labels')
  np.testing.assert_array_equal(q.P_DECISION,1-F)
 # Replicated aggregate metrics must match recorded evidence, not new predictions.
 finish=x[x.method.ne('DECISION')]
 for surface,model in NAMES.items():
  m=EV['binary_metrics'](finish.method.eq('KO_TKO'),finish[model]);r=load(RUN/'conditional_metrics.json')[surface]['aggregate']
  for k in ['log_loss','brier','ECE','ROC_AUC']:require(abs(m[k]-r[k])<1e-12,'Recorded aggregate drift '+model+k)
 verification={'status':'SOURCE_AND_EVIDENCE_IDENTITIES_PASSED','main':MAIN,'source_pr':121,'source_head':SOURCE_HEAD,'source_state':'open draft; unchanged at audit start','required_manifests':{str(k.relative_to(ROOT)):v for k,v in EXPECTED.items()},'source_members_checked':len(records),'evaluation_archive_members_checked':len(tabledata),'native_archive_members_checked':len(seen),'population_N':5658,'finish_population_N':2822,'outer_N_per_model':4260,'outer_finish_N_per_model':2115,'exact_fight_and_metadata_alignment':True,'corrected_F02_and_MOV0_verified':True,'immutable_terrain_and_archetype_membership':True,'decision_probabilities_identical':True,'recorded_aggregate_metrics_reproduced':True,'predictive_fits':0,'new_predictions_generated':False,'metric_runtime':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},'all_source_files':records}
 return x,tabledata,verification

def losses(q,model):
 y=q.method.eq('KO_TKO').to_numpy();p=q[model].to_numpy();return EV['binary_loss'](y,p),(p-y)**2

def simple(q,model):
 z=q[q.method.ne('DECISION')];n=len(z);ll,b=losses(z,model);bl,bb=losses(z,'LINEAR_MIN')
 return {'model':model,'all_N':len(q),'all_gate':EV['gate'](len(q)),'finish_N':n,'finish_gate':EV['gate'](n),'KO_N':int(z.method.eq('KO_TKO').sum()),'SUB_N':int(z.method.eq('SUBMISSION').sum()),'actual_KO':float(z.method.eq('KO_TKO').mean()) if n else None,'actual_SUB':float(z.method.eq('SUBMISSION').mean()) if n else None,'mean_KO':float(z[model].mean()) if n else None,'mean_SUB':float(1-z[model].mean()) if n else None,'gap':float(z[model].mean()-z.method.eq('KO_TKO').mean()) if n else None,'log_loss':float(ll.mean()) if n>=25 else None,'brier':float(b.mean()) if n>=25 else None,'ll_delta_MIN':float((ll-bl).mean()) if n>=25 else None,'brier_delta_MIN':float((b-bb).mean()) if n>=25 else None,'finish_year_counts':json.dumps(z.outer_year.value_counts().sort_index().to_dict(),sort_keys=True),'all_year_counts':json.dumps(q.outer_year.value_counts().sort_index().to_dict(),sort_keys=True),'event_N':z.event_id.nunique(),'observed_Wilson95':json.dumps(EV['wilson'](int(z.method.eq('KO_TKO').sum()),n))}

def run():
 OUT.mkdir(parents=True,exist_ok=True)
 x,t,v=verify();writej('EVIDENCE_VERIFICATION.json',v)
 spec=load(CON/'terrain_archetype_evaluation.json');arches=spec['archetypes'];finish=x[x.method.ne('DECISION')].copy()
 aggregate=[];annual=[];unc=[];panels=[];composed=[];classwise=[];composed_annual=[]
 for model in MODELS:
  q=EV['binary_metrics'](finish.method.eq('KO_TKO'),finish[model]);aggregate.append({**simple(x,model),'ECE':q['ECE'],'AUC':q['ROC_AUC'],'calibration_intercept':q['calibration']['intercept'],'calibration_slope':q['calibration']['slope']})
  for year in range(2018,2027):annual.append({'year':year,'partial_2026_through':'2026-08-15' if year==2026 else '',**simple(x[x.outer_year.eq(year)],model)})
  p=np.c_[x.F*x[model],x.F*(1-x[model]),1-x.F];q=EV['multiclass_metrics'](x.method,p)
  base=np.c_[x.F*x.LINEAR_MIN,x.F*(1-x.LINEAR_MIN),1-x.F];bm=EV['multiclass_metrics'](x.method,base)
  composed.append({'model':model,'N':len(x),'multiclass_log_loss':q['log_loss'],'summed_brier':q['brier'],'ll_delta_S2':q['log_loss']-bm['log_loss'],'brier_delta_S2':q['brier']-bm['brier']})
  for method,c in q['classwise'].items():classwise.append({'model':model,'method':method,'ECE':c['ECE'],'mean_prediction':c['mean_prediction'],'actual_frequency':c['observed_frequency'],'intercept':c['calibration']['intercept'],'slope':c['calibration']['slope'],'calibration_status':c['calibration']['status']})
  for year in range(2018,2027):
   mask=x.outer_year.eq(year);d=EV['multiclass_metrics'](x.loc[mask,'method'],p[mask]);bd=EV['multiclass_metrics'](x.loc[mask,'method'],base[mask])
   composed_annual.append({'year':year,'model':model,'N':int(mask.sum()),'log_loss':d['log_loss'],'summed_brier':d['brier'],'ll_delta_S2':d['log_loss']-bd['log_loss'],'brier_delta_S2':d['brier']-bd['brier']})
  if model in FAMILIES:
   ll,b=losses(finish,model);bl,bb=losses(finish,'LINEAR_MIN')
   for metric,delta in [('log_loss',ll-bl),('brier',b-bb)]:unc.append({'scope':'aggregate','model':model,'metric':metric,'N':len(finish),'event_N':finish.event_id.nunique(),'delta':float(delta.mean()),**EV['bootstraps'](finish,delta)})
   delta=EV['multiclass_losses'](x.method,p)-EV['multiclass_losses'](x.method,base)
   u={'scope':'composed','model':model,'metric':'multiclass_log_loss','N':len(x),'event_N':x.event_id.nunique(),'delta':float(delta.mean()),**EV['bootstraps'](x,delta)};unc.append(u)
   expected=np.zeros(len(x));expected[x.method.ne('DECISION')]=ll-bl;np.testing.assert_allclose(delta,expected,atol=1e-12,rtol=0)
 csv('AGGREGATE_CONDITIONAL_COMPARISON.csv',pd.DataFrame(aggregate));csv('ANNUAL_CONDITIONAL_COMPARISON.csv',pd.DataFrame(annual))
 csv('COMPOSED_SYSTEM_COMPARISON.csv',pd.DataFrame(composed));csv('COMPOSED_CLASSWISE_CALIBRATION.csv',pd.DataFrame(classwise));csv('COMPOSED_ANNUAL_COMPARISON.csv',pd.DataFrame(composed_annual))
 archrows=[];archannual=[];divisionrows=[];terrainrows=[];divannual=[];terrannual=[]
 for kind,groups,target,annualtarget in [('archetype',[(a+'::'+s,x[x[a].eq(s)]) for a in arches for s in ['MATCH','NO_MATCH','UNASSIGNABLE']],archrows,archannual),('division',[(a,x[x.division.eq(a)]) for a in spec['normalized_weight_classes']],divisionrows,divannual),('terrain',[(dim+'::'+str(val),x[x[dim].astype(str).eq(str(val))]) for dim in spec['terrain']['diagnostics']+['scheduled_rounds','era'] for val in sorted(set(x[dim].astype(str).unique()) | ({'MODERATE_MISSINGNESS'} if dim=='completeness_tier' else set()))],terrainrows,terrannual)]:
  for cell,q in groups:
   for model in MODELS:
    target.append({'kind':kind,'cell':cell,**simple(q,model)})
    for year in range(2018,2027):annualtarget.append({'kind':kind,'cell':cell,'year':year,**simple(q[q.outer_year.eq(year)],model)})
 csv('ALL_15_ARCHETYPE_COMPARISON.csv',pd.DataFrame(archrows));csv('ARCHETYPE_ANNUAL_COMPARISON.csv',pd.DataFrame(archannual));csv('ALL_DIVISION_COMPARISON.csv',pd.DataFrame(divisionrows));csv('DIVISION_ANNUAL_COMPARISON.csv',pd.DataFrame(divannual));csv('VALIDATION_TERRAIN_COMPARISON.csv',pd.DataFrame(terrainrows));csv('TERRAIN_ANNUAL_COMPARISON.csv',pd.DataFrame(terrannual))
 # Verify recomputed conditional records against archived reports wherever metrics were governed.
 for source,recomputed in [('all_archetype_report.csv',archrows),('division_report.csv',divisionrows),('terrain_report.csv',terrainrows)]:
  old=t[source];new={(r['cell'],r['model']):r for r in recomputed}
  for _,r in old.iterrows():
   key=(str(r['cell']) if source!='terrain_report.csv' else str(r['kind'])+'::'+str(r['cell']),NAMES[r.surface])
   if key not in new:continue
   d=new[key]
   for a,b in [('N','all_N'),('finish_N','finish_N'),('K_finish_mean','mean_KO'),('conditional_log_loss','log_loss'),('conditional_brier','brier')]:
    if pd.notna(r[a]):require(abs(float(r[a])-d[b])<1e-12,'Archived cell mismatch '+str(key)+a)
 # Fixed panel uncertainty; no automatic significance interpretation or specialist selection.
 panel=load(CON/'evaluation_panels.json');labels=[]
 for pname in ['preservation','correction']:
  cfg=panel[pname]
  for k in ['archetypes','divisions','primary','additional']:labels+=cfg.get(k,[])
 for label in dict.fromkeys(labels):
  q=finish[finish[label].eq('MATCH')] if label in finish.columns else finish[finish.division.eq(label)]
  for model in FAMILIES:
   ll,b=losses(q,model);bl,bb=losses(q,'LINEAR_MIN')
   for metric,delta in [('log_loss',ll-bl),('brier',b-bb)]:
    d={'scope':label,'model':model,'metric':metric,'N':len(q),'event_N':q.event_id.nunique(),'gate':EV['gate'](len(q)),'delta':float(delta.mean()) if len(q)>=25 else None}
    if len(q)>=25:d.update(EV['bootstraps'](q,delta))
    panels.append(d)
 writej('PAIRED_UNCERTAINTY.json',{'procedure':load(CON/'uncertainty_persistence.json')['bootstrap'],'post_run_descriptive_only':True,'not_independent_confirmation':True,'aggregate_and_composed':unc,'predefined_panels':panels})
 csv('PAIRED_UNCERTAINTY.csv',pd.DataFrame(unc+panels))
 candidates=load(RUN/'INNER_CANDIDATES.json');selected=load(RUN/'SELECTED_BY_YEAR.json');choices=[];selection=[]
 for year in range(2018,2027):
  chosen=next(r for r in selected if r['outer_year']==year)
  for family in FAMILIES:
   c=t['conditional_oof_all_eligible.csv'];rows=c[c.outer_year.eq(year)&c.surface.eq('MOV1-'+family)];require(rows.candidate_id.nunique()==1 and rows['rounds'].nunique()==1,'Family choice inconsistency')
   cid=rows.candidate_id.iloc[0];r=next(r for r in candidates if r['outer_year']==year and r['candidate_id']==cid)
   own=[r for r in candidates if r['outer_year']==year and r['family']==family];best=min(own,key=lambda r:r['inner_log_loss']);require(r['inner_log_loss']<=best['inner_log_loss']+1e-12,'Family not selected by inner loss')
   choices.append({'year':year,'family':family,'candidate_id':cid,'rounds':int(rows['rounds'].iloc[0]),'inner_log_loss':r['inner_log_loss'],'parameters':json.dumps(r['parameters'],sort_keys=True),'SELECT_family':chosen['family'],'SELECT_candidate':chosen['candidate_id']})
   q=finish[finish.outer_year.eq(year)];ll,_=losses(q,family);sl,_=losses(q,'SELECT')
   selection.append({'year':year,'family':family,'N':len(q),'selected_by_SELECT':family==chosen['family'],'family_outer_LL':float(ll.mean()),'SELECT_outer_LL':float(sl.mean()),'SELECT_minus_family_LL':float((sl-ll).mean()),'inner_family_LL':r['inner_log_loss'],'SELECT_inner_LL':chosen['inner_log_loss']})
 csv('FAMILY_SELECTED_CONFIGURATIONS.csv',pd.DataFrame(choices));csv('SELECT_VS_SHADOW_BY_YEAR.csv',pd.DataFrame(selection))
 # Deterministic examples chosen by prediction patterns, never by successful outcomes.
 # All eligible observed finishes considered; sorted IDs settle ties. Outcomes are joined for review only.
 fights=pd.read_csv(ROOT/'data/canonical/v0/fights.csv');fighters=pd.read_csv(ROOT/'data/canonical/v0/fighters.csv')
 examples=[]
 for code in ['A1','A4','B3','B5']:
  a=next(a for a in arches if a.startswith(code+'_'));q=finish[finish[a].eq('MATCH')].copy()
  q['mean_shift']=q[FAMILIES].mean(axis=1)-q.LINEAR_MIN;q['family_spread']=q[FAMILIES].max(axis=1)-q[FAMILIES].min(axis=1);q['agreement_distance']=abs(q.mean_shift)+q.family_spread
  conditions=[('largest_shift_toward_submission','mean_shift',True),('largest_shift_toward_KO','mean_shift',False),('largest_family_disagreement','family_spread',False),('closest_family_linear_agreement','agreement_distance',True)]
  for reason,col,ascending in conditions:
   for _,r in q.sort_values([col,'fight_id'],ascending=[ascending,True]).head(2).iterrows():
    item={'archetype':code,'selection_rule':reason,'fight_id':r.fight_id,'event_date':r.event_date,'year':int(r.outer_year),'actual_method':r.method,'division':r.division,'mean_shift':r.mean_shift,'family_spread':r.family_spread,**{m:r[m] for m in MODELS}}
    for m in MODELS:item[m+'_loss']=float(EV['binary_loss']([r.method=='KO_TKO'],[r[m]])[0])
    examples.append(item)
 examples=pd.DataFrame(examples)
 # Human-readable names from canonical IDs when available; IDs are always authoritative.
 fighter_names=dict(zip(fighters.fighter_id,fighters.canonical_name))
 fc=[c for c in fights.columns if 'fighter' in c];ident=fights.set_index('fight_id')
 for col in fc:
  if col.endswith('_id'):examples[col.removesuffix('_id')+'_name']=examples.fight_id.map(ident[col]).map(fighter_names)
 csv('REPRESENTATIVE_FIGHT_DISAGREEMENTS.csv',examples)
 # Full primary-cell prediction differences make example selection reviewable and include errors.
 ids=set().union(*(set(finish[finish[a].eq('MATCH')].fight_id) for a in arches if a.startswith(('A1_','A4_','B3_','B5_'))))
 full=finish[finish.fight_id.isin(ids)][['fight_id','event_id','event_date','outer_year','method','division']+[a for a in arches if a.startswith(('A1_','A4_','B3_','B5_'))]+[c for c in finish if c.startswith('state__')]+MODELS].copy()
 for model in FAMILIES:
  full[model+'_minus_MIN']=full[model]-full.LINEAR_MIN
  ll,b=losses(finish[finish.fight_id.isin(ids)],model);bl,bb=losses(finish[finish.fight_id.isin(ids)],'LINEAR_MIN');full[model+'_LL_delta']=ll-bl;full[model+'_Brier_delta']=b-bb
 csv('PRIMARY_PATHWAY_FIGHT_LEVEL_DIFFERENCES.csv',full)
 csv('FROZEN_FIXED_PROBABILITY_BUCKETS.csv',t['fixed_probability_buckets.csv'])
 writej('AUDIT_IDENTITY.json',{'audit':'MOV1_THREE_FAMILY_FINISH_PATHWAY_COMPARATIVE_AUDIT_V1','starting_main':MAIN,'starting_repository_HEAD':SOURCE_HEAD,'source_pr_121_head':SOURCE_HEAD,'branch':'audit/mov1-three-family-finish-pathways-v1','dependency':'PR121 remains unmerged; audit branch/PR depends on its exact frozen head','purpose':'post-run explanatory P(KO|STANDARD_FINISH) audit','prediction_models_fit':0,'frozen_predictions_modified':False,'BOOST_SELECT_classification':'INCONCLUSIVE','source_manifest_hashes':v['required_manifests'],'metric_functions_source':{'path':'models/mov1/evaluation_v1.py','sha256':sha(ROOT/'models/mov1/evaluation_v1.py')},'runner_sha256':sha(Path(__file__)),'example_selection':'two extrema for each of four prediction-only pattern rules per primary archetype, stable fight-ID tie-break; outcomes not used to select examples','governance':'MATCH/NO_MATCH/UNASSIGNABLE from PR117; no formula/threshold changes; separate total/finish gates; overlapping groups not independent'})
 writej('SOURCE_MANIFEST.json',v)
 writej('SOURCE_PR_STATUS.json',{'snapshot':'audit start 2026-10-01; verified through GitHub connector','main':MAIN,'113':{'merged':True,'head':'88f7e820706fb5df8ccd89c0c2f86675b870a90e'},'117':{'merged':True,'head':'4d019cc6accc4c9057053774b889613e926ff672'},'118':{'merged':True,'head':'6e14713f1f01835164e2425702b75fc81144f9e1'},'119':{'merged':True,'head':'83822191168a94f4a0eef2b9f26295c0b9492b5b'},'120':{'merged':True,'head':'532ea013b3d8765348a6ba71779e34e894d6a2d5'},'121':{'merged':False,'draft':True,'state':'open','head':SOURCE_HEAD},'continuity_note':'PROJECT_STATUS/PROJECT_MAP are pre-MOV1 navigation snapshots; merged PR118-120 and exact PR121 evidence govern this audit.'})
 generate_reports(pd.DataFrame(aggregate),pd.DataFrame(annual),pd.DataFrame(archrows),pd.DataFrame(divisionrows),pd.DataFrame(terrainrows),pd.DataFrame(archannual),pd.DataFrame(composed),pd.DataFrame(classwise),unc,panels,pd.DataFrame(selection),examples)
 md('EVIDENCE_VERIFICATION.md',f'# Evidence verification\n\nAll three required manifest digests match. Verified {v["source_members_checked"]} source artifacts, all {len(t)} evaluation archive members and all {v["native_archive_members_checked"]} native archive members. Corrected F02, MOV0, immutable terrain and the PR117 membership manifest match. All five prediction surfaces align on identical 4,260 fights and 2,115 actual finishes. Conditional complements and composed identities pass. Recorded aggregate metrics and archived cell metrics reproduce to 1e-12. No predictive fitting, refitting, new scoring or binary artifact duplication.\n\nMain `{MAIN}`; PR121 `{SOURCE_HEAD}` remains open draft at audit start. The audit is dependent on that exact evidence head; PR121 conclusions remain unchanged.')
 md('README.md','# MOV1 three-family finish-pathway comparative audit V1\n\nStart with `FINAL_AUDIT_REPORT.md` and `THREE_FAMILY_FINISH_PATHWAY_COMPARISON.md`. This is post-run explanatory evidence, not a new experiment or production selection. Reproduce with `python tools/diagnostics/run_mov1_three_family_finish_pathways_v1.py`. Accepts `--f02-table /path/to/winner_modeling_table.parquet --mov0-min-oof /path/to/oof_MOV0_MIN.csv`; defaults to the verified workspace attachment paths; uses archived predictions, no boosted estimator dependencies. All large native evidence remains solely in PR121. The audit PR is stacked on its unmerged evidence branch.')
 writej('MOV1_THREE_FAMILY_FINISH_PATHWAY_COMPARATIVE_AUDIT_V1_COMPLETE.json',{'status':'MOV1_THREE_FAMILY_FINISH_PATHWAY_COMPARATIVE_AUDIT_V1_COMPLETE','source_verification':'PASSED','prediction_model_fits':0,'source_pr_head':SOURCE_HEAD,'BOOST_SELECT':'INCONCLUSIVE','model_promotion':False})
 manifest={'audit':'MOV1_THREE_FAMILY_FINISH_PATHWAY_COMPARATIVE_AUDIT_V1','source_head':SOURCE_HEAD,'self_excluded':True,'runner':{'path':str(Path(__file__).relative_to(ROOT)),'sha256':sha(Path(__file__))},'code_files':{name:sha(ROOT/name) for name in ['tools/diagnostics/verify_mov1_three_family_finish_pathways_v1.py','tests/diagnostics/test_mov1_three_family_finish_pathways_v1.py','.github/workflows/mov1-three-family-pathway-audit-v1.yml']},'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='EVIDENCE_MANIFEST.json'}}
 writej('EVIDENCE_MANIFEST.json',manifest)
 print(json.dumps({'status':'COMPLETE','manifest_sha256':sha(OUT/'EVIDENCE_MANIFEST.json'),'artifact_count':len(manifest['files']),'fits':0},indent=2))

# Narrative/report helpers follow below.
def generate_reports(agg,annual,arches,divisions,terrain,archannual,composed,classwise,unc,panels,selection,examples):
 warning='This is descriptive reuse of already observed chronological OOF evidence. All conditional metrics use actual finishes only. It is not independent confirmation or a model/specialist promotion rule. BOOST-SELECT remains INCONCLUSIVE. Archetypes/terrain overlap; separate finish sample gates apply. 2026 is partial through August 15.'
 def matrix(data,cells,metric,percent=False):
  rows=[]
  for cell in cells:
   q=data[data.cell.eq(cell)];r=q[q.model.eq('LINEAR_MIN')].iloc[0]
   row={'Environment':cell.replace('::MATCH',''),'All N':int(r.all_N),'Finish N':int(r.finish_N),'Gate':r.finish_gate,'Actual KO':pct(r.actual_KO),'Actual SUB':pct(r.actual_SUB)}
   for m in ['LINEAR_MIN','XGB','LGBM','CAT']:
    z=q[q.model.eq(m)].iloc[0][metric];row[m]=pct(z) if percent else (f'{z:.6f}' if pd.notna(z) else '—')
   rows.append(row)
  return table(pd.DataFrame(rows))
 match=arches[arches.cell.str.endswith('::MATCH')];important=match[match.cell.str.startswith(tuple(c+'_' for c in PRIMARY))]
 cells=important.cell.drop_duplicates().tolist();keydiv=['Heavyweight','Light Heavyweight','Flyweight',"Women's Strawweight","Women's Flyweight"]
 central=pd.concat([important,divisions[divisions.cell.isin(keydiv)]],ignore_index=True);centralcells=cells+keydiv
 text='# Three-family finish-pathway comparison\n\n'+warning+'\n\nProbability table is mean P(KO/TKO | STANDARD_FINISH) over the same actual finishes. Submission is exactly 1−K. It is not P(FINISH), and decisions never count as conditional negatives.\n\n## Conditional KO probability\n\n'+matrix(central,centralcells,'mean_KO',True)+'\n\n## Individual-fight conditional log loss\n\n'+matrix(central,centralcells,'log_loss')+'\n\n## Individual-fight conditional Brier\n\n'+matrix(central,centralcells,'brier')+'\n\nLower loss/Brier is better. Means and individual probability losses answer different questions; a closer mean does not guarantee lower individual loss. Complete gaps, deltas, sample gates and annual coverage are in the comparison CSVs.\n'
 md('THREE_FAMILY_FINISH_PATHWAY_COMPARISON.md',text)
 md('ALL_FAMILY_AGGREGATE_COMPARISON.md','# Aggregate conditional comparison\n\n'+warning+'\n\n'+table(agg,['model','finish_N','actual_KO','mean_KO','log_loss','brier','AUC','ECE','calibration_intercept','calibration_slope'])+'\n\nThe same 2,115 outcomes underpin all rows. These repeat the global results already observed in PR121, not new independent evidence.')
 ar=annual.copy();ar['candidate']=''
 choices=pd.read_csv(OUT/'FAMILY_SELECTED_CONFIGURATIONS.csv');ar=ar.merge(choices[['year','family','candidate_id','rounds']],left_on=['year','model'],right_on=['year','family'],how='left')
 csv('ANNUAL_WITH_FROZEN_CONFIGURATION.csv',ar.drop(columns=['candidate','family']))
 primaryannual=archannual[archannual.cell.str.startswith(('A1_','A4_','B3_','B5_')) & archannual.cell.str.endswith('::MATCH')]
 chronology=[]
 for cell,q in primaryannual.groupby('cell',sort=False):
  for family in FAMILIES:
   a=q[q.model.eq(family)];valid=a[a.finish_N.ge(25)]
   chronology.append({'pathway':cell.split('_')[0],'family':family,'years_with_reportable_loss':len(valid),'LL_favorable_years':int(valid.ll_delta_MIN.lt(-1e-12).sum()),'Brier_favorable_years':int(valid.brier_delta_MIN.lt(-1e-12).sum()),'other_years_retained_below_gate':9-len(valid)})
 csv('PRIMARY_PATHWAY_ANNUAL_PERSISTENCE.csv',pd.DataFrame(chronology))
 md('PRIMARY_PATHWAY_CHRONOLOGICAL_STABILITY.md','# Primary pathway chronology\n\n'+warning+'\n\n'+table(pd.DataFrame(chronology))+'\n\nA1 loss improves in 5/9 years for every family. A4 improves in 7/9 for XGB/LGBM but 3/9 for CAT. B3 annual finish samples reach 25 in six years; B5 in eight. Those annual cells remain largely thin/moderate, so counts of favorable years are descriptive rather than independent tests. Every insufficient-year mean/count is retained and its performance interpretation suppressed.\n\n'+table(primaryannual[['cell','year','model','finish_N','finish_gate','actual_KO','mean_KO','log_loss','brier','ll_delta_MIN','brier_delta_MIN']]))
 md('ALL_FAMILY_ANNUAL_COMPARISON.md','# Annual conditional comparison\n\n'+warning+'\n\n'+table(ar,['year','model','finish_N','actual_KO','mean_KO','log_loss','brier','ll_delta_MIN','brier_delta_MIN','candidate_id','rounds'])+'\n\nExact effective family-specific configurations are retained in `FAMILY_SELECTED_CONFIGURATIONS.csv`. They were selected historically using inner chronology, not this audit. No unfavorable year is excluded.')
 def describe_cell(data,cell):
  q=data[data.cell.eq(cell)];b=q[q.model.eq('LINEAR_MIN')].iloc[0];pieces=[f'**{cell.replace("::MATCH", "")}**: {int(b.finish_N)} finishes ({b.finish_gate}); observed KO {pct(b.actual_KO)}, SUB {pct(b.actual_SUB)}.']
  for family in FAMILIES:
   r=q[q.model.eq(family)].iloc[0]
   if pd.isna(r.log_loss):pieces.append(f'{family}: mean KO {pct(r.mean_KO)}; performance interpretation suppressed by the <25 gate.');continue
   gapmove=abs(r.gap)-abs(b.gap);pieces.append(f'{family}: KO {pct(r.mean_KO)}, SUB {pct(r.mean_SUB)}, gap {r.gap*100:+.2f} pp; LL delta {r.ll_delta_MIN:+.6f}, Brier delta {r.brier_delta_MIN:+.6f}; absolute mean gap {"narrows" if gapmove<0 else "widens"} by {abs(gapmove)*100:.2f} pp.')
  return ' '.join(pieces)
 md('STRIKING_PRESERVATION_REPORT.md','# Striking pathway preservation\n\n'+warning+'\n\nA1 is KD creation against weak significant-striking defense; A2 is both-high damage exchange; A4 is historical KO wins against historical KO losses. These references are evaluation memberships, not new predictors. MIN does not directly contain the FULL significant-strike-defense surface; membership-specific performance does not establish a learned direct KD×strike-defense interaction.\n\n'+'\n\n'.join(describe_cell(arches,c) for c in cells if c.startswith('A'))+'\n\nElevated group KO concentration can persist while discrimination or loss worsens. A2 has 79 finishes and moderate uncertainty; do not use it as a specialist-selection rule.')
 md('GRAPPLING_SUBMISSION_CORRECTION_REPORT.md','# Grappling and submission correction\n\n'+warning+'\n\nB1 distinguishes TD attempt pressure against opponent TD defense; B2 uses conversion success against defense; B3 requires submission pressure plus TD access (both high pressure and high conversion); B4 isolates pressure with poor access; B5 uses submission pressure against faced submission-attempt vulnerability. Faced attempts are not identical to historical submission losses. These concepts remain distinct and frozen.\n\n'+'\n\n'.join(describe_cell(arches,c) for c in cells if c.startswith('B'))+'\n\nNo mean-rate target was optimized. Improved loss with a wider group mean gap is possible when individual assignments improve despite residual aggregate bias.')
 for code in ['B3','B5']:
  cell=next(c for c in cells if c.startswith(code+'_'));q=arches[arches.cell.eq(cell)];z=archannual[archannual.cell.eq(cell)]
  paragraphs=[describe_cell(arches,cell)]
  for family in FAMILIES:
   r=q[q.model.eq(family)].iloc[0];b=q[q.model.eq('LINEAR_MIN')].iloc[0];a=z[z.model.eq(family)];valid=a[a.finish_N.ge(25)];wins=int(valid.ll_delta_MIN.lt(-1e-12).sum());means=a[a.finish_N.gt(0)];bm=z[z.model.eq('LINEAR_MIN')].set_index('year')
   toward=sum(v.mean_KO<bm.loc[v.year,'mean_KO'] for _,v in means.iterrows())
   paragraphs.append(f'{family} moves toward submission in {toward}/{len(means)} observed annual group means; loss improves in {wins}/{len(valid)} years meeting the 25-finish reporting gate. Annual subgroup means and counts are retained for all nine years; unavailable gated losses are blank. Mean movement is not equivalent to stable loss improvement.')
  us=[u for u in panels if u['scope']==cell.replace('::MATCH','')]
  md(code+'_FOCUSED_DIAGNOSTIC.md','# '+code+' focused diagnostic\n\n'+warning+'\n\n'+'\n\n'.join(paragraphs)+'\n\n'+table(q,['model','all_N','finish_N','actual_KO','mean_KO','mean_SUB','gap','log_loss','brier','ll_delta_MIN','brier_delta_MIN'])+'\n\n## All annual coverage\n\n'+table(z,['year','model','finish_N','finish_gate','actual_KO','mean_KO','log_loss','ll_delta_MIN','brier_delta_MIN'])+'\n\n## Descriptive paired intervals\n\n'+table(pd.DataFrame(us),['model','metric','N','event_N','delta','fight_paired_95','event_paired_95'])+'\n\nRepresentative examples are chosen from predictions alone, with successful and unsuccessful shifts visible. See `REPRESENTATIVE_FIGHT_DISAGREEMENTS.csv` and the complete primary-cell fight-level differences.')
 md('ALL_15_ARCHETYPE_COMPARISON.md','# All 15 frozen archetypes\n\n'+warning+'\n\n## Conditional KO means\n\n'+matrix(match,match.cell.drop_duplicates().tolist(),'mean_KO',True)+'\n\n## Conditional log loss\n\n'+matrix(match,match.cell.drop_duplicates().tolist(),'log_loss')+'\n\n## Conditional Brier\n\n'+matrix(match,match.cell.drop_duplicates().tolist(),'brier')+'\n\nAll three membership statuses and every year are retained in CSV. C1 (19 finishes) and D1 (20) are insufficient; D3 (39) is thin. Descriptive means/counts for insufficient cells are shown transparently; performance interpretation is suppressed.')
 md('ALL_DIVISION_CONDITIONAL_COMPARISON.md','# Division conditional comparison\n\n'+warning+'\n\n'+matrix(divisions,divisions.cell.drop_duplicates().tolist(),'mean_KO',True)+'\n\n'+matrix(divisions,divisions.cell.drop_duplicates().tolist(),'log_loss')+'\n\n'+matrix(divisions,divisions.cell.drop_duplicates().tolist(),'brier')+'\n\n'+'\n\n'.join(describe_cell(divisions,c) for c in keydiv)+'\n\nAll divisions plus Catch Weight retained. Women’s Featherweight is insufficient; Catch Weight and women’s Bantamweight retain their own finish gates. Full annual coverage, gaps and count distributions are in CSV; no division correction is fitted.')
 keys=[c for c in terrain.cell.drop_duplicates() if any(s in c for s in ['GRAPPLE_TWO_SIDED','GRAPPLE_ONE_SIDED','STRIKE_LOW','STRIKE_ONE_SIDED','HIGH_MISSINGNESS','LOW_MISSINGNESS','5_ROUND','TITLE'])]
 md('VALIDATION_TERRAIN_COMPARISON.md','# Immutable Validation Terrain comparison\n\n'+warning+'\n\n'+matrix(terrain,keys,'log_loss')+'\n\n'+matrix(terrain,keys,'mean_KO',True)+'\n\nAll experience, layoff, duration/rounds, title, weight, completeness, striking, grappling, joint and fixed era cells are retained in CSV, with complete annual tables. GRAPPLE_TWO_SIDED has 76 finishes and STRIKE_LOW×GRAPPLE_TWO_SIDED 68: moderate, overlapping samples. They cannot be counted as independent confirmations. Unknown states are retained, never reconstructed as LOW.\n\n'+'\n\n'.join(describe_cell(terrain,c) for c in keys if c in ['grappling_environment::GRAPPLE_TWO_SIDED','grappling_environment::GRAPPLE_ONE_SIDED','striking_environment::STRIKE_LOW','striking_environment::STRIKE_ONE_SIDED']))
 u=pd.DataFrame(unc+panels)
 md('PAIRED_UNCERTAINTY_REPORT.md','# Paired descriptive uncertainty\n\n'+warning+'\n\n'+table(pd.DataFrame(unc),['scope','model','metric','N','event_N','delta','fight_paired_95','event_paired_95'])+'\n\n## Predefined preservation/correction panels\n\n'+table(pd.DataFrame(panels),['scope','model','metric','N','event_N','delta','fight_paired_95','event_paired_95'])+'\n\nMethod: frozen 2,000 replicates, seed17 reset for each comparison/kind, fight resampling or lexically ordered event-cluster resampling, fight-weighted mean and linear 2.5/97.5 percentiles. Rows are chronological event_date/event_id/fight_id. Intervals condition on fitted OOF predictions; repeated-fighter and training-selection dependence remains. No new test thresholds, significance battery or opportunistic multiple-testing treatment. These intervals cannot convert a post-hoc family choice into independent confirmation.')
 md('COMPLETE_SYSTEM_SECONDARY_COMPARISON.md','# Complete-system secondary check\n\n'+warning+'\n\nWith frozen F=MOV0-MIN and family K: P(KO)=F×K; P(SUB)=F×(1−K); P(DEC)=1−F. All 4,260 outer fights participate.\n\n'+table(composed)+'\n\n'+table(classwise)+'\n\nDEC predictions are byte-identical numerically across all surfaces; their calibration is unchanged. Composed LL gains equal 2115/4260 times conditional LL gains, so they are algebraically linked evidence. Summed Brier and classwise calibration expose additional tradeoffs. Annual complete-system results retained in CSV.')
 # Existing native diagnostics cover SELECT folds only; do not mislabel them as all-shadow importance.
 imp=pd.DataFrame(load(RUN/'IMPORTANCE.json'));co=pd.DataFrame(load(RUN/'HYPOTHESIS_SPLIT_CO_USE.json')['rows']);csv('EXISTING_SPLIT_CO_USE.csv',co)
 cov=imp.groupby(['family','kind']).outer_year.apply(lambda s:','.join(map(str,sorted(s.unique())))).reset_index(name='covered_outer_years');csv('EXISTING_IMPORTANCE_COVERAGE.csv',cov)
 native=imp[imp.kind.ne('held_out_permutation_log_loss')].copy();tops=[]
 for (family,kind),g in native.groupby(['family','kind']):
  d=g.groupby('feature').value.mean().sort_values(ascending=False).head(10)
  tops.extend({'family':family,'kind':kind,'feature':f,'mean_existing_value':val,'coverage':'SELECT folds only'} for f,val in d.items())
 csv('EXISTING_NATIVE_IMPORTANCE_TOP_FEATURES.csv',pd.DataFrame(tops))
 md('NONLINEAR_RELATIONSHIP_INTERPRETATION.md','# Existing nonlinear relationship evidence\n\n'+warning+'\n\n## Coverage\n\n'+table(cov)+'\n\nExisting IMPORTANCE and co-use diagnostics describe only the historically selected SELECT outer models: XGB 2018–2019; LGBM 2020,2022,2025–2026; CAT 2021,2023–2024. The native archives contain all shadow models and were hash-verified, but this audit does not generate new importance or new predictions. No nine-year shadow-wide importance claim is justified by these selected-fold diagnostics.\n\n## Native feature evidence within its own scale\n\n'+table(pd.DataFrame(tops))+'\n\nXGB weight is split count; gain is mean loss reduction and total_gain cumulative reduction. LGBM split and gain retain their native meanings. CatBoost PredictionValuesChange is a different importance quantity. Means above use only the listed selected-fold coverage; do not compare their scales as a library ranking. Correlation and representation split importance among variables.\n\n## Existing co-use\n\n'+table(co[['outer_year','family','hypothesis','tree_count','trees_with_both_on_a_path_or_oblivious_tree']])+'\n\nSubmission-pressure×TD-access, submission-pressure×vulnerability and KD-creation×vulnerability co-use provide descriptive evidence that trees can use both concepts in paths (XGB/LGBM) or shared oblivious split sets (CAT). They do not isolate interaction effects, direction, causality or benefits in B3/B5. KO-history×vulnerability is not isolated by the saved three-hypothesis co-use audit. KD×significant-striking-defense is not established: that direct defense predictor is outside MIN. No SHAP was computed in V1. Predictions support method-specific behavioral descriptions; they do not prove the internal mechanism.')
 md('REPRESENTATIVE_FIGHT_DISAGREEMENTS.md','# Real-fight prediction disagreements\n\n'+warning+'\n\nTwo cases per prediction-only rule per A1/A4/B3/B5: largest average movement toward submission, largest toward KO, largest family spread and closest agreement. Stable fight-ID tie break. Outcomes were not used for selection; they are shown to reveal correct and incorrect shifts. These are intentionally diagnostic extremes/agreements, not a representative sample of population frequency. Some fights appear under multiple rules/archetypes.\n\n'+table(examples,[c for c in ['archetype','selection_rule','event_date','fighter_a_name','fighter_b_name','actual_method','LINEAR_MIN','XGB','LGBM','CAT','family_spread'] if c in examples])+'\n\nAll model-specific losses and authoritative fight IDs are in CSV. Complete primary-cell differences retain every qualifying finish, not only attractive examples.')
 # Verified selection decomposition separates mechanical facts from causal hypotheses.
 selectedrows=selection[selection.selected_by_SELECT];require(np.max(abs(selectedrows.SELECT_minus_family_LL))<1e-12,'SELECT does not equal selected shadow')
 md('WHY_SELECT_DIFFERS_FROM_SHADOWS.md','# Why SELECT differs from fixed-family shadows\n\n'+warning+'\n\n## Verified behavior\n\nSELECT equals the chosen family shadow prediction in each year, with identical within-family configuration and rounds. It chooses XGB twice, LightGBM four times, CatBoost three times, using pooled preceding two inner validation years. It performs no averaging. The table reconstructs those exact choices and their outer cost/benefit against each always-family procedure.\n\n'+table(selection)+'\n\nThe all-year performance difference is a weighted sum of the years where SELECT chooses another family; no extra model was trained. A fixed-family shadow still selects configurations inside its family, so it is not one fixed hyperparameter model.\n\n## Hypotheses, not established causes\n\nShort inner windows, correlated near-tied candidates, changing method prevalence, configuration selection variability or family differences may explain why inner winners were less effective in some later years. Better aggregate shadows do not prove selector instability, overfitting or a universally superior library. Nine selections cannot disentangle these explanations. The audit preserves all years and does not select the outer-best family for production.')
 implications='''# Future research and simulator implications

Observed descriptive performance is separate from recurring behavior, future hypotheses and independently confirmed improvement. This audit answers how frozen families behave in finish-method environments; it does not authorize specialist routing.

Supported hypotheses for later preregistration: test whether a specified fixed-family architecture retains grappling/submission loss advantages without sacrificing A1/A4, Flyweight and women’s divisions; test whether historical inner-selection rules generalize beyond the short two-year selector; investigate conditional calibration with a governed training-only chronology if independently authorized. Choose the confirmation specification using disclosed observed evidence, then evaluate on genuinely new/sealed future evidence rather than rebranding this audit as a fresh test.

Before a family/specialist can be frozen: an explicit architecture/selection contract, temporally untouched confirmation data, stable conditional and complete-system losses, sufficient sample size by intended pathway, independent calibration checks, and a governed way to handle overlap, unknown state and uncertainty. A favorable cell/interval from this audit is insufficient. No routing thresholds, new features, calibration or estimators are implemented.

The hybrid simulator can retain the MOV0→MOV1 probability decomposition. Keep frozen linear MOV1-MIN/S2 as the current reference. Family disagreement and pathway residuals identify research questions and potential uncertainty signals, not already validated abstention rules. Conditional finish probabilities do not identify who wins, finish-round hazards, positions, actions or causal state transitions. Such mechanics require separate data and chronology-governed validation. Frozen MOV0’s decision overprediction cannot be repaired by changing MOV1. Sportsbook comparison remains downstream; no prices, EV or ROI are used here.
'''
 md('FUTURE_RESEARCH_IMPLICATIONS.md',implications)
 # Fifteen explicit scientific answers, with actual model-specific cell behavior.
 profiles='''XGBoost has the lowest observed aggregate conditional LL and strongest A1/A4 loss preservation among these shadows. It improves B1–B5 loss while B1/B2/B3 average KO bias widens. Its B5 submission shift is modest; Heavyweight improves, but men’s and women’s Flyweight deteriorate. LightGBM has the lowest pooled ECE and strong B1/B3 loss gains plus B5 improvement. A1/A4/HW improve, but LHW LL is slightly worse, Flyweight/women’s Flyweight worsen and partial2026 is its largest reversal. CatBoost has the highest observed AUC and lowest conditional Brier. It has the lowest observed B3/B5 losses and largest B5 submission movement, but B3 mean bias still worsens; A4 LL worsens slightly despite better Brier, A2 worsens, and Flyweight/women’s divisions remain limitations. All three are more promising descriptively than SELECT globally, with no confirmed or promoted winner.'''
 md('INDIVIDUAL_FAMILY_BEHAVIOR.md','# Individual family behavior\n\n'+warning+'\n\n'+profiles+'\n\n'+table(agg,['model','log_loss','brier','AUC','ECE','calibration_slope'])+'\n\nUse the pathway and annual tables, sample gates and paired intervals to qualify these descriptions. No model-wide causal learning claim follows from probability behavior.')
 answers=[]
 for i,family in enumerate(FAMILIES,1):
  r=agg[agg.model.eq(family)].iloc[0];a=annual[annual.model.eq(family)];wins=int(a.ll_delta_MIN.lt(-1e-12).sum())
  answers.append(f'{i}. **{family} observed finish-method information:** LL {r.log_loss:.6f}, Brier {r.brier:.6f}, ECE {r.ECE:.6f}, AUC {r.AUC:.6f}; {wins}/9 favorable outer years. Read the full pathway matrices for striking/grappling tradeoffs. “Learned” here means observed prediction behavior, not an identified causal mechanism.')
 answers.append('4. **Against linear MIN:** all three repeat the already-observed lower aggregate conditional losses/Brier and better pooled ECE; their uncertainty and nonuniform pathway changes remain material. Linear reference and SELECT remain unchanged.')
 for number,prefixes,question in [(5,['A1','A2','A4'],'Useful striking-specific behavior'),(6,['B1','B2','B3','B4','B5'],'Useful grappling/submission behavior')]:
  parts=[]
  for family in FAMILIES:
   q=match[match.model.eq(family)&match.cell.str.startswith(tuple(p+'_' for p in prefixes))];positive=q[q.ll_delta_MIN.lt(0)].cell.str.split('_').str[0].tolist();negative=q[q.ll_delta_MIN.gt(0)].cell.str.split('_').str[0].tolist()
   parts.append(f'{family}: lower observed LL in {", ".join(positive) or "none"}; higher in {", ".join(negative) or "none"}.')
  answers.append(f'{number}. **{question}:** '+' '.join(parts)+' These are descriptive environments, not validated specialist assignments.')
 for number,code in [(7,'B3'),(8,'B5')]:
  cell=next(c for c in cells if c.startswith(code+'_'));answers.append(f'{number}. **{code}:** '+describe_cell(arches,cell))
 answers.append('9. **Individual loss rather than means:** LL/Brier deltas are computed on matched real fights; full primary-cell records and successful/unsuccessful disagreement examples are retained. Group mean correction and loss improvement are reported separately.')
 parts=[]
 for f in FAMILIES:
  a=annual[annual.model.eq(f)];parts.append(f'{f} improves LL in {int(a.ll_delta_MIN.lt(-1e-12).sum())}/9 years, Brier in {int(a.brier_delta_MIN.lt(-1e-12).sum())}/9; worst LL year {int(a.loc[a.ll_delta_MIN.idxmax(),"year"])} ({a.ll_delta_MIN.max():+.6f}).')
 answers.append('10. **Chronological persistence:** '+' '.join(parts)+' A1 improves in 5/9 years for every family; A4 in 7/9 for XGB/LGBM and 3/9 for CAT. B3 loss improves in 3/6 gated years for XGB and 4/6 for LGBM/CAT; B5 in 6/8 for XGB and 5/8 for LGBM/CAT. Primary-cell annual results use the existing sample gates; all partial2026 rows remain.')
 answers.append('11. **Thin/overlapping terrain:** important two-sided-grappling and low-strike/two-sided-grapple cells have 76/68 finishes, with overlapping membership. Other broadly populated panels are also inspected. Gains do not supply independent confirmations across overlapping groups.')
 answers.append('12. **Why SELECT trails shadows:** verified annual composition is documented in WHY_SELECT_DIFFERS_FROM_SHADOWS.md; SELECT equals its selected family. The causal reason for inner/outer rank changes remains a hypothesis, not proven instability.')
 answers.append('13. **Specialist research support:** recurring paired losses, pathway-specific residuals and family disagreements can motivate a later predefined confirmation of conditional method behavior. They do not supply a production routing rule.')
 answers.append('14. **Missing confirmation:** new/sealed chronology, preregistered architecture and any specialist routing, sufficiently populated independent subgroup checks, robust calibration and complete-system validation. Reuse of these OOF outcomes is descriptive, even if an interval excludes zero.')
 answers.append('15. **Simulator:** preserve F×K, F×(1−K), 1−F decomposition and frozen linear reference. Neither native feature importance nor group rates identify causal transitions or round mechanics. No simulator is built.')
 limitations='This is post-run evidence reuse, with many correlated comparisons and no independent family promotion test. Conditional bootstrap intervals condition on fitted OOF predictions and do not exhaust training/selection/repeated-fighter uncertainty. Groups overlap; unknown handling is immutable; small finish cells suppress performance interpretation. Partial2026 ends August15. Native importance/co-use cover SELECT folds rather than every shadow-year. Correlated predictors obscure attribution; no causal or isolated interaction claims. Existing chronology fixes all rows; no favorable-era filtering, recalibration or fit is performed.'
 md('FINAL_AUDIT_REPORT.md','# MOV1 three-family finish-pathway comparative audit V1\n\n**MOV1_THREE_FAMILY_FINISH_PATHWAY_COMPARATIVE_AUDIT_V1_COMPLETE**\n\n'+warning+'\n\nMain `'+MAIN+'`; source PR121 `'+SOURCE_HEAD+'` remains unmerged draft. Separate audit branch `audit/mov1-three-family-finish-pathways-v1` depends on its exact evidence head. All required manifest, archive, population, F02/MOV0, immutable membership and probability identities pass. Zero predictive fits, zero new scoring, zero frozen source modifications.\n\n## Individual-family aggregate comparison\n\n'+table(agg,['model','finish_N','log_loss','brier','AUC','ECE','mean_KO','calibration_intercept','calibration_slope'])+'\n\n'+profiles+'\n\n## Central pathway evidence\n\n'+matrix(central,centralcells,'mean_KO',True)+'\n\n'+matrix(central,centralcells,'log_loss')+'\n\nThe dedicated THREE_FAMILY_FINISH_PATHWAY_COMPARISON.md also provides Brier. Full gaps/deltas/uncertainty and annual coverage accompany every primary environment.\n\n## Explicit scientific answers\n\n'+'\n\n'.join(answers)+'\n\n## Secondary complete-system results\n\n'+table(composed)+'\n\n## Aggregate descriptive uncertainty\n\n'+table(pd.DataFrame([r for r in unc if r['scope']=='aggregate' and r['metric']=='log_loss']),['model','N','event_N','delta','fight_paired_95','event_paired_95'])+'\n\n## Limitations\n\n'+limitations+'\n\n## Evidence map\n\nSOURCE_MANIFEST / EVIDENCE_VERIFICATION; aggregate/annual/configuration CSVs; all15 archetype statuses, division and terrain comparisons; focused B3/B5 and preservation/correction reports; primary-cell complete fight-level differences and deterministic representative examples; paired uncertainty; existing importance/co-use interpretation; composed classwise/annual results; future research implications; completion marker and SHA256 manifest. Native archives remain only in PR121. No automatic merge or promotion.')

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--f02-table',type=Path,default=F02)
 parser.add_argument('--mov0-min-oof',type=Path,default=MOV0)
 args=parser.parse_args();F02=args.f02_table;MOV0=args.mov0_min_oof
 run()
