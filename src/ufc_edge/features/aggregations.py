"""Contract-faithful sufficient-stat aggregation and shrinkage for F01."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable, Mapping


@dataclass(frozen=True)
class FightStats:
    fight_id: str
    numerators: Mapping[str, float]
    denominator: float
    observation_count: int


@dataclass(frozen=True)
class AggregateStats:
    numerators: dict[str, float]
    denominator: float
    fight_count: int
    observation_count: int
    fight_ids: tuple[str, ...]


@dataclass(frozen=True)
class ShrunkEstimate:
    value: float | None
    raw_value: float | None
    prior_value: float | None
    prior_source: str | None
    numerator: float
    denominator: float
    posterior_denominator: float


def aggregate_fight_stats(
    stats: Iterable[FightStats],
    weights: Mapping[str, float],
) -> AggregateStats:
    numerators: dict[str, float] = {}
    denominator = 0.0
    fight_ids: list[str] = []
    observation_count = 0
    for item in stats:
        if item.fight_id not in weights:
            continue
        weight = float(weights[item.fight_id])
        if weight < 0 or not math.isfinite(weight):
            raise ValueError(f"invalid history weight for {item.fight_id}: {weight}")
        denominator += weight * item.denominator
        for component, numerator in item.numerators.items():
            numerators[component] = numerators.get(component, 0.0) + weight * numerator
        observation_count += item.observation_count
        fight_ids.append(item.fight_id)
    return AggregateStats(
        numerators=numerators,
        denominator=denominator,
        fight_count=len(set(fight_ids)),
        observation_count=observation_count,
        fight_ids=tuple(sorted(set(fight_ids))),
    )


def prior_strength(shrinkage_rule: str) -> float:
    strengths = {
        "attempt_probability_v1": 20.0,
        "composition_v1": 30.0,
        "fight_rate_v1": 6.0,
        "none": 0.0,
    }
    if shrinkage_rule == "time_rate_v1":
        raise ValueError("time_rate_v1 is not materializable under feature contract 0.1.1-draft")
    try:
        return strengths[shrinkage_rule]
    except KeyError as exc:
        raise ValueError(f"unsupported shrinkage rule {shrinkage_rule}") from exc


def shrink_component(
    numerator: float,
    denominator: float,
    *,
    shrinkage_rule: str,
    prior_numerator: float | None,
    prior_denominator: float | None,
    prior_source: str | None,
) -> ShrunkEstimate:
    raw = numerator / denominator if denominator > 0 else None
    strength = prior_strength(shrinkage_rule)
    if strength == 0:
        return ShrunkEstimate(raw, raw, None, None, numerator, denominator, denominator)

    if prior_numerator is None or prior_denominator is None or prior_denominator <= 0:
        return ShrunkEstimate(None, raw, None, prior_source, numerator, denominator, denominator)
    prior = prior_numerator / prior_denominator
    posterior_denominator = denominator + strength
    value = (numerator + strength * prior) / posterior_denominator
    return ShrunkEstimate(
        value=value,
        raw_value=raw,
        prior_value=prior,
        prior_source=prior_source,
        numerator=numerator,
        denominator=denominator,
        posterior_denominator=posterior_denominator,
    )


def minimum_support(feature: Mapping[str, object]) -> float | None:
    """Extract the contract's stated raw-display support threshold when numeric.

    The catalog remains authoritative; this helper does not invent thresholds. It
    only reads the first explicit number in minimum_sample for audit-state labeling.
    """
    text = str(feature["minimum_sample"])
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", text)
    return float(match.group(1)) if match else None


def semantic_state(
    *,
    value: object | None,
    personal_denominator: float | None,
    compatible_observations: int,
    prior_fight_count: int | None,
    minimum: float | None = None,
    not_applicable: bool = False,
    missing_history: bool = False,
) -> str:
    if not_applicable:
        return "not_applicable"
    if missing_history or prior_fight_count is None:
        return "missing_observation"
    if compatible_observations == 0 and prior_fight_count > 0:
        return "missing_observation"
    if personal_denominator is not None and personal_denominator <= 0:
        return "insufficient_exposure"
    if minimum is not None and personal_denominator is not None and personal_denominator < minimum:
        return "insufficient_exposure"
    if value is None:
        return "insufficient_exposure" if prior_fight_count == 0 else "missing_observation"
    if isinstance(value, bool):
        return "observed_positive" if value else "observed_zero"
    if isinstance(value, (int, float)):
        return "observed_zero" if float(value) == 0.0 else "observed_positive"
    return "observed_positive"
