"""M1 regularized shared-feature UFC winner model.

M1 consumes the frozen F02 historical predictor replay and expands M0's compact
linear benchmark to the broad governed fighter/matchup surface.  It remains a
chronological, deterministic, validation-only logistic model: no market inputs,
no outcome-driven feature selection, no nonlinear model family, and no feature
rebuild are permitted here.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ufc_edge.models.m0 import (
    MODEL_ERA_START,
    VALIDATION_YEARS,
    RANDOM_SEED,
    F02_IDENTITY,
    calibration_table,
    canonical_json,
    empirical_experience_probability,
    fold_frames,
    history_depth_slice,
    load_modeling_table,
    metric_bundle,
    oof_logical_hash as m0_oof_logical_hash,
    primary_population,
    validate_f02_identity,
)


M0_OOF_LOGICAL_SHA256 = "708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c"
M0_FREEZE_VERSION = "1.0.0"
M0_ACTIONS_RUN_ID = 34676508116
M0_ARTIFACT_ID = 10292502486
M0_ARTIFACT_ZIP_SHA256 = "69e2a4db932ecbfd747a387b708d5107e3d682223d4f608b850a00a605af3be0"
C_GRID = (0.01, 0.1, 1.0, 10.0)
INNER_VALIDATION_START_YEAR = 2013
EXPECTED_F02_PREDICTORS = 200
EXPECTED_FIGHTER_SIDE_PREDICTORS = 96
EXPECTED_MATCHUP_PREDICTORS = 5
SHARED_CONTEXT_COLUMNS = ("scheduled_rounds", "ctx__title_bout", "ctx__weight_class")
IDENTITY_COLUMNS = {
    "fight_id", "event_id", "event_date", "prediction_as_of", "promotion",
    "fighter_1_id", "fighter_2_id", "winner_id", "target_state",
    "binary_winner_eligible", "fighter_1_win",
}
FORBIDDEN_MODEL_TOKENS = (
    "odds", "sportsbook", "bookmaker", "price", "roi", "kelly", "closing_line", "market_probability",
)


class M1Error(ValueError):
    """Raised when M1 contracts or validation inputs fail closed."""


@dataclass(frozen=True)
class FeatureContract:
    fighter_pairs: tuple[tuple[str, str, str], ...]
    matchup_pairs: tuple[tuple[str, str, str], ...]
    self_antisymmetric_matchups: tuple[tuple[str, str], ...]
    excluded_shared_context: tuple[str, ...]
    source_predictor_count: int

    @property
    def model_source_columns(self) -> tuple[str, ...]:
        columns: list[str] = []
        for _, f1_col, f2_col in self.fighter_pairs:
            columns.extend((f1_col, f2_col))
        for _, left_col, right_col in self.matchup_pairs:
            columns.extend((left_col, right_col))
        columns.extend(column for _, column in self.self_antisymmetric_matchups)
        return tuple(columns)

    @property
    def output_names(self) -> tuple[str, ...]:
        names: list[str] = []
        for source, _, _ in self.fighter_pairs:
            names.extend((f"pair::{source}::diff", f"pair::{source}::missing_diff"))
        for source, _, _ in self.matchup_pairs:
            names.extend((f"matchup::{source}::diff", f"matchup::{source}::missing_diff"))
        names.extend(f"matchup::{source}::value" for source, _ in self.self_antisymmetric_matchups)
        return tuple(names)


def _schema_items(schema: dict[str, Any]) -> list[dict[str, Any]]:
    items = schema.get("columns", [])
    if not isinstance(items, list):
        raise M1Error("F02 schema columns must be a list")
    return [item for item in items if isinstance(item, dict)]


def discover_feature_contract(schema: dict[str, Any], *, strict_counts: bool = True) -> FeatureContract:
    items = _schema_items(schema)
    predictors = [item for item in items if item.get("predictor") is True]
    by_name = {str(item.get("name")): item for item in predictors}

    if strict_counts and len(predictors) != EXPECTED_F02_PREDICTORS:
        raise M1Error(f"unexpected F02 predictor count {len(predictors)} != {EXPECTED_F02_PREDICTORS}")

    shared = tuple(name for name in SHARED_CONTEXT_COLUMNS if name in by_name)
    if tuple(shared) != SHARED_CONTEXT_COLUMNS:
        missing = sorted(set(SHARED_CONTEXT_COLUMNS) - set(shared))
        raise M1Error(f"missing required F02 diagnostic context columns: {missing}")

    f1_by_source: dict[str, str] = {}
    f2_by_source: dict[str, str] = {}
    matchup_items: list[dict[str, Any]] = []

    for item in predictors:
        name = str(item.get("name"))
        role = item.get("role")
        source = item.get("source_materialized_name")
        if name in SHARED_CONTEXT_COLUMNS:
            continue
        if role == "f1":
            if not source:
                raise M1Error(f"fighter-1 predictor lacks source_materialized_name: {name}")
            f1_by_source[str(source)] = name
        elif role == "f2":
            if not source:
                raise M1Error(f"fighter-2 predictor lacks source_materialized_name: {name}")
            f2_by_source[str(source)] = name
        elif role == "mx":
            matchup_items.append(item)
        else:
            raise M1Error(f"unexpected predictor role for M1 model input: {name} role={role!r}")

    if set(f1_by_source) != set(f2_by_source):
        raise M1Error("F02 fighter-side predictor source sets do not match")
    if strict_counts and len(f1_by_source) != EXPECTED_FIGHTER_SIDE_PREDICTORS:
        raise M1Error(
            f"unexpected fighter-side predictor count {len(f1_by_source)} != {EXPECTED_FIGHTER_SIDE_PREDICTORS}"
        )
    if strict_counts and len(matchup_items) != EXPECTED_MATCHUP_PREDICTORS:
        raise M1Error(f"unexpected matchup predictor count {len(matchup_items)} != {EXPECTED_MATCHUP_PREDICTORS}")

    fighter_pairs = tuple(
        (source, f1_by_source[source], f2_by_source[source])
        for source in sorted(f1_by_source)
    )

    mx_by_source = {
        str(item.get("source_materialized_name")): str(item.get("name"))
        for item in matchup_items
    }
    matchup_pairs: list[tuple[str, str, str]] = []
    self_antisymmetric: list[tuple[str, str]] = []
    consumed: set[str] = set()

    for source in sorted(mx_by_source):
        if source in consumed:
            continue
        if "f1_vs_f2" in source:
            mirror = source.replace("f1_vs_f2", "f2_vs_f1", 1)
            if mirror not in mx_by_source:
                raise M1Error(f"directional matchup predictor lacks mirror: {source}")
            base = source.replace("f1_vs_f2", "direction", 1)
            matchup_pairs.append((base, mx_by_source[source], mx_by_source[mirror]))
            consumed.update((source, mirror))
            continue
        if "f2_vs_f1" in source:
            mirror = source.replace("f2_vs_f1", "f1_vs_f2", 1)
            if mirror not in mx_by_source:
                raise M1Error(f"directional matchup predictor lacks mirror: {source}")
            continue
        concept = next(
            (str(item.get("source_concept")) for item in matchup_items if str(item.get("source_materialized_name")) == source),
            "",
        )
        if concept != "reach_difference_cm" and "reach_difference_cm" not in source:
            raise M1Error(f"unrecognized unpaired matchup predictor: {source}")
        self_antisymmetric.append((source, mx_by_source[source]))
        consumed.add(source)

    model_columns = [column for _, a, b in fighter_pairs for column in (a, b)]
    model_columns += [column for _, a, b in matchup_pairs for column in (a, b)]
    model_columns += [column for _, column in self_antisymmetric]
    bad_identity = sorted(set(model_columns) & IDENTITY_COLUMNS)
    if bad_identity:
        raise M1Error(f"identity/provenance columns entered M1 model matrix: {bad_identity}")
    bad_context = sorted(set(model_columns) & set(SHARED_CONTEXT_COLUMNS))
    if bad_context:
        raise M1Error(f"shared diagnostic context entered M1 model matrix: {bad_context}")
    bad_market = [
        column for column in model_columns
        if any(token in column.casefold() for token in FORBIDDEN_MODEL_TOKENS)
    ]
    if bad_market:
        raise M1Error(f"forbidden market/sportsbook token in M1 model matrix: {bad_market}")

    source_predictor_count = len(model_columns)
    expected_source_count = len(predictors) - len(SHARED_CONTEXT_COLUMNS)
    if source_predictor_count != expected_source_count:
        raise M1Error(
            f"M1 source predictor accounting mismatch {source_predictor_count} != {expected_source_count}"
        )

    return FeatureContract(
        fighter_pairs=fighter_pairs,
        matchup_pairs=tuple(matchup_pairs),
        self_antisymmetric_matchups=tuple(self_antisymmetric),
        excluded_shared_context=SHARED_CONTEXT_COLUMNS,
        source_predictor_count=source_predictor_count,
    )


@dataclass
class BroadSymmetricProjector:
    contract: FeatureContract
    medians: dict[str, float] | None = None

    @property
    def output_names(self) -> tuple[str, ...]:
        return self.contract.output_names

    @staticmethod
    def _pooled_median(frame: pd.DataFrame, left: str, right: str, label: str) -> float:
        pooled = pd.concat(
            [pd.to_numeric(frame[left], errors="coerce"), pd.to_numeric(frame[right], errors="coerce")],
            ignore_index=True,
        )
        value = pooled.median(skipna=True)
        if pd.isna(value):
            raise M1Error(f"training fold has no observed values for {label}")
        return float(value)

    def fit(self, frame: pd.DataFrame) -> "BroadSymmetricProjector":
        medians: dict[str, float] = {}
        for source, left, right in self.contract.fighter_pairs:
            medians[f"pair::{source}"] = self._pooled_median(frame, left, right, source)
        for source, left, right in self.contract.matchup_pairs:
            medians[f"matchup::{source}"] = self._pooled_median(frame, left, right, source)
        self.medians = medians
        return self

    @staticmethod
    def _paired_projection(
        frame: pd.DataFrame, left: str, right: str, median: float
    ) -> tuple[np.ndarray, np.ndarray]:
        a = pd.to_numeric(frame[left], errors="coerce")
        b = pd.to_numeric(frame[right], errors="coerce")
        missing_diff = a.isna().to_numpy(dtype=float) - b.isna().to_numpy(dtype=float)
        diff = (a.fillna(median) - b.fillna(median)).to_numpy(dtype=float)
        return diff, missing_diff

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        if self.medians is None:
            raise M1Error("projector must be fit before transform")
        columns: list[np.ndarray] = []
        for source, left, right in self.contract.fighter_pairs:
            diff, missing = self._paired_projection(frame, left, right, self.medians[f"pair::{source}"])
            columns.extend((diff, missing))
        for source, left, right in self.contract.matchup_pairs:
            diff, missing = self._paired_projection(frame, left, right, self.medians[f"matchup::{source}"])
            columns.extend((diff, missing))
        for _, column in self.contract.self_antisymmetric_matchups:
            # A missing already-oriented difference has no safe directional missing flag.
            # Neutral zero model-space imputation preserves exact swap antisymmetry.
            values = pd.to_numeric(frame[column], errors="coerce").fillna(0.0).to_numpy(dtype=float)
            columns.append(values)
        if not columns:
            raise M1Error("M1 projected matrix is empty")
        matrix = np.column_stack(columns)
        if not np.isfinite(matrix).all():
            raise M1Error("M1 projected matrix contains non-finite values")
        return matrix


@dataclass
class M1Logistic:
    projector: BroadSymmetricProjector
    scaler: StandardScaler
    model: LogisticRegression
    C: float

    @classmethod
    def fit(
        cls,
        frame: pd.DataFrame,
        target: pd.Series,
        contract: FeatureContract,
        *,
        C: float,
    ) -> "M1Logistic":
        if C not in C_GRID:
            raise M1Error(f"C={C} is outside predeclared M1 grid")
        projector = BroadSymmetricProjector(contract).fit(frame)
        matrix = projector.transform(frame)
        scaler = StandardScaler(with_mean=False)
        scaled = scaler.fit_transform(matrix)
        model = LogisticRegression(
            penalty="l2",
            C=float(C),
            solver="lbfgs",
            max_iter=4000,
            random_state=RANDOM_SEED,
            fit_intercept=False,
        )
        model.fit(scaled, target.astype(int).to_numpy())
        return cls(projector, scaler, model, float(C))

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        matrix = self.projector.transform(frame)
        return self.model.predict_proba(self.scaler.transform(matrix))[:, 1]

    def coefficient_map(self) -> dict[str, float]:
        return {
            name: float(value)
            for name, value in zip(self.projector.output_names, self.model.coef_[0], strict=True)
        }


def swap_model_columns(frame: pd.DataFrame, contract: FeatureContract) -> pd.DataFrame:
    swapped = frame.copy()
    for _, left, right in contract.fighter_pairs:
        swapped[left] = frame[right].to_numpy()
        swapped[right] = frame[left].to_numpy()
    for _, left, right in contract.matchup_pairs:
        swapped[left] = frame[right].to_numpy()
        swapped[right] = frame[left].to_numpy()
    for _, column in contract.self_antisymmetric_matchups:
        values = pd.to_numeric(frame[column], errors="coerce")
        swapped[column] = -values
    return swapped


def orientation_error(model: M1Logistic, frame: pd.DataFrame, contract: FeatureContract) -> float:
    original = model.predict_proba(frame)
    swapped = model.predict_proba(swap_model_columns(frame, contract))
    return float(np.max(np.abs(original + swapped - 1.0)))


def load_frozen_m0_oof(m0_dir: Path) -> pd.DataFrame:
    path = m0_dir / "m0_oof_predictions.parquet"
    if not path.exists():
        raise M1Error(f"missing frozen M0 OOF artifact: {path}")
    oof = pd.read_parquet(path)
    required = (
        "fight_id", "event_date", "fold_id", "target",
        "naive_probability", "empirical_probability", "logistic_probability",
    )
    missing = [column for column in required if column not in oof.columns]
    if missing:
        raise M1Error(f"frozen M0 OOF artifact missing columns: {missing}")
    oof = oof.loc[:, required].copy()
    oof["event_date"] = oof["event_date"].astype(str)
    oof["fold_id"] = oof["fold_id"].astype(str)
    if oof["fight_id"].duplicated().any():
        raise M1Error("frozen M0 OOF fight_id is not unique")
    logical_hash = m0_oof_logical_hash(oof)
    if logical_hash != M0_OOF_LOGICAL_SHA256:
        raise M1Error(
            f"authoritative frozen M0 OOF hash mismatch: {logical_hash} != {M0_OOF_LOGICAL_SHA256}"
        )
    return oof


def inner_validation_years(outer_train: pd.DataFrame) -> tuple[int, ...]:
    years = sorted(int(year) for year in outer_train["event_date"].dt.year.unique())
    candidates = [year for year in years if year >= INNER_VALIDATION_START_YEAR]
    valid: list[int] = []
    for year in candidates:
        prior = outer_train[outer_train["event_date"].dt.year < year]
        current = outer_train[outer_train["event_date"].dt.year == year]
        if not prior.empty and not current.empty:
            valid.append(year)
    if len(valid) < 2:
        raise M1Error("nested chronological regularization selection requires at least two inner folds")
    return tuple(valid)


def select_regularization(
    outer_train: pd.DataFrame,
    contract: FeatureContract,
) -> tuple[float, dict[str, Any]]:
    years = inner_validation_years(outer_train)
    candidate_rows: list[dict[str, Any]] = []

    for C in C_GRID:
        targets: list[int] = []
        probabilities: list[float] = []
        folds: list[dict[str, Any]] = []
        for year in years:
            train, valid = fold_frames(outer_train, year)
            y_train = train["fighter_1_win"].astype(int)
            y_valid = valid["fighter_1_win"].astype(int)
            model = M1Logistic.fit(train, y_train, contract, C=C)
            prob = model.predict_proba(valid)
            metric = metric_bundle(y_valid, prob)
            folds.append({"fold_id": str(year), **metric})
            targets.extend(y_valid.tolist())
            probabilities.extend(prob.tolist())
        pooled = metric_bundle(targets, probabilities)
        candidate_rows.append({"C": float(C), "pooled": pooled, "folds": folds})

    chosen = min(candidate_rows, key=lambda row: (row["pooled"]["log_loss"], row["C"]))
    return float(chosen["C"]), {
        "selection_metric": "pooled_inner_oof_log_loss",
        "tie_break": "smaller_C_stronger_regularization",
        "inner_validation_years": [str(year) for year in years],
        "candidates": candidate_rows,
        "selected_C": float(chosen["C"]),
    }


def _slice_metrics(oof: pd.DataFrame, mask: pd.Series) -> dict[str, Any] | None:
    subset = oof.loc[mask]
    if len(subset) < 30:
        return None
    return metric_bundle(subset["target"], subset["m1_probability"])


def slice_report(oof: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {"history_depth": {}, "fight_length": {}, "title": {}, "weight_class": {}}
    for name in ("zero_history", "sparse_history", "established_history"):
        value = _slice_metrics(oof, oof["history_depth"].eq(name))
        if value is not None:
            out["history_depth"][name] = value
    for rounds in (3, 5):
        value = _slice_metrics(oof, oof["scheduled_rounds"].eq(rounds))
        if value is not None:
            out["fight_length"][str(rounds)] = value
    for title, label in ((True, "title"), (False, "non_title")):
        value = _slice_metrics(oof, oof["title_bout"].eq(title))
        if value is not None:
            out["title"][label] = value
    for weight_class, count in oof["weight_class"].value_counts().items():
        if int(count) < 50:
            continue
        value = _slice_metrics(oof, oof["weight_class"].eq(weight_class))
        if value is not None:
            out["weight_class"][str(weight_class)] = value
    return out


def m1_oof_logical_hash(oof: pd.DataFrame) -> str:
    digest = sha256()
    columns = (
        "fight_id", "event_date", "fold_id", "target",
        "naive_probability", "empirical_probability", "m0_probability", "m1_probability", "selected_C",
    )
    ordered = oof.sort_values(["event_date", "fight_id"])
    for row in ordered.loc[:, columns].itertuples(index=False, name=None):
        payload = list(row)
        payload[1] = str(payload[1])
        digest.update(canonical_json(payload).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _verdict(aggregate: dict[str, dict[str, Any]], fold_rows: list[dict[str, Any]]) -> str:
    m0 = aggregate["m0"]
    m1 = aggregate["m1"]
    better_both = sum(
        1 for row in fold_rows
        if row["m1"]["log_loss"] < row["m0"]["log_loss"]
        and row["m1"]["brier"] < row["m0"]["brier"]
    )
    if (
        m1["log_loss"] < m0["log_loss"]
        and m1["brier"] < m0["brier"]
        and better_both >= int(np.ceil((2.0 / 3.0) * len(fold_rows)))
    ):
        return "M1_OUTPERFORMS_M0"
    if m1["log_loss"] < m0["log_loss"] or m1["brier"] < m0["brier"]:
        return "M1_MIXED_VS_M0"
    return "M1_DOES_NOT_OUTPERFORM_M0"


def run_validation(f02_dir: Path, m0_dir: Path, output_dir: Path) -> dict[str, Any]:
    identity = validate_f02_identity(f02_dir)
    contract = discover_feature_contract(identity["schema"])
    frame = load_modeling_table(f02_dir)
    population = primary_population(frame)
    frozen_m0 = load_frozen_m0_oof(m0_dir)

    fold_results: list[dict[str, Any]] = []
    coefficient_rows: list[dict[str, Any]] = []
    regularization_rows: list[dict[str, Any]] = []
    oof_parts: list[pd.DataFrame] = []

    for year in VALIDATION_YEARS:
        train, valid = fold_frames(population, year)
        y_train = train["fighter_1_win"].astype(int)
        y_valid = valid["fighter_1_win"].astype(int)

        selected_C, selection = select_regularization(train, contract)
        regularization_rows.append({"outer_fold_id": str(year), **selection})

        m1_model = M1Logistic.fit(train, y_train, contract, C=selected_C)
        m1_prob = m1_model.predict_proba(valid)
        swap_error = orientation_error(m1_model, valid, contract)
        if swap_error > 1e-10:
            raise M1Error(f"orientation invariance failed for {year}: {swap_error}")

        m0_fold = frozen_m0[frozen_m0["fold_id"].eq(str(year))].set_index("fight_id")
        valid_ids = valid["fight_id"].astype(str).tolist()
        if set(m0_fold.index.astype(str)) != set(valid_ids):
            raise M1Error(f"frozen M0 row identity mismatch for outer fold {year}")
        m0_fold = m0_fold.loc[valid_ids]
        frozen_target = pd.to_numeric(m0_fold["target"], errors="raise").astype(int).to_numpy()
        if not np.array_equal(frozen_target, y_valid.to_numpy()):
            raise M1Error(f"frozen M0 target mismatch for outer fold {year}")
        m0_prob = pd.to_numeric(m0_fold["logistic_probability"], errors="raise").to_numpy(dtype=float)
        naive = pd.to_numeric(m0_fold["naive_probability"], errors="raise").to_numpy(dtype=float)
        empirical = pd.to_numeric(m0_fold["empirical_probability"], errors="raise").to_numpy(dtype=float)

        fold_results.append({
            "fold_id": str(year),
            "train_start": str(train["event_date"].min().date()),
            "train_end": str(train["event_date"].max().date()),
            "validation_start": str(valid["event_date"].min().date()),
            "validation_end": str(valid["event_date"].max().date()),
            "train_rows": int(len(train)),
            "validation_rows": int(len(valid)),
            "selected_C": float(selected_C),
            "naive": metric_bundle(y_valid, naive),
            "empirical": metric_bundle(y_valid, empirical),
            "m0": metric_bundle(y_valid, m0_prob),
            "m1": metric_bundle(y_valid, m1_prob),
            "orientation_max_abs_error": swap_error,
        })
        coefficient_rows.append({
            "fold_id": str(year),
            "selected_C": float(selected_C),
            "coefficients": m1_model.coefficient_map(),
        })

        part = pd.DataFrame({
            "fight_id": valid["fight_id"].to_numpy(),
            "event_date": valid["event_date"].dt.date.astype(str).to_numpy(),
            "fold_id": str(year),
            "target": y_valid.to_numpy(),
            "naive_probability": naive,
            "empirical_probability": empirical,
            "m0_probability": m0_prob,
            "m1_probability": m1_prob,
            "selected_C": float(selected_C),
            "scheduled_rounds": valid["scheduled_rounds"].to_numpy(),
            "title_bout": valid["ctx__title_bout"].to_numpy(),
            "weight_class": valid["ctx__weight_class"].to_numpy(),
        })
        part["history_depth"] = history_depth_slice(valid).to_numpy()
        oof_parts.append(part)

    oof = pd.concat(oof_parts, ignore_index=True)
    if oof["fight_id"].duplicated().any():
        raise M1Error("M1 OOF prediction fight_id is not unique")

    m0_reference = pd.DataFrame({
        "fight_id": oof["fight_id"],
        "event_date": oof["event_date"],
        "fold_id": oof["fold_id"],
        "target": oof["target"],
        "naive_probability": oof["naive_probability"],
        "empirical_probability": oof["empirical_probability"],
        "logistic_probability": oof["m0_probability"],
    })
    m0_hash = m0_oof_logical_hash(m0_reference)
    if m0_hash != M0_OOF_LOGICAL_SHA256:
        raise M1Error(f"frozen M0 OOF reproduction mismatch: {m0_hash}")

    aggregate = {
        "naive": metric_bundle(oof["target"], oof["naive_probability"]),
        "empirical": metric_bundle(oof["target"], oof["empirical_probability"]),
        "m0": metric_bundle(oof["target"], oof["m0_probability"]),
        "m1": metric_bundle(oof["target"], oof["m1_probability"]),
    }
    calibration, ece = calibration_table(oof["target"], oof["m1_probability"])
    logical_hash = m1_oof_logical_hash(oof)
    folds_better_both = sum(
        1 for row in fold_results
        if row["m1"]["log_loss"] < row["m0"]["log_loss"]
        and row["m1"]["brier"] < row["m0"]["brier"]
    )

    result = {
        "status": "M1_REGULARIZED_SHARED_FEATURE_WINNER_MODEL_V1_COMPLETE",
        "source": {
            "f02_identity": F02_IDENTITY,
            "m0_freeze_version": M0_FREEZE_VERSION,
            "m0_actions_run_id": M0_ACTIONS_RUN_ID,
            "m0_artifact_id": M0_ARTIFACT_ID,
            "m0_artifact_zip_sha256": M0_ARTIFACT_ZIP_SHA256,
            "m0_oof_logical_sha256_expected": M0_OOF_LOGICAL_SHA256,
            "m0_oof_logical_sha256_loaded": m0_hash,
        },
        "dataset": {
            "total_f02_rows": int(len(frame)),
            "modeling_era_rows": int(len(population)),
            "modeling_era_start": str(MODEL_ERA_START.date()),
            "oof_rows": int(len(oof)),
            "validation_years": [str(year) for year in VALIDATION_YEARS],
        },
        "feature_contract": {
            "f02_predictor_true_count": EXPECTED_F02_PREDICTORS,
            "excluded_shared_diagnostic_context": list(contract.excluded_shared_context),
            "model_source_predictor_count": contract.source_predictor_count,
            "fighter_side_pair_count": len(contract.fighter_pairs),
            "directional_matchup_pair_count": len(contract.matchup_pairs),
            "self_antisymmetric_matchup_count": len(contract.self_antisymmetric_matchups),
            "projected_numeric_dimensions": len(contract.output_names),
            "preprocessing": (
                "training-fold pooled median for paired fighter/directional matchup values; antisymmetric value and "
                "missingness differences; already-oriented reach difference neutral-zero imputation when missing; "
                "StandardScaler(with_mean=false); fit_intercept=false"
            ),
        },
        "regularization": {
            "penalty": "l2",
            "solver": "lbfgs",
            "C_grid": list(C_GRID),
            "selection": "nested expanding chronological inner OOF pooled log loss; ties choose smaller C",
            "inner_validation_start_year": INNER_VALIDATION_START_YEAR,
            "selected_C_by_outer_fold": {
                row["fold_id"]: row["selected_C"] for row in fold_results
            },
        },
        "folds": fold_results,
        "aggregate": aggregate,
        "m1_minus_m0": {
            "log_loss": float(aggregate["m1"]["log_loss"] - aggregate["m0"]["log_loss"]),
            "brier": float(aggregate["m1"]["brier"] - aggregate["m0"]["brier"]),
            "accuracy": float(aggregate["m1"]["accuracy"] - aggregate["m0"]["accuracy"]),
            "auc": (
                None if aggregate["m1"]["auc"] is None or aggregate["m0"]["auc"] is None
                else float(aggregate["m1"]["auc"] - aggregate["m0"]["auc"])
            ),
            "folds_improving_both_primary_metrics": int(folds_better_both),
            "outer_fold_count": len(fold_results),
        },
        "calibration": {
            "expected_calibration_error": ece,
            "bins": calibration,
        },
        "slices": slice_report(oof),
        "orientation": {
            "max_fold_swap_probability_error": float(max(row["orientation_max_abs_error"] for row in fold_results)),
        },
        "oof": {
            "rows": int(len(oof)),
            "logical_sha256": logical_hash,
        },
        "verdict": _verdict(aggregate, fold_results),
        "limitations": [
            "M1 is validation-only; no production model is created.",
            "Shared scheduled-round/title/weight-class context is diagnostic-only and not a model input in M1.",
            "Frozen M0 comparator probabilities are consumed from the authoritative M0 Actions artifact rather than numerically recomputed.",
            "No sportsbook, odds, market probability, ROI, Kelly, or threshold analysis is used in M1.",
            "No outcome-driven feature selection, nonlinear model, ensemble, AutoML, opponent adjustment, or simulator feature is introduced.",
            "2026 is a partial latest-year validation fold as represented in frozen F02.",
        ],
        "self_review": {
            "question": "Did M1 test broad governed F02 signal without changing feature semantics or using market information?",
            "answer": "YES",
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "m1_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    oof.to_parquet(output_dir / "m1_oof_predictions.parquet", index=False)
    (output_dir / "m1_coefficients.json").write_text(
        json.dumps(coefficient_rows, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "m1_regularization_selection.json").write_text(
        json.dumps(regularization_rows, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result
