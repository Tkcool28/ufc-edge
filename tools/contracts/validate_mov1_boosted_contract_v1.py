"""No estimator fitting: verify finite preregistration and exact outcome-blind matrices."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

ROOT=Path(__file__).resolve().parents[2]
DIRECTORY=ROOT/'models/challengers/mov1_boosted_v1'
sys.path.insert(0,str(ROOT/'models/mov1'))
from implementation_v1 import Preprocessor, finish_history, scope_identity, swap
from validate_mov1_contract_v1 import validate as validate_linear_inputs


def load(name):
    return json.loads((DIRECTORY/name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok,message):
    if not ok:
        raise ValueError(message)


class TreeInputRepresentation(Preprocessor):
    """Reuse frozen MIN imputation/transform semantics without fitting a scaler."""
    def __init__(self):
        super().__init__('MOV1_MIN')

    def fit(self,train):
        require(train.event_date.ge('2015-01-01').all(),'Pre2015 preprocessing')
        require(set(train.method)=={'KO_TKO','SUBMISSION'},'Decision/invalid preprocessing labels')
        self.identity=scope_identity(train)
        x=train[self.columns]
        self.medians={p['name']:self.median(x[p['columns']].to_numpy(float).ravel()) for p in self.pairs}
        self.round_median=self.median(x.scheduled_rounds)
        require(x.ctx__title_bout.dropna().isin([True,False,0,1]).all(),'Invalid title')
        self.title_mode=bool(self.mode(x.ctx__title_bout))
        self.division_mode=self.mode(self.divisions(x))
        _,_,division=self.unscaled(x)
        self.encoder=OneHotEncoder(handle_unknown='ignore',drop=None,sparse_output=False,dtype=np.float64).fit(division)
        self.names=load('common_input_representation.json')['numeric_names']+['ctx__title_bout']+['division='+c for c in self.encoder.categories_[0]]
        return self

    def transform(self,frame):
        numeric,title,division=self.unscaled(frame)
        output=np.ascontiguousarray(np.c_[numeric,title,self.encoder.transform(division)],dtype=np.float64)
        require(np.isfinite(output).all(),'Nonfinite matrix')
        return output


def validate(f02_path):
    import xgboost as xgb
    import lightgbm as lgb
    import catboost as cat
    # Enforce this tool's no-estimator-fit promise even through imported helpers.
    def forbidden(*args,**kwargs):
        raise AssertionError('Estimator fitting forbidden in contract validation')
    from sklearn.linear_model import LogisticRegression
    LogisticRegression.fit=forbidden
    xgb.train=lgb.train=forbidden
    xgb.XGBClassifier.fit=lgb.LGBMClassifier.fit=cat.CatBoostClassifier.fit=forbidden
    versions={k:importlib.metadata.version(k) for k in ['numpy','pandas','pyarrow','scipy','scikit-learn','xgboost','lightgbm','catboost']}
    for line in (DIRECTORY/'requirements.in').read_text().splitlines():
        key,version=line.split('==');require(versions[key]==version,'Dependency version drift '+key)
    require(platform.python_version()=='3.12.14','Python version drift')
    manifest=DIRECTORY/'CONTRACT_MANIFEST.json'
    if manifest.exists():
        for name,record in load('CONTRACT_MANIFEST.json')['files'].items():
            require(digest(ROOT/name)==record['sha256'],'Contract hash mismatch '+name)
    for name,expected in load('source_identities.json')['files'].items():
        require(digest(ROOT/name)==expected,'Frozen source mismatch '+name)
    baseline=load('authoritative_baseline_identity.json')
    require(digest(ROOT/'models/mov1/run_v1/EVIDENCE_MANIFEST.json')==baseline['evidence_manifest_sha256'],'Baseline evidence drift')
    # Reuse exact canonical-population, F02, chronology and foundation checks (no fit).
    evidence=validate_linear_inputs(f02_path)
    original=ROOT/'models/mov1/contracts/ko_vs_submission_given_finish_v1'
    for name in ['mov1_min_allowlist.json','chronological_fold_plan.json','target_population.json','conditional_probability_buckets.json','terrain_archetype_evaluation.json']:
        require((DIRECTORY/name).read_bytes()==(original/name).read_bytes(),'Frozen copy drift '+name)
    for name,record in json.loads((ROOT/'models/mov1/run_v1/EVIDENCE_MANIFEST.json').read_text())['files'].items():
        require(digest(ROOT/'models/mov1/run_v1'/name)==record['sha256'],'Baseline artifact drift '+name)
    registry=load('model_family_registry.json')['ordered_families'];counts=[]
    for family in registry:
        candidates=load(family['candidate_file']);require(len(candidates)==18,'Grid size')
        require(len({json.dumps(c['parameters'],sort_keys=True) for c in candidates})==18,'Duplicate grid')
        for c in candidates:
            p=c['parameters'];require(c['depth'] in [2,3,4] and c['learning_rate'] in [.02,.05,.1],'Envelope drift')
            if family['family']=='XGB':
                require(p['objective']=='binary:logistic' and p['device']=='cpu','XGB objective/device')
                require(xgb.XGBClassifier(**p).get_params()['objective']=='binary:logistic','XGB constructor')
            elif family['family']=='LGBM':
                require(p['objective']=='binary' and p['metric']=='binary_logloss' and p['deterministic'],'LGBM objective')
                require(lgb.LGBMClassifier(**p).get_params()['objective']=='binary','LGBM constructor')
            else:
                require(p['loss_function']=='Logloss' and 'cat_features' not in p and p['task_type']=='CPU','CAT objective/native encoding')
                require(cat.CatBoostClassifier(**p).get_params()['loss_function']=='Logloss','CAT constructor')
        counts.append(len(candidates))
    budget=load('search_budget.json');require(sum(counts)*2*9==budget['inner_fits']==972,'Fit calculation')
    require(972+27+9==budget['total_fits']==1008,'Total budget')
    source=load('target_population.json')['source_population_path']
    population=pd.read_csv(ROOT/source).sort_values(['event_date','event_id','fight_id']).reset_index(drop=True)
    f02=pd.read_parquet(f02_path).set_index('fight_id')
    columns=load('mov1_min_allowlist.json')['literal_f02_columns']
    frame=population[['fight_id','event_date','event_id','method']].merge(f02[columns],left_on='fight_id',right_index=True,validate='one_to_one')
    require(len(columns)==35 and len(frame)==5658,'Source population')
    matrix_records=[]
    for fold in load('chronological_fold_plan.json')['folds']:
        y=fold['outer_year'];histories=[('outer',y)]+[('inner',i['validation_year']) for i in fold['inner_folds']]
        for kind,year in histories:
            train=finish_history(frame,year)
            pp=TreeInputRepresentation().fit(train)
            swapped_pp=TreeInputRepresentation().fit(swap(train,'MOV1_MIN'))
            require(pp.medians==swapped_pp.medians,'Side-dependent median')
            score=frame[frame.event_date.str[:4].astype(int).eq(year)]
            if kind=='inner':score=score[score.method.isin(['KO_TKO','SUBMISSION'])]
            features=score[columns]
            X=pp.transform(features)
            require(np.array_equal(X,pp.transform(swap(features,'MOV1_MIN'))),'Matrix swap')
            changed=score.copy();changed['method']='DECISION'
            require(np.array_equal(X,pp.transform(changed)),'Outcome dependence')
            require(np.array_equal(X,pp.transform(features)),'Matrix regeneration')
            fixture=features.iloc[:2].copy();a,b=pp.pairs[0]['columns'];fixture.loc[fixture.index[0],a]=np.nan;fixture.loc[fixture.index[-1],b]=np.nan
            require(np.array_equal(pp.transform(fixture),pp.transform(swap(fixture,'MOV1_MIN'))),'Asymmetric null swap')
            numeric,title,division=pp.unscaled(features)
            require(np.array_equal(X[:,:numeric.shape[1]],numeric),'Unwanted numeric scaling')
            require(X.shape[1]==34+len(pp.encoder.categories_[0]),'Matrix size')
            matrix_records.append({'outer_year':y,'history':kind,'validation_year':year,'fit_identity':scope_identity(train),'scoring_N':len(score),'matrix_shape':list(X.shape),'matrix_sha256':hashlib.sha256(X.tobytes()).hexdigest()})
    require(sum(r['scoring_N'] for r in matrix_records if r['history']=='outer')==4260,'Missing outer rows')
    try:
        bad=finish_history(frame,2018).copy();bad.loc[bad.index[0],'method']='DECISION';TreeInputRepresentation().fit(bad)
    except ValueError:pass
    else:raise AssertionError('Decision accepted')
    return {'status':'CONTRACT_INPUT_VALIDATION_PASSED','model_fits':0,'boosted_predictions_generated':False,'versions':versions,'python':platform.python_version(),'platform':platform.platform(),'machine':platform.machine(),'upstream_validation':evidence,'common_matrix_records':matrix_records,'candidate_counts':counts,'total_future_fit_budget':1008,'binary_objectives':'Pinned package imports and unfitted constructor/parameter checks passed; required objectives documented by libraries. No training smoke test permitted. Fitted runtime compatibility must pass before later performance interpretation.','outcome_blind_features':True,'swap_and_asymmetric_null_matrix_checks':True,'all_outer_scoring_rows_representable':4260,'outer_conditional_rows':2115}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--f02-table',type=Path,required=True);parser.add_argument('--write-evidence',type=Path)
    args=parser.parse_args();result=validate(args.f02_table)
    if args.write_evidence:args.write_evidence.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['upstream_validation','common_matrix_records']},indent=2))
