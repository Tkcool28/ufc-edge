"""Deterministic generic-ground Markov propagator (engine only, no fitted hazards).

Probabilities are supplied externally after strict-prior calibration. This module
MUST NOT be used to turn raw UFCStats activity rates directly into hazards.
"""
from dataclasses import dataclass
from math import exp, isfinite


@dataclass(frozen=True)
class HazardSet:
    standing_ko: float
    enter_ground_a: float
    enter_ground_b: float
    ground_ko_a: float
    ground_ko_b: float
    ground_sub_a: float
    ground_sub_b: float
    return_a: float
    return_b: float


def _competing_rates(rates: tuple[float, ...], seconds: float) -> tuple[float, ...]:
    if seconds <= 0 or not isfinite(seconds):
        raise ValueError("step must be finite and positive")
    if any(not isfinite(x) or x < 0 for x in rates):
        raise ValueError("negative/nonfinite transition intensity")
    total = sum(rates)
    if total == 0:
        return (1.0,) + tuple(0.0 for _ in rates)
    survival = exp(-total * seconds)
    each = (1 - survival) / total
    result = (survival,) + tuple(x * each for x in rates)
    if any(x < 0 or x > 1 for x in result) or abs(sum(result) - 1) > 1e-12:
        raise ValueError("invalid transition probabilities")
    return result


def propagate(h: HazardSet, *, fight_seconds: int = 900, step_seconds: int = 1) -> dict[str, float]:
    """Exact discrete-time mass propagation: standing, A ground, B ground, terminals.

    Direction identifies which fighter is active while grounded. A generic state
    does not distinguish guard/mount/escape positions. Decision is remaining
    nonterminal mass at the scheduled fight end; round breaks are not modeled.
    """
    if type(fight_seconds) is not int or fight_seconds <= 0:
        raise ValueError("invalid fight duration")
    if type(step_seconds) is not int or step_seconds <= 0 or fight_seconds % step_seconds:
        raise ValueError("step must divide duration")
    s, ga, gb, ko, sub = 1.0, 0.0, 0.0, 0.0, 0.0
    for _ in range(fight_seconds // step_seconds):
        ss, se_a, se_b, sk = _competing_rates(
            (h.enter_ground_a, h.enter_ground_b, h.standing_ko), step_seconds
        )
        aa, ar, ak, au = _competing_rates(
            (h.return_a, h.ground_ko_a, h.ground_sub_a), step_seconds
        )
        bb, br, bk, bu = _competing_rates(
            (h.return_b, h.ground_ko_b, h.ground_sub_b), step_seconds
        )
        next_s = s * ss + ga * ar + gb * br
        next_a = s * se_a + ga * aa
        next_b = s * se_b + gb * bb
        ko += s * sk + ga * ak + gb * bk
        sub += ga * au + gb * bu
        s, ga, gb = next_s, next_a, next_b
    result = {"ko": ko, "submission": sub, "decision": s + ga + gb}
    if any(not isfinite(x) or x < -1e-12 or x > 1 + 1e-12 for x in result.values()):
        raise ValueError("nonfinite/out-of-range result")
    if abs(sum(result.values()) - 1) > 1e-10:
        raise ValueError("mass conservation failed")
    return result


def compose_external_mov0(finish_probability: float, conditional_ko: float) -> dict[str, float]:
    """Fallback algebra only; frozen MOV0 remains outside the simulator."""
    if any(not isfinite(x) or x < 0 or x > 1 for x in (finish_probability, conditional_ko)):
        raise ValueError("invalid input probability")
    return {"ko": finish_probability * conditional_ko,
            "submission": finish_probability * (1 - conditional_ko),
            "decision": 1 - finish_probability}
