"""M0 empirical UFC winner baseline.

Validation-only, deliberately simple, chronological, deterministic, and
orientation-safe. F02 remains feature-semantic authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler


MODEL_ERA_START = pd.Timestamp("2010-01-01")
VALIDATION_YEARS = tuple(range(2015, 2027))
RANDOM_SEED = 17

F02_IDENTITY = {
    "replay_schema_version": "1.0.1",
    "schema_sha256": "488c96eed4d86a75da8b763c879a65d6b85959393ec7b6c59f7051b0c03836a8",
    "predictor_logical_sha256": "ac55fd6fc1f19be7afac2007fccceb43b5c3f98327554d0c58fbe6cb0b164383",
    "predictor_manifest_sha256": "27b26736079bba7f5bc811bc96798f35ece36d54f1b0632cbd5e37f57ebd3c07",
    "target_contract_sha256": "fe34f7fd2b70611ec0602d9c9208debf8ec11d7eb8ea1adc0a4104ddb46ffd52",
    "target_logical_sha256": "02b735aabcb354fa16cd3800f72e5ccd504f5fb6dc9963510987c57438a44956",
}

PAIR_SPECS = (
    ("prior_fight_count",
     "f1__fs__prior_fight_count__career__raw",
     "f2__fs__prior_fight_count__career__raw"),
    ("age_at_fight",
     "f1__ctx__age_at_fight",
     "f2__ctx__age_at_fight"),
    ("layoff_days",
     "f1__ctx__layoff_days",
     "f2__ctx__layoff_days"),
    ("sig_strike_accuracy_career",
     "f1__fs__sig_strike_efficiency__accuracy__career__shrunk",
     "f2__fs__sig_strike_efficiency__accuracy__career__shrunk"),
    ("sig_strike_defense_career",
     "f1__fs__sig_strike_efficiency__defense__career__shrunk",
     "f2__fs__sig_strike_efficiency__defense__career__shrunk"),
    ("takedown_success_career",
     "f1__fs__takedown_conversion__success__career__shrunk",
     "f2__fs__takedown_conversion__success__career__shrunk"),
    ("takedown_defense_career",
     "f1__fs__takedown_conversion__defense__career__shrunk",
     "f2__fs__takedown_conversion__defense__career__shrunk"),
)

MATERIALIZED_COLUMNS = tuple(
    column for _, f1, f2 in PAIR_SPECS for column in (f1, f2)
)

IDENTITY_COLUMNS = {
    "fight_id", "event_id", "event_date", "prediction_as_of", "promotion",
    "fighter_1_id", "fighter_2_id",
}
FORBIDDEN_MODEL_TOKENS = ("odds", "sportsbook", "price", "roi", "closing_line")


class M0Error(ValueError):
    """Raised when M0 contracts or inputs fail closed."""


@dataclass
class SymmetricPairProjector:
    """Training-fold-only pooled-median paired projection.

    For each governed fighter-side pair, learn one median from the pooled
    training observations across both sides. Emit:
      value_diff = imputed(f1) - imputed(f2)
      missing_diff = missing(f1) - missing(f2)

    Both outputs negate exactly when fighter presentation is swapped.
    """

    medians: dict[str, float] | None = None

    @property
    def output_names(self) -> list[str]:
        return [
            name
            for concept, _, _ in PAIR_SPECS
            for name in (f"{concept}__diff", f"{concept}__missing_diff")
        ]

    def fit(self, frame: pd.DataFrame) -> "SymmetricPairProjector":
        medians: dict[str, float] = {}
        for concept, f1_col, f2_col in PAIR_SPECS:
            pooled = pd.concat([frame[f1_col], frame[f2_col]], ignore_index=True)
            value = pooled.median(skipna=True)
            if pd.isna(value):
                raise M0Error(f"training fold has no observed values for {concept}")
            medians[concept] = float(value)
        self.medians = medians
        return self

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        if self.medians is None:
            raise M0Error("projector must be fit before transform")
        columns: list[np.ndarray] = []
        for concept, f1_col, f2_col in PAIR_SPECS:
            a = pd.to_numeric(frame[f1_col], errors="coerce")
            b = pd.to_numeric(frame[f2_col], errors="coerce")
            missing_a = a.isna().to_numpy(dtype=float)
            missing_b = b.isna().to_numpy(dtype=float)
            median = self.medians[concept]
            diff = (a.fillna(median) - b.fillna(median)).to_numpy(dtype=float)
            missing_diff = missing_a - missing_b
            columns.extend([diff, missing_diff])
        return np.column_stack(columns)


@dataclass
class M0Logistic:
    projector: SymmetricPairProjector
    scaler: StandardScaler
    model: LogisticRegression

    @classmethod
    def fit(cls, frame: pd.DataFrame, target: pd.Series) -> "M0Logistic":
        projector = SymmetricPairProjector().fit(frame)
        matrix = projector.transform(frame)
        scaler = StandardScaler(with_mean=False)
        scaled = scaler.fit_transform(matrix)
        model = LogisticRegression(
            penalty="l2",
            C=1.0,
            solver="lbfgs",
            max_iter=2000,
            random_state=RANDOM_SEED,
            fit_intercept=False,
        )
        model.fit(scaled, target.astype(int).to_numpy())
        return cls(projector, scaler, model)

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        matrix = self.projector.transform(frame)
        scaled = self.scaler.transform(matrix)
        return self.model.predict_proba(scaled)[:, 1]

    def coefficient_map(self) -> dict[str, float]:
        return {
            name: float(value)
            for name, value in zip(
                self.projector.output_names,
                self.model.coef_[0],
                strict=True,
            )
        }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise M0Error(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise M0Error(f"{path} must contain a JSON object")
    return value


def validate_model_columns_against_schema(schema: dict[str, Any]) -> None:
    validate_model_columns_against_schema(schema)


def validate_f02_identity(f02_dir: Path) -> dict[str, Any]:
    schema = _read_json(f02_dir / "schema.json")
    manifest = _read_json(f02_dir / "manifest.json")
    target_manifest = _read_json(f02_dir / "target_manifest.json")
    summary = _read_json(f02_dir / "summary.json")

    if schema.get("replay_schema_version") != F02_IDENTITY["replay_schema_version"]:
        raise M0Error("F02 replay schema version mismatch")
    if schema.get("schema_sha256") != F02_IDENTITY["schema_sha256"]:
        raise M0Error("F02 schema hash mismatch")
    if summary.get("predictor_logical_sha256") != F02_IDENTITY["predictor_logical_sha256"]:
        raise M0Error("F02 predictor logical hash mismatch")
    if summary.get("predictor_manifest_sha256") != F02_IDENTITY["predictor_manifest_sha256"]:
        raise M0Error("F02 predictor manifest hash mismatch")

    target_det = target_manifest.get("deterministic", {})
    target_contract = manifest.get("deterministic", {}).get("target_contract", {})
    if target_contract.get("contract_sha256") != F02_IDENTITY["target_contract_sha256"]:
        raise M0Error("F02 target contract hash mismatch")
    if target_det.get("target_logical_sha256") != F02_IDENTITY["target_logical_sha256"]:
        raise M0Error("F02 target logical hash mismatch")

    schema_by_name = {item["name"]: item for item in schema.get("columns", [])}
    missing = sorted(set(MATERIALIZED_COLUMNS) - set(schema_by_name))
    if missing:
        raise M0Error(f"M0 materialized columns absent from F02 schema: {missing}")
    for column in MATERIALIZED_COLUMNS:
        if schema_by_name[column].get("predictor") is not True:
            raise M0Error(f"M0 column is not predictor=true in F02 schema: {column}")
    if IDENTITY_COLUMNS & set(MATERIALIZED_COLUMNS):
        raise M0Error("identity/provenance column entered M0 feature contract")
    bad = [
        column for column in MATERIALIZED_COLUMNS
        if any(token in column.casefold() for token in FORBIDDEN_MODEL_TOKENS)
    ]
    if bad:
        raise M0Error(f"forbidden sportsbook/market token in M0 model matrix: {bad}")

    return {
        "schema": schema,
        "manifest": manifest,
        "target_manifest": target_manifest,
        "summary": summary,
    }


def load_modeling_table(f02_dir: Path) -> pd.DataFrame:
    validate_f02_identity(f02_dir)
    path = f02_dir / "winner_modeling_table.parquet"
    if not path.exists():
        raise M0Error(f"missing F02 target table: {path}")
    frame = pd.read_parquet(path)
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="raise")
    return frame.sort_values(["event_date", "event_id", "fight_id"]).reset_index(drop=True)


def primary_population(frame: pd.DataFrame) -> pd.DataFrame:
    mask = (
        frame["promotion"].eq("UFC")
        & frame["binary_winner_eligible"].eq(True)
        & frame["fighter_1_win"].notna()
        & frame["event_date"].ge(MODEL_ERA_START)
    )
    out = frame.loc[mask].copy()
    if out.empty:
        raise M0Error("primary UFC modeling population is empty")
    if not out["fighter_1_win"].isin([True, False]).all():
        raise M0Error("primary target contains non-binary values")
    return out


def fold_frames(population: pd.DataFrame, validation_year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = population[
        (population["event_date"].dt.year >= MODEL_ERA_START.year)
        & (population["event_date"].dt.year < validation_year)
    ].copy()
    valid = population[population["event_date"].dt.year == validation_year].copy()
    if train.empty or valid.empty:
        raise M0Error(f"empty train/validation fold for {validation_year}")
    if train["event_date"].max() >= valid["event_date"].min():
        raise M0Error(f"chronological overlap/leakage in fold {validation_year}")
    if set(train["fight_id"]) & set(valid["fight_id"]):
        raise M0Error(f"fight overlap in fold {validation_year}")
    return train, valid


def empirical_experience_probability(train: pd.DataFrame, valid: pd.DataFrame) -> np.ndarray:
    f1_col = PAIR_SPECS[0][1]
    f2_col = PAIR_SPECS[0][2]
    unequal = train[f1_col] != train[f2_col]
    if not unequal.any():
        p_more = 0.5
    else:
        rows = train.loc[unequal]
        f1_more = rows[f1_col] > rows[f2_col]
        y = rows["fighter_1_win"].astype(int)
        more_wins = np.where(f1_more.to_numpy(), y.to_numpy(), 1 - y.to_numpy())
        p_more = float((more_wins.sum() + 1.0) / (len(more_wins) + 2.0))

    a = valid[f1_col].to_numpy()
    b = valid[f2_col].to_numpy()
    return np.where(a > b, p_more, np.where(a < b, 1.0 - p_more, 0.5)).astype(float)


def metric_bundle(target: Iterable[int | bool], prob: Iterable[float]) -> dict[str, float | int | None]:
    y = np.asarray(list(target), dtype=int)
    p = np.clip(np.asarray(list(prob), dtype=float), 1e-12, 1 - 1e-12)
    if len(y) != len(p):
        raise M0Error("metric target/probability length mismatch")
    auc: float | None
    try:
        auc = float(roc_auc_score(y, p))
    except ValueError:
        auc = None
    return {
        "rows": int(len(y)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "accuracy": float(accuracy_score(y, p >= 0.5)),
        "auc": auc,
    }


def calibration_table(target: pd.Series, probability: pd.Series) -> tuple[list[dict[str, Any]], float]:
    edges = [0.0, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 1.0]
    labels = [f"{edges[i]:.2f}-{edges[i+1]:.2f}" for i in range(len(edges) - 1)]
    bins = pd.cut(probability, bins=edges, labels=labels, include_lowest=True, right=True)
    rows: list[dict[str, Any]] = []
    ece = 0.0
    total = len(target)
    for label in labels:
        mask = bins == label
        n = int(mask.sum())
        if n == 0:
            continue
        mean_p = float(probability[mask].mean())
        actual = float(target[mask].astype(int).mean())
        ece += (n / total) * abs(mean_p - actual)
        rows.append({
            "bin": label,
            "rows": n,
            "mean_predicted": mean_p,
            "actual_win_rate": actual,
        })
    return rows, float(ece)


def history_depth_slice(frame: pd.DataFrame) -> pd.Series:
    a = frame[PAIR_SPECS[0][1]]
    b = frame[PAIR_SPECS[0][2]]
    return pd.Series(
        np.where(
            (a == 0) | (b == 0),
            "zero_history",
            np.where(np.minimum(a, b) < 3, "sparse_history", "established_history"),
        ),
        index=frame.index,
    )


def _slice_metrics(oof: pd.DataFrame, mask: pd.Series) -> dict[str, Any] | None:
    subset = oof.loc[mask]
    if len(subset) < 30:
        return None
    return metric_bundle(subset["target"], subset["logistic_probability"])


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


def swap_pair_columns(frame: pd.DataFrame) -> pd.DataFrame:
    swapped = frame.copy()
    for _, f1_col, f2_col in PAIR_SPECS:
        swapped[f1_col] = frame[f2_col].to_numpy()
        swapped[f2_col] = frame[f1_col].to_numpy()
    return swapped


def orientation_error(model: M0Logistic, frame: pd.DataFrame) -> float:
    original = model.predict_proba(frame)
    swapped = model.predict_proba(swap_pair_columns(frame))
    return float(np.max(np.abs(original + swapped - 1.0)))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def oof_logical_hash(oof: pd.DataFrame) -> str:
    digest = sha256()
    columns = (
        "fight_id", "event_date", "fold_id", "target",
        "naive_probability", "empirical_probability", "logistic_probability",
    )
    ordered = oof.sort_values(["event_date", "fight_id"])
    for row in ordered.loc[:, columns].itertuples(index=False, name=None):
        payload = list(row)
        payload[1] = str(payload[1])
        digest.update(canonical_json(payload).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def verdict(aggregate: dict[str, dict[str, Any]], fold_rows: list[dict[str, Any]]) -> str:
    naive = aggregate["naive"]
    empirical = aggregate["empirical"]
    logistic = aggregate["logistic"]
    stable_folds = sum(
        1 for row in fold_rows
        if row["logistic"]["log_loss"] < row["naive"]["log_loss"]
        and row["logistic"]["brier"] < row["naive"]["brier"]
    )
    fold_count = len(fold_rows)
    confirmed = (
        naive["log_loss"] - logistic["log_loss"] >= 0.01
        and naive["brier"] - logistic["brier"] >= 0.005
        and logistic["log_loss"] < empirical["log_loss"]
        and logistic["brier"] < empirical["brier"]
        and stable_folds >= int(np.ceil((2.0 / 3.0) * fold_count))
    )
    if confirmed:
        return "M0_SIGNAL_CONFIRMED"
    weak = (
        logistic["log_loss"] < naive["log_loss"]
        and logistic["brier"] < naive["brier"]
        and stable_folds >= int(np.ceil(0.5 * fold_count))
    )
    if weak:
        return "M0_SIGNAL_WEAK_BUT_PRESENT"
    return "M0_SIGNAL_NOT_CONFIRMED"


def run_validation(f02_dir: Path, output_dir: Path) -> dict[str, Any]:
    frame = load_modeling_table(f02_dir)
    total_f02_rows = int(len(frame))
    ufc_rows = int(frame["promotion"].eq("UFC").sum())
    binary_ufc = int((frame["promotion"].eq("UFC") & frame["binary_winner_eligible"].eq(True)).sum())
    population = primary_population(frame)

    fold_results: list[dict[str, Any]] = []
    coefficient_rows: list[dict[str, Any]] = []
    oof_parts: list[pd.DataFrame] = []

    for year in VALIDATION_YEARS:
        train, valid = fold_frames(population, year)
        y_train = train["fighter_1_win"].astype(int)
        y_valid = valid["fighter_1_win"].astype(int)

        naive = np.full(len(valid), 0.5, dtype=float)
        empirical = empirical_experience_probability(train, valid)
        logistic_model = M0Logistic.fit(train, y_train)
        logistic = logistic_model.predict_proba(valid)

        swap_error = orientation_error(logistic_model, valid)
        if swap_error > 1e-10:
            raise M0Error(f"orientation invariance failed for {year}: {swap_error}")

        fold_results.append({
            "fold_id": str(year),
            "train_start": str(train["event_date"].min().date()),
            "train_end": str(train["event_date"].max().date()),
            "validation_start": str(valid["event_date"].min().date()),
            "validation_end": str(valid["event_date"].max().date()),
            "train_rows": int(len(train)),
            "validation_rows": int(len(valid)),
            "naive": metric_bundle(y_valid, naive),
            "empirical": metric_bundle(y_valid, empirical),
            "logistic": metric_bundle(y_valid, logistic),
            "orientation_max_abs_error": swap_error,
        })
        coefficient_rows.append({
            "fold_id": str(year),
            "coefficients": logistic_model.coefficient_map(),
        })

        part = pd.DataFrame({
            "fight_id": valid["fight_id"].to_numpy(),
            "event_date": valid["event_date"].dt.date.astype(str).to_numpy(),
            "fold_id": str(year),
            "target": y_valid.to_numpy(),
            "naive_probability": naive,
            "empirical_probability": empirical,
            "logistic_probability": logistic,
            "scheduled_rounds": valid["scheduled_rounds"].to_numpy(),
            "title_bout": valid["ctx__title_bout"].to_numpy(),
            "weight_class": valid["ctx__weight_class"].to_numpy(),
        })
        part["history_depth"] = history_depth_slice(valid).to_numpy()
        oof_parts.append(part)

    oof = pd.concat(oof_parts, ignore_index=True)
    if oof["fight_id"].duplicated().any():
        raise M0Error("OOF prediction fight_id is not unique")

    aggregate = {
        "naive": metric_bundle(oof["target"], oof["naive_probability"]),
        "empirical": metric_bundle(oof["target"], oof["empirical_probability"]),
        "logistic": metric_bundle(oof["target"], oof["logistic_probability"]),
    }
    calibration, ece = calibration_table(oof["target"], oof["logistic_probability"])

    coefficient_names = SymmetricPairProjector().output_names
    stability: dict[str, Any] = {}
    for name in coefficient_names:
        values = [row["coefficients"][name] for row in coefficient_rows]
        nonzero = [np.sign(value) for value in values if abs(value) > 1e-12]
        stability[name] = {
            "mean": float(np.mean(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "positive_folds": int(sum(value > 0 for value in values)),
            "negative_folds": int(sum(value < 0 for value in values)),
            "zero_folds": int(sum(abs(value) <= 1e-12 for value in values)),
            "direction_consistent": bool(len(set(nonzero)) <= 1) if nonzero else True,
        }

    logical_hash = oof_logical_hash(oof)
    result = {
        "status": "M0_EMPIRICAL_WINNER_BASELINE_V1_COMPLETE",
        "dataset": {
            "total_f02_rows": total_f02_rows,
            "ufc_rows": ufc_rows,
            "binary_eligible_ufc_rows": binary_ufc,
            "modeling_era_rows": int(len(population)),
            "modeling_era_start": str(MODEL_ERA_START.date()),
            "fighter_1_win_rate_modeling_era": float(population["fighter_1_win"].astype(int).mean()),
            "by_year": {
                str(year): int(count)
                for year, count in population.groupby(population["event_date"].dt.year).size().items()
            },
        },
        "feature_contract": {
            "materialized_columns": list(MATERIALIZED_COLUMNS),
            "source_column_count": len(MATERIALIZED_COLUMNS),
            "projected_numeric_dimensions": len(coefficient_names),
            "projected_feature_names": coefficient_names,
            "preprocessing": "training-fold pooled median by fighter-pair concept; antisymmetric value and missingness differences; StandardScaler; no intercept",
        },
        "folds": fold_results,
        "aggregate": aggregate,
        "calibration": {
            "expected_calibration_error": ece,
            "bins": calibration,
        },
        "slices": slice_report(oof),
        "coefficient_stability": stability,
        "orientation": {
            "overall_fighter_1_win_rate": float(frame.loc[
                frame["promotion"].eq("UFC") & frame["binary_winner_eligible"].eq(True),
                "fighter_1_win"
            ].astype(int).mean()),
            "max_fold_swap_probability_error": float(max(row["orientation_max_abs_error"] for row in fold_results)),
        },
        "oof": {
            "rows": int(len(oof)),
            "logical_sha256": logical_hash,
            "columns": [
                "fight_id", "event_date", "fold_id", "target",
                "naive_probability", "empirical_probability", "logistic_probability",
            ],
        },
        "verdict": verdict(aggregate, fold_results),
        "limitations": [
            "M0 is validation only; no production model is created.",
            "The compact subset intentionally excludes the broader F02 surface.",
            "2026 is a partial latest-year validation fold as represented in frozen F02.",
            "External-history target slicing is not reconstructed because F02 does not carry that row-level flag in the predictor table.",
            "No sportsbook or market comparison is part of M0.",
        ],
        "self_review": {
            "question": "Did M0 remain simple enough that poor performance would be interpretable?",
            "answer": "YES",
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "m0_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    oof.to_parquet(output_dir / "m0_oof_predictions.parquet", index=False)
    (output_dir / "m0_coefficients.json").write_text(
        json.dumps(coefficient_rows, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result
