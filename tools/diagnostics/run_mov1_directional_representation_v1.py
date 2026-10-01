"""PR123 read-only F02 feasibility gates. No training, no new predictions, no outcome-selected bins."""
import argparse, hashlib, json, pathlib, numpy as np, pandas as pd
R=pathlib.Path(__file__).resolve().parents[2]
EXPECTED='d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580'
B='fs__submission_attempt_rate__'
S=['created_per_15','faced_per_15']
T=['fs__takedown_pressure__created_per_15__career__shrunk','fs__takedown_conversion__defense__career__shrunk']
def h(p):
 d=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(2**20),b''):d.update(chunk)
 return d.hexdigest()
def gate(n):return 'NORMAL' if n>=100 else 'MODERATE_UNCERTAINTY' if n>=50 else 'THIN_EXPLORATORY' if n>=25 else 'INSUFFICIENT'
def audit(f02):
 assert h(f02)==EXPECTED,'PHYSICAL F02 SHA256 MISMATCH'
 f=pd.read_parquet(f02);assert not f.fight_id.duplicated().any()
 pop=pd.read_csv(R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz')
 assert len(pop)==5658
 c=[f'{side}__{B}{n}__career__shrunk' for side in ('f1','f2') for n in S]
 td=[f'{side}__{suffix}' for side in ('f1','f2') for suffix in T]
 kd=[f'mx__knockdown_creation_vs_vulnerability__{side}__career__raw' for side in ('f1_vs_f2','f2_vs_f1')]
 allcols=c+td+kd
 assert set(allcols).issubset(f.columns)
 z=pop[['fight_id','event_date','method']].merge(f[['fight_id']+allcols],on='fight_id',validate='one_to_one')
 z['year']=z.event_date.str[:4].astype(int)
 out={'f02_physical_sha256':h(f02),'modern_N':len(z),'training':[],'collision_rule':{'scope':'all eligible complete F02 fights, no labels consulted','bin':'floor(each submission marginal mean and absolute difference / 0.10), four bins total','contrast':'max(directional_sum)-min(directional_sum) >= 0.20 raw product units within same bin; no selection of thresholds based on outcomes'},'collision':{}}
 for year in range(2018,2027):
  tr=z[(z.event_date>= '2015-01-01')&(z.event_date<f'{year}-01-01')&z.method.isin(['KO_TKO','SUBMISSION'])]
  rec={'outer_year':year,'finish_N':len(tr),'KO_N':int(tr.method.eq('KO_TKO').sum()),'SUB_N':int(tr.method.eq('SUBMISSION').sum()),'each_literal_nonnull':{k:int(tr[k].notna().sum()) for k in allcols},'submission_four_complete_N':int(tr[c].notna().all(axis=1).sum()),'submission_plus_takedown_complete_N':int(tr[c+td].notna().all(axis=1).sum()),'all_candidates_including_KD_complete_N':int(tr[allcols].notna().all(axis=1).sum())}
  out['training'].append(rec)
 q=z.dropna(subset=c).copy()
 p1,p2,v1,v2=(q[k].to_numpy(float) for k in [c[0],c[2],c[1],c[3]])
 q['directional_sum']=p1*v2+p2*v1
 q['mP']=(p1+p2)/2;q['dP']=abs(p1-p2);q['mV']=(v1+v2)/2;q['dV']=abs(v1-v2)
 for n in ['mP','dP','mV','dV']:q['bin_'+n]=np.floor(q[n]/.1).astype(int)
 grp=q.groupby(['bin_'+n for n in ['mP','dP','mV','dV']],dropna=False).directional_sum.agg(['size','min','max'])
 qualifying=grp[(grp['size']>=2)&((grp['max']-grp['min'])>=.2)]
 out['collision']={'submission_complete_N':len(q),'multi_fight_bins':int((grp['size']>=2).sum()),'contrasting_bins':len(qualifying),'fights_in_contrasting_bins':int(qualifying['size'].sum()),'share_of_complete':float(qualifying['size'].sum()/len(q)) if len(q) else None,'max_within_bin_directional_range':float((grp['max']-grp['min']).max()) if len(grp) else None,'exact_original_vector_collision_claimed':False}
 assert out['training'][0]['finish_N']==707
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--f02',required=True);p.add_argument('--output');a=p.parse_args()
 print('PR123_F02_EMPIRICAL_EVIDENCE_BEGIN')
 e=audit(a.f02)
 if a.output:
  dest=pathlib.Path(a.output);dest.mkdir(parents=True,exist_ok=True)
  (dest/'F02_TRAINING_COMPLETENESS_AND_ALIGNMENT.json').write_text(json.dumps(e,sort_keys=True,indent=2,allow_nan=False)+chr(10))
 print(json.dumps(e,sort_keys=True,allow_nan=False))
 print('PR123_F02_EMPIRICAL_EVIDENCE_END')
