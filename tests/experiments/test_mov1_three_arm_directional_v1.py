"""Outcome-free pre-fit tests; no call to a predictive estimator fit."""
import importlib.util,json,pathlib,sys
import numpy as np
import pandas as pd
import pytest
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'models/challengers/mov1_three_arm_directional_run_v1'))
from implementation import Preprocessor,predict_record,select_candidate,spec,FitLedger,completeness
from reporting import paired_draws,classify,pathway_status,preservation_status

def fixture():
    rng=np.random.default_rng(17);cols=spec('feature_specifications.json')['arms']['B']['raw_columns'];x=pd.DataFrame({c:rng.uniform(.1,.9,100) for c in cols if c not in ['ctx__weight_class','ctx__title_bout','scheduled_rounds']});x['ctx__weight_class']='Lightweight';x['ctx__title_bout']=np.arange(100)%2;x['scheduled_rounds']=np.where(np.arange(100)%3,3,5);return x

def fake_record(arm,x):
    pp=Preprocessor(arm).freeze(x);co=np.arange(pp.transform(x).shape[1])/100
    return {'preprocessing':pp.record(),'coef':co.tolist(),'intercept':.1},pp

def test_source_order_dimensions_and_restoration():
    x=fixture()
    for arm,expected in [('B',36),('C',16)]:
        rec,pp=fake_record(arm,x);assert pp.transform(x).shape[1]==expected
        restored=Preprocessor.restore(rec['preprocessing']);assert np.array_equal(restored.transform(x),pp.transform(x))
        assert np.array_equal(predict_record(rec,x),predict_record(rec,x))

def test_feature_and_fake_probability_swap_labelblind():
    x=fixture()
    for arm in ['B','C']:
        rec,pp=fake_record(arm,x);x2=x.copy();x2['winner_id']='NO';x2['method']='anything'
        assert np.array_equal(predict_record(rec,x),predict_record(rec,x2))
        assert np.allclose(predict_record(rec,x),predict_record(rec,pp.swap(x)),atol=1e-12,rtol=0)
        for a,b in pp.pairs:x2.loc[0,a]=np.nan;x2.loc[1,[a,b]]=np.nan
        assert np.allclose(predict_record(rec,x2),predict_record(rec,pp.swap(x2)),atol=1e-12,rtol=0)

def test_regularization_tie_rule():
    assert select_candidate([{'C':.03,'inner_log_loss':.5},{'C':.1,'inner_log_loss':.5-5e-13}])['C']==.03
    assert select_candidate([{'C':.03,'inner_log_loss':.5},{'C':.1,'inner_log_loss':.49}])['C']==.1

def test_shared_source_imputation_and_null_preservation():
    x=fixture();x.iloc[0,3]=np.nan;copy=x.copy(deep=True)
    b=Preprocessor('B').freeze(x);c=Preprocessor('C').freeze(x)
    for pair,median in c.medians.items():assert b.medians[pair]==median
    assert x.equals(copy)
    source=spec('feature_specifications.json')['source_concepts']['TD_DEFENSE']['columns'];assert all((x[col]>=0).all() and (x[col]<=1).all() for col in source)
    assert np.array_equal(b.unscaled(x)[:,33],c.unscaled(x)[:,11])

def test_bootstrap_exact_shared_draws_against_scalar():
    frame=pd.DataFrame({'event_id':['z','a','z','b'],'outer_year':[2018]*4});loss=np.arange(24,dtype=float).reshape(4,3,2)/10
    drawn,hashes=paired_draws(frame,loss,reps=20)
    for kind in ['fight','event']:
        rng=np.random.default_rng(17);expected=[]
        groups=[np.flatnonzero(frame.event_id.to_numpy()==e) for e in sorted(frame.event_id.unique())]
        for k in range(20):
            ix=rng.integers(0,4,4) if kind=='fight' else np.concatenate([groups[j] for j in rng.choice(len(groups),len(groups),replace=True)])
            avg=loss[ix].mean(axis=0);expected.append(np.stack([avg[2]-avg[0],avg[1]-avg[0],avg[2]-avg[1]]))
        assert np.allclose(drawn[kind],expected,atol=1e-12,rtol=0)

def test_classification_fixed_gates():
    c={'delta':{'log_loss':-.01,'brier':-.002},'paired_intervals':{kind:{'log_loss':[-.02,-.001],'brier':[-.004,.001]} for kind in ['fight','event']},'favorable_years':6,'median_annual_delta':-.01,'leave_one_year_out_LL':{'2018':-.01}}
    assert classify(c)=='SUPPORTED_IMPROVEMENT';c['favorable_years']=5;assert classify(c)=='INCONCLUSIVE'
    c['delta']['log_loss']=.01
    for iv in c['paired_intervals'].values():iv['log_loss']=[.001,.02]
    assert classify(c)=='CURRENT_SPECIFICATION_NOT_SUPPORTED'

def test_absolute_fit_ledger_cap(tmp_path):
    ledger=FitLedger(tmp_path)
    for i in range(164):ledger.begin({'phase':'TEST'});ledger.finish({})
    with pytest.raises(ValueError,match='budget'):ledger.begin({'phase':'TEST'})

def test_missingness_not_zero_and_train_score_isolation():
    x=fixture();pp=Preprocessor('C').freeze(x);rec=pp.record();z=x.copy();z.iloc[0,0]=1e12;pp.transform(z);assert pp.record()==rec
    pair=pp.pairs[0];x[list(pair)]=np.nan
    with pytest.raises(ValueError,match='All missing'):Preprocessor('C').freeze(x)

def test_complete_probability_identity():
    x=fixture();F=np.linspace(0,1,100)
    for arm in ['B','C']:
        rec,_=fake_record(arm,x);K=predict_record(rec,x);p=np.c_[F*K,F*(1-K),1-F]
        assert np.allclose(p.sum(axis=1),1,atol=1e-12,rtol=0);assert np.array_equal(p[:,2],1-F)

def test_reporting_cell_is_json_serializable():
    from reporting import cell_records
    n=100;x=pd.DataFrame({'method':['KO_TKO','SUBMISSION']*50,'outer_year':[2021]*n,'division':['Lightweight']*n,'sub_complete':[True]*n,'compact_complete':[False]*n,'F':np.full(n,.5)})
    for arm in ['A','B','C']:
        x['K_'+arm]=np.linspace(.1,.9,n);x['KO_'+arm]=x.F*x['K_'+arm];x['SUB_'+arm]=x.F*(1-x['K_'+arm]);x['DEC_'+arm]=1-x.F
    rows=cell_records(x,'synthetic','FAKE');json.dumps(rows,sort_keys=True,allow_nan=False)
    assert len(rows)==3 and all(r['finish_N']==100 for r in rows)

def test_native_packaging_and_table_recovery(tmp_path):
    from implementation import write_json
    from verification import package,package_tables,restore_tables
    (tmp_path/'MODELS').mkdir();write_json(tmp_path/'MODELS/fake.json',{'arbitrary':'outcome-free record'})
    package(tmp_path);info=json.loads((tmp_path/'NATIVE_MODELS_MANIFEST.json').read_text());assert list(info['members'])==['MODELS/fake.json']
    f=tmp_path/'synthetic_table.csv';text='x,y\n'+'abc,123\n'*5000;f.write_text(text);package_tables(tmp_path);f.unlink();restore_tables(tmp_path);assert f.read_text()==text
