"""Outcome-free algebraic audit. No estimator, labels, or repository mutation."""
from math import isclose

def symmetric(x):
    return ((x[0]+x[1])/2, abs(x[0]-x[1]))

def directional(p,v):
    return p[0]*v[1]+p[1]*v[0]

def run():
    pressure=(.9,.1)
    vuln_A=(.1,.9)
    vuln_B=(.9,.1)
    assert symmetric(pressure)==symmetric(pressure)
    assert symmetric(vuln_A)==symmetric(vuln_B)
    assert isclose(directional(pressure,vuln_A),.82)
    assert isclose(directional(pressure,vuln_B),.18)
    # Hold all other fighter pairs, shared context and the existing KD directional pair identical.
    # These two fights then have an identical frozen MIN linear input and tree input.
    # The original f1/f2 alignment differs, although both outputs are invariant to simultaneous fighter swap.
    for p,v in [(pressure,vuln_A),(pressure,vuln_B)]:
        assert isclose(directional(p,v),directional(p[::-1],v[::-1]))
    return 'PASS: same marginal mean/absolute gaps, different cross-fighter SUB alignment (0.82 vs 0.18)'

if __name__=='__main__': print(run())
