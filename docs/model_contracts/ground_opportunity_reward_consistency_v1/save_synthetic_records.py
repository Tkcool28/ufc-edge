"""Save invented reward fixtures only; no historical records or outcomes."""
import json,sys
from pathlib import Path
import numpy as np
from synthetic_math import solve_synthetic,Unavailable
P=Path(__file__).parent
fixtures=[]
for rounds in (3,5):
    fixtures.append(dict(name='requested_example',rounds=rounds,td=[.2,.2],sub=[4/15]*2,gnp=[20/15]*2,td_success=[.5,.5],target_ground=[.15,.15]))
    for name,q,td in [('low',[.02,.02],[.2,.2]),('asymmetric',[.1,.3],[.2,.4]),('high',[.4,.4],[.2,.2])]:
        fixtures.append(dict(name=name,rounds=rounds,td=td,sub=[.05,.05],gnp=[1.,1.],td_success=[.5,.5],target_ground=q))
    fixtures.append(dict(name='absorbing',rounds=rounds,td=[.4,.3],sub=[.08,.06],gnp=[1.,.6],td_success=[.6,.5],target_ground=[.2,.15],sub_conversion=[.2,.25],ground_conversion=[.002,.003],standing_terminal=.025))
fixtures.extend([dict(name='unresolved_asymmetric',td=[.2,.2],sub=[.05,.05],gnp=[1.,1.],td_success=[.5,.5],target_ground=[.1,.3]),dict(name='infeasible_bilateral',td=[.2,.2],sub=[.05,.05],gnp=[1.,1.],td_success=[.5,.5],target_ground=[.6,.6])])
def serial(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)
records=[]
for fixture in fixtures:
    args={k:v for k,v in fixture.items() if k!='name'}
    try:record=dict(fixture=fixture,status='VALID',result=solve_synthetic(**args))
    except Unavailable as e:record=dict(fixture=fixture,status='UNAVAILABLE',reason=e.code,detail=e.detail)
    records.append(record)
payload=json.loads(json.dumps(dict(real_fights_used=0,records=records),default=serial,allow_nan=False))
if '--check' in sys.argv:
    saved=json.loads((P/'SYNTHETIC_REWARD_RECORDS.json').read_text())
    def compare(a,b,path='root'):
        if isinstance(a,dict):
            assert a.keys()==b.keys(),path
            for key in a:compare(a[key],b[key],path+'/'+key)
        elif isinstance(a,list):
            assert len(a)==len(b),path
            for i,(aa,bb) in enumerate(zip(a,b)):compare(aa,bb,path+'/'+str(i))
        elif isinstance(a,(int,float)) and not isinstance(a,bool):
            if path.endswith('/solver_nfev'):return
            assert abs(a-b)<=1e-7*max(1.,abs(a),abs(b)),(path,a,b)
        else:assert a==b,(path,a,b)
    compare(saved,payload)
    print('PASS: saved synthetic fixtures regenerate within fixed numerical tolerance; metadata matches')
else:
    (P/'SYNTHETIC_REWARD_RECORDS.json').write_text(json.dumps(payload,indent=2)+'\n')
