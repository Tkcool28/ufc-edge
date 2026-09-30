#!/usr/bin/env python3
"""Validate an accepted or blocked V1.1 publication, never refit it."""
import argparse,gzip,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evidence-dir',type=Path,required=True);a=ap.parse_args();out=a.evidence_dir
    m=read(out/'MANIFEST.json')
    for name,r in m['files'].items():
        b=(out/name).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];assert len(b)==r['bytes']
    amend=read(ROOT/'models/challengers/mov0_hierarchical_v1_1/amendment.json')
    for path,h in {**amend['scientific_specification_hashes'],**amend['source_snapshots'],**amend['immutable_sources']}.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    ds=read(out/('fit_diagnostics.json.gz' if (out/'fit_diagnostics.json.gz').exists() else 'fit_diagnostics.json'))
    assert len({(d['surface'],d['year']) for d in ds})==len(ds)
    if (out/'BLOCKED.json').exists():
        assert read(out/'BLOCKED.json')['status']=='V1_1_BLOCKED_CONVERGENCE'
        assert not ds[-1]['passed'] and all(d['passed'] for d in ds[:-1])
        assert not (out/'COMPLETE.json').exists()
        print('V1_1_BLOCKED_EVIDENCE_VERIFIED');return
    assert len(ds)==18 and all(d['passed'] for d in ds)
    assert read(out/'FIT_COMPLETE.json')['status']=='V1_1_CONVERGENCE_VALIDATED'
    repro=read(out/'reproducibility.json');assert repro['posterior_arrays_identical'] and repro['predictions_identical']
    assert read(out/'COMPLETE.json')['status']=='MOV0_HIERARCHICAL_PARTIAL_POOLING_CHALLENGER_V1_1_COMPLETE'
    print('V1_1_COMPLETE_EVIDENCE_VERIFIED')
if __name__=='__main__':main()
