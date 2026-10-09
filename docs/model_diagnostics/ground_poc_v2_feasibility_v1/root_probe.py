import argparse,json,sys,numpy as np
from pathlib import Path
from scipy.linalg import expm,expm_frechet
from scipy.optimize import root
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'models/challengers/ground_opportunity_consistent_poc_v2'))
import opportunity as op
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path(__file__).with_name('root_probe_records.json'));args=ap.parse_args()
rows=json.loads((ROOT/'models/challengers/ground_opportunity_consistent_poc_v2/run_v1/opportunity_transition_reward_records.json').read_text())
res=[]
for x in rows:
 if x['status']!='UNAVAILABLE':continue
 q=np.array(x['target_ground']);td=np.array(x['TD_reward']);u=np.array(x['SUB_reward']);g=np.array(x['GNP_reward']);pi=np.array(x['TD_success']);cv=np.array(x['SUB_conversion']);gv=np.array(x['GNP_conversion']);s=x['standing_target'];entry=td*pi/s;term=u/q*cv+g/q*gv;entry=td/s*pi;upper=td*pi/q-term
 def fun(gamma,jac=False):
  returns=gamma*upper;t=np.array([[-sum(entry)-x['standing_KO'],*entry],[returns[0],-returns[0]-term[0],0],[returns[1],0,-returns[1]-term[1]]]);aug=np.zeros((6,6));aug[:3,:3]=t;aug[:3,3:]=np.eye(3);aug*=5
  z=expm(aug);E=z[0,3:];L=E.sum();value=E[1:]/L-q
  if not jac:return value
  deriv=[]
  for i in range(2):
   d=np.zeros((6,6));d[i+1,0]=5*upper[i];d[i+1,i+1]=-5*upper[i];dz=expm_frechet(aug,d,compute_expm=False);de=dz[0,3:];deriv.append((de[1:]*L-E[1:]*de.sum())/L**2)
  return np.array(deriv).T
 initial=np.array(x['detail']['returns'])/upper
 fit=root(fun,initial,jac=lambda z:fun(z,True),method='hybr',options={'xtol':1e-10,'maxfev':200})
 error=max(abs(fun(fit.x)));physical=bool(min(fit.x)>=0 and max(fit.x)<=1 and error<=1e-8)
 if physical:
  z=op.exposures(entry,fit.x*upper,term,x['standing_KO'],x['scheduled_rounds'])
  physical=all(max(abs(h*ex-rate*z['alive'])/np.maximum(1.,rate*z['alive']))<=1e-7 for h,ex,rate in [(td/s,z['minutes'][0],td),(u/q,z['minutes'][1:],u),(g/q,z['minutes'][1:],g)])
 res.append({'fight_id':x['fight_id'],'gamma':fit.x.tolist(),'returns':(fit.x*upper).tolist(),'root_error':float(error),'physical_witness':physical,'root_success':bool(fit.success),'nfev':int(fit.nfev)})
 if len(res)%300==0:print(len(res),flush=True)
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(res,indent=2,sort_keys=True,allow_nan=False)+'\n')
print({'rows':len(res),'physical_witnesses':sum(x['physical_witness'] for x in res),'accurate_negative_return_roots':sum(min(x['gamma'])<0 and x['root_error']<1e-8 for x in res)},flush=True)
print([x for x in res if x['physical_witness']])
