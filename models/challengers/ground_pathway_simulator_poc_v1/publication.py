"""Lossless evidence packaging and immutable publication checks; zero scoring changes."""
import argparse, hashlib, io, json, lzma, shutil, tarfile, tempfile
from pathlib import Path
import run
P=Path(__file__).resolve().parent;OUT=P/'run_v1'
LARGE=['fighter_abilities.csv.gz','population_priors.json','prediction_only.csv','predictions.csv.gz','simulator_records.json']

def package():
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w') as t:
        for name in LARGE:
            data=(OUT/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.mode=0o644;t.addfile(info,io.BytesIO(data))
    archive=lzma.compress(buffer.getvalue(),preset=6);parts=[]
    for i,start in enumerate(range(0,len(archive),100000)):
        name=f'RECORDS.tar.xz.part{i:03d}';(OUT/name).write_bytes(archive[start:start+100000]);parts.append({'name':name,'sha256':run.sha(OUT/name),'bytes':(OUT/name).stat().st_size})
    m={'archive_sha256':hashlib.sha256(archive).hexdigest(),'parts':parts,
       'members':{name:{'sha256':run.sha(OUT/name),'bytes':(OUT/name).stat().st_size} for name in LARGE}}
    run.js(OUT/'RECORDS_MANIFEST.json',m)
    return m

def restore(dest):
    m=json.loads((OUT/'RECORDS_MANIFEST.json').read_text());parts=[]
    for a in m['parts']:
        data=(OUT/a['name']).read_bytes();assert hashlib.sha256(data).hexdigest()==a['sha256'];parts.append(data)
    data=b''.join(parts);assert hashlib.sha256(data).hexdigest()==m['archive_sha256']
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:xz') as t:
        assert set(t.getnames())==set(LARGE)
        for name in LARGE:
            raw=t.extractfile(name).read();assert hashlib.sha256(raw).hexdigest()==m['members'][name]['sha256']
            (dest/name).write_bytes(raw)

def manifest():
    verification=json.loads((OUT/'SIMULATION_VALIDATION.json').read_text());assert verification['status']=='PASS'
    artifacts={str(p.relative_to(OUT)):{'sha256':run.sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in {'EVIDENCE_MANIFEST.json','UFC_EDGE_SIMPLIFIED_GROUND_PATHWAY_SIMULATOR_POC_V1_COMPLETE.json'} and p.name not in LARGE}
    raw=json.loads((OUT/'RECORDS_MANIFEST.json').read_text())['members']
    m={'starting_main':'f70848818005e54d2db000ec73677f2fd27be033','preregistration_sha':'b224f68a78558e55a9734d92ef6207967fef8f01',
       'pre_scoring_manifest_sha256':run.sha(P/'PRE_SCORING_MANIFEST.json'),'artifacts':artifacts,'restored_records':raw,
       'publication_code_sha256':run.sha(Path(__file__)),'workflow_sha256':run.sha(run.R/'.github/workflows/ground-pathway-simulator-poc-v1-independent.yml')}
    run.js(OUT/'EVIDENCE_MANIFEST.json',m)
    decisions=json.loads((OUT/'GATE_DECISIONS.json').read_text())
    run.js(OUT/'UFC_EDGE_SIMPLIFIED_GROUND_PATHWAY_SIMULATOR_POC_V1_COMPLETE.json',
      {'marker':'UFC_EDGE_SIMPLIFIED_GROUND_PATHWAY_SIMULATOR_POC_V1_COMPLETE','status':'COMPLETE_VALID_NEGATIVE_RESULT',
       'starting_main':m['starting_main'],'branch':'feat/ground-pathway-simulator-poc-v1-independent','draft_pr':163,
       'classification':decisions['classification'],'scientific_success':False,'verification':'PASS',
       'evidence_manifest_sha256':run.sha(OUT/'EVIDENCE_MANIFEST.json'),'preregistration_sha':m['preregistration_sha'],
       'scored_fights':4260,'scored_standard_finishes':2115,'prospective_outcomes_accessed':False,'promoted':False,'merged':False})

def check():
    m=json.loads((OUT/'EVIDENCE_MANIFEST.json').read_text())
    for n,v in m['artifacts'].items():assert run.sha(OUT/n)==v['sha256'],n
    assert run.sha(P/'PRE_SCORING_MANIFEST.json')==m['pre_scoring_manifest_sha256']
    assert run.sha(Path(__file__))==m['publication_code_sha256']
    assert run.sha(run.R/'.github/workflows/ground-pathway-simulator-poc-v1-independent.yml')==m['workflow_sha256']
    frozen=json.loads((P/'PRE_SCORING_MANIFEST.json').read_text())
    for n,h in frozen['implementation'].items():assert run.sha(run.R/n)==h,n
    assert run.source_lock()==frozen['sources']
    completion=json.loads((OUT/'UFC_EDGE_SIMPLIFIED_GROUND_PATHWAY_SIMULATOR_POC_V1_COMPLETE.json').read_text())
    assert completion['evidence_manifest_sha256']==run.sha(OUT/'EVIDENCE_MANIFEST.json')
    with tempfile.TemporaryDirectory() as td:restore(Path(td))
    print('Immutable publication/evidence check PASS',run.sha(OUT/'EVIDENCE_MANIFEST.json'),flush=True)

def isolated_verify():
    import verify
    import pandas as pd
    reader=pd.read_csv
    def lossless_reader(*args,**kwargs):
        # Saved predictions have 17 significant digits. Pandas' default parser
        # can lose the last bit and perturb diagnostic BFGS coefficients. Only
        # this persisted output uses round-trip parsing; source readers unchanged.
        if args and str(args[0]).endswith('/predictions.csv.gz'):
            kwargs.setdefault('float_precision','round_trip')
        return reader(*args,**kwargs)
    with tempfile.TemporaryDirectory() as td:
        dest=Path(td)
        for p in OUT.iterdir():
            if p.is_file() and p.name not in LARGE and not p.name.startswith('RECORDS.tar.xz.part'):shutil.copy2(p,dest/p.name)
        restore(dest)
        pd.read_csv=lossless_reader
        try:verify.verify(dest)
        finally:pd.read_csv=reader
    # The verifier writes only temporary evidence; original manifest stays exact.
    check()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--package',action='store_true');ap.add_argument('--manifest',action='store_true');ap.add_argument('--check',action='store_true');ap.add_argument('--verify-isolated',action='store_true');a=ap.parse_args()
    if a.package:print(json.dumps({'parts':len(package()['parts'])}))
    if a.manifest:manifest()
    if a.verify_isolated:isolated_verify()
    if a.check:check()
