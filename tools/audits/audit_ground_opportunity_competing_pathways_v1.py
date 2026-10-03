#!/usr/bin/env python3
"""Read-only historical source/support audit; never imports or fits a predictive model.

Run: PYTHONPATH=src python tools/audits/audit_ground_opportunity_competing_pathways_v1.py
Optional --output-dir allows isolated deterministic reproduction.
"""
from __future__ import annotations
import argparse, hashlib, io, json, lzma, sys, tarfile
from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R/'src'))
from ufc_edge.features.elapsed_exposure import infer_round_exposure, load_registry
BASE='3e2b14a8391ed17d072b4bbb9570b31bc6d12b85'
SEAL='2026-08-15'
CAN=R/'data/canonical/v0'
RUN=R/'models/challengers/mov1_three_arm_directional_run_v1/run_v1'
CON=R/'models/challengers/mov1_three_arm_directional_v1'
DEFAULT=R/'docs/data_audits/ground_opportunity_competing_pathways_v1'
RAW=['takedowns_attempted','takedowns_landed','submission_attempts','sig_ground_attempted','sig_ground_landed','control_sec','reversals']
POS=['ground_bucket_min','ground_control_bucket_min','back_control_bucket_min','standups']
PAIRS={
 'sub_per_td':('submission_attempts','takedowns_landed'),
 'control_per_td':('control_sec','takedowns_landed'),
 'sub_per_ground_bucket':('submission_attempts','ground_bucket_min'),
 'ground_strikes_per_ground_bucket':('sig_ground_attempted','ground_bucket_min'),
 'sub_per_elapsed_min':('submission_attempts','elapsed_min'),
 'ground_strikes_per_elapsed_min':('sig_ground_attempted','elapsed_min'),
 'sub_conversion':('sub_win','submission_attempts'),
 'sub_conversion_faced':('sub_loss','submission_attempts_faced'),
}
INPUTS=set()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source(p):
 p=Path(p);INPUTS.add(p);return p

def read(p):return pd.read_csv(source(p),keep_default_na=True)
def js(p):return json.loads(source(p).read_text())
def writej(out,n,v):(out/n).write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n')
def writecsv(out,n,x):
 x.to_csv(out/n,index=False,float_format='%.10g',lineterminator='\n',compression={'method':'gzip','mtime':0} if n.endswith('.gz') else None)
def recover_evidence():
 m=js(RUN/'EVALUATION_TABLES_MANIFEST.json'); parts=[]
 for a in m['parts']:
  p=source(RUN/a['name']);assert sha(p)==a['sha256'];parts.append(p.read_bytes())
 b=b''.join(parts);assert hashlib.sha256(b).hexdigest()==m['archive_SHA256']
 with tarfile.open(fileobj=io.BytesIO(b),mode='r:xz') as t:
  n='FIGHT_LEVEL_EVIDENCE.csv.xz';data=t.extractfile(n).read()
  assert hashlib.sha256(data).hexdigest()==m['members'][n]['sha256']
 return pd.read_csv(io.BytesIO(data),compression='xz'),m['archive_SHA256']

def load():
 ev=read(CAN/'events.csv').set_index('event_id');f=read(CAN/'fights.csv')
 f['event_date']=f.event_id.map(ev.event_date)
 # Date is examined before any outcomes or round payloads are selected.
 f=f[(f.promotion=='UFC') & f.event_date.notna() & (f.event_date<=SEAL)].copy()
 assert f.fight_id.is_unique
 fights=f.set_index('fight_id').to_dict('index')
 st=read(CAN/'fighter_round_stats.csv');po=read(CAN/'fighter_round_position.csv')
 st=st[st.fight_id.isin(fights)].copy();po=po[po.fight_id.isin(fights)].copy()
 keys=['fight_id','fighter_id','round'];assert not st.duplicated(keys).any();assert not po.duplicated(keys).any()
 joined=st.merge(po,on=keys,how='outer',validate='one_to_one')
 registry=load_registry(R);source(R/'provenance/rulesets/elapsed_exposure_ruleset_registry_v1.json')
 e=[]
 for row in joined.itertuples(index=False):
  fight=fights[row.fight_id];assert row.fighter_id in {fight['fighter_a_id'],fight['fighter_b_id']}
  sec=infer_round_exposure(dict(fight,fight_id=row.fight_id),fight['event_date'],int(row.round),registry)
  e.append(np.nan if sec is None or sec<=0 else sec/60)
 joined['elapsed_min']=e
 # Opponent counts are actual paired fighter rows, never a TD-defense substitute.
 side=st[keys+['opponent_id','submission_attempts','control_sec','reversals']].copy()
 side=side.rename(columns={'opponent_id':'fighter_id','fighter_id':'original_fighter_id','submission_attempts':'submission_attempts_faced','control_sec':'control_sec_allowed','reversals':'reversals_faced'})
 joined=joined.merge(side.drop(columns='original_fighter_id'),on=keys,how='left',validate='one_to_one')
 return f,fights,joined,st,po

def bout_records(f,fights,j):
 fields=RAW+POS+['elapsed_min','submission_attempts_faced','control_sec_allowed','reversals_faced']
 groups={(fid,who):g for (fid,who),g in j.groupby(['fight_id','fighter_id'],sort=True)}
 records=[]
 for fight in f.sort_values(['event_date','fight_id']).to_dict('records'):
  for who in sorted([fight['fighter_a_id'],fight['fighter_b_id']]):
   g=groups.get((fight['fight_id'],who),pd.DataFrame(columns=fields+['round']))
   n=int(fight['finish_round']) if pd.notna(fight['finish_round']) else 0
   full=n>0 and set(g['round'].astype(int))==set(range(1,n+1))
   rec={k:fight[k] for k in ['fight_id','event_date','weight_class']};rec['fighter_id']=who
   rec['sub_win']=int(fight['result']=='win_loss' and fight['method']=='SUBMISSION' and fight['winner_id']==who)
   rec['sub_loss']=int(fight['result']=='win_loss' and fight['method']=='SUBMISSION' and pd.notna(fight['winner_id']) and fight['winner_id']!=who)
   rec['expected_rounds']=n;rec['observed_rows']=len(g)
   for field in fields:
    v=g[field];rec[field]=float(v.sum()) if full and v.notna().all() else np.nan
    rec[field+'_observed_rows']=int(v.notna().sum());rec[field+'_observed_sum']=float(v.sum()) if v.notna().any() else np.nan
   for name,(num,den) in PAIRS.items():
    # Conversion joins a bout result only when ALL attempted-submission rounds exist.
    if num in ('sub_win','sub_loss'):
     valid=pd.notna(rec[den]);rec[name+'_num']=float(rec[num]) if valid else np.nan;rec[name+'_den']=rec[den] if valid else np.nan
    else:
     valid=g[[num,den]].notna().all(axis=1)
     if den=='ground_bucket_min':
      valid &= g.elapsed_min.notna() & (g[den] <= g.elapsed_min)
     rec[name+'_num']=float(g.loc[valid,num].sum()) if valid.any() else np.nan
     rec[name+'_den']=float(g.loc[valid,den].sum()) if valid.any() else np.nan
    rec[name+'_complete_bout']=bool(pd.notna(rec[den]) and pd.notna(rec[num]))
    if den=='ground_bucket_min':
     rec[name+'_complete_bout'] &= bool(full and valid.all())
   records.append(rec)
 return pd.DataFrame(records)

class History:
 def __init__(self,b):self.groups={who:g.sort_values(['event_date','fight_id']).reset_index(drop=True) for who,g in b.groupby('fighter_id')}
 def state(self,who,cutoff,window='career'):
  g=self.groups.get(who,pd.DataFrame());g=g[g.event_date<cutoff] if len(g) else g
  if len(g):assert g.event_date.max()<cutoff
  ambiguous=False
  if window=='last5' and len(g)>5:
   ds=list(g.event_date); start=len(g)-5
   if ds[start]==ds[start-1]:ambiguous=True;g=g.iloc[0:0]
   else:g=g.iloc[-5:]
  out={'fighter_id':who,'cutoff':cutoff,'window':window,'prior_ufc_bouts':len(g),'ambiguous_recent_boundary':ambiguous,'latest_prior_date':None if not len(g) else g.event_date.max()}
  fields=RAW+POS+['elapsed_min','submission_attempts_faced','control_sec_allowed','reversals_faced','sub_win','sub_loss']
  cols=fields+[name+'_'+suffix for name in PAIRS for suffix in ['num','den','complete_bout']]
  sums=g[cols].sum(min_count=1).to_dict() if len(g) else {}
  counts=g[cols].notna().sum().to_dict() if len(g) else {}
  for field in fields:
   out[field]=float(sums.get(field,np.nan))
   out[field+'_complete_bouts']=int(counts.get(field,0))
  for name in PAIRS:
   for suffix in ['num','den']:
    k=name+'_'+suffix;out[k]=float(sums.get(k,np.nan))
   out[name+'_complete_bouts']=int(sums.get(name+'_complete_bout',0))
   n,d=out[name+'_num'],out[name+'_den'];out[name+'_diagnostic_ratio']=n/d if not name.startswith('sub_conversion') and pd.notna(d) and d>0 else np.nan
  return out

def summary(s,name,scope,year,division='ALL'):
 n,d=s[name+'_num'],s[name+'_den'];available=n.notna()&d.notna();vals=d[available]
 out={'scope':scope,'outer_year':year,'division':division,'candidate':name,'fighter_states':len(s),'unique_fighters':s.fighter_id.nunique(),'unique_target_fights':s.target_fight_id.nunique() if 'target_fight_id' in s else 0,
      'num_observed_states':int(n.notna().sum()),'den_observed_states':int(d.notna().sum()),'missing_pair_pct':float(100*(~available).mean()),'zero_den_states':int((available&(d==0)).sum()),'zero_den_pct_observed':float(100*(vals==0).mean()) if len(vals) else None,
      'zero_num_states':int((available&(n==0)).sum()),'no_prior_ufc_states':int((s.prior_ufc_bouts==0).sum()),'ambiguous_recent_states':int(s.ambiguous_recent_boundary.sum()),'num_support_sum_state_weighted':float(n.sum()),'den_support_sum_state_weighted':float(d.sum()),'complete_history_pct':float(100*((s[name+'_complete_bouts']==s.prior_ufc_bouts)&(s.prior_ufc_bouts>0)).mean())}
 for q in [.1,.25,.5,.75,.9]:out[f'den_p{int(q*100)}']=float(vals.quantile(q)) if len(vals) else None
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=DEFAULT);args=ap.parse_args();out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
 f,fights,j,st,po=load();
 quality=[]
 for field in ['ground','ground_control','standing','back_control']:
  eligible=j[field+'_bucket_min'].notna() & j.elapsed_min.notna()
  impossible=eligible & (j[field+'_lower_sec']>j.elapsed_min*60)
  quality.append({'field':field,'observed_bucket_rows':int(j[field+'_bucket_min'].notna().sum()),'round_duration_eligible_rows':int(eligible.sum()),'lower_bound_exceeds_elapsed_rows':int(impossible.sum()),'zero_bucket_rows':int(j[field+'_bucket_min'].eq(0).sum())})
 writej(out,'POSITION_INTERVAL_QUALITY.json',quality)
 b=bout_records(f,fights,j);h=History(b)
 pop=read(R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz');assert pop.event_date.max()<=SEAL;assert set(pop.fight_id)<=set(fights)
 evidence,archive= recover_evidence();assert len(evidence)==4260 and evidence.fight_id.is_unique and evidence.event_date.max()<=SEAL
 assert set(evidence.fight_id)<=set(pop.fight_id)
 for c in ['B3_TD_ACCESS_PLUS_SUB_PRESSURE','B5_SUB_PRESSURE_VS_SUB_VULNERABILITY']:
  assert evidence.set_index('fight_id')[c].equals(pop.set_index('fight_id').loc[evidence.fight_id,c])
 folds=json.loads(lzma.decompress(source(CON/'ordered_fold_fight_ids.json.xz').read_bytes()))['folds'];assert [a['outer_year'] for a in folds]==list(range(2018,2027))
 states=[]
 for target in pop.sort_values(['event_date','fight_id']).to_dict('records'):
  for who in sorted([fights[target['fight_id']]['fighter_a_id'],fights[target['fight_id']]['fighter_b_id']]):
   for window in ['career','last5']:
    s=h.state(who,target['event_date'],window);s.update(target_fight_id=target['fight_id'],division=target['division'],outer_year=int(target['event_date'][:4]));states.append(s)
 s=pd.DataFrame(states);writecsv(out,'strict_prior_fighter_states.csv.gz',s)
 writecsv(out,'bout_measurements.csv.gz',b)
 boundary=[];coverage=[];conversion=[]
 for fold in folds:
  y=fold['outer_year'];cut=f'{y}-01-01';train=set(fold['training']);score=set(fold['scoring'])
  assert (pop[pop.fight_id.isin(train)].event_date<cut).all();assert score==set(evidence[evidence.outer_year==y].fight_id)
  people=sorted({v for fid in train for v in [fights[fid]['fighter_a_id'],fights[fid]['fighter_b_id']]})
  snap=pd.DataFrame([h.state(who,cut) for who in people]);snap['division']='ALL';snap['target_fight_id']=''
  for name in PAIRS:
   row=summary(snap,name,'training_fighters_at_boundary',y);row['eligible_training_fights']=len(train);row['eligible_prior_ufc_fights']=int((f.event_date<cut).sum());boundary.append(row)
  for scope,ids in [('frozen_training_prefight',train),('frozen_outer_scoring_prefight',score)]:
   for window in ['career','last5']:
    z=s[(s.target_fight_id.isin(ids))&(s.window==window)]
    for division,g in [('ALL',z)]+list(z.groupby('division')):
     for name in PAIRS:
      row=summary(g,name,scope,y,division);row['window']=window;coverage.append(row)
    for field in ['submission_attempts','submission_attempts_faced','sub_win','sub_loss']:
     for binname,lo,hi in [('missing',None,None),('0',0,0),('1',1,1),('2-4',2,4),('5-9',5,9),('10+',10,None)]:
      v=z[field];mask=v.isna() if lo is None else v.ge(lo)&(True if hi is None else v.le(hi))
      conversion.append({'outer_year':y,'scope':scope,'window':window,'field':field,'support_bin':binname,'states':int(mask.sum()),'total_states':len(z),'pct':float(100*mask.mean())})
  for field in ['submission_attempts','submission_attempts_faced']:
   v=snap[field]
   for binname,lo,hi in [('missing',None,None),('0',0,0),('1',1,1),('2-4',2,4),('5-9',5,9),('10+',10,None)]:
    mask=v.isna() if lo is None else v.ge(lo)&(True if hi is None else v.le(hi))
    conversion.append({'outer_year':y,'scope':'training_fighters_at_boundary','window':'career','field':field,'support_bin':binname,'states':int(mask.sum()),'total_states':len(snap),'pct':float(100*mask.mean())})
 writecsv(out,'boundary_coverage.csv',pd.DataFrame(boundary));writecsv(out,'fold_state_coverage.csv',pd.DataFrame(coverage));cvbins=pd.DataFrame(conversion)
 assert not cvbins.duplicated(['outer_year','scope','window','field','support_bin']).any()
 for _,g in cvbins.groupby(['outer_year','scope','window','field']):assert int(g.states.sum())==int(g.total_states.iloc[0])
 writecsv(out,'conversion_support_bins.csv',cvbins)
 # Canonical yearly availability uses EXPECTED fighter-round keys, including absent rows.
 yearly=[]
 for y,g in f.groupby(f.event_date.str[:4]):
  ids=set(g.fight_id);jg=j[j.fight_id.isin(ids)];expected=int(2*g.finish_round.fillna(0).sum())
  for field in RAW+POS+['elapsed_min']:
   count=int(jg[field].notna().sum());yearly.append({'year':y,'field':field,'fights':len(g),'fighters':len(set(g.fighter_a_id)|set(g.fighter_b_id)),'expected_fighter_rounds':expected,'observed_rows':count,'missing_pct':100*(1-count/expected) if expected else None,'observed_sum':float(jg[field].sum()),'observed_zero_rows':int(jg[field].eq(0).sum())})
 writecsv(out,'year_field_coverage.csv',pd.DataFrame(yearly))
 # Entire fixed cells; no subgroup threshold selected using outcomes.
 panel=[];cellstats=[];des=[]
 for cell,col,nfinish in [('B3','B3_TD_ACCESS_PLUS_SUB_PRESSURE',224),('B5','B5_SUB_PRESSURE_VS_SUB_VULNERABILITY',355)]:
  e=evidence[evidence[col]=='MATCH'];assert e.method.isin(['KO_TKO','SUBMISSION']).sum()==nfinish
  z=s[s.target_fight_id.isin(e.fight_id)].copy();z['cell']=cell;panel.append(z)
  for window in ['career','last5']:
   zz=z[z.window==window]
   for era,g in [('ALL',zz)]+[(str(y),g) for y,g in zz.groupby('outer_year')]:
    for name in PAIRS:
     row=summary(g,name,cell,int(era) if era!='ALL' else 0);row['window']=window;cellstats.append(row)
    for field in RAW+POS+['submission_attempts_faced','control_sec_allowed','reversals_faced']:
     vals=g[field].dropna();row={'cell':cell,'year':era,'window':window,'field':field,'states':len(g),'observed_states':len(vals),'zero_observed_pct':float(100*vals.eq(0).mean()) if len(vals) else None}
     row.update({f'p{int(q*100)}':float(vals.quantile(q)) if len(vals) else None for q in [.1,.25,.5,.75,.9]});des.append(row)
  # Re-report saved cell calibration, never recompute model probabilities.
  ef=e[e.method.isin(['KO_TKO','SUBMISSION'])]
  writej(out,f'{cell}_FROZEN_CELL.json',{'all_scored_bouts':len(e),'standard_finishes':len(ef),'observed_SUB':float(ef.method.eq('SUBMISSION').mean()),'Arm_C_predicted_SUB':float((1-ef.K_C).mean()),'fixed_membership_column':col})
 writecsv(out,'B3_B5_strict_prior_states.csv.gz',pd.concat(panel));writecsv(out,'B3_B5_candidate_coverage.csv',pd.DataFrame(cellstats));writecsv(out,'B3_B5_measurement_distributions.csv',pd.DataFrame(des))
 # Descriptive correlations only; no outcomes or predictions enter them.
 correlations=[]
 for cell,z in pd.concat(panel).groupby('cell'):
  for window,g in z.groupby('window'):
   for a,bb in [('submission_attempts','sig_ground_attempted'),('submission_attempts','control_sec'),('takedowns_landed','control_sec'),('standups','reversals')]:
    v=g[[a,bb]].dropna();correlations.append({'cell':cell,'window':window,'a':a,'b':bb,'paired_states':len(v),'spearman':float(v.corr(method='spearman').iloc[0,1]) if len(v)>2 else None})
 writecsv(out,'B3_B5_descriptive_correlations.csv',pd.DataFrame(correlations))
 # SUB successes are fight-level outcomes, not verified per-attempt Bernoulli trials.
 cv=b[b.sub_win==1];valid=cv.sub_conversion_den.notna()
 conversion_check={'prior_ufc_submission_wins':len(cv),'complete_attempt_bouts':int(valid.sum()),'wins_with_zero_recorded_attempts':int((valid&(cv.sub_conversion_den==0)).sum()),'missing_attempt_bouts':int((~valid).sum()),'all_ufc_attempts':float(st.submission_attempts.sum())}
 writej(out,'CONVERSION_MEASUREMENT_CHECK.json',conversion_check)
 # Executable future/target and same-date invariance: history state excludes mutations.
 who=s.iloc[0].fighter_id;cut=s.iloc[0].cutoff;before=h.state(who,cut);mut=b.copy();future=mut.event_date>=cut
 for field in RAW+POS:mut.loc[future,field]=999999
 for name in PAIRS:mut.loc[future,[name+'_num',name+'_den']]=999999
 after=History(mut).state(who,cut)
 def stable(d):return json.dumps(d,sort_keys=True,default=str).replace('NaN','null')
 assert stable(before)==stable(after)
 # Every date/fighter projection checked against a source-specific max date.
 assert (s.latest_prior_date.dropna()<s.loc[s.latest_prior_date.notna(),'cutoff']).all()
 expected=s[s.window=='career'][['target_fight_id','fighter_id']];assert len(expected)==2*len(pop) and not expected.duplicated().any()
 writej(out,'STRICT_PRIOR_VERIFICATION.json',{'status':'PASS','max_allowed_event_date':SEAL,'target_and_same_date_excluded':True,'all_state_latest_dates_strictly_before_cutoff':True,'future_stat_mutation_invariant':True,'state_rows':len(s),'career_fighter_target_pairs':len(expected),'frozen_membership_equal':True,'frozen_evaluation_archive_SHA256':archive,'fits':0,'prospective_confirmation_outcomes_accessed':False,'scope':'retrospective event-date strict prior; 2026 snapshots do not establish historical publication vintages'})
 # Capture source bytes incl. original raw pages, transformations and research references.
 for p in (DEFAULT/'research_context').glob('*.md'):source(p)
 for p in [R/'features/data_requirements.json',R/'provenance/source_inventory.md',R/'schemas/canonical_data_contract_v0.md',CON/'SOURCE_LINEAGE_VALIDATION.json',CAN/'manifest.json',CAN/'source_identity_links.csv',R/'data/derived/identity/ufc_greco_fight_alignment_candidate.csv',R/'pipelines/build_canonical_core_v0.py',R/'pipelines/build_canonical_fightmetric_position_v0.py',R/'features/feature_catalog.yaml',R/'features/f02/README.md',R/'features/F01_MATERIALIZER.md',R/'src/ufc_edge/features/state.py',R/'src/ufc_edge/features/history.py',R/'src/ufc_edge/features/aggregations.py',R/'src/ufc_edge/features/elapsed_exposure.py',R/'provenance/source_precedence_v0.md',R/'provenance/data_sourcing_rules.md',R/'provenance/ufc_com_jsonapi_candidate.md',R/'provenance/fightmetric_round0.md']:
  source(p)
 for p in (R/'provenance/audits').glob('fightmetric*'):source(p)
 for p in [R/'provenance/audits/canonical_fightmetric_position_v0_latest.json',R/'docs/model_diagnostics/mov1_directional_representation_v1/MOV1_DIRECTIONAL_REPRESENTATION_AUDIT_V1.md',CON/'MOV1_THREE_ARM_DIRECTIONAL_CHALLENGER_V1_CONTRACT.md',CON/'SOURCE_MANIFEST.json']:
  source(p)
 for n in ['FINAL_REPORT.md','FOCUSED_B3_DIAGNOSTIC.md','FOCUSED_B5_DIAGNOSTIC.md','B1_B5_PATHWAY_COMPARISON.md','STRIKING_PRESERVATION_REPORT.md','SCIENTIFIC_INTERPRETATION_REPORT.md','ANNUAL_COMPARISON.md','COMPLETE_SYSTEM_COMPOSITION_REPORT.md','FORWARD_CONFIRMATION_READINESS_REPORT.md']:
  source(RUN/n)
 for root in [R/'data/raw/greco1899/8e40eb945e11',R/'data/raw/ufc_fightmetric_official/20260820T123046Z']:
  m=js(root/'manifest.json')
  for entry in m['files']:
   p=R/entry['path'] if entry['path'].startswith('data/') else root/entry['path'];source(p);assert sha(p)==entry['sha256']
 writej(out,'SOURCE_IDENTITIES.json',{'starting_main':BASE,'sources':[{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(INPUTS)],'script_SHA256':sha(Path(__file__))})
 print(json.dumps({'fights':len(f),'modern_population':len(pop),'stats_rows':len(st),'position_rows':len(po),'conversion':conversion_check,'output_dir':str(out)},indent=2))
if __name__=='__main__':main()
