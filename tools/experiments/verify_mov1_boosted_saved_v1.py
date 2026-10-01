"""Zero-fit regeneration of all native prefixes, selected configurations and OOF scores."""
import argparse
import importlib.util
import json
import tarfile
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('boost_verification',ROOT/'models/challengers/mov1_boosted_v1/implementation_v1.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def native(family,path):
    if family=='XGB':model=m.xgb.Booster();model.load_model(str(path)+'.ubj')
    elif family=='LGBM':model=m.lgb.Booster(model_file=str(path)+'.txt')
    else:model=m.cat.CatBoostClassifier();model.load_model(str(path)+'.cbm')
    return model

def verify(f02,mov0,directory):
    directory=Path(directory);frame,pop,F,evidence=m.verify(Path(f02),Path(mov0))
    if (directory/'EVIDENCE_MANIFEST.json').exists():
        for name,r in json.loads((directory/'EVIDENCE_MANIFEST.json').read_text())['files'].items():
            m.require(m.sha(directory/name)==r['sha256'],'Evidence drift '+name)
    modeldir=directory/'MODELS'
    temporary=None
    if not modeldir.exists():
        temporary=tempfile.TemporaryDirectory()
        archive_path=directory/'NATIVE_MODELS.tar.xz'
        if not archive_path.exists():
            archive_path=Path(temporary.name)/'NATIVE_MODELS.tar.xz'
            with archive_path.open('wb') as stream:
                for part in sorted(directory.glob('NATIVE_MODELS.tar.xz.part*')):stream.write(part.read_bytes())
        with tarfile.open(archive_path) as archive:
            archive.extractall(temporary.name,filter='data')
        modeldir=Path(temporary.name)/'MODELS'
    for name,record in json.loads((directory/'NATIVE_MODEL_MANIFEST.json').read_text())['files'].items() if (directory/'NATIVE_MODEL_MANIFEST.json').exists() else []:
        m.require(m.sha(modeldir/name)==record['sha256'],'Native artifact hash drift '+name)
    tabledir=directory
    tabletemporary=None
    if not (directory/'conditional_oof_all_eligible.csv').exists():
        tabletemporary=tempfile.TemporaryDirectory()
        with tarfile.open(directory/'EVALUATION_TABLES.tar.xz') as archive:archive.extractall(tabletemporary.name,filter='data')
        tabledir=Path(tabletemporary.name)
    for name,record in json.loads((directory/'EVALUATION_TABLE_MANIFEST.json').read_text())['files'].items() if (directory/'EVALUATION_TABLE_MANIFEST.json').exists() else []:
        m.require(m.sha(tabledir/name)==record['sha256'],'Evaluation table hash drift '+name)
    selected=json.loads((directory/'SELECTED_BY_YEAR.json').read_text());candidates=json.loads((directory/'INNER_CANDIDATES.json').read_text())
    max_error=0.;count=0
    ledger=json.loads((directory/'FIT_LEDGER.json').read_text());m.require(len(ledger)==1008 and all(r['status']=='COMPLETED' for r in ledger),'Fit budget')
    bykey={r['key']:r for r in ledger}
    for r in candidates:
        losses=[]
        for inner in r['inner']:
            year=inner['year'];key=f'{r["outer_year"]}_inner_{year}_{r["candidate_id"]}'
            params=json.loads((modeldir/(key+'.parameters.json')).read_text())
            m.require(params['requested']==r['parameters'],'Effective requested parameters drift')
            if r['family']=='XGB':
                actual=params['effective']['learner'];m.require(actual['objective']['name']=='binary:logistic' and actual['generic_param']['device']=='cpu' and int(actual['generic_param']['nthread'])==1 and int(actual['generic_param']['seed'])==17,'XGB effective objective/device/thread/seed drift')
            elif r['family']=='CAT':
                actual=params['effective'];m.require(actual['loss_function']=='Logloss' and actual['task_type']=='CPU' and actual['random_seed']==17 and actual['depth']==r['parameters']['depth'],'CAT effective loss/device/seed/depth drift')
            else:
                actual=params['effective']['native_parameter_dump'];m.require('[objective: binary]' in actual and '[num_threads: 1]' in actual and '[seed: 17]' in actual,'LGB effective objective/thread/seed drift')
            pp=m.restore_pp(json.loads((modeldir/f'{r["outer_year"]}_inner_{year}.preprocessing.json').read_text()))
            rows=frame[frame.outer_year.eq(year)&frame.method.ne('DECISION')]
            p=m.predict(r['family'],native(r['family'],modeldir/key),pp.transform(rows))
            npz=np.load(modeldir/(key+'.predictions.npz'));m.require(np.array_equal(npz['fight_id'],rows.fight_id.to_numpy(str)),'Inner IDs')
            error=float(abs(p-npz['p']).max());m.require(error<=1e-12,'Inner saved predictions');max_error=max(error,max_error);count+=1
            trace=json.loads((modeldir/(key+'.stopping.json')).read_text());state=m.StopState()
            for i,value in enumerate(trace['trace']):
                stop=state.update(value);m.require(not stop or i==len(trace['trace'])-1,'Stopping continued beyond patience')
            m.require(state.rounds==inner['best_rounds']==trace['best_rounds'],'Best iteration drift')
            m.require(len(trace['trace'])==2000 or len(trace['trace'])-state.rounds==100,'Incorrect stopping endpoint')
            losses.extend(m.binary_loss(rows.method.eq('KO_TKO'),p))
        m.require(abs(float(np.mean(losses))-r['inner_log_loss'])<=1e-12 and m.refit_rounds(r['inner'])==r['refit_rounds'],'Inner ranking/rounds drift')
    scores=pd.read_csv(tabledir/'conditional_oof_all_eligible.csv',float_precision='round_trip')
    for year in range(2018,2027):
        records=[r for r in candidates if r['outer_year']==year];best=m.choose(records)
        original=next(r for r in selected if r['outer_year']==year)
        m.require(best['candidate_id']==original['candidate_id'] and best['refit_rounds']==original['refit_rounds'],'Selected choice drift')
        rows=frame[frame.outer_year.eq(year)];pp=m.restore_pp(json.loads((modeldir/f'{year}_outer.preprocessing.json').read_text()))
        for family in ['XGB','LGBM','CAT']:
            r=m.choose([r for r in records if r['family']==family]);key=f'{year}_outer_{r["candidate_id"]}'
            model=native(family,modeldir/key)
            actual_rounds=model.num_boosted_rounds() if family=='XGB' else model.current_iteration() if family=='LGBM' else model.tree_count_
            m.require(actual_rounds==r['refit_rounds'],'Outer refit actual rounds mismatch')
            p=m.predict(family,model,pp.transform(rows))
            for surface in ['MOV1-'+family]+(['MOV1-BOOST-SELECT'] if family==best['family'] else []):
                q=scores[scores.outer_year.eq(year)&scores.surface.eq(surface)].set_index('fight_id').loc[rows.fight_id]
                m.require(q.candidate_id.eq(r['candidate_id']).all() and q['rounds'].eq(r['refit_rounds']).all(),'Outer choice drift')
                error=float(abs(p-q.P_KO_given_finish.to_numpy()).max());m.require(error<=1e-12,'Outer reproduction');max_error=max(error,max_error)
            np.testing.assert_allclose(p,m.predict(family,model,pp.transform(m.swap(rows,'MOV1_MIN'))),atol=1e-12,rtol=0);count+=1
        repeat=m.predict(best['family'],native(best['family'],modeldir/f'{year}_repro_{best["candidate_id"]}'),pp.transform(rows))
        q=scores[scores.outer_year.eq(year)&scores.surface.eq('MOV1-BOOST-SELECT')].set_index('fight_id').loc[rows.fight_id]
        np.testing.assert_allclose(repeat,q.P_KO_given_finish,atol=1e-12,rtol=0);count+=1
    comp=pd.read_csv(tabledir/'composed_oof_all_eligible.csv',float_precision='round_trip')
    for system in m.SYSTEMS:
        q=comp[comp.system.eq(system)];np.testing.assert_allclose(q[['P_'+v for v in m.ev.METHODS]].sum(axis=1),1,atol=1e-12,rtol=0)
        np.testing.assert_allclose(q.P_KO_TKO,q.F*q.K,atol=1e-12,rtol=0);np.testing.assert_allclose(q.P_SUBMISSION,q.F*(1-q.K),atol=1e-12,rtol=0);np.testing.assert_allclose(q.P_DECISION,1-q.F,atol=1e-12,rtol=0)
    return {'status':'SAVED_RUN_REPRODUCED','models_checked':count,'max_error':max_error,'atol':1e-12,'rtol':0,'same_selected_configs_and_rounds_from_all_inner_evidence':True,'additional_estimator_fits':0,'full_search_refitting_performed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--f02-table',required=True);p.add_argument('--mov0-min-oof',required=True);p.add_argument('--run-dir',required=True);p.add_argument('--report')
    a=p.parse_args();result=verify(a.f02_table,a.mov0_min_oof,a.run_dir)
    if a.report:m.write_json(a.report,result)
    print(json.dumps(result,indent=2))
