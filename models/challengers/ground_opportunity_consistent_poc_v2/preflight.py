"""Outcome-blind frozen construction. No outcome recovery or scorer is imported."""
import argparse, hashlib, json, lzma, sys, tempfile, shutil, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parent; ROOT=P.parents[2]
SRC=ROOT/'models/challengers/ground_pathway_simulator_poc_v1'
CON=ROOT/'docs/model_contracts/ground_opportunity_reward_consistency_v1'
sys.path.insert(0,str(SRC));sys.path.insert(0,str(P))
import abilities as ab
import engine
import validate
import publication
import opportunity as op
START='222c7a76bc75bd66e0517930863ebeab41baf99f'
STRUCTURAL={'INFEASIBLE_SIMPLEX','NO_POSITIVE_RESET_BUDGET','INFEASIBLE_FINITE_ROUND_CEILING'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,np.ndarray):return clean(v.tolist())
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(tuple,list)):return [clean(x) for x in v]
    return v
def js(p,v):p.write_text(json.dumps(clean(v),indent=2,sort_keys=True,allow_nan=False)+'\n')
def csv(p,d):d.to_csv(p,index=False,float_format='%.17g',lineterminator='\n',compression={'method':'gzip','mtime':0} if str(p).endswith('.gz') else None)
def construct(a,b,prior,rounds):
    actors=[a,b];raw=[];d=[];u=[];g=[];pi=[];cv=[]
    h=ab.hazards(a,b,prior)
    for i,x in enumerate(actors):
        y=actors[1-i];raw.append(float(np.sqrt(x['control']*y['control_allowed'])))
        d.append(x['access']);u.append(float(np.sqrt(x['submission']*y['sub_faced'])))
        g.append(float(np.sqrt(x['gnp']*y['ground_allowed'])))
        pi.append(float(np.sqrt(x['td_conversion']*(1-y['td_resistance']))))
        cv.append(float(np.sqrt(x['sub_conversion']*y['sub_conversion_allowed'])))
    q=np.clip(raw,.02,.8);gv=[prior['ground_conversion']]*2
    base=dict(raw_proxy=raw,target_ground=q,regularized=(q!=raw),standing_target=1-float(sum(q)),TD_reward=d,SUB_reward=u,GNP_reward=g,TD_success=pi,SUB_conversion=cv,GNP_conversion=gv,standing_KO=h['standing_ko'])
    try:
        z=op.solve(d,u,g,pi,q,cv,gv,h['standing_ko'],rounds)
        sk=h['standing_ko']*z['minutes'][0];gk=z['minutes'][1:]@(np.asarray(g)/q*np.asarray(gv));su=z['minutes'][1:]@(np.asarray(u)/q*np.asarray(cv))
        rawp=np.array([sk+gk,su,z['decision']]);k=rawp[0]/rawp[:2].sum()
        closed=(h['standing_ko']*(1-sum(q))+np.dot(g,gv))/(h['standing_ko']*(1-sum(q))+np.dot(g,gv)+np.dot(u,cv))
        if abs(k-closed)>1e-8 or abs(rawp.sum()-1)>1e-10:raise op.Unavailable('NUMERICAL_TRANSITION','closed form/probability identity')
        qmat=engine.generator(z['entry'],z['returns'],np.asarray(g)/q*np.asarray(gv),np.asarray(u)/q*np.asarray(cv),h['standing_ko'])
        if np.max(abs(engine.propagate(qmat,rounds)-rawp))>1e-10:raise op.Unavailable('NUMERICAL_TRANSITION','independent five-state engine')
        rates=np.r_[z['TD_hazard'],z['SUB_creation'],z['GNP_actions'],z['returns']]
        assert np.isfinite(rates).all() and min(rates)>=0
        multipliers=[]
        for i,x in enumerate(actors):
            multipliers.append({'A':z['SUB_creation'][i]/u[i] if u[i] else None,'B':z['SUB_creation'][i]/x['submission'] if x['submission'] else None,'C':u[i]/x['submission'] if x['submission'] else None,'D':1/q[i]})
        return dict(**base,status='VALID',failure_code=None,certified_structural=False,solution=z,raw_KO=rawp[0],raw_SUB=rawp[1],raw_DEC=rawp[2],K=k,closed_form_K=closed,identity_error=abs(k-closed),expected_returns=z['returns']*z['minutes'][1:],multipliers=multipliers)
    except op.Unavailable as e:
        return dict(**base,status='UNAVAILABLE',failure_code=e.code,certified_structural=e.code in STRUCTURAL,detail=e.detail)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=P/'run_v1');args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    assert sha(CON/'EVIDENCE_MANIFEST.json')=='7a5fd85dcc5b84b610374f7cc1ff219a2892e58e69e098df57d468e1478e955e'
    assert sha(SRC/'run_v1/EVIDENCE_MANIFEST.json')=='839587507aa470f8d0cf8df7b66f13c04a665790ebde1b2802abfc0c99f07d8b'
    subprocess.run([sys.executable,str(CON/'verify.py')],check=True)
    publication.check()
    source_hash=sha(CON/'SOURCE_LOCK.json')
    foldpath=ROOT/'models/challengers/mov1_three_arm_directional_contract_v1/ordered_fold_fight_ids.json.xz'
    # Resolve the frozen path from PR163, never from outcomes.
    import audit_ground_opportunity_competing_pathways_v1 as upstream
    foldpath=upstream.CON/'ordered_fold_fight_ids.json.xz'
    folds=json.loads(lzma.decompress(foldpath.read_bytes()))['folds'];ids=[f for fold in folds for f in fold['scoring']]
    assert len(ids)==len(set(ids))==4260
    meta=pd.read_csv(ROOT/'governance/finish_method_target_structure_v1/population_manifest.csv.gz',usecols=['fight_id','event_date','division','scheduled_rounds']).set_index('fight_id')
    with tempfile.TemporaryDirectory() as td:
        dest=Path(td);publication.restore(dest) # byte-only hash verification, no outcome parsing
        saved=pd.read_csv(dest/'fighter_abilities.csv.gz',float_precision='round_trip')
        pools=json.loads((dest/'population_priors.json').read_text())
        oldrows=pd.read_csv(dest/'prediction_only.csv',float_precision='round_trip').set_index('fight_id')
        oldrates={r['fight_id']:r for r in json.loads((dest/'simulator_records.json').read_text()) if r['variant']=='identity'}
        assert oldrows.index.tolist()==ids
        b=ab.add_strike_totals(ab.load_bouts());groups={who:g for who,g in b.groupby('fighter_id')}
        saved=saved.set_index(['fight_id','side']);records=[];abilities=[];summaries=[];max_ability=0.;max_A=0.;max_swap=0.
        chronology=validate.chronology(b,pools[0]);numerical=validate.numerical()
        for pool,fold in zip(pools,folds):
            year=fold['outer_year'];assert pool['outer_year']==year
            regenerated=ab.pool(b,year);assert regenerated==pool
            for fid in fold['scoring']:
                t=meta.loc[fid];prior=pool['divisions'][t.division];sides=[]
                for side in range(2):
                    s=saved.loc[(fid,side)].to_dict();who=s['fighter_id'];hist=groups.get(who,b.iloc[:0]);hist=hist[hist.event_date<t.event_date]
                    fresh=ab.estimate(hist,prior)
                    for key,val in fresh.items():
                        old=s[key]
                        if isinstance(val,(float,int,bool)):
                            err=abs(float(val)-float(old));max_ability=max(max_ability,err);assert err<=1e-10,(fid,key,err)
                        else:assert (val is None and pd.isna(old)) or val==old
                    assert fresh['latest_prior_date'] is None or fresh['latest_prior_date']<t.event_date
                    abilities.append(dict(fight_id=fid,side=side,outer_year=year,cutoff=t.event_date,division=t.division,fighter_id=who,**fresh));sides.append(fresh)
                h=ab.hazards(*sides,prior);old=oldrates[fid]
                for key in h:assert np.allclose(h[key],old[key],rtol=0,atol=1e-12)
                rawA=engine.propagate(engine.generator(**{k:h[k] for k in ['entry','back','ground_ko','submission','standing_ko']}),int(t.scheduled_rounds))
                max_A=max(max_A,abs(rawA[0]/rawA[:2].sum()-oldrows.loc[fid,'K_identity']));assert max_A<1e-12
                v=construct(*sides,prior,int(t.scheduled_rounds));sw=construct(sides[1],sides[0],prior,int(t.scheduled_rounds))
                assert v['status']==sw['status'] and v['failure_code']==sw['failure_code']
                if v['status']=='VALID':
                    err=abs(v['K']-sw['K']);max_swap=max(max_swap,err);assert err<1e-8
                minimum=min(x['prior_fights'] for x in sides);stratum='0' if minimum==0 else '1-2' if minimum<3 else '3-7' if minimum<8 else '8+'
                supported=all(x[k+'_supported'] for x in sides for k in ['access','control','submission','gnp'])
                context=dict(fight_id=fid,outer_year=year,event_date=t.event_date,division=t.division,scheduled_rounds=int(t.scheduled_rounds),support_stratum=stratum,supported=supported,source_lock_sha256=source_hash,fold_sha256=sha(foldpath))
                records.append(dict(**context,**v));summaries.append(dict(**context,status=v['status'],failure_code=v['failure_code'],certified_structural=v['certified_structural']))
            print('Outcome-blind construction complete',year,flush=True)
    csv(out/'ability_records.csv.gz',pd.DataFrame(abilities));js(out/'opportunity_transition_reward_records.json',records);df=pd.DataFrame(summaries);csv(out/'feasibility_rows.csv',df)
    valid=df.status.eq('VALID');supported=df.supported
    counts=df.failure_code.value_counts().to_dict();struct=int(df.certified_structural.sum());invalid=int((~valid).sum())
    breakdown=[]
    for key in ['outer_year','division','support_stratum','scheduled_rounds']:
        for label,g in df.groupby(key):
            breakdown.append(dict(dimension=key,cell=str(label),rows=len(g),valid=int(g.status.eq('VALID').sum()),invalid=int(g.status.ne('VALID').sum()),certified_structural=int(g.certified_structural.sum()),failure_codes=g.failure_code.value_counts().to_dict()))
    js(out/'breakdown.json',breakdown)
    result=dict(starting_main_sha=START,outer_rows=4260,valid_outer_rows=int(valid.sum()),invalid_outer_rows=invalid,supported_rows=int(supported.sum()),supported_valid_rows=int((valid&supported).sum()),supported_feasibility_fraction=float(valid[supported].mean()),overall_feasibility_fraction=float(valid.mean()),failure_codes=counts,certified_structural_rows=struct,unresolved_or_numerical_rows=invalid-struct,outcomes_scored=0,prospective_outcomes_accessed=False,status='BLOCKED_OPPORTUNITY_FEASIBILITY' if invalid or valid[supported].mean()<.99 else 'PREFLIGHT_PASS',classification='D' if int((df.certified_structural&supported).sum()) else 'E' if invalid else None)
    js(out/'PREFLIGHT_RESULT.json',result)
    js(out/'VALIDATION.json',dict(strict_prior_reconstruction=True,ability_max_error=max_ability,POC_A_prediction_max_error=max_A,directional_swap_max_error=max_swap,chronology=chronology,numerical=numerical,outer_outcomes_read=False,pinned_numpy=np.__version__,pinned_scipy=__import__('scipy').__version__,python=sys.version,ordered_ids_sha256=sha(foldpath),source_lock_sha256=source_hash))
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
