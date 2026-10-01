"""Verify every persisted MOV1 prediction from fitted records without refitting MOV0."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'models/mov1'))
from implementation_v1 import (SURFACES, probability, require, restore_model, sha, verify_inputs)


def verify(f02,mov0,run_dir):
    manifest=json.loads((run_dir/'EVIDENCE_MANIFEST.json').read_text())
    for path,record in manifest['files'].items():
        require(sha(run_dir/path)==record['sha256'],'Evidence mismatch '+path)
    frame,_,finish_node,_=verify_inputs(f02,mov0)
    scores=pd.read_csv(run_dir/'conditional_oof_all_eligible.csv',float_precision='round_trip')
    composed=pd.read_csv(run_dir/'composed_oof_all_eligible.csv',float_precision='round_trip')
    require(len(scores)==17040 and len(composed)==17040,'Unexpected row loss')
    max_error=0.;sum_error=0.
    with threadpool_limits(1):
        for year in range(2018,2027):
            rows=frame[frame.outer_year.eq(year)]
            F=finish_node.set_index('fight_id').loc[rows.fight_id].probability.to_numpy(float)
            for surface,system in zip(SURFACES,['S0','S1','S2','S3']):
                record=json.loads((run_dir/'MODELS'/f'{year}_{surface}.json').read_text())
                p=np.full(len(rows),record['P_KO_given_finish']) if surface=='C0' else probability(*restore_model(record),rows)
                saved=scores[scores.outer_year.eq(year)&scores.surface.eq(surface)].set_index('fight_id').loc[rows.fight_id]
                c=composed[composed.outer_year.eq(year)&composed.system.eq(system)].set_index('fight_id').loc[rows.fight_id]
                expected=np.c_[F*p,F*(1-p),1-F]
                e=max(float(np.max(abs(p-saved.P_KO_given_finish.to_numpy()))),float(np.max(abs(expected-c[['P_KO_TKO','P_SUBMISSION','P_DECISION']].to_numpy()))))
                require(e<=1e-12,'Persisted model/prediction mismatch')
                max_error=max(max_error,e);sum_error=max(sum_error,float(np.max(abs(expected.sum(axis=1)-1))))
    return {'status':'PERSISTED_RUN_REGENERATION_PASSED','all_binary_score_rows':17040,'all_composed_score_rows':17040,
            'max_probability_error':max_error,'max_composition_sum_error':sum_error,'atol':1e-12,'rtol':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--f02-table',type=Path,required=True)
    parser.add_argument('--mov0-min-oof',type=Path,required=True)
    parser.add_argument('--run-dir',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(verify(args.f02_table,args.mov0_min_oof,args.run_dir),indent=2))
