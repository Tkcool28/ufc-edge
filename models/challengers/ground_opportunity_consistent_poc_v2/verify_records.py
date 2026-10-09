"""Exact artifact recovery and deterministic, tolerance-qualified numerical replay."""
import json,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from preflight import P,SRC,CON,ROOT,sha,clean,construct
import publication
import opportunity as op

def compare_record(r,actual):
    # Inputs and support remain immutable; solver low-order bits may differ
    # across Python patch releases/BLAS builds, without changing equations.
    for key in ['status','failure_code','certified_structural','raw_proxy','target_ground','regularized','standing_target','TD_reward','SUB_reward','GNP_reward','TD_success','SUB_conversion','GNP_conversion','standing_KO']:
        assert r[key]==actual[key],(r['fight_id'],key)
    td=np.array(r['TD_reward']);u=np.array(r['SUB_reward']);g=np.array(r['GNP_reward']);q=np.array(r['target_ground']);s=r['standing_target'];pi=np.array(r['TD_success']);cv=np.array(r['SUB_conversion']);gv=np.array(r['GNP_conversion'])
    terminal=u/q*cv+g/q*gv;entry=td/s*pi;upper=td*pi/q-terminal
    if r['status']=='UNAVAILABLE':
        # Preserve failed fits as evidence. Re-evaluate their saved point;
        # successful optimizer termination is not equality feasibility.
        detail=r['detail'];returns=np.array(detail['returns'])
        assert np.isfinite(detail['jacobian']).all() and np.array(detail['jacobian']).shape==(2,2)
        assert np.allclose(detail['return_upper_bound'],upper,rtol=0,atol=1e-12)
        assert (returns>=0).all() and (returns<=upper+1e-12).all()
        x=op.exposures(entry,returns,terminal,r['standing_KO'],r['scheduled_rounds'])
        residual=x['shares'][1:]-q
        assert max(abs(residual-np.array(detail['residual'])))<=1e-10
        assert max(abs(residual))>1e-8
        return 0.,0.,0.
    z=r['solution'];returns=np.array(z['returns'])
    assert np.isfinite(z['jacobian']).all() and np.array(z['jacobian']).shape==(2,2)
    assert (returns>=0).all() and (returns<=upper+1e-12).all()
    x=op.exposures(entry,returns,terminal,r['standing_KO'],r['scheduled_rounds'])
    assert max(abs(x['shares'][1:]-q))<=1e-8
    assert max(abs(x['shares'][1:]-q-np.array(z['solver_residual'])))<=1e-10
    reward_error=0.
    for key,hazard,exposure,total in [('TD',td/s,x['minutes'][0],td),('SUB',u/q,x['minutes'][1:],u),('GNP',g/q,x['minutes'][1:],g)]:
        actions=hazard*exposure;targets=total*x['alive']
        error=max(abs(actions-targets)/np.maximum(1.,targets));assert error<=1e-7;reward_error=max(reward_error,float(error))
        assert max(abs(actions-z['actions'][key])/np.maximum(1.,actions))<=1e-7
        assert max(abs(targets-z['targets'][key])/np.maximum(1.,targets))<=1e-7
    flux=entry*x['minutes'][0]-(returns+terminal)*x['minutes'][1:]-x['boundary_removal_mass']
    flux_error=float(max(abs(flux)));assert flux_error<=1e-8
    raw=np.array([r['standing_KO']*x['minutes'][0]+np.dot(g/q*gv,x['minutes'][1:]),np.dot(u/q*cv,x['minutes'][1:]),x['decision']])
    assert abs(raw.sum()-1)<=1e-10 and min(raw)>=0
    assert max(abs(raw-np.array([r['raw_KO'],r['raw_SUB'],r['raw_DEC']])))<=1e-10
    k=raw[0]/sum(raw[:2]);identity_error=abs(k-r['closed_form_K']);assert identity_error<=1e-8
    assert abs(k-r['K'])<=1e-8 and abs(actual['K']-r['K'])<=1e-8
    return reward_error,flux_error,identity_error

def verify(out=None):
    out=out or P/'run_v1'
    records=json.loads((out/'opportunity_transition_reward_records.json').read_text())
    abilities=pd.read_csv(out/'ability_records.csv.gz',float_precision='round_trip').set_index(['fight_id','side'])
    with tempfile.TemporaryDirectory() as td:
        publication.restore(Path(td));pools=json.loads((Path(td)/'population_priors.json').read_text())
    pools={p['outer_year']:p for p in pools};max_reward=0.;max_flux=0.;max_identity=0.;bit_exact=True
    for r in records:
        a=abilities.loc[(r['fight_id'],0)].to_dict();b=abilities.loc[(r['fight_id'],1)].to_dict();prior=pools[r['outer_year']]['divisions'][r['division']]
        actual=clean(construct(a,b,prior,r['scheduled_rounds']))
        repeat=clean(construct(a,b,prior,r['scheduled_rounds']))
        assert actual==repeat,(r['fight_id'],'nondeterministic same-runtime solve')
        bit_exact &= all(r[key]==value for key,value in actual.items())
        reward,flux,identity=compare_record(r,actual)
        max_reward=max(max_reward,reward);max_flux=max(max_flux,flux);max_identity=max(max_identity,identity)
    result=dict(saved_records_replayed=len(records),same_runtime_deterministic=True,exact_regeneration=bit_exact,cross_runtime_frozen_tolerances_pass=True,maximum_reward_residual=max_reward,maximum_boundary_flux_residual=max_flux,maximum_conditional_identity_error=max_identity)
    print(json.dumps(result),flush=True)
    return result
if __name__=='__main__':verify()
