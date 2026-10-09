"""Synthetic contract mathematics only. No fighter loader, IDs, outcome scoring or POC runner."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from scipy.optimize import least_squares
CONFIG=json.loads((Path(__file__).parent/'contract.json').read_text())
class Unavailable(ValueError):
    def __init__(self,code,detail):
        self.code=code;self.detail=detail
        super().__init__(f'{code}: {detail}')
def exposures(entry,returns,ground_terminal,standing_terminal,rounds):
    """Renewal occupation integrals; works with singular/zero-terminal generators."""
    e=np.asarray(entry,float);r=np.asarray(returns,float);h=np.asarray(ground_terminal,float)
    if rounds not in (3,5):raise Unavailable('ROUND_STRUCTURE','requires three/five five-minute rounds')
    if not np.isfinite(np.r_[e,r,h,standing_terminal]).all() or np.min(np.r_[e,r,h,standing_terminal])<0:raise Unavailable('INVALID_HAZARD','nonnegative finite inputs required')
    t=np.array([[-sum(e)-standing_terminal,e[0],e[1]],[r[0],-r[0]-h[0],0],[r[1],0,-r[1]-h[1]]])
    aug=np.zeros((6,6));aug[:3,:3]=t;aug[:3,3:]=np.eye(3)
    z=expm(5*aug);p=z[:3,:3];one=z[0,3:];survival=p[0].sum();scale=sum(survival**j for j in range(rounds))
    minutes=one*scale;boundary_mass=p[0,1:]*scale
    reset_mass=p[0,1:]*sum(survival**j for j in range(rounds-1));expiry_mass=p[0,1:]*survival**(rounds-1)
    if min(*minutes,survival)<-1e-10 or survival>1+1e-10:raise Unavailable('NUMERICAL_TRANSITION','invalid occupation or transient survival')
    alive=minutes.sum()
    if alive<=0 or not np.isfinite(alive):raise Unavailable('NUMERICAL_EXPOSURE','zero/nonfinite alive exposure')
    return dict(minutes=minutes,shares=minutes/alive,alive=alive,boundary_removal_mass=boundary_mass,interround_reset_mass=reset_mass,fight_expiry_ground_mass=expiry_mass,decision=survival**rounds,one_round=one,transition=p)
def solve_synthetic(td,sub,gnp,td_success,target_ground,sub_conversion=(0.,0.),ground_conversion=(0.,0.),standing_terminal=0.,rounds=3):
    """Inverse demonstration accepts invented numeric fixtures, not repository records."""
    td,sub,gnp,pi,gq,cv,gv=[np.asarray(x,float) for x in [td,sub,gnp,td_success,target_ground,sub_conversion,ground_conversion]]
    if any(x.shape!=(2,) for x in [td,sub,gnp,pi,gq,cv,gv]):raise Unavailable('INPUT_SHAPE','two actor sides required')
    if not np.isfinite(np.r_[td,sub,gnp,pi,gq,cv,gv,standing_terminal]).all() or min(*td,*sub,*gnp,standing_terminal)<0:raise Unavailable('INVALID_INPUT','finite nonnegative rewards required')
    if min(*pi,*cv,*gv)<0 or max(*pi,*cv,*gv)>1:raise Unavailable('INVALID_CONVERSION','probabilities outside [0,1]')
    floor=CONFIG['eligible_share_floor'];s=1-gq.sum()
    if max(gq)>CONFIG['legacy_control_proxy_ceiling']+1e-12:raise Unavailable('INVALID_PROXY_TARGET','legacy actor control ceiling exceeded')
    if min(*gq,s)<floor-1e-12:raise Unavailable('INFEASIBLE_SIMPLEX','both ground shares and standing must be at least 0.02; no clipping/projection')
    td_hazard=td/s;entry=td_hazard*pi;creation=sub/gq;ground_actions=gnp/gq;terminal=creation*cv+ground_actions*gv
    upper=td*pi/gq-terminal
    if min(upper)<=0:raise Unavailable('NO_POSITIVE_RESET_BUDGET',{'return_upper_bounds':upper.tolist(),'necessary_flow_constraint_failed':True})
    if min(upper)<=CONFIG['solver']['flux_budget_tolerance_per_minute']:raise Unavailable('NUMERICAL_RESET_BUDGET','positive budget below fixed numerical resolution; no structural infeasibility claim')
    if max(terminal)==0 and standing_terminal==0:
        z=5*sum(entry)
        ceiling=z/2-z*z/6+z*z*z/24 if z<1e-7 else 1+np.expm1(-z)/z
        if gq.sum()>ceiling+CONFIG['solver']['occupancy_absolute_tolerance']:raise Unavailable('INFEASIBLE_FINITE_ROUND_CEILING',{'requested':float(gq.sum()),'maximum_no_return_ground_share':float(ceiling)})
    def residual(u):return exposures(entry,u*upper,terminal,standing_terminal,rounds)['shares'][1:]-gq
    cfg=CONFIG['solver'];fit=least_squares(residual,[.5,.5],bounds=(0.,1.),method='trf',ftol=cfg['ftol'],xtol=cfg['xtol'],gtol=cfg['gtol'],max_nfev=cfg['max_nfev'])
    r=fit.x*upper;x=exposures(entry,r,terminal,standing_terminal,rounds);error=max(abs(x['shares'][1:]-gq))
    if not fit.success or error>cfg['occupancy_absolute_tolerance']:raise Unavailable('UNRESOLVED_FINITE_ROUND_TARGET',{'solver_success':bool(fit.success),'error':float(error),'no_claim_of_global_infeasibility':True})
    actions={'TD':td_hazard*x['minutes'][0],'SUB':creation*x['minutes'][1:],'GNP':ground_actions*x['minutes'][1:]}
    targets={'TD':td*x['alive'],'SUB':sub*x['alive'],'GNP':gnp*x['alive']}
    for k in actions:
        if max(abs(actions[k]-targets[k])/np.maximum(1.,targets[k]))>cfg['reward_relative_tolerance']:raise Unavailable('REWARD_RESIDUAL',k)
    flux=entry*x['minutes'][0]-(r+terminal)*x['minutes'][1:]-x['boundary_removal_mass']
    if max(abs(flux))>1e-8:raise Unavailable('RESET_FLUX_RESIDUAL',flux.tolist())
    return dict(**x,returns=r,return_upper_bound=upper,entry=entry,TD_hazard=td_hazard,SUB_creation=creation,GNP_actions=ground_actions,actions=actions,targets=targets,implicit_SUB_multiplier=[float(1/gq[i]) if sub[i]>0 else None for i in range(2)],opportunity_scale_operator=1/gq,implicit_SUB_multiplier_null_reason=[None if sub[i]>0 else "ZERO_TOTAL_RATE" for i in range(2)],implicit_TD_multiplier=1/s,implicit_GNP_multiplier=1/gq,occupancy_error=float(error),flux_residual=flux,solver_nfev=fit.nfev,jacobian=fit.jac)
