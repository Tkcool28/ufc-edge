"""Independent audit evidence, exact population and zero-fit probability checks."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('pathway_verify',ROOT/'tools/diagnostics/verify_mov1_three_family_finish_pathways_v1.py')
v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def test_committed_audit_matches_frozen_source_predictions_and_uncertainty():
 result=v.verify()
 assert result['status']=='AUDIT_EVIDENCE_VERIFIED'
 assert result['conditional_finishes']==2115 and result['all_fights']==4260
 assert result['additional_predictive_fits']==0
