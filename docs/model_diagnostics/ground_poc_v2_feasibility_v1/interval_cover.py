"""Exhaustive interval occupation bounds on the frozen two-return rectangle."""
import numpy as np
import mpmath as mp
from bounds import rates,IV
mp.iv.dps=60
DOWN=lambda x:np.nextafter(x,-np.inf)
UP=lambda x:np.nextafter(x,np.inf)
def endpoints(x):return max(0.,float(DOWN(float(x.a)))),max(0.,float(UP(float(x.b))))
def poisson_weights(lam):
    z=IV(5)*IV(lam);term=IV(1);acc=term;decay=mp.iv.exp(-z);lo=[];hi=[]
    for n in range(1000):
        if n:term=term*z/n;acc+=term
        tail=1-decay*acc;w=tail/IV(lam);a,b=endpoints(w);lo.append(a);hi.append(b)
        if float(tail.b)<1e-24:return np.array(lo),np.array(hi),float(UP(5*float(tail.b)))
    raise ArithmeticError('unresolved Poisson truncation')

def occupation_boxes(row,boxes,cache=None):
    q,s,e,h,hs=rates(row);U=np.array(row['detail']['return_upper_bound'])
    if cache is None:
        exits=[IV(float(e[0]))+IV(float(e[1]))+IV(hs),*[IV(float(U[i]))+IV(float(h[i])) for i in range(2)]]
        lam=max(float(x.b) for x in exits);lam=float(UP(lam));wl,wh,tail=poisson_weights(lam)
        p00=endpoints(1-(IV(float(e[0]))+IV(float(e[1]))+IV(hs))/IV(lam));p01=endpoints(IV(float(e[0]))/IV(lam));p02=endpoints(IV(float(e[1]))/IV(lam))
        cache=(lam,wl,wh,tail,p00,p01,p02)
    lam,wl,wh,tail,p00,p01,p02=cache
    low=boxes[:,:2];high=boxes[:,2:]
    # Every elementary binary64 operation is rounded outwards. Constant
    # Poisson weights and fixed matrix entries are 60-digit interval-enclosed.
    rlo=np.maximum(0,DOWN(low*U));rhi=UP(high*U)
    offlo=np.maximum(0,DOWN(rlo/lam));offhi=UP(rhi/lam)
    diaglo=np.maximum(0,DOWN(1-UP(UP(rhi+h)/lam)));diaghi=np.minimum(1,UP(1-DOWN(DOWN(rlo+h)/lam)))
    n=len(boxes);vl=np.tile([1.,0.,0.],(n,1));vh=vl.copy();El=np.zeros((n,3));Eh=np.zeros((n,3))
    def mul(a,b,up):return UP(a*b) if up else np.maximum(0,DOWN(a*b))
    def add(a,b,up):return UP(a+b) if up else np.maximum(0,DOWN(a+b))
    for j in range(len(wl)):
        El=add(El,mul(vl,wl[j],False),False);Eh=add(Eh,mul(vh,wh[j],True),True)
        nl=np.c_[add(add(mul(vl[:,0],p00[0],False),mul(vl[:,1],offlo[:,0],False),False),mul(vl[:,2],offlo[:,1],False),False),add(mul(vl[:,0],p01[0],False),mul(vl[:,1],diaglo[:,0],False),False),add(mul(vl[:,0],p02[0],False),mul(vl[:,2],diaglo[:,1],False),False)]
        nh=np.c_[add(add(mul(vh[:,0],p00[1],True),mul(vh[:,1],offhi[:,0],True),True),mul(vh[:,2],offhi[:,1],True),True),add(mul(vh[:,0],p01[1],True),mul(vh[:,1],diaghi[:,0],True),True),add(mul(vh[:,0],p02[1],True),mul(vh[:,2],diaghi[:,1],True),True)]
        vl=np.minimum(1,nl);vh=np.minimum(1,nh)
    Eh=np.minimum(5,UP(Eh+tail))
    lower=[];upper=[]
    for i in [1,2]:
        other=[j for j in range(3) if j!=i]
        denlo=np.maximum(0,DOWN(DOWN(Eh[:,i]+El[:,other[0]])+El[:,other[1]]))
        denhi=UP(UP(El[:,i]+Eh[:,other[0]])+Eh[:,other[1]])
        lower.append(np.maximum(0,DOWN(El[:,i]/denhi)));upper.append(np.minimum(1,UP(Eh[:,i]/denlo)))
    return np.array(lower).T,np.array(upper).T,cache

def certify(row,max_boxes=200000,max_depth=45):
    q=np.array(row['target_ground']);todo=np.array([[0.,0.,1.,1.]]);cache=None;processed=0;levels=[]
    for depth in range(max_depth+1):
        lo,hi,cache=occupation_boxes(row,todo,cache);excluded=np.any((hi<DOWN(q-1e-8))|(lo>UP(q+1e-8)),axis=1);processed+=len(todo)
        keep=todo[~excluded];levels.append(dict(depth=depth,boxes=len(todo),excluded=int(excluded.sum())))
        if not len(keep):return dict(fight_id=row['fight_id'],certified=True,processed_boxes=processed,depth=depth,levels=levels,tail_bound=cache[3])
        if processed>max_boxes or depth==max_depth:return dict(fight_id=row['fight_id'],certified=False,processed_boxes=processed,depth=depth,remaining_boxes=len(keep),levels=levels)
        width=keep[:,2:]-keep[:,:2];side=width.argmax(axis=1);mid=(keep[np.arange(len(keep)),side]+keep[np.arange(len(keep)),side+2])/2
        a=keep.copy();b=keep.copy();a[np.arange(len(keep)),side+2]=mid;b[np.arange(len(keep)),side]=mid;todo=np.r_[a,b]
    raise AssertionError('unreachable')
