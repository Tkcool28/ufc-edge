"""F02 deterministic historical predictor replay over the governed F01 surface.

F02 is an orchestration layer only.  It does not redefine feature semantics:
all fighter state, matchup interactions, cutoff behavior, missingness, shrinkage,
and elapsed-exposure interpretation remain owned by F01.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable, Iterator, Sequence

from .history import FightRef, parse_cutoff
from .materializer import V1Materializer, deterministic_hash
from .state import MATCHUP_IMPLEMENTATIONS, MatchupState, StateBuilder, active_v1_features


REPLAY_SCHEMA_VERSION = "1.0.0"
TARGET_CONTRACT_VERSION = "1.0.0"
REPLAY_STATUS = "F02_PREDICTOR_REPLAY_V1_COMPLETE"
CUTOFF_POLICY = "target_event_date_start_utc; F01 date-only history requires event_date < cutoff_date"
TARGET_ORDERING = "event_date,event_id,fight_id"
CHUNK_POLICY = "five_year_event_date_ranges"
PREDICTOR_CONSUMER = None
MISSINGNESS_STATES = (
    "observed_positive",
    "observed_zero",
    "missing_observation",
    "not_applicable",
    "insufficient_exposure",
)

SHARED_FIGHT_CONTEXT_CONCEPTS = (
    "scheduled_rounds",
    "title_bout",
    "weight_class",
)

IDENTITY_SCHEMA: tuple[tuple[str, str, bool], ...] = (
    ("fight_id", "string", False),
    ("event_id", "string", False),
    ("event_date", "string", False),
    ("prediction_as_of", "string", False),
    ("promotion", "string", True),
    ("scheduled_rounds", "int64", True),
    ("fighter_1_id", "string", False),
    ("fighter_2_id", "string", False),
)
TARGET_SCHEMA: tuple[tuple[str, str, bool], ...] = (
    ("target_state", "string", False),
    ("binary_winner_eligible", "bool", False),
    ("fighter_1_win", "bool", True),
    ("winner_id", "string", True),
)
INTEGER_CONCEPTS = {"prior_fight_count", "layoff_days", "scheduled_rounds"}
BOOLEAN_CONCEPTS = {"title_bout"}
STRING_CONCEPTS = {"weight_class"}


class ReplayError(ValueError):
    """Raised when F02 cannot preserve its deterministic replay contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def git_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def row_hash(rows: Iterable[dict[str, Any]], columns: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        payload = [row.get(column) for column in columns]
        digest.update(canonical_json(payload).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def target_ids_hash(targets: Iterable[FightRef]) -> str:
    digest = hashlib.sha256()
    for target in targets:
        digest.update(target.fight_id.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def prediction_as_of(target: FightRef) -> str:
    # F01 interprets history by date, not intra-day time.  Midnight makes the
    # policy explicit while preserving its strict event_date < cutoff_date rule.
    return f"{target.event_date.isoformat()}T00:00:00Z"


def target_sort_key(target: FightRef) -> tuple[date, str, str]:
    return target.event_date, target.event_id, target.fight_id


def five_year_chunk(target: FightRef) -> str:
    start = target.event_date.year - (target.event_date.year % 5)
    return f"{start:04d}-{start + 4:04d}"


def _concept_from_materialized(name: str) -> str:
    parts = name.split("__")
    if len(parts) < 2:
        raise ReplayError(f"unrecognized F01 materialized name: {name}")
    return parts[1]


def predictor_type(source_materialized_name: str) -> str:
    concept = _concept_from_materialized(source_materialized_name)
    if concept in INTEGER_CONCEPTS:
        return "int64"
    if concept in BOOLEAN_CONCEPTS:
        return "bool"
    if concept in STRING_CONCEPTS:
        return "string"
    return "float64"


def _row_name(role: str, source_name: str) -> str:
    if role == "f1":
        return f"f1__{source_name}"
    if role == "f2":
        return f"f2__{source_name}"
    if role == "ctx":
        concept = _concept_from_materialized(source_name)
        if concept == "scheduled_rounds":
            return "scheduled_rounds"
        return f"ctx__{concept}"
    if role == "mx":
        # F01 matchup names are already mx__*.  Strip and re-add exactly once
        # so the F02 namespace is explicit without duplicate prefixes.
        return source_name if source_name.startswith("mx__") else f"mx__{source_name}"
    raise ReplayError(f"unknown predictor role {role}")


@dataclass(frozen=True)
class ReplaySchema:
    replay_schema_version: str
    columns: tuple[dict[str, Any], ...]
    schema_sha256: str
    f01_materialized_value_count: int
    fighter_specific_value_count: int
    shared_fight_context_value_count: int
    matchup_interaction_value_count: int
    row_predictor_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TargetContract:
    target_contract_version: str
    fields: tuple[dict[str, Any], ...]
    states: dict[str, Any]
    contract_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayRow:
    row: dict[str, Any]
    audit: dict[str, dict[str, Any]]


class ExactPopulationPriorIndex:
    """Exact F01 population-prior accelerator for a fixed replay date set.

    For every component, updates are applied in the same canonical fight order
    and fighter_a/fighter_b order as StateBuilder._population_prior. NumPy only
    broadcasts each individual scalar addition across future cutoff cells; it
    never reorders additions *within* a cutoff cell. Equivalence against the
    untouched F01 reference path is a required gate before full replay.
    """

    def __init__(self, builder: StateBuilder, target_dates: Sequence[date]):
        try:
            import numpy as np  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised by CLI guard
            raise ReplayError("optimized replay requires numpy") from exc
        self.np = np
        self.builder = builder
        self.store = builder.store
        self.catalog = builder.catalog
        self.target_dates = tuple(sorted(set(target_dates)))
        self.date_index = {item: idx for idx, item in enumerate(self.target_dates)}
        self._built_features: dict[str, dict[str | None, dict[str, tuple[Any, Any]]]] = {}
        self._weight_class_counts = self._build_weight_class_counts()

    def _first_eligible_target_index(self, fight_date: date) -> int:
        return bisect_right(self.target_dates, fight_date)

    def _build_weight_class_counts(self) -> dict[str, Any]:
        np = self.np
        counts: dict[str, Any] = {}
        n = len(self.target_dates)
        for fight in self.store.fights.values():
            if fight.weight_class is None:
                continue
            idx = self._first_eligible_target_index(fight.event_date)
            if idx >= n:
                continue
            arr = counts.setdefault(fight.weight_class, np.zeros(n, dtype=np.int64))
            arr[idx:] += 1
        return counts

    def _build_feature(self, feature_name: str) -> None:
        if feature_name in self._built_features:
            return
        np = self.np
        feature = next(
            item for item in active_v1_features(self.catalog)
            if item["feature_name"] == feature_name
        )
        components = tuple(feature.get("components") or ())
        if not components or feature["shrinkage_rule"] == "none":
            raise ReplayError(f"population prior requested for non-shrunk feature {feature_name}")
        n = len(self.target_dates)

        # scope -> component -> (numerator vector, denominator vector)
        scopes: dict[str | None, dict[str, tuple[Any, Any]]] = {
            None: {
                component: (np.zeros(n, dtype=np.float64), np.zeros(n, dtype=np.float64))
                for component in components
            }
        }

        for fight in self.store.fights.values():
            idx = self._first_eligible_target_index(fight.event_date)
            if idx >= n:
                continue
            if fight.weight_class is not None and fight.weight_class not in scopes:
                scopes[fight.weight_class] = {
                    component: (np.zeros(n, dtype=np.float64), np.zeros(n, dtype=np.float64))
                    for component in components
                }
            for fighter_id in (fight.fighter_a_id, fight.fighter_b_id):
                stats_by_component = self.builder._single_fight_stats(  # noqa: SLF001 - exact F01 primitive
                    fighter_id, feature_name, fight
                )
                for component, stats in stats_by_component.items():
                    if component not in components:
                        continue
                    numerator = float(stats.numerators[component])
                    denominator = float(stats.denominators[component])
                    global_num, global_den = scopes[None][component]
                    global_num[idx:] += numerator
                    global_den[idx:] += denominator
                    if fight.weight_class is not None:
                        scope_num, scope_den = scopes[fight.weight_class][component]
                        scope_num[idx:] += numerator
                        scope_den[idx:] += denominator

        self._built_features[feature_name] = scopes

    def get(
        self,
        feature_name: str,
        component: str,
        prediction_cutoff: str,
        target_weight_class: str | None,
    ) -> tuple[float | None, float | None, str | None] | None:
        cutoff_date = parse_cutoff(prediction_cutoff).date()
        index = self.date_index.get(cutoff_date)
        if index is None:
            return None
        self._build_feature(feature_name)
        scopes = self._built_features[feature_name]
        scope: str | None = None
        if target_weight_class is not None:
            counts = self._weight_class_counts.get(target_weight_class)
            if counts is not None and int(counts[index]) >= 100:
                scope = target_weight_class
        component_vectors = scopes.get(scope)
        if component_vectors is None:
            # A weight class with 100 prior fights must necessarily have a scope
            # vector; fail closed rather than silently downgrade hierarchy.
            raise ReplayError(f"missing optimized prior scope {scope!r}")
        numerator_vec, denominator_vec = component_vectors[component]
        numerator = float(numerator_vec[index])
        denominator = float(denominator_vec[index])
        source = f"weight_class:{scope}" if scope is not None else "global"
        if denominator <= 0:
            return None, None, source
        return numerator, denominator, source


class ExactReplayStateBuilder(StateBuilder):
    """F01 StateBuilder with an exact-equivalence population-prior index."""

    def __init__(self, store: Any, catalog: dict[str, Any], target_dates: Sequence[date]):
        super().__init__(store, catalog)
        self._f02_single_stats_cache: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._f02_prior_index = ExactPopulationPriorIndex(self, target_dates)

    def _single_fight_stats(self, fighter_id: str, feature_name: str, fight: FightRef) -> dict[str, Any]:
        key = (fighter_id, feature_name, fight.fight_id)
        cached = self._f02_single_stats_cache.get(key)
        if cached is None:
            cached = super()._single_fight_stats(fighter_id, feature_name, fight)
            self._f02_single_stats_cache[key] = cached
        return cached

    def _population_prior(
        self,
        feature_name: str,
        component: str,
        prediction_as_of: str,
        target_weight_class: str | None,
    ) -> tuple[float | None, float | None, str | None]:
        optimized = self._f02_prior_index.get(
            feature_name, component, prediction_as_of, target_weight_class
        )
        if optimized is None:
            return super()._population_prior(
                feature_name, component, prediction_as_of, target_weight_class
            )
        return optimized


class ReplayMaterializer(V1Materializer):
    def __init__(
        self,
        root: Path | None = None,
        *,
        target_dates: Sequence[date] = (),
        optimized: bool = False,
    ):
        super().__init__(root)
        self.optimized = optimized
        if optimized:
            self.builder = ExactReplayStateBuilder(self.store, self.catalog, target_dates)


class CoverageDiagnostics:
    def __init__(self, elapsed_feature_names: set[str]):
        self.by_year: Counter[str] = Counter()
        self.by_promotion: Counter[str] = Counter()
        self.history_depth_fighter_sides: Counter[str] = Counter()
        self.slices: Counter[str] = Counter()
        self.scheduled_rounds: Counter[str] = Counter()
        self.feature_states: dict[str, Counter[str]] = defaultdict(Counter)
        self.elapsed_states: Counter[str] = Counter()
        self.elapsed_feature_names = elapsed_feature_names

    @staticmethod
    def _history_bucket(value: int) -> str:
        if value == 0:
            return "zero_prior_canonical_history"
        if value <= 2:
            return "one_to_two_prior_fights"
        if value <= 9:
            return "three_to_nine_prior_fights"
        return "ten_plus_prior_fights"

    def add(
        self,
        target: FightRef,
        replay_row: ReplayRow,
        prior_counts: tuple[int, int],
        external_history: bool,
    ) -> None:
        self.by_year[str(target.event_date.year)] += 1
        self.by_promotion[target.promotion or "<missing>"] += 1
        for count in prior_counts:
            self.history_depth_fighter_sides[self._history_bucket(count)] += 1
        if 0 in prior_counts:
            self.slices["zero_prior_history_target"] += 1
        if any(1 <= value <= 2 for value in prior_counts):
            self.slices["sparse_history_target"] += 1
        if any(value >= 10 for value in prior_counts):
            self.slices["long_history_target"] += 1
        if external_history:
            self.slices["external_history_target"] += 1
        if (target.promotion or "").casefold() == "ufc":
            if target.event_date < date(2000, 11, 17):
                self.slices["ufc_pre_unified_rules_reference_era"] += 1
            else:
                self.slices["ufc_unified_rules_reference_era"] += 1
        self.scheduled_rounds[str(target.scheduled_rounds) if target.scheduled_rounds is not None else "<missing>"] += 1
        for column, meta in replay_row.audit.items():
            state = str(meta["missingness_state"])
            self.feature_states[column][state] += 1
            if meta["source_concept"] in self.elapsed_feature_names:
                self.elapsed_states[state] += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "by_year": dict(sorted(self.by_year.items())),
            "by_promotion": dict(sorted(self.by_promotion.items())),
            "fighter_history_depth": dict(sorted(self.history_depth_fighter_sides.items())),
            "slices": dict(sorted(self.slices.items())),
            "scheduled_rounds": dict(sorted(self.scheduled_rounds.items())),
            "feature_missingness_states": {
                name: {state: counter.get(state, 0) for state in MISSINGNESS_STATES}
                for name, counter in sorted(self.feature_states.items())
            },
            "elapsed_exposure_feature_states": {
                state: self.elapsed_states.get(state, 0) for state in MISSINGNESS_STATES
            },
            "unavailable_requested_slices": {
                "sex_or_gender": "Frozen canonical fighters.csv has no governed sex/gender field; F02 does not infer it."
            },
        }


class ReplayEngine:
    def __init__(
        self,
        root: Path | None = None,
        *,
        optimized: bool = False,
        target_dates: Sequence[date] = (),
    ):
        self.root = (root or Path(__file__).resolve().parents[3]).resolve()
        self.materializer = ReplayMaterializer(
            self.root, target_dates=target_dates, optimized=optimized
        )
        self.store = self.materializer.store
        self.optimized = optimized
        self._schema = self._build_schema()
        self._target_contract = self._build_target_contract()
        self.elapsed_feature_names = {
            feature["feature_name"]
            for feature in active_v1_features(self.materializer.catalog)
            if (feature.get("elapsed_exposure_source") or {}).get("source") == "ruleset_registry_v1"
        }

    def targets(
        self,
        *,
        start_year: int | None = None,
        end_year: int | None = None,
        limit: int | None = None,
    ) -> list[FightRef]:
        targets = sorted(self.store.fights.values(), key=target_sort_key)
        if start_year is not None:
            targets = [item for item in targets if item.event_date.year >= start_year]
        if end_year is not None:
            targets = [item for item in targets if item.event_date.year <= end_year]
        if limit is not None:
            targets = targets[:limit]
        self.validate_target_universe(targets)
        return targets

    def validate_target_universe(self, targets: Sequence[FightRef]) -> None:
        ids = [item.fight_id for item in targets]
        if len(ids) != len(set(ids)):
            raise ReplayError("duplicate canonical target fight IDs")
        if list(targets) != sorted(targets, key=target_sort_key):
            raise ReplayError("target universe is not in deterministic event_date,event_id,fight_id order")
        for target in targets:
            if target.fighter_a_id == target.fighter_b_id:
                raise ReplayError(f"self-match target {target.fight_id}")
            self.store.require_fighter(target.fighter_a_id)
            self.store.require_fighter(target.fighter_b_id)

    def _build_schema(self) -> ReplaySchema:
        selected = active_v1_features(self.materializer.catalog)
        matchup_concepts = {
            item["feature_name"]
            for item in selected
            if item["feature_name"] in MATCHUP_IMPLEMENTATIONS
        }
        source_names = self.materializer.names()
        matchup_names = [
            name for name in source_names
            if _concept_from_materialized(name) in matchup_concepts
        ]
        non_matchup_names = [name for name in source_names if name not in matchup_names]
        shared_names = [
            name for name in non_matchup_names
            if _concept_from_materialized(name) in SHARED_FIGHT_CONTEXT_CONCEPTS
        ]
        fighter_names = [name for name in non_matchup_names if name not in shared_names]
        shared_concepts = tuple(sorted(_concept_from_materialized(name) for name in shared_names))
        if shared_concepts != tuple(sorted(SHARED_FIGHT_CONTEXT_CONCEPTS)):
            raise ReplayError(
                "unexpected shared fight-context surface "
                f"expected={sorted(SHARED_FIGHT_CONTEXT_CONCEPTS)} actual={list(shared_concepts)}"
            )
        if len(fighter_names) != 96 or len(shared_names) != 3 or len(matchup_names) != 5:
            raise ReplayError(
                "unexpected F01 surface "
                f"fighter_specific={len(fighter_names)} shared_context={len(shared_names)} "
                f"matchup={len(matchup_names)}"
            )

        columns: list[dict[str, Any]] = []
        for name, kind, nullable in IDENTITY_SCHEMA:
            if name == "scheduled_rounds":
                source_name = next(
                    item for item in shared_names
                    if _concept_from_materialized(item) == "scheduled_rounds"
                )
                columns.append({
                    "name": name,
                    "type": kind,
                    "nullable": nullable,
                    "role": "fight_context",
                    "predictor": True,
                    "source_materialized_name": source_name,
                    "source_concept": "scheduled_rounds",
                    "metadata_role": "replay_context",
                })
            else:
                columns.append({
                    "name": name,
                    "type": kind,
                    "nullable": nullable,
                    "role": "identity",
                    "predictor": False,
                })

        for role in ("f1", "f2"):
            for source_name in fighter_names:
                columns.append({
                    "name": _row_name(role, source_name),
                    "type": predictor_type(source_name),
                    "nullable": True,
                    "role": role,
                    "predictor": True,
                    "source_materialized_name": source_name,
                    "source_concept": _concept_from_materialized(source_name),
                })

        for source_name in shared_names:
            if _concept_from_materialized(source_name) == "scheduled_rounds":
                continue
            columns.append({
                "name": _row_name("ctx", source_name),
                "type": predictor_type(source_name),
                "nullable": True,
                "role": "fight_context",
                "predictor": True,
                "source_materialized_name": source_name,
                "source_concept": _concept_from_materialized(source_name),
            })

        for source_name in matchup_names:
            columns.append({
                "name": _row_name("mx", source_name),
                "type": predictor_type(source_name),
                "nullable": True,
                "role": "mx",
                "predictor": True,
                "source_materialized_name": source_name,
                "source_concept": _concept_from_materialized(source_name),
            })

        names = [item["name"] for item in columns]
        if len(names) != len(set(names)):
            raise ReplayError("duplicate F02 replay schema column")
        predictor_columns = [item for item in columns if item["predictor"]]
        if len(predictor_columns) != 200:
            raise ReplayError(f"unexpected F02 predictor count {len(predictor_columns)} != 200")
        payload = {
            "replay_schema_version": REPLAY_SCHEMA_VERSION,
            "columns": columns,
        }
        return ReplaySchema(
            replay_schema_version=REPLAY_SCHEMA_VERSION,
            columns=tuple(columns),
            schema_sha256=deterministic_hash(payload),
            f01_materialized_value_count=len(source_names),
            fighter_specific_value_count=len(fighter_names),
            shared_fight_context_value_count=len(shared_names),
            matchup_interaction_value_count=len(matchup_names),
            row_predictor_count=len(predictor_columns),
        )

    def _build_target_contract(self) -> TargetContract:
        fields = tuple(
            {"name": name, "type": kind, "nullable": nullable}
            for name, kind, nullable in TARGET_SCHEMA
        )
        states = {
            "win_loss": "binary eligible only when canonical winner_id equals fighter_1_id or fighter_2_id",
            "draw": "preserved; binary winner target null/ineligible",
            "no_contest": "preserved; binary winner target null/ineligible",
            "other": "preserved; binary winner target null/ineligible; not relabeled as overturned",
            "unknown": "preserved; binary winner target null/ineligible",
            "overturned": "not a current canonical result enum; F02 does not infer it",
        }
        payload = {
            "target_contract_version": TARGET_CONTRACT_VERSION,
            "fields": fields,
            "states": states,
        }
        return TargetContract(
            TARGET_CONTRACT_VERSION,
            fields,
            states,
            deterministic_hash(payload),
        )

    @property
    def schema(self) -> ReplaySchema:
        return self._schema

    @property
    def target_contract(self) -> TargetContract:
        return self._target_contract

    def build_row(self, target: FightRef) -> ReplayRow:
        cutoff = prediction_as_of(target)
        matchup = self.materializer.materialize_matchup(
            target.fighter_a_id,
            target.fighter_b_id,
            cutoff,
            target_fight_id=target.fight_id,
            consumer=PREDICTOR_CONSUMER,
        )
        if target.fight_id in {
            fight_id
            for value in list(matchup.fighter_1.values.values()) + list(matchup.fighter_2.values.values())
            for fight_id in value.lineage_fight_ids
        }:
            raise ReplayError(f"target leaked into historical lineage: {target.fight_id}")
        if parse_cutoff(cutoff).date() != target.event_date:
            raise ReplayError(f"target cutoff date mismatch for {target.fight_id}")
        row: dict[str, Any] = {
            "fight_id": target.fight_id,
            "event_id": target.event_id,
            "event_date": target.event_date.isoformat(),
            "prediction_as_of": cutoff,
            "promotion": target.promotion,
            "scheduled_rounds": target.scheduled_rounds,
            "fighter_1_id": matchup.fighter_1_id,
            "fighter_2_id": matchup.fighter_2_id,
        }
        audit: dict[str, dict[str, Any]] = {}

        shared_by_concept: dict[str, str] = {}
        for source_name in sorted(matchup.fighter_1.values):
            concept = _concept_from_materialized(source_name)
            if concept in SHARED_FIGHT_CONTEXT_CONCEPTS:
                shared_by_concept[concept] = source_name

        if tuple(sorted(shared_by_concept)) != tuple(sorted(SHARED_FIGHT_CONTEXT_CONCEPTS)):
            raise ReplayError(
                "shared fight-context materialization drift "
                f"expected={sorted(SHARED_FIGHT_CONTEXT_CONCEPTS)} actual={sorted(shared_by_concept)}"
            )

        for concept in SHARED_FIGHT_CONTEXT_CONCEPTS:
            source_name = shared_by_concept[concept]
            left = matchup.fighter_1.values[source_name]
            right = matchup.fighter_2.values.get(source_name)
            if right is None:
                raise ReplayError(
                    f"shared fight-context {source_name} missing from fighter_2 for {target.fight_id}"
                )
            if left.to_dict() != right.to_dict():
                raise ReplayError(
                    f"shared fight-context disagreement for {source_name} on {target.fight_id}"
                )
            name = _row_name("ctx", source_name)
            if concept == "scheduled_rounds":
                if row["scheduled_rounds"] != left.value:
                    raise ReplayError(
                        f"scheduled_rounds canonical/F01 disagreement on {target.fight_id}: "
                        f"{row['scheduled_rounds']!r} != {left.value!r}"
                    )
            else:
                row[name] = left.value
            meta = left.to_dict()
            meta["source_materialized_name"] = source_name
            meta["orientation_role"] = "fight_context"
            audit[name] = meta

        for role, state in (("f1", matchup.fighter_1), ("f2", matchup.fighter_2)):
            for source_name, value in sorted(state.values.items()):
                if _concept_from_materialized(source_name) in SHARED_FIGHT_CONTEXT_CONCEPTS:
                    continue
                name = _row_name(role, source_name)
                row[name] = value.value
                meta = value.to_dict()
                meta["source_materialized_name"] = source_name
                meta["orientation_role"] = role
                audit[name] = meta
        for source_name, value in sorted(matchup.interactions.items()):
            name = _row_name("mx", source_name)
            row[name] = value.value
            meta = value.to_dict()
            meta["source_materialized_name"] = source_name
            meta["orientation_role"] = "mx"
            audit[name] = meta
        expected = [item["name"] for item in self.schema.columns]
        if list(row) != expected:
            missing = [name for name in expected if name not in row]
            extra = [name for name in row if name not in expected]
            raise ReplayError(f"row/schema mismatch missing={missing} extra={extra}")
        return ReplayRow(row, audit)

    def target_fields(self, target: FightRef, fighter_1_id: str, fighter_2_id: str) -> dict[str, Any]:
        state = target.result or "unknown"
        eligible = False
        fighter_1_win: bool | None = None
        if state == "win_loss":
            if target.winner_id == fighter_1_id:
                eligible = True
                fighter_1_win = True
            elif target.winner_id == fighter_2_id:
                eligible = True
                fighter_1_win = False
            else:
                raise ReplayError(
                    f"win_loss target {target.fight_id} has winner outside oriented participants"
                )
        return {
            "target_state": state,
            "binary_winner_eligible": eligible,
            "fighter_1_win": fighter_1_win,
            "winner_id": target.winner_id,
        }

    def equivalence_fixture(self, max_targets: int = 16) -> list[FightRef]:
        universe = self.targets()
        chosen: dict[str, FightRef] = {}
        for target in universe:
            cutoff = prediction_as_of(target)
            counts = [len(self.store.prior_fights(fid, cutoff)) for fid in (target.fighter_a_id, target.fighter_b_id)]
            if min(counts) == 0:
                chosen.setdefault("zero", target)
            if any(1 <= count <= 2 for count in counts):
                chosen.setdefault("sparse", target)
            if max(counts) >= 10:
                chosen.setdefault("long", target)
            if any(
                (prior.promotion or "").casefold() != "ufc"
                for fid in (target.fighter_a_id, target.fighter_b_id)
                for prior in self.store.prior_fights(fid, cutoff)
            ):
                chosen.setdefault("external", target)
            if target.event_date.year < 2001:
                chosen.setdefault("early", target)
            if target.event_date.year >= 2020:
                chosen.setdefault("modern", target)
            if target.scheduled_rounds == 3:
                chosen.setdefault("three_round", target)
            if target.scheduled_rounds == 5:
                chosen.setdefault("five_round", target)
            if len(chosen) >= 8:
                break
        # Add deterministic spread so equivalence is not only category-driven.
        if universe:
            for numerator in range(1, 9):
                idx = ((len(universe) - 1) * numerator) // 9
                chosen.setdefault(f"quantile_{numerator}", universe[idx])
        result = sorted({item.fight_id: item for item in chosen.values()}.values(), key=target_sort_key)
        return result[:max_targets]

    def validate_reference_equivalence(self, targets: Sequence[FightRef]) -> dict[str, Any]:
        if not targets:
            raise ReplayError("equivalence fixture is empty")
        dates = [target.event_date for target in targets]
        reference = ReplayEngine(self.root, optimized=False)
        optimized = ReplayEngine(self.root, optimized=True, target_dates=dates)
        comparisons: list[dict[str, Any]] = []
        for target in targets:
            ref = reference.build_row(reference.store.require_fight(target.fight_id))
            opt = optimized.build_row(optimized.store.require_fight(target.fight_id))
            if ref.row != opt.row or ref.audit != opt.audit:
                raise ReplayError(f"optimized/reference divergence for target {target.fight_id}")
            comparisons.append({
                "fight_id": target.fight_id,
                "event_date": target.event_date.isoformat(),
                "row_sha256": deterministic_hash(ref.row),
                "audit_sha256": deterministic_hash(ref.audit),
            })
        return {
            "status": "exact_equal",
            "target_count": len(comparisons),
            "targets": comparisons,
            "comparison_sha256": deterministic_hash(comparisons),
        }

    def replay_rows(
        self,
        targets: Sequence[FightRef],
        *,
        collect_audit: bool = True,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        self.validate_target_universe(targets)
        rows: list[dict[str, Any]] = []
        diagnostics = CoverageDiagnostics(self.elapsed_feature_names)
        seen: set[str] = set()
        for target in targets:
            if target.fight_id in seen:
                raise ReplayError(f"duplicate target during replay: {target.fight_id}")
            replay_row = self.build_row(target)
            cutoff = prediction_as_of(target)
            counts = (
                len(self.store.prior_fights(replay_row.row["fighter_1_id"], cutoff)),
                len(self.store.prior_fights(replay_row.row["fighter_2_id"], cutoff)),
            )
            external = any(
                (prior.promotion or "").casefold() != "ufc"
                for fid in (replay_row.row["fighter_1_id"], replay_row.row["fighter_2_id"])
                for prior in self.store.prior_fights(fid, cutoff)
            )
            diagnostics.add(target, replay_row, counts, external)
            rows.append(replay_row.row)
            seen.add(target.fight_id)
        if [row["fight_id"] for row in rows] != [target.fight_id for target in targets]:
            raise ReplayError("replay row order diverged from deterministic target order")
        return rows, diagnostics.to_dict() if collect_audit else {}

    def build_manifest(
        self,
        *,
        targets: Sequence[FightRef],
        rows: Sequence[dict[str, Any]],
        diagnostics: dict[str, Any],
        chunks: Sequence[dict[str, Any]],
        artifact_sha256: str,
        parquet_bytes: int,
        equivalence: dict[str, Any] | None,
        created_at_utc: str | None = None,
        code_commit: str | None = None,
    ) -> dict[str, Any]:
        source_names = self.materializer.names()
        f01_manifest = self.materializer.manifest(
            prediction_cutoff=CUTOFF_POLICY,
            row_count=len(rows),
            consumer=None,
            materialized_names=source_names,
            code_commit=code_commit or git_head(self.root),
            generated_at_utc="1970-01-01T00:00:00Z",
        ).deterministic
        all_targets = self.targets()
        emitted_ids = {row["fight_id"] for row in rows}
        excluded = [item.fight_id for item in targets if item.fight_id not in emitted_ids]
        deterministic = {
            "status": REPLAY_STATUS,
            "replay_schema_version": REPLAY_SCHEMA_VERSION,
            "target_contract_version": TARGET_CONTRACT_VERSION,
            "code_commit": code_commit or git_head(self.root),
            "target_universe_definition": "all canonical data/canonical/v0/fights.csv rows with resolvable distinct canonical participants",
            "canonical_total_fight_count": len(all_targets),
            "selected_target_count": len(targets),
            "emitted_row_count": len(rows),
            "excluded_target_count": len(excluded),
            "excluded_target_ids": excluded,
            "target_ordering": TARGET_ORDERING,
            "cutoff_policy": CUTOFF_POLICY,
            "same_day_policy": "exclude every same-date fight from history; never infer bout order",
            "orientation_policy": f01_manifest["fighter_orientation_policy"],
            "consumer_selection": "broad_active_v1_surface",
            "feature_contract_version": f01_manifest["feature_contract_version"],
            "governance_version": f01_manifest["feature_governance_version"],
            "feature_governance_sha256": f01_manifest["feature_governance_sha256"],
            "feature_catalog_sha256": f01_manifest["feature_catalog_sha256"],
            "feature_schema_sha256": f01_manifest["feature_schema_sha256"],
            "terminology_sha256": f01_manifest["terminology_sha256"],
            "feature_dependencies_sha256": f01_manifest["feature_dependencies_sha256"],
            "ruleset_registry_sha256": f01_manifest["ruleset_registry_sha256"],
            "data_contract_version": f01_manifest["data_contract_version"],
            "data_freeze_sha256": f01_manifest["data_freeze_sha256"],
            "canonical_manifest_sha256": f01_manifest["canonical_manifest_sha256"],
            "canonical_manifest_build": f01_manifest["canonical_manifest_build"],
            "durable_feature_ids": f01_manifest["feature_ids"],
            "feature_methodologies": f01_manifest["feature_methodologies"],
            "f01_materialized_feature_names": source_names,
            "replay_schema": self.schema.to_dict(),
            "target_contract": self.target_contract.to_dict(),
            "chunk_policy": CHUNK_POLICY,
            "chunks": list(chunks),
            "artifact_logical_sha256": artifact_sha256,
            "parquet_total_bytes": parquet_bytes,
            "coverage_sha256": deterministic_hash(diagnostics),
            "optimized_reference_equivalence": equivalence,
            "known_limitations": [
                "DR_EXACT_POSITIONAL_DURATION_V1 remains DATA_REQUIRED / SIMULATOR_REQUIRED and is not synthesized.",
                "Canonical v0 has no governed sex/gender field; sex/gender coverage is not inferred.",
                "Canonical event-date chronology cannot order bouts within the same day/event; all same-date history is excluded.",
            ],
        }
        return {
            "deterministic": deterministic,
            "deterministic_manifest_sha256": deterministic_hash(deterministic),
            "runtime": {"created_at_utc": created_at_utc or utc_now()},
        }


def build_target_row(target: FightRef, predictor_row: dict[str, Any]) -> dict[str, Any]:
    fighter_1 = predictor_row["fighter_1_id"]
    fighter_2 = predictor_row["fighter_2_id"]
    state = target.result or "unknown"
    eligible = state == "win_loss" and target.winner_id in {fighter_1, fighter_2}
    if state == "win_loss" and not eligible:
        raise ReplayError(f"win_loss target {target.fight_id} has invalid canonical winner_id")
    return {
        **predictor_row,
        "target_state": state,
        "binary_winner_eligible": eligible,
        "fighter_1_win": (target.winner_id == fighter_1) if eligible else None,
        "winner_id": target.winner_id,
    }


def parquet_schema(schema: ReplaySchema, *, include_targets: bool = False) -> Any:
    try:
        import pyarrow as pa  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ReplayError("Parquet output requires pyarrow") from exc
    type_map = {
        "string": pa.string(),
        "int64": pa.int64(),
        "float64": pa.float64(),
        "bool": pa.bool_(),
    }
    fields = [
        pa.field(item["name"], type_map[item["type"]], nullable=bool(item["nullable"]))
        for item in schema.columns
    ]
    if include_targets:
        fields += [pa.field(name, type_map[kind], nullable=nullable) for name, kind, nullable in TARGET_SCHEMA]
    return pa.schema(fields)


def write_parquet(path: Path, rows: Sequence[dict[str, Any]], schema: ReplaySchema, *, include_targets: bool = False) -> None:
    try:
        import pyarrow as pa  # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ReplayError("Parquet output requires pyarrow") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(list(rows), schema=parquet_schema(schema, include_targets=include_targets))
    pq.write_table(
        table,
        path,
        compression="zstd",
        use_dictionary=True,
        write_statistics=True,
        version="2.6",
    )


def read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ReplayError("Parquet input requires pyarrow") from exc
    return pq.read_table(path).to_pylist()
