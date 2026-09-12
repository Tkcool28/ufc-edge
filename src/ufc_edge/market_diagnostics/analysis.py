from __future__ import annotations
from hashlib import sha256
import math
from typing import Any, Iterable
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from .core import LOGIT_CLIP, MarketDiagnosticError, canonical_json, metric_bundle


def logit_probability(probability: Iterable[float]) -> np.ndarray:
    p = np.clip(np.asarray(list(probability), float), LOGIT_CLIP, 1-LOGIT_CLIP)
    return np.log(p/(1-p))


def chronological_incremental_test(matched: pd.DataFrame) -> dict[str, Any]:
    frame = matched.copy(); frame["year"] = pd.to_datetime(frame.event_date).dt.year
    years, folds, parts = sorted(int(y) for y in frame.year.unique()), [], []
    if len(years) < 2: raise MarketDiagnosticError("incremental test needs >=2 matched years")
    for year in years[1:]:
        train, valid = frame[frame.year < year], frame[frame.year == year]
        if len(train) < 50 or valid.empty or train.target.nunique() < 2: continue
        xm_tr, xm_va = logit_probability(train.market_probability).reshape(-1,1), logit_probability(valid.market_probability).reshape(-1,1)
        xb_tr = np.column_stack([logit_probability(train.market_probability),logit_probability(train.m0_probability)])
        xb_va = np.column_stack([logit_probability(valid.market_probability),logit_probability(valid.m0_probability)])
        yt, yv = train.target.astype(int).to_numpy(), valid.target.astype(int).to_numpy()
        mm = LogisticRegression(penalty=None,solver="lbfgs",max_iter=2000).fit(xm_tr,yt)
        bm = LogisticRegression(penalty=None,solver="lbfgs",max_iter=2000).fit(xb_tr,yt)
        pm, pb = mm.predict_proba(xm_va)[:,1], bm.predict_proba(xb_va)[:,1]
        a,b = metric_bundle(yv,pm), metric_bundle(yv,pb)
        folds.append({"fold_year":str(year),"train_rows":int(len(train)),"validation_rows":int(len(valid)),"market_only":a,"market_plus_m0":b,
                      "market_only_intercept":float(mm.intercept_[0]),"market_only_market_logit_coefficient":float(mm.coef_[0][0]),
                      "market_plus_m0_intercept":float(bm.intercept_[0]),"market_plus_m0_market_logit_coefficient":float(bm.coef_[0][0]),
                      "market_plus_m0_m0_logit_coefficient":float(bm.coef_[0][1])})
        parts.append(pd.DataFrame({"target":yv,"market_only_probability":pm,"market_plus_m0_probability":pb}))
    if not parts: raise MarketDiagnosticError("no evaluable chronological folds")
    pred = pd.concat(parts,ignore_index=True); coeff=[f["market_plus_m0_m0_logit_coefficient"] for f in folds]
    better = lambda f: f["market_plus_m0"]["log_loss"] < f["market_only"]["log_loss"] and f["market_plus_m0"]["brier"] < f["market_only"]["brier"]
    return {"evaluation_rows":int(len(pred)),"first_evaluated_year":folds[0]["fold_year"],"last_evaluated_year":folds[-1]["fold_year"],
            "fold_count":len(folds),"market_only":metric_bundle(pred.target,pred.market_only_probability),
            "market_plus_m0":metric_bundle(pred.target,pred.market_plus_m0_probability),"folds":folds,
            "folds_market_plus_m0_better_log_loss":sum(f["market_plus_m0"]["log_loss"]<f["market_only"]["log_loss"] for f in folds),
            "folds_market_plus_m0_better_brier":sum(f["market_plus_m0"]["brier"]<f["market_only"]["brier"] for f in folds),
            "folds_market_plus_m0_better_both":sum(better(f) for f in folds),
            "m0_logit_coefficient":{"mean":float(np.mean(coeff)),"min":float(np.min(coeff)),"max":float(np.max(coeff)),
                                    "positive_folds":sum(c>0 for c in coeff),"negative_folds":sum(c<0 for c in coeff),"zero_folds":sum(abs(c)<=1e-12 for c in coeff)}}


def disagreement_report(m0: pd.Series, market: pd.Series) -> dict[str, Any]:
    diff=(m0.astype(float)-market.astype(float)).abs()
    buckets=pd.cut(diff,[-np.inf,.05,.10,.15,np.inf],labels=["<0.05","0.05-0.10","0.10-0.15",">=0.15"],right=False)
    return {"pearson":float(m0.corr(market,method="pearson")),"spearman":float(m0.corr(market,method="spearman")),
            "mean_absolute_difference":float(diff.mean()),"median_absolute_difference":float(diff.median()),
            "distribution":{str(k):int(v) for k,v in buckets.value_counts(sort=False).items()}}


def diagnostic_table_logical_hash(table: pd.DataFrame) -> str:
    cols=["fight_id","event_date","fold_year","target","m0_probability","market_probability","blend_probability","market_source","market_timing"]
    digest=sha256()
    for row in table.sort_values(["event_date","fight_id"])[cols].itertuples(index=False,name=None):
        digest.update(canonical_json(list(row)).encode()); digest.update(b"\n")
    return digest.hexdigest()


def classify_verdict(result: dict[str, Any]) -> str:
    m0,market,blend=result["same_sample_metrics"]["m0"],result["same_sample_metrics"]["market"],result["same_sample_metrics"]["blend_50_50"]
    inc=result["incremental_information"]
    adds=(inc["market_plus_m0"]["log_loss"]<inc["market_only"]["log_loss"] and inc["market_plus_m0"]["brier"]<inc["market_only"]["brier"]
          and inc["folds_market_plus_m0_better_both"]>=math.ceil(inc["fold_count"]/2)
          and inc["m0_logit_coefficient"]["positive_folds"]>inc["m0_logit_coefficient"]["negative_folds"])
    close=m0["log_loss"]<=market["log_loss"]+.015 and m0["brier"]<=market["brier"]+.0075
    blend_wins=blend["log_loss"]<min(m0["log_loss"],market["log_loss"]) and blend["brier"]<min(m0["brier"],market["brier"])
    dominant=market["log_loss"]+.02<m0["log_loss"] and market["brier"]+.01<m0["brier"]
    if close and (blend_wins or adds): return "MARKET_COMPETITIVE"
    if adds: return "MARKET_COMPLEMENTARY"
    if dominant: return "MARKET_DOMINANT"
    return "MARKET_REDUNDANT"
