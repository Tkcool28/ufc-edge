"""Separately authorized frozen experiment; bounded fits, then saved-only evaluation."""
import argparse,json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'models/challengers/mov1_three_arm_directional_run_v1'))
from implementation import training,write_json,sha,D,require
from reporting import evaluate
from verification import verify,package,package_tables
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--f02',required=True);p.add_argument('--mov0',required=True);p.add_argument('--output',required=True);p.add_argument('--implementation-freeze',required=True);a=p.parse_args();out=pathlib.Path(a.output)
    try:
        inputs=training(a.f02,a.mov0,out,a.implementation_freeze);evaluate(*inputs,out);verify(out,a.f02);package(out);package_tables(out)
        write_json(out/'MOV1_THREE_ARM_DIRECTIONAL_CHALLENGER_V1_RUN_COMPLETE.json',{'marker':'MOV1_THREE_ARM_DIRECTIONAL_CHALLENGER_V1_RUN_COMPLETE','engineering_status':'PASS','completed_fits':164,'Arm_A_refits':0,'MOV0_refits':0,'implementation_freeze_SHA':a.implementation_freeze,'contract_SHA256':sha(D/'CONTRACT_MANIFEST.json'),'post_boundary_outcomes_accessed':False,'forward_composition':'BLOCKED_MISSING_FROZEN_MOV0_RECORD','automatically_promoted':False})
        manifest={'experiment':'MOV1_THREE_ARM_DIRECTIONAL_CHALLENGER_V1','files':{str(p.relative_to(out)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='EVIDENCE_MANIFEST.json' and 'MODELS/' not in str(p.relative_to(out)) and p.name not in json.loads((out/'EVALUATION_TABLES_MANIFEST.json').read_text())['members']},'native_records_manifest':'NATIVE_MODELS_MANIFEST.json','hash_policy':'no self-reference; all original fitted records preserved in hashed native parts; referenceA read unchanged'}
        write_json(out/'EVIDENCE_MANIFEST.json',manifest);print('RUN_COMPLETE '+sha(out/'EVIDENCE_MANIFEST.json'),flush=True)
    except Exception as exc:
        out.mkdir(parents=True,exist_ok=True);write_json(out/'EXECUTION_INVALID_INCOMPLETE.json',{'status':'INVALID_INCOMPLETE','error_type':type(exc).__name__,'error':str(exc),'scientific_interpretation_permitted':False,'do_not_rerun_or_change_specification':True});raise
