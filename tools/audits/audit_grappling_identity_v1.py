#!/usr/bin/env python3
"""Strict-prior descriptive audit. No predictive imports, fits or style labels."""
from pathlib import Path
import argparse, hashlib, json, lzma, sys
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/audits'))
import audit_ground_opportunity_competing_pathways_v1 as upstream
BASE='b8194cd37831348bd856900cba134d05ff21e430'
OLD=R/'docs/data_audits/ground_opportunity_competing_pathways_v1'
OUT=R/'docs/data_audits/grappling_identity_competing_pathways_v1'
# Outcome-blind support screens, sensitivity only; not claims of reliability.
# metric: numerator, denominator, scale, denominator screen, minimum matched bouts
METRICS={
 'td_attempts_per15':('takedowns_attempted','elapsed_min',15,15,3),
 'td_landed_per15':('takedowns_landed','elapsed_min',15,15,3),
 'failed_td_per15':('failed_td','elapsed_min',15,15,3),
 'td_conversion':('takedowns_landed','takedowns_attempted',1,5,3),
 'td_defense':('opponent_failed_td','opponent_td_attempts',1,5,3),
 'control_share':('control_sec','elapsed_min',1/60,15,3),
 'control_sec_per_fight':('control_sec','one',1,3,3),
 'control_sec_per_td':('control_sec','takedowns_landed',1,5,3),
 'control_allowed_share':('control_sec_allowed','elapsed_min',1/60,15,3),
 'sub_attempts_per_fight':('submission_attempts','one',1,3,3),
 'sub_attempts_per_min':('submission_attempts','elapsed_min',1,15,3),
 'sub_attempts_per_td':('submission_attempts','takedowns_landed',1,5,3),
 'sub_attempts_per_control_min_PROXY':('submission_attempts','control_sec',60,300,3),
 'sub_attempts_faced_per_min':('submission_attempts_faced','elapsed_min',1,15,3),
 'sub_wins_per_fight':('sub_win','one',1,3,3),
 'ground_attempts_per_fight':('sig_ground_attempted','one',1,3,3),
 'ground_attempts_per_min':('sig_ground_attempted','elapsed_min',1,15,3),
 'ground_landed_per_fight':('sig_ground_landed','one',1,3,3),
 'ground_attempts_allowed_per_min':('ground_attempts_allowed','elapsed_min',1,15,3),
 'ground_attempts_per_td':('sig_ground_attempted','takedowns_landed',1,5,3),
 'ground_attempts_per_control_min_PROXY':('sig_ground_attempted','control_sec',60,300,3),
 'sub_to_ground_attempts_PROXY':('submission_attempts','sig_ground_attempted',1,20,3),
 'reversals_per15':('reversals','elapsed_min',15,15,3),
 'duration_min_per_fight':('elapsed_min','one',1,3,3),
 'early_sub_win_share':('early_sub_win','sub_win',1,3,3),
 'early_ko_win_share':('early_ko_win','ko_win',1,3,3),
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csv(out,n,d):d.to_csv(out/n,index=False,float_format='%.10g',lineterminator='\n',compression={'method':'gzip','mtime':0} if n.endswith('.gz') else None)
def js(out,n,d):(out/n).write_text(json.dumps(d,sort_keys=True,indent=2,allow_nan=False)+'\n')
def verify_upstream():
 m=json.loads((OLD/'EVIDENCE_MANIFEST.json').read_text());assert sha(OLD/'EVIDENCE_MANIFEST.json')=='6fe5387b3d4b184fc61e2c1c1ca1fe0844daa8b6b6e056ac83e62c86d5dd447b'
 for n,v in m['artifacts'].items():assert sha(OLD/n)==v['sha256'],n
 for v in m['sources']:assert sha(R/v['path'])==v['sha256'],v['path']
 for n,v in m['scripts'].items():assert sha(R/n)==(v['sha256'] if isinstance(v,dict) else v),n
 return m
def load():
 b=pd.read_csv(OLD/'bout_measurements.csv.gz'); f=pd.read_csv(R/'data/canonical/v0/fights.csv')
 # Filter by the already verified sealed bout identities BEFORE outcome join.
 f=f[f.fight_id.isin(b.fight_id)]
 b=b.merge(f[['fight_id','method','result','winner_id','finish_round','finish_time_sec','scheduled_rounds']],on='fight_id',validate='many_to_one')
 assert b.event_date.max()<='2026-08-15'
 b['one']=1.;b['failed_td']=b.takedowns_attempted-b.takedowns_landed
 opp=b[['fight_id','fighter_id','takedowns_attempted','failed_td','sig_ground_attempted']].rename(columns={'fighter_id':'opponent_id','takedowns_attempted':'opponent_td_attempts','failed_td':'opponent_failed_td','sig_ground_attempted':'ground_attempts_allowed'})
 ids=f[['fight_id','fighter_a_id','fighter_b_id']].set_index('fight_id')
 b['opponent_id']=[ids.loc[x].fighter_b_id if ids.loc[x].fighter_a_id==who else ids.loc[x].fighter_a_id for x,who in zip(b.fight_id,b.fighter_id)]
 b=b.merge(opp,on=['fight_id','opponent_id'],validate='one_to_one')
 b['ko_win']=((b.method=='KO_TKO')&(b.result=='win_loss')&(b.winner_id==b.fighter_id)).astype(float)
 b['early_sub_win']=((b.sub_win==1)&(b.finish_round==1)).astype(float)
 b['early_ko_win']=((b.ko_win==1)&(b.finish_round==1)).astype(float)
 return b
def state(g):
 d={'prior_fights':len(g),'latest_prior_date':g.event_date.max() if len(g) else None}
 fields={c:g[c].to_numpy(dtype=float) for c in set([c for spec in METRICS.values() for c in spec[:2]]+['takedowns_landed','control_sec','submission_attempts','sig_ground_attempted'])}
 for c in ['takedowns_landed','control_sec','submission_attempts','sig_ground_attempted']:
  v=fields[c];d[c]=float(np.nansum(v)) if np.isfinite(v).any() else np.nan;d[c+'_observed_bouts']=int(np.isfinite(v).sum())
 for m,(num,den,scale,screen,minb) in METRICS.items():
  valid=np.isfinite(fields[num])&np.isfinite(fields[den]);nb=int(valid.sum());n=float(fields[num][valid].sum()) if nb else np.nan;v=float(fields[den][valid].sum()) if nb else np.nan
  d[m+'_num']=n;d[m+'_den']=v;d[m+'_bouts']=nb
  d[m]=scale*n/v if v>0 else np.nan
  d[m+'_supported']=bool(nb>=minb and v>=screen)
 return d
def support(g,scope,y,division):
 rows=[]
 for m in METRICS:
  den=g[m+'_den'];v=g[m].dropna()
  row={'scope':scope,'year':y,'division':division,'metric':m,'states':len(g),'fighters':g.fighter_id.nunique(),'nonmissing_histories':int(den.notna().sum()),'zero_denominators':int(den.eq(0).sum()),'median_prior_fights':g.prior_fights.median(),'no_prior_ufc_pct':100*g.prior_fights.eq(0).mean(),'median_td':g.takedowns_landed.median(),'median_control_sec':g.control_sec.median(),'median_sub_attempts':g.submission_attempts.median(),'median_ground_attempts':g.sig_ground_attempted.median(),'supported_pct':100*g[m+'_supported'].mean(),'complete_history_pct':100*((g[m+'_bouts']==g.prior_fights)&g.prior_fights.gt(0)).mean()}
  for q in [.1,.25,.5,.75,.9]:row['ratio_p'+str(int(q*100))]=v.quantile(q);row['den_p'+str(int(q*100))]=den.quantile(q)
  rows.append(row)
 return rows
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=OUT);args=ap.parse_args();out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
 manifest=verify_upstream();b=load();groups={who:g.sort_values(['event_date','fight_id']) for who,g in b.groupby('fighter_id')}
 pop=pd.read_csv(R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz')
 folds=json.loads(lzma.decompress((upstream.CON/'ordered_fold_fight_ids.json.xz').read_bytes()))['folds']
 evidence,arch=upstream.recover_evidence();assert evidence.event_date.max()<='2026-08-15'
 f=pd.read_csv(R/'data/canonical/v0/fights.csv').set_index('fight_id')
 # Never use target outcome in its own state; same-date history entirely excluded.
 states=[];subset_states=[]
 for t in pop.sort_values(['event_date','fight_id']).itertuples():
  for who in sorted([f.loc[t.fight_id].fighter_a_id,f.loc[t.fight_id].fighter_b_id]):
   g=groups.get(who,b.iloc[:0]);g=g[g.event_date<t.event_date]
   common={'fighter_id':who,'target_fight_id':t.fight_id,'cutoff':t.event_date,'division':t.division,'year':int(t.event_date[:4])}
   states.append(dict(common,**state(g)))
   for kind in ['DECISION','SUBMISSION','KO_TKO']:
    subset_states.append(dict(common,prior_subset=kind,**state(g[g.method==kind])))
 s=pd.DataFrame(states);ss=pd.DataFrame(subset_states)
 assert ((s.latest_prior_date.isna())|(s.latest_prior_date<s.cutoff)).all()
 csv(out,'identity_states.csv.gz',s);csv(out,'outcome_separated_prior_states.csv.gz',ss)
 cov=[];stab=[];matched=[];timing=[]
 for fold in folds:
  y=fold['outer_year'];cut=f'{y}-01-01';train=set(fold['training']);score=set(fold['scoring'])
  people=sorted({who for fid in train for who in [f.loc[fid].fighter_a_id,f.loc[fid].fighter_b_id]})
  snaps=[];pairs=[]
  for who in people:
   g=groups[who];g=g[g.event_date<cut];snaps.append(dict(fighter_id=who,**state(g)))
   # Equal-length NONOVERLAPPING, first3 vs next3 prior fights. No reliability tuning.
   if len(g)>=6 and g.iloc[2].event_date<g.iloc[3].event_date:
    a=state(g.iloc[:3]);bb=state(g.iloc[3:6]);pairs.append((who,a,bb))
  snap=pd.DataFrame(snaps)
  cov+=support(snap,'training_fighters_boundary',y,'ALL')
  for scope,ids in [('training_prefight',train),('scoring_prefight',score)]:
   z=s[s.target_fight_id.isin(ids)]
   for div,g in [('ALL',z)]+list(z.groupby('division')):cov+=support(g,scope,y,div)
  for m in METRICS:
   for screen in ['positive_denominator','supported_both_blocks']:
    vals=[(a[m],bb[m]) for _,a,bb in pairs if np.isfinite(a[m]) and np.isfinite(bb[m]) and (screen=='positive_denominator' or (a[m+'_supported'] and bb[m+'_supported']))]
    v=pd.DataFrame(vals,columns=['first3','next3']);rho=v.corr(method='spearman').iloc[0,1] if len(v)>=25 else np.nan
    stab.append({'year':y,'metric':m,'screen':screen,'unique_fighters':len(v),'spearman':rho,'median_first3':v.first3.median(),'median_next3':v.next3.median()})
  # Comparable access: outcome-blind within-boundary TD-attempt-rate quartiles.
  z=snap[snap.td_attempts_per15_supported].copy()
  if len(z):z['access_quartile']=pd.qcut(z.td_attempts_per15.rank(method='average'),4,labels=False,duplicates='drop')+1
  for q,g in z.groupby('access_quartile'):
   for m in ['control_share','sub_attempts_per_min','ground_attempts_per_min','sub_attempts_per_td','ground_attempts_per_td']:
    v=g.loc[g[m+'_supported'],m];matched.append({'year':y,'access_quartile':int(q),'metric':m,'fighters':len(g),'supported_fighters':len(v),'access_min':g.td_attempts_per15.min(),'access_max':g.td_attempts_per15.max(),'p10':v.quantile(.1),'p25':v.quantile(.25),'p50':v.median(),'p75':v.quantile(.75),'p90':v.quantile(.9)})
  # Unique bouts; timing by era and scheduled length, no modern-rule shortcut.
  tb=b[b.event_date<cut].drop_duplicates('fight_id')
  for scope,gg in [('all_prior',tb),('modern_2015_prior',tb[tb.event_date>='2015-01-01'])]:
   for method,g in gg[gg.method.isin(['SUBMISSION','KO_TKO'])].groupby('method'):
    for sched,h in [('ALL',g)]+[(str(k),h) for k,h in g.groupby('scheduled_rounds')]:
     timing.append({'year':y,'scope':scope,'method':method,'scheduled_rounds':sched,'bouts':len(h),'elapsed_known':h.elapsed_min.notna().sum(),'median_elapsed_min':h.elapsed_min.median(),'R1_pct':100*h.finish_round.eq(1).mean(),'R2_pct':100*h.finish_round.eq(2).mean(),'R3plus_pct':100*h.finish_round.ge(3).mean(),'round_missing':h.finish_round.isna().sum()})
 csv(out,'chronological_support.csv',pd.DataFrame(cov));csv(out,'nonoverlapping_stability.csv',pd.DataFrame(stab));csv(out,'matched_access_dimensions.csv',pd.DataFrame(matched));csv(out,'finish_timing.csv',pd.DataFrame(timing))
 # Timing repeatability on independent prior win pairs. Only first versus second win.
 ts=[]
 for y in range(2018,2027):
  for method,win in [('SUBMISSION','sub_win'),('KO_TKO','ko_win')]:
   pairs=[]
   for who,g in groups.items():
    h=g[(g.event_date<f'{y}-01-01')&g[win].eq(1)]
    if len(h)>=2 and h.iloc[0].event_date<h.iloc[1].event_date:pairs.append((h.iloc[0].finish_round==1,h.iloc[1].finish_round==1))
   v=pd.DataFrame(pairs,columns=['first_early','second_early'])
   for first in [False,True]:
    h=v[v.first_early==first];ts.append({'year':y,'method':method,'first_R1':first,'fighters':len(h),'second_R1_pct':100*h.second_early.mean() if len(h) else np.nan})
 csv(out,'repeat_finish_timing.csv',pd.DataFrame(ts))
 # Boundary histories: decisions versus own finish wins, matched within fighter.
 ds=[];duration_assoc=[]
 for y in range(2018,2027):
  snaps=[]
  for who,g in groups.items():
   h=g[g.event_date<f'{y}-01-01'];a=state(h[h.method=='DECISION']);sub=state(h[h.sub_win.eq(1)]);ko=state(h[h.ko_win.eq(1)])
   snaps.append(dict(fighter_id=who,**state(h)))
   for kind,bb in [('own_SUB_wins',sub),('own_KO_wins',ko)]:
    if a['control_share_bouts']>=1 and bb['control_share_bouts']>=1:
     ds.append({'year':y,'fighter_id':who,'finish_subset':kind,'decision_bouts':a['control_share_bouts'],'finish_bouts':bb['control_share_bouts'],'decision_control_share':a['control_share'],'finish_control_share':bb['control_share'],'decision_control_sec_per_fight':a['control_sec_per_fight'],'finish_control_sec_per_fight':bb['control_sec_per_fight'],'decision_duration_min':a['duration_min_per_fight'],'finish_duration_min':bb['duration_min_per_fight']})
  snap=pd.DataFrame(snaps)
  for m in ['control_share','sub_attempts_per_min']:
   v=snap[snap[m+'_supported']&snap.duration_min_per_fight_supported]
   duration_assoc.append({'year':y,'metric':m,'fighters':len(v),'spearman_with_mean_duration':v[[m,'duration_min_per_fight']].corr(method='spearman').iloc[0,1]})
 csv(out,'paired_decision_finish_control.csv',pd.DataFrame(ds));csv(out,'duration_associations.csv',pd.DataFrame(duration_assoc))
 # Cell distributions preserve all scored bouts, not finish-only selected histories.
 cells=[];panel=[]
 for cell,col,n in [('B3','B3_TD_ACCESS_PLUS_SUB_PRESSURE',224),('B5','B5_SUB_PRESSURE_VS_SUB_VULNERABILITY',355)]:
  e=evidence[evidence[col]=='MATCH'];ef=e[e.method.isin(['SUBMISSION','KO_TKO'])];assert len(ef)==n
  assert evidence.set_index('fight_id')[col].equals(pop.set_index('fight_id').loc[evidence.fight_id,col])
  z=s[s.target_fight_id.isin(e.fight_id)].copy();z['cell']=cell;panel.append(z)
  for era,g in [('ALL',z)]+[(str(y),g) for y,g in z.groupby('year')]:
   rows=support(g,cell,era,'ALL');cells+=rows
  js(out,cell+'_FROZEN.json',{'all_bouts':len(e),'standard_finishes':n,'observed_sub':float(ef.method.eq('SUBMISSION').mean()),'Arm_A_sub':float((1-ef.K_A).mean()),'Arm_C_sub':float((1-ef.K_C).mean()),'membership_column':col})
 csv(out,'B3_B5_identity_states.csv.gz',pd.concat(panel));csv(out,'B3_B5_identity_distributions.csv',pd.DataFrame(cells))
 # Invariance with an experienced fighter and a real mid-history cutoff.
 who=next(w for w,g in groups.items() if len(g)>=8);g=groups[who];cut=g.iloc[4].event_date
 prior=g[g.event_date<cut];mut=g.copy();future=mut.event_date>=cut
 numeric=mut.select_dtypes(include='number').columns;mut.loc[future,numeric]=999999
 def stable(d):return json.dumps(d,sort_keys=True,default=str)
 assert stable(state(prior))==stable(state(mut[mut.event_date<cut]))
 # Independently verify canonical counts for 17538 bout-sides on source-complete fields.
 st=pd.read_csv(R/'data/canonical/v0/fighter_round_stats.csv');st=st[st.fight_id.isin(b.fight_id)]
 checks=0
 for field in upstream.RAW:
  agg=st.groupby(['fight_id','fighter_id'])[field].agg(['sum','count'])
  for t in b[b[field].notna()].itertuples():
   v=agg.loc[(t.fight_id,t.fighter_id)];assert v['count']==t.expected_rounds;assert v['sum']==getattr(t,field);checks+=1
 js(out,'VALIDATION.json',{'status':'PASS','starting_main':BASE,'sealed_through':'2026-08-15','upstream_manifest_verified':True,'frozen_evaluation_archive_sha256':arch,'frozen_membership_equal':True,'strict_prior_all_states':True,'future_same_date_mutation_invariant':True,'independent_canonical_bout_field_checks':checks,'state_rows':len(s),'fits':0,'prospective_outcomes_accessed':False})
 print(json.dumps({'states':len(s),'support_rows':len(cov),'checks':checks,'output':str(out)}))
if __name__=='__main__':main()
