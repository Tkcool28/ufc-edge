#!/usr/bin/env python3
"""Frozen hierarchical challenger. Stop before evaluation if any fit is unreliable."""
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
import pytensor.tensor as pt
from scipy.special import expit
from ufc_edge.models import mov0

ROOT=Path(__file__).resolve().parents[2]
SPEC=ROOT/'models/challengers/mov0_hierarchical_v1'
FREEZE='30b14dc5b355e9356dbdd80c793ab6d6feedf861'

def write(path,value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')

def groups(frame,fill,mapping):
    raw=frame.ctx__weight_class.fillna(fill).astype(str)
    if not set(raw).issubset(mapping): raise ValueError('UNREGISTERED_WEIGHT_LABEL')
    return raw.map(mapping)

def build_model(X,y,g,n_groups,indices,family_index):
    with pm.Model() as model:
        alpha=pm.Normal('alpha',0,1.5)
        beta=pm.Normal('beta',0,.5,shape=X.shape[1])
        tau_i=pm.HalfNormal('tau_intercept',1.)
        z_i=pm.Normal('z_intercept',0,1,shape=n_groups)
        di=pm.Deterministic('intercept_deviation',tau_i*z_i)
        eta=alpha+pt.dot(X,beta)+di[g]
        if indices:
            tau=pm.HalfNormal('tau_family',.5,shape=4)
            z=pm.Normal('z_slope',0,1,shape=(n_groups,len(indices)))
            ds=pm.Deterministic('slope_deviation',z*tau[np.asarray(family_index)])
            eta=eta+pt.sum(ds[g]*X[:,indices],axis=1)
        pm.Bernoulli('observed',logit_p=eta,observed=y)
    return model

def draws(idata,name):
    a=idata.posterior[name].values
    return a.reshape((-1,)+a.shape[2:])

def summarize(a):
    a=np.asarray(a);return {'mean':float(a.mean()),'sd':float(a.std()),'ci95':list(map(float,np.quantile(a,[.025,.975])))}

def predict(idata,X,labels,trained,indices,family_index,seed):
    a=draws(idata,'alpha'); b=draws(idata,'beta'); di=draws(idata,'intercept_deviation')
    ds=draws(idata,'slope_deviation') if indices else None
    rng=np.random.default_rng(seed)
    unseen={}
    for label in sorted(set(labels)-set(trained)):
        ui=rng.normal(size=len(a))*draws(idata,'tau_intercept')
        us=rng.normal(size=(len(a),len(indices)))*draws(idata,'tau_family')[:,family_index] if indices else None
        unseen[label]=(ui,us)
    logits=a[:,None]+b@X.T
    for j,label in enumerate(labels):
        if label in trained:
            gi=trained.index(label);logits[:,j]+=di[:,gi]
            if indices: logits[:,j]+=(ds[:,gi,:]*X[j,indices]).sum(axis=1)
        else:
            ui,us=unseen[label];logits[:,j]+=ui
            if indices: logits[:,j]+=(us*X[j,indices]).sum(axis=1)
    ps=expit(logits)
    return ps.mean(axis=0),np.quantile(ps,[.025,.975],axis=0)

def diagnostic(idata):
    names=['alpha','beta','tau_intercept','z_intercept']
    if 'tau_family' in idata.posterior:names+=['tau_family','z_slope']
    summary=az.summary(idata,var_names=names,round_to=None)
    # Direct computations retain full precision; rounded az.summary used only for per-parameter table.
    rhat=float(max(np.nanmax(x.values) for x in az.rhat(idata,var_names=names).data_vars.values()))
    bulk=float(min(np.nanmin(x.values) for x in az.ess(idata,var_names=names,method='bulk').data_vars.values()))
    tail=float(min(np.nanmin(x.values) for x in az.ess(idata,var_names=names,method='tail').data_vars.values()))
    d={'max_rhat':rhat,'min_bulk_ess':bulk,'min_tail_ess':tail,'divergences':int(idata.sample_stats.diverging.sum()),'bfmi_by_chain':list(map(float,az.bfmi(idata))),'max_tree_depth_hits':int((idata.sample_stats.tree_depth>=12).sum()),'parameters':json.loads(summary.to_json(orient='index'))}
    d['passed']=bool(np.isfinite([rhat,bulk,tail]).all() and rhat<=1.01 and bulk>=400 and tail>=400 and d['divergences']==0 and min(d['bfmi_by_chain'])>=.3 and d['max_tree_depth_hits']==0)
    return d

def effects(idata,X,g,trained,names,indices,family_index,train):
    p,_=predict(idata,X,list(train['_group']),trained,indices,family_index,0)
    info=p*(1-p);rows=[]
    for j,col in enumerate(['intercept']+[names[i] for i in indices]):
        global_d=draws(idata,'alpha') if j==0 else draws(idata,'beta')[:,indices[j-1]]
        dev=draws(idata,'intercept_deviation') if j==0 else draws(idata,'slope_deviation')[:,:,j-1]
        tau=draws(idata,'tau_intercept') if j==0 else draws(idata,'tau_family')[:,family_index[j-1]]
        for k,label in enumerate(trained):
            mask=g==k; x=np.ones(mask.sum()) if j==0 else X[mask,indices[j-1]]
            I=float((info[mask]*x*x).sum());pool=1/(1+tau*tau*I)
            rows.append({'column':col,'group':label,'global':summarize(global_d),'deviation':summarize(dev[:,k]),'group_effect':summarize(global_d+dev[:,k]),'tau':summarize(tau),'approximate_pooling_weight':summarize(pool),'conditional_information':I,'train_n':int(mask.sum()),'train_finishes':int(train.loc[mask,'target'].sum()),'training_predictor_variance':float(np.var(x))})
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--f02-dir',type=Path,required=True);ap.add_argument('--mov0-run-dir',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);args=ap.parse_args()
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    contract=mov0.load_json(SPEC/'contract.json')
    amendment=mov0.load_json(ROOT/'models/challengers/mov0_hierarchical_v1_1/amendment.json')
    for path,h in {**amendment['scientific_specification_hashes'],**amendment['source_snapshots']}.items():
        if mov0.file_sha256(ROOT/path)!=h:raise ValueError('SCIENTIFIC_SPECIFICATION_CHANGED '+path)
    if subprocess.check_output(['git','show',f"{FREEZE}:models/challengers/mov0_hierarchical_v1_1/amendment.json"],cwd=ROOT)!=(ROOT/'models/challengers/mov0_hierarchical_v1_1/amendment.json').read_bytes():raise ValueError('AMENDMENT_CHANGED')
    subprocess.run(['git','merge-base','--is-ancestor',FREEZE,'HEAD'],cwd=ROOT,check=True)
    for path,h in contract['frozen_sources'].items():
        if mov0.file_sha256(ROOT/path)!=h:raise ValueError('IMMUTABLE_SOURCE_CHANGED '+path)
    for path in SPEC.iterdir():
        if path.name in ['contract.json','requirements.lock','weight_class_map.json','varying_effect_map.json']:
            committed=subprocess.check_output(['git','show',f'{FREEZE}:{path.relative_to(ROOT)}'],cwd=ROOT)
            if committed!=path.read_bytes():raise ValueError('FROZEN_SPEC_CHANGED')
    write(out/'execution_identity.json',{'contract_commit':FREEZE,'contract_sha256':mov0.file_sha256(SPEC/'contract.json'),'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'python':platform.python_version(),'software':subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True).splitlines()})
    baseline_path=args.mov0_run_dir/'oof_MOV0_MIN.csv'
    if mov0.file_sha256(baseline_path)!=contract['frozen_MIN_OOF_sha256']:raise ValueError('FROZEN_OOF_HASH')
    baseline=pd.read_csv(baseline_path)
    population=mov0.build_population(args.f02_dir,ROOT/'data/canonical/v0/fights.csv')
    surface=mov0.load_json(ROOT/'models/mov0/feature_surface_v1.json')
    mapping=mov0.load_json(SPEC/'weight_class_map.json')['literal_map']
    families=mov0.load_json(SPEC/'varying_effect_map.json')['families']
    family_names=['striking','submission','takedown','survival'];varying=[x for f in family_names for x in families[f]];fi=[i for i,f in enumerate(family_names) for _ in families[f]]
    all_predictions={s:[] for s in ['H1','H2']};diags=[]
    for year in mov0.OUTER_YEARS:
        train,valid=mov0.fold_frames(population,year)
        expected=next(f for f in mov0.load_json(ROOT/'models/mov0/validation_plan_v1.json')['chronology']['folds'] if f['outer_year']==year)
        assert (len(train),len(valid))==(expected['outer_train_n'],expected['outer_validation_n'])
        frozen=baseline[baseline.year.eq(year)].set_index('fight_id').loc[valid.fight_id]
        assert np.array_equal(frozen.target.to_numpy(),valid.target.to_numpy())
        pre=mov0.SurfacePreprocessor.fit(train,surface,'MOV0_MIN');names=pre.numeric_names+['ctx__title_bout'];n=len(names)
        X=pre.transform(train)[:,:n];V=pre.transform(valid)[:,:n]
        train['_group']=groups(train,pre.weight_fill,mapping);vgroup=list(groups(valid,pre.weight_fill,mapping));trained=sorted(train['_group'].unique());g=np.array([trained.index(x) for x in train['_group']])
        write(out/f'preprocessing_{year}.json',{'train_n':len(train),'validation_n':len(valid),'train_max_date':str(train.event_date.max()),'validation_min_date':str(valid.event_date.min()),'metadata':pre.metadata(),'model_columns':names,'trained_groups':trained,'group_counts':train['_group'].value_counts().to_dict(),'unseen_validation_groups':sorted(set(vgroup)-set(trained))})
        for si,s in enumerate(['H1','H2'],1):
            indices=[] if s=='H1' else [names.index(x) for x in varying];family_index=[] if s=='H1' else fi;seed=17+year*10+si
            model=build_model(X,train.target.to_numpy(),g,len(trained),indices,family_index)
            with model:
                idata=pm.sample(draws=2000,tune=2000,chains=4,cores=4,random_seed=seed,target_accept=.95,init='jitter+adapt_diag',nuts={'max_treedepth':12},progressbar=False,compute_convergence_checks=True)
            d=diagnostic(idata);d.update({'surface':s,'year':year,'seed':seed});diags.append(d);write(out/'fit_diagnostics.json',diags)
            idata.to_netcdf(out/f'posterior_{s}_{year}.nc',engine='h5netcdf')
            write(out/f'effects_{s}_{year}.json',effects(idata,X,g,trained,names,indices,family_index,train))
            if not d['passed']:
                write(out/'BLOCKED.json',{'status':'V1_1_BLOCKED_CONVERGENCE','failed_surface':s,'failed_year':year,'diagnostics':d,'performance_interpretation':False});raise RuntimeError(f'CONVERGENCE_GATE_FAILED {s} {year}')
            p,ci=predict(idata,V,vgroup,trained,indices,family_index,seed+100000)
            swapped=pre.transform(mov0.swap_fighters(valid,surface,'MOV0_MIN'))[:,:n]
            q,_=predict(idata,swapped,vgroup,trained,indices,family_index,seed+100000)
            assert np.max(np.abs(p-q))<=1e-12
            if year==2018 and s=='H1':
                with model:
                    repeat=pm.sample(draws=2000,tune=2000,chains=4,cores=4,random_seed=seed,target_accept=.95,init='jitter+adapt_diag',nuts={'max_treedepth':12},progressbar=False,compute_convergence_checks=True)
                rp,_=predict(repeat,V,vgroup,trained,indices,family_index,seed+100000)
                same=all(np.array_equal(idata.posterior[k].values,repeat.posterior[k].values) for k in idata.posterior)
                write(out/'reproducibility.json',{'posterior_arrays_identical':same,'predictions_identical':bool(np.array_equal(rp,p)),'max_abs_probability_delta':float(np.max(np.abs(rp-p))),'scope':'first H1 fold exact same environment repeat'})
                if not same or not np.array_equal(rp,p):raise RuntimeError('REPRODUCIBILITY_GATE_FAILED')
            rows=valid[['fight_id','event_id','event_date','target']].copy();rows['year']=year;rows['probability']=p;rows['posterior_p_lower95']=ci[0];rows['posterior_p_upper95']=ci[1];rows['normalized_weight_class']=vgroup
            rows.to_csv(out/f'fold_{s}_{year}.csv',index=False);all_predictions[s].append(rows)
            print(f'FIT_PASS {s} {year}',flush=True)
    for s,frames in all_predictions.items():pd.concat(frames).to_csv(out/f'oof_{s}.csv',index=False)
    write(out/'FIT_COMPLETE.json',{'status':'V1_1_CONVERGENCE_VALIDATED','contract_commit':FREEZE,'oof_n':4260})

if __name__=='__main__':
    main()
    print('V1_1_CONVERGENCE_VALIDATED',flush=True)
