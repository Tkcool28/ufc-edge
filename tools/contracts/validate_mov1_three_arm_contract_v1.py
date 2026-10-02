"""No-training preregistration validator. Matrix probes only; not an experiment runner."""
from __future__ import annotations
import argparse, lzma, hashlib, importlib.util, json, pathlib, sys
import numpy as np
import pandas as pd
R=pathlib.Path(__file__).resolve().parents[2]
D=R/'models/challengers/mov1_three_arm_directional_v1'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(n):return json.loads(lzma.decompress((D/n).read_bytes())) if n.endswith('.xz') else json.loads((D/n).read_text())
def require(ok,msg):
    if not ok:raise ValueError(msg)
def read_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def operation(op,x):
    if op=='mean':return (x[:,0]+x[:,1])/2
    if op=='absolute_difference':return np.abs(x[:,0]-x[:,1])
    if op=='identity':return x[:,0]
    if op=='cross_product_sum':return x[:,0]*x[:,3]+x[:,1]*x[:,2]
    if op=='pressure_against_weakness_sum':return x[:,0]*(1-x[:,3])+x[:,1]*(1-x[:,2])
    raise ValueError('Unapproved operation '+op)

class MatrixProbe:
    """Freeze source-level medians and moments without invoking any predictive estimator."""
    def __init__(self,arm):
        self.arm=arm; self.spec=load('feature_specifications.json');self.features=self.spec['arms'][arm]['predictors']
        self.pairs={tuple(f['inputs']) for f in self.features if f['operation'] in ('mean','absolute_difference')}
        # Interactions share original pairs, not a four-column pooled median.
        for f in self.features:
            if f['operation'] in ('cross_product_sum','pressure_against_weakness_sum'):
                self.pairs.update([tuple(f['inputs'][:2]),tuple(f['inputs'][2:])])
        self.pairs=sorted(self.pairs); self.columns=self.spec['arms'][arm]['raw_columns']
        self.mapping=json.loads((R/'models/challengers/mov0_hierarchical_v1/weight_class_map.json').read_text())['literal_map']
    def normalized_division(self,x):
        require(x.ctx__weight_class.dropna().isin(self.mapping).all(),'Unknown division literal')
        return x.ctx__weight_class.map(self.mapping)
    @staticmethod
    def median(v):
        v=np.asarray(v,float); require(not np.isinf(v).any(),'Inf input');v=v[np.isfinite(v)];require(len(v)>0,'All missing history');return float(np.median(v))
    @staticmethod
    def mode(s):
        q=s.dropna().value_counts();require(len(q)>0,'All missing category');return sorted(q[q==q.max()].index.tolist())[0]
    def freeze(self,train):
        self.medians={p:self.median(train[list(p)].to_numpy(float)) for p in self.pairs}
        self.round_median=self.median(train.scheduled_rounds)
        require(train.ctx__title_bout.dropna().isin([0,1,False,True]).all(),'Invalid title')
        self.title_mode=self.mode(train.ctx__title_bout)
        div=self.normalized_division(train);self.division_mode=self.mode(div);self.categories=sorted(div.fillna(self.division_mode).unique())
        raw=self.unscaled(train);self.scaled=np.array([f['scaled'] for f in self.features],bool)
        self.mean=raw[:,self.scaled].mean(axis=0);self.var=raw[:,self.scaled].var(axis=0)
        self.scale=np.sqrt(self.var);self.scale[self.scale==0]=1
        return self
    def imputed(self,rows):
        x=rows[self.columns].copy()
        for pair,median in self.medians.items():
            v=x[list(pair)].to_numpy(float);require(not np.isinf(v).any(),'Inf input');x[list(pair)]=np.where(np.isnan(v),median,v)
        x['scheduled_rounds']=x.scheduled_rounds.fillna(self.round_median)
        require(x.ctx__title_bout.dropna().isin([0,1,False,True]).all(),'Invalid title')
        x['ctx__title_bout']=x.ctx__title_bout.fillna(self.title_mode)
        return x
    def unscaled(self,rows):
        x=self.imputed(rows)
        return np.column_stack([operation(f['operation'],x[f['inputs']].to_numpy(float)) for f in self.features])
    def transform(self,rows):
        raw=self.unscaled(rows);raw[:,self.scaled]=(raw[:,self.scaled]-self.mean)/self.scale
        div=self.normalized_division(rows).fillna(self.division_mode).to_numpy()
        onehot=np.column_stack([div==cat for cat in self.categories]).astype(float)
        out=np.c_[raw,onehot];require(np.isfinite(out).all(),'Nonfinite matrix');return out
    def swap(self,rows):
        x=rows.copy()
        for a,b in self.pairs:x[a],x[b]=rows[b].copy(),rows[a].copy()
        return x

def validate(f02path,check_manifest=True):
    # Explicitly disable predictive entry points before any repository validator imports.
    from sklearn.linear_model import LogisticRegression
    def forbidden(*a,**k):raise RuntimeError('Stage1 predictive fit/prediction prohibited')
    for name in ('fit','predict','predict_proba','decision_function'):setattr(LogisticRegression,name,forbidden)
    src=load('SOURCE_MANIFEST.json')
    for p,h in src['files'].items():require(sha(R/p)==h,'Source changed: '+p)
    require(sha(f02path)==src['corrected_F02']['physical_sha256'],'F02 physical bytes mismatch')
    require(sha(R/'docs/model_diagnostics/mov1_directional_representation_v1/EVIDENCE_MANIFEST.json')==src['PR123_manifest_sha256'],'PR123 manifest mismatch')
    if check_manifest:
        for p,h in load('CONTRACT_MANIFEST.json')['files'].items():require(sha(R/p)==h,'Contract changed: '+p)
    old=read_module(R/'tools/contracts/validate_mov1_contract_v1.py','original_contract_validator')
    original=old.validate(pathlib.Path(f02path))
    collision=read_module(R/'tests/diagnostics/test_mov1_directional_collision_v1.py','collision');collision.test_directional_collision()
    spec=load('feature_specifications.json');arms=spec['arms']
    require([len(arms[k]['raw_columns']) for k in 'ABC']==[35,35,23],'Raw column counts')
    require([len(arms[k]['predictors']) for k in 'ABC']==[34,35,15],'Transformed counts')
    require(arms['A']['raw_columns']==arms['B']['raw_columns'],'B added raw source')
    require([f for f in arms['B']['predictors'] if f['name']!='SUB_DIRECTIONAL_SUM']==arms['A']['predictors'],'B changed original representation')
    require(arms['B']['predictors'][-2]==arms['C']['predictors'][11],'Different SUB formulas')
    require(load('model_regularization.json')['C_grid']==[.03,.1,.3,1.0],'Grid changed')
    require(load('chronological_fold_plan.json')==json.loads((R/'models/mov1/run_v1/FOLD_IDENTITIES.json').read_text()),'Fold identities changed')
    f02=pd.read_parquet(f02path)
    require(set(arms['C']['raw_columns'])<=set(f02.columns),'Compact column missing')
    # The reused KD quantity is NOT KD-per15 product: independently check its efficiency definition.
    kds=spec['source_concepts']['KD_DIRECTIONAL']['columns'];nkd=0
    for index,(a,b) in enumerate([('f1','f2'),('f2','f1')]):
        creation=f'{a}__fs__knockdown_efficiency__creation__career__shrunk';vul=f'{b}__fs__knockdown_efficiency__vulnerability__career__shrunk'
        q=f02[[creation,vul,kds[index]]].dropna();require(np.allclose(q[kds[index]],q[creation]-q[vul],atol=1e-12,rtol=0),'KD semantic mismatch');nkd+=len(q)
    pop=pd.read_csv(R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz')
    require(pop.event_date.max()<='2026-08-15','Post-boundary labels')
    # Keep features and metadata separate; pop labels used ONLY for original membership/fold verification.
    rows=pop[['fight_id','event_id','event_date','method']].merge(f02[['fight_id']+arms['B']['raw_columns']],on='fight_id',validate='one_to_one').sort_values(['event_date','event_id','fight_id'])
    folds=load('chronological_fold_plan.json')['folds'];checks=[]
    explicit=load('ordered_fold_fight_ids.json.xz')['folds']
    for fold in folds:
        year=fold['outer_year'];ids=next(t for t in explicit if t['outer_year']==year);hist=[(year,rows[(rows.event_date<f'{year}-01-01')&rows.method.isin(['KO_TKO','SUBMISSION'])],rows[rows.event_date.str[:4].astype(int)==year],'outer')]
        for inner in fold['inner_folds']:
            iy=inner['validation_year'];hist.append((iy,rows[(rows.event_date<f'{iy}-01-01')&rows.method.isin(['KO_TKO','SUBMISSION'])],rows[(rows.event_date.str[:4].astype(int)==iy)&rows.method.isin(['KO_TKO','SUBMISSION'])],'inner'))
        for cutoff,train,score,kind in hist:
            id_scope=ids if kind=='outer' else next(t for t in ids['inner'] if t['validation_year']==cutoff)
            require(train.fight_id.tolist()==id_scope['training'],'Explicit training ID list drift')
            require(score.fight_id.tolist()==id_scope['scoring' if kind=='outer' else 'validation'],'Explicit scoring ID list drift')
            pp={k:MatrixProbe(k).freeze(train[arms[k]['raw_columns']]) for k in ('B','C')}
            for p in set(pp['B'].medians)&set(pp['C'].medians):require(pp['B'].medians[p]==pp['C'].medians[p],'Shared median mismatch')
            bi,ci=pp['B'].imputed(score),pp['C'].imputed(score)
            for col in set(bi.columns)&set(ci.columns):require(bi[col].equals(ci[col]),'Shared imputed input mismatch')
            expected=old.summarize(train.to_dict('records'));target=fold['training'] if kind=='outer' else next(i['training'] for i in fold['inner_folds'] if i['validation_year']==cutoff)
            require(expected==target,'Training class prevalence/IDs changed')
            s_target=fold['all_eligible_scoring'] if kind=='outer' else next(i['validation'] for i in fold['inner_folds'] if i['validation_year']==cutoff)
            require(old.summarize(score.to_dict('records'))==s_target,'Scoring IDs changed')
            for k,p in pp.items():
                features=score[p.columns];matrix=p.transform(features)
                require(np.allclose(matrix,p.transform(p.swap(features)),atol=1e-12,rtol=0),'Swap matrix mismatch')
                mutated=score.copy();mutated['method']='ARBITRARY';mutated['winner_id']='future';require(np.array_equal(matrix,p.transform(mutated)),'Labels consulted')
                # No score input alters frozen medians/scales; verify with hostile score outlier.
                before=(dict(p.medians),p.mean.copy(),p.scale.copy());hostile=features.copy();hostile[p.pairs[0][0]]=1e9;p.transform(hostile)
                require(p.medians==before[0] and np.array_equal(p.mean,before[1]) and np.array_equal(p.scale,before[2]),'Score affected preprocessing')
                require(np.array_equal(matrix,p.transform(features)),'Nonreproducible matrix')
                # Pair null patterns exercise one-side/both-side imputation including swapped rows.
                missing=features.head(4).copy()
                for a,b in p.pairs:
                    missing.loc[missing.index[:2],a]=np.nan;missing.loc[missing.index[1:3],b]=np.nan
                require(np.allclose(p.transform(missing),p.transform(p.swap(missing)),atol=1e-12,rtol=0),'Missing pattern swap')
            # Original B prefix matches unchanged A preprocessing, tested without training.
            sys.path.insert(0,str(R/'models/mov1'));from implementation_v1 import Preprocessor
            oldpp=Preprocessor('MOV1_MIN').fit(train)
            bm=pp['B'].transform(score);am=oldpp.transform(score)
            require(np.allclose(np.delete(bm,33,axis=1),am,atol=1e-12,rtol=0),'B differs from original MIN prefix')
            subcols=spec['source_concepts']['SUB_PRESSURE']['columns']+spec['source_concepts']['SUB_EXPOSURE']['columns']
            checks.append({'outer_year':year,'phase':kind,'cutoff_year':cutoff,'training_N':len(train),'score_N':len(score),'submission_complete_training_N':int(train[subcols].notna().all(axis=1).sum()),'dimensions':{k:len(arms[k]['predictors'])+len(p.categories) for k,p in pp.items()},'division_categories':pp['B'].categories})
    # Outcome-free numerical composition, not challenger predictions.
    F=np.array([0,.2,.8,1.]);K=np.array([0,.3,.7,1.]);prob=np.c_[F*K,F*(1-K),1-F]
    require(np.max(np.abs(prob.sum(axis=1)-1))<=1e-12 and (prob>=0).all() and (prob<=1).all(),'Composition algebra')
    return {'status':'PASS','predictive_fits':0,'challenger_predictions':0,'post_boundary_outcomes_accessed':False,'F02_physical_SHA256':sha(f02path),'PR123_manifest_SHA256':src['PR123_manifest_sha256'],'frozen_sources_verified':len(src['files']),'original_validator':original,'KD_semantic_equal_rows':nkd,'history_checks':checks,'feature_counts_before_one_hot':{k:len(v['predictors']) for k,v in arms.items()},'checks':['source identities','population and original exact folds','shared source imputation','original MIN prefix preserved','train-only moments/categories','all outer IDs unchanged','swap plus asymmetric nulls','label blindness','KD signed-efficiency semantic equality','SUB/TD formulas and synthetic collision','composition algebra','source artifacts immutable','zero predictive entrypoints']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--f02',required=True);p.add_argument('--output');p.add_argument('--bootstrap-manifest',action='store_true');args=p.parse_args()
    out=validate(args.f02,check_manifest=not args.bootstrap_manifest)
    if args.output:pathlib.Path(args.output).write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':out['status'],'histories':len(out['history_checks']),'fits':0,'sources':out['frozen_sources_verified'],'dimensions':out['feature_counts_before_one_hot']},sort_keys=True))
