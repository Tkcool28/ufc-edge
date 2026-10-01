"""Frozen conditional finish-method experiment V1. No MOV0 fitting or changes."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow
import scipy
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_info, threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'models/mov1/contracts/ko_vs_submission_given_finish_v1'
START = 'b6a644d9ef8d267f7d7da97f21e691f2bae99226'
CONTRACT_SHA = '9034e647bebaa7099f5358ed7a5db0e1bc515df1894db912274e5dae629cb714'
SURFACES = ['C0', 'C1', 'MOV1_MIN', 'MOV1_FULL']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spec(name):
    return json.loads((CONTRACT / name).read_text())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def write_csv(path, frame):
    frame.to_csv(path, index=False, float_format='%.17g', lineterminator='\n')


def id_sha(frame):
    return hashlib.sha256(''.join(frame.fight_id.astype(str) + '\n').encode()).hexdigest()


def scope_identity(frame):
    return {'N': len(frame), **{m: int(frame.method.eq(m).sum())
            for m in ['KO_TKO', 'SUBMISSION', 'DECISION']},
            'ordered_fight_id_sha256': id_sha(frame)}


def finish_history(frame, year):
    x = frame[frame.event_date.ge('2015-01-01') & frame.event_date.lt(f'{year}-01-01')
              & frame.method.isin(['KO_TKO', 'SUBMISSION'])].copy()
    require(len(x) > 0 and set(x.method) == {'KO_TKO', 'SUBMISSION'}, 'Invalid fit labels')
    return x


def binary_loss(y, p):
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, int)
    return -(y * np.log(p) + (1-y) * np.log1p(-p))


class Preprocessor:
    """Fit only on a caller-verified finish history; prediction consumes allowlist only."""
    def __init__(self, surface):
        self.surface = surface
        self.columns = spec(surface.lower() + '_allowlist.json')['literal_f02_columns']
        self.pairs = [p for p in spec('fighter_order_transformation.json')['pairs']
                      if set(p['columns']) <= set(self.columns)]
        self.mapping = json.loads((ROOT / spec('missingness_preprocessing.json')
                                  ['weight_class']['literal_map_path']).read_text())['literal_map']

    @staticmethod
    def median(values):
        values = np.asarray(values, float)
        require(not np.isinf(values).any(), 'Infinite input')
        finite = values[np.isfinite(values)]
        require(len(finite) > 0, 'No finite imputation history')
        return float(np.median(finite))

    @staticmethod
    def mode(values):
        counts = pd.Series(values).dropna().value_counts()
        require(len(counts) > 0, 'No observed categorical history')
        return sorted(counts[counts.eq(counts.max())].index.tolist())[0]

    def divisions(self, x):
        raw = x.ctx__weight_class
        require(raw.dropna().isin(self.mapping).all(), 'Unknown raw division')
        return raw.map(self.mapping)

    def fit(self, train):
        require(train.event_date.ge('2015-01-01').all(), 'Pre-2015 fit row')
        require(set(train.method) == {'KO_TKO','SUBMISSION'}, 'Decision or invalid label in preprocessing')
        self.identity = scope_identity(train)
        x = train[self.columns]
        self.medians = {p['name']: self.median(x[p['columns']].to_numpy(float).ravel())
                        for p in self.pairs}
        self.round_median = self.median(x.scheduled_rounds)
        require(x.ctx__title_bout.dropna().isin([True,False,0,1]).all(), 'Invalid title context')
        self.title_mode = bool(self.mode(x.ctx__title_bout))
        self.division_mode = self.mode(self.divisions(x))
        numeric, title, division = self.unscaled(x)
        self.scaler = StandardScaler(with_mean=True, with_std=True).fit(numeric)
        self.encoder = OneHotEncoder(handle_unknown='ignore', drop=None,
                                     sparse_output=False, dtype=np.float64).fit(division)
        self.numeric_names = [p['name'] + '::' + transform for p in self.pairs
                              for transform in ['mean','absolute_difference']] + ['scheduled_rounds']
        self.names = self.numeric_names + ['ctx__title_bout'] + [
            'division=' + c for c in self.encoder.categories_[0]]
        expected = spec('fighter_order_transformation.json')['model_dimensions_before_one_hot'][self.surface]
        require(len(self.numeric_names) + 1 == expected, 'Transformed dimensionality mismatch')
        return self

    def unscaled(self, frame):
        x = frame[self.columns]
        arrays = []
        for pair in self.pairs:
            v = x[pair['columns']].to_numpy(float)
            require(not np.isinf(v).any(), 'Infinite numeric input')
            v = np.where(np.isnan(v), self.medians[pair['name']], v)
            arrays.extend([(v[:,0]+v[:,1])/2, np.abs(v[:,0]-v[:,1])])
        rounds = x.scheduled_rounds.to_numpy(float)
        require(not np.isinf(rounds).any(), 'Infinite rounds')
        arrays.append(np.where(np.isnan(rounds), self.round_median, rounds))
        require(x.ctx__title_bout.dropna().isin([True,False,0,1]).all(), 'Invalid title')
        title = x.ctx__title_bout.fillna(self.title_mode).to_numpy(float).reshape(-1,1)
        division = self.divisions(x).fillna(self.division_mode).to_numpy().reshape(-1,1)
        return np.column_stack(arrays).astype(np.float64), title, division

    def transform(self, frame):
        numeric, title, division = self.unscaled(frame)
        out = np.c_[self.scaler.transform(numeric), title, self.encoder.transform(division)]
        require(np.isfinite(out).all(), 'Invalid transformed input')
        return out

    def record(self):
        return {'surface':self.surface,'fit_identity':self.identity,'literal_columns':self.columns,
                'pooled_pair_medians':self.medians,'rounds_median':self.round_median,
                'title_mode':self.title_mode,'division_mode':self.division_mode,
                'division_categories':self.encoder.categories_[0].tolist(),
                'numeric_names':self.numeric_names,'feature_names':self.names,
                'scaler_mean':self.scaler.mean_.tolist(),'scaler_var':self.scaler.var_.tolist(),
                'scaler_scale':self.scaler.scale_.tolist(),'scaler_n_samples':int(self.scaler.n_samples_seen_)}

    @classmethod
    def restore(cls, record):
        obj = cls(record['surface'])
        obj.identity = record['fit_identity']
        obj.medians = record['pooled_pair_medians']
        obj.round_median = record['rounds_median']
        obj.title_mode = record['title_mode']
        obj.division_mode = record['division_mode']
        obj.numeric_names = record['numeric_names']
        obj.names = record['feature_names']
        obj.scaler = StandardScaler(with_mean=True,with_std=True)
        obj.scaler.mean_ = np.array(record['scaler_mean'],float)
        obj.scaler.var_ = np.array(record['scaler_var'],float)
        obj.scaler.scale_ = np.array(record['scaler_scale'],float)
        obj.scaler.n_samples_seen_ = record['scaler_n_samples']
        obj.scaler.n_features_in_ = len(obj.scaler.mean_)
        # Encoder fit on persisted categories only; no incoming scoring row influences it.
        obj.encoder = OneHotEncoder(handle_unknown='ignore',drop=None,sparse_output=False,dtype=np.float64)
        obj.encoder.fit(np.array(record['division_categories'],object).reshape(-1,1))
        return obj


def swap(frame, surface):
    x = frame.copy()
    columns = spec(surface.lower() + '_allowlist.json')['literal_f02_columns']
    for pair in spec('fighter_order_transformation.json')['pairs']:
        a,b = pair['columns']
        if a in columns:
            x[a],x[b] = frame[b].copy(),frame[a].copy()
    return x


def estimator(C):
    settings = spec('model_regularization.json')
    return LogisticRegression(C=C,penalty=settings['penalty'],solver=settings['solver'],
                              fit_intercept=settings['fit_intercept'],max_iter=settings['max_iter'],
                              tol=settings['tol'],class_weight=settings['class_weight'],
                              random_state=settings['random_state'])


def fitted(train, surface, C):
    require(set(train.method)=={'KO_TKO','SUBMISSION'}, 'Decision in estimator fit')
    pp = Preprocessor(surface).fit(train)
    X = pp.transform(train)
    y = train.method.eq('KO_TKO').to_numpy(int)
    model = estimator(C)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model.fit(X,y)
    require(not any(issubclass(w.category,ConvergenceWarning) for w in caught), 'Solver nonconvergence')
    require(int(model.n_iter_[0]) < 3000, 'Iteration cap reached')
    require(np.isfinite(model.coef_).all() and np.isfinite(model.intercept_).all(), 'Nonfinite fit')
    return pp,model,{'n_iter':int(model.n_iter_[0]),'warnings':[str(w.message) for w in caught],
                    'converged':True,'C':C}


def select_candidate(losses):
    best=losses[0]
    for value in losses[1:]:
        if value['inner_log_loss']<best['inner_log_loss']-1e-12:best=value
    return best


def probability(pp, model, rows):
    p = model.predict_proba(pp.transform(rows))[:,1]
    require(np.isfinite(p).all() and ((p>=0)&(p<=1)).all(), 'Invalid probability')
    return p


def runtime_prediction_checks(pp, model, rows):
    p = probability(pp,model,rows)
    swapped = probability(pp,model,swap(rows,pp.surface))
    error = float(np.max(np.abs(p-swapped)))
    require(error<=1e-12, 'Fighter swap failed')
    # Score has no outcome gate and accepts only literal predictor columns.
    features = rows[pp.columns].copy()
    require(np.array_equal(p,probability(pp,model,features)), 'Labels/IDs affect prediction')
    changed = rows.copy()
    changed['method'] = 'DECISION'
    changed['target'] = 999
    require(np.array_equal(p,probability(pp,model,changed)), 'Changed outcomes affect scoring')
    fixture = features.iloc[:min(4,len(features))].copy()
    for pair in pp.pairs:
        fixture.loc[fixture.index[0],pair['columns'][0]] = np.nan
        if len(fixture)>1:
            fixture.loc[fixture.index[1],pair['columns'][1]] = np.nan
    fixture_error=float(np.max(abs(probability(pp,model,fixture)-probability(pp,model,swap(fixture,pp.surface)))))
    require(fixture_error<=1e-12, 'Asymmetric missingness swap failed')
    # A known canonical division absent from fitted encoder must be all zero.
    absent = sorted(set(pp.mapping.values())-set(pp.encoder.categories_[0]))
    require(len(absent)>0, 'No unseen-category fixture available')
    raw = sorted(k for k,v in pp.mapping.items() if v==absent[0])[0]
    unseen=features.iloc[:1].copy();unseen['ctx__weight_class']=raw
    require(np.array_equal(pp.transform(unseen)[0,-len(pp.encoder.categories_[0]):],np.zeros(len(pp.encoder.categories_[0]))), 'Unseen division encoding failed')
    return p,{'N':len(rows),'max_swap_error':error,'asymmetric_null_swap_error':fixture_error,
              'labels_removed_and_changed_identical':True,'known_unseen_category_all_zero':True}


def environment():
    actual = {'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
              'pyarrow':pyarrow.__version__,'scikit-learn':sklearn.__version__,'scipy':scipy.__version__}
    for name,expected in spec('model_regularization.json')['dependency_lock'].items():
        require(actual[name].startswith(expected+'.') if name=='python' else actual[name]==expected,
                f'Dependency mismatch {name}: {actual[name]} expected {expected}')
    return {'versions':actual,'platform':platform.platform(),'threads':1,'threadpools':threadpool_info(),
            'cross_platform_bitwise_identity_claimed':False,'prediction_regeneration_atol':1e-12,'rtol':0}


def verify_inputs(f02_path, mov0_path):
    require(sha(CONTRACT/'CONTRACT_MANIFEST.json')==CONTRACT_SHA,'Contract manifest identity mismatch')
    module_path=ROOT/'tools/contracts/validate_mov1_contract_v1.py'
    s=importlib.util.spec_from_file_location('frozen_mov1_contract_validator',module_path)
    validator=importlib.util.module_from_spec(s);s.loader.exec_module(validator)
    evidence=validator.validate(Path(f02_path))
    require(sha(mov0_path)==spec('three_way_composition.json')['MOV0_MIN_OOF_sha256'],'MOV0 MIN identity mismatch')
    mov0=pd.read_csv(mov0_path,float_precision='round_trip')
    require(len(mov0)==4260 and not mov0.fight_id.duplicated().any(),'Frozen MOV0 coverage')
    require(mov0.surface.eq('MOV0_MIN').all(),'Wrong MOV0 surface')
    population=pd.read_csv(ROOT/spec('target_population.json')['source_population_path'])
    population=population.sort_values(['event_date','event_id','fight_id']).reset_index(drop=True)
    f02=pd.read_parquet(f02_path)
    cols=spec('mov1_full_allowlist.json')['literal_f02_columns']
    # Outcome-independent states and references are kept separate until metric reporting.
    states=f02[['fight_id']+cols]
    frame=population[['fight_id','event_id','event_date','method']].merge(states,on='fight_id',validate='one_to_one')
    require(frame.fight_id.tolist()==population.fight_id.tolist(),'Join reordered rows')
    frame['outer_year']=frame.event_date.str[:4].astype(int)
    outer=frame[frame.outer_year.ge(2018)]
    require(set(outer.fight_id)==set(mov0.fight_id),'MOV0 scoring membership differs')
    check=outer.merge(mov0,on='fight_id',validate='one_to_one',suffixes=('','_mov0'))
    require(check.outer_year.eq(check.year).all() and check.event_date.eq(check.event_date_mov0).all()
            and check.event_id.eq(check.event_id_mov0).all(),'MOV0 chronology mismatch')
    require(check.method.ne('DECISION').astype(int).eq(check.target).all(),'MOV0 labels mismatch')
    require(np.isfinite(mov0.probability).all() and mov0.probability.between(0,1).all(),'Invalid frozen F')
    return frame,population,mov0,evidence


def run_training(f02_path, mov0_path, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    frame,population,mov0,input_evidence=verify_inputs(f02_path,mov0_path)
    with threadpool_limits(limits=1):
        env=environment()
        predictions=[];audits=[];runtime=[];coefs=[];selected=[]
        models=output/'MODELS';models.mkdir(exist_ok=True)
        for fold in spec('chronological_fold_plan.json')['folds']:
            year=fold['outer_year'];train=finish_history(frame,year)
            score=frame[frame.outer_year.eq(year)].copy()
            require(scope_identity(train)==fold['training'],'Outer training ID mismatch')
            require(scope_identity(score)==fold['all_eligible_scoring'],'Scoring ID mismatch')
            require(scope_identity(score[score.method.ne('DECISION')])==fold['conditional_validation'],'Conditional ID mismatch')
            c0=float(train.method.eq('KO_TKO').mean())
            write_json(models/f'{year}_C0.json',{'outer_year':year,'surface':'C0','P_KO_given_finish':c0,'fit_identity':scope_identity(train)})
            preds={'C0':(np.full(len(score),c0),None)}
            for surface in SURFACES[1:]:
                losses=[]
                for C in spec('model_regularization.json')['C_grid']:
                    all_losses=[]
                    for inner in fold['inner_folds']:
                        iy=inner['validation_year'];it=finish_history(frame,iy)
                        iv=frame[frame.outer_year.eq(iy)&frame.method.ne('DECISION')]
                        require(scope_identity(it)==inner['training'] and scope_identity(iv)==inner['validation'],'Inner membership mismatch')
                        pp,model,conv=fitted(it,surface,C)
                        p,checks=runtime_prediction_checks(pp,model,iv)
                        all_losses.extend(binary_loss(iv.method.eq('KO_TKO'),p))
                        audits.append({'stage':'inner','outer_year':year,'inner_year':iy,'surface':surface,'C':C,
                                       'preprocessing':pp.record(),'validation_identity':scope_identity(iv),'solver':conv})
                        runtime.append({'stage':'inner','outer_year':year,'inner_year':iy,'surface':surface,'C':C,**checks})
                    losses.append({'C':C,'inner_log_loss':float(np.mean(all_losses)),'N':len(all_losses)})
                best=select_candidate(losses)
                pp,model,conv=fitted(train,surface,best['C'])
                p,checks=runtime_prediction_checks(pp,model,score)
                record={'outer_year':year,'surface':surface,'C':best['C'],'preprocessing':pp.record(),
                        'coef':model.coef_.tolist(),'intercept':model.intercept_.tolist(),'classes':model.classes_.tolist(),'solver':conv}
                write_json(models/f'{year}_{surface}.json',record)
                restored_pp,restored_model=restore_model(record)
                restored_p=probability(restored_pp,restored_model,score)
                regen_error=float(np.max(abs(p-restored_p)))
                require(regen_error<=1e-12,'Saved-model prediction regeneration failed')
                runtime.append({'stage':'outer','outer_year':year,'surface':surface,'C':best['C'],
                                'saved_regeneration_error':regen_error,**checks})
                audits.append({'stage':'outer','outer_year':year,'surface':surface,'C':best['C'],
                               'preprocessing':pp.record(),'scoring_identity':scope_identity(score),'solver':conv,'grid':losses})
                selected.append({'outer_year':year,'surface':surface,'selected_C':best['C'],'inner_log_loss':best['inner_log_loss']})
                for name,coef in zip(pp.names,model.coef_[0]):
                    coefs.append({'outer_year':year,'surface':surface,'feature':name,'coefficient':float(coef),
                                  'scale':'standardized numeric; unscaled title/one-hot','sign':int(np.sign(coef))})
                coefs.append({'outer_year':year,'surface':surface,'feature':'intercept','coefficient':float(model.intercept_[0]),'scale':'intercept','sign':int(np.sign(model.intercept_[0]))})
                preds[surface]=(p,best['C'])
            for surface in SURFACES:
                p,C=preds[surface]
                x=score[['fight_id','event_id','event_date','outer_year']].copy()
                x['surface']=surface;x['P_KO_given_finish']=p;x['P_SUB_given_finish']=1-p
                x['selected_C']=C;x['train_finish_N']=len(train);predictions.append(x)
            print(f'Completed outer {year}: fitted and scored {len(score)} bouts; gates pass',flush=True)
        all_scores=pd.concat(predictions,ignore_index=True)
        all_scores['surface']=pd.Categorical(all_scores.surface,categories=SURFACES,ordered=True)
        all_scores=all_scores.sort_values(['event_date','event_id','fight_id','surface']).reset_index(drop=True)
        require(len(all_scores)==17040 and not all_scores.duplicated(['fight_id','surface']).any(),'Incomplete score file')
        write_csv(output/'conditional_oof_all_eligible.csv',all_scores)
        # Persist before any label join for conditional/composed evaluation.
        for surface in SURFACES:write_csv(output/f'oof_{surface}.csv',all_scores[all_scores.surface.eq(surface)])
        roundtrip=pd.read_csv(output/'conditional_oof_all_eligible.csv',float_precision='round_trip')
        representative_year=2021;surface='MOV1_MIN'
        original=all_scores[all_scores.outer_year.eq(representative_year)&all_scores.surface.eq(surface)]
        C=float(original.selected_C.iloc[0]);pp,model,_=fitted(finish_history(frame,representative_year),surface,C)
        score=frame[frame.outer_year.eq(representative_year)]
        again=probability(pp,model,score)
        original=original.set_index('fight_id').loc[score.fight_id]
        rerun_error=float(np.max(abs(again-original.P_KO_given_finish.to_numpy())))
        require(rerun_error<=1e-12,'Representative deterministic rerun failed')
        persisted_error=0.
        for year in range(2018,2027):
            score=frame[frame.outer_year.eq(year)]
            for surface in SURFACES:
                r=json.loads((models/f'{year}_{surface}.json').read_text())
                p=np.full(len(score),r['P_KO_given_finish']) if surface=='C0' else probability(*restore_model(r),score)
                saved=roundtrip[roundtrip.outer_year.eq(year)&roundtrip.surface.eq(surface)].set_index('fight_id').loc[score.fight_id]
                error=float(np.max(abs(p-saved.P_KO_given_finish.to_numpy())))
                persisted_error=max(persisted_error,error)
                require(error<=1e-12,'Persisted prediction regeneration failed')
        write_json(output/'ENVIRONMENT_LOCK.json',env)
        write_json(output/'INPUT_VALIDATION.json',input_evidence)
        write_json(output/'TRAINING_AUDIT.json',audits)
        write_csv(output/'selected_C_by_surface_year.csv',pd.DataFrame(selected))
        write_csv(output/'coefficient_by_year.csv',pd.DataFrame(coefs))
        validation={'status':'ALL_IMPLEMENTATION_GATES_PASSED','fit_records':len(audits),
                    'inner_models':216,'outer_models':27,'C0_models':9,'model_checks':runtime,
                    'representative_rerun':{'surface':'MOV1_MIN','year':2021,'max_probability_error':rerun_error,'identical_float64':rerun_error==0},
                    'persisted_predictions_regenerated_max_error':persisted_error,
                    'all17040_score_rows_regenerated':True,'scoring_before_outcome_join':True,
                    'no_decision_fit_rows':True,'no_pre2015_fit_rows':True,'unexpected_dropped_rows':0,
                    'max_swap_error':max(r['max_swap_error'] for r in runtime),
                    'interpretation_permitted_only_after_composition_and_regeneration_gates':True}
        write_json(output/'RUNTIME_VALIDATION.json',validation)
    return frame,population,mov0,all_scores


def restore_model(record):
    pp=Preprocessor.restore(record['preprocessing'])
    model=estimator(record['C']);model.coef_=np.asarray(record['coef'],float)
    model.intercept_=np.asarray(record['intercept'],float);model.classes_=np.asarray(record['classes'],int)
    model.n_features_in_=len(pp.names)
    return pp,model
