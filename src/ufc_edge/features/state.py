"""Auditable fighter-state and matchup assembly for F01.

The catalog chooses concepts and variants. This module provides executable
implementations for exactly the currently active V1 surface and fails closed if
that surface changes without reviewed implementation work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .aggregations import (
    FightStats,
    aggregate_fight_stats,
    minimum_support,
    semantic_state,
    shrink_component,
)
from .elapsed_exposure import control_share, infer_round_exposure, load_registry
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
    "sig_strike_flow",
    "knockdown_rate",
    "takedown_pressure",
    "control_rate",
    "submission_attempt_rate",
    "reversal_rate",
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
        output: dict[str, Any] = {}
        for name, value in sorted(self.fighter_1.projection().items()):
            output[f"fighter_1__{name}"] = value
        for name, value in sorted(self.fighter_2.projection().items()):
            output[f"fighter_2__{name}"] = value
        output.update({name: self.interactions[name].value for name in sorted(self.interactions)})
        return output


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
    missing = {feature["feature_name"] for feature in selected} - IMPLEMENTED_V1_CONCEPTS
    if missing:
        raise MaterializationError(f"active V1 concepts lack F01 implementation: {sorted(missing)}")
    return selected


def _windows(feature: dict[str, Any]) -> list[str | None]:
    flags = (
        ("career_variant", "career"),
        ("recent_3_variant", "last3"),
        ("recent_5_variant", "last5"),
        ("ewma_variant", "ewma_365d"),
    )
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
            column = base if window is None else f"{base}__{window}__{estimator}"
            key = (component, window)
            if key in result or column in result.values():
                raise MaterializationError(f"materialized naming collision for {feature['feature_name']}")
            result[key] = column
    return result


def selected_v1_names(catalog: dict[str, Any], consumer: str | None = None) -> list[str]:
    names = [
        column
        for feature in active_v1_features(catalog, consumer)
        for column in concept_columns(catalog, feature).values()
    ]
    if len(names) != len(set(names)):
        raise MaterializationError("selected V1 materialized names collide")
    return sorted(names)


class StateBuilder:
    """Reference-correct F01 state builder over a CanonicalStore."""

    def __init__(self, store: CanonicalStore, catalog: dict[str, Any]):
        self.store = store
        self.catalog = catalog
        self._by_name = {feature["feature_name"]: feature for feature in catalog["features"]}
        active = {feature["feature_name"] for feature in active_v1_features(catalog)}
        if active != IMPLEMENTED_V1_CONCEPTS:
            raise MaterializationError(
                f"F01 registry/catalog mismatch: missing={sorted(active - IMPLEMENTED_V1_CONCEPTS)} "
                f"extra={sorted(IMPLEMENTED_V1_CONCEPTS - active)}"
            )
        allowed_elapsed = catalog["elapsed_exposure_policy"]["allowed_sources"]
        if allowed_elapsed != ["ruleset_registry_v1"]:
            raise MaterializationError(
                f"F01 requires the reviewed ruleset_registry_v1 elapsed source, got {allowed_elapsed}"
            )
        self._elapsed_registry = load_registry(store.root)
        self._round_elapsed_cache: dict[tuple[str, int], int | None] = {}
        self._prior_cache: dict[tuple[str, str, str, str | None], tuple[float, float, str]] = {}

    def _round_elapsed_sec(self, fight: FightRef, round_no: int) -> int | None:
        key = (fight.fight_id, round_no)
        if key in self._round_elapsed_cache:
            return self._round_elapsed_cache[key]
        payload = {
            "fight_id": fight.fight_id,
            "promotion": fight.promotion,
            "method": fight.method,
            "finish_round": fight.finish_round,
            "finish_time_sec": fight.finish_time_sec,
            "scheduled_rounds": fight.scheduled_rounds,
        }
        elapsed = infer_round_exposure(
            payload,
            fight.event_date.isoformat(),
            round_no,
            self._elapsed_registry,
        )
        self._round_elapsed_cache[key] = elapsed
        return elapsed

    def _single_fight_stats(self, fighter_id: str, feature_name: str, fight: FightRef) -> dict[str, FightStats]:
        rows = self.store.round_rows_for_fight(fighter_id, fight.fight_id)
        if feature_name in {
            "sig_strike_flow",
            "knockdown_rate",
            "takedown_pressure",
            "control_rate",
            "submission_attempt_rate",
            "reversal_rate",
        }:
            numerators: dict[str, float] = {}
            denominators: dict[str, float] = {}
            observations: dict[str, int] = {}

            def add(component: str, numerator: float, denominator_minutes: float) -> None:
                if denominator_minutes <= 0:
                    return
                numerators[component] = numerators.get(component, 0.0) + numerator
                denominators[component] = denominators.get(component, 0.0) + denominator_minutes
                observations[component] = observations.get(component, 0) + 1

            for row in rows:
                round_no = int(row["round"])
                elapsed_sec = self._round_elapsed_sec(fight, round_no)
                if elapsed_sec is None or elapsed_sec <= 0:
                    continue
                elapsed_min = elapsed_sec / 60.0
                opponent = self.store.opponent_round_row(fight.fight_id, fighter_id, round_no)

                if feature_name == "sig_strike_flow":
                    attempted = as_int(row.get("sig_strikes_attempted"))
                    landed = as_int(row.get("sig_strikes_landed"))
                    if attempted is not None:
                        add("attempted_per_min", float(attempted), elapsed_min)
                    if landed is not None:
                        add("landed_per_min", float(landed), elapsed_min)
                    if opponent is not None:
                        absorbed = as_int(opponent.get("sig_strikes_landed"))
                        if absorbed is not None:
                            add("absorbed_per_min", float(absorbed), elapsed_min)
                elif feature_name == "knockdown_rate":
                    created = as_int(row.get("knockdowns"))
                    if created is not None:
                        add("created_per_15", 15.0 * created, elapsed_min)
                    if opponent is not None:
                        allowed = as_int(opponent.get("knockdowns"))
                        if allowed is not None:
                            add("allowed_per_15", 15.0 * allowed, elapsed_min)
                elif feature_name == "takedown_pressure":
                    created = as_int(row.get("takedowns_attempted"))
                    if created is not None:
                        add("created_per_15", 15.0 * created, elapsed_min)
                    if opponent is not None:
                        faced = as_int(opponent.get("takedowns_attempted"))
                        if faced is not None:
                            add("faced_per_15", 15.0 * faced, elapsed_min)
                elif feature_name == "control_rate":
                    created = as_int(row.get("control_sec"))
                    if created is not None:
                        control_share(created, elapsed_sec)  # bound validation; generic control only
                        add("created_share", created / 60.0, elapsed_min)
                    if opponent is not None:
                        allowed = as_int(opponent.get("control_sec"))
                        if allowed is not None:
                            control_share(allowed, elapsed_sec)
                            add("allowed_share", allowed / 60.0, elapsed_min)
                elif feature_name == "submission_attempt_rate":
                    created = as_int(row.get("submission_attempts"))
                    if created is not None:
                        add("created_per_15", 15.0 * created, elapsed_min)
                    if opponent is not None:
                        faced = as_int(opponent.get("submission_attempts"))
                        if faced is not None:
                            add("faced_per_15", 15.0 * faced, elapsed_min)
                else:
                    created = as_int(row.get("reversals"))
                    if created is not None:
                        add("created_per_15", 15.0 * created, elapsed_min)
                    if opponent is not None:
                        faced = as_int(opponent.get("reversals"))
                        if faced is not None:
                            add("faced_per_15", 15.0 * faced, elapsed_min)

            return {
                component: FightStats(
                    fight.fight_id,
                    {component: numerators[component]},
                    {component: denominators[component]},
                    observations[component],
                )
                for component in sorted(numerators)
            }

        if feature_name in {
            "sig_strike_efficiency",
            "sig_target_mix",
            "sig_environment_mix",
            "knockdown_efficiency",
            "takedown_conversion",
        }:
            numerators: dict[str, float] = {}
            denominators: dict[str, float] = {}
            observations: dict[str, int] = {}

            def add(component: str, numerator: float, denominator: float) -> None:
                numerators[component] = numerators.get(component, 0.0) + numerator
                denominators[component] = denominators.get(component, 0.0) + denominator
                observations[component] = observations.get(component, 0) + 1

            for row in rows:
                round_no = int(row["round"])
                opponent = self.store.opponent_round_row(fight.fight_id, fighter_id, round_no)
                if feature_name == "sig_strike_efficiency":
                    landed = as_int(row.get("sig_strikes_landed"))
                    attempted = as_int(row.get("sig_strikes_attempted"))
                    if landed is not None and attempted is not None:
                        add("accuracy", landed, attempted)
                    if opponent is not None:
                        opp_landed = as_int(opponent.get("sig_strikes_landed"))
                        opp_attempted = as_int(opponent.get("sig_strikes_attempted"))
                        if opp_landed is not None and opp_attempted is not None:
                            add("defense", opp_attempted - opp_landed, opp_attempted)
                elif feature_name == "sig_target_mix":
                    fields = ("sig_head_attempted", "sig_body_attempted", "sig_leg_attempted")
                    values = [as_int(row.get(field)) for field in fields]
                    if all(value is not None for value in values):
                        denominator = float(sum(value for value in values if value is not None))
                        for component, value in zip(("head_share", "body_share", "leg_share"), values):
                            add(component, float(value), denominator)
                elif feature_name == "sig_environment_mix":
                    fields = ("sig_distance_attempted", "sig_clinch_attempted", "sig_ground_attempted")
                    values = [as_int(row.get(field)) for field in fields]
                    if all(value is not None for value in values):
                        denominator = float(sum(value for value in values if value is not None))
                        for component, value in zip(("distance_share", "clinch_share", "ground_share"), values):
                            add(component, float(value), denominator)
                elif feature_name == "knockdown_efficiency":
                    knockdowns = as_int(row.get("knockdowns"))
                    landed = as_int(row.get("sig_strikes_landed"))
                    if knockdowns is not None and landed is not None:
                        add("creation", knockdowns, landed)
                    if opponent is not None:
                        opp_kd = as_int(opponent.get("knockdowns"))
                        opp_landed = as_int(opponent.get("sig_strikes_landed"))
                        if opp_kd is not None and opp_landed is not None:
                            add("vulnerability", opp_kd, opp_landed)
                else:
                    landed = as_int(row.get("takedowns_landed"))
                    attempted = as_int(row.get("takedowns_attempted"))
                    if landed is not None and attempted is not None:
                        add("success", landed, attempted)
                    if opponent is not None:
                        opp_landed = as_int(opponent.get("takedowns_landed"))
                        opp_attempted = as_int(opponent.get("takedowns_attempted"))
                        if opp_landed is not None and opp_attempted is not None:
                            add("defense", opp_attempted - opp_landed, opp_attempted)

            return {
                component: FightStats(
                    fight.fight_id,
                    {component: numerators[component]},
                    {component: denominators[component]},
                    observations[component],
                )
                for component in sorted(numerators)
            }

        if feature_name in {"finish_method_win_profile", "finish_method_loss_profile"}:
            if fight.result is None or fight.method is None:
                return {}
            is_win = fight.winner_id == fighter_id
            is_loss = fight.winner_id is not None and fight.winner_id != fighter_id
            output: dict[str, FightStats] = {}
            for component, method in (("ko_tko", "KO_TKO"), ("submission", "SUBMISSION"), ("decision", "DECISION")):
                qualifying = is_win if feature_name == "finish_method_win_profile" else is_loss
                numerator = 1.0 if qualifying and fight.method == method else 0.0
                output[component] = FightStats(fight.fight_id, {component: numerator}, {component: 1.0}, 1)
            return output

        if feature_name == "early_finish_profile":
            if fight.result is None or fight.method is None or fight.finish_round is None:
                return {}
            early = fight.finish_round == 1 and fight.method != "DECISION"
            is_win = fight.winner_id == fighter_id
            is_loss = fight.winner_id is not None and fight.winner_id != fighter_id
            return {
                "r1_finish_win": FightStats(
                    fight.fight_id,
                    {"r1_finish_win": 1.0 if early and is_win else 0.0},
                    {"r1_finish_win": 1.0},
                    1,
                ),
                "r1_finish_loss": FightStats(
                    fight.fight_id,
                    {"r1_finish_loss": 1.0 if early and is_loss else 0.0},
                    {"r1_finish_loss": 1.0},
                    1,
                ),
            }

        raise MaterializationError(f"no sufficient-stat implementation for {feature_name}")

    def _component_history_stats(
        self,
        fighter_id: str,
        feature_name: str,
        prior_fights: Iterable[FightRef],
    ) -> dict[str, list[FightStats]]:
        output: dict[str, list[FightStats]] = {}
        for fight in prior_fights:
            for component, stats in self._single_fight_stats(fighter_id, feature_name, fight).items():
                output.setdefault(component, []).append(stats)
        return output

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
        target_weight_class = self._target_weight_class(self.store, target_fight_id)
        output: dict[str, AuditValue] = {}

        for (component, window), column in columns.items():
            if component is None or window is None:
                raise MaterializationError(f"rate concept {feature_name} lacks component/window metadata")
            stats = by_component.get(component, [])
            eligible_fights = [self.store.require_fight(item.fight_id) for item in stats]
            try:
                selection = self.store.select_window(eligible_fights, window, prediction_as_of)
            except AmbiguousWindowBoundary as exc:
                output[column] = AuditValue(
                    column,
                    feature_name,
                    component,
                    window,
                    None,
                    "missing_observation",
                    None,
                    None,
                    None,
                    0,
                    0,
                    feature["shrinkage_rule"],
                    None,
                    None,
                    (),
                    str(exc),
                )
                continue

            aggregate = aggregate_fight_stats(stats, selection.weights)
            numerator = aggregate.numerators.get(component, 0.0)
            denominator = aggregate.denominators.get(component, 0.0)

            # F00 permits a population prior for a *known* true debutant, but
            # canonical v0 exposes no completeness/debut flag. Zero prior
            # canonical fights therefore does not prove a true debut; F01
            # withholds prior substitution in that case rather than silently
            # converting coverage uncertainty into debutant semantics.
            if prior_fight_count == 0:
                prior_num = prior_den = None
                prior_source = "withheld:zero_canonical_history_debut_unproven"
            else:
                prior_num, prior_den, prior_source = self._population_prior(
                    feature_name,
                    component,
                    prediction_as_of,
                    target_weight_class,
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
            reason = None
            if prior_fight_count == 0:
                reason = "zero prior canonical fights; true debut status is not proven by canonical v0"
            output[column] = AuditValue(
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
                reason=reason,
            )
        return output

    @staticmethod
    def _simple_value(
        feature: dict[str, Any],
        column: str,
        value: Any,
        *,
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
        )
        return AuditValue(
            column,
            feature["feature_name"],
            component,
            None,
            value,
            state,
            None,
            None,
            None,
            len(set(fight_ids)),
            observation_count,
            feature["shrinkage_rule"],
            None,
            None,
            tuple(sorted(set(fight_ids))),
            reason,
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
                    column,
                    name,
                    None,
                    "career",
                    prior_count,
                    "observed_zero" if prior_count == 0 else "observed_positive",
                    float(prior_count),
                    float(prior_count),
                    float(prior_count),
                    prior_count,
                    prior_count,
                    "none",
                    None,
                    None,
                    tuple(sorted(fight.fight_id for fight in prior_fights)),
                )
            elif name in {
                "sig_strike_efficiency",
                "sig_target_mix",
                "sig_environment_mix",
                "knockdown_efficiency",
                "takedown_conversion",
                "finish_method_win_profile",
                "finish_method_loss_profile",
                "early_finish_profile",
                "sig_strike_flow",
                "knockdown_rate",
                "takedown_pressure",
                "control_rate",
                "submission_attempt_rate",
                "reversal_rate",
            }:
                values.update(
                    self._materialize_rate_feature(fighter_id, cutoff, target_fight_id, feature, prior_count)
                )
            elif name == "layoff_days":
                column = columns[(None, None)]
                if not prior_fights:
                    values[column] = self._simple_value(
                        feature,
                        column,
                        None,
                        prior_fight_count=prior_count,
                        reason="no eligible prior fight",
                        force_state="not_applicable",
                    )
                else:
                    latest_date = max(fight.event_date for fight in prior_fights)
                    lineage = tuple(sorted(fight.fight_id for fight in prior_fights if fight.event_date == latest_date))
                    target_date = (
                        self.store.require_fight(target_fight_id).event_date
                        if target_fight_id
                        else parse_cutoff(cutoff).date()
                    )
                    values[column] = self._simple_value(
                        feature,
                        column,
                        (target_date - latest_date).days,
                        prior_fight_count=prior_count,
                        fight_ids=lineage,
                        observation_count=len(lineage),
                    )
            elif name == "prior_scale_weight_lbs":
                column = columns[(None, None)]
                row = self.store.prior_scale_weight(fighter_id, cutoff)
                if row is None:
                    values[column] = self._simple_value(
                        feature,
                        column,
                        None,
                        prior_fight_count=prior_count,
                        reason="no explicit prior canonical scale weight",
                        force_state="missing_observation",
                    )
                else:
                    weight = as_float(row.get("scale_weight_lbs"))
                    values[column] = self._simple_value(
                        feature,
                        column,
                        weight,
                        prior_fight_count=prior_count,
                        fight_ids=(row["fight_id"],),
                        observation_count=1,
                    )
            elif name == "age_at_fight":
                column = columns[(None, None)]
                if target_fight_id is None:
                    values[column] = self._simple_value(
                        feature,
                        column,
                        None,
                        prior_fight_count=prior_count,
                        reason="target_fight_id required for age_at_fight",
                        force_state="not_applicable",
                    )
                else:
                    dob = self.store.require_fighter(fighter_id).get("dob")
                    if not dob:
                        values[column] = self._simple_value(
                            feature,
                            column,
                            None,
                            prior_fight_count=prior_count,
                            reason="canonical DOB missing",
                            force_state="missing_observation",
                        )
                    else:
                        target_date = self.store.require_fight(target_fight_id).event_date
                        age_years = (target_date - parse_date(dob)).days / 365.2425
                        values[column] = self._simple_value(
                            feature,
                            column,
                            age_years,
                            prior_fight_count=prior_count,
                            observation_count=1,
                        )
            elif name == "physical_size_profile":
                fighter = self.store.require_fighter(fighter_id)
                for component in ("height_cm", "reach_cm"):
                    column = columns[(component, None)]
                    value = as_float(fighter.get(component))
                    values[column] = self._simple_value(
                        feature,
                        column,
                        value,
                        prior_fight_count=prior_count,
                        component=component,
                        observation_count=1 if value is not None else 0,
                        reason=None if value is not None else f"canonical {component} missing",
                        force_state=None if value is not None else "missing_observation",
                    )
            elif name in {"scheduled_rounds", "title_bout", "weight_class"}:
                column = columns[(None, None)]
                if target_fight_id is None:
                    values[column] = self._simple_value(
                        feature,
                        column,
                        None,
                        prior_fight_count=prior_count,
                        reason="target_fight_id required for target context",
                        force_state="not_applicable",
                    )
                else:
                    target = self.store.require_fight(target_fight_id)
                    if not target.includes(fighter_id):
                        raise MaterializationError(
                            f"fighter {fighter_id} is not a participant in target fight {target_fight_id}"
                        )
                    value = {
                        "scheduled_rounds": target.scheduled_rounds,
                        "title_bout": target.title_bout,
                        "weight_class": target.weight_class,
                    }[name]
                    values[column] = self._simple_value(
                        feature,
                        column,
                        value,
                        prior_fight_count=prior_count,
                        observation_count=1 if value is not None else 0,
                        reason=None if value is not None else f"target {name} missing",
                        force_state=None if value is not None else "missing_observation",
                    )
            else:
                raise MaterializationError(f"selected non-matchup concept has no materializer: {name}")

        expected = {
            column
            for feature in selected
            if feature["feature_name"] not in MATCHUP_IMPLEMENTATIONS
            for column in concept_columns(self.catalog, feature).values()
        }
        if set(values) != expected:
            raise MaterializationError(
                f"fighter-state column mismatch missing={sorted(expected - set(values))} "
                f"extra={sorted(set(values) - expected)}"
            )
        return FighterState(fighter_id, cutoff, target_fight_id, values)

    @staticmethod
    def orient(fighter_a_id: str, fighter_b_id: str) -> tuple[str, str]:
        if fighter_a_id == fighter_b_id:
            raise MaterializationError("matchup requires two distinct canonical fighter IDs")
        ordered = sorted((fighter_a_id, fighter_b_id))
        return ordered[0], ordered[1]

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
        fighter_1 = self.materialize_fighter(
            fighter_1_id,
            prediction_as_of,
            target_fight_id=target_fight_id,
            consumer=consumer,
        )
        fighter_2 = self.materialize_fighter(
            fighter_2_id,
            prediction_as_of,
            target_fight_id=target_fight_id,
            consumer=consumer,
        )
        selected = active_v1_features(self.catalog, consumer)
        interactions: dict[str, AuditValue] = {}

        for feature in selected:
            name = feature["feature_name"]
            if name not in MATCHUP_IMPLEMENTATIONS:
                continue
            columns = concept_columns(self.catalog, feature)

            if name == "reach_difference_cm":
                dependency = concept_columns(self.catalog, self._by_name["physical_size_profile"])[("reach_cm", None)]
                left = fighter_1.values.get(dependency)
                right = fighter_2.values.get(dependency)
                if left is None or right is None:
                    raise MaterializationError("reach interaction dependency was not selected for consumer")
                if left.value is None or right.value is None:
                    value, state, reason = None, "missing_observation", "reach dependency missing"
                else:
                    value = float(left.value) - float(right.value)
                    state = "observed_zero" if value == 0 else "observed_positive"
                    reason = None
                column = columns[(None, None)]
                interactions[column] = AuditValue(
                    column, name, None, None, value, state, None, None, None, 0, 0, "none", None, None, (), reason
                )
                continue

            dependency_columns = concept_columns(self.catalog, self._by_name["knockdown_efficiency"])
            for window in ("career", "last5"):
                f1_creation = fighter_1.values.get(dependency_columns[("creation", window)])
                f1_vulnerability = fighter_1.values.get(dependency_columns[("vulnerability", window)])
                f2_creation = fighter_2.values.get(dependency_columns[("creation", window)])
                f2_vulnerability = fighter_2.values.get(dependency_columns[("vulnerability", window)])
                dependencies = (f1_creation, f1_vulnerability, f2_creation, f2_vulnerability)
                if any(item is None for item in dependencies):
                    raise MaterializationError("KD interaction dependency was not selected for consumer")
                pairs = {
                    "f1_vs_f2": (f1_creation, f2_vulnerability),
                    "f2_vs_f1": (f2_creation, f1_vulnerability),
                }
                for component, pair in pairs.items():
                    attack, vulnerability = pair
                    if attack is None or vulnerability is None:
                        raise MaterializationError("KD interaction dependency unexpectedly missing")
                    if attack.value is None or vulnerability.value is None:
                        value, state, reason = None, "missing_observation", "knockdown-efficiency dependency missing"
                    else:
                        value = float(attack.value) - float(vulnerability.value)
                        state = "observed_zero" if value == 0 else "observed_positive"
                        reason = None
                    column = columns[(component, window)]
                    interactions[column] = AuditValue(
                        column,
                        name,
                        component,
                        window,
                        value,
                        state,
                        None,
                        None,
                        None,
                        0,
                        0,
                        "none",
                        None,
                        None,
                        (),
                        reason,
                    )

        expected = {
            column
            for feature in selected
            if feature["feature_name"] in MATCHUP_IMPLEMENTATIONS
            for column in concept_columns(self.catalog, feature).values()
        }
        if set(interactions) != expected:
            raise MaterializationError(
                f"matchup column mismatch missing={sorted(expected - set(interactions))} "
                f"extra={sorted(set(interactions) - expected)}"
            )
        return MatchupState(
            fighter_1_id,
            fighter_2_id,
            fighter_1.prediction_as_of,
            target_fight_id,
            fighter_1,
            fighter_2,
            interactions,
        )
