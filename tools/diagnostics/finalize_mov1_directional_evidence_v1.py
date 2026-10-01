"""Create deterministic SHA256 manifest for PR123 zero-fit audit CI evidence."""
import argparse,hashlib,json,pathlib
R=pathlib.Path(__file__).resolve().parents[2]
FROZEN={'corrected_F02':'d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580',
         'boosted_predictions_archive_member':'d1899df12dc560e3633b37fee78c45a68246cfae16dcdb6de8627888bd423d02',
         'linear_predictions':'f8841d5007d0dec1000ed3c93a1d397428b2e5668cfdeedca6d3afc7fe4f2b3a'}
SOURCES=['tools/diagnostics/run_mov1_directional_representation_v1.py',
 'tools/diagnostics/verify_mov1_submission_lineage_v1.py',
 'tools/diagnostics/run_mov1_b3_b5_supplement_v1.py',
 'tests/diagnostics/test_mov1_directional_collision_v1.py',
 'models/mov1/implementation_v1.py',
 'tools/contracts/validate_mov1_boosted_contract_v1.py',
 'src/ufc_edge/features/state.py',
 'src/ufc_edge/features/history.py',
 'src/ufc_edge/features/aggregations.py',
 'src/ufc_edge/features/elapsed_exposure.py',
 'models/mov1/contracts/ko_vs_submission_given_finish_v1/mov1_min_allowlist.json',
 'tools/diagnostics/finalize_mov1_directional_evidence_v1.py',
 '.github/workflows/mov1-directional-audit-v1.yml',
 'features/feature_catalog.yaml',
 'data/canonical/v0/events.csv',
 'data/canonical/v0/fights.csv',
 'data/canonical/v0/fighter_round_stats.csv',
 'provenance/rulesets/elapsed_exposure_ruleset_registry_v1.json',
 'governance/finish_method_target_structure_v1/EVIDENCE_MANIFEST.json',
 'models/mov1/run_v1/EVIDENCE_MANIFEST.json',
 'models/challengers/mov1_boosted_v1/run_v1/EVIDENCE_MANIFEST.json',
 'docs/model_diagnostics/mov1_three_family_finish_pathways_v1/EVIDENCE_MANIFEST.json',
 'docs/model_diagnostics/mov1_directional_representation_v1/MOV1_EXACT_35_COLUMN_INVENTORY.csv',
 'docs/model_diagnostics/mov1_directional_representation_v1/MOV1_STATE_CONCEPT_TO_FEATURE_MAP.csv',
 'docs/model_diagnostics/mov1_directional_representation_v1/MOV1_FOLD_SAMPLE_SUPPORT.csv',
 'docs/model_diagnostics/mov1_directional_representation_v1/MOV1_DIVISION_TRAINING_COMPLETENESS.csv']
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def run(out):
 assert (out/'B3_B5_CHRONOLOGY_DIVISION_EXPERIENCE_MISSINGNESS.csv').exists()
 assert (out/'B3_B5_DIAGNOSTIC_MANIFEST.json').exists()
 info=json.loads((out/'B3_B5_DIAGNOSTIC_MANIFEST.json').read_text())
 assert info['saved_predictions_SHA256']['boosted_archive_member']==FROZEN['boosted_predictions_archive_member']
 assert info['saved_predictions_SHA256']['linear_oof']==FROZEN['linear_predictions']
 assert info['frozen_F02_SHA256']==FROZEN['corrected_F02']
 assert info['file_SHA256']==sha(out/'B3_B5_CHRONOLOGY_DIVISION_EXPERIENCE_MISSINGNESS.csv')
 src={n:sha(R/n) for n in SOURCES}
 outputs={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='EVIDENCE_MANIFEST.json'}
 result={'audit':'MOV1_DIRECTIONAL_FEATURE_REPRESENTATION_AUDIT_V1','base_main':'6f92ce406af77758bacd2ce1f91fbbce0b4fc64b','FROZEN_IDENTITIES':FROZEN,'source_SHA256':src,'generated_evidence':outputs,'prediction_training_fits':0,'post_boundary_outcome_inspection':False,'calibrator_applied':False,'source_artifact_retrieval_run':35182939981}
 dest=out/'EVIDENCE_MANIFEST.json';dest.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 committed=R/'docs/model_diagnostics/mov1_directional_representation_v1/EVIDENCE_MANIFEST.json'
 if committed.exists():assert sha(committed)==sha(dest),'Committed evidence manifest differs from CI regeneration'
 print('PR123_MANIFEST_BEGIN')
 print(json.dumps({'sha256':sha(dest),'content':result},sort_keys=True))
 print('PR123_MANIFEST_END')
 return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);p=a.parse_args();run(pathlib.Path(p.output))
