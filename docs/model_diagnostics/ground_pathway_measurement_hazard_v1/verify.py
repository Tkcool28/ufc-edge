"""Independent quadrature checks for reward accounting; immutable-source verification."""
import json,sys,hashlib
import numpy as np
from scipy.integrate import quad
from scipy.linalg import expm
import audit
P=audit.OUT
records=json.loads((audit.SRC/'run_v1/simulator_records.json').read_text())
err=0.
for h in [r for r in records if r['variant']=='identity'][::426]:
 q=audit.engine.generator(**{k:h[k] for k in ['entry','back','ground_ko','submission','standing_ko']});t=q[:3,:3];survival=expm(5*t)[0].sum();mult=sum(survival**r for r in range(h['scheduled_rounds']))
 minutes=np.array([quad(lambda tm:expm(tm*t)[0,i],0,5,epsabs=1e-11)[0]*mult for i in range(3)])
 a=audit.account(h,h['scheduled_rounds']);err=max(err,abs(minutes[1:].sum()-a['ground_minutes']))
 raw=audit.engine.propagate(q,h['scheduled_rounds']);err=max(err,float(np.max(abs(raw-[a['ground_ko']+a['standing_ko'],a['sub_finishes'],a['raw_dec']]))))
 bad=dict(h,entry=[-1.,0.]);
 try:audit.account(bad,3)
 except ValueError:pass
 else:raise AssertionError('Invalid hazard accepted')
assert err<1e-10
v=json.loads((P/'VALIDATION.json').read_text());v['independent_quadrature_max_error']=err;v['negative_hazard_rejected']=True
(P/'VALIDATION.json').write_text(json.dumps(v,indent=2))
print(json.dumps(v,indent=2))
