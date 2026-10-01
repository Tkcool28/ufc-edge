"""Execution of merged MOV1 boosting contract. No scientific fallback or extra fits."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
import time
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
import catboost as cat
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_info, threadpool_limits

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools/contracts'),str(ROOT/'models/mov1')]
from validate_mov1_boosted_contract_v1 import TreeInputRepresentation, load
from implementation_v1 import (finish_history, scope_identity, swap, sha, binary_loss,
                                require, write_json, write_csv)
import evaluation_v1 as ev
DIRECTORY=ROOT/'models/challengers/mov1_boosted_v1'
CONTRACT_SHA='4593dc0056455356ea9e28191acd2fda109124ca9e18ccb07c09319e99a2849b'
START='4ec01227a4a35872eed51ce7ce67c45b02e46ebd'
SURFACES=['MOV1-BOOST-SELECT','MOV1-XGB','MOV1-LGBM','MOV1-CAT','MOV1_MIN']
SYSTEMS=['SB','SB-XGB','SB-LGBM','SB-CAT','S2']

class StopState:
    def __init__(self):
        self.trace=[];self.best=float('inf');self.rounds=0
    def update(self,value):
        value=float(value);require(math.isfinite(value),'Nonfinite stopping metric')
        self.trace.append(value)
        if value<self.best-1e-12:self.best=value;self.rounds=len(self.trace)
        return len(self.trace)-self.rounds>=100

class XStop(xgb.callback.TrainingCallback):
    def __init__(self,state):self.state=state
    def after_iteration(self,model,epoch,evals_log):
        require(list(evals_log)==['validation'],'Unexpected XGB stopping dataset')
        return self.state.update(evals_log['validation']['logloss'][-1])

class LStop:
    order=30;before_iteration=False
    def __init__(self,state):self.state=state
    def __call__(self,env):
        require(len(env.evaluation_result_list)==1,'Unexpected LGB stopping metric')
        name,metric,value,*_=env.evaluation_result_list[0]
        require(name=='validation' and metric=='binary_logloss','Wrong LGB stopping metric')
        if self.state.update(value):
            raise lgb.callback.EarlyStopException(self.state.rounds-1,[(name,metric,self.state.best,False)])

class CStop:
    def __init__(self,state):self.state=state
    def after_iteration(self,info):
        return not self.state.update(info.metrics['validation']['Logloss'][-1])


def choose(records):
    minimum=min(r['inner_log_loss'] for r in records)
    return next(r for r in records if r['inner_log_loss']<=minimum+1e-12)


def refit_rounds(records):
    return min(2000,max(1,int(math.floor(sum(r['best_rounds']*r['N'] for r in records)/sum(r['N'] for r in records)+.5))))


def pp_record(pp):
    return {'fit_identity':pp.identity,'literal_columns':pp.columns,'pooled_pair_medians':pp.medians,
            'rounds_median':pp.round_median,'title_mode':pp.title_mode,'division_mode':pp.division_mode,
            'division_categories':pp.encoder.categories_[0].tolist(),'feature_names':pp.names,'numeric_scaling':False}


def restore_pp(r):
    pp=TreeInputRepresentation();pp.identity=r['fit_identity'];pp.medians=r['pooled_pair_medians']
    pp.round_median=r['rounds_median'];pp.title_mode=r['title_mode'];pp.division_mode=r['division_mode'];pp.names=r['feature_names']
    pp.encoder=OneHotEncoder(handle_unknown='ignore',drop=None,sparse_output=False,dtype=np.float64)
    pp.encoder.fit(np.array(r['division_categories'],object).reshape(-1,1));return pp


def predict(family,model,X):
    if family=='XGB':p=model.predict(xgb.DMatrix(X))
    elif family=='LGBM':p=model.predict(X,num_threads=1)
    else:p=model.predict_proba(X,thread_count=1)[:,1]
    p=np.asarray(p,float);require(np.isfinite(p).all() and ((p>=0)&(p<=1)).all(),'Invalid probability')
    return p


def save_model(family,model,path):
    suffix={'XGB':'.ubj','LGBM':'.txt','CAT':'.cbm'}[family];path=Path(str(path)+suffix)
    if family=='LGBM':model.save_model(str(path))
    else:model.save_model(str(path))
    if family=='XGB':restored=xgb.Booster();restored.load_model(str(path))
    elif family=='LGBM':restored=lgb.Booster(model_file=str(path))
    else:restored=cat.CatBoostClassifier();restored.load_model(str(path))
    return restored,path


def effective(family,model):
    if family=='XGB':return json.loads(model.save_config())
    if family=='LGBM':return {'parameters':model.params,'native_parameter_dump':model.model_to_string().split('parameters:')[-1]}
    return model.get_all_params()


def fit(family,candidate,X,y,ledger,output,key,validation=None,rounds=None):
    # Every attempted fit is durable before calling an estimator; failure never retries.
    entry={'key':key,'family':family,'candidate_id':candidate['candidate_id'],'status':'STARTED','rounds_requested':rounds,
           'training_N':len(y),'validation_N':len(validation[1]) if validation else 0}
    require(len(ledger)<1008,'Fit budget exceeded');ledger.append(entry);write_json(output/'FIT_LEDGER.json',ledger)
    state=StopState();p=candidate['parameters'].copy();begin=time.monotonic()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        if family=='XGB':
            ds=xgb.DMatrix(X,label=y)
            if validation:
                model=xgb.train(p,ds,num_boost_round=2000,evals=[(xgb.DMatrix(validation[0],label=validation[1]),'validation')],callbacks=[XStop(state)],verbose_eval=False)
                model=model[:state.rounds]
            else:model=xgb.train(p,ds,num_boost_round=rounds)
        elif family=='LGBM':
            ds=lgb.Dataset(X,label=y,params=p)
            if validation:
                model=lgb.train(p,ds,num_boost_round=2000,valid_sets=[lgb.Dataset(validation[0],label=validation[1],reference=ds)],valid_names=['validation'],callbacks=[LStop(state)])
                # Save/load the best prefix, independently of native best_iteration defaults.
                model=lgb.Booster(model_str=model.model_to_string(num_iteration=state.rounds))
            else:model=lgb.train(p,ds,num_boost_round=rounds)
        else:
            model=cat.CatBoostClassifier(**p,iterations=2000 if validation else rounds,use_best_model=False)
            if validation:
                model.fit(X,y,eval_set=validation,callbacks=[CStop(state)])
                model.shrink(ntree_end=state.rounds)
            else:model.fit(X,y)
    messages=[str(w.message) for w in caught]
    require(not any(any(t in m.lower() for t in ['unknown parameter','unused','not used','unsupported','ignored parameter']) for m in messages),'Unexpected parameter warning '+str(messages))
    entry.update(status='COMPLETED',elapsed_seconds=time.monotonic()-begin,best_rounds=state.rounds if validation else rounds,
                 completed_rounds=len(state.trace) if validation else rounds,cap_hit=len(state.trace)==2000,warnings=messages)
    write_json(output/'FIT_LEDGER.json',ledger)
    folder=output/'MODELS';folder.mkdir(exist_ok=True)
    restored,path=save_model(family,model,folder/key)
    write_json(folder/(key+'.parameters.json'),{'requested':candidate['parameters'],'effective':effective(family,model)})
    if validation:write_json(folder/(key+'.stopping.json'),{'trace':state.trace,'best_rounds':state.rounds,'best_native_loss':state.best,'patience':100,'tie_atol':1e-12})
    return model,restored,entry


def checked_prediction(family,model,restored,pp,rows):
    X=pp.transform(rows);p=predict(family,model,X);r=predict(family,restored,X)
    error=float(np.max(abs(p-r)));require(error<=1e-12,'Saved model reproduction failed')
    np.testing.assert_allclose(p,predict(family,model,pp.transform(swap(rows,'MOV1_MIN'))),atol=1e-12,rtol=0)
    require(np.array_equal(p,predict(family,model,pp.transform(rows[pp.columns]))),'Label dependence')
    changed=rows.copy();changed['method']='DECISION'
    require(np.array_equal(p,predict(family,model,pp.transform(changed))),'Changed label dependence')
    fixture=rows[pp.columns].iloc[:4].copy()
    for pair in pp.pairs:
        fixture.loc[fixture.index[0],pair['columns'][0]]=np.nan
        fixture.loc[fixture.index[-1],pair['columns'][1]]=np.nan
    np.testing.assert_allclose(predict(family,model,pp.transform(fixture)),predict(family,model,pp.transform(swap(fixture,'MOV1_MIN'))),atol=1e-12,rtol=0)
    require(np.array_equal(X,restore_pp(pp_record(pp)).transform(rows)),'Preprocessing restoration failed')
    return p,{'saved_max_error':error,'swap_label_asymmetric_null_passed':True,'matrix_sha256':hashlib.sha256(X.tobytes()).hexdigest()}


def verify(f02,mov0):
    require(sha(DIRECTORY/'CONTRACT_MANIFEST.json')==CONTRACT_SHA,'Contract identity mismatch')
    for name,r in load('CONTRACT_MANIFEST.json')['files'].items():require(sha(ROOT/name)==r['sha256'],'Contract drift '+name)
    for name,digest in load('source_identities.json')['files'].items():require(sha(ROOT/name)==digest,'Frozen source drift '+name)
    # Validator runs in a child: its explicit estimator disabling must not leak into execution.
    proc=subprocess.run([sys.executable,str(ROOT/'tools/contracts/validate_mov1_boosted_contract_v1.py'),'--f02-table',str(f02)],capture_output=True,text=True)
    require(proc.returncode==0,'No-fitting input validator failed: '+proc.stderr[-3000:])
    require(sha(mov0)==load('authoritative_baseline_identity.json')['frozen_MOV0_MIN_OOF_sha256'],'MOV0 identity mismatch')
    for name,r in json.loads((ROOT/'models/mov1/run_v1/EVIDENCE_MANIFEST.json').read_text())['files'].items():require(sha(ROOT/'models/mov1/run_v1'/name)==r['sha256'],'Linear evidence drift')
    pop=pd.read_csv(ROOT/load('target_population.json')['source_population_path']).sort_values(['event_date','event_id','fight_id']).reset_index(drop=True)
    columns=load('mov1_min_allowlist.json')['literal_f02_columns'];require(len(columns)==35,'Wrong feature count')
    frame=pop[['fight_id','event_date','event_id','method']].merge(pd.read_parquet(f02)[['fight_id']+columns],on='fight_id',validate='one_to_one')
    frame['outer_year']=frame.event_date.str[:4].astype(int)
    F=pd.read_csv(mov0,float_precision='round_trip')
    require(len(frame)==5658 and len(frame[frame.method.ne('DECISION')])==2822,'Population mismatch')
    outer=frame[frame.outer_year.ge(2018)];require(len(outer)==4260 and len(F)==4260 and not F.fight_id.duplicated().any() and set(outer.fight_id)==set(F.fight_id),'MOV0/outer coverage')
    q=outer.merge(F,on='fight_id',validate='one_to_one',suffixes=('','_mov0'))
    require(q.outer_year.eq(q.year).all() and q.event_date.eq(q.event_date_mov0).all() and q.event_id.eq(q.event_id_mov0).all(),'MOV0 chronology')
    require(q.method.ne('DECISION').astype(int).eq(q.target).all() and F.surface.eq('MOV0_MIN').all(),'MOV0 target')
    require(np.isfinite(F.probability).all() and F.probability.between(0,1).all(),'Invalid F')
    ev.join_terrain(pop)
    return frame,pop,F,{'status':'INPUT_IDENTITIES_PASSED','contract_sha256':CONTRACT_SHA,'F02_sha256':sha(f02),'MOV0_sha256':sha(mov0),'population_N':5658,'finish_N':2822,'outer_N':4260,'outer_finish_N':2115,'validator_stdout':proc.stdout}


def train(frame,output):
    ledger=[];preds=[];selections=[];candidates=[];checks=[];importance=[];preprocess=[]
    for fold in load('chronological_fold_plan.json')['folds']:
        year=fold['outer_year'];train=finish_history(frame,year);score=frame[frame.outer_year.eq(year)]
        require(scope_identity(train)==fold['training'] and scope_identity(score)==fold['all_eligible_scoring'],'Outer fold mismatch')
        require(scope_identity(score[score.method.ne('DECISION')])==fold['conditional_validation'],'Conditional fold mismatch')
        histories=[]
        for inner in fold['inner_folds']:
            iy=inner['validation_year'];it=finish_history(frame,iy);iv=frame[frame.outer_year.eq(iy)&frame.method.ne('DECISION')]
            require(scope_identity(it)==inner['training'] and scope_identity(iv)==inner['validation'],'Inner fold mismatch')
            pp=TreeInputRepresentation().fit(it);X=pp.transform(it);V=pp.transform(iv)
            rec={'outer_year':year,'stage':'inner','year':iy,'preprocessing':pp_record(pp),'training_matrix_sha256':hashlib.sha256(X.tobytes()).hexdigest(),'validation_matrix_sha256':hashlib.sha256(V.tobytes()).hexdigest()}
            preprocess.append(rec);write_json(output/'PREPROCESSING.json',preprocess)
            write_json(output/'MODELS'/f'{year}_inner_{iy}.preprocessing.json',pp_record(pp)) if (output/'MODELS').exists() else None
            histories.append((iy,it,iv,pp,X,V))
        year_candidates=[]
        for family in ['XGB','LGBM','CAT']:
            for candidate in load({'XGB':'xgb','LGBM':'lgbm','CAT':'cat'}[family]+'_candidates.json'):
                losses=[];inner_records=[]
                for iy,it,iv,pp,X,V in histories:
                    key=f'{year}_inner_{iy}_{candidate["candidate_id"]}'
                    model,restored,entry=fit(family,candidate,X,it.method.eq('KO_TKO').to_numpy(int),ledger,output,key,validation=(V,iv.method.eq('KO_TKO').to_numpy(int)))
                    p,c=checked_prediction(family,model,restored,pp,iv);checks.append({'key':key,**c})
                    np.savez_compressed(output/'MODELS'/(key+'.predictions.npz'),fight_id=iv.fight_id.to_numpy(str),p=p)
                    inner_records.append({'year':iy,'N':len(iv),'best_rounds':entry['best_rounds'],'completed_rounds':entry['completed_rounds'],'cap_hit':entry['cap_hit']})
                    losses.extend(binary_loss(iv.method.eq('KO_TKO'),p))
                record={'outer_year':year,'family':family,'candidate_id':candidate['candidate_id'],'parameters':candidate['parameters'],'inner_log_loss':float(np.mean(losses)),'inner':inner_records,'refit_rounds':refit_rounds(inner_records)}
                year_candidates.append(record);candidates.append(record);write_json(output/'INNER_CANDIDATES.json',candidates)
            print(f'Outer {year}: {family} inner candidates complete; fits={len(ledger)}',flush=True)
        best=choose(year_candidates);family_best={f:choose([r for r in year_candidates if r['family']==f]) for f in ['XGB','LGBM','CAT']}
        ordered=sorted(year_candidates,key=lambda r:r['inner_log_loss']);runner=next(r for r in ordered if r['candidate_id']!=best['candidate_id'])
        selections.append({**best,'runner_up_candidate':runner['candidate_id'],'margin_to_runner_up':runner['inner_log_loss']-best['inner_log_loss']})
        write_json(output/'SELECTED_BY_YEAR.json',selections)
        pp=TreeInputRepresentation().fit(train);X=pp.transform(train);T=pp.transform(score)
        write_json(output/'MODELS'/f'{year}_outer.preprocessing.json',pp_record(pp));preprocess.append({'outer_year':year,'stage':'outer','preprocessing':pp_record(pp),'training_matrix_sha256':hashlib.sha256(X.tobytes()).hexdigest(),'scoring_matrix_sha256':hashlib.sha256(T.tobytes()).hexdigest()})
        selected_model=None;selected_p=None
        for family,r in family_best.items():
            candidate={'candidate_id':r['candidate_id'],'parameters':r['parameters']};key=f'{year}_outer_{r["candidate_id"]}'
            model,restored,entry=fit(family,candidate,X,train.method.eq('KO_TKO').to_numpy(int),ledger,output,key,rounds=r['refit_rounds'])
            p,c=checked_prediction(family,model,restored,pp,score);checks.append({'key':key,**c})
            for surface in ['MOV1-'+family]+(['MOV1-BOOST-SELECT'] if family==best['family'] else []):
                q=score[['fight_id','event_id','event_date','outer_year']].copy();q['surface']=surface;q['selected_family']=family;q['candidate_id']=r['candidate_id'];q['rounds']=r['refit_rounds'];q['P_KO_given_finish']=p;q['P_SUB_given_finish']=1-p;preds.append(q)
            if family==best['family']:selected_model=model;selected_p=p
        candidate={'candidate_id':best['candidate_id'],'parameters':best['parameters']}
        repeated,restored,entry=fit(best['family'],candidate,X,train.method.eq('KO_TKO').to_numpy(int),ledger,output,f'{year}_repro_{best["candidate_id"]}',rounds=best['refit_rounds'])
        np.testing.assert_allclose(selected_p,predict(best['family'],repeated,T),atol=1e-12,rtol=0)
        checks.append({'key':f'{year}_repro','repeat_max_error':float(np.max(abs(selected_p-predict(best['family'],repeated,T))))})
        finish=score.method.ne('DECISION').to_numpy();V=T[finish];yy=score.loc[finish,'method'].eq('KO_TKO').to_numpy(int);base=binary_loss(yy,selected_p[finish]).mean()
        rng=np.random.default_rng(17)
        for j,name in enumerate(pp.names):
            values=[]
            for rep in range(5):
                perturbed=V.copy();perturbed[:,j]=V[rng.permutation(len(V)),j]
                values.append(float(binary_loss(yy,predict(best['family'],selected_model,perturbed)).mean()-base))
            importance.append({'outer_year':year,'family':best['family'],'feature':name,'kind':'held_out_permutation_log_loss','five_repetitions':values,'mean_increase':float(np.mean(values))})
        if best['family']=='XGB':
            for kind in ['weight','gain','total_gain']:
                values=selected_model.get_score(importance_type=kind)
                for j,name in enumerate(pp.names):importance.append({'outer_year':year,'family':'XGB','feature':name,'kind':'XGB_'+kind,'value':float(values.get('f'+str(j),0))})
        elif best['family']=='LGBM':
            for kind in ['split','gain']:
                for name,v in zip(pp.names,selected_model.feature_importance(importance_type=kind)):importance.append({'outer_year':year,'family':'LGBM','feature':name,'kind':'LGBM_'+kind,'value':float(v)})
        else:
            for name,v in zip(pp.names,selected_model.get_feature_importance(type='PredictionValuesChange')):importance.append({'outer_year':year,'family':'CAT','feature':name,'kind':'CAT_PredictionValuesChange','value':float(v)})
        write_json(output/'PREPROCESSING.json',preprocess);write_json(output/'REPRODUCIBILITY.json',checks);write_json(output/'IMPORTANCE.json',importance)
        print(f'Outer {year} scoring and reproduction pass; fits={len(ledger)}',flush=True)
    require(len(ledger)==1008 and sum('_inner_' in r['key'] for r in ledger)==972 and sum('_outer_' in r['key'] for r in ledger)==27 and sum('_repro_' in r['key'] for r in ledger)==9,'Fit accounting mismatch')
    require(all(r['status']=='COMPLETED' for r in ledger),'Incomplete fit')
    allscores=pd.concat(preds,ignore_index=True).sort_values(['event_date','event_id','fight_id','surface']).reset_index(drop=True)
    require(len(allscores)==17040 and not allscores.duplicated(['fight_id','surface']).any(),'Incomplete predictions')
    write_csv(output/'conditional_oof_all_eligible.csv',allscores)
    for surface in SURFACES[:-1]:write_csv(output/('oof_'+surface+'.csv'),allscores[allscores.surface.eq(surface)])
    saved=pd.read_csv(output/'conditional_oof_all_eligible.csv',float_precision='round_trip');np.testing.assert_allclose(saved.P_KO_given_finish,allscores.P_KO_given_finish,atol=1e-12,rtol=0)
    write_json(output/'FIT_BUDGET.json',{'inner':972,'outer':27,'reproducibility':9,'total':1008,'completed_rounds':sum(r['completed_rounds'] for r in ledger),'ceiling_hits':sum(r['cap_hit'] for r in ledger),'additional_exploratory_fits':0})
    return allscores


def evaluate(pop,F,scores,output):
    # Frozen evaluation routines; model training never sees memberships or outer labels.
    ev.SURFACES=SURFACES;ev.SYSTEMS=SYSTEMS
    x=pop[pop.event_date.ge('2018-01-01')].copy().reset_index(drop=True);x['outer_year']=x.event_date.str[:4].astype(int)
    x['F']=F.set_index('fight_id').loc[x.fight_id].probability.to_numpy(float)
    baseline=pd.read_csv(ROOT/'models/mov1/run_v1/conditional_oof_all_eligible.csv',float_precision='round_trip')
    baseline=baseline[baseline.surface.eq('MOV1_MIN')]
    require(len(baseline)==4260 and set(baseline.fight_id)==set(x.fight_id),'Linear scoring identity')
    scores=pd.concat([scores,baseline],ignore_index=True)
    ks={};ps={};composed=[]
    for surface,system in zip(SURFACES,SYSTEMS):
        k=scores[scores.surface.eq(surface)].set_index('fight_id').loc[x.fight_id].P_KO_given_finish.to_numpy(float)
        ks[surface]='K_'+surface;x[ks[surface]]=k;P=np.c_[x.F*k,x.F*(1-k),1-x.F]
        require(np.isfinite(P).all() and ((P>=0)&(P<=1)).all(),'Invalid composition')
        np.testing.assert_allclose(P.sum(axis=1),1,atol=1e-12,rtol=0)
        ps[system]=['P_'+system+'_'+m for m in ev.METHODS];x[ps[system]]=P
        q=x[['fight_id','event_id','event_date','outer_year']].copy();q['system']=system;q['F']=x.F;q['K']=k
        q[['P_'+m for m in ev.METHODS]]=P;q['actual_method']=x.method;composed.append(q)
    comp=pd.concat(composed,ignore_index=True);write_csv(output/'composed_oof_all_eligible.csv',comp)
    champion=pd.read_csv(ROOT/'models/mov1/run_v1/composed_oof_all_eligible.csv',float_precision='round_trip');champion=champion[champion.system.eq('S2')].set_index('fight_id').loc[x.fight_id]
    np.testing.assert_allclose(champion[['P_'+m for m in ev.METHODS]],x[ps['S2']],atol=1e-12,rtol=0)
    np.testing.assert_allclose(x[ps['SB'][2]],x[ps['S2'][2]],atol=0,rtol=0)
    finish=x[x.method.ne('DECISION')].copy();require(len(finish)==2115,'Conditional count')
    out=scores.merge(x[['fight_id','method']],on='fight_id',validate='many_to_one');write_csv(output/'conditional_oof_finishes.csv',out[out.method.ne('DECISION')])
    conditional={};composed_metrics={};losses={};mlosses={}
    for surface,system in zip(SURFACES,SYSTEMS):
        k=finish[ks[surface]];losses[surface]=binary_loss(finish.method.eq('KO_TKO'),k)
        conditional[surface]={'aggregate':ev.binary_metrics(finish.method.eq('KO_TKO'),k),'annual':{str(y):ev.binary_metrics(q.method.eq('KO_TKO'),q[ks[surface]]) for y in range(2018,2027) for q in [finish[finish.outer_year.eq(y)]]}}
        mlosses[system]=ev.multiclass_losses(x.method,x[ps[system]].to_numpy())
        composed_metrics[system]={'aggregate':ev.multiclass_metrics(x.method,x[ps[system]].to_numpy()),'annual':{str(y):ev.multiclass_metrics(q.method,q[ps[system]].to_numpy()) for y in range(2018,2027) for q in [x[x.outer_year.eq(y)]]}}
    expected=np.zeros(len(x));expected[x.method.ne('DECISION')]=losses[SURFACES[0]]-losses['MOV1_MIN']
    np.testing.assert_allclose(mlosses['SB']-mlosses['S2'],expected,atol=1e-12,rtol=0)
    runtime={'status':'ALL_IMPLEMENTATION_GATES_PASSED','fit_budget':json.loads((output/'FIT_BUDGET.json').read_text()),'outer_scoring_N_per_surface':4260,'conditional_N_per_surface':2115,'unexpected_dropped_rows':0,'decisions_in_fitting':0,'early_stopping_outer_rows':0,'common_matrix_all_families':True,'composition_max_sum_error':float(abs(comp[['P_'+m for m in ev.METHODS]].sum(axis=1)-1).max()),'conditional_composed_loss_identity_max_error':float(abs(mlosses['SB']-mlosses['S2']-expected).max()),'saved_models_and_repeated_refits_passed':True}
    write_json(output/'RUNTIME_VALIDATION.json',runtime)
    write_json(output/'conditional_metrics.json',conditional);write_json(output/'composed_metrics.json',composed_metrics)
    uncertainty={'conditional_SELECT_vs_MIN':ev.comparison(finish,losses[SURFACES[0]],losses['MOV1_MIN']),'composed_SB_vs_S2':ev.comparison(x,mlosses['SB'],mlosses['S2'])}
    write_json(output/'paired_uncertainty.json',uncertainty)
    buckets=[]
    for surface in SURFACES:
        for population_name,data in [('conditional_finishes',finish),('all_scoring_distribution',x)]:
            ix=np.searchsorted([.3,.4,.5,.6,.7,.8],data[ks[surface]],side='right')
            for i,label in enumerate(load('conditional_probability_buckets.json')['labels']):
                q=data.iloc[np.flatnonzero(ix==i)];n=len(q);k=int(q.method.eq('KO_TKO').sum());actual=k/n if n and population_name=='conditional_finishes' else None;mean=float(q[ks[surface]].mean()) if n else None
                buckets.append({'surface':surface,'population':population_name,'bucket':label,'N':n,'sample_status':ev.gate(n),'mean_predicted_KO':mean,'actual_KO_frequency':actual,'gap':mean-actual if actual is not None else None,'Wilson95':json.dumps(ev.wilson(k,n) if population_name=='conditional_finishes' else [None,None]),'year_coverage':json.dumps(q.outer_year.value_counts().sort_index().to_dict()),'division_composition':json.dumps(q.division.value_counts().sort_index().to_dict()),'archetype_composition':json.dumps({a:q[a].value_counts().sort_index().to_dict() for a in load('terrain_archetype_evaluation.json')['archetypes']})})
    write_csv(output/'fixed_probability_buckets.csv',pd.DataFrame(buckets))
    terrain=ev.join_terrain(pop);records=[];weight=[];arches=[];cross=[];annual=[]
    dims=load('terrain_archetype_evaluation.json')['terrain']['diagnostics']+['scheduled_rounds','era']
    for dim in dims:
        values=sorted(set(pop[dim].astype(str))|set(terrain[dim].astype(str)) if dim in terrain else set(pop[dim].astype(str)))
        if dim=='completeness_tier':values=sorted(set(values)|{'MODERATE_MISSINGNESS'})
        for value in values:records.extend(ev.cell_records(x[x[dim].astype(str).eq(value)],dim,value,ks,ps))
    for division in load('terrain_archetype_evaluation.json')['normalized_weight_classes']:
        weight.extend(ev.cell_records(x[x.division.eq(division)],'normalized_division',division,ks,ps))
    for archetype in load('terrain_archetype_evaluation.json')['archetypes']:
        for status in ['MATCH','NO_MATCH','UNASSIGNABLE']:
            q=x[x[archetype].eq(status)];label=archetype+'::'+status
            arches.extend(ev.cell_records(q,'archetype',label,ks,ps))
            for division in load('terrain_archetype_evaluation.json')['normalized_weight_classes']:
                cross.extend(ev.cell_records(q[q.division.eq(division)],'division_archetype',division+'::'+label,ks,ps))
    write_csv(output/'terrain_report.csv',pd.DataFrame(records));write_csv(output/'division_report.csv',pd.DataFrame(weight));write_csv(output/'all_archetype_report.csv',pd.DataFrame(arches));write_csv(output/'division_archetype_report.csv',pd.DataFrame(cross))
    panels={};panel_uncertainty={}
    for panel in ['preservation','correction']:
        spec=load('evaluation_panels.json')[panel];labels=spec.get('archetypes',[])+spec.get('divisions',[])+spec.get('primary',[])+spec.get('additional',[])
        rows=[]
        for label in labels:
            q=x[x[label].eq('MATCH')] if label in x.columns else x[x.division.eq(label)]
            rows.extend(ev.cell_records(q,'panel',label,ks,ps))
            for year in range(2018,2027):
                annual.extend({**r,'panel':panel,'outer_year':year} for r in ev.cell_records(q[q.outer_year.eq(year)],'panel',label,ks,ps))
            z=q[q.method.ne('DECISION')]
            panel_uncertainty[label]={'N':len(q),'finish_N':len(z),'sample_status':ev.gate(len(z))}
            if len(z)>=25:panel_uncertainty[label]['conditional_loss']=ev.bootstraps(z,binary_loss(z.method.eq('KO_TKO'),z[ks[SURFACES[0]]])-binary_loss(z.method.eq('KO_TKO'),z[ks['MOV1_MIN']]))
            if len(q)>=25:panel_uncertainty[label]['composed_loss']=ev.bootstraps(q,ev.multiclass_losses(q.method,q[ps['SB']].to_numpy())-ev.multiclass_losses(q.method,q[ps['S2']].to_numpy()))
        panels[panel]=rows;write_csv(output/(panel+'_panel.csv'),pd.DataFrame(rows))
    write_csv(output/'panel_annual.csv',pd.DataFrame(annual));write_json(output/'panel_uncertainty.json',panel_uncertainty)
    differences=[]
    baseline_cells={(r['kind'],r['cell']):r for r in records+weight+arches+cross if r['surface']=='MOV1_MIN'}
    for r in records+weight+arches+cross:
        if r['surface']!=SURFACES[0]:continue
        b=baseline_cells[(r['kind'],r['cell'])]
        differences.append({'kind':r['kind'],'cell':r['cell'],'N':r['N'],'finish_N':r['finish_N'],'sample_status':r['sample_status'],'finish_sample_status':r['finish_sample_status'],**{k+'_delta':r[k]-b[k] if r[k] is not None and b[k] is not None else None for k in ['K_finish_mean','conditional_gap','conditional_log_loss','conditional_brier','multiclass_log_loss','multiclass_brier']}})
    write_csv(output/'matched_cell_differences.csv',pd.DataFrame(differences))
    selection=json.loads((output/'SELECTED_BY_YEAR.json').read_text())
    selection_report={'annual':selection,'family_counts':{f:sum(r['family']==f for r in selection) for f in ['XGB','LGBM','CAT']},'caution':'Nine nested selections do not establish universal library superiority.'}
    write_json(output/'FAMILY_SELECTION_REPORT.json',selection_report)
    write_json(output/'SHADOW_FAMILY_REPORT.json',{'warning':'These fixed-family shadow results are descriptive. The experiment did not preregister choosing the production model by selecting the best outer-performing shadow family.','metrics':{s:conditional[s] for s in SURFACES[1:4]}})
    write_json(output/'pathway_decomposition.json',{'finish_node':ev.binary_metrics(x.method.ne('DECISION'),x.F),'method_node_weighted_losses':{s:float(losses[s].sum()/len(x)) for s in SURFACES},'identity':'Composed log-loss deltas equal conditional deltas weighted by finish fraction; not independent confirmation.','SHAP':'Deferred by frozen V1 contract','causality':'Predictive importance is not a causal hazard or transition parameter.'})
    return conditional,composed_metrics,uncertainty


def run(args):
    output=Path(args.output_dir);require(not output.exists() or not list(output.iterdir()),'Output must be empty; no silent resume/retry')
    output.mkdir(parents=True,exist_ok=True);(output/'MODELS').mkdir()
    freeze=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    require(not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip(),'Tracked tree dirty before fit')
    run_identity={'starting_main':START,'implementation_freeze_sha':freeze,'contract_sha256':CONTRACT_SHA,'seed':17,'threads':1,'code_sha256':sha(Path(__file__))}
    write_json(output/'RUN_MANIFEST.json',run_identity)
    begin=time.monotonic()
    try:
        frame,pop,F,input_evidence=verify(Path(args.f02_table),Path(args.mov0_min_oof))
        write_json(output/'INPUT_VALIDATION.json',input_evidence);write_json(output/'FOLD_IDENTITIES.json',load('chronological_fold_plan.json'))
    except Exception as e:
        write_json(output/'FAILURE.json',{'status':'MOV1_BOOSTED_TREE_CHALLENGER_V1_INPUT_IDENTITY_FAILED','error':str(e),'fits':0});raise
    with threadpool_limits(limits=1):
        versions={line.split('==')[0]:importlib.metadata.version(line.split('==')[0]) for line in (DIRECTORY/'requirements-lock.txt').read_text().splitlines()}
        for line in (DIRECTORY/'requirements-lock.txt').read_text().splitlines():
            name,version=line.split('==');require(versions[name]==version,'Transitive environment drift '+name)
        env={'python':platform.python_version(),'platform':platform.platform(),'machine':platform.machine(),'versions':versions,'threadpools':threadpool_info(),'CPU':Path('/proc/cpuinfo').read_text().split('model name')[1].splitlines()[0].strip() if Path('/proc/cpuinfo').exists() else platform.processor(),'cross_platform_bitwise_claim':False}
        write_json(output/'ENVIRONMENT_LOCK.json',env)
        try:
            scores=train(frame,output)
            evaluate(pop,F,scores,output)
        except Exception as e:
            count=len(json.loads((output/'FIT_LEDGER.json').read_text())) if (output/'FIT_LEDGER.json').exists() else 0
            write_json(output/'FAILURE.json',{'status':'MOV1_BOOSTED_TREE_CHALLENGER_V1_IMPLEMENTATION_FAILED','error':str(e),'attempted_fits':count,'predictive_interpretation_permitted':False});raise
    run_identity['runtime_seconds']=time.monotonic()-begin;write_json(output/'RUN_MANIFEST.json',run_identity)
    write_json(output/'EXECUTION_COMPLETE.json',{'status':'EXECUTION_AND_GATES_COMPLETE','scientific_report_required':True})
    print('Execution and evaluation complete; all implementation gates passed.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--f02-table',required=True);parser.add_argument('--mov0-min-oof',required=True);parser.add_argument('--output-dir',required=True)
    run(parser.parse_args())
