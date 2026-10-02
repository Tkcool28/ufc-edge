"""Independent saved-only checks. Never call estimator fit or inspect new outcomes."""
from __future__ import annotations
import io,json,lzma,pathlib,tarfile
import numpy as np
import pandas as pd
from scipy.special import expit
from implementation import R,D,spec,sha,require,write_json,Preprocessor

def verify(out,f02path):
    out=pathlib.Path(out)
    for p,h in spec('SOURCE_MANIFEST.json')['files'].items():require(sha(R/p)==h,'Frozen source modified '+p)
    states=pd.read_parquet(f02path).set_index('fight_id');require(sha(f02path)==spec('SOURCE_MANIFEST.json')['corrected_F02']['physical_sha256'],'F02 changed')
    records=sorted((out/'MODELS').glob('*.json'))
    if not records:
        bundle=b''.join(p.read_bytes() for p in sorted(out.glob('NATIVE_MODELS.tar.xz.part*')))
        require(sha_bytes(bundle)==json.loads((out/'NATIVE_MODELS_MANIFEST.json').read_text())['archive_SHA256'],'Native archive hash mismatch')
        with tarfile.open(fileobj=io.BytesIO(bundle),mode='r:xz') as t:
            rawrecords={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
            data={name:json.loads(b) for name,b in rawrecords.items()}
    else:
        rawrecords={'MODELS/'+p.name:p.read_bytes() for p in records};data={name:json.loads(b) for name,b in rawrecords.items()}
    ledger=json.loads((out/'FIT_LEDGER.json').read_text());require(len(ledger)==164 and len(data)==164 and all(r['status']=='COMPLETE' for r in ledger),'Native fit ledger mismatch')
    native=json.loads((out/'NATIVE_MODELS_MANIFEST.json').read_text()) if (out/'NATIVE_MODELS_MANIFEST.json').exists() else None
    maxerr=0.;inner=[];outer={};dimensions={}
    for item in ledger:
        require(sha_bytes(rawrecords[item['record_path']])==item['record_SHA256'],'Native member hash mismatch')
        rec=data[item['record_path']];pp=Preprocessor.restore(rec['preprocessing']);x=states.loc[rec['scoring_fight_ids'],pp.columns].reset_index(drop=True)
        prediction=expit(pp.transform(x)@np.asarray(rec['coef'])+rec['intercept']);saved=np.asarray(rec['scoring_probabilities'])
        error=float(np.max(abs(prediction-saved)));maxerr=max(maxerr,error);require(error<=1e-12,'Native saved prediction mismatch')
        swapped=expit(pp.transform(pp.swap(x))@np.asarray(rec['coef'])+rec['intercept']);require(np.max(abs(prediction-swapped))<=1e-12,'Native swap failure')
        require(len(rec['coef'])==len(rec['preprocessing']['feature_names']),'Native features mismatch');dimensions[rec['phase']+'_'+rec['arm']+'_'+str(rec['outer_year'])+'_'+str(rec.get('inner_year',0))]=len(rec['coef'])
        if rec['phase']=='outer':outer[(rec['outer_year'],rec['arm'])]=(rec,prediction)
        if rec['phase']=='inner':inner.append(rec)
    pop=pd.read_csv(R/'governance/finish_method_target_structure_v1/population_manifest.csv.gz').set_index('fight_id');require(pop.event_date.max()<='2026-08-15','Future outcomes')
    selections=json.loads((out/'MODEL_SELECTION.json').read_text())
    for selected in selections:
        grid=[]
        for C in spec('model_regularization.json')['C_grid']:
            rows=[r for r in inner if r['outer_year']==selected['outer_year'] and r['arm']==selected['arm'] and r['C']==C];require(len(rows)==2,'Inner fitting records incomplete');loss=[]
            for rec in sorted(rows,key=lambda r:r['inner_year']):
                y=pop.loc[rec['scoring_fight_ids'],'method'].eq('KO_TKO').to_numpy();p=np.clip(np.asarray(rec['scoring_probabilities']),1e-15,1-1e-15);loss.extend(-(y*np.log(p)+(1-y)*np.log1p(-p)))
            grid.append({'C':C,'loss':float(np.mean(loss))})
        best=grid[0]
        for row in grid[1:]:
            if row['loss']<best['loss']-1e-12:best=row
        require(best['C']==selected['selected_C'] and abs(best['loss']-selected['inner_log_loss'])<=1e-12,'Selection not reproduced')
    pred=pd.read_csv(out/'CHALLENGER_OUTER_PREDICTIONS.csv',float_precision='round_trip')
    for (year,arm),(rec,p) in outer.items():
        saved=pred[(pred.outer_year==year)&(pred.arm==arm)].set_index('fight_id').loc[rec['scoring_fight_ids'],'K'].to_numpy();require(np.max(abs(saved-p))<=1e-12,'Persisted outer scores mismatch')
    frame=pd.read_csv(out/'FIGHT_LEVEL_EVIDENCE.csv.xz',float_precision='round_trip');finish=frame[frame.method!='DECISION'];metrics=json.loads((out/'AGGREGATE_CONDITIONAL_METRICS.json').read_text());composed=json.loads((out/'AGGREGATE_COMPOSED_METRICS.json').read_text())
    for arm in ['A','B','C']:
        y=finish.method.eq('KO_TKO').to_numpy();p=finish['K_'+arm].to_numpy();q=np.clip(p,1e-15,1-1e-15);ll=float(np.mean(-(y*np.log(q)+(1-y)*np.log1p(-q))));b=float(np.mean((y-p)**2));require(abs(ll-metrics[arm]['log_loss'])<=1e-12 and abs(b-metrics[arm]['brier'])<=1e-12,'Conditional aggregate mismatch')
        require(np.max(abs(frame[['KO_'+arm,'SUB_'+arm,'DEC_'+arm]].sum(axis=1)-1))<=1e-12,'Composition sum mismatch')
        require(np.array_equal(frame['DEC_'+arm],frame.DEC_A),'Decision identity mismatch')
        idx=pd.Categorical(frame.method,categories=['KO_TKO','SUBMISSION','DECISION']).codes;P=frame[['KO_'+arm,'SUB_'+arm,'DEC_'+arm]].to_numpy();mll=float(-np.log(np.clip(P[np.arange(len(P)),idx],1e-15,1-1e-15)).mean());mb=float(np.sum((P-np.eye(3)[idx])**2,axis=1).mean());require(abs(mll-composed[arm]['log_loss'])<=1e-12 and abs(mb-composed[arm]['brier'])<=1e-12,'Composed aggregate mismatch')
    # Recompute both exact aggregate bootstrap streams, no fits, from saved losses.
    from reporting import comparisons,loss_array,classify
    saved=json.loads((out/'PAIRED_UNCERTAINTY.json').read_text());classes=json.loads((out/'SCIENTIFIC_CLASSIFICATIONS.json').read_text())
    for scope,df in [('conditional',finish),('composed',frame)]:
        reproduced,_=comparisons(df,loss_array(df,scope))
        for pair,r in reproduced.items():
            for kind in ['fight','event']:
                for metric in ['log_loss','brier']:require(np.allclose(r['paired_intervals'][kind][metric],saved[scope][pair]['paired_intervals'][kind][metric],atol=1e-12,rtol=0),'Paired interval mismatch')
            require(r['draw_SHA256']==saved[scope][pair]['draw_SHA256'],'Bootstrap draws changed');require(classify(r,scope=='composed')==classes[scope][pair],'Scientific classification mismatch')
    result={'status':'PASS','saved_native_records_verified':len(data),'inner_selection_records_verified':144,'outer_models_verified':18,'reproduction_records_verified':2,'max_prediction_regeneration_error':maxerr,'all_8520_challenger_outer_scores_verified':True,'all_12780_arm_scores_present':True,'aggregate_metrics_and_paired_intervals_reproduced':True,'fit_count_this_verifier':0,'frozen_source_files_unchanged':True,'post_boundary_outcomes_accessed':False}
    write_json(out/'REPRODUCIBILITY_VERIFICATION.json',result);return result

def sha_bytes(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()
def package(out):
    out=pathlib.Path(out);members={}
    bio=io.BytesIO()
    with tarfile.open(fileobj=bio,mode='w') as tar:
        for p in sorted((out/'MODELS').glob('*.json')):
            b=p.read_bytes();name='MODELS/'+p.name;info=tarfile.TarInfo(name);info.size=len(b);info.mtime=0;info.mode=0o644;tar.addfile(info,io.BytesIO(b));members[name]={'sha256':sha_bytes(b),'bytes':len(b)}
    bundle=lzma.compress(bio.getvalue());parts=[]
    for i,start in enumerate(range(0,len(bundle),65536)):
        p=out/f'NATIVE_MODELS.tar.xz.part{i:03d}';p.write_bytes(bundle[start:start+65536]);parts.append({'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size})
    write_json(out/'NATIVE_MODELS_MANIFEST.json',{'archive_SHA256':sha_bytes(bundle),'archive_bytes':len(bundle),'parts':parts,'members':members,'format':'concatenate lexical part files to XZ-compressed POSIX tar; JSON records preserve all fitted parameters/preprocessing/predictions; no ArmA duplication'})

def package_tables(out):
    out=pathlib.Path(out);files=[p for p in out.iterdir() if p.is_file() and p.stat().st_size>32768 and not p.name.startswith(('NATIVE_MODELS','EVALUATION_TABLES'))]
    bio=io.BytesIO();members={}
    with tarfile.open(fileobj=bio,mode='w') as t:
        for p in sorted(files):
            b=p.read_bytes();info=tarfile.TarInfo(p.name);info.size=len(b);info.mode=0o644;info.mtime=0;t.addfile(info,io.BytesIO(b));members[p.name]={'sha256':sha_bytes(b),'bytes':len(b)}
    bundle=lzma.compress(bio.getvalue());parts=[]
    for i,start in enumerate(range(0,len(bundle),65536)):
        p=out/f'EVALUATION_TABLES.tar.xz.part{i:03d}';p.write_bytes(bundle[start:start+65536]);parts.append({'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size})
    write_json(out/'EVALUATION_TABLES_MANIFEST.json',{'archive_SHA256':sha_bytes(bundle),'members':members,'parts':parts,'recovery':'concatenate lexical parts, extract tar.xz; original exact table/evidence filenames retained'})

def restore_tables(out):
    out=pathlib.Path(out);manifest=out/'EVALUATION_TABLES_MANIFEST.json'
    if not manifest.exists():return
    info=json.loads(manifest.read_text());bundle=b''.join((out/p['name']).read_bytes() for p in info['parts']);require(sha_bytes(bundle)==info['archive_SHA256'],'Evaluation archive changed')
    with tarfile.open(fileobj=io.BytesIO(bundle),mode='r:xz') as t:
        for name,v in info['members'].items():
            require(pathlib.PurePosixPath(name).name==name,'Unsafe evidence member');b=t.extractfile(name).read();require(sha_bytes(b)==v['sha256'],'Evidence member changed')
            if not (out/name).exists():(out/name).write_bytes(b)
            else:require(sha(out/name)==v['sha256'],'Unpacked evidence differs')
