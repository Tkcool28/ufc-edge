"""One preregistered pass. Ability/prediction production precedes outcome scoring."""
import argparse, hashlib, json, lzma, sys
from pathlib import Path
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent; R=P.parents[2]
sys.path.insert(0,str(P));sys.path.insert(0,str(R/'tools/audits'))
import abilities as ab
import engine
import audit_ground_opportunity_competing_pathways_v1 as upstream

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')
def csv(p,d):d.to_csv(p,index=False,float_format='%.17g',lineterminator='\n',compression={'method':'gzip','mtime':0} if str(p).endswith('.gz') else None)

def source_lock():
    inputs=[R/'data/canonical/v0/fights.csv',R/'data/canonical/v0/events.csv',R/'data/canonical/v0/fighter_round_stats.csv',
      upstream.CON/'ordered_fold_fight_ids.json.xz',R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz',
      R/'docs/data_audits/grappling_identity_separation_v1/fighter_states.csv.gz',
      R/'docs/data_audits/grappling_identity_separation_v1/EVIDENCE_MANIFEST.json',
      R/'models/challengers/mov0_hierarchical_v1/weight_class_map.json',
      upstream.RUN/'EVALUATION_TABLES_MANIFEST.json']
    m=json.loads((upstream.RUN/'EVALUATION_TABLES_MANIFEST.json').read_text())
    inputs += [upstream.RUN/x['name'] for x in m['parts']]
    # Includes all raw/source hashes already frozen by PR158 plus diagnostic manifests.
    inputs += [R/x['path'] for x in json.loads((upstream.DEFAULT/'EVIDENCE_MANIFEST.json').read_text())['sources']]
    inputs += [R/'tools/audits'/n for n in ['audit_ground_opportunity_competing_pathways_v1.py','audit_grappling_identity_v1.py','grappling_identity_separation_v1.py']]
    return {str(x.relative_to(R)):sha(x) for x in sorted(set(inputs))}

def predictions(b,folds,metadata,out):
    groups={who:g.sort_values(['event_date','fight_id']) for who,g in b.groupby('fighter_id')}
    f=pd.read_csv(R/'data/canonical/v0/fights.csv',usecols=['fight_id','fighter_a_id','fighter_b_id']).set_index('fight_id')
    records=[];rates=[];pools=[];checks=0
    frozen=pd.read_csv(R/'docs/data_audits/grappling_identity_separation_v1/fighter_states.csv.gz').set_index(['target_fight_id','fighter_id'])
    for fold in folds:
        year=fold['outer_year'];pool=ab.pool(b,year);pools.append(pool)
        for fid in fold['scoring']:
            t=metadata.loc[fid];prior=pool['divisions'][t.division]
            who=[f.loc[fid].fighter_a_id,f.loc[fid].fighter_b_id]
            sides=[]
            for side,w in enumerate(who):
                g=groups.get(w,b.iloc[:0]);g=g[g.event_date<t.event_date]
                x=ab.estimate(g,prior);sides.append(x)
                if x['latest_prior_date'] is not None:assert x['latest_prior_date']<t.event_date
                z=frozen.loc[(fid,w)]
                for k in ['access','control','submission','gnp']:
                    scale=1/60 if k=='control' else 1
                    for new,old in [(x[k+'_num'],z[k+'_num']*scale),(x[k+'_den'],z[k+'_den_min'])]:
                        assert np.isclose(new,0 if pd.isna(old) else old,rtol=1e-8,atol=1e-8),(fid,w,k,new,old)
                        checks+=1
                records.append(dict(fight_id=fid,fighter_id=w,side=side,outer_year=year,cutoff=t.event_date,division=t.division,**x))
            row={'fight_id':fid,'event_date':t.event_date,'outer_year':year,'scheduled_rounds':int(t.scheduled_rounds)}
            for variant,mult,label in [('identity',1.,'identity'),('population',1.,'population'),('pooled_conversion',1.,'pooled_conversion'),('identity',.5,'return_half'),('identity',2.,'return_double')]:
                h=ab.hazards(*sides,prior,variant,mult)
                q=engine.generator(**{k:h[k] for k in ['entry','back','ground_ko','submission','standing_ko']})
                raw=engine.propagate(q,int(t.scheduled_rounds))
                k=raw[0]/raw[:2].sum();row['K_'+label]=k
                for name,value in zip(['KO','SUB','DEC'],raw):row['RAW_'+name+'_'+label]=value
                rates.append({'fight_id':fid,'variant':label,'outer_year':year,'scheduled_rounds':int(t.scheduled_rounds),**h})
                # Every real fight directional swap must conserve method probability.
                hh=ab.hazards(sides[1],sides[0],prior,variant,mult)
                qq=engine.generator(**{kk:hh[kk] for kk in ['entry','back','ground_ko','submission','standing_ko']})
                assert np.allclose(raw,engine.propagate(qq,int(t.scheduled_rounds)),rtol=1e-11,atol=1e-12)
            yield_row=row
            if 'rows' not in locals(): rows=[]
            rows.append(yield_row)
        print('Prediction-only boundary complete',year,flush=True)
    csv(out/'fighter_abilities.csv.gz',pd.DataFrame(records))
    js(out/'population_priors.json',pools)
    js(out/'simulator_records.json',rates)
    d=pd.DataFrame(rows);csv(out/'prediction_only.csv',d)
    js(out/'ABILITY_VALIDATION.json',{'PR161_exact_measurement_checks':checks,'strict_prior':True,'all_real_fighter_swap_tests':len(rates),'scoring_fights':len(d)})
    return d

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',required=True);ap.add_argument('--output',type=Path,default=P/'run_v1');a=ap.parse_args()
    if len(a.freeze)!=40:raise ValueError('Published preregistration SHA required')
    out=a.output;out.mkdir(parents=True,exist_ok=False)
    frozen=json.loads((P/'PRE_SCORING_MANIFEST.json').read_text())
    for name,h in frozen['implementation'].items(): assert sha(R/name)==h,name
    lock=source_lock()
    assert lock==frozen['sources'],'Source lock changed'
    js(out/'RUN_PROVENANCE.json',{'starting_main':'f70848818005e54d2db000ec73677f2fd27be033','preregistration_sha':a.freeze,
       'preregistration_manifest_sha256':sha(P/'PRE_SCORING_MANIFEST.json'),'prospective_outcomes_accessed':False,'predictive_fits':0})
    b=ab.add_strike_totals(ab.load_bouts())
    folds=json.loads(lzma.decompress((upstream.CON/'ordered_fold_fight_ids.json.xz').read_bytes()))['folds']
    pop=pd.read_csv(R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz',usecols=['fight_id','event_date','division','scheduled_rounds']).set_index('fight_id')
    d=predictions(b,folds,pop,out)
    # Save/hash predictions BEFORE recovering outcome/probability references.
    js(out/'PREDICTION_BEFORE_SCORING.json',{'prediction_only_sha256':sha(out/'prediction_only.csv'),'records_sha256':sha(out/'simulator_records.json')})
    e,archive=upstream.recover_evidence()
    assert d.fight_id.tolist()==[fid for fold in folds for fid in fold['scoring']]
    assert set(d.fight_id)==set(e.fight_id) and len(d)==4260
    e=e.merge(d,on=['fight_id','event_date','outer_year','scheduled_rounds'],validate='one_to_one')
    for variant in ['identity','population','pooled_conversion','return_half','return_double']:
        k=e['K_'+variant];e['KO_'+variant]=e.F*k;e['SUB_'+variant]=e.F*(1-k);e['DEC_'+variant]=1-e.F
        assert np.allclose(e[['KO_'+variant,'SUB_'+variant,'DEC_'+variant]].sum(axis=1),1,atol=1e-12)
    csv(out/'predictions.csv.gz',e)
    import reporting
    reporting.report(e,out)
    for name,h in lock.items():assert sha(R/name)==h,name
    print('Frozen predictions and reporting complete',flush=True)
if __name__=='__main__':main()
