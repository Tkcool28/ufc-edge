"""Preregistered three-arm evaluation; immutable historical outcomes only."""
from __future__ import annotations
import hashlib, json, pathlib, sys
import numpy as np
import pandas as pd
from implementation import R,D,spec,require,sha,write_json,write_csv,binary_loss
sys.path.insert(0,str(R/'models/mov1'))
from evaluation_v1 import binary_metrics,multiclass_metrics,multiclass_losses,gate,join_terrain
ARMS=['A','B','C'];PAIRS=[('C','A'),('B','A'),('C','B')];ARCH=spec('terrain_archetype_evaluation.json')['archetypes'];DIMS=spec('terrain_archetype_evaluation.json')['terrain']['diagnostics']

def metrics_binary(y,p):
    z=binary_metrics(y,p)
    if len(y)<100:z['calibration']={'intercept':None,'slope':None,'status':'SUPPRESSED_N_LT100'}
    return z

def paired_draws(frame,losses,reps=10000):
    """Shared draws across three arms/two metrics; seed reset independently per kind."""
    losses=np.asarray(losses,float);n=len(frame);require(losses.shape==(n,3,2) and n>0,'Bootstrap input shape')
    result={}; hashes={}
    for kind in ['fight','event']:
        rng=np.random.default_rng(17);h=hashlib.sha256();blocks=[]
        if kind=='event':
            events=sorted(frame.event_id.astype(str).unique());ix=pd.Categorical(frame.event_id.astype(str),categories=events).codes
            sums=np.zeros((len(events),3,2));counts=np.bincount(ix,minlength=len(events));np.add.at(sums,ix,losses);size=len(events)
        else:size=n
        for start in range(0,reps,64):
            chosen=rng.integers(0,size,size=(min(64,reps-start),size));h.update(chosen.astype('<i8').tobytes())
            average=losses[chosen].mean(axis=1) if kind=='fight' else sums[chosen].sum(axis=1)/counts[chosen].sum(axis=1)[:,None,None]
            blocks.append(np.stack([average[:,ARMS.index(c)]-average[:,ARMS.index(b)] for c,b in PAIRS],axis=1))
        result[kind]=np.concatenate(blocks);hashes[kind]=h.hexdigest()
    return result,hashes

def comparisons(frame,losses,diagnostic=False,reps=10000):
    draws,hashes=paired_draws(frame,losses,reps);results={}
    for j,(candidate,baseline) in enumerate(PAIRS):
        level=.95 if diagnostic or j==0 else .975;alpha=(1-level)/2
        delta=losses[:,ARMS.index(candidate)]-losses[:,ARMS.index(baseline)];annual=[]
        for year in range(2018,2027):
            mask=frame.outer_year.to_numpy()==year
            annual.append({'year':year,'N':int(mask.sum()),'log_loss_delta':float(delta[mask,0].mean()) if mask.any() else None,'brier_delta':float(delta[mask,1].mean()) if mask.any() else None,'summed_LL_delta':float(delta[mask,0].sum()),'direction':('TIED' if abs(delta[mask,0].mean())<=1e-12 else 'FAVORABLE' if delta[mask,0].mean()<0 else 'UNFAVORABLE') if mask.any() else 'NO_SAMPLE'})
        leave={str(y):float(delta[frame.outer_year.to_numpy()!=y,0].mean()) for y in range(2018,2027) if (frame.outer_year.to_numpy()!=y).any()}
        valid=[a for a in annual if a['N']];total=float(delta[:,0].sum());best=min(valid,key=lambda a:a['summed_LL_delta'])
        results[candidate+'-'+baseline]={'candidate':candidate,'baseline':baseline,'N':len(frame),'confidence_level':level,'replicates':reps,'seed':17,'delta':{'log_loss':float(delta[:,0].mean()),'brier':float(delta[:,1].mean())},'paired_intervals':{kind:{metric:np.quantile(draws[kind][:,j,m],[alpha,1-alpha],method='linear').tolist() for m,metric in enumerate(['log_loss','brier'])} for kind in ['fight','event']},'annual':annual,'favorable_years':sum(a['direction']=='FAVORABLE' for a in annual),'unfavorable_years':sum(a['direction']=='UNFAVORABLE' for a in annual),'tied_years':sum(a['direction']=='TIED' for a in annual),'median_annual_delta':float(np.median([a['log_loss_delta'] for a in valid])),'leave_one_year_out_LL':leave,'strongest_favorable_year':min(valid,key=lambda a:a['log_loss_delta']),'strongest_unfavorable_year':max(valid,key=lambda a:a['log_loss_delta']),'single_best_year_share_of_net_improvement_percent':100*abs(best['summed_LL_delta'])/abs(total) if total<0 else None,'draw_SHA256':hashes,'limitations':'fixed fitted predictions; overlapping training and repeated fighters remain; subgroup panels developmental'}
    return results,draws

def classify(comparison,composed=False):
    d=comparison['delta'];iv=comparison['paired_intervals'];tol=.004 if composed else .002
    supported=d['log_loss']<0 and all(iv[k]['log_loss'][1]<0 for k in iv) and d['brier']<=0 and all(iv[k]['brier'][1]<=tol for k in iv) and comparison['favorable_years']>=6 and comparison['median_annual_delta']<0 and all(v<0 for v in comparison['leave_one_year_out_LL'].values())
    unsupported=(d['log_loss']>0 and all(iv[k]['log_loss'][0]>0 for k in iv)) or (d['brier']>tol and all(iv[k]['brier'][0]>tol for k in iv))
    return 'SUPPORTED_IMPROVEMENT' if supported else 'CURRENT_SPECIFICATION_NOT_SUPPORTED' if unsupported else 'INCONCLUSIVE'

def loss_array(frame,kind):
    y=frame.method.eq('KO_TKO').to_numpy(int)
    return np.stack([np.c_[frame['LL_'+a].to_numpy(),frame['BR_'+a].to_numpy()] if kind=='conditional' else np.c_[frame['MLL_'+a].to_numpy(),frame['MBR_'+a].to_numpy()] for a in ARMS],axis=1)

def cell_records(x,kind,label):
    records=[];finish=x[x.method!='DECISION']
    for arm in ARMS:
        n=len(x);nf=len(finish);cm=metrics_binary(finish.method.eq('KO_TKO'),finish['K_'+arm]) if nf>=25 else None
        tm=multiclass_metrics(x.method,x[['KO_'+arm,'SUB_'+arm,'DEC_'+arm]]) if n>=25 else None
        if tm and n<100:
            for c in tm['classwise'].values():c['calibration']={'intercept':None,'slope':None,'status':'SUPPRESSED_N_LT100'}
        p=finish['K_'+arm].to_numpy();hist=np.histogram(p,bins=np.linspace(0,1,11))[0].tolist() if nf>=25 else None
        row={'kind':kind,'cell':str(label),'arm':arm,'all_bout_N':n,'finish_N':nf,'gate':gate(nf),'all_bout_gate':gate(n),'KO_N':int((finish.method=='KO_TKO').sum()),'SUB_N':int((finish.method=='SUBMISSION').sum()),'year_coverage':x.outer_year.value_counts().sort_index().to_dict(),'division_composition':x.division.value_counts().sort_index().to_dict(),'submission_complete_finish_N':int(finish.sub_complete.sum()),'compact_complete_finish_N':int(finish.compact_complete.sum()),'F_all_mean':float(x.F.mean()) if n else None,'F_finish_mean':float(finish.F.mean()) if nf else None,'K_all_mean':float(x['K_'+arm].mean()) if n>=25 else None,'actual_KO':float(finish.method.eq('KO_TKO').mean()) if nf else None,'actual_SUB':float(finish.method.eq('SUBMISSION').mean()) if nf else None,'mean_KO':float(p.mean()) if nf>=25 else None,'mean_SUB':float((1-p).mean()) if nf>=25 else None,'absolute_calibration_gap':abs(float(p.mean()-finish.method.eq('KO_TKO').mean())) if nf>=25 else None,'conditional_metrics':cm,'composed_metrics':tm,'prediction_quantiles':dict(zip(['min','p10','p25','p50','p75','p90','max'],np.quantile(p,[0,.1,.25,.5,.75,.9,1]).tolist())) if nf>=25 else None,'fixed_10_bin_prediction_histogram':hist}
        records.append(row)
    return records

def pathway_status(comp,base,cand,n):
    d=comp['delta'];gap=cand['absolute_calibration_gap']<base['absolute_calibration_gap'];iv=comp['paired_intervals']
    supportive=d['log_loss']<0 and d['brier']<0 and gap
    if supportive and n>=100 and all(iv[k]['log_loss'][1]<0 for k in iv):return 'SUPPORTED_CELL_IMPROVEMENT'
    if d['log_loss']>0 and d['brier']>0:return 'NOT_SUPPORTED'
    return 'INCONCLUSIVE'

def preservation_status(comp,n):
    if n<100:return 'THIN_DESCRIPTIVE'
    iv=comp['paired_intervals']
    if all(iv[k]['log_loss'][1]<=.01 and iv[k]['brier'][1]<=.005 for k in iv):return 'RETAINED_SUPPORTED'
    if all(iv[k]['log_loss'][0]>.01 for k in iv) or all(iv[k]['brier'][0]>.005 for k in iv):return 'NOT_PRESERVED'
    return 'UNCERTAIN'

def table_md(rows,columns):
    def fmt(v):
        if v is None:return '—'
        if isinstance(v,float):return f'{v:.6f}'
        return str(v).replace('|','/')
    return '\n'.join(['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']+['| '+' | '.join(fmt(r.get(c)) for c in columns)+' |' for r in rows])

def diagnostic_markdown(name,records,comparisons_data):
    rows=[]
    for r in records:
        cm=r['conditional_metrics'];rows.append({'Arm':r['arm'],'N':r['finish_N'],'Actual SUB':r['actual_SUB'],'Predicted SUB':r['mean_SUB'],'Predicted KO':r['mean_KO'],'Abs gap':r['absolute_calibration_gap'],'Log loss':cm['log_loss'] if cm else None,'Brier':cm['brier'] if cm else None})
    lines=['# '+name,'',table_md(rows,['Arm','N','Actual SUB','Predicted SUB','Predicted KO','Abs gap','Log loss','Brier']),'','Individual-fight losses are retained in FIGHT_LEVEL_EVIDENCE.csv.xz. Prediction quantiles/histograms, all annual and completeness strata are in PANEL_METRICS.json; paired annual deltas and both uncertainty variants are in PATHWAY_UNCERTAINTY.json. These overlapping, repeatedly inspected cells are developmental diagnostics.']
    if comparisons_data:
        for pair,c in comparisons_data.items():
            lines += ['',f"{pair}: {c['pathway_status'] if 'pathway_status' in c else c.get('preservation_status','DESCRIPTIVE')}. LL delta {c['delta']['log_loss']:.6f}; Brier delta {c['delta']['brier']:.6f}; fight LL interval {c['paired_intervals']['fight']['log_loss']}; event LL interval {c['paired_intervals']['event']['log_loss']}."]
    lines += ['','Lower average KO alone does not establish correction. Coefficients and directional inputs are associative representations, not causal pathway/hazard estimates.']
    return '\n'.join(lines)+'\n'

def evaluate(population,states,F,pred,out):
    out=pathlib.Path(out);join_terrain(population)
    frame=population[population.event_date>='2018-01-01'].copy().sort_values(['event_date','event_id','fight_id']).reset_index(drop=True);frame['outer_year']=frame.event_date.str[:4].astype(int)
    specf=spec('feature_specifications.json');subs=specf['source_concepts']['SUB_PRESSURE']['columns']+specf['source_concepts']['SUB_EXPOSURE']['columns'];compact=[c for c in specf['arms']['C']['raw_columns'] if c.startswith(('f1__','f2__','mx__'))]
    frame['sub_complete']=states.loc[frame.fight_id,subs].notna().all(axis=1).to_numpy();frame['compact_complete']=states.loc[frame.fight_id,compact].notna().all(axis=1).to_numpy()
    prior=states.loc[frame.fight_id,['f1__fs__prior_fight_count__career__raw','f2__fs__prior_fight_count__career__raw']];minimum=prior.min(axis=1,skipna=False);frame['experience_group']=pd.cut(minimum,[-1,0,2,7,np.inf],labels=['0','1-2','3-7','8+']).astype('object').fillna('UNKNOWN').to_numpy()
    frame['division']=frame.division.astype(str);frame['F']=F.set_index('fight_id').loc[frame.fight_id,'probability'].to_numpy()
    for arm in ARMS:
        p=pred[pred.arm==arm];require(set(p.fight_id)==set(frame.fight_id),'Evaluation arms unmatched')
        K=p.set_index('fight_id').loc[frame.fight_id,'K'].to_numpy(float);frame['K_'+arm]=K;frame['LL_'+arm]=binary_loss(frame.method.eq('KO_TKO'),K);frame['BR_'+arm]=(K-frame.method.eq('KO_TKO').to_numpy())**2
        frame['KO_'+arm]=frame.F*K;frame['SUB_'+arm]=frame.F*(1-K);frame['DEC_'+arm]=1-frame.F
        probs=frame[['KO_'+arm,'SUB_'+arm,'DEC_'+arm]].to_numpy();require(np.isfinite(probs).all() and (probs>=0).all() and (probs<=1).all() and np.max(abs(probs.sum(axis=1)-1))<=1e-12,'Invalid composed probabilities')
        frame['MLL_'+arm]=multiclass_losses(frame.method,probs);yy=np.eye(3)[pd.Categorical(frame.method,categories=['KO_TKO','SUBMISSION','DECISION']).codes];frame['MBR_'+arm]=np.sum((probs-yy)**2,axis=1)
    require(np.array_equal(frame.DEC_A,frame.DEC_B) and np.array_equal(frame.DEC_A,frame.DEC_C),'Decision node changed')
    finish=frame[frame.method!='DECISION'].copy();require(len(frame)==4260 and len(finish)==2115,'Evaluation count drift')
    # Decision rows never get conditional losses in the persisted evidence.
    frame.loc[frame.method=='DECISION',[p+a for p in ['LL_','BR_'] for a in ARMS]]=np.nan
    conditional={a:metrics_binary(finish.method.eq('KO_TKO'),finish['K_'+a]) for a in ARMS};composed={a:multiclass_metrics(frame.method,frame[['KO_'+a,'SUB_'+a,'DEC_'+a]]) for a in ARMS}
    cc,cdraw=comparisons(finish,loss_array(finish,'conditional'));mc,mdraw=comparisons(frame,loss_array(frame,'composed'))
    classification={'conditional':{p:classify(v) for p,v in cc.items()},'composed':{p:classify(v,True) for p,v in mc.items()},'pathways':{},'preservation':{},'scope':'historical developmental only; no automatic production promotion'}
    write_json(out/'AGGREGATE_CONDITIONAL_METRICS.json',conditional);write_json(out/'AGGREGATE_COMPOSED_METRICS.json',composed);write_json(out/'PAIRED_UNCERTAINTY.json',{'conditional':cc,'composed':mc})
    bootstrap_rows=[]
    for scope,draws in [('conditional',cdraw),('composed',mdraw)]:
        for kind,z in draws.items():
            for i,pair in enumerate(['C-A','B-A','C-B']):
                bootstrap_rows.extend({'scope':scope,'kind':kind,'comparison':pair,'replicate':k,'LL_delta':float(v[0]),'Brier_delta':float(v[1])} for k,v in enumerate(z[:,i]))
    pd.DataFrame(bootstrap_rows).to_csv(out/'BOOTSTRAP_DISTRIBUTIONS.csv.xz',index=False,float_format='%.17g',compression='xz')
    records=[];panels=[('aggregate','ALL',frame)]
    for year,x in frame.groupby('outer_year',sort=True):panels.append(('year',str(year),x))
    divisions=spec('terrain_archetype_evaluation.json')['normalized_weight_classes']
    for d in divisions:
        x=frame[frame.division==d];panels.append(('division',d,x))
        for y in range(2018,2027):panels.append(('division_year',d+'|'+str(y),x[x.outer_year==y]))
    for dim in DIMS+['scheduled_rounds','experience_group','sub_complete','compact_complete']:
        for v,x in frame.groupby(dim,dropna=False,sort=True):
            label='UNKNOWN' if pd.isna(v) else str(v);panels.append((dim,label,x))
            for year,q in x.groupby('outer_year',sort=True):panels.append((dim+'_year',label+'|'+str(year),q))
    for arch in ARCH:
        for status in ['MATCH','NO_MATCH','UNASSIGNABLE']:
            x=frame[frame[arch]==status];panels.append(('archetype',arch+'|'+status,x))
            for y in range(2018,2027):panels.append(('archetype_year',arch+'|'+status+'|'+str(y),x[x.outer_year==y]))
            for d in divisions:panels.append(('division_archetype',d+'|'+arch+'|'+status,x[x.division==d]))
            for complete in [True,False]:panels.append(('archetype_submission_completeness',arch+'|'+status+'|'+str(complete),x[x.sub_complete==complete]));panels.append(('archetype_compact_completeness',arch+'|'+status+'|'+str(complete),x[x.compact_complete==complete]))
    for kind,label,x in panels:records.extend(cell_records(x,kind,label))
    write_json(out/'PANEL_METRICS.json',records)
    flat=[]
    for r in records:
        cm=r['conditional_metrics'] or {};flat.append({k:r[k] for k in ['kind','cell','arm','all_bout_N','finish_N','gate','actual_KO','actual_SUB','mean_KO','mean_SUB','absolute_calibration_gap','submission_complete_finish_N','compact_complete_finish_N']}|{'conditional_log_loss':cm.get('log_loss'),'conditional_brier':cm.get('brier'),'ECE':cm.get('ECE')})
    write_csv(out/'PANEL_COMPARISONS.csv',pd.DataFrame(flat))
    primary=[a for a in ARCH if a.startswith(('A1_','A2_','A4_','B1_','B2_','B3_','B4_','B5_'))];special={a:frame[frame[a]=='MATCH'] for a in primary};special.update({d:frame[frame.division==d] for d in ['Heavyweight','Light Heavyweight']})
    diagnostics={}
    for cell,x in special.items():
        q=x[x.method!='DECISION'];n=len(q);recs=cell_records(x,'focused',cell);iv=None
        if n>=25:
            iv,_=comparisons(q,loss_array(q,'conditional'),diagnostic=True)
            for pair,c in iv.items():
                candidate,baseline=pair.split('-');base=next(r for r in recs if r['arm']==baseline);cand=next(r for r in recs if r['arm']==candidate)
                if cell.startswith(('B3_','B5_')):c['pathway_status']=pathway_status(c,base,cand,n);classification['pathways'].setdefault(cell,{})[pair]=c['pathway_status']
                if cell.startswith(('A1_','A2_','A4_')) or cell in ['Heavyweight','Light Heavyweight']:c['preservation_status']=preservation_status(c,n);classification['preservation'].setdefault(cell,{})[pair]=c['preservation_status']
        diagnostics[cell]={'records':recs,'comparisons':iv,'finish_N':n}
        if cell.startswith(('B3_','B5_')):(out/('FOCUSED_'+cell[:2]+'_DIAGNOSTIC.md')).write_text(diagnostic_markdown(cell,recs,iv))
    write_json(out/'PATHWAY_UNCERTAINTY.json',diagnostics);write_json(out/'SCIENTIFIC_CLASSIFICATIONS.json',classification)
    # Retain raw source values, original nulls and per-literal completeness, never just group flags.
    sourceframe=frame[['fight_id','event_id','event_date','outer_year','method','sub_complete','compact_complete']].merge(states.reset_index(),on='fight_id',validate='one_to_one');sourceframe.to_csv(out/'RAW_SOURCE_COMPLETENESS.csv.xz',index=False,float_format='%.17g',compression='xz')
    frame.to_csv(out/'FIGHT_LEVEL_EVIDENCE.csv.xz',index=False,float_format='%.17g',compression='xz')
    frame[[c for c in frame if c in ['fight_id','event_id','event_date','outer_year','method','F'] or c.startswith(('K_','KO_','SUB_','DEC_'))]].to_csv(out/'COMPOSED_OUTER_PREDICTIONS.csv',index=False,float_format='%.17g')
    # Full frozen context report partitions and all source null counts by history/group.
    nulls=[]
    for kind,label,x in panels:
        if kind in ['aggregate','year','division','archetype','sub_complete','compact_complete']:
            raw=states.loc[x.fight_id]
            nulls.append({'kind':kind,'cell':label,'all_N':len(x),'finish_N':int(x.method.ne('DECISION').sum()),'null_counts_all':raw.isna().sum().to_dict(),'null_counts_finishes':raw.loc[x.loc[x.method!='DECISION','fight_id']].isna().sum().to_dict()})
    write_json(out/'LITERAL_COMPLETENESS_DIAGNOSTICS.json',nulls)
    for prefix,kinds in [('DIVISION_REPORT',['division','division_year']),('VALIDATION_TERRAIN_REPORT',DIMS),('MISSINGNESS_COMPLETENESS_REPORT',['sub_complete','compact_complete','archetype_submission_completeness','archetype_compact_completeness']),('ALL_15_ARCHETYPE_REPORT',['archetype']),('ANNUAL_COMPARISON',['year']),('B1_B5_PATHWAY_COMPARISON',['archetype'])]:
        rows=[r for r in flat if r['kind'] in kinds and (prefix!='B1_B5_PATHWAY_COMPARISON' or r['cell'].startswith(('B1_','B2_','B3_','B4_','B5_')))]
        (out/(prefix+'.md')).write_text('# '+prefix.replace('_',' ')+'\n\n'+table_md(rows,['cell','arm','finish_N','gate','actual_SUB','mean_SUB','absolute_calibration_gap','conditional_log_loss','conditional_brier'])+'\n')
    preservation=[]
    for cell,d in diagnostics.items():
        if cell in classification['preservation']:
            preservation.extend({'Cell':cell,'Comparison':p,'Status':c['preservation_status'],'LL delta':c['delta']['log_loss'],'Brier delta':c['delta']['brier']} for p,c in d['comparisons'].items())
    (out/'STRIKING_PRESERVATION_REPORT.md').write_text('# Striking preservation\n\n'+table_md(preservation,['Cell','Comparison','Status','LL delta','Brier delta'])+'\n')
    gapmax=0.;clipping=[]
    for candidate,base in PAIRS:
        delta=frame['MLL_'+candidate]-frame['MLL_'+base];expected=np.zeros(len(frame));mask=frame.method!='DECISION';expected[mask]=frame.loc[mask,'LL_'+candidate]-frame.loc[mask,'LL_'+base];err=float(np.max(abs(delta-expected)));gapmax=max(gapmax,err)
        if err>1e-12:clipping.append({'comparison':candidate+'-'+base,'max_error':err})
    write_json(out/'COMPOSITION_VALIDATION.json',{'status':'PASS','N':4260,'max_sum_error':float(max(np.max(abs(frame[['KO_'+a,'SUB_'+a,'DEC_'+a]].sum(axis=1)-1)) for a in ARMS)),'decision_probabilities_identical':True,'conditional_composed_LL_identity_max_error':gapmax,'log_clipping_exceptions':clipping})
    aggregate_rows=[{'Arm':a,'Conditional LL':conditional[a]['log_loss'],'Conditional Brier':conditional[a]['brier'],'ECE':conditional[a]['ECE'],'Calibration intercept':conditional[a]['calibration']['intercept'],'Calibration slope':conditional[a]['calibration']['slope'],'AUC':conditional[a]['ROC_AUC'],'Composed LL':composed[a]['log_loss'],'Composed Brier':composed[a]['brier']} for a in ARMS]
    comp_rows=[{'Comparison':p,'Classification':classification['conditional'][p],'LL delta':v['delta']['log_loss'],'Brier delta':v['delta']['brier'],'Favorable years':v['favorable_years']} for p,v in cc.items()]
    lines=['# MOV1 three-arm directional challenger V1 — scientific interpretation','',table_md(aggregate_rows,list(aggregate_rows[0])),'',table_md(comp_rows,list(comp_rows[0])),'','## Representation isolation: B versus A','',classification['conditional']['B-A']+'. This tests only the appended submission cross-sum, under independently inner-selected regularization.','', '## Compact model: C versus A','',classification['conditional']['C-A']+'. The primary conclusion applies the frozen pooled/paired/Brier/annual and leave-one-year-out criteria.','', '## Compact versus augmented MIN: C versus B','',classification['conditional']['C-B']+'. Multiple representation choices change; no removed-feature causal attribution.']
    for p,v in cc.items():lines+=['',f"{p}: fight LL interval {v['paired_intervals']['fight']['log_loss']}; event LL interval {v['paired_intervals']['event']['log_loss']}; {v['favorable_years']}/9 favorable years; median annual delta {v['median_annual_delta']:.6f}; leave-one-year-out deltas {v['leave_one_year_out_LL']}. All unfavorable and partial2026 folds are retained."]
    for cell,d in diagnostics.items():
        if cell.startswith(('B3_','B5_')):lines+=['','## '+cell,'',diagnostic_markdown(cell,d['records'],d['comparisons'])]
    lines+=['','## Striking and division preservation','',table_md(preservation,['Cell','Comparison','Status','LL delta','Brier delta']),'','All13 governed division reports retain men/women Flyweight and women Strawweight separately. Detailed annual/terrain/archetype/completeness cells, including thin/empty/unknown samples and all15 archetypes, remain in the full tables. No probability shifts or feature changes follow from a preservation failure.','', '## Complete system','',table_md([{'Comparison':p,'Classification':classification['composed'][p],'LL delta':v['delta']['log_loss'],'Summed Brier delta':v['delta']['brier']} for p,v in mc.items()],['Comparison','Classification','LL delta','Summed Brier delta']),'','Decision probabilities are exactly unchanged. Conditional and composed LL differences are algebraically related; multiclass Brier and classwise calibration add distinct evidence.','', '## Forward confirmation and next milestone','', 'Historical results remain developmental, motivated by repeatedly inspected samples. Conditional2026 fixed-model records are saved; independent confirmation requires prospective pre-event source/prediction snapshots and sealed outcomes under the existing protocol. No forward predictions or enrollment performed here. Forward complete-system enrollment remains BLOCKED_MISSING_FROZEN_MOV0_RECORD; no MOV0 retraining or replacement. The next scientific milestone is prospective confirmation of these frozen specifications, alongside separately authorized preservation-only MOV0 record recovery if composed confirmation is desired. If compact specification is not supported, retain the reference and treat alternatives as requiring a new preregistration rather than repairing C posthoc.','', '## Limitations','', 'Paired bootstrap conditions on fixed fitted OOF predictions; event clustering does not eliminate repeat-fighter dependence or overlapping training. Sparse calibration/AUC/metrics are suppressed under frozen gates; archetype overlap and previous inspection limit group inference. Source exposure is not measured causal susceptibility. Coefficients are associations, not mechanistic/hazard estimates. No sportsbook/ROI/EV, simulator, recalibration or automatic model promotion.']
    (out/'SCIENTIFIC_INTERPRETATION_REPORT.md').write_text('\n'.join(lines).rstrip()+'\n')
    (out/'AGGREGATE_COMPARISON.md').write_text('# Conditional and composed aggregates\n\n'+table_md(aggregate_rows,list(aggregate_rows[0]))+'\n')
    (out/'PAIRED_UNCERTAINTY_REPORT.md').write_text('# Paired uncertainty\n\n'+table_md([{'Scope':scope,'Comparison':p,'Confidence':v['confidence_level'],'LL delta':v['delta']['log_loss'],'Fight interval':v['paired_intervals']['fight']['log_loss'],'Event interval':v['paired_intervals']['event']['log_loss'],'Brier fight':v['paired_intervals']['fight']['brier'],'Brier event':v['paired_intervals']['event']['brier']} for scope,data in [('conditional',cc),('composed',mc)] for p,v in data.items()],['Scope','Comparison','Confidence','LL delta','Fight interval','Event interval','Brier fight','Brier event'])+'\n')
    (out/'COMPLETE_SYSTEM_COMPOSITION_REPORT.md').write_text('# Complete MOV0 × MOV1 system\n\n'+table_md([{'Arm':a,'Log loss':composed[a]['log_loss'],'Summed Brier':composed[a]['brier'],'KO ECE':composed[a]['classwise']['KO_TKO']['ECE'],'SUB ECE':composed[a]['classwise']['SUBMISSION']['ECE'],'DEC ECE':composed[a]['classwise']['DECISION']['ECE']} for a in ARMS],['Arm','Log loss','Summed Brier','KO ECE','SUB ECE','DEC ECE'])+'\n\nDecision probabilities identical. Classwise intercept/slope/reliability and every annual result are retained in the machine-readable aggregate and panel metrics.\n')
    write_json(out/'FORWARD_CONFIRMATION_READINESS.json',{'conditional_status':'FROZEN_MODELS_AVAILABLE_NOT_ENROLLED','fixed_year':2026,'arms':{'A':'existing models/mov1/run_v1/MODELS/2026_MOV1_MIN.json',**{a:{'record_path':r['record_path'],'SHA256':r['record_SHA256']} for a in ['B','C'] for r in json.loads((out/'FIT_LEDGER.json').read_text()) if r['phase']=='outer' and r['outer_year']==2026 and r['arm']==a}},'enrollment_rule':spec('forward_confirmation_protocol.json')['entry'],'no_retrospective_forward_predictions':True,'post_boundary_outcomes_accessed':False,'forward_composed_status':'BLOCKED_MISSING_FROZEN_MOV0_RECORD','historical_composed_status':'PASS','MOV0_refits':0,'promotion':'NONE'})
    (out/'FORWARD_CONFIRMATION_READINESS_REPORT.md').write_text('# Forward confirmation readiness\n\nConditional fixed outer2026 A/B/C records are preserved, trained only through2025. No prospective cohort enrolled and no post-Aug15 outcomes inspected. Enrollment follows the original next-UTC-day rule after the latest contract/model freeze and October2. Pre-event governed source versions and prediction manifests must precede every scored event. No refits/calibration/retrospective prediction substitution.\n\nProspective composition: BLOCKED_MISSING_FROZEN_MOV0_RECORD. Historical composition uses the exact frozen4260 OOF F values. No MOV0 recovery, retraining or substitution was attempted. Separate frozen-record recovery remains required.\n')
    return classification
