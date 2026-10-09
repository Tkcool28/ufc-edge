#!/usr/bin/env python3
"""Frozen nonpredictive grappling measurement experiment. Offline sealed inputs only."""
import argparse, hashlib, json, lzma, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/audits'))
import audit_grappling_identity_v1 as old
OUT=R/'docs/data_audits/grappling_identity_separation_v1'
BASE='4a202a2eeb599b790323d1463288690addf3bd47'
SEED=160161
DIMS={'access':('takedowns_attempted',False,1),'control':('control_sec',True,1/60),'submission':('submission_attempts',False,1),'gnp':('sig_ground_attempted',False,1),'all_control':('control_sec',False,1/60)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,d):Path(p).write_text(json.dumps(d,sort_keys=True,indent=2,allow_nan=False)+'\n')
def save(out,n,d):old.csv(out,n,d)
def verify_inputs():
 old.verify_upstream();p=old.OUT;m=json.loads((p/'EVIDENCE_MANIFEST.json').read_text())
 assert sha(p/'EVIDENCE_MANIFEST.json')=='8c2c660722743607733f77b5c86013d36dcca46daa2417ed39487e31d1cfa849'
 for n,v in m['artifacts'].items():assert sha(p/n)==v['sha256'],n
 for n,v in m['scripts'].items():assert sha(R/n)==v,n
 return m

def state(g):
 d={'prior_fights':len(g),'prior_decisions':int(g.method.eq('DECISION').sum()),'latest_prior_date':g.event_date.max() if len(g) else None}
 for c in ['takedowns_landed','submission_attempts','sig_ground_attempted']:
  d[c]=g[c].sum(min_count=1);d[c+'_observed_bouts']=int(g[c].notna().sum())
 for key,(field,dec,scale) in DIMS.items():
  h=g[g.method.eq('DECISION')] if dec else g
  v=h[[field,'elapsed_min']].dropna();n=v[field].sum() if len(v) else np.nan;den=v.elapsed_min.sum() if len(v) else np.nan
  d[key+'_num']=n;d[key+'_den_min']=den;d[key+'_bouts']=len(v);d[key+'_missing_bouts']=len(h)-len(v)
  d[key]=scale*n/den if den>0 else np.nan
  d[key+'_supported']=bool(len(v)>=(1 if dec else 3) and den>=15)
  d[key+'_strict']=bool(d[key+'_supported'] and (len(v)>=2 if dec else len(g)>=6))
 return d

def derived_original():
 s=pd.read_csv(old.OUT/'identity_states.csv.gz');dec=pd.read_csv(old.OUT/'outcome_separated_prior_states.csv.gz');dec=dec[dec.prior_subset.eq('DECISION')].set_index(['target_fight_id','fighter_id'])
 d=s[['fighter_id','target_fight_id','cutoff','division','year','prior_fights','latest_prior_date','takedowns_landed','takedowns_landed_observed_bouts','submission_attempts','submission_attempts_observed_bouts','sig_ground_attempted','sig_ground_attempted_observed_bouts']].copy()
 dd=dec.loc[pd.MultiIndex.from_frame(d[['target_fight_id','fighter_id']])].reset_index(drop=True)
 d['prior_decisions']=dd.prior_fights.to_numpy()
 for k,m in [('access','td_attempts_per15'),('control','control_share'),('submission','sub_attempts_per_min'),('gnp','ground_attempts_per_min'),('all_control','control_share')]:
  z=dd if k=='control' else s
  for suffix,source in [('_num','_num'),('_den_min','_den'),('_bouts','_bouts')]:d[k+suffix]=z[m+source].to_numpy()
  d[k]=z[m].to_numpy()/(15 if k=='access' else 1)
  total=d.prior_decisions if k=='control' else d.prior_fights
  d[k+'_missing_bouts']=total-d[k+'_bouts']
  d[k+'_supported']=(d[k+'_bouts']>=(1 if k=='control' else 3))&d[k+'_den_min'].ge(15)
  d[k+'_strict']=d[k+'_supported']&(d[k+'_bouts'].ge(2) if k=='control' else d.prior_fights.ge(6))
 return d

def rho(x,y):
 if len(x)<25 or len(np.unique(x))<2 or len(np.unique(y))<2:return np.nan
 return float(np.corrcoef(rankdata(x),rankdata(y))[0,1])
def pearson(x,y):return float(np.corrcoef(x,y)[0,1]) if len(x)>=25 and np.std(x)>0 and np.std(y)>0 else np.nan

def corr_result(g,x,y,boot=True):
 z=g[[x,y]].dropna();a=z[x].to_numpy();b=z[y].to_numpy();r=rho(a,b);lo=hi=np.nan
 if boot and len(z)>=25 and np.isfinite(r):
  rng=np.random.default_rng(SEED);rr=[]
  for _ in range(2000):
   ix=rng.integers(0,len(z),len(z));rr.append(rho(a[ix],b[ix]))
  lo,hi=np.nanquantile(rr,[.025,.975])
 if len(z):
  am=np.median(a);bm=np.median(b);valid=(a!=am)&(b!=am)
  agree=float(np.mean((a[valid]>am)==(b[valid]>am))) if valid.any() else np.nan
 else:agree=np.nan
 return {'n':len(z),'spearman':r,'pearson':pearson(a,b),'ci_low':lo,'ci_high':hi,'direction_agreement':agree}

def cuts(s):
 h=s[s.access_supported].copy();h['access_quartile']=pd.qcut(h.access.rank(method='average'),4,labels=False,duplicates='drop')+1
 return h

def summarize(g,scope,year,division='ALL'):
 row={'scope':scope,'year':year,'division':division,'states':len(g),'fighters':g.fighter_id.nunique(),'zero_history_share':g.prior_fights.eq(0).mean(),'median_prior_fights':g.prior_fights.median(),'median_prior_decisions':g.prior_decisions.median(),'median_td_landed':g.takedowns_landed.median(),'median_sub_attempts':g.submission_attempts.median(),'median_ground_attempts':g.sig_ground_attempted.median(),'both_share':(g.control_supported&g.submission_supported&g.access_supported).mean(),'both_strict_share':(g.control_strict&g.submission_strict&g.access_strict).mean()}
 for k in DIMS:
  row[k+'_supported_share']=g[k+'_supported'].mean();row[k+'_low_support_share']=(~g[k+'_supported']).mean();row[k+'_missing_share']=g[k].isna().mean();row[k+'_zero_den_share']=g[k+'_den_min'].eq(0).mean();row[k+'_median_den_min']=g[k+'_den_min'].median();row[k+'_median_bouts']=g[k+'_bouts'].median()
 return row

def pooled_states(s,b):
 # Prior-only division totals on joint observed bouts, excluding focal fighter.
 pools={}
 for k,(field,dec,scale) in DIMS.items():
  v=b[b.method.eq('DECISION')] if dec else b
  v=v.dropna(subset=[field,'elapsed_min']).sort_values('event_date')
  for div,g in v.groupby('division'):
   pools[(k,div)]={None:g.groupby('event_date')[[field,'elapsed_min']].sum().cumsum()}
   for who,h in g.groupby('fighter_id'):pools[(k,div)][who]=h.groupby('event_date')[[field,'elapsed_min']].sum().cumsum()
 for k,(_,_,scale) in DIMS.items():
  means=[];prior_den=[]
  for t in s.itertuples():
   p=pools.get((k,t.division),{});vals=[]
   for who in [None,t.fighter_id]:
    z=p.get(who);idx=z.index.searchsorted(t.cutoff)-1 if z is not None else -1
    vals.append(z.iloc[idx].to_numpy() if idx>=0 else np.zeros(2))
   n,d=vals[0]-vals[1];means.append(scale*n/d if d>0 else np.nan);prior_den.append(d)
  s[k+'_prior_mean']=means;s[k+'_prior_den_min']=prior_den
  # Work in elapsed minutes with control numerator scaled to minutes.
  s[k+'_pooled']=(scale*s[k+'_num'].fillna(0)+15*s[k+'_prior_mean'])/(s[k+'_den_min'].fillna(0)+15)
 return s

def main(out):
 out.mkdir(parents=True,exist_ok=True);verify_inputs();b=old.load();f=pd.read_csv(R/'data/canonical/v0/fights.csv',usecols=['fight_id','fighter_a_id','fighter_b_id','weight_class']).set_index('fight_id')
 mapping_path=R/'models/challengers/mov0_hierarchical_v1/weight_class_map.json'
 assert sha(mapping_path)=='9ad4d7f701dcab2453b3ed8fe4aa500a07aabe027d7f0e951b823a8a6f7fb92e'
 mapping=json.loads(mapping_path.read_text())['literal_map']
 assert b.weight_class.dropna().isin(mapping).all()
 b['division']=b.weight_class.map(mapping).fillna('UNAVAILABLE')
 groups={w:g.sort_values(['event_date','fight_id']) for w,g in b.groupby('fighter_id')}
 folds=json.loads(lzma.decompress((old.upstream.CON/'ordered_fold_fight_ids.json.xz').read_bytes()))['folds']
 s=derived_original();s=pooled_states(s,b);save(out,'fighter_states.csv.gz',s)
 boundaries=[];blocks=[];support=[];rep=[];sep=[];regions=[];region_rep=[];divera=[];edges=[]
 for fold in folds:
  y=fold['outer_year'];cut=f'{y}-01-01';people=sorted({w for fid in fold['training'] for w in [f.loc[fid].fighter_a_id,f.loc[fid].fighter_b_id]})
  snap=[];pairs=[]
  for who in people:
   g=groups[who];g=g[g.event_date<cut];division=g.iloc[-1].division
   snap.append(dict(fighter_id=who,cutoff=cut,year=y,division=division,**state(g)))
   if len(g)>=6 and g.iloc[2].event_date<g.iloc[3].event_date:
    a=g.iloc[:3];bb=g.iloc[3:6];aa=state(a);zz=state(bb)
    for k in DIMS:
     for block,st,gg in [('first',aa,a),('next',zz,bb)]:
      if k!='control':st[k+'_supported']=st[k+'_supported'] and st[k+'_bouts']==3
      else:st[k+'_supported']=st[k+'_supported'] and st[k+'_missing_bouts']==0
      st[k+'_strict']=st[k+'_supported'] and (st[k+'_bouts']>=2 if k=='control' else True)
    row={'year':y,'fighter_id':who,'division':a.iloc[-1].division,'era':'pre2015' if a.iloc[-1].event_date<'2015-01-01' else '2015plus','first_ids':'|'.join(a.fight_id),'next_ids':'|'.join(bb.fight_id),'first_end':a.iloc[-1].event_date,'next_start':bb.iloc[0].event_date}
    for prefix,st in [('first_',aa),('next_',zz)]:row.update({prefix+k:v for k,v in st.items()})
    pairs.append(row)
  snap=pd.DataFrame(snap);snap=pooled_states(snap,b);boundaries.append(snap);v=pd.DataFrame(pairs)
  support.append(summarize(snap,'training_fighters_boundary',y))
  for scope,ids in [('training_prefight',fold['training']),('scoring_prefight',fold['scoring'])]:
   z=s[s.target_fight_id.isin(ids)]
   for div,g in [('ALL',z)]+list(z.groupby('division')):support.append(summarize(g,scope,y,div))
  for k in DIMS:
   for screen in ['positive_denominator','primary','strict']:
    z=v.copy()
    if screen!='positive_denominator':z=z[z['first_'+k+('_strict' if screen=='strict' else '_supported')]&z['next_'+k+('_strict' if screen=='strict' else '_supported')]]
    rep.append(dict(year=y,metric=k,screen=screen,**corr_result(z,'first_'+k,'next_'+k)))
  q=cuts(snap);joint=q[q.control_supported&q.submission_supported].copy()
  for quart,g in joint.groupby('access_quartile'):
   cm=g.control.median();sm=g.submission.median();g=g.copy();g['region']=(g.control>cm).astype(int)*2+(g.submission>sm).astype(int)
   sep.append(dict(year=y,scope='boundary',access_quartile=int(quart),control_cut=cm,sub_cut=sm,**corr_result(g,'control','submission',False)))
   for rg in range(4):regions.append({'year':y,'scope':'boundary','access_quartile':int(quart),'region':rg,'n':int(g.region.eq(rg).sum()),'total':len(g)})
  # Freeze first-block quartile edges on supported ACCESS, identical rank-qcut rule.
  base=v[v.first_access_supported].copy();base['q']=pd.qcut(base.first_access.rank(method='average'),4,labels=False,duplicates='drop')+1
  maxima=base.groupby('q').first_access.max().sort_index().to_numpy();bins=np.r_[-np.inf,maxima[:-1],np.inf]
  v['q_first']=pd.cut(v.first_access,bins=bins,labels=False)+1;v['q_next']=pd.cut(v.next_access,bins=bins,labels=False)+1
  for i in range(1,len(bins)):edges.append({'year':y,'q':i,'upper':float(bins[i]) if np.isfinite(bins[i]) else None})
  mask=v.first_control_supported&v.next_control_supported&v.first_submission_supported&v.next_submission_supported&v.first_access_supported&v.next_access_supported
  vv=v[mask].copy();vv['same_access']=vv.q_first.eq(vv.q_next)
  for k in ['control','submission','gnp']:
   for label,z in [('joint_all',vv),('same_access',vv[vv.same_access]),('same_access_strict',vv[vv.same_access&vv.first_control_strict&vv.next_control_strict])]:rep.append(dict(year=y,metric=k,screen=label,**corr_result(z,'first_'+k,'next_'+k)))
  for quart,g in vv.groupby('q_first'):
   # Medians fixed using first-side supported cohort, independent of next-side eligibility.
   h=base[(base.q==quart)&base.first_control_supported&base.first_submission_supported]
   cm=h.first_control.median();sm=h.first_submission.median()
   ix=g.index;vv.loc[ix,'first_region']=(g.first_control>cm).astype(int)*2+(g.first_submission>sm).astype(int);vv.loc[ix,'next_region']=(g.next_control>cm).astype(int)*2+(g.next_submission>sm).astype(int)
   for side in ['first','next']:sep.append(dict(year=y,scope='same_access_'+side,access_quartile=int(quart),control_cut=cm,sub_cut=sm,**corr_result(g[g.same_access],side+'_control',side+'_submission',False)))
  z=vv[vv.same_access].copy()
  for side in ['first','next']:
   for k in ['control','submission']:
    z[side+'_'+k+'_resrank']=z.groupby('q_first')[side+'_'+k].transform(lambda x:x.rank(pct=True)-x.rank(pct=True).mean())
   sep.append(dict(year=y,scope='same_access_'+side+'_residual',access_quartile=0,**corr_result(z,side+'_control_resrank',side+'_submission_resrank',False)))
  for rg in range(4):
   n=int(z.first_region.eq(rg).sum());ret=(z.loc[z.first_region.eq(rg),'next_region']==rg).mean();counts=z[z.first_region.eq(rg)].groupby('q_first').size();prev=sum(cnt*z[z.q_first.eq(q)].next_region.eq(rg).mean() for q,cnt in counts.items())/n if n else np.nan
   rng=np.random.default_rng(SEED);ex=[]
   arrays=[h[['first_region','next_region']].to_numpy() for _,h in z.groupby('q_first')]
   for _ in range(2000):
    total=retained=expected=0
    for arr in arrays:
     draw=arr[rng.integers(0,len(arr),len(arr))];m=draw[:,0]==rg;nn=int(m.sum())
     total+=nn;retained+=int((draw[m,1]==rg).sum());expected+=nn*float((draw[:,1]==rg).mean())
    if total:ex.append((retained-expected)/total)
   lo,hi=np.quantile(ex,[.025,.975]) if ex else (np.nan,np.nan)
   region_rep.append(dict(year=y,region=rg,n=n,total=len(z),share=n/len(z) if len(z) else np.nan,retention=ret,independence_prevalence=prev,excess=ret-prev,ci_low=lo,ci_high=hi))
  if y in range(2018,2027):
   for scope,col in [('division','division'),('era','era')]:
    for group,h in z.groupby(col):
     for k in ['control','submission']:divera.append(dict(year=y,scope=scope,group=group,metric=k,**corr_result(h,'first_'+k,'next_'+k)))
   if y==2026:
    for div in z.division.unique():
     for k in ['control','submission']:divera.append(dict(year=y,scope='leave_division_out',group=div,metric=k,**corr_result(z[z.division.ne(div)],'first_'+k,'next_'+k,False)))
  print('Boundary',y,'complete',flush=True)
  blocks.append(v.merge(vv[['fighter_id','same_access','first_region','next_region']],on='fighter_id',how='left',validate='one_to_one'))
 save(out,'boundary_states.csv.gz',pd.concat(boundaries));save(out,'block_states.csv.gz',pd.concat(blocks));save(out,'support.csv',pd.DataFrame(support));save(out,'replication.csv',pd.DataFrame(rep));save(out,'separation.csv',pd.DataFrame(sep));save(out,'regions.csv',pd.DataFrame(regions));save(out,'region_replication.csv',pd.DataFrame(region_rep));save(out,'division_era.csv',pd.DataFrame(divera));save(out,'access_edges.csv',pd.DataFrame(edges))
 # Boundary rank redundancy after stratification.
 br=[]
 for snap in boundaries:
  z=cuts(snap);z=z[z.control_supported&z.submission_supported].copy()
  for k in ['control','submission']:z[k+'_resrank']=z.groupby('access_quartile')[k].transform(lambda x:x.rank(pct=True)-x.rank(pct=True).mean())
  br.append(dict(year=int(z.year.iloc[0]),**corr_result(z,'control_resrank','submission_resrank',False)))
 save(out,'boundary_redundancy.csv',pd.DataFrame(br))
 # Strict-prior cell membership join ONLY: no method, outcomes or saved probabilities.
 ids=pd.read_csv(old.OUT/'B3_B5_identity_states.csv.gz',usecols=['target_fight_id','fighter_id','cell'])
 cell=s.merge(ids,on=['target_fight_id','fighter_id'],validate='one_to_many');save(out,'cell_states.csv.gz',cell)
 dist=[]
 for cellname,g in [('ALL_SCORED',s[s.target_fight_id.isin({fid for fold in folds for fid in fold['scoring']})])]+list(cell.groupby('cell')):
  for era,h in [('ALL',g)]+[(str(y),h) for y,h in g.groupby('year')]:
   for k in DIMS:
    for representation in ['raw','pooled']:
     v=h.loc[h[k+'_supported'],k+('_pooled' if representation=='pooled' else '')]
     row=dict(cell=cellname,year=era,metric=k,representation=representation,states=len(h),supported=len(v),support_share=len(v)/len(h))
     for q in [.1,.25,.5,.75,.9]:row['p'+str(int(q*100))]=v.quantile(q)
     dist.append(row)
 save(out,'cell_distributions.csv',pd.DataFrame(dist))
 # Decision-selection comparator and shrinkage displacement: no learned tuning.
 comp=[]
 for snap in boundaries:
  z=snap[snap.control_supported&snap.all_control_supported]
  comp.append(dict(year=int(snap.year.iloc[0]),comparison='decision_vs_all_control',**corr_result(z,'control','all_control',False)))
  for k in DIMS:
   z=snap[snap[k+'_supported']];comp.append(dict(year=int(snap.year.iloc[0]),comparison=k+'_raw_vs_pooled',**corr_result(z,k,k+'_pooled',False)))
 save(out,'sensitivity.csv',pd.DataFrame(comp))
 # Independent scalar reconstruction; invariant to target/same-date/future mutations.
 checks=0
 for t in s.iloc[np.linspace(0,len(s)-1,101,dtype=int)].itertuples():
  gg=groups.get(t.fighter_id,b.iloc[:0]);gg=gg[gg.event_date<t.cutoff];st=state(gg)
  for key in st:
   if isinstance(st[key],(float,np.floating,int,np.integer,bool)):
    v=getattr(t,key);assert (pd.isna(v) and pd.isna(st[key])) or np.isclose(v,st[key],rtol=1e-8,atol=1e-8),(key,v,st[key]);checks+=1
 for who,g in list(groups.items())[::max(1,len(groups)//30)]:
  if len(g)<2:continue
  cut=g.iloc[len(g)//2].event_date;before=state(g[g.event_date<cut]);mut=g.copy();mut.loc[mut.event_date>=cut,['control_sec','submission_attempts','takedowns_attempted','sig_ground_attempted']]=999999
  after=state(mut[mut.event_date<cut]);assert json.dumps(before,default=str,sort_keys=True)==json.dumps(after,default=str,sort_keys=True)
 assert ((s.latest_prior_date.isna())|(s.latest_prior_date<s.cutoff)).all()
 assert all(set(t.first_ids.split('|')).isdisjoint(t.next_ids.split('|')) and t.first_end<t.next_start for t in pd.concat(blocks).itertuples())
 js(out/'VALIDATION.json',{'status':'PASS','independent_scalar_checks':checks,'strict_prior':True,'same_date_future_mutation_invariant':True,'blocks_disjoint':True,'frozen_membership_source_verified':True,'fits':0,'sealed_through':'2026-08-15','prospective_outcomes_accessed':False,'states':len(s)})
 print('Measurement tables complete',out)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=OUT);a=ap.parse_args();main(a.output_dir)
