"""Auditable fighter-state and matchup assembly for F01.

The catalog chooses concepts/variants. This module is an executable dispatch for
those concepts; it fails closed if the active V1 catalog and implementation
registry diverge.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import math
from typing import Any, Iterable

from .aggregations import (
    FightStats,
    aggregate_fight_stats,
    minimum_support,
    semantic_state,
    shrink_component,
)
from .history import (
    AmbiguousWindowBoundary,
    CanonicalStore,
    FightRef,
    as_float,
    as_int,
    parse_cutoff,
    parse_date,
)


ACTIVE_V1_STATUSES = {"V1_MUST", "V1_DERIVED"}

HISTORICAL_IMPLEMENTATIONS = {
    "prior_fight_count",
    "sig_strike_efficiency",
    "sig_target_mix",
    "sig_environment_mix",
    "knockdown_efficiency",
    "takedown_conversion",
    "finish_method_win_profile",
    "finish_method_loss_profile",
    "early_finish_profile",
    "layoff_days",
    "prior_scale_weight_lbs",
}
CONTEXT_IMPLEMENTATIONS = {
    "age_at_fight",
    "physical_size_profile",
    "scheduled_rounds",
    "title_bout",
    "weight_class",
}
MATCHUP_IMPLEMENTATIONS = {
    "knockdown_creation_vs_vulnerability",
    "reach_difference_cm",
}
IMPLEMENTED_V1_CONCEPTS = HISTORICAL_IMPLEMENTATIONS | CONTEXT_IMPLEMENTATIONS | MATCHUP_IMPLEMENTATIONS


class MaterializationError(ValueError):
    """Raised when a contract-selected feature cannot be materialized safely."""


@dataclass(frozen=True)
class AuditValue:
    column_name: str
    source_concept: str
    component: str | None
    window: str | None
    value: Any
    missingness_state: str
    numerator: float | None
    denominator: float | None
    posterior_denominator: float | None
    contributing_fight_count: int
    contributing_observation_count: int
    shrinkage_rule: str
    prior_source: str | None
    prior_value: float | None
    lineage_fight_ids: tuple[str, ...]
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FighterState:
    fighter_id: str
    prediction_as_of: str
    target_fight_id: str | None
    values: dict[str, AuditValue]

    def projection(self) -> dict[str, Any]:
        return {name: self.values[name].value for name in sorted(self.values)}

    def audit_projection(self) -> dict[str, dict[str, Any]]:
        return {name: self.values[name].to_dict() for name in sorted(self.values)}


@dataclass(frozen=True)
class MatchupState:
    fighter_1_id: str
    fighter_2_id: str
    prediction_as_of: str
    target_fight_id: str | None
    fighter_1: FighterState
    fighter_2: FighterState
    interactions: dict[str, AuditValue]

    def projection(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, value in sorted(self.fighter_1.projection().items()):
            result[f"fighter_1__{name}"] = value
        for name, value in sorted(self.fighter_2.projection().items()):
            result[f"fighter_2__{name}"] = value
        result.update({name: self.interactions[name].value for name in sorted(self.interactions)})
        return result


def active_v1_features(catalog: dict[str, Any], consumer: str | None = None) -> list[dict[str, Any]]:
    blocked = set(catalog["elapsed_exposure_policy"]["blocked_feature_concepts"])
    selected: list[dict[str, Any]] = []
    for feature in catalog["features"]:
        if feature["status"] not in ACTIVE_V1_STATUSES:
            continue
        if consumer is not None and consumer not in feature["intended_model_consumers"]:
            continue
        if feature["feature_name"] in blocked:
            raise MaterializationError(f"active V1 concept is blocked by elapsed exposure: {feature['feature_name']}")
        selected.append(feature)
    unknown = {feature["feature_name"] for feature in selected} - IMPLEMENTED_V1_CONCEPTS
    if unknown:
        raise MaterializationError(f"active V1 concepts lack F01 implementation: {sorted(unknown)}")
    return selected


def _windows(feature: dict[str, Any]) -> list[str | None]:
    flags = [
        ("career_variant", "career"),
        ("recent_3_variant", "last3"),
        ("recent_5_variant", "last5"),
        ("ewma_variant", "ewma_365d"),
    ]
    windows = [name for flag, name in flags if feature[flag]]
    return windows or [None]


def concept_columns(catalog: dict[str, Any], feature: dict[str, Any]) -> dict[tuple[str | None, str | None], str]:
    prefix = catalog["materialization_naming"]["layer_prefixes"][feature["layer"]]
    components = feature.get("components") or [None]
    estimator = "shrunk" if feature["shrinkage_rule"] != "none" else "raw"
    result: dict[tuple[str | None, str | None], str] = {}
    for component in components:
        base = f"{prefix}__{feature['feature_name']}"
        if component is not None:
            base += f"__{component}"
        for window in _windows(feature):
            if window is None:
                column = base
            else:
                column = f"{base}__{window}__{estimator}"
            key = (component, window)
            if key in result or column in result.values():
                raise MaterializationError(f"materialized naming collision for {feature['feature_name']}")
            result[key] = column
    return result


def selected_v1_names(catalog: dict[str, Any], consumer: str | None = None) -> list[str]:
    names: list[str] = []
    for feature in active_v1_features(catalog, consumer):
        names.extend(concept_columns(catalog, feature).values())
    if len(names) != len(set(names)):
        raise MaterializationError("selected V1 materialized names collide")
    return sorted(names)


class StateBuilder:
    """Reference-correct F01 state builder over a CanonicalStore."""

    def __init__(self, store: CanonicalStore, catalog: dict[str, Any]):
        self.store = store
        self.catalog = catalog
        self._by_name = {feature["feature_name"]: feature for feature in catalog["features"]}
        all_active = {feature["feature_name"] for feature in active_v1_features(catalog)}
        if all_active != IMPLEMENTED_V1_CONCEPTS:
            raise MaterializationError(
                f"F01 registry/catalog mismatch: missing={sorted(all_active - IMPLEMENTED_V1_CONCEPTS)} "
                f"extra={sorted(IMPLEMENTED_V1_CONCEPTS - all_active)}"
            )
        if catalog["elapsed_exposure_policy"]["allowed_sources"]:
            raise MaterializationError("F01 is pinned to canonical-v0 empty elapsed-exposure allowed_sources")
        self._prior_cache: dict[tuple[str, str, str, str | None], tuple[float, float, str]] = {}

    def _single_fight_stats(self, fighter_id: str, feature_name: str, fight: FightRef) -> dict[str, FightStats]:
        result: dict[str, FightStats] = {}
        rows = self.store.round_rows_for_fight(fighter_id, fight.fight_id)

        if feature_name in {
            "sig_strike_efficiency", "sig_target_mix", "sig_environment_mix",
            "knockdown_efficiency", "takedown_conversion",
        }:
            accum_num: dict[str, float] = {}
            accum_den: dict[str, float] = {}
            obs: dict[str, int] = {}

            def add(component: str, numerator: float, denominator: float) -> None:
                accum_num[component] = accum_num.get(component, 0.0) + numerator
                accum_den[component] = accum_den.get(component, 0.0) + denominator
                obs[component] = obs.get(component, 0) + 1

            for row in rows:
                round_no = int(row["round"])
                opp = self.store.opponent_round_row(fight.fight_id, fighter_id, round_no)
                if feature_name == "sig_strike_efficiency":
                    landed, attempted = as_int(row.get("sig_strikes_landed")), as_int(row.get("sig_strikes_attempted"))
                    if landed is not None and attempted is not None:
                        add("accuracy", landed, attempted)
                    if opp is not None:
                        o_landed, o_attempted = as_int(opp.get("sig_strikes_landed")), as_int(opp.get("sig_strikes_attempted"))
                        if o_landed is not None and o_attempted is not None:
                            add("defense", o_attempted - o_landed, o_attempted)
                elif feature_name == "sig_target_mix":
                    vals = [as_int(row.get(field)) for field in ("sig_head_attempted", "sig_body_attempted", "sig_leg_attempted")]
                    if all(value is not None for value in vals):
                        denominator = float(sum(value for value in vals if value is not None))
                        for component, value in zip(("head_share", "body_share", "leg_share"), vals):
                            add(component, float(value), denominator)
                elif feature_name == "sig_environment_mix":
                    vals = [as_int(row.get(field)) for field in ("sig_distance_attempted", "sig_clinch_attempted", "sig_ground_attempted")]
                    if all(value is not None for value in vals):
                        denominator = float(sum(value for value in vals if value is not None))
                        for component, value in zip(("distance_share", "clinch_share", "ground_share"), vals):
                            add(component, float(value), denominator)
                elif feature_name == "knockdown_efficiency":
                    kd, landed = as_int(row.get("knockdowns")), as_int(row.get("sig_strikes_landed"))
                    if kd is not None and landed is not None:
                        add("creation", kd, landed)
                    if opp is not None:
                        o_kd, o_landed = as_int(opp.get("knockdowns")), as_int(opp.get("sig_strikes_landed"))
                        if o_kd is not None and o_landed is not None:
                            add("vulnerability", o_kd, o_landed)
                elif feature_name == "takedown_conversion":
                    landed, attempted = as_int(row.get("takedowns_landed")), as_int(row.get("takedowns_attempted"))
                    if landed is not None and attempted is not None:
                        add("success", landed, attempted)
                    if opp is not None:
                        o_landed, o_attempted = as_int(opp.get("takedowns_landed")), as_int(opp.get("takedowns_attempted"))
                        if o_landed is not None and o_attempted is not None:
                            add("defense", o_attempted - o_landed, o_attempted)

            for component in sorted(accum_num):
                result[component] = FightStats(
                    fight_id=fight.fight_id,
                    numerators={component: accum_num[component]},
                    denominators={component: accum_den[component]},
                    observation_count=obs[component],
                )
            return result

        if feature_name in {"finish_method_win_profile", "finish_method_loss_profile"}:
            if fight.result is None or fight.method is None:
                return result
            is_win = fight.winner_id == fighter_id
            is_loss = fight.winner_id is not None and fight.winner_id != fighter_id
            for component, method in (("ko_tko", "KO_TKO"), ("submission", "SUBMISSION"), ("decision", "DECISION")):
                event = is_win if feature_name == "finish_method_win_profile" else is_loss
                numerator = 1.0 if event and fight.method == method else 0.0
                result[component] = FightStats(fight.fight_id, {component: numerator}, {component: 1.0}, 1)
            return result

        if feature_name == "early_finish_profile":
            if fight.result is None or fight.method is None or fight.finish_round is None:
                return result
            is_finish = fight.finish_round == 1 and fight.method != "DECISION"
            is_win = fight.winner_id == fighter_id
            is_loss = fight.winner_id is not None and fight.winner_id != fighter_id
            result["r1_finish_win"] = FightStats(
                fight.fight_id, {"r1_finish_win": 1.0 if is_finish and is_win else 0.0}, {"r1_finish_win": 1.0}, 1
            )
            result["r1_finish_loss"] = FightStats(
                fight.fight_id, {"r1_finish_loss": 1.0 if is_finish and is_loss else 0.0}, {"r1_finish_loss": 1.0}, 1
            )
            return result

        raise MaterializationError(f"no sufficient-stat implementation for {feature_name}")

    def _component_history_stats(
        self, fighter_id: str, feature_name: str, prior_fights: Iterable[FightRef]
    ) -> dict[str, list[FightStats]]:
        by_component: dict[str, list[FightStats]] = {}
        for fight in prior_fights:
            for component, stats in self._single_fight_stats(fighter_id, feature_name, fight).items():
                by_component.setdefault(component, []).append(stats)
        return by_component

    def _population_prior(
        self,
        feature_name: str,
        component: str,
        prediction_as_of: str,
        target_weight_class: str | None,
    ) -> tuple[float | None, float | None, str | None]:
        cutoff = parse_cutoff(prediction_as_of).date().isoformat()
        use_weight_class = (
            target_weight_class is not None
            and self.store.fight_count_in_weight_class(target_weight_class, prediction_as_of) >= 100
        )
        scope = target_weight_class if use_weight_class else None
        cache_key = (feature_name, component, cutoff, scope)
        if cache_key in self._prior_cache:
            numerator, denominator, source = self._prior_cache[cache_key]
            return numerator, denominator, source

        numerator = 0.0
        denominator = 0.0
        for fight in self.store.all_prior_fights(prediction_as_of):
            if scope is not None and fight.weight_class != scope:
                continue
            for fighter_id in (fight.fighter_a_id, fight.fighter_b_id):
                stats = self._single_fight_stats(fighter_id, feature_name, fight).get(component)
                if stats is None:
                    continue
                numerator += stats.numerators[component]
                denominator += stats.denominators[component]
        source = f"weight_class:{scope}" if scope is not None else "global"
        self._prior_cache[cache_key] = (numerator, denominator, source)
        if denominator <= 0:
            return None, None, source
        return numerator, denominator, source

    @staticmethod
    def _target_weight_class(store: CanonicalStore, target_fight_id: str | None) -> str | None:
        return store.require_fight(target_fight_id).weight_class if target_fight_id else None

    def _materialize_rate_feature(
        self,
        fighter_id: str,
        prediction_as_of: str,
        target_fight_id: str | None,
        feature: dict[str, Any],
        prior_fight_count: int,
    ) -> dict[str, AuditValue]:
        feature_name = feature["feature_name"]
        prior_fights = self.store.prior_fights(fighter_id, prediction_as_of)
        by_component = self._component_history_stats(fighter_id, feature_name, prior_fights)
        columns = concept_columns(self.catalog, feature)
        target_wc = self._target_weight_class(self.store, target_fight_id)
        result: dict[str, AuditValue] = {}
        for (component, window), column in columns.items():
            assert component is not None and window is not None
            stats = by_component.get(component, [])
            eligible_fights = [self.store.require_fight(item.fight_id) for item in stats]
            try:
                selection = self.store.select_window(eligible_fights, window, prediction_as_of)
            except AmbiguousWindowBoundary as exc:
                result[column] = AuditValue(
                    column, feature_name, component, window, None, "missing_observation",
                    None, None, None, 0, 0, feature["shrinkage_rule"], None, None, (), str(exc)
                )
                continue
            aggregate = aggregate_fight_stats(stats, selection.weights)
            numerator = aggregate.numerators.get(component, 0.0)
            denominator = aggregate.denominators.get(component, 0.0)
            prior_num, prior_den, prior_source = self._population_prior(
                feature_name, component, prediction_as_of, target_wc
            )
            estimate = shrink_component(
                numerator,
                denominator,
                shrinkage_rule=feature["shrinkage_rule"],
                prior_numerator=prior_num,
                prior_denominator=prior_den,
                prior_source=prior_source,
            )
            state = semantic_state(
                value=estimate.value,
                personal_denominator=denominator,
                compatible_observations=aggregate.observation_count,
                prior_fight_count=prior_fight_count,
                minimum=minimum_support(feature),
            )
            result[column] = AuditValue(
                column_name=column,
                source_concept=feature_name,
                component=component,
                window=window,
                value=estimate.value,
                missingness_state=state,
                numerator=numerator,
                denominator=denominator,
                posterior_denominator=estimate.posterior_denominator,
                contributing_fight_count=aggregate.fight_count,
                contributing_observation_count=aggregate.observation_count,
                shrinkage_rule=feature["shrinkage_rule"],
                prior_source=estimate.prior_source,
                prior_value=estimate.prior_value,
                lineage_fight_ids=aggregate.fight_ids,
            )
        return result

    def _simple_value(
        self,
        feature: dict[str, Any],
        column: str,
        value: Any,
        *,
        fighter_id: str,
        prediction_as_of: str,
        prior_fight_count: int,
        component: str | None = None,
        fight_ids: tuple[str, ...] = (),
        observation_count: int = 0,
        reason: str | None = None,
        force_state: str | None = None,
    ) -> AuditValue:
        state = force_state or semantic_state(
            value=value,
            personal_denominator=None,
            compatible_observations=observation_count,
            prior_fight_count=prior_fight_count,
            not_applicable=force_state == "not_applicable",
        )
        return AuditValue(
            column, feature["feature_name"], component, None, value, state,
            None, None, None, len(set(fight_ids)), observation_count,
            feature["shrinkage_rule"], None, None, tuple(sorted(set(fight_ids))), reason
        )

    def materialize_fighter(
        self,
        fighter_id: str,
        prediction_as_of: str,
        *,
        target_fight_id: str | None = None,
        consumer: str | None = None,
    ) -> FighterState:
        self.store.require_fighter(fighter_id)
        cutoff = parse_cutoff(prediction_as_of).isoformat().replace("+00:00", "Z")
        prior_fights = self.store.prior_fights(fighter_id, cutoff)
        prior_count = len({fight.fight_id for fight in prior_fights})
        selected = active_v1_features(self.catalog, consumer)
        values: dict[str, AuditValue] = {}

        for feature in selected:
            name = feature["feature_name"]
            if name in MATCHUP_IMPLEMENTATIONS:
                continue
            columns = concept_columns(self.catalog, feature)

            if name == "prior_fight_count":
                column = columns[(None, "career")]
                values[column] = AuditValue(
                    column, name, None, "career", prior_count,
                    "observed_zero" if prior_count == 0 else "observed_positive",
                    float(prior_count), float(prior_count), float(prior_count), prior_count, prior_count,
                    "none", None, None, tuple(sorted(f.fight_id for f in prior_fights)), None
                )
            elif name in {
                "sig_strike_efficiency", "sig_target_mix", "sig_environment_mix",
                "knockdown_efficiency", "takedown_conversion",
                "finish_method_win_profile", "finish_method_loss_profile", "early_finish_profile",
            }:
                values.update(self._materialize_rate_feature(
                    fighter_id, cutoff, target_fight_id, feature, prior_count
                ))
            elif name == "layoff_days":
                column = columns[(None, None)]
                if not prior_fights:
                    value, state, reason, lineage = None, "not_applicable", "no eligible prior fight", ()
                else:
                    latest_date = max(f.event_date for f in prior_fights)
                    latest = sorted(f.fight_id for f in prior_fights if f.event_date == latest_date)
                    if len(latest) > 1:
                        value, state, reason, lineage = None, "missing_observation", "most-recent prior fight date is tied; chronology unresolved", tuple(latest)
                    else:
                        target_date = self.store.require_fight(target_fight_id).event_date if target_fight_id else parse_cutoff(cutoff).date()
                        value = (target_date - latest_date).days
                        state, reason, lineage = "observed_positive", None, tuple(latest)
                values[column] = self._simple_value(
                    feature, column, value, fighter_id=fighter_id, prediction_as_of=cutoff,
                    prior_fight_count=prior_count, fight_ids=lineage, observation_count=len(lineage),
                    reason=reason, force_state=state
                )
            elif name == "prior_scale_weight_lbs":
                column = columns[(None, None)]
                row = self.store.prior_scale_weight(fighter_id, cutoff)
                if row is None:
                    values[column] = self._simple_value(
                        feature, column, None, fighter_id=fighter_id, prediction_as_of=cutoff,
                        prior_fight_count=prior_count, reason="no explicit prior canonical scale weight",
                        force_state="missing_observation"
                    )
                else:
                    weight = as_float(row.get("scale_weight_lbs"))
                    values[column] = self._simple_value(
                        feature, column, weight, fighter_id=fighter_id, prediction_as_of=cutoff,
                        prior_fight_count=prior_count, fight_ids=(row["fight_id"],), observation_count=1
                    )
            elif name == "age_at_fight":
                column = columns[(None, None)]
                if target_fight_id is None:
                    values[column] = self._simple_value(
                        feature, column, None, fighter_id=fighter_id, prediction_as_of=cutoff,
                        prior_fight_count=prior_count, reason="target_fight_id required for age_at_fight",
                        force_state="not_applicable"
                    )
                else:
                    dob = self.store.require_fighter(fighter_id).get("dob")
                    if not dob:
                        values[column] = self._simple_value(
                            feature, column, None, fighter_id=fighter_id, prediction_as_of=cutoff,
                            prior_fight_count=prior_count, reason="canonical DOB missing",
                            force_state="missing_observation"
                        )
                    else:
                        target_date = self.store.require_fight(target_fight_id).event_date
                        age = (target_date - parse_date(dob)).days / 365.2425
                        values[column] = self._simple_value(
                            feature, column, age, fighter_id=fighter_id, prediction_as_of=cutoff,
                            prior_fight_count=prior_count, observation_count=1
                        )
            elif name == "physical_size_profile":
                fighter = self.store.require_fighter(fighter_id)
                for component in ("height_cm", "reach_cm"):
                    column = columns[(component, None)]
                    value = as_float(fighter.get(component))
                    values[column] = self._simple_value(
                        feature, column, value, component=component, fighter_id=fighter_id,
                        prediction_as_of=cutoff, prior_fight_count=prior_count,
                        observation_count=1 if value is not None else 0,
                        reason=None if value is not None else f"canonical {component} missing",
                        force_state=None if value is not None else "missing_observation"
                    )
            elif name in {"scheduled_rounds", "title_bout", "weight_class"}:
                column = columns[(None, None)]
                if target_fight_id is None:
                    values[column] = self._simple_value(
                        feature, column, None, fighter_id=fighter_id, prediction_as_of=cutoff,
                        prior_fight_count=prior_count, reason="target_fight_id required for target context",
                        force_state="not_applicable"
                    )
                else:
                    target = self.store.require_fight(target_fight_id)
                    if not target.includes(fighter_id):
                        raise MaterializationError(f"fighter {fighter_id} is not a participant in target fight {target_fight_id}")
                    raw = {
                        "scheduled_rounds": target.scheduled_rounds,
                        "title_bout": target.title_bout,
                        "weight_class": target.weight_class,
                    }[name]
                    values[column] = self._simple_value(
                        feature, column, raw, fighter_id=fighter_id, prediction_as_of=cutoff,
                        prior_fight_count=prior_count, observation_count=1 if raw is not None else 0,
                        reason=None if raw is not None else f"target {name} missing",
                        force_state=None if raw is not None else "missing_observation"
                    )
            else:
                raise MaterializationError(f"selected non-matchup concept has no materializer: {name}")

        expected = {
            name for feature in selected if feature["feature_name"] not in MATCHUP_IMPLEMENTATIONS
            for name in concept_columns(self.catalog, feature).values()
        }
        if set(values) != expected:
            raise MaterializationError(
                f"fighter-state column mismatch missing={sorted(expected-set(values))} extra={sorted(set(values)-expected)}"
            )
        return FighterState(fighter_id, cutoff, target_fight_id, values)

    @staticmethod
    def orient(fighter_a_id: str, fighter_b_id: str) -> tuple[str, str]:
        if fighter_a_id == fighter_b_id:
            raise MaterializationError("matchup requires two distinct canonical fighter IDs")
        return tuple(sorted((fighter_a_id, fighter_b_id)))  # type: ignore[return-value]

    def materialize_matchup(
        self,
        fighter_a_id: str,
        fighter_b_id: str,
        prediction_as_of: str,
        *,
        target_fight_id: str | None = None,
        consumer: str | None = None,
    ) -> MatchupState:
        fighter_1_id, fighter_2_id = self.orient(fighter_a_id, fighter_b_id)
        f1 = self.materialize_fighter(fighter_1_id, prediction_as_of, target_fight_id=target_fight_id, consumer=consumer)
        f2 = self.materialize_fighter(fighter_2_id, prediction_as_of, target_fight_id=target_fight_id, consumer=consumer)
        selected = active_v1_features(self.catalog, consumer)
        interactions: dict[str, AuditValue] = {}

        for feature in selected:
            name = feature["feature_name"]
            if name not in MATCHUP_IMPLEMENTATIONS:
                continue
            columns = concept_columns(self.catalog, feature)
            if name == "reach_difference_cm":
                out = columns[(None, None)]
                source_feature = self._by_name["physical_size_profile"]
                source_columns = concept_columns(self.catalog, source_feature)
                c = source_columns[("reach_cm", None)]
                a, b = f1.values.get(c), f2.values.get(c)
                if a is None or b is None:
                    raise MaterializationError("reach interaction dependency was not selected for consumer")
                if a.value is None or b.value is None:
                    value, state, reason = None, "missing_observation", "reach dependency missing"
                else:
                    value, state, reason = float(a.value) - float(b.value), "observed_zero" if float(a.value) == float(b.value) else "observed_positive", None
                interactions[out] = AuditValue(
                    out, name, None, None, value, state, None, None, None, 0, 0, "none", None, None, (), reason
                )
            elif name == "knockdown_creation_vs_vulnerability":
                source_feature = self._by_name["knockdown_efficiency"]
                source_cols = concept_columns(self.catalog, source_feature)
                for window in ("career", "last5"):
                    a_creation = f1.values.get(source_cols[("creation", window)])
                    a_vuln = f1.values.get(source_cols[("vulnerability", window)])
                    b_creation = f2.values.get(source_cols[("creation", window)])
                    b_vuln = f2.values.get(source_cols[("vulnerability", window)])
                    if None in {a_creation, a_vuln, b_creation, b_vuln}:
                        raise MaterializationError("KD interaction dependency was not selected for consumer")
                    pairs = {
                        "f1_vs_f2": (a_creation, b_vuln),
                        "f2_vs_f1": (b_creation, a_vuln),
                    }
                    for component, (attack, vulnerability) in pairs.items():
                        out = columns[(component, window)]
                        assert attack is not None and vulnerability is not None
                        if attack.value is None or vulnerability.value is None:
                            value, state, reason = None, "missing_observation", "knockdown-efficiency dependency missing"
                        else:
                            value = float(attack.value) - float(vulnerability.value)
                            state, reason = "observed_zero" if value == 0 else "observed_positive", None
                        interactions[out] = AuditValue(
                            out, name, component, window, value, state, None, None, None,
                            0, 0, "none", None, None, (), reason
                        )

        expected = {
            name for feature in selected if feature["feature_name"] in MATCHUP_IMPLEMENTATIONS
            for name in concept_columns(self.catalog, feature).values()
        }
        if set(interactions) != expected:
            raise MaterializationError(
                f"matchup column mismatch missing={sorted(expected-set(interactions))} extra={sorted(set(interactions)-expected)}"
            )
        return MatchupState(fighter_1_id, fighter_2_id, f1.prediction_as_of, target_fight_id, f1, f2, interactions)
