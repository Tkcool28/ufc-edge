"""Hash-locked feasibility investigation replay. Never reads scoring outcomes."""
import argparse,hashlib,importlib.util,io,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
def digest(data):return hashlib.sha256(data).hexdigest()
def read(name):return json.loads((P/name).read_text())
def restore():
    m=read('RECORDS_MANIFEST.json');chunks=[]
    for part in m['parts']:
        data=(P/part['name']).read_bytes();assert digest(data)==part['sha256'];chunks.append(data)
    archive=b''.join(chunks);assert digest(archive)==m['archive_sha256']
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:xz') as t:
        assert set(t.getnames())==set(m['members'])
        for name,sha in m['members'].items():
            assert Path(name).name==name
            data=t.extractfile(name).read();assert digest(data)==sha;(P/name).write_bytes(data)
    original=ROOT/'models/challengers/ground_opportunity_consistent_poc_v2/publish_evidence.py'
    spec=importlib.util.spec_from_file_location('original_restore',original);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.restore()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--replay',action='store_true');args=ap.parse_args()
    m=read('EVIDENCE_MANIFEST.json')
    for name,sha in m['artifacts'].items():assert digest((ROOT/name).read_bytes())==sha,name
    assert read('COMPLETION.json')['evidence_manifest_sha256']==digest((P/'EVIDENCE_MANIFEST.json').read_bytes())
    restore()
    for name,sha in read('SOURCE_LOCK.json')['files'].items():assert digest((ROOT/name).read_bytes())==sha,name
    if args.replay:
        with tempfile.TemporaryDirectory(prefix='poc-v2-diagnosis-') as folder:
            out=Path(folder)
            subprocess.run([sys.executable,str(P/'root_probe.py'),'--output',str(out/'roots.json')],check=True,cwd=ROOT)
            subprocess.run([sys.executable,str(P/'investigate.py'),'--output',str(out),'--roots',str(out/'roots.json')],check=True,cwd=ROOT)
            for name in ['RESULT.json','row_diagnosis.json']:
                assert json.loads((out/name).read_text())==read(name),name
            saved=read('numerical_witness.json');fresh=json.loads((out/'numerical_witness.json').read_text())
            assert [x['fight_id'] for x in saved]==[x['fight_id'] for x in fresh]
            assert all(x['occupancy_error']<=1e-8 and x['reward_residual']<=1e-7 for x in fresh)
    print('Diagnosis verification PASS',digest((P/'EVIDENCE_MANIFEST.json').read_bytes()))
if __name__=='__main__':main()
