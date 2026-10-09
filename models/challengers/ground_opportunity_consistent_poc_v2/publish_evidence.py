"""Lossless blocked-run evidence verification, without target outcomes."""
import hashlib,io,json,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[2];OUT=P/'run_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def restore():
    m=json.loads((OUT/'RECORDS_MANIFEST.json').read_text());parts=[]
    for item in m['parts']:
        data=(OUT/item['name']).read_bytes();assert hashlib.sha256(data).hexdigest()==item['sha256'];parts.append(data)
    data=b''.join(parts);assert hashlib.sha256(data).hexdigest()==m['archive_sha256']
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:xz') as t:
        assert set(t.getnames())==set(m['members'])
        for name,digest in m['members'].items():
            raw=t.extractfile(name).read();assert hashlib.sha256(raw).hexdigest()==digest;(OUT/name).write_bytes(raw)
def main():
    m=json.loads((OUT/'EVIDENCE_MANIFEST.json').read_text())
    assert sha(ROOT/'.github/workflows/ground-opportunity-consistent-poc-v2.yml')==m['workflow_sha256']
    for name,digest in m['artifacts'].items():assert sha(ROOT/name)==digest,name
    restore()
    for name,digest in m['restored_records'].items():assert sha(OUT/name)==digest,name
    marker=json.loads((OUT/'COMPLETION.json').read_text());assert marker['evidence_manifest_sha256']==sha(OUT/'EVIDENCE_MANIFEST.json')
    assert marker['status']=='BLOCKED_OPPORTUNITY_FEASIBILITY' and marker['outcomes_scored']==0
    from verify_records import verify
    verify();print('Publication/hash verification PASS',sha(OUT/'EVIDENCE_MANIFEST.json'))
if __name__=='__main__':main()
