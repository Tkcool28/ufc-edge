"""Replay every construction without recovering target outcomes."""
import json,sys,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from preflight import P,SRC,CON,ROOT,sha,clean,construct
import publication

def verify(out=None):
    out=out or P/'run_v1'
    records=json.loads((out/'opportunity_transition_reward_records.json').read_text())
    abilities=pd.read_csv(out/'ability_records.csv.gz',float_precision='round_trip').set_index(['fight_id','side'])
    with tempfile.TemporaryDirectory() as td:
        publication.restore(Path(td));pools=json.loads((Path(td)/'population_priors.json').read_text())
    pools={p['outer_year']:p for p in pools};max_reward=0.;max_flux=0.;max_identity=0.
    for r in records:
        a=abilities.loc[(r['fight_id'],0)].to_dict();b=abilities.loc[(r['fight_id'],1)].to_dict();prior=pools[r['outer_year']]['divisions'][r['division']]
        actual=clean(construct(a,b,prior,r['scheduled_rounds']))
        for key,value in actual.items():assert r[key]==value,(r['fight_id'],key)
        if r['status']=='VALID':
            z=r['solution'];max_identity=max(max_identity,r['identity_error'])
            for key in ['TD','SUB','GNP']:
                err=max(abs(np.array(z['actions'][key])-z['targets'][key])/np.maximum(1.,z['targets'][key]));assert err<=1e-7;max_reward=max(max_reward,float(err))
            max_flux=max(max_flux,max(abs(np.array(z['flux_residual']))));assert max_flux<=1e-8
    print(json.dumps({'saved_records_replayed':len(records),'exact_regeneration':True,'maximum_reward_residual':max_reward,'maximum_boundary_flux_residual':max_flux,'maximum_conditional_identity_error':max_identity}),flush=True)
    return dict(saved_records_replayed=len(records),exact_regeneration=True,maximum_reward_residual=max_reward,maximum_boundary_flux_residual=max_flux,maximum_conditional_identity_error=max_identity)
if __name__=='__main__':verify()
