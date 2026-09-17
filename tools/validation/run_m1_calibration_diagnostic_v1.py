#!/usr/bin/env python3
"""Stage B only: N-gated corrected-M1 diagnostics on frozen V1 terrain."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd

EPS=1e-15
CONF=[(.50,.55,"50–55%"),(.55,.60,"55–60%"),(.60,.65,"60–65%"),(.65,.70,"65–70%"),(.70,.75,"70–75%"),(.75,.80,"75–80%"),(.80,.85,"80–85%"),(.85,1.0000001,"85%+")]
def sha(p):
 h=hashlib.sha256();
 with open(p,"rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def gate(n): return "NORMAL" if n>=100 else "MODERATE_UNCERTAINTY" if n>=50 else "THIN_EXPLORATORY" if n>=25 else "INSUFFICIENT_SAMPLE"
def auc(y,p):
 order=np.argsort(p); ranks=np.empty(len(p)); ranks[order]=np.arange(1,len(p)+1)
 pos=y==1; n1=pos.sum(); n0=len(y)-n1
 return None if not n1 or not n0 else float((ranks[pos].sum()-n1*(n1+1)/2)/(n1*n0))
def slope_intercept(y,p):
 x=np.log(np.clip(p,EPS,1-EPS)/(1-np.clip(p,EPS,1-EPS))); X=np.c_[np.ones(len(x)),x]; b=np.zeros(2)
 for _ in range(40):
  q=1/(1+np.exp(-np.clip(X@b,-30,30))); w=np.clip(q*(1-q),1e-8,None); step=np.linalg.solve(X.T@(X*w[:,None]),X.T@(y-q)); b+=step
  if max(abs(step))<1e-10:break
 return float(b[1]),float(b[0])
def metric(g,prob="m1_probability",target="target"):
 n=len(g); p=np.clip(g[prob].astype(float).to_numpy(),EPS,1-EPS); y=g[target].astype(int).to_numpy(); pick=np.maximum(p,1-p); picked=np.where(p>.5,y,1-y)
 z=1.96; ph=y.mean(); den=1+z*z/n; ci=((ph+z*z/(2*n)-z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n)))/den,(ph+z*z/(2*n)+z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n)))/den)
 out={"N":n,"status":gate(n),"mean_predicted_probability":float(p.mean()),"observed_win_rate":float(y.mean()),"calibration_gap":float(y.mean()-p.mean()),"absolute_calibration_gap":float(abs(y.mean()-p.mean())),"pick_accuracy":float(picked.mean()),"mean_pick_confidence":float(pick.mean()),"brier":float(np.mean((p-y)**2)),"log_loss":float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p))),"observed_ci95":[float(ci[0]),float(ci[1])],"auc":auc(y,p)}
 return {"N":n,"status":out["status"]} if n<25 else out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--assignment',type=Path,required=True);ap.add_argument('--m1-oof',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
 ass=pd.read_csv(a.assignment); oof=pd.read_parquet(a.m1_oof)
 need={'fight_id','target','m1_probability'}
 if not need.issubset(oof):raise RuntimeError('corrected M1 OOF schema missing required columns')
 if oof.fight_id.duplicated().any() or ass.fight_id.duplicated().any():raise RuntimeError('duplicate fight identity')
 m=oof[['fight_id','target','m1_probability']].merge(ass,on='fight_id',how='left',validate='one_to_one',indicator=True)
 if not m['_merge'].eq('both').all():raise RuntimeError('OOF identity missing from frozen assignment')
 m=m.drop(columns='_merge'); overall=metric(m); sl,inter=slope_intercept(m.target.to_numpy(int),m.m1_probability.to_numpy(float))
 m['pick_confidence']=np.maximum(m.m1_probability,1-m.m1_probability); m['selected_side_win']=np.where(m.m1_probability>.5,m.target,1-m.target)
 ece=0.0
 for lo,hi,_ in CONF:
  g=m[(m.pick_confidence>=lo)&(m.pick_confidence<hi)]
  if len(g): ece += len(g)/len(m)*abs(float(g.selected_side_win.mean()-g.pick_confidence.mean()))
 overall.update({'calibration_slope':sl,'calibration_intercept':inter,'ece':float(ece)})
 rows=[]
 for lo,hi,label in CONF:
  g=m[(m.pick_confidence>=lo)&(m.pick_confidence<hi)]
  r=metric(g.assign(m1_probability=g.pick_confidence,target=g.selected_side_win)) if len(g) else {'N':0,'status':'INSUFFICIENT_SAMPLE'};r.update({'surface':'pick_confidence','bucket':label});rows.append(r)
 for col in ['experience_bucket','layoff_bucket','scheduled_duration_bucket','title_status','weight_class','completeness_tier','striking_environment','grappling_environment','joint_mov_environment']:
  for key,g in m.groupby(col,dropna=False):
   r=metric(g);r.update({'surface':col,'bucket':str(key)});rows.append(r)
 report={'status':'M1_CALIBRATION_DIAGNOSTIC_V1_COMPLETE','overall':overall,'rows':rows,'formulas':{'calibration_gap':'observed_win_rate - mean_predicted_probability','brier':'mean((p-y)^2)','log_loss':'-mean(y log(p)+(1-y)log(1-p)); epsilon=1e-15','calibration_slope_intercept':'logistic regression of target on logit(p)','sample_gate':'N<25 returns only N/status'}}
 a.output_dir.mkdir(parents=True,exist_ok=True);(a.output_dir/'M1_CALIBRATION_DIAGNOSTIC_V1.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');pd.DataFrame(rows).to_csv(a.output_dir/'M1_CALIBRATION_DIAGNOSTIC_V1.csv',index=False)
 manifest={'status':'M1_CALIBRATION_DIAGNOSTIC_V1_COMPLETE','assignment_sha256':sha(a.assignment),'m1_oof_sha256':sha(a.m1_oof),'report_sha256':sha(a.output_dir/'M1_CALIBRATION_DIAGNOSTIC_V1.json'),'rows':len(m)};(a.output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');print('M1_CALIBRATION_DIAGNOSTIC_V1_COMPLETE')
if __name__=='__main__':main()
