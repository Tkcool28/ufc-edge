"""Outcome-blind analytic occupancy ceiling, verified by interval arithmetic."""
import numpy as np
from scipy.optimize import brentq
import mpmath as mp
mp.iv.dps=60
IV=mp.iv.mpf
TOL=1e-8

def rates(row):
    q=np.array(row['target_ground']);s=row['standing_target']
    entry=np.array(row['TD_reward'])/s*np.array(row['TD_success'])
    terminal=np.array(row['SUB_reward'])/q*np.array(row['SUB_conversion'])+np.array(row['GNP_reward'])/q*np.array(row['GNP_conversion'])
    return q,s,entry,terminal,row['standing_KO']
def integral(k,a,b):
    return b-a if k==0 else (np.exp(-k*a)-np.exp(-k*b))/k

def ceiling(alpha,m,h):
    def H(R):
        t=5+np.log1p(-h*R)/h
        def segment(k,a,b):
            E=integral(k,a,b)
            F=(E-np.exp(-5*h)*integral(k-h,a,b))/h
            return F-R*E
        return segment(m,0,t)+segment(alpha,t,5)
    return brentq(H,0,-np.expm1(-5*h)/h,xtol=1e-13)

def iv_integral(k,a,b):
    return b-a if k.a==0 and k.b==0 else (mp.iv.exp(-k*a)-mp.iv.exp(-k*b))/k

def H_interval(R,alpha,m,h):
    R,alpha,m,h=map(IV,[R,alpha,m,h]);t=IV(5)+mp.iv.ln(1-h*R)/h
    def segment(k,a,b):
        E=iv_integral(k,a,b)
        F=(E-mp.iv.exp(-5*h)*iv_integral(k-h,a,b))/h
        return F-R*E
    return segment(m,IV(0),t)+segment(alpha,t,IV(5))

def envelope_certificate(row):
    q,s,e,h,hs=rates(row);alpha=float(np.nextafter(float((IV(float(e[0]))+IV(float(e[1]))+IV(hs)).b),np.inf));m=float(min(hs,*h));cert=[]
    for i in range(2):
        root=ceiling(alpha,m,float(h[i]));upper=float(np.nextafter(root+1e-10,np.inf))
        H=H_interval(upper,alpha,m,float(h[i]))
        assert H.b<0,'upper bracket lacks a rigorous sign certificate'
        # A tolerated solution may undershoot actor share by TOL and increase
        # standing share by 2*TOL. These relaxed bounds favor feasibility.
        gap=IV(float(q[i]))-IV(TOL)-IV(float(e[i]))*(IV(float(s))+2*IV(TOL))*IV(upper)
        cert.append(dict(actor=i,residence_ceiling_upper=upper,H_upper=float(H.b),target_share=float(q[i]),maximum_share_with_tolerance=float(np.nextafter(float((IV(float(e[i]))*(IV(float(s))+2*IV(TOL))*IV(upper)).b),np.inf)),gap_lower=float(gap.a),certified=bool(gap.a>0)))
    return dict(fight_id=row['fight_id'],certified=any(x['certified'] for x in cert),actors=cert)
