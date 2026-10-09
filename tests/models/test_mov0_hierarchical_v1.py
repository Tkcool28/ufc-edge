import importlib.util,json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('hier',ROOT/'tools/models/run_mov0_hierarchical_v1.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)

def test_hierarchy_is_shared_scale_and_only_registered_slopes():
    X=np.arange(30,dtype=float).reshape(10,3)/30
    model=h.build_model(X,np.tile([0,1],5),np.tile([0,1],5),2,[0,2],[0,3])
    assert model['z_slope'].eval().shape==(2,2)
    assert model['tau_family'].eval().shape==(4,)
    assert set(v.name for v in model.free_RVs)=={'alpha','beta','tau_intercept','z_intercept','tau_family','z_slope'}
    point=model.initial_point();assert np.isfinite(model.compile_logp()(point))
    point['z_slope'][1,0]=2
    assert np.isfinite(model.compile_logp()(point))
    model1=h.build_model(X,np.tile([0,1],5),np.tile([0,1],5),2,[],[])
    assert 'z_slope' not in model1.named_vars

def test_mapping_missing_and_unknown_fail_closed():
    mapping=json.loads((h.SPEC/'weight_class_map.json').read_text())['literal_map']
    f=pd.DataFrame({'ctx__weight_class':['Interim Heavyweight',None,"Ultimate Fighter 28 Women's Featherweight Tournament"]})
    assert h.groups(f,'Lightweight',mapping).tolist()==['Heavyweight','Lightweight',"Women's Featherweight"]
    with pytest.raises(ValueError):h.groups(pd.DataFrame({'ctx__weight_class':['new unsupported label']}),'Lightweight',mapping)

def test_exact_seven_columns_are_min_only():
    spec=json.loads((h.SPEC/'varying_effect_map.json').read_text())
    cols=sum(spec['families'].values(),[])
    assert len(cols)==7 and len(set(cols))==7
    assert not any('sig_strike' in c or 'takedown_conversion' in c for c in cols)
    assert set(spec['families'])=={'striking','submission','takedown','survival'}

def test_deviations_really_use_learned_family_scale():
    import pymc as pm
    X=np.ones((6,3));y=np.array([0,1,0,1,0,1]);g=np.array([0,0,0,1,1,1])
    model=h.build_model(X,y,g,2,[0,2],[0,3])
    with model:prior=pm.sample_prior_predictive(samples=5,random_seed=17)
    tau=prior.prior['tau_family'].values
    z=prior.prior['z_slope'].values
    ds=prior.prior['slope_deviation'].values
    np.testing.assert_allclose(ds,z*tau[:,:,None,[0,3]])
    np.testing.assert_allclose(prior.prior['intercept_deviation'].values,prior.prior['z_intercept'].values*prior.prior['tau_intercept'].values[:,:,None])

def test_evaluation_governance_and_paired_bucket_directions():
    sp=importlib.util.spec_from_file_location('evaluation',ROOT/'tools/models/evaluate_mov0_hierarchical_v1.py');e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
    f=pd.DataFrame({'year':[2018]*24,'target':[0,1]*12,'probability':[.5]*24})
    assert set(e.cell(f))=={'N','governance','years'}
    assert e.sign(-.001)=='HELPED' and e.sign(.001)=='HURT' and e.sign(0)=='UNCHANGED'
    f=pd.concat([f,f.iloc[:1]],ignore_index=True)
    assert e.cell(f)['governance']=='THIN_EXPLORATORY'
    assert len(e.arch.ARCHETYPES)==15
