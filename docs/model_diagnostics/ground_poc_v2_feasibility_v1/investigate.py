"""Frozen-input feasibility diagnosis only. Does not read target outcomes."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from bounds import envelope_certificate,rates
from interval_cover import certify,occupation_boxes
P=Path(__file__).resolve().parent;ROOT=P.parents[2];SOURCE=ROOT/'models/challengers/ground_opportunity_consistent_poc_v2/run_v1'
sys.path.insert(0,str(SOURCE.parent));import opportunity as op

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p,x):p.write_text(json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n')

def main():
    assert sha(SOURCE/'EVIDENCE_MANIFEST.json')=='5ed906bd1852eea3e16ac20d7551dc4926141aaf75dbe6b9c49a578e03f772f3'
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=P);ap.add_argument('--roots',type=Path,default=P/'root_probe_records.json');args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    rows=json.loads((SOURCE/'opportunity_transition_reward_records.json').read_text())
    root={x['fight_id']:x for x in json.loads(args.roots.read_text())}
    certificates=[];cover=[];decisions=[];witness=[]
    for row in rows:
        c=envelope_certificate(row);certificates.append(c)
        if row['status']=='VALID':assert not c['certified'];continue
        fid=row['fight_id'];q,s,e,h,hs=rates(row);U=np.array(row['detail']['return_upper_bound']);a=root[fid]
        if c['certified']:kind='CERTIFIED_ANALYTIC_ENVELOPE'
        elif a['physical_witness']:
            ret=np.array(a['returns']);assert np.min(ret)>=0 and np.max(ret-U)<=0
            state=op.exposures(e,ret,h,hs,row['scheduled_rounds']);err=float(max(abs(state['shares'][1:]-q)));assert err<=1e-8
            td=np.array(row['TD_reward']);u=np.array(row['SUB_reward']);g=np.array(row['GNP_reward']);cv=np.array(row['SUB_conversion']);gv=np.array(row['GNP_conversion'])
            rw=max(float(max(abs(hh*ex-rate*state['alive'])/np.maximum(1.,rate*state['alive']))) for hh,ex,rate in [(td/s,state['minutes'][0],td),(u/q,state['minutes'][1:],u),(g/q,state['minutes'][1:],g)])
            assert rw<=1e-7
            flux=e*state['minutes'][0]-(ret+h)*state['minutes'][1:]-state['boundary_removal_mass'];assert max(abs(flux))/state['alive']<=1e-12
            raw=np.array([hs*state['minutes'][0]+np.dot(g/q*gv,state['minutes'][1:]),np.dot(u/q*cv,state['minutes'][1:]),state['decision']]);assert abs(raw.sum()-1)<=1e-10
            closed=(hs*s+np.dot(g,gv))/(hs*s+np.dot(g,gv)+np.dot(u,cv));assert abs(raw[0]/sum(raw[:2])-closed)<=1e-8
            initial=np.array(row['detail']['returns'])/U
            def residual(x):return op.exposures(e,x*U,h,hs,row['scheduled_rounds'])['shares'][1:]-q
            fine=least_squares(residual,[.5,.5],bounds=(0,1),method='trf',ftol=1e-12,xtol=1e-12,gtol=1e-15,max_nfev=400)
            assert max(abs(fine.fun))<=1e-8
            gradient=np.array(row['detail']['jacobian']).T@row['detail']['residual'];scaled=gradient*np.where(gradient>0,initial,1-initial)
            lo,hi,_=occupation_boxes(row,np.r_[ret/U,ret/U][None,:]);assert np.all(lo[0]<=q) and np.all(q<=hi[0])
            witness.append(dict(fight_id=fid,root_returns=ret.tolist(),occupancy_error=err,reward_residual=rw,flux_residual=float(max(abs(flux))),original_error=row['detail']['error'],original_scaled_gradient=float(max(abs(scaled))),diagnostic_TRF_gtol=1e-15,diagnostic_TRF_error=float(max(abs(fine.fun))),diagnostic_TRF_returns=(fine.x*U).tolist(),supported=row['supported'],applied_to_POC_B=False))
            kind='SOLVER_MISSED_VALID_SOLUTION'
        else:
            v=certify(row);assert v['certified'],fid;cover.append(v);kind='CERTIFIED_INTERVAL_DOMAIN_COVER'
        decisions.append(dict(fight_id=fid,year=row['outer_year'],division=row['division'],support_stratum=row['support_stratum'],supported=row['supported'],classification=kind))
    counts={k:sum(x['classification']==k for x in decisions) for k in sorted(set(x['classification'] for x in decisions))}
    assert len(decisions)==1838 and counts['SOLVER_MISSED_VALID_SOLUTION']==1
    assert counts['CERTIFIED_ANALYTIC_ENVELOPE']+counts['CERTIFIED_INTERVAL_DOMAIN_COVER']==1837
    result=dict(original_rows=4260,original_valid=2422,original_unavailable=1838,certified_structural=1837,missed_valid_roots=1,unresolved=0,maximum_valid_after_numerical_repair=2423,maximum_feasibility_after_numerical_repair=2423/4260,certified_supported=sum(x['supported'] and x['classification'].startswith('CERTIFIED') for x in decisions),outcomes_read_for_scoring=0,original_POC_B_modified=False,classification='D_FOR_FROZEN_MAPPING_WITH_ONE_NUMERICAL_MISS',counts=counts)
    js(out/'analytic_certificates.json',certificates);js(out/'interval_cover_certificates.json',cover);js(out/'row_diagnosis.json',decisions);js(out/'numerical_witness.json',witness);js(out/'RESULT.json',result)
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
