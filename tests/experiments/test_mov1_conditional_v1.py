"""Independent guardrail tests; synthetic fixtures do not evaluate historical MOV1."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import log_loss

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'models/mov1'))
from implementation_v1 import (Preprocessor, fitted, probability, restore_model,
                               runtime_prediction_checks, select_candidate, spec, swap)
from evaluation_v1 import binary_metrics, calibration, multiclass_losses, multiclass_metrics


def fixture(surface='MOV1_FULL'):
    x=pd.DataFrame({c:np.linspace(.1,1.2,12) for c in spec(surface.lower()+'_allowlist.json')['literal_f02_columns']})
    x['ctx__weight_class']=['Lightweight','Interim Lightweight']*6
    x['ctx__title_bout']=[False,True]*6
    x['scheduled_rounds']=[3,5]*6
    x['event_date']='2015-06-01';x['event_id']='event';x['fight_id']=[str(i) for i in range(12)]
    x['method']=['KO_TKO','SUBMISSION']*6
    return x


def test_pooled_imputation_independent_of_side_and_scoring_history():
    x=fixture('C1');a,b=spec('c1_allowlist.json')['literal_f02_columns'][-2:]
    x[a]=[0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,np.nan]
    x[b]=[100.,101.,102.,103.,104.,105.,106.,107.,108.,109.,110.,111.]
    p=Preprocessor('C1').fit(x)
    expected=float(np.median(np.r_[x[a].dropna(),x[b].dropna()]))
    assert p.medians['fs__prior_fight_count__career__raw']==expected
    pp=Preprocessor('C1').fit(swap(x,'C1'))
    assert p.record()==pp.record()
    unseen=x.iloc[:1].copy();unseen[a]=np.nan;unseen[b]=1e9
    median_before=p.medians.copy();transformed=p.unscaled(unseen)[0]
    assert transformed[0,0]==(expected+1e9)/2
    assert transformed[0,1]==abs(expected-1e9)
    assert p.medians==median_before


def test_decisions_pre2015_and_allmissing_are_rejected():
    x=fixture()
    for bad in ['DECISION','DQ']:
        changed=x.copy();changed.loc[0,'method']=bad
        with pytest.raises(ValueError):Preprocessor('MOV1_FULL').fit(changed)
    changed=x.copy();changed['event_date']='2014-12-31'
    with pytest.raises(ValueError):Preprocessor('MOV1_FULL').fit(changed)
    changed=x.copy()
    for c in spec('c1_allowlist.json')['literal_f02_columns'][-2:]:changed[c]=np.nan
    with pytest.raises(ValueError):Preprocessor('MOV1_FULL').fit(changed)


def test_fitted_swap_label_blindness_and_saved_regeneration():
    x=fixture();x.loc[0,spec('mov1_full_allowlist.json')['literal_f02_columns'][3]]=np.nan
    pp,m,conv=fitted(x,'MOV1_FULL',.03)
    p,checks=runtime_prediction_checks(pp,m,x)
    assert checks['max_swap_error']<=1e-12 and checks['labels_removed_and_changed_identical']
    record={'preprocessing':pp.record(),'C':.03,'coef':m.coef_.tolist(),'intercept':m.intercept_.tolist(),'classes':m.classes_.tolist()}
    rp,rm=restore_model(record)
    np.testing.assert_allclose(probability(rp,rm,x),p,atol=1e-12,rtol=0)
    unseen=x.iloc[:1].copy();unseen['ctx__weight_class']='Flyweight'
    assert np.array_equal(pp.transform(unseen)[0,-1:],np.zeros(1))
    unknown=x.iloc[:1].copy();unknown['ctx__weight_class']='not-a-governed-label'
    with pytest.raises(ValueError):pp.transform(unknown)
    assert conv['converged']


def test_frozen_grid_tie_break():
    grid=[{'C':.03,'inner_log_loss':.5},{'C':.1,'inner_log_loss':.5-5e-13},
          {'C':.3,'inner_log_loss':.5},{'C':1.,'inner_log_loss':.6}]
    assert select_candidate(grid)['C']==.03
    grid[2]['inner_log_loss']=.49
    assert select_candidate(grid)['C']==.3


def test_metrics_and_three_way_identity_against_independent_formula():
    methods=np.array(['KO_TKO','SUBMISSION','DECISION','KO_TKO'])
    F=np.array([.4,.7,.3,.8]);a=np.array([.2,.3,.4,.5]);b=np.array([.5,.6,.7,.8])
    pa=np.c_[F*a,F*(1-a),1-F];pb=np.c_[F*b,F*(1-b),1-F]
    np.testing.assert_allclose(pa.sum(axis=1),1,atol=1e-12,rtol=0)
    idx=np.array([0,1,2,0]);ya=np.eye(3)[idx]
    result=multiclass_metrics(methods,pa)
    assert abs(result['log_loss']-log_loss(idx,pa,labels=[0,1,2]))<1e-12
    assert abs(result['brier']-np.mean(np.sum((pa-ya)**2,axis=1)))<1e-12
    finish=methods!='DECISION';y=(methods[finish]=='KO_TKO').astype(int)
    expected=np.zeros(4)
    expected[finish]=-(y*np.log(a[finish])+(1-y)*np.log(1-a[finish]))+(y*np.log(b[finish])+(1-y)*np.log(1-b[finish]))
    np.testing.assert_allclose(multiclass_losses(methods,pa)-multiclass_losses(methods,pb),expected,atol=1e-12,rtol=0)
    m=binary_metrics(y,a[finish]);assert abs(m['log_loss']-log_loss(y,a[finish]))<1e-12
    assert calibration([0,1],[.5,.5])['status']=='CONSTANT_PREDICTION'
    assert calibration([1,1],[.2,.7])['status']=='ONE_CLASS'
