"""Prove the scientific functions, NUTS settings and evaluation stayed frozen."""
import ast,hashlib,json,importlib.util
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[2]
SPEC=ROOT/'models/challengers/mov0_hierarchical_v1_1'

def tree(path):return ast.parse(path.read_text())
def funcs(t):return {n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.FunctionDef)}
def samples(t):
    return [{k.arg:ast.dump(k.value,include_attributes=False) for k in n.keywords} for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='pm' and n.func.attr=='sample']

def test_exact_scientific_source_and_specification():
    c=json.loads((SPEC/'amendment.json').read_text())
    for path,h in {**c['scientific_specification_hashes'],**c['source_snapshots'],**c['immutable_sources']}.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    old=funcs(tree(SPEC/'v1_source/run_mov0_hierarchical_v1.py'));new=funcs(tree(ROOT/'tools/models/run_mov0_hierarchical_v1_1.py'))
    for name in old.keys()-{'main'}:assert old[name]==new[name],name
    assert (ROOT/'tools/models/evaluate_mov0_hierarchical_v1.py').read_bytes()==(SPEC/'v1_source/evaluate_mov0_hierarchical_v1.py').read_bytes()

def test_only_sampling_budget_changed_in_all_calls():
    old=samples(tree(SPEC/'v1_source/run_mov0_hierarchical_v1.py'));new=samples(tree(ROOT/'tools/models/run_mov0_hierarchical_v1_1.py'))
    assert len(old)==len(new)==2
    for a,b in zip(old,new):
        for k in ['draws','tune']:
            assert a.pop(k)=="Constant(value=1000)"
            assert b.pop(k)=="Constant(value=2000)"
        assert a==b

def test_shared_scale_hierarchy_remains_wired():
    import pymc as pm
    sp=importlib.util.spec_from_file_location('hier11',ROOT/'tools/models/run_mov0_hierarchical_v1_1.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
    model=h.build_model(np.ones((6,3)),np.array([0,1,0,1,0,1]),np.array([0,0,0,1,1,1]),2,[0,2],[0,3])
    with model:prior=pm.sample_prior_predictive(samples=5,random_seed=17)
    np.testing.assert_allclose(prior.prior.slope_deviation.values,prior.prior.z_slope.values*prior.prior.tau_family.values[:,:,None,[0,3]])
    assert np.isfinite(model.compile_logp()(model.initial_point()))
