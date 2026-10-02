"""No-fit verification of saved experiment evidence."""
import argparse,pathlib,sys,json
R=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'models/challengers/mov1_three_arm_directional_run_v1'))
from verification import verify,restore_tables
from implementation import sha,require
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--f02',required=True);a=p.parse_args();out=pathlib.Path(a.output)
    manifest=json.loads((out/'EVIDENCE_MANIFEST.json').read_text())
    for name,record in manifest['files'].items():require(sha(out/name)==record['sha256'],'Evidence bytes mismatch '+name)
    restore_tables(out)
    print(json.dumps(verify(out,a.f02),sort_keys=True))
