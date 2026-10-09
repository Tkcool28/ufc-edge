"""Mathematical certificate validation; no outcomes or scoring."""
import json,sys,unittest
from pathlib import Path
import numpy as np
from bounds import envelope_certificate,rates
from interval_cover import occupation_boxes,certify
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'models/challengers/ground_opportunity_consistent_poc_v2'))
import opportunity as op

class Certificates(unittest.TestCase):
    def test_real_box_enclosures(self):
        records=json.loads((ROOT/'models/challengers/ground_opportunity_consistent_poc_v2/run_v1/opportunity_transition_reward_records.json').read_text())
        rng=np.random.default_rng(166)
        for row in [x for x in records if x['status']=='UNAVAILABLE'][::19]:
            q,s,e,h,hs=rates(row);U=np.array(row['detail']['return_upper_bound']);points=rng.random((8,2));lo=np.maximum(0,points-.05);hi=np.minimum(1,points+.05);boxes=np.c_[lo,hi]
            lower,upper,_=occupation_boxes(row,boxes)
            for i,p in enumerate(points):
                shares=op.exposures(e,p*U,h,hs,row['scheduled_rounds'])['shares'][1:]
                self.assertTrue(np.all(lower[i]<=shares));self.assertTrue(np.all(shares<=upper[i]))
    def test_known_feasible_fixture(self):
        e=np.array([.2,.15]);r=np.array([.2,.1]);h=np.array([.03,.04]);hs=.02
        x=op.exposures(e,r,h,hs,3);q=x['shares'][1:];s=x['shares'][0];td=e*s/.5
        row={'target_ground':q.tolist(),'standing_target':float(s),'TD_reward':td.tolist(),'TD_success':[.5,.5],'SUB_reward':(h*q/.1).tolist(),'SUB_conversion':[.1,.1],'GNP_reward':[0.,0.],'GNP_conversion':[0.,0.],'standing_KO':hs,'fight_id':'fixture'}
        U=td*.5/q-h;row['detail']={'return_upper_bound':U.tolist()}
        self.assertFalse(envelope_certificate(row)['certified'])
        gamma=r/U;box=np.r_[gamma,gamma][None,:];lo,hi,_=occupation_boxes(row,box)
        self.assertTrue(np.all(lo[0]<=q));self.assertTrue(np.all(q<=hi[0]))
    def test_known_infeasible_zero_terminal_fixture(self):
        row={'target_ground':[.4,.4],'standing_target':.2,'TD_reward':[.004,.004],'TD_success':[.5,.5],'SUB_reward':[0.,0.],'SUB_conversion':[0.,0.],'GNP_reward':[0.,0.],'GNP_conversion':[0.,0.],'standing_KO':0.,'fight_id':'fixture','detail':{'return_upper_bound':[.005,.005]}}
        self.assertTrue(certify(row)['certified'])
if __name__=='__main__':unittest.main()
