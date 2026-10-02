"""Outcome-free contract tests. No predictive estimator fitting."""
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('three_arm_validator',R/'tools/contracts/validate_mov1_three_arm_contract_v1.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture():
    spec=m.load('feature_specifications.json');cols=spec['arms']['B']['raw_columns'];rng=np.random.default_rng(17)
    x=pd.DataFrame({c:rng.uniform(.1,.9,200) for c in cols if c not in ['ctx__weight_class','ctx__title_bout','scheduled_rounds']})
    x['ctx__weight_class']='Lightweight';x['ctx__title_bout']=np.arange(200)%2;x['scheduled_rounds']=np.where(np.arange(200)%3,3,5)
    return x

def test_collision_formula_and_swap():
    p=np.array([[.9,.1,.1,.9],[.9,.1,.9,.1]])
    assert np.allclose(m.operation('cross_product_sum',p),[.82,.18])
    assert np.array_equal(m.operation('cross_product_sum',p),m.operation('cross_product_sum',p[:,[1,0,3,2]]))
    assert np.allclose(m.operation('pressure_against_weakness_sum',np.array([[2,3,.2,.7]])),[3.])

def test_compact_nonredundant_synthetic_rank():
    pp=m.MatrixProbe('C').freeze(fixture());raw=pp.unscaled(fixture());numeric=raw[:,pp.scaled]
    assert numeric.shape[1]==14
    assert np.linalg.matrix_rank(numeric-numeric.mean(axis=0))==14

def test_shared_imputation_before_interaction():
    x=fixture();cols=m.load('feature_specifications.json')['source_concepts'];p=cols['SUB_PRESSURE']['columns'];v=cols['SUB_EXPOSURE']['columns']
    x.loc[:20,p[0]]=np.nan;x.loc[15:30,v[1]]=np.nan
    b=m.MatrixProbe('B').freeze(x);c=m.MatrixProbe('C').freeze(x)
    for pair in set(c.medians)&set(b.medians):assert b.medians[pair]==c.medians[pair]
    bi=b.imputed(x);ci=c.imputed(x)
    assert np.array_equal(bi[p+v],ci[p+v])
    expect=bi[p[0]]*bi[v[1]]+bi[p[1]]*bi[v[0]]
    assert np.allclose(b.unscaled(x)[:,33],expect)
    assert np.allclose(c.unscaled(x)[:,11],expect)

def test_labels_and_score_cannot_change_parameters():
    x=fixture();pp=m.MatrixProbe('C').freeze(x);before=pp.transform(x);means=pp.mean.copy();med=dict(pp.medians)
    y=x.copy();y['method']='KO_TKO';y['winner_id']='anything';assert np.array_equal(before,pp.transform(y))
    y.iloc[0,0]=1e6;pp.transform(y);assert pp.medians==med and np.array_equal(pp.mean,means)

def test_swap_with_missing_sources():
    x=fixture()
    for arm in ['B','C']:
        pp=m.MatrixProbe(arm).freeze(x);y=x.copy()
        for a,b in pp.pairs:y.loc[0,a]=np.nan;y.loc[1,[a,b]]=np.nan
        assert np.allclose(pp.transform(y),pp.transform(pp.swap(y)),atol=1e-12,rtol=0)

def test_all_missing_is_not_zero():
    x=fixture();pair=m.MatrixProbe('C').pairs[0];x[list(pair)]=np.nan
    with pytest.raises(ValueError,match='All missing'):m.MatrixProbe('C').freeze(x)

def test_domain_and_probability_algebra():
    rng=np.random.default_rng(17);F=rng.random(100);K=rng.random(100)
    for candidate in [K,1-K,np.zeros(100)]:
        z=np.c_[F*candidate,F*(1-candidate),1-F]
        assert np.allclose(z.sum(axis=1),1,atol=1e-12,rtol=0)
        assert np.array_equal(z[:,2],1-F)

def test_exact_three_arm_inventory():
    a=m.load('feature_specifications.json')['arms']
    assert [len(a[k]['predictors']) for k in 'ABC']==[34,35,15]
    assert [len(a[k]['raw_columns']) for k in 'ABC']==[35,35,23]
    assert [f for f in a['B']['predictors'] if f['name']!='SUB_DIRECTIONAL_SUM']==a['A']['predictors']
    assert [f['name'] for f in a['C']['predictors']]==['KD_CREATED_MEAN','KD_ALLOWED_MEAN','KO_WIN_MEAN','KO_LOSS_MEAN','SUB_PRESSURE_MEAN','SUB_EXPOSURE_MEAN','SUB_WIN_MEAN','TD_PRESSURE_MEAN','TD_DEFENSE_MEAN','KD_DIRECTIONAL_MEAN','KD_DIRECTIONAL_ABS_DIFF','SUB_DIRECTIONAL_SUM','TD_ACCESS_DIRECTIONAL_SUM','scheduled_rounds','ctx__title_bout']
