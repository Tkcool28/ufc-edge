#!/usr/bin/env python3
"""Check durable publication without refitting or changing frozen inputs."""
import argparse,gzip,hashlib,json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',type=Path,required=True);a=ap.parse_args();p=a.evidence_dir
    manifest=json.loads((p/'MANIFEST.json').read_text())
    for rel,record in manifest['files'].items():
        data=(p/rel).read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256'];assert len(data)==record['bytes']
    for rel,h in manifest['immutable_sources'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==h
    if manifest['status']=='BLOCKED_CONVERGENCE':
        blocked=json.loads((p/'BLOCKED.json').read_text());assert blocked['status']=='BLOCKED_CONVERGENCE'
        ds=json.loads(gzip.decompress((p/'fit_diagnostics.json.gz').read_bytes()))
        assert len(ds)==8 and sum(d['passed'] for d in ds)==7 and not ds[-1]['passed']
        assert (ds[-1]['surface'],ds[-1]['year'])==('H2',2021)
        assert not (p/'COMPLETE.json').exists()
        for f in p.glob('fold_*.csv.gz'):
            df=pd.read_csv(f);assert not df.fight_id.duplicated().any();assert df.probability.between(0,1).all()
        assert len(list(p.glob('fold_*.csv.gz')))==7
        print('PARTIAL_BLOCKED_EVIDENCE_VERIFIED');return
    done=json.loads((p/'COMPLETE.json').read_text());assert done['status']=='MOV0_HIERARCHICAL_PARTIAL_POOLING_CHALLENGER_V1_COMPLETE'
    ds=json.loads((p/'fit_diagnostics.json').read_text());assert len(ds)==18 and all(d['passed'] for d in ds)
    ids=None
    for s in ['H1','H2']:
        df=pd.read_csv(p/f'oof_{s}.csv');assert len(df)==4260 and not df.fight_id.duplicated().any()
        assert set(df.year)==set(range(2018,2027));assert df.probability.between(0,1).all()
        if ids is None:ids=df.fight_id.tolist()
        else:assert ids==df.fight_id.tolist()
    for fname in ['aggregate_metrics.json','annual_metrics.json','paired_uncertainty.json','validation_terrain.json','probability_buckets.json','archetype_comparison.json','varying_effects_and_shrinkage.json','HELPED_HURT_UNCHANGED.md','IMPLICATIONS_FOR_MOV1.md','IMPLICATIONS_FOR_HYBRID_SIMULATOR.md','REPORT.md']:assert (p/fname).exists()
    print('DURABLE_EVIDENCE_VERIFIED')
if __name__=='__main__':main()
