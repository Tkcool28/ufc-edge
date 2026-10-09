"""Outcome-blind numerical, directional and chronology validation."""
import numpy as np
import engine
import abilities as ab

def numerical():
    q=engine.generator([.15,.08],[.4,.6],[.015,.02],[.04,.01],.035)
    p=engine.transition(q)
    assert np.allclose(p.sum(axis=1),1) and p.min()>=0 and p.max()<=1
    r=engine.propagate(q,3)
    # Independent continuous-time transient mass integral (block matrix formula).
    from scipy.linalg import expm
    t=q[:3,:3];b=q[:3,3:];z=expm(t*5)
    absorption=np.linalg.solve(t,(z-np.eye(3))@b)[0]
    survive=z[0].sum()
    exact=absorption*sum(survive**i for i in range(3))
    assert np.allclose(r,[*exact,survive**3],atol=1e-12)
    assert np.allclose(r,engine.propagate(q,3,1/60),atol=1e-12)
    zero=engine.generator([0.,0.],[.4,.5],[0.,0.],[0.,0.],.1)
    assert np.allclose(engine.propagate(zero,3),[1-np.exp(-1.5),0,np.exp(-1.5)],atol=1e-12)
    failed=0
    for bad in [-1.,np.nan,np.inf]:
        try:engine.generator([bad,.1],[.1,.1],[.1,.1],[.1,.1],.1)
        except ValueError:failed+=1
    assert failed==3
    bad=q.copy();bad[0,1]=-1
    try:engine.transition(bad)
    except ValueError:pass
    else:raise AssertionError('Invalid transition accepted')
    k,v=engine.compose(r,.6);assert np.isclose(v.sum(),1.) and np.isclose(v[2],.4)
    return {'normalization':True,'nonnegative_bounded_transitions':True,'closed_form_absorption':True,
      'one_second_vs_round_max_error':float(np.max(np.abs(r-engine.propagate(q,3,1/60)))),
      'analytic_no_ground_case':True,'invalid_input_fail_closed':True}

def chronology(b,pool):
    checks=0
    for _,g in list(b.groupby('fighter_id'))[::47]:
        g=g.sort_values(['event_date','fight_id'])
        if len(g)<3:continue
        cut=g.iloc[len(g)//2].event_date
        prior=pool['divisions'].get(g.iloc[0].division)
        if prior is None:continue
        before=ab.estimate(g[g.event_date<cut],prior)
        changed=g.copy();future=changed.event_date>=cut
        for col in changed.select_dtypes(include='number'):changed.loc[future,col]=99999.
        changed.loc[future,'method']='SUBMISSION'
        after=ab.estimate(changed[changed.event_date<cut],prior)
        assert before==after;checks+=1
    assert checks>=10
    return {'experienced_fighter_target_same_date_future_mutation_checks':checks}

def monte_carlo(q,rounds=3):
    # Independent event-driven Gillespie trajectories, not drawing the saved final
    # probability vector. Fixed seeds; validation only, predictions remain exact.
    target=engine.propagate(q,rounds);rows=[]
    def sample(n):
        rng=np.random.default_rng(161163);counts=np.zeros(3,dtype=int)
        for _ in range(n):
            terminal=2
            for rnd in range(rounds):
                state=0;clock=0.
                while state<3:
                    rate=-q[state,state]
                    if rate==0:break
                    clock+=rng.exponential(1/rate)
                    if clock>=5:break
                    weights=q[state].copy();weights[state]=0
                    state=int(rng.choice(5,p=weights/rate))
                if state>=3:terminal=state-3;break
            counts[terminal]+=1
        return counts/n
    for n in [10000,100000]:
        estimated=sample(n)
        error=float(np.max(np.abs(estimated-target)))
        assert error<6/np.sqrt(n)
        rows.append({'n':n,'estimated':estimated.tolist(),'exact':target.tolist(),'max_absolute_error':error,'six_se_bound':6/np.sqrt(n)})
    assert np.array_equal(sample(10000),np.array(rows[0]['estimated']))
    return {'method':'event-driven Gillespie','seed':161163,'seed_reproducible':True,'count_convergence':rows}

if __name__=='__main__':
    import json
    print(json.dumps(numerical(),sort_keys=True))
