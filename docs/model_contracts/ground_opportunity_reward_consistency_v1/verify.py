"""Hash verification only. Does not reconstruct measurements or score predictions."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((P/'EVIDENCE_MANIFEST.json').read_text())
for name,sha in manifest['artifacts'].items():
    assert digest(ROOT/name)==sha,f'contract artifact changed: {name}'
lock=json.loads((P/'SOURCE_LOCK.json').read_text())
for name,sha in lock['hashes'].items():
    assert digest(ROOT/name)==sha,f'frozen source changed: {name}'
marker=json.loads((P/'COMPLETION.json').read_text())
assert marker['evidence_manifest_sha256']==digest(P/'EVIDENCE_MANIFEST.json')
assert marker['completion']=='UFC_EDGE_GROUND_OPPORTUNITY_REWARD_CONSISTENCY_CONTRACT_V1_COMPLETE'
assert manifest['starting_main_sha']==lock['starting_main_sha']=='675da47d6ad9b937c4b01dcd3986250b72308948'
result=json.loads((P/'SYNTHETIC_VALIDATION.json').read_text())
assert result['status']=='PASS' and result['tests_run']==18 and result['real_fights_used']==result['outcomes_scored']==0 and result['POC_B_executed'] is False
assert not marker['POC_B_executed'] and not marker['outer_performance_inspected']
print(f"PASS: {len(manifest['artifacts'])} contract artifacts; {len(lock['hashes'])} frozen sources; 18 synthetic tests; no challenger")
