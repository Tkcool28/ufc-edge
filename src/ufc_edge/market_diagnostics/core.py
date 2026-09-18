from __future__ import annotations
from hashlib import sha256
import json, math, re, unicodedata
from typing import Any, Iterable, Sequence
import numpy as np, pandas as pd
from sklearn.metrics import accuracy_score,brier_score_loss,log_loss,roc_auc_score
M0_OOF_ROWS=5626
M0_OOF_LOGICAL_SHA256="708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c"
BLEND_WEIGHT=0.5
LOGIT_CLIP=1e-6
class MarketDiagnosticError(ValueError): pass
def canonical_json(value:Any)->str:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
def normalize_name(value:str)->str:
    if not isinstance(value,str) or not value.strip(): return ""
    value=unicodedata.normalize("NFKD",value)
    value="".join(ch for ch in value if not unicodedata.combining(ch))
    value=re.sub(r"[^a-z0-9]+"," ",value.casefold().replace("’","'"))
    return " ".join(value.split())
def decimal_odds_to_raw_implied(odds:float|int)->float:
    v=float(odds)
    if not math.isfinite(v) or v<=1: raise MarketDiagnosticError("decimal odds must be finite and >1")
    return 1.0/v
def proportional_no_vig(p1:float,p2:float)->tuple[float,float]:
    if not all(math.isfinite(x) and x>0 for x in (p1,p2)): raise MarketDiagnosticError("invalid implied probabilities")
    s=p1+p2
    return p1/s,p2/s
def median_no_vig_probability(values:Sequence[float])->float:
    a=np.asarray(list(values),dtype=float)
    if not len(a) or not np.isfinite(a).all() or ((a<=0)|(a>=1)).any(): raise MarketDiagnosticError("invalid median inputs")
    return float(np.median(a))
def fixed_blend(m0:Iterable[float],market:Iterable[float])->np.ndarray:
    a,b=np.asarray(list(m0),float),np.asarray(list(market),float)
    if a.shape!=b.shape: raise MarketDiagnosticError("blend shape mismatch")
    return .5*a+.5*b
def metric_bundle(target:Iterable[int|bool],prob:Iterable[float])->dict[str,Any]:
    y=np.asarray(list(target),int); p=np.clip(np.asarray(list(prob),float),1e-12,1-1e-12)
    auc=None
    if len(np.unique(y))>1: auc=float(roc_auc_score(y,p))
    return {"rows":int(len(y)),"log_loss":float(log_loss(y,p,labels=[0,1])),"brier":float(brier_score_loss(y,p)),"accuracy":float(accuracy_score(y,p>=.5)),"auc":auc}
def calibration_table(target:pd.Series,probability:pd.Series):
    edges=np.linspace(0,1,11); labels=[f"{edges[i]:.1f}-{edges[i+1]:.1f}" for i in range(10)]
    bins=pd.cut(probability,edges,labels=labels,include_lowest=True); rows=[]; ece=0.0; total=len(target)
    for label in labels:
        mask=bins==label; n=int(mask.sum())
        if not n: continue
        mp=float(probability[mask].mean()); actual=float(target[mask].astype(int).mean()); ece+=n/total*abs(mp-actual)
        rows.append({"bin":label,"rows":n,"mean_predicted":mp,"actual_win_rate":actual})
    return rows,float(ece)
def m0_oof_logical_hash(oof:pd.DataFrame)->str:
    cols=["fight_id","event_date","fold_id","target","naive_probability","empirical_probability","logistic_probability"]
    d=sha256()
    for row in oof.sort_values(["event_date","fight_id"])[cols].itertuples(index=False,name=None):
        x=list(row); x[1]=str(x[1]); d.update(canonical_json(x).encode()); d.update(b"\n")
    return d.hexdigest()
def validate_m0_oof(oof:pd.DataFrame)->None:
    if len(oof)!=M0_OOF_ROWS or oof["fight_id"].duplicated().any() or m0_oof_logical_hash(oof)!=M0_OOF_LOGICAL_SHA256:
        raise MarketDiagnosticError("frozen M0 OOF identity mismatch")
