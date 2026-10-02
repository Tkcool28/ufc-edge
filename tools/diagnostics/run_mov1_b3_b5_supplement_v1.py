"""Descriptive PR123 B3/B5 from saved OOF only. No training, no modified probabilities."""
import hashlib,io,json,tarfile,pathlib,argparse,numpy as np,pandas as pd
from scipy.special import expit
from scipy.optimize import minimize
R=pathlib.Path(__file__).resolve().parents[2]
RUN=R/'models/challengers/mov1_boosted_v1/run_v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def gate(n):return 'NORMAL' if n>=100 else 'MODERATE_UNCERTAINTY' if n>=50 else 'THIN_EXPLORATORY' if n>=25 else 'INSUFFICIENT'
def calibrate(y,p):
 if len(y)<100 or len(np.unique(y))!=2 or np.std(p)<1e-5:return (None,None,'SUPPRESSED_N_CLASS_OR_VARIATION')
 lp=np.log(np.clip(p,1e-12,1-1e-12)/np.clip(1-p,1e-12,1-1e-12))
 def obj(v):
  pp=np.clip(expit(v[0]+v[1]*lp),1e-12,1-1e-12)
  return float(-np.sum(y*np.log(pp)+(1-y)*np.log(1-pp)))
 q=minimize(obj,[0.,1.],method='BFGS')
 return (float(q.x[0]),float(q.x[1]),'DIAGNOSTIC_ONLY' if q.success else 'NONCONVERGED') if np.isfinite(q.x).all() else (None,None,'NONFINITE')
def run(f02path,out):
 assert hashlib.sha256(pathlib.Path(f02path).read_bytes()).hexdigest()=='d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580'
 out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((RUN/'EVALUATION_TABLE_MANIFEST.json').read_text())['files']
 with tarfile.open(RUN/'EVALUATION_TABLES.tar.xz') as t:
  item=t.extractfile('conditional_oof_all_eligible.csv').read()
 assert sha(item)==manifest['conditional_oof_all_eligible.csv']['sha256']
 tree=pd.read_csv(io.BytesIO(item),float_precision='round_trip')
 lin=pd.read_csv(R/'models/mov1/run_v1/oof_MOV1_MIN.csv',float_precision='round_trip')
 allpred=pd.concat([tree,lin],ignore_index=True)
 names={'MOV1_MIN':'LINEAR_MIN','MOV1-XGB':'XGB','MOV1-LGBM':'LGBM','MOV1-CAT':'CAT'}
 pop=pd.read_csv(R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz')
 f=pd.read_parquet(f02path)
 feat=['f1__fs__prior_fight_count__career__raw','f2__fs__prior_fight_count__career__raw']+[f'{side}__fs__submission_attempt_rate__{typ}_per_15__career__shrunk' for side in ('f1','f2') for typ in ('created','faced')]
 # No post-boundary data; frozen labels/predictions only.
 assert len(pop)==5658 and max(pop.event_date)<='2026-08-15'
 z=pop.merge(f[['fight_id']+feat],on='fight_id',validate='one_to_one')
 z['missing_SUB']=~z[feat[2:]].notna().all(axis=1)
 exp=z[feat[:2]].min(axis=1)
 z['min_prior_experience']=pd.cut(exp,[-1,0,2,7,float('inf')],labels=['0','1-2','3-7','8+'])
 z['min_prior_experience']=z['min_prior_experience'].astype(str)
 records=[]; distributions=[]
 for arch in ('B3_TD_ACCESS_PLUS_SUB_PRESSURE','B5_SUB_PRESSURE_VS_SUB_VULNERABILITY'):
  base=z[(z[arch]=='MATCH')&(z.method.isin(['KO_TKO','SUBMISSION']))&(z.event_date>='2018-01-01')]
  assert len(base) in (224,355),('archetype finish count mismatch',arch,len(base))
  for surface,name in names.items():
   sc=allpred[allpred.surface.eq(surface)][['fight_id','P_KO_given_finish']]
   assert len(sc)==4260 and not sc.fight_id.duplicated().any()
   x=base.merge(sc,on='fight_id',validate='one_to_one')
   x['year']=x.event_date.str[:4].astype(int)
   groups=[('all','ALL',x)]
   for k in ('year','division','min_prior_experience','missing_SUB'):
    groups += [(k,str(val),part) for val,part in x.groupby(k,dropna=False,observed=True,sort=True)]
   for kind,group,t in groups:
    n=len(t);y=t.method.eq('KO_TKO').to_numpy(int);p=t.P_KO_given_finish.to_numpy(float);pp=np.clip(p,1e-15,1-1e-15)
    ll=-(y*np.log(pp)+(1-y)*np.log(1-pp));b=(y-p)**2
    inter,slope,calstat=calibrate(y,p) if kind=='all' else (None,None,'NOT_FIT_SUBGROUP')
    r={'archetype':arch,'model':name,'group_kind':kind,'group':group,'finish_N':n,'gate':gate(n),'KO_N':int(y.sum()),'SUB_N':int(n-y.sum()),'actual_KO':float(y.mean()),'pred_KO':float(p.mean()),'gap_KO':float(p.mean()-y.mean()),'log_loss':float(ll.mean()) if n>=25 else None,'brier':float(b.mean()) if n>=25 else None,'p10':float(np.quantile(p,.1)) if n>=25 else None,'p50':float(np.quantile(p,.5)) if n>=25 else None,'p90':float(np.quantile(p,.9)) if n>=25 else None,'calibration_intercept':inter,'calibration_slope':slope,'calibration_status':calstat}
    records.append(r)
   distributions.append({'archetype':arch,'model':name,'N':len(x),'null_submission_feature_N':int(x.missing_SUB.sum()),'experience_counts':x.min_prior_experience.value_counts().to_dict()})
 d=pd.DataFrame(records).sort_values(['archetype','model','group_kind','group'])
 d.to_csv(out/'B3_B5_CHRONOLOGY_DIVISION_EXPERIENCE_MISSINGNESS.csv',index=False,float_format='%.17g',lineterminator='\n')
 info={'frozen_F02_SHA256':hashlib.sha256(pathlib.Path(f02path).read_bytes()).hexdigest(),'saved_predictions_SHA256':{'boosted_archive_member':sha(item),'linear_oof':hashlib.sha256((R/'models/mov1/run_v1/oof_MOV1_MIN.csv').read_bytes()).hexdigest()},'group_rows':len(d),'no_fits_of_predictive_models':True,'calibration_regression':'evaluation-only on pooled N >=100; NEVER applied to probabilities','distribution':distributions,'file_SHA256':hashlib.sha256((out/'B3_B5_CHRONOLOGY_DIVISION_EXPERIENCE_MISSINGNESS.csv').read_bytes()).hexdigest()}
 (out/'B3_B5_DIAGNOSTIC_MANIFEST.json').write_text(json.dumps(info,sort_keys=True,indent=2)+'\n')
 print('PR123_DIAGNOSTIC_BEGIN')
 print(json.dumps({'verification':info,'all_and_missingness':d[d.group_kind.isin(['all','missing_SUB'])].replace({np.nan:None}).to_dict('records')},allow_nan=False,sort_keys=True))
 print('PR123_DIAGNOSTIC_END')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--f02',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();run(a.f02,pathlib.Path(a.output))
