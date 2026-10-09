"""Strict event-date histories; fold-boundary population priors, no outcome fitting."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'tools/audits'))
import audit_grappling_identity_v1 as lineage
import grappling_identity_separation_v1 as separation

# name: raw numerator, denominator, decision-only, numerator scale, prior strength
DEFINITIONS={
 'access':('takedowns_attempted','elapsed_min',False,1.,30.),
 'control':('control_sec','elapsed_min',True,1/60,30.),
 'submission':('submission_attempts','elapsed_min',False,1.,30.),
 'gnp':('sig_ground_attempted','elapsed_min',False,1.,60.),
 'td_conversion':('takedowns_landed','takedowns_attempted',False,1.,20.),
 'td_resistance':('opponent_failed_td','opponent_td_attempts',False,1.,20.),
 'control_allowed':('control_sec_allowed','elapsed_min',True,1/60,30.),
 'sub_faced':('submission_attempts_faced','elapsed_min',False,1.,30.),
 'ground_allowed':('ground_attempts_allowed','elapsed_min',False,1.,60.),
 'sub_conversion':('conversion_success','conversion_attempts',False,1.,50.),
 'sub_conversion_allowed':('conversion_loss','conversion_faced',False,1.,50.),
 'ko_created':('ko_win','elapsed_min',False,1.,60.),
 'ko_allowed':('ko_loss','elapsed_min',False,1.,60.),
 'kd_created':('knockdowns','elapsed_min',False,1.,30.),
 'kd_allowed':('knockdowns_allowed','elapsed_min',False,1.,30.),
}
BOUNDED={'control','control_allowed','td_conversion','td_resistance','sub_conversion','sub_conversion_allowed'}

def load_bouts(verify=True):
    if verify: separation.verify_inputs()
    b=lineage.load()
    stats=pd.read_csv(R/'data/canonical/v0/fighter_round_stats.csv',usecols=['fight_id','fighter_id','round','knockdowns'])
    stats=stats[stats.fight_id.isin(b.fight_id)]
    agg=stats.groupby(['fight_id','fighter_id']).knockdowns.agg(['sum','count'])
    b['knockdowns']=[agg.loc[(t.fight_id,t.fighter_id),'sum'] if (t.fight_id,t.fighter_id) in agg.index and agg.loc[(t.fight_id,t.fighter_id),'count']==t.expected_rounds else np.nan for t in b.itertuples()]
    b['ko_loss']=((b.method=='KO_TKO')&(b.result=='win_loss')&(b.winner_id!=b.fighter_id)&b.winner_id.notna()).astype(float)
    # A success with zero recorded attempts is not a usable Bernoulli trial.
    good=b.submission_attempts.notna() & b.submission_attempts.ge(b.sub_win)
    b['conversion_success']=b.sub_win.where(good)
    b['conversion_attempts']=b.submission_attempts.where(good)
    b['conversion_excluded']=~good
    o=b[['fight_id','fighter_id','conversion_success','conversion_attempts','knockdowns']].rename(columns={'fighter_id':'opponent_id','conversion_success':'conversion_loss','conversion_attempts':'conversion_faced','knockdowns':'knockdowns_allowed'})
    b=b.merge(o,on=['fight_id','opponent_id'],validate='one_to_one')
    mapping=__import__('json').loads((R/'models/challengers/mov0_hierarchical_v1/weight_class_map.json').read_text())['literal_map']
    b['division']=b.weight_class.map(mapping).fillna('UNAVAILABLE')
    assert b.event_date.max()<='2026-08-15'
    return b

def totals(g):
    d={'prior_fights':len(g),'prior_decisions':int(g.method.eq('DECISION').sum()),
       'latest_prior_date':None if not len(g) else g.event_date.max(),
       'prior_td_landed':float(g.takedowns_landed.sum()),'td_observed_bouts':int(g.takedowns_landed.notna().sum()),
       'conversion_excluded_bouts':int(g.conversion_excluded.sum())}
    for key,(n,den,decision,scale,strength) in DEFINITIONS.items():
        h=g[g.method.eq('DECISION')] if decision else g
        z=h[[n,den]].dropna()
        d[key+'_num']=float(z[n].sum())*scale
        d[key+'_den']=float(z[den].sum())
        d[key+'_bouts']=len(z)
        d[key+'_missing_bouts']=len(h)-len(z)
    return d

def mean(t,key):
    return t[key+'_num']/t[key+'_den'] if t[key+'_den']>0 else np.nan

def pool(b,year):
    # Parameters frozen at Jan 1; modern training era. No outer outcomes.
    g=b[(b.event_date>='2015-01-01')&(b.event_date<f'{year}-01-01')]
    global_t=totals(g); record={'outer_year':year,'cutoff':f'{year}-01-01','global':global_t,'divisions':{}}
    for div,h in g.groupby('division'):
        t=totals(h);rates={}
        for k in DEFINITIONS:
            p=mean(global_t,k)
            if not np.isfinite(p) or p<=0: raise ValueError(('Unavailable population prior',k,year))
            strength=100. if k in BOUNDED and k not in {'control','control_allowed'} else 300.
            rates[k]=(t[k+'_num']+strength*p)/(t[k+'_den']+strength)
        # Ground KO is not observed: conservative pooled equal-per-significant-
        # attempt attribution, explicitly NOT a measured conversion parameter.
        valid=h.sig_ground_attempted.notna() & h.elapsed_min.notna()
        # Frozen source has no total strikes in bout table; add measured total below.
        valid &= h.sig_total_attempted.gt(0)
        z=h[valid]
        latent_ground_ko=float((z.ko_win*z.sig_ground_attempted/z.sig_total_attempted).sum())
        den=float(z.sig_ground_attempted.sum())
        gv=g[g.sig_total_attempted.gt(0)&g.sig_ground_attempted.notna()&g.elapsed_min.notna()]
        gn=float((gv.ko_win*gv.sig_ground_attempted/gv.sig_total_attempted).sum());gd=float(gv.sig_ground_attempted.sum())
        ground_conv=(latent_ground_ko+1000*(gn/gd))/(den+1000)
        ground_fraction=(latent_ground_ko+20*(gn/max(float(gv.ko_win.sum()),1)))/(float(z.ko_win.sum())+20)
        record['divisions'][div]={'rates':rates,'support':t,'latent_ground_ko_count':latent_ground_ko,
          'ground_attempt_support':den,'ground_conversion':ground_conv,'ground_ko_fraction':ground_fraction,
          'attribution_observed_bouts':len(z)}
    return record

def add_strike_totals(b):
    st=pd.read_csv(R/'data/canonical/v0/fighter_round_stats.csv',usecols=['fight_id','fighter_id','sig_strikes_attempted'])
    st=st[st.fight_id.isin(b.fight_id)]
    z=st.groupby(['fight_id','fighter_id']).sig_strikes_attempted.agg(['sum','count'])
    b=b.copy()
    b['sig_total_attempted']=[z.loc[(t.fight_id,t.fighter_id),'sum'] if (t.fight_id,t.fighter_id) in z.index and z.loc[(t.fight_id,t.fighter_id),'count']==t.expected_rounds else np.nan for t in b.itertuples()]
    return b

def estimate(g,prior):
    t=totals(g)
    for k,(_,_,_,_,strength) in DEFINITIONS.items():
        p=prior['rates'][k];n=t[k+'_num'];d=t[k+'_den']
        value=(n+strength*p)/(d+strength)
        if value<0 or not np.isfinite(value) or (k in BOUNDED and value>1+1e-12):
            raise ValueError(('Invalid ability',k,n,d,value))
        t[k]=value;t[k+'_prior_mean']=p;t[k+'_prior_strength']=strength
        t[k+'_effective_support']=d/(d+strength)
    # Retain PR161 broad support screen separately from continuous shrinkage.
    for k in ['access','control','submission','gnp']:
        t[k+'_supported']=t[k+'_bouts']>=(1 if k=='control' else 3) and t[k+'_den']>=15
    return t

def hazards(a,b,prior,variant='identity',return_multiplier=1.):
    p=prior['rates'];people=[a,b]
    ground_keys={'access','control','submission','gnp','td_conversion','td_resistance','control_allowed','sub_faced','ground_allowed','sub_conversion','sub_conversion_allowed'}
    if variant=='population':
        people=[dict(x,**{k:p[k] for k in ground_keys}) for x in people]
    elif variant=='pooled_conversion':
        people=[dict(x,sub_conversion=p['sub_conversion'],sub_conversion_allowed=p['sub_conversion_allowed']) for x in people]
    elif variant!='identity': raise ValueError('Unknown ablation')
    entry=[];back=[];sub=[];gko=[];standing=[];creation=[];ground_activity=[];shares=[]
    for i in range(2):
        x=people[i];y=people[1-i]
        share=float(np.clip(np.sqrt(x['control']*y['control_allowed']),.02,.8))
        own=float(np.clip(x['control'],.02,.8));allowed=float(np.clip(y['control_allowed'],.02,.8))
        e=x['access']*np.sqrt(x['td_conversion']*(1-y['td_resistance']))
        ref=x['access']*x['td_conversion']
        r=return_multiplier*ref*(1-share)/share
        c=np.sqrt((x['submission']/own)*(y['sub_faced']/allowed))
        conv=np.sqrt(x['sub_conversion']*y['sub_conversion_allowed'])
        ga=np.sqrt((x['gnp']/own)*(y['ground_allowed']/allowed))
        # Non-ground KO proxy retains existing KO creation/vulnerability and KD
        # creation/vulnerability concepts. No feature search or new classifier.
        ko_pair=np.sqrt(x['ko_created']*y['ko_allowed'])
        kd_pair=np.sqrt(x['kd_created']*y['kd_allowed'])
        kd_pop=np.sqrt(p['kd_created']*p['kd_allowed'])
        standing.append(ko_pair*np.sqrt(kd_pair/kd_pop)*(1-prior['ground_ko_fraction'])/(1-p['control']))
        entry.append(e);back.append(r);sub.append(c*conv);gko.append(ga*prior['ground_conversion'])
        creation.append(c);ground_activity.append(ga);shares.append(share)
    return {'entry':entry,'back':back,'ground_ko':gko,'submission':sub,'standing_ko':sum(standing),
      'submission_creation':creation,'ground_activity':ground_activity,'control_exposure_proxy':shares}
