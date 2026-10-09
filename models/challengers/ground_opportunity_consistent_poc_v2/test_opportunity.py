"""Verify the real wrapper preserves every frozen synthetic equation and rejection."""
import sys,unittest,importlib.util
import numpy as np
from preflight import CON
import opportunity as real
spec=importlib.util.spec_from_file_location('frozen_synthetic',CON/'synthetic_math.py');frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
class FrozenEquivalence(unittest.TestCase):
    def test_solutions(self):
        for rounds in [3,5]:
            for q in [[.02,.02],[.1,.3],[.4,.4]]:
                args=([.3,.4],[.05,.04],[.8,1.],[.6,.7],q,[.1,.12],[.005,.005],.03,rounds)
                a=real.solve(*args);b=frozen.solve_synthetic(*args)
                for key in b:
                    if isinstance(b[key],dict):
                        for k in b[key]:np.testing.assert_array_equal(a[key][k],b[key][k])
                    else:np.testing.assert_equal(a[key],b[key])
    def test_failures(self):
        for args in [([.3,.3],[.1,.1],[1.,1.],[.5,.5],[.6,.6]),([.01,.01],[1.,1.],[1.,1.],[.1,.1],[.1,.1],[.8,.8]),([.02,.02],[0.,0.],[0.,0.],[.5,.5],[.4,.4])]:
            with self.assertRaises(real.Unavailable) as x:real.solve(*args)
            with self.assertRaises(frozen.Unavailable) as y:frozen.solve_synthetic(*args)
            self.assertEqual(x.exception.code,y.exception.code)
if __name__=='__main__':unittest.main()
