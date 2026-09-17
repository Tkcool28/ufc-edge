import math
from tools.validation.build_bucket_assignment_v1 import bucket_experience, bucket_layoff, classify, required_mean

def test_bucket_boundaries_are_exact():
    assert [bucket_experience(x,x) for x in (0,1,2,3,5,6,10,11)] == ["0","1–2","1–2","3–5","3–5","6–10","6–10","11+"]
    assert [bucket_layoff(x,x) for x in (182,183,364,365,547,548)] == ["< 6 months","6–12 months","6–12 months","12–18 months","12–18 months","18+ months"]

def test_environment_is_swap_invariant_and_side_flips():
    left=classify(.8,.2,.5,"STRIKE","a","b"); right=classify(.2,.8,.5,"STRIKE","b","a")
    assert left[0] == right[0] == "STRIKE_ONE_SIDED"
    assert left[1] == right[1] == "a"
    assert classify(.8,.8,.5,"STRIKE","a","b") == ("STRIKE_TWO_SIDED","BOTH")
    assert classify(.2,.2,.5,"STRIKE","a","b") == ("STRIKE_LOW","NONE")

def test_missing_rich_component_is_unassignable_not_low():
    assert math.isnan(required_mean([.5, float("nan")]))
    assert classify(float("nan"),.1,.5,"GRAPPLE","a","b") == ("UNASSIGNABLE_BY_CONTRACT","UNASSIGNABLE")
