"""Execute merged PR124 exactly. No reference retraining or prospective outcome access."""
from __future__ import annotations
import hashlib, importlib.util, json, pathlib, platform, subprocess, sys, warnings
import numpy as np
import pandas as pd
import pyarrow, scipy, sklearn
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits, threadpool_info
R=pathlib.Path(__file__).resolve().parents[3]
D=R/'models/challengers/mov1_three_arm_directional_v1'
BASE='a638fc1c9a66986875e1929949886c3ef6bf6621'
CONTRACT_SHA='08386e74b5a9e2257d2650c8925754b5cac61a625cee8746bbc8a19c3d606243'
sys.path.insert(0,str(R/'models/mov1'))
from implementation_v1 import binary_loss, scope_identity
s=importlib.util.spec_from_file_location('three_arm_contract_probe',R/'tools/contracts/validate_mov1_three_arm_contract_v1.py')
probe=importlib.util.module_from_spec(s);s.loader.exec_module(probe)
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def spec(n):return json.loads((D/n).read_text())
def write_json(p,x):pathlib.Path(p).write_text(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n')
def write_csv(p,x):x.to_csv(p,index=False,float_format='%.17g',lineterminator='\n')
def environment():
    v={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__,'scipy':scipy.__version__,'scikit-learn':sklearn.__version__}
    for name,value in spec('model_regularization.json')['dependency_lock'].items():require(v[name].startswith(value+'.') if name=='python' else v[name]==value,'Dependency mismatch '+name)
    return {'versions':v,'threads':1,'threadpools':threadpool_info(),'prediction_atol':1e-12,'prediction_rtol':0,'cross_platform_bitwise_identity_claimed':False}
class Preprocessor(probe.MatrixProbe):
    def record(self):
        return {'arm':self.arm,'pair_medians':[{'columns':list(k),'median':v} for k,v in self.medians.items()], 'round_median':self.round_median,'title_mode':bool(self.title_mode),'division_mode':self.division_mode,'categories':self.categories,'scaled':self.scaled.tolist(),'mean':self.mean.tolist(),'variance':self.var.tolist(),'scale':self.scale.tolist(),'feature_names':[f['name'] for f in self.features]+['division='+c for c in self.categories],'literal_sources':self.columns}
    @classmethod
    def restore(cls,rec):
        pp=cls(rec['arm']);pp.medians={tuple(x['columns']):x['median'] for x in rec['pair_medians']}
        for name in ['round_median','title_mode','division_mode','categories']:setattr(pp,name,rec[name])
        for name in ['scaled','mean','scale']:setattr(pp,name,np.asarray(rec[name],bool if name=='scaled' else float))
        pp.var=np.asarray(rec['variance'],float);return pp

def predict_record(record,features):
    pp=Preprocessor.restore(record['preprocessing']);return expit(pp.transform(features)@np.asarray(record['coef'],float)+record['intercept'])
def select_candidate(losses):
    best=losses[0]
    for row in losses[1:]:
        if row['inner_log_loss']<best['inner_log_loss']-1e-12:best=row
    return best

def check_probabilities(pp,predict,rows):
    features=rows[pp.columns].copy();p=predict(features)
    require(np.isfinite(p).all() and ((0<=p)&(p<=1)).all(),'Invalid K')
    err=float(np.max(np.abs(p-predict(pp.swap(features)))))
    require(err<=1e-12,'Predictive fighter swap failed')
    changed=features.copy();changed['method']='ARBITRARY';changed['winner_id']='IGNORED'
    require(np.array_equal(p,predict(changed)),'Labels affect scoring')
    fixture=features.head(4).copy()
    for a,b in pp.pairs:
        fixture.loc[fixture.index[:2],a]=np.nan;fixture.loc[fixture.index[1:3],b]=np.nan
    merr=float(np.max(np.abs(predict(fixture)-predict(pp.swap(fixture)))))
    require(merr<=1e-12,'Asymmetric null probability swap failed')
    return p,{'probability_swap_error':err,'asymmetric_null_swap_error':merr,'labels_changed_identical':True}

def verify_sources(f02path,mov0path,out):
    require(sha(D/'CONTRACT_MANIFEST.json')==CONTRACT_SHA,'PR124 contract digest mismatch')
    # Validator deliberately disables predictive methods, so run it in an isolated process.
    subprocess.run([sys.executable,'-W','ignore::FutureWarning',str(R/'tools/contracts/validate_mov1_three_arm_contract_v1.py'),'--f02',str(f02path),'--output',str(out/'CONTRACT_INPUT_VALIDATION.json')],check=True,cwd=R)
    require(sha(mov0path)==spec('three_way_composition.json')['MOV0_MIN_OOF_sha256'],'Frozen F mismatch')
    require(sha(R/'models/mov1/run_v1/oof_MOV1_MIN.csv')==spec('arm_a_reference.json')['prediction_sha256'],'Frozen A mismatch')
    f02=pd.read_parquet(f02path);population=pd.read_csv(R/spec('target_population.json')['source_population_path']).sort_values(['event_date','event_id','fight_id']).reset_index(drop=True)
    require(len(population)==5658 and population.event_date.max()<='2026-08-15','Historical population/boundary')
    columns=spec('feature_specifications.json')['arms']['B']['raw_columns']
    # Labels kept apart from feature states. Only prior finish membership selects training rows.
    states=f02[['fight_id']+columns].set_index('fight_id');meta=population[['fight_id','event_id','event_date']].copy();meta['outer_year']=meta.event_date.str[:4].astype(int)
    require(set(meta.fight_id)<=set(states.index),'Missing source IDs')
    A=pd.read_csv(R/'models/mov1/run_v1/oof_MOV1_MIN.csv',float_precision='round_trip');F=pd.read_csv(mov0path,float_precision='round_trip')
    outer=meta[meta.outer_year>=2018]
    require(len(A)==len(F)==4260 and not A.fight_id.duplicated().any() and not F.fight_id.duplicated().any(),'Reference row counts/uniqueness')
    require(set(A.fight_id)==set(F.fight_id)==set(outer.fight_id),'Reference population identity')
    require(np.isfinite(F.probability).all() and F.probability.between(0,1).all(),'Invalid frozen F')
    labels=population.set_index('fight_id').method
    for ref,yearcol in [(A,'outer_year'),(F,'year')]:
        aligned=ref.set_index('fight_id').loc[outer.fight_id]
        require(aligned[yearcol].tolist()==outer.outer_year.tolist() and aligned.event_id.tolist()==outer.event_id.tolist() and aligned.event_date.tolist()==outer.event_date.tolist(),'Reference chronological metadata mismatch')
    evidence={'status':'PASS','contract_SHA256':CONTRACT_SHA,'starting_main':BASE,'F02_physical_SHA256':sha(f02path),'Arm_A_SHA256':sha(R/'models/mov1/run_v1/oof_MOV1_MIN.csv'),'MOV0_MIN_SHA256':sha(mov0path),'PR123_manifest_SHA256':sha(R/'docs/model_diagnostics/mov1_directional_representation_v1/EVIDENCE_MANIFEST.json'),'modern_eligible_N':5658,'conditional_N':int(labels.isin(['KO_TKO','SUBMISSION']).sum()),'outer_eligible_N':4260,'post_boundary_outcomes_accessed':False,'source_files':spec('SOURCE_MANIFEST.json')['files']}
    write_json(out/'VERIFIED_INPUT_MANIFEST.json',evidence)
    return states,meta,labels,population,A,F

class FitLedger:
    def __init__(self,out):self.out=out;self.rows=[]
    def begin(self,record):
        require(len(self.rows)<164,'Absolute fit budget exceeded');self.rows.append({**record,'fit_number':len(self.rows)+1,'status':'STARTED'});write_json(self.out/'FIT_LEDGER.json',self.rows)
    def finish(self,record):self.rows[-1].update(record,status='COMPLETE');write_json(self.out/'FIT_LEDGER.json',self.rows)
    def check(self):
        counts={k:sum(r['phase']==k for r in self.rows) for k in ['inner','outer','representative_reproduction']}
        require(counts=={'inner':144,'outer':18,'representative_reproduction':2} and all(r['status']=='COMPLETE' for r in self.rows),'Incomplete/invalid fit ledger')
        return {'completed':len(self.rows),'attempted':len(self.rows),'counts':counts,'Arm_A_refits':0,'unauthorized_fits':0,'status':'PASS'}

def completeness(train,y,score,arm):
    fs=spec('feature_specifications.json');sub=fs['source_concepts']['SUB_PRESSURE']['columns']+fs['source_concepts']['SUB_EXPOSURE']['columns'];compact=[c for c in fs['arms']['C']['raw_columns'] if c.startswith(('f1__','f2__','mx__'))]
    return {'training':{'N':len(train),'per_literal_null':train.isna().sum().to_dict(),'submission_complete':int(train[sub].notna().all(axis=1).sum()),'compact_complete':int(train[compact].notna().all(axis=1).sum()),'by_label':{str(label):{'N':int((y==label).sum()),'submission_complete':int(train.loc[y==label,sub].notna().all(axis=1).sum()),'compact_complete':int(train.loc[y==label,compact].notna().all(axis=1).sum())} for label in [0,1]}},'scoring':{'N':len(score),'per_literal_null':score.isna().sum().to_dict(),'submission_complete':int(score[sub].notna().all(axis=1).sum()),'compact_complete':int(score[compact].notna().all(axis=1).sum())}}

def fit_one(ledger,train_features,y,score_features,details,train_meta,score_meta):
    settings=spec('model_regularization.json');require(set(y)=={0,1},'Invalid/nonnatural training classes')
    pp=Preprocessor(details['arm']).freeze(train_features)
    expected=spec('feature_specifications.json')['arms'][details['arm']]['before_one_hot']+len(pp.categories)
    require(pp.transform(train_features).shape[1]==expected,'Feature dimension mismatch')
    ledger.begin({**details,'train_identity':scope_identity(train_meta),'score_identity':{'N':len(score_meta),'ordered_fight_id_sha256':hashlib.sha256(''.join(score_meta.fight_id+'\n').encode()).hexdigest()},'KO_N':int(np.sum(y)),'SUB_N':int(len(y)-np.sum(y)),'features':expected})
    model=LogisticRegression(C=details['C'],penalty='l2',solver='lbfgs',fit_intercept=True,tol=1e-4,max_iter=3000,random_state=17,class_weight=None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');model.fit(pp.transform(train_features),y)
    require(not any(issubclass(w.category,ConvergenceWarning) for w in caught) and int(model.n_iter_[0])<3000,'Solver convergence failed')
    require(np.isfinite(model.coef_).all() and np.isfinite(model.intercept_).all(),'Nonfinite parameters')
    p,checks=check_probabilities(pp,lambda x:model.predict_proba(pp.transform(x))[:,1],score_features)
    record={**details,'train_identity':scope_identity(train_meta),'preprocessing':pp.record(),'coef':model.coef_[0].tolist(),'intercept':float(model.intercept_[0]),'classes':model.classes_.tolist(),'n_iter':int(model.n_iter_[0]),'warnings':[str(w.message) for w in caught],'scoring_fight_ids':score_meta.fight_id.tolist(),'scoring_probabilities':p.tolist(),'source_completeness':completeness(train_features,y,score_features,details['arm']),**checks}
    regen=predict_record(record,score_features);error=float(np.max(abs(p-regen)));require(error<=1e-12,'Saved prediction regeneration failed')
    record['saved_prediction_max_error']=error
    name=f"{details['phase']}_{details['outer_year']}_{details['arm']}_{details.get('inner_year',0)}_C{details['C']}.json"
    write_json(ledger.out/'MODELS'/name,record)
    ledger.finish({'record_path':'MODELS/'+name,'record_SHA256':sha(ledger.out/'MODELS'/name),'n_iter':record['n_iter'],'warnings':record['warnings'],**checks,'saved_prediction_max_error':error})
    return record,p,pp

def training(f02path,mov0path,out,freeze):
    out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    require(not (out/'FIT_LEDGER.json').exists(),'Output already has fit ledger; do not rerun')
    require(len(freeze)==40,'Implementation freeze SHA required')
    frozen=R/'models/challengers/mov1_three_arm_directional_run_v1/PRE_FIT_IMPLEMENTATION_MANIFEST.json';identity=json.loads(frozen.read_text())
    for path,h in identity['files'].items():require(sha(R/path)==h,'Implementation changed after freeze '+path)
    states,meta,labels,population,A,F=verify_sources(f02path,mov0path,out)
    write_json(out/'IMPLEMENTATION_FREEZE_RECORD.json',{'starting_main':BASE,'implementation_freeze_SHA':freeze,'manifest_SHA256':sha(frozen),'contract_SHA256':CONTRACT_SHA,'implementation_files':identity['files'],'verified_before_first_fit':True})
    (out/'MODELS').mkdir(exist_ok=True);ledger=FitLedger(out);foldids=probe.load('ordered_fold_fight_ids.json.xz')['folds'];selected=[];scores=[];selection=[];prepchecks=[]
    def history(ids):
        t=meta.set_index('fight_id',drop=False).loc[ids].reset_index(drop=True);t['method']=labels.loc[ids].to_numpy();require(t.method.isin(['KO_TKO','SUBMISSION']).all(),'Decision in fitting');return t
    def feats(ids,arm):return states.loc[ids,spec('feature_specifications.json')['arms'][arm]['raw_columns']].reset_index(drop=True)
    with threadpool_limits(limits=1):
        write_json(out/'ENVIRONMENT_LOCK.json',environment())
        for fold in foldids:
            year=fold['outer_year'];ot=history(fold['training']);os=meta.set_index('fight_id',drop=False).loc[fold['scoring']].reset_index(drop=True)
            for arm in ['B','C']:
                grid=[]
                for C in spec('model_regularization.json')['C_grid']:
                    loss=[]
                    for inner in fold['inner']:
                        it=history(inner['training']);iv=history(inner['validation']);iy=inner['validation_year']
                        record,p,pp=fit_one(ledger,feats(it.fight_id,arm),it.method.eq('KO_TKO').to_numpy(int),feats(iv.fight_id,arm),{'phase':'inner','outer_year':year,'inner_year':iy,'arm':arm,'C':C},it,iv)
                        require(it.event_date.max()<f'{iy}-01-01','Inner cutoff failure');loss.extend(binary_loss(iv.method.eq('KO_TKO'),p))
                        selection.append({'outer_year':year,'arm':arm,'C':C,'inner_year':iy,'N':len(iv),'log_loss':float(np.mean(binary_loss(iv.method.eq('KO_TKO'),p)))})
                    grid.append({'C':C,'N':len(loss),'inner_log_loss':float(np.mean(loss))})
                best=select_candidate(grid);require(ot.event_date.max()<f'{year}-01-01','Outer cutoff failure')
                record,p,pp=fit_one(ledger,feats(ot.fight_id,arm),ot.method.eq('KO_TKO').to_numpy(int),feats(os.fight_id,arm),{'phase':'outer','outer_year':year,'arm':arm,'C':best['C']},ot,os)
                require(len(pp.categories)==13 and len(record['coef'])=={'B':48,'C':28}[arm],'Outer dimensions failure')
                selected.append({'outer_year':year,'arm':arm,'selected_C':best['C'],'inner_log_loss':best['inner_log_loss'],'grid':grid})
                z=os.copy();z['arm']=arm;z['K']=p;z['SUB_given_finish']=1-p;scores.append(z)
                # Source completeness and shared-imputation comparison are outcome-free.
                prepchecks.append({'year':year,'arm':arm,'pair_medians':record['preprocessing']['pair_medians']})
            b,c=prepchecks[-2:];bm={tuple(v['columns']):v['median'] for v in b['pair_medians']};cm={tuple(v['columns']):v['median'] for v in c['pair_medians']};require(all(bm[k]==v for k,v in cm.items()),'B/C source imputation differs')
            print(f'Outer {year}: fits and prediction gates passed; no outer metrics inspected',flush=True)
        # Exactly two authorized 2021 refits; no A refit.
        rep=[];fold=next(f for f in foldids if f['outer_year']==2021);ot=history(fold['training']);os=meta.set_index('fight_id',drop=False).loc[fold['scoring']].reset_index(drop=True)
        for arm in ['B','C']:
            C=next(x['selected_C'] for x in selected if x['outer_year']==2021 and x['arm']==arm)
            record,p,pp=fit_one(ledger,feats(ot.fight_id,arm),ot.method.eq('KO_TKO').to_numpy(int),feats(os.fight_id,arm),{'phase':'representative_reproduction','outer_year':2021,'arm':arm,'C':C},ot,os)
            orig=next(x for x in scores if x.arm.iloc[0]==arm and x.outer_year.iloc[0]==2021);err=float(np.max(abs(orig.K.to_numpy()-p)));require(err<=1e-12,'2021 reproduction failure');rep.append({'arm':arm,'year':2021,'max_probability_error':err,'identical_float64':err==0})
        completed=ledger.check()
    # Persist prediction-only tables before any evaluation label join.
    pred=pd.concat(scores).sort_values(['event_date','event_id','fight_id','arm']).reset_index(drop=True)
    require(len(pred)==8520 and not pred.duplicated(['fight_id','arm']).any(),'Incomplete outer score coverage')
    write_csv(out/'CHALLENGER_OUTER_PREDICTIONS.csv',pred)
    a=A[['fight_id','event_id','event_date','outer_year']].copy();a['arm']='A';a['K']=A.P_KO_given_finish;a['SUB_given_finish']=1-a.K
    for arm in ['B','C']:write_csv(out/f'oof_{arm}.csv',pred[pred.arm==arm])
    allpred=pd.concat([a,pred]).sort_values(['event_date','event_id','fight_id','arm']).reset_index(drop=True);write_csv(out/'ALL_ARMS_OUTER_PREDICTIONS.csv',allpred)
    roundtrip=pd.read_csv(out/'CHALLENGER_OUTER_PREDICTIONS.csv',float_precision='round_trip');require(np.array_equal(roundtrip.K,pred.K),'Prediction CSV roundtrip failure')
    write_json(out/'MODEL_SELECTION.json',selected);write_csv(out/'INNER_SELECTION_EVIDENCE.csv',pd.DataFrame(selection));write_csv(out/'SELECTED_REGULARIZATION.csv',pd.DataFrame([{k:v for k,v in row.items() if k!='grid'} for row in selected]))
    write_json(out/'FIT_BUDGET_VALIDATION.json',completed);write_json(out/'REPRODUCTION_2021.json',rep)
    for path,h in spec('SOURCE_MANIFEST.json')['files'].items():require(sha(R/path)==h,'Frozen source modified '+path)
    write_json(out/'RUNTIME_VALIDATION.json',{'status':'PASS','source_artifacts_unchanged':True,'exact_fit_budget':completed,'max_swap_error':max(x['probability_swap_error'] for x in ledger.rows),'saved_predictions_max_error':max(x['saved_prediction_max_error'] for x in ledger.rows),'scoring_precedes_outer_outcome_join':True,'natural_training_prevalence_retained':True,'shared_source_imputation_equal':True,'reproduction':rep,'post_boundary_outcomes_accessed':False})
    return population,states,F,allpred
