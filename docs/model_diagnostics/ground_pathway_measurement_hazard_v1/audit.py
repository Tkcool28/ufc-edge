"""Diagnostic rewards only. Frozen engine imported, never replaced or trained."""
import sys,json,hashlib,copy
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.optimize import brentq
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'models/challengers/ground_pathway_simulator_poc_v1'
sys.path.insert(0,str(SRC)); import engine,abilities
OUT=Path(__file__).resolve().parent
CELLS={'B3':'B3_TD_ACCESS_PLUS_SUB_PRESSURE','B5':'B5_SUB_PRESSURE_VS_SUB_VULNERABILITY','A1':'A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE','A2':'A2_BOTH_HIGH_DAMAGE_EXCHANGE','A4':'A4_KO_HISTORY_VS_KO_VULNERABILITY'}
FACTORS=[.5,.75,1.,1.25,1.5,2.]
def account(h,rounds):
 q=engine.generator(h['entry'],h['back'],h['ground_ko'],h['submission'],h['standing_ko']);t=q[:3,:3]
 p=expm(5*t); integ=np.linalg.solve(t,p-np.eye(3))[0]
 survival=p[0].sum(); mass=sum(survival**r for r in range(rounds)); occ=integ*mass
 s,g=occ[0],occ[1:];sub=float(g@h['submission']);gko=float(g@h['ground_ko']);sko=float(s*h['standing_ko']);dec=survival**rounds
 assert min(*occ,sub,gko,sko,dec)>=-1e-12
 assert abs(sub+gko+sko+dec-1)<1e-10
 e=sum(h['entry']); z=e+h['standing_ko'];never=np.exp(-5*z)
 ever=e/z*(1-never)*sum(never**r for r in range(rounds))
 return dict(ever_entry=ever,entries=s*e,ground_minutes=g.sum(),standing_minutes=s,alive_minutes=occ.sum(),returns=float(g@h['back']),sub_attempts=float(g@h['submission_creation']),ground_actions=float(g@h['ground_activity']),sub_finishes=sub,ground_ko=gko,standing_ko=sko,raw_dec=dec,K=(sko+gko)/(sko+gko+sub),ground_share=g.sum()/occ.sum(),conversion_weighted=sub/float(g@h['submission_creation']))
def change(h,key,f):
 h=copy.deepcopy(h)
 if key=='entry':h['entry']=[v*f for v in h['entry']]
 if key=='return':h['back']=[v*f for v in h['back']]
 if key in ['attempt','conversion']:h['submission']=[v*f for v in h['submission']]
 if key=='attempt':h['submission_creation']=[v*f for v in h['submission_creation']]
 if key=='strike':
  for k in ['ground_ko','ground_activity']:h[k]=[v*f for v in h[k]]
 return h

def metrics(d):
 f=d[d.method.isin(['KO_TKO','SUBMISSION'])];y=f.method.eq('KO_TKO').to_numpy(dtype=float);k=f.K.to_numpy();k=np.clip(k,1e-15,1-1e-15)
 probs=np.c_[d.F*d.K,d.F*(1-d.K),1-d.F];truth=np.c_[d.method.eq('KO_TKO'),d.method.eq('SUBMISSION'),d.method.eq('DECISION')].astype(float)
 mll=float(-(truth*np.log(np.clip(probs,1e-15,1))).sum(axis=1).mean());mbr=float(((probs-truth)**2).sum(axis=1).mean())
 return dict(multiclass_LL=mll,summed_Brier=mbr,n=len(d),n_finish=len(f),LL=float(np.mean(-y*np.log(k)-(1-y)*np.log1p(-k))),Brier=float(np.mean((k-y)**2)),conditional_SUB=float(1-k.mean()),full_SUB=float((d.F*(1-d.K)).mean()),observed_SUB=float(d.method.eq('SUBMISSION').mean()),observed_conditional_SUB=float(1-y.mean()))
def table_rows(d,label):
 rows=[]
 groups={'ALL':d,**{c:d[d[col].eq('MATCH')] for c,col in CELLS.items()},**{str(y):g for y,g in d.groupby('outer_year')},**{'support_'+str(s):g for s,g in d.groupby('support')}}
 reward=['ever_entry','entries','ground_minutes','ground_share','returns','sub_attempts','ground_actions','sub_finishes','ground_ko','standing_ko','conversion_weighted']
 for name,g in groups.items():
  row=dict(diagnostic=label,group=name,**metrics(g));row.update({k:float(g[k].mean()) for k in reward if k in g});rows.append(row)
 return rows

def run():
 files=[p for p in SRC.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
 hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 d=pd.read_csv(SRC/'run_v1/predictions.csv.gz',float_precision='round_trip');a=pd.read_csv(SRC/'run_v1/fighter_abilities.csv.gz',float_precision='round_trip')
 support=a.groupby('fight_id').prior_fights.min();d['support']=d.fight_id.map(support).map(lambda n:'0' if n==0 else '1-2' if n<3 else '3-7' if n<8 else '8+')
 assert (pd.to_datetime(a.latest_prior_date.dropna())<pd.to_datetime(a.loc[a.latest_prior_date.notna(),'cutoff'])).all()
 records=json.loads((SRC/'run_v1/simulator_records.json').read_text()); rs={x['fight_id']:x for x in records if x['variant']=='identity'}
 assert set(rs)==set(d.fight_id) and len(d)==4260
 pools=json.loads((SRC/'run_v1/population_priors.json').read_text()); oracle={}; poolrows=[]
 for pool in pools:
  year=pool['outer_year']; assert pool['cutoff']==f'{year}-01-01'
  for div,p in pool['divisions'].items():
   h=abilities.hazards(p['rates'],p['rates'],p);base=account(h,3);target=np.clip(2*p['rates']['control'],.02,.95)
   maximum=account(change(h,'return',1e-7),3)['ground_share']
   attainable=target<maximum
   fac=brentq(lambda f:account(change(h,'return',f),3)['ground_share']-target,1e-7,1e7) if attainable else 1e-7
   af=2*p['rates']['submission']/(base['sub_attempts']/base['alive_minutes'])
   t=p['support'];gt=pool['global'];cv=t['sub_conversion_num']/t['sub_conversion_den'] if t['sub_conversion_den'] else gt['sub_conversion_num']/gt['sub_conversion_den']
   oracle[(year,div)]=(fac,af,cv)
   poolrows.append(dict(year=year,division=div,cutoff=pool['cutoff'],modeled_ground_share=base['ground_share'],target_CTRL_share=target,maximum_ground_share=maximum,occupancy_target_attainable=attainable,return_factor=fac,attempt_factor=af,conversion=cv,conversion_prior=p['rates']['sub_conversion'],conversion_success=t['sub_conversion_num'],conversion_attempts=t['sub_conversion_den'],training_TD_landed_per_fight_min=2*p['rates']['access']*p['rates']['td_conversion'],modeled_entries_per_alive_min=base['entries']/base['alive_minutes'],modeled_SUB_attempts_per_alive_min=base['sub_attempts']/base['alive_minutes'],training_SUB_attempts_per_fight_min=2*p['rates']['submission']))
 pd.DataFrame(poolrows).to_csv(OUT/'training_oracle_parameters.csv',index=False)
 labels=[('primary',None,1),('return_half','return',.5),('return_double','return',2)]+[(f'{k}_{f:g}',k,f) for k in ['entry','return','attempt','conversion','strike'] for f in FACTORS]+[(f'oracle_{s}',s,None) for s in ['occupancy','attempts','conversion_pool','combined']]
 summaries=[]; validations={'baseline_max_error':0.,'half_double_max_error':0.,'swap_max_error':0.,'one_second_max_error':0.}
 for label,key,f in labels:
  rows=[]
  for r in d.itertuples():
   h=rs[r.fight_id]
   if label.startswith('oracle_'):
    h=copy.deepcopy(h);rf,af,cv=oracle[(r.outer_year,r.division)]
    if key=='occupancy':h=change(h,'return',rf)
    if key in ['attempts','combined']:h=change(h,'attempt',af)
    if key in ['conversion_pool','combined']:h['submission']=[v*cv for v in h['submission_creation']]
   elif key:h=change(h,key,f)
   v=account(h,r.scheduled_rounds);rows.append(dict(fight_id=r.fight_id,**v))
   if label in ['primary','return_half','return_double']:
    err=abs(v['K']-getattr(r,'K_identity' if label=='primary' else 'K_'+label));field='baseline_max_error' if label=='primary' else 'half_double_max_error';validations[field]=max(validations[field],err)
   if label=='primary':
    sw=copy.deepcopy(h)
    for k in ['entry','back','ground_ko','submission','submission_creation','ground_activity']:sw[k]=h[k][::-1]
    validations['swap_max_error']=max(validations['swap_max_error'],abs(account(sw,r.scheduled_rounds)['K']-v['K']))
  res=pd.DataFrame(rows);joined=d.merge(res,on='fight_id',validate='one_to_one');summaries+=table_rows(joined,label)
  if label=='primary':
   joined.to_csv(OUT/'fight_hazard_accounting.csv.gz',index=False,float_format='%.17g',compression={'method':'gzip','mtime':0});joined.groupby('outer_year')[['ever_entry','entries','ground_minutes','returns','sub_attempts','ground_actions','sub_finishes','ground_ko','standing_ko']].agg(['mean','median','std']).to_csv(OUT/'annual_rewards.csv')
   res.describe(percentiles=[.05,.25,.5,.75,.95]).to_csv(OUT/'reward_distributions.csv')
  if label.startswith('oracle_'):res.to_csv(OUT/(label+'.csv.gz'),index=False,float_format='%.17g',compression={'method':'gzip','mtime':0})
  print(label,metrics(joined),flush=True)
 summary=pd.DataFrame(summaries);summary.to_csv(OUT/'diagnostic_summary.csv',index=False,float_format='%.17g')
 for k in ['A','C','population','pooled_conversion']:
  ref=d.copy();ref['K']=ref['K_'+k];pd.DataFrame(table_rows(ref,k)).to_csv(OUT/('reference_'+k+'.csv'),index=False)
 # raw/posterior variance within year/division; positive denominators only
 z=a[a.sub_conversion_den.gt(0)].copy();z['raw_conversion']=z.sub_conversion_num/z.sub_conversion_den
 for col in ['raw_conversion','sub_conversion']:z[col+'_residual']=z[col]-z.groupby(['outer_year','division'])[col].transform('mean')
 stats={'positive_denominator_sides':len(z),'all_sides':len(a),'raw_residual_variance':z.raw_conversion_residual.var(),'posterior_residual_variance':z.sub_conversion_residual.var(),'variance_removed_fraction':1-z.sub_conversion_residual.var()/z.raw_conversion_residual.var()}
 a[['sub_conversion_den','sub_conversion','sub_conversion_effective_support','submission','control','sub_faced','control_allowed']].describe(percentiles=[.05,.25,.5,.75,.95]).to_csv(OUT/'ability_support_distribution.csv')
 (OUT/'conversion_variance.json').write_text(json.dumps(stats,indent=2))
 for f in FACTORS:
  x=summary[summary.diagnostic.eq(f'attempt_{f:g}')].set_index('group');y=summary[summary.diagnostic.eq(f'conversion_{f:g}')].set_index('group');assert np.allclose(x.LL,y.LL,atol=1e-14)
 q=engine.generator(**{k:rs[d.fight_id.iloc[0]][k] for k in ['entry','back','ground_ko','submission','standing_ko']})
 validations['one_second_max_error']=float(np.max(abs(engine.propagate(q,3)-engine.propagate(q,3,1/60))))
 assert max(validations.values())<1e-10
 assert all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in hashes.items())
 validations.update(source_files=len(hashes),scored_fights=len(d),record_count=len(records),outer_years=sorted(map(int,d.outer_year.unique())),source_unchanged=True,training_cutoffs_valid=True)
 (OUT/'VALIDATION.json').write_text(json.dumps(validations,indent=2));(OUT/'SOURCE_HASHES.json').write_text(json.dumps(hashes,indent=2,sort_keys=True))
 # static scientific response curves
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,axes=plt.subplots(2,3,figsize=(12,7))
 for ax,metric in zip(axes.flat,['full_SUB','conditional_SUB','LL','Brier','sub_attempts','ground_minutes']):
  for key in ['entry','return','attempt','conversion','strike']:
   x=summary[summary.group.eq('ALL') & summary.diagnostic.isin([f'{key}_{f:g}' for f in FACTORS])];ax.plot(FACTORS,x[metric],marker='o',label=key)
  ax.set(title=metric,xlabel='isolated hazard factor');ax.grid(alpha=.2)
 axes[0,0].legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'sensitivity.png',dpi=150);plt.close(fig)
if __name__=='__main__':run()
