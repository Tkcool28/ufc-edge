"""Invented fixtures only. No canonical fights, fighter records, targets or scores."""
import unittest,json
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.linalg import expm
from synthetic_math import solve_synthetic,exposures,Unavailable,CONFIG
class ConservationContract(unittest.TestCase):
    def assert_rewards(self,x):
        self.assertLess(x['occupancy_error'],1e-8)
        self.assertAlmostEqual(sum(x['shares']),1,places=11)
        self.assertTrue(np.all(x['returns']>=0))
        for key in x['actions']:np.testing.assert_allclose(x['actions'][key],x['targets'][key],rtol=1e-7,atol=1e-8)
        np.testing.assert_allclose(x['flux_residual'],0,atol=1e-8)
    def test_requested_example_both_round_lengths(self):
        for rounds in (3,5):
            x=solve_synthetic([3/15]*2,[4/15]*2,[20/15]*2,[.5,.5],[.15,.15],rounds=rounds)
            self.assert_rewards(x)
            np.testing.assert_allclose(x['actions']['TD'],[rounds]*2,atol=1e-8)
            np.testing.assert_allclose(x['actions']['SUB'],[4*rounds/3]*2,atol=1e-8)
            np.testing.assert_allclose(x['actions']['GNP'],[20*rounds/3]*2,atol=1e-8)
            self.assertAlmostEqual(x['minutes'][1:].sum(),.3*rounds*5,places=7)
            np.testing.assert_allclose(x['implicit_SUB_multiplier'],[1/.15]*2)
    def test_thirty_percent_actor_opportunity_example(self):
        for rounds in (3,5):
            x=solve_synthetic([3/15,.2],[4/15,.05],[20/15,.5],[1.,.5],[.3,.02],rounds=rounds)
            self.assert_rewards(x)
            self.assertAlmostEqual(x['minutes'][1],.3*5*rounds,places=7)
            self.assertAlmostEqual(x['actions']['SUB'][0],4*rounds/3,places=7)
    def test_low_high_bilateral_opportunity(self):
        for q in ([.02,.02],[.1,.3],[.4,.4]):
            for rounds in (3,5):
                td=[.2,.4] if q==[.1,.3] else [.2,.2]
                x=solve_synthetic(td,[.05,.05],[1.,1.],[.5,.5],q,rounds=rounds)
                self.assert_rewards(x)
                self.assertLessEqual(max(x['implicit_SUB_multiplier']),50.)
    def test_absorption_uses_alive_exposure_not_schedule(self):
        for rounds in (3,5):
            x=solve_synthetic([.4,.3],[.08,.06],[1.,.6],[.6,.5],[.2,.15],[.2,.25],[.002,.003],.025,rounds)
            self.assert_rewards(x)
            self.assertLess(x['alive'],5*rounds)
            self.assertAlmostEqual(float(x['actions']['SUB'][0]),.08*x['alive'],places=8)
            self.assertGreater(abs(float(x['actions']['SUB'][0])-.08*5*rounds),.01)
    def test_side_swap(self):
        args=[[.4,.3],[.08,.06],[1.,.6],[.6,.5],[.2,.15],[.2,.25],[.002,.003]]
        x=solve_synthetic(*args,standing_terminal=.025,rounds=5);y=solve_synthetic(*[a[::-1] for a in args],standing_terminal=.025,rounds=5)
        np.testing.assert_allclose(x['returns'],y['returns'][::-1],atol=1e-7)
        np.testing.assert_allclose(x['minutes'][1:],y['minutes'][1:][::-1],atol=1e-7)
        for k in x['actions']:np.testing.assert_allclose(x['actions'][k],y['actions'][k][::-1],atol=1e-7)
    def test_round_renewal_ratios_and_counts(self):
        args=[[.4,.3],[.08,.06],[1.,.6],[.6,.5],[.2,.15],[.2,.25],[.002,.003]]
        a=solve_synthetic(*args,standing_terminal=.025,rounds=3);b=solve_synthetic(*args,standing_terminal=.025,rounds=5)
        np.testing.assert_allclose(a['returns'],b['returns'],atol=1e-8)
        self.assertGreater(b['alive'],a['alive']);self.assertGreater(b['actions']['SUB'][0],a['actions']['SUB'][0])
    def test_synthetic_reproducibility(self):
        args=[[.4,.3],[.08,.06],[1.,.6],[.6,.5],[.2,.15],[.2,.25],[.002,.003]]
        a=solve_synthetic(*args,standing_terminal=.025);b=solve_synthetic(*args,standing_terminal=.025)
        np.testing.assert_array_equal(a['returns'],b['returns']);np.testing.assert_array_equal(a['minutes'],b['minutes'])
    def test_impossible_bilateral_share(self):
        with self.assertRaisesRegex(Unavailable,'INFEASIBLE_SIMPLEX'):solve_synthetic([.2]*2,[.1]*2,[1.]*2,[.5]*2,[.6,.6])
    def test_tiny_eligible_share_not_clipped(self):
        with self.assertRaisesRegex(Unavailable,'INFEASIBLE_SIMPLEX'):solve_synthetic([.2]*2,[.1]*2,[1.]*2,[.5]*2,[.001,.3])
    def test_asymmetric_target_not_silently_projected(self):
        with self.assertRaisesRegex(Unavailable,'UNRESOLVED_FINITE_ROUND_TARGET'):solve_synthetic([.2,.2],[.05,.05],[1.,1.],[.5,.5],[.1,.3])
    def test_terminal_reward_exceeds_entry(self):
        with self.assertRaisesRegex(Unavailable,'NO_POSITIVE_RESET_BUDGET'):solve_synthetic([.01]*2,[.5]*2,[1.]*2,[.5]*2,[.2,.2],[.5]*2)
    def test_finite_round_entry_ceiling(self):
        with self.assertRaisesRegex(Unavailable,'INFEASIBLE_FINITE_ROUND_CEILING'):solve_synthetic([.00001]*2,[.1]*2,[1.]*2,[.5]*2,[.3,.3])
    def test_invalid_input_and_rounds(self):
        for td in ([float('nan'),.2],[-.1,.2]):
            with self.assertRaisesRegex(Unavailable,'INVALID_INPUT'):solve_synthetic(td,[.1]*2,[1.]*2,[.5]*2,[.2,.2])
        with self.assertRaisesRegex(Unavailable,'ROUND_STRUCTURE'):solve_synthetic([.2]*2,[.1]*2,[1.]*2,[.5]*2,[.2,.2],rounds=4)
        with self.assertRaisesRegex(Unavailable,'INVALID_CONVERSION'):solve_synthetic([.2]*2,[.1]*2,[1.]*2,[1.1,.5],[.2,.2])
    def test_debut_prior_and_tiny_conversion_support(self):
        self.assertEqual((0+30*.2)/(0+30),.2)
        converted=(1+50*.3)/(1+50);self.assertLess(converted,.32);self.assertGreater(converted,.3)
        self.assertEqual(CONFIG['arms'],['POC_A_EXACT_PR163_SAVED_REFERENCE','POC_B_OPPORTUNITY_MAPPING_ONLY'])
    def test_conditional_reward_ratio_equivalence(self):
        values=[]
        for rounds in (3,5):
            td=np.array([.4,.3]);sub=np.array([.08,.06]);gnp=np.array([1.,.6]);cv=np.array([.2,.25]);gv=np.array([.002,.003]);q=np.array([.2,.15]);standing=.025
            x=solve_synthetic(td,sub,gnp,[.6,.5],q,cv,gv,standing,rounds)
            KO=standing*x['minutes'][0]+sum(x['actions']['GNP']*gv);SUB=sum(x['actions']['SUB']*cv)
            flat=(standing*(1-q.sum())+sum(gnp*gv))/(standing*(1-q.sum())+sum(gnp*gv)+sum(sub*cv))
            self.assertAlmostEqual(KO/(KO+SUB),flat,places=8);values.append(KO/(KO+SUB))
            np.testing.assert_allclose(x['boundary_removal_mass'],x['interround_reset_mass']+x['fight_expiry_ground_mass'],atol=1e-12)
        self.assertAlmostEqual(*values,places=8)
    def test_zero_submission_reward_multiplier_is_undefined(self):
        x=solve_synthetic([.2,.2],[0.,.05],[1.,1.],[.5,.5],[.15,.15])
        self.assert_rewards(x)
        self.assertEqual(x["actions"]["SUB"][0],0)
        self.assertIsNone(x["implicit_SUB_multiplier"][0])
        self.assertEqual(x["implicit_SUB_multiplier_null_reason"][0],"ZERO_TOTAL_RATE")
        self.assertAlmostEqual(x["opportunity_scale_operator"][0],1/.15)
    def test_independent_quadrature(self):
        e=[.3,.2];r=[.4,.7];h=[.02,.03];x=exposures(e,r,h,.025,3)
        t=np.array([[-.525,.3,.2],[.4,-.42,0],[.7,0,-.73]])
        for i in range(3):self.assertAlmostEqual(quad(lambda tm:expm(t*tm)[0,i],0,5)[0],x['one_round'][i],places=11)
    def test_probability_normalization_at_times_and_resets(self):
        q=np.array([[-.525,.3,.2,.025,0],[.4,-.42,0,.005,.015],[.7,0,-.73,.01,.02],[0,0,0,0,0],[0,0,0,0,0]])
        v=np.array([1.,0.,0.,0.,0.]);p=expm(q/60)
        self.assertGreaterEqual(p.min(),-1e-12);self.assertLessEqual(p.max(),1+1e-12)
        for _ in range(5):
            for _ in range(300):v=v@p;self.assertAlmostEqual(v.sum(),1,places=10);self.assertGreaterEqual(v.min(),-1e-12)
            v[0]=v[:3].sum();v[1:3]=0
            self.assertAlmostEqual(v.sum(),1,places=10)
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ConservationContract);result=unittest.TextTestRunner(verbosity=2).run(suite)
    Path(__file__).with_name('SYNTHETIC_VALIDATION.json').write_text(json.dumps({'status':'PASS' if result.wasSuccessful() else 'FAIL','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'real_fights_used':0,'POC_B_executed':False,'outcomes_scored':0},indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
