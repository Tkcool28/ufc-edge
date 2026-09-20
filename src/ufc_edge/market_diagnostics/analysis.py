from __future__ import annotations
import math
from typing import Any,Iterable
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from .core import LOGIT_CLIP,MarketDiagnosticError,metric_bundle
def logit_probability(probability:Iterable[float])->np.ndarray:
    p=np.clip(np.asarray(list(probability),float),LOGIT_CLIP,1-LOGIT_CLIP); return np.log(p/(1-p))
def chronological_incremental_test(matched:pd.DataFrame)->dict[str,Any]:
    f=matched.copy(); f["year"]=pd.to_datetime(f.event_date).dt.year; years=sorted(f.year.unique()); folds=[]; parts=[]
    for year in years[1:]:
        tr,va=f[f.year<year],f[f.year==year]
        if len(tr)<50 or va.empty or tr.target.nunique()<2: continue
        xmtr=logit_probability(tr.market_probability).reshape(-1,1); xmva=logit_probability(va.market_probability).reshape(-1,1)
        xbtr=np.column_stack([logit_probability(tr.market_probability),logit_probability(tr.m0_probability)])
        xbva=np.column_stack([logit_probability(va.market_probability),logit_probability(va.m0_probability)])
        yt=tr.target.astype(int).to_numpy(); yv=va.target.astype(int).to_numpy()
        mm=LogisticRegression(penalty=None,solver="lbfgs",max_iter=2000).fit(xmtr,yt)
        bm=LogisticRegression(penalty=None,solver="lbfgs",max_iter=2000).fit(xbtr,yt)
        pm=mm.predict_proba(xmva)[:,1]; pb=bm.predict_proba(xbva)[:,1]
        a=metric_bundle(yv,pm); b=metric_bundle(yv,pb)
        folds.append({"fold_year":str(year),"train_rows":int(len(tr)),"validation_rows":int(len(va)),"market_only":a,"market_plus_m0":b,"market_plus_m0_m0_logit_coefficient":float(bm.coef_[0][1])})
        parts.append(pd.DataFrame({"target":yv,"market_only_probability":pm,"market_plus_m0_probability":pb}))
    if not parts: raise MarketDiagnosticError("no evaluable chronological folds")
    p=pd.concat(parts,ignore_index=True); c=[x["market_plus_m0_m0_logit_coefficient"] for x in folds]
    return {"evaluation_rows":int(len(p)),"fold_count":len(folds),"market_only":metric_bundle(p.target,p.market_only_probability),"market_plus_m0":metric_bundle(p.target,p.market_plus_m0_probability),"folds":folds,
    "folds_market_plus_m0_better_log_loss":sum(x["market_plus_m0"]["log_loss"]<x["market_only"]["log_loss"] for x in folds),
    "folds_market_plus_m0_better_brier":sum(x["market_plus_m0"]["brier"]<x["market_only"]["brier"] for x in folds),
    "folds_market_plus_m0_better_both":sum(x["market_plus_m0"]["log_loss"]<x["market_only"]["log_loss"] and x["market_plus_m0"]["brier"]<x["market_only"]["brier"] for x in folds),
    "m0_logit_coefficient":{"mean":float(np.mean(c)),"min":float(np.min(c)),"max":float(np.max(c)),"positive_folds":sum(v>0 for v in c),"negative_folds":sum(v<0 for v in c)}}
def disagreement_report(m0:pd.Series,market:pd.Series)->dict[str,Any]:
    d=(m0.astype(float)-market.astype(float)).abs()
    return {"pearson":float(m0.corr(market,method="pearson")),"spearman":float(m0.corr(market,method="spearman")),"mean_absolute_difference":float(d.mean()),"median_absolute_difference":float(d.median()),
    "distribution":{"<0.05":int((d<.05).sum()),"0.05-0.10":int(((d>=.05)&(d<.10)).sum()),"0.10-0.15":int(((d>=.10)&(d<.15)).sum()),">=0.15":int((d>=.15).sum())}}
