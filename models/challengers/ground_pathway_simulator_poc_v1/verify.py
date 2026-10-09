"""Offline source replay, saved-record regeneration and engineering checks."""
import json,lzma,sys,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[2]
sys.path.insert(0,str(P))
import abilities as ab
import engine,run,validate,reporting

def close(a,b):
    if isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:close(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b)
        for x,y in zip(a,b):close(x,y)
    elif isinstance(a,(float,int)) and not isinstance(a,bool):assert np.isclose(a,b,rtol=1e-10,atol=1e-10),(a,b)
    else:assert a==b,(a,b)

def verify(out):
    lock=json.loads((P/'PRE_SCORING_MANIFEST.json').read_text())
    assert run.source_lock()==lock['sources']
    for n,h in lock['implementation'].items():assert run.sha(R/n)==h,n
    e=pd.read_csv(out/'predictions.csv.gz')
    s=pd.read_csv(out/'fighter_abilities.csv.gz');assert len(s)==8520 and not s.duplicated(['fight_id','fighter_id']).any()
    records=json.loads((out/'simulator_records.json').read_text());assert len(records)==5*4260
    saved=json.loads((out/'PREDICTION_BEFORE_SCORING.json').read_text())
    assert run.sha(out/'prediction_only.csv')==saved['prediction_only_sha256']
    assert run.sha(out/'simulator_records.json')==saved['records_sha256']
    ix=e.set_index('fight_id');max_error=0.
    for r in records:
        q=engine.generator(**{k:r[k] for k in ['entry','back','ground_ko','submission','standing_ko']})
        raw=engine.propagate(q,r['scheduled_rounds'])
        target=ix.loc[r['fight_id']];label=r['variant'];k,v=engine.compose(raw,target.F)
        actual=target[['KO_'+label,'SUB_'+label,'DEC_'+label]].to_numpy(dtype=float)
        error=float(np.max(np.abs(actual-v)));max_error=max(max_error,error)
        assert np.allclose(actual,v,rtol=1e-11,atol=1e-12)
        assert np.isclose(k,target['K_'+label],rtol=1e-11,atol=1e-12)
    reference,archive=run.upstream.recover_evidence()
    frozen_cols=['K_A','K_C','F','KO_A','SUB_A','DEC_A','KO_C','SUB_C','DEC_C']
    assert set(e.fight_id)==set(reference.fight_id)
    assert np.allclose(ix.loc[reference.fight_id,frozen_cols],reference[frozen_cols],rtol=1e-12,atol=1e-12)
    for col in reporting.CELLS:assert ix.loc[reference.fight_id,col].tolist()==reference[col].tolist()
    b=ab.add_strike_totals(ab.load_bouts())
    folds=json.loads(lzma.decompress((run.upstream.CON/'ordered_fold_fight_ids.json.xz').read_bytes()))['folds']
    pop=pd.read_csv(R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz',usecols=['fight_id','event_date','division','scheduled_rounds']).set_index('fight_id')
    with tempfile.TemporaryDirectory() as td:
        dest=Path(td)
        run.predictions(b,folds,pop,dest)
        names=['prediction_only.csv','fighter_abilities.csv.gz','population_priors.json','simulator_records.json','ABILITY_VALIDATION.json']
        for n in names:assert run.sha(out/n)==run.sha(dest/n),n
        reporting.report(e,dest)
        close(json.loads((out/'AGGREGATE_RESULTS.json').read_text()),json.loads((dest/'AGGREGATE_RESULTS.json').read_text()))
        close(json.loads((out/'GATE_DECISIONS.json').read_text()),json.loads((dest/'GATE_DECISIONS.json').read_text()))
    # Canonical count orientation independent from prebuilt paired bout table.
    stats=pd.read_csv(R/'data/canonical/v0/fighter_round_stats.csv');stats=stats[stats.fight_id.isin(b.fight_id)]
    counts=stats.groupby(['fight_id','fighter_id']).agg({'takedowns_attempted':['sum','count'],'submission_attempts':['sum','count'],'sig_ground_attempted':['sum','count'],'control_sec':['sum','count'],'knockdowns':['sum','count']})
    independent=0
    for t in b.itertuples():
        key=(t.fight_id,t.fighter_id)
        for field in ['takedowns_attempted','submission_attempts','sig_ground_attempted','control_sec','knockdowns']:
            value=getattr(t,field)
            if pd.notna(value):
                assert key in counts.index
                assert counts.loc[key,(field,'count')]==t.expected_rounds
                assert counts.loc[key,(field,'sum')]==value
                independent+=1
    result={'status':'PASS','saved_transition_records_regenerated':len(records),'max_probability_regeneration_error':max_error,
      'all_frozen_reference_probabilities_unchanged':True,'exact_outer_fight_identity_matching':True,'frozen_B3_B5_A1_A2_A4_matching':True,
      'byte_identical_full_ability_prediction_reconstruction':names,'independent_canonical_scalar_checks':independent,
      'metrics_and_gate_reproduction':True,'source_hashes_unchanged':True,'prospective_outcomes_accessed':False,
      'numerical':validate.numerical(),'chronology':validate.chronology(b,ab.pool(b,2018))}
    first=next(x for x in records if x['variant']=='identity')
    q=engine.generator(**{k:first[k] for k in ['entry','back','ground_ko','submission','standing_ko']})
    result['monte_carlo']=validate.monte_carlo(q,first['scheduled_rounds'])
    run.js(out/'SIMULATION_VALIDATION.json',result)
    reporting.md(out,'SIMULATION_VALIDATION.md','Engineering validation',json.dumps(result,sort_keys=True,indent=2)+'\nExact propagation used for predictions; Gillespie checks are validation only. No simulation-count choice affects scores.')
    print(json.dumps(result,sort_keys=True,indent=2),flush=True)
    return result

if __name__=='__main__':verify(P/'run_v1')
