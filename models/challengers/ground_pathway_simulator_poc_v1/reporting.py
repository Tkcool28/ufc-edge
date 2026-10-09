"""Fixed reporting and gates. Never adjusts probabilities."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit,logit
from scipy.optimize import minimize
from run import js,csv
MODELS=['A','C','identity','population','pooled_conversion','return_half','return_double']
CELLS=['B3_TD_ACCESS_PLUS_SUB_PRESSURE','B5_SUB_PRESSURE_VS_SUB_VULNERABILITY','A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE','A2_BOTH_HIGH_DAMAGE_EXCHANGE','A4_KO_HISTORY_VS_KO_VULNERABILITY']

def calibration(y,p):
    if len(y)<100 or min(y.sum(),len(y)-y.sum())<25:return {'status':'INSUFFICIENT_SUPPORT'}
    x=logit(np.clip(p,1e-10,1-1e-10))
    def objective(b):
        z=b[0]+b[1]*x
        return np.logaddexp(0,z).sum()-np.dot(y,z)
    def jac(b):
        r=expit(b[0]+b[1]*x)-y
        return np.array([r.sum(),np.dot(r,x)])
    fit=minimize(objective,[0.,1.],jac=jac,method='BFGS',options={'gtol':1e-7,'maxiter':1000})
    converged=fit.success or np.max(np.abs(jac(fit.x)))<1e-5
    return {'status':'CONVERGED' if converged else 'NOT_CONVERGED','intercept':float(fit.x[0]),'slope':float(fit.x[1])}

def loss(e,m):
    y=e.method.eq('KO_TKO').to_numpy(dtype=float);k=np.clip(e['K_'+m].to_numpy(),1e-12,1-1e-12)
    p=np.clip(e[['KO_'+m,'SUB_'+m,'DEC_'+m]].to_numpy(),1e-12,1)
    target=np.array([{'KO_TKO':0,'SUBMISSION':1,'DECISION':2}[x] for x in e.method])
    ll=-(y*np.log(k)+(1-y)*np.log1p(-k));br=(k-y)**2
    mask=e.method.ne('DECISION').to_numpy();ll[~mask]=np.nan;br[~mask]=np.nan
    return {'conditional_ll':ll,'conditional_brier':br,'multiclass_ll':-np.log(p[np.arange(len(e)),target]),
      'summed_brier':((p-np.eye(3)[target])**2).sum(axis=1)}

def metrics(e,m):
    mask=e.method.ne('DECISION');n=int(mask.sum());l=loss(e,m)
    d={'N':len(e),'N_finish':n}
    for key,v in l.items():d[key]=float(np.nanmean(v)) if (n if key.startswith('conditional') else len(e))>=25 else None
    for kind in ['KO','SUB','DEC']:
        y=e.method.eq({'KO':'KO_TKO','SUB':'SUBMISSION','DEC':'DECISION'}[kind]).to_numpy(dtype=float)
        p=e[kind+'_'+m].to_numpy()
        if len(e)>=25:
            d['mean_'+kind]=float(p.mean());d['actual_'+kind]=float(y.mean());d['calibration_'+kind]=calibration(y,p)
    if n>=25:
        k=e.loc[mask,'K_'+m].to_numpy();y=e.loc[mask,'method'].eq('KO_TKO').to_numpy(dtype=float)
        d['mean_conditional_SUB']=float((1-k).mean());d['actual_conditional_SUB']=float((1-y).mean())
        d['conditional_calibration']=calibration(y,k)
    return d

def paired(e,a,b,key,cluster):
    la=loss(e,a)[key];lb=loss(e,b)[key];valid=np.isfinite(la)&np.isfinite(lb)
    d=la[valid]-lb[valid]
    if len(d)<25:return {'N':len(d),'status':'INSUFFICIENT_SUPPORT'}
    ids=e.loc[valid,'event_id'].to_numpy() if cluster=='event' else np.arange(len(d))
    z=pd.DataFrame({'id':ids,'difference':d}).groupby('id').difference.agg(['sum','count'])
    vals=z.to_numpy();rng=np.random.default_rng(161163);draws=[]
    for _ in range(2000):
        sample=vals[rng.integers(0,len(vals),len(vals))]
        draws.append(sample[:,0].sum()/sample[:,1].sum())
    lo,hi=np.quantile(draws,[.025,.975])
    return {'N':len(d),'clusters':len(vals),'mean_difference':float(d.mean()),'ci_low':float(lo),'ci_high':float(hi),'draws':2000,'cluster':cluster}

def table(rows,cols):
    def value(x):
        if isinstance(x,float):return f'{x:.6f}'
        return 'NA' if x is None else str(x)
    return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+''.join('| '+' | '.join(value(r.get(c)) for c in cols)+' |\n' for r in rows)

def md(out,name,title,body):
    (out/name).write_text('# '+title+'\n\n'+body.rstrip()+'\n')

def report(e,out):
    aggregate={m:metrics(e,m) for m in MODELS}
    annual=[];cells=[];uncertainty=[];reliability=[]
    for year,g in e.groupby('outer_year'):
        for m in MODELS:annual.append({'year':int(year),'model':m,**metrics(g,m)})
    for cell in CELLS:
        g=e[e[cell].eq('MATCH')]
        for m in MODELS:cells.append({'cell':cell.split('_')[0],'model':m,**metrics(g,m)})
        for metric in ['conditional_ll','conditional_brier']:
            uncertainty.append({'scope':cell.split('_')[0],'comparison':'identity-C','metric':metric,**paired(g,'identity','C',metric,'event')})
    for comparator in ['A','C','population']:
        for metric in ['conditional_ll','conditional_brier','multiclass_ll','summed_brier']:
            for cluster in ['event','fight']:
                uncertainty.append({'scope':'ALL','comparison':'identity-'+comparator,'metric':metric,**paired(e,'identity',comparator,metric,cluster)})
    for m in MODELS:
        for kind in ['conditional_KO','KO','SUB','DEC']:
            g=e[e.method.ne('DECISION')] if kind=='conditional_KO' else e
            p=g['K_'+m].to_numpy() if kind=='conditional_KO' else g[kind+'_'+m].to_numpy()
            y=g.method.eq({'conditional_KO':'KO_TKO','KO':'KO_TKO','SUB':'SUBMISSION','DEC':'DECISION'}[kind]).to_numpy(dtype=float)
            bins=np.minimum((p*10).astype(int),9)
            for j in range(10):
                z=bins==j;n=int(z.sum());reliability.append({'model':m,'kind':kind,'bin':j,'lower':j/10,'upper':(j+1)/10,'N':n,
                  'mean_prediction':float(p[z].mean()) if n>=25 else None,'actual_frequency':float(y[z].mean()) if n>=25 else None})
    def upper(scope,comp,metric):
        r=next(x for x in uncertainty if x['scope']==scope and x['comparison']==comp and x['metric']==metric and x.get('cluster')=='event')
        return r.get('ci_high',float('inf'))
    a=aggregate['identity'];c=aggregate['C'];pop=aggregate['population']
    n_years=sum(metrics(g,'identity')['conditional_ll']<metrics(g,'C')['conditional_ll'] for _,g in e.groupby('outer_year'))
    pathway_pass=[];preservation=[]
    for cell in ['B3','B5','A1','A2','A4']:
        p=next(x for x in cells if x['cell']==cell and x['model']=='identity');r=next(x for x in cells if x['cell']==cell and x['model']=='C')
        supported=p['N_finish']>=25
        dl=p['conditional_ll']-r['conditional_ll'] if supported else None
        db=p['conditional_brier']-r['conditional_brier'] if supported else None
        if cell in ['B3','B5']:pathway_pass.append(supported and dl<=-.005 and db<=.002 and upper(cell,'identity-C','conditional_ll')<0)
        else:preservation.append(supported and dl<=.01 and db<=.005)
    cal=all(abs(a['mean_'+k]-a['actual_'+k])<=.03 and a['calibration_'+k].get('status')=='CONVERGED' and .75<=a['calibration_'+k]['slope']<=1.25 for k in ['KO','SUB','DEC'])
    gates={'conditional_LL':a['conditional_ll']-c['conditional_ll']<=-.005 and upper('ALL','identity-C','conditional_ll')<0,
      'conditional_Brier':a['conditional_brier']-c['conditional_brier']<=.002,
      'chronological_persistence':n_years>=6,'B3_or_B5':any(pathway_pass),'striking_preservation':all(preservation),
      'three_way_and_calibration':a['multiclass_ll']-c['multiclass_ll']<=.005 and a['summed_brier']-c['summed_brier']<=.005 and cal,
      'identity_contribution':a['conditional_ll']-pop['conditional_ll']<=-.005 and upper('ALL','identity-population','conditional_ll')<0}
    classification='A' if all(gates.values()) else ('C' if a['conditional_ll']>=pop['conditional_ll'] or a['conditional_brier']>=pop['conditional_brier'] else 'B')
    decision={'classification':classification,'gates':{k:bool(v) for k,v in gates.items()},'favorable_years_vs_C':n_years,
      'recommended_next_milestone':'UFC_EDGE_GROUND_PATHWAY_POC_MEASUREMENT_AND_HAZARD_AUDIT_V1',
      'interpretation_limit':'Single preregistered assumption-driven model; cannot identify positional necessity or disprove mechanistic modeling.'}
    js(out/'AGGREGATE_RESULTS.json',aggregate);js(out/'GATE_DECISIONS.json',decision)
    csv(out/'annual.csv',pd.DataFrame(annual));csv(out/'pathways.csv',pd.DataFrame(cells));csv(out/'paired_uncertainty.csv',pd.DataFrame(uncertainty));csv(out/'reliability.csv',pd.DataFrame(reliability))
    summary=table([{'model':m,**v} for m,v in aggregate.items()],['model','N_finish','conditional_ll','conditional_brier','multiclass_ll','summed_brier','mean_conditional_SUB'])
    md(out,'CONDITIONAL_MOV_RESULTS.md','Conditional finish-method results',summary+'\nAll standard finishes; lower individual LL/Brier is better. Primary is identity, sensitivities are not selected. Paired event/fight uncertainty saved in paired_uncertainty.csv. No calibration applied.')
    md(out,'THREE_WAY_RESULTS.md','External MOV0 three-way composition',summary+'\nF is unchanged archived MOV0. Raw simulator probabilities are separately saved diagnostic outputs and are not promoted. Composition has exact unit sum.')
    md(out,'IDENTITY_ABLATION_RESULTS.md','Continuous identity contribution',summary+'\nPopulation ablation replaces all ground abilities and defensive counterparts with division means, retaining identical standing pathway. Pooled-conversion ablation changes only SUB conversion. This evaluates the whole ground identity package, not an isolated dimension.')
    md(out,'B3_B5_PATHWAY_RESULTS.md','Frozen submission cells',table([x for x in cells if x['cell'] in ['B3','B5']],['cell','model','N_finish','conditional_ll','conditional_brier','mean_conditional_SUB','actual_conditional_SUB'])+'\nMemberships unchanged; subgroup event uncertainty saved. Calibration gap alone is not success.')
    md(out,'STRIKING_PRESERVATION.md','Frozen striking cells',table([x for x in cells if x['cell'] in ['A1','A2','A4']],['cell','model','N_finish','conditional_ll','conditional_brier','mean_conditional_SUB','actual_conditional_SUB']))
    md(out,'ANNUAL_PERSISTENCE.md','Every frozen outer year',table(annual,['year','model','N_finish','conditional_ll','conditional_brier','multiclass_ll','summed_brier'])+f'\nIdentity improves conditional LL versus C in {n_years}/9 years. 2026 partial through Aug15. No years omitted.')
    calrows=[{'model':m,'class':k,'predicted':v['mean_'+k],'actual':v['actual_'+k],**v['calibration_'+k]} for m,v in aggregate.items() for k in ['KO','SUB','DEC']]
    md(out,'CALIBRATION_FINDINGS.md','Calibration diagnostics',table(calrows,['model','class','predicted','actual','status','intercept','slope'])+'\nTen fixed reliability bins in reliability.csv; N<25 bin means withheld. Diagnostic one-vs-rest fits are not prediction wrappers.')
    states=pd.read_csv(out/'fighter_abilities.csv.gz');dist=[]
    for year,g in [('ALL',states)]+list(states.groupby('outer_year')):
        for k in ['access','control','submission','gnp']:
            row={'year':year,'ability':k,'states':len(g),'supported':int(g[k+'_supported'].sum()),'debut_share':float(g.prior_fights.eq(0).mean()),'median_effective_support':float(g[k+'_effective_support'].median())}
            row.update({'p'+str(q):float(g[k].quantile(q/100)) for q in [10,25,50,75,90]});dist.append(row)
    csv(out/'identity_distributions.csv',pd.DataFrame(dist))
    md(out,'FIGHTER_IDENTITY_SANITY.md','Full-population continuous abilities',table(dist[:4],['year','ability','states','supported','debut_share','median_effective_support','p10','p50','p90'])+'\nState-weighted population, not cherry-picked named fighters or independent repeated fighter observations. Annual distributions saved. No labels assigned. Actual support retained even with population prior.')
    md(out,'SCIENTIFIC_INTERPRETATION.md','Scientific interpretation',f"Classification **{classification}**.\n\n"+table([{'gate':k,'passed':v} for k,v in gates.items()],['gate','passed'])+'\n'+summary+'\nA valid negative result is not invalid implementation. Neither D (positional necessity) nor the exact source of error is identified. CONTROL is decision-selected and includes clinch, activities use all-history exposure, recorded attempts omit some finishes, ground KO allocation is latent and return is proxy-only. TD-only entry omits knockdown entry and pulling guard; active-ground actor approximates an unobserved process. These are specific possible mechanisms of failure, not proven causes. Historical folds have been examined in previous development; no prospective confirmation accessed.\n\nNext milestone: **'+decision['recommended_next_milestone']+'** — diagnostic only: audit coherent SUB-attempt support, decision-control selection, entry coverage and latent KO attribution before authorizing any new frozen challenger; no unrestricted feature search, detailed positions, paid data or promotion.')
