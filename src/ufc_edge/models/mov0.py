"""Frozen MOV0 STANDARD_FINISH probability experiment."""
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
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ERA_START = pd.Timestamp("2015-01-01")
OUTER_YEARS = tuple(range(2018, 2027))
C_GRID = (0.03, 0.1, 0.3, 1.0)
SEED = 17
EXPECTED_OOF_N = 4260
EXPECTED_MODERN_N = 5658
EXPECTED_MODERN_POSITIVE = 2822
EXPECTED_FIRST_TRAIN_N = 1398
EXPECTED_F02_LOGICAL = "2d1a367416e105ed6fe546eb8590ae7b555dd044304ad0ba40c7945420599ba0"
EXPECTED_F02_TABLE = "d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580"
EXPECTED_TERRAIN_PHYSICAL = "8b59c09e103997e4c6d6311608620e7178962aac0cdf807dfa9d1740c7aa6d97"
DIRECTIONAL = (
    "mx__knockdown_creation_vs_vulnerability__f1_vs_f2__career__raw",
    "mx__knockdown_creation_vs_vulnerability__f2_vs_f1__career__raw",
)
TERRAIN_COLUMNS = (
    "experience_bucket",
    "layoff_bucket",
    "scheduled_duration_bucket",
    "title_status",
    "weight_class",
    "completeness_tier",
    "striking_environment",
    "grappling_environment",
    "joint_mov_environment",
)
WATCHPOINTS = {"HIGH_MISSINGNESS", "3_ROUND", "5_ROUND", "STRIKE_TWO_SIDED", "GRAPPLE_TWO_SIDED"}


class MOV0Error(ValueError):
    """Frozen MOV0 contract violation."""


def file_sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise MOV0Error(f"{path} must contain an object")
    return value


def load_contracts(contract_dir: Path) -> dict[str, dict[str, Any]]:
    names = (
        "target_contract_v1.json",
        "feature_surface_v1.json",
        "model_contract_v1.json",
        "validation_plan_v1.json",
        "acceptance_framework_v1.json",
    )
    return {name: load_json(contract_dir / name) for name in names}


def validate_contracts(contracts: dict[str, dict[str, Any]]) -> None:
    model = contracts["model_contract_v1.json"]["specification"]
    chronology = contracts["validation_plan_v1.json"]["chronology"]
    target = contracts["target_contract_v1.json"]
    if tuple(float(x) for x in model["C_grid"]) != C_GRID:
        raise MOV0Error("frozen C grid changed")
    expected = {
        "penalty": "l2",
        "solver": "lbfgs",
        "max_iter": 3000,
        "tol": 1e-4,
        "fit_intercept": True,
        "class_weight": None,
        "random_seed": 17,
    }
    for key, value in expected.items():
        if model.get(key) != value:
            raise MOV0Error(f"model contract changed: {key}")
    if model.get("selection_objective") != "concatenated inner chronological log loss only":
        raise MOV0Error("selection objective changed")
    if tuple(chronology["governed_oof_evaluation_years"]) != OUTER_YEARS:
        raise MOV0Error("outer years changed")
    if chronology["modeling_era_start"] != "2015-01-01" or chronology["pre_2015_rows_allowed"]:
        raise MOV0Error("2015+ era gate changed")
    if target["governed_evaluation_population"]["exact_counts"]["TOTAL"] != EXPECTED_OOF_N:
        raise MOV0Error("frozen OOF N changed")
    if target["governed_modern_label_population"]["exact_counts"]["TOTAL"] != EXPECTED_MODERN_N:
        raise MOV0Error("frozen modern population N changed")


def verify_f02(f02_dir: Path) -> None:
    summary = load_json(f02_dir / "summary.json")
    logical = summary.get("predictor_logical_sha256")
    physical = file_sha256(f02_dir / "winner_modeling_table.parquet")
    if logical != EXPECTED_F02_LOGICAL:
        raise MOV0Error(f"corrected F02 logical hash mismatch: {logical}")
    if physical != EXPECTED_F02_TABLE:
        raise MOV0Error(f"corrected F02 table hash mismatch: {physical}")


def standard_finish_label(result: Any, method: Any) -> int | None:
    if result == "win_loss" and method in {"KO_TKO", "SUBMISSION"}:
        return 1
    if result in {"win_loss", "draw"} and method == "DECISION":
        return 0
    return None


def attach_target(predictors: pd.DataFrame, canonical_fights: Path) -> pd.DataFrame:
    fights = pd.read_csv(canonical_fights, usecols=["fight_id", "result", "method"])
    if fights["fight_id"].duplicated().any():
        raise MOV0Error("duplicate fight_id in canonical fights")
    joined = predictors.merge(
        fights,
        on="fight_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if not joined["_merge"].eq("both").all():
        raise MOV0Error("F02 fight missing canonical target row")
    joined["target"] = [
        standard_finish_label(result, method)
        for result, method in zip(joined["result"], joined["method"])
    ]
    joined = joined[joined["target"].notna()].copy()
    joined["target"] = joined["target"].astype(int)
    return joined.drop(columns=["_merge"])


def assert_modern(frame: pd.DataFrame, context: str) -> None:
    if "event_date" not in frame:
        raise MOV0Error(f"{context}: event_date required")
    dates = pd.to_datetime(frame["event_date"], errors="raise")
    if dates.lt(ERA_START).any():
        raise MOV0Error(f"{context}: pre-2015 row prohibited")


def build_population(f02_dir: Path, canonical_fights: Path) -> pd.DataFrame:
    verify_f02(f02_dir)
    frame = pd.read_parquet(f02_dir / "winner_modeling_table.parquet")
    required = {"fight_id", "event_id", "event_date", "promotion"}
    if not required.issubset(frame.columns):
        raise MOV0Error(f"F02 missing identity columns: {sorted(required - set(frame.columns))}")
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="raise")
    frame = frame[frame["promotion"].eq("UFC") & frame["event_date"].ge(ERA_START)].copy()
    assert_modern(frame, "predictor population")
    if frame["fight_id"].duplicated().any():
        raise MOV0Error("duplicate F02 fight_id")
    frame = frame.sort_values(["event_date", "event_id", "fight_id"]).reset_index(drop=True)
    population = attach_target(frame, canonical_fights)
    if len(population) != EXPECTED_MODERN_N or int(population["target"].sum()) != EXPECTED_MODERN_POSITIVE:
        raise MOV0Error(
            f"modern target population mismatch N={len(population)} positives={int(population['target'].sum())}"
        )
    return population


def surface_columns(surface_contract: dict[str, Any], name: str) -> list[str]:
    try:
        return list(surface_contract["surfaces"][name]["literal_f02_columns"])
    except KeyError as exc:
        raise MOV0Error(f"unknown surface {name}") from exc


def validate_requested_columns(
    surface_contract: dict[str, Any], name: str, requested: Iterable[str]
) -> None:
    frozen = surface_columns(surface_contract, name)
    got = list(requested)
    if got != frozen:
        extra = sorted(set(got) - set(frozen))
        missing = sorted(set(frozen) - set(got))
        raise MOV0Error(f"{name} feature allowlist mismatch extra={extra} missing={missing}")


def _mode(series: pd.Series) -> Any:
    values = series.dropna().mode()
    if values.empty:
        raise MOV0Error("categorical training column is entirely missing")
    return values.iloc[0]


def _bool_array(series: pd.Series, fill: Any) -> np.ndarray:
    values = series.fillna(fill)
    if pd.api.types.is_bool_dtype(values):
        return values.astype(float).to_numpy().reshape(-1, 1)
    mapping = {
        "true": 1.0,
        "false": 0.0,
        "1": 1.0,
        "0": 0.0,
        "yes": 1.0,
        "no": 0.0,
    }
    mapped = values.astype(str).str.strip().str.lower().map(mapping)
    if mapped.isna().any():
        bad = sorted(values[mapped.isna()].astype(str).unique().tolist())
        raise MOV0Error(f"unrecognized title_bout values: {bad}")
    return mapped.to_numpy(float).reshape(-1, 1)


@dataclass
class SurfacePreprocessor:
    requested: list[str]
    pair_specs: list[tuple[str, str, str]]
    singleton_numeric: list[str]
    pair_medians: dict[str, float]
    singleton_medians: dict[str, float]
    title_fill: Any
    weight_fill: Any
    encoder: OneHotEncoder
    scaler: StandardScaler
    numeric_names: list[str]

    @classmethod
    def fit(
        cls,
        train: pd.DataFrame,
        surface_contract: dict[str, Any],
        surface_name: str,
    ) -> "SurfacePreprocessor":
        assert_modern(train, f"{surface_name} preprocessing fit")
        requested = surface_columns(surface_contract, surface_name)
        validate_requested_columns(surface_contract, surface_name, requested)
        absent = [column for column in requested if column not in train.columns]
        if absent:
            raise MOV0Error(f"{surface_name} missing frozen F02 columns: {absent}")

        pair_specs: list[tuple[str, str, str]] = []
        seen: set[str] = set()
        for column in requested:
            if not column.startswith("f1__") or column in seen:
                continue
            mate = "f2__" + column[4:]
            if mate not in requested:
                raise MOV0Error(f"unpaired fighter feature: {column}")
            key = column[4:]
            pair_specs.append((key, column, mate))
            seen.update((column, mate))
        if all(column in requested for column in DIRECTIONAL):
            pair_specs.append(("directional_knockdown_matchup", DIRECTIONAL[0], DIRECTIONAL[1]))
            seen.update(DIRECTIONAL)

        singleton_numeric = [column for column in requested if column == "scheduled_rounds"]
        allowed_special = {"ctx__title_bout", "ctx__weight_class"}
        uncovered = set(requested) - seen - set(singleton_numeric) - allowed_special
        if uncovered:
            raise MOV0Error(f"unapproved or unhandled model columns: {sorted(uncovered)}")

        pair_medians: dict[str, float] = {}
        numeric_arrays: list[np.ndarray] = []
        numeric_names: list[str] = []
        for key, a_column, b_column in pair_specs:
            a = pd.to_numeric(train[a_column], errors="coerce")
            b = pd.to_numeric(train[b_column], errors="coerce")
            median = pd.concat([a, b], ignore_index=True).median(skipna=True)
            if pd.isna(median):
                raise MOV0Error(f"training pair entirely missing: {key}")
            median = float(median)
            pair_medians[key] = median
            aa = a.fillna(median).to_numpy(float)
            bb = b.fillna(median).to_numpy(float)
            numeric_arrays.extend([(aa + bb) / 2.0, np.abs(aa - bb)])
            numeric_names.extend([f"{key}::mean", f"{key}::absdiff"])

        singleton_medians: dict[str, float] = {}
        for column in singleton_numeric:
            values = pd.to_numeric(train[column], errors="coerce")
            median = values.median(skipna=True)
            if pd.isna(median):
                raise MOV0Error(f"training singleton entirely missing: {column}")
            singleton_medians[column] = float(median)
            numeric_arrays.append(values.fillna(median).to_numpy(float))
            numeric_names.append(column)

        if not numeric_arrays:
            raise MOV0Error(f"{surface_name} has no numeric model features")
        numeric = np.column_stack(numeric_arrays)
        scaler = StandardScaler().fit(numeric)

        title_fill = _mode(train["ctx__title_bout"]) if "ctx__title_bout" in requested else False
        weight_fill = _mode(train["ctx__weight_class"]) if "ctx__weight_class" in requested else "__NONE__"
        if "ctx__weight_class" in requested:
            weights = (
                train["ctx__weight_class"]
                .fillna(weight_fill)
                .astype(str)
                .to_numpy()
                .reshape(-1, 1)
            )
            encoder = OneHotEncoder(
                handle_unknown="ignore", drop=None, sparse_output=False
            ).fit(weights)
        else:
            encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(
                np.array([["__NONE__"]])
            )
        return cls(
            requested,
            pair_specs,
            singleton_numeric,
            pair_medians,
            singleton_medians,
            title_fill,
            weight_fill,
            encoder,
            scaler,
            numeric_names,
        )

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        arrays: list[np.ndarray] = []
        for key, a_column, b_column in self.pair_specs:
            median = self.pair_medians[key]
            a = pd.to_numeric(frame[a_column], errors="coerce").fillna(median).to_numpy(float)
            b = pd.to_numeric(frame[b_column], errors="coerce").fillna(median).to_numpy(float)
            arrays.extend([(a + b) / 2.0, np.abs(a - b)])
        for column in self.singleton_numeric:
            median = self.singleton_medians[column]
            arrays.append(
                pd.to_numeric(frame[column], errors="coerce")
                .fillna(median)
                .to_numpy(float)
            )
        numeric = self.scaler.transform(np.column_stack(arrays))
        blocks = [numeric]
        if "ctx__title_bout" in self.requested:
            blocks.append(_bool_array(frame["ctx__title_bout"], self.title_fill))
        if "ctx__weight_class" in self.requested:
            weights = (
                frame["ctx__weight_class"]
                .fillna(self.weight_fill)
                .astype(str)
                .to_numpy()
                .reshape(-1, 1)
            )
            blocks.append(self.encoder.transform(weights))
        return np.column_stack(blocks)

    def metadata(self) -> dict[str, Any]:
        return {
            "pair_medians": self.pair_medians,
            "singleton_medians": self.singleton_medians,
            "title_fill": str(self.title_fill),
            "weight_fill": str(self.weight_fill),
            "weight_categories": [str(value) for value in self.encoder.categories_[0]],
            "numeric_names": self.numeric_names,
            "scaler_mean": self.scaler.mean_.tolist(),
            "scaler_scale": self.scaler.scale_.tolist(),
        }


@dataclass
class FittedSurface:
    preprocessor: SurfacePreprocessor
    model: LogisticRegression

    @classmethod
    def fit(
        cls,
        train: pd.DataFrame,
        surface_contract: dict[str, Any],
        surface_name: str,
        C: float,
    ) -> "FittedSurface":
        assert_modern(train, f"{surface_name} model fit")
        preprocessor = SurfacePreprocessor.fit(train, surface_contract, surface_name)
        x = preprocessor.transform(train)
        y = train["target"].to_numpy(int)
        model = LogisticRegression(
            penalty="l2",
            solver="lbfgs",
            C=float(C),
            fit_intercept=True,
            class_weight=None,
            max_iter=3000,
            tol=1e-4,
            random_state=SEED,
        ).fit(x, y)
        return cls(preprocessor, model)

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(self.preprocessor.transform(frame))[:, 1]


def swap_fighters(
    frame: pd.DataFrame,
    surface_contract: dict[str, Any],
    surface_name: str,
) -> pd.DataFrame:
    out = frame.copy()
    requested = surface_columns(surface_contract, surface_name)
    for column in requested:
        if column.startswith("f1__"):
            mate = "f2__" + column[4:]
            if mate in requested:
                out[column] = frame[mate].copy()
                out[mate] = frame[column].copy()
    if all(column in requested for column in DIRECTIONAL):
        out[DIRECTIONAL[0]] = frame[DIRECTIONAL[1]].copy()
        out[DIRECTIONAL[1]] = frame[DIRECTIONAL[0]].copy()
    return out


def order_invariance_error(
    model: FittedSurface,
    frame: pd.DataFrame,
    surface_contract: dict[str, Any],
    surface_name: str,
) -> float:
    original = model.predict(frame)
    swapped = model.predict(swap_fighters(frame, surface_contract, surface_name))
    return float(np.max(np.abs(original - swapped)))


def fold_frames(population: pd.DataFrame, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    assert_modern(population, f"outer fold {year} population")
    train = population[population["event_date"].dt.year < year].copy()
    valid = population[population["event_date"].dt.year == year].copy()
    if train.empty or valid.empty:
        raise MOV0Error(f"empty outer fold {year}")
    if train["event_date"].max() >= valid["event_date"].min():
        raise MOV0Error(f"chronology overlap {year}")
    if set(train["fight_id"]) & set(valid["fight_id"]):
        raise MOV0Error(f"fight overlap {year}")
    return train, valid


def inner_years(outer_year: int) -> tuple[int, int]:
    return outer_year - 2, outer_year - 1


def b0_probability(train: pd.DataFrame, n: int) -> np.ndarray:
    assert_modern(train, "B0 training prevalence")
    return np.repeat(float(train["target"].mean()), n)


def select_C(
    population: pd.DataFrame,
    outer_year: int,
    surface_contract: dict[str, Any],
    surface_name: str,
) -> tuple[float, list[dict[str, Any]]]:
    assert_modern(population, f"{surface_name} inner selection population")
    scores: list[dict[str, Any]] = []
    best_C = C_GRID[0]
    best_score = float("inf")
    for C in C_GRID:
        targets: list[int] = []
        probabilities: list[float] = []
        fold_rows: list[dict[str, Any]] = []
        for year in inner_years(outer_year):
            train = population[population["event_date"].dt.year < year].copy()
            valid = population[population["event_date"].dt.year == year].copy()
            if train.empty or valid.empty:
                raise MOV0Error(f"empty inner fold {year} for outer {outer_year}")
            fitted = FittedSurface.fit(train, surface_contract, surface_name, C)
            pred = fitted.predict(valid)
            targets.extend(valid["target"].astype(int).tolist())
            probabilities.extend(pred.tolist())
            fold_rows.append(
                {
                    "year": year,
                    "train_n": len(train),
                    "validation_n": len(valid),
                    "train_max_date": str(train["event_date"].max().date()),
                    "validation_min_date": str(valid["event_date"].min().date()),
                }
            )
        score = float(
            log_loss(
                np.asarray(targets),
                np.clip(np.asarray(probabilities), 1e-15, 1 - 1e-15),
                labels=[0, 1],
            )
        )
        scores.append({"C": C, "concatenated_log_loss": score, "folds": fold_rows})
        if score < best_score:
            best_score = score
            best_C = C
    return best_C, scores


def deterministic_tie_break(scores: list[float]) -> float:
    if len(scores) != len(C_GRID):
        raise MOV0Error("score vector must match frozen C grid")
    best = 0
    for index in range(1, len(scores)):
        if scores[index] < scores[best]:
            best = index
    return C_GRID[best]


def metric_bundle(target: Iterable[int], probability: Iterable[float]) -> dict[str, Any]:
    y = np.asarray(list(target), dtype=int)
    p = np.asarray(list(probability), dtype=float)
    safe = np.clip(p, 1e-15, 1 - 1e-15)
    auc = None if len(np.unique(y)) < 2 else float(roc_auc_score(y, p))
    return {
        "N": int(len(y)),
        "log_loss": float(log_loss(y, safe, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "roc_auc": auc,
        "prevalence": float(y.mean()),
        "mean_prediction": float(p.mean()),
        "accuracy_p_ge_0_5": float(accuracy_score(y, p >= 0.5)),
    }


def calibration_intercept_slope(
    target: np.ndarray, probability: np.ndarray
) -> tuple[float | None, float | None]:
    y = np.asarray(target, dtype=float)
    p = np.clip(np.asarray(probability, dtype=float), 1e-6, 1 - 1e-6)
    x = np.log(p / (1 - p))
    if len(np.unique(y)) < 2 or float(np.ptp(x)) <= 1e-15:
        return None, None
    X = np.c_[np.ones(len(x)), x]
    beta = np.zeros(2)
    for _ in range(100):
        eta = np.clip(X @ beta, -30, 30)
        q = 1.0 / (1.0 + np.exp(-eta))
        w = np.clip(q * (1 - q), 1e-10, None)
        hessian = X.T @ (X * w[:, None])
        score = X.T @ (y - q)
        try:
            step = np.linalg.solve(hessian, score)
        except np.linalg.LinAlgError:
            return None, None
        beta += step
        if float(np.max(np.abs(step))) < 1e-10:
            break
    return float(beta[0]), float(beta[1])


def reliability(
    target: np.ndarray, probability: np.ndarray
) -> tuple[list[dict[str, Any]], float]:
    y = np.asarray(target, dtype=int)
    p = np.asarray(probability, dtype=float)
    rows: list[dict[str, Any]] = []
    total = len(y)
    ece = 0.0
    indexes = np.minimum((np.clip(p, 0, 1) * 10).astype(int), 9)
    for bucket in range(10):
        mask = indexes == bucket
        n = int(mask.sum())
        close = "]" if bucket == 9 else ")"
        row: dict[str, Any] = {
            "bin": f"[{bucket / 10:.1f},{(bucket + 1) / 10:.1f}{close}",
            "N": n,
        }
        if n:
            mean_prediction = float(p[mask].mean())
            observed = float(y[mask].mean())
            gap = observed - mean_prediction
            row.update(
                {
                    "mean_prediction": mean_prediction,
                    "observed_finish_rate": observed,
                    "calibration_gap": gap,
                }
            )
            ece += n / total * abs(gap)
        else:
            row.update(
                {
                    "mean_prediction": None,
                    "observed_finish_rate": None,
                    "calibration_gap": None,
                }
            )
        rows.append(row)
    return rows, float(ece)


def full_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    y = frame["target"].to_numpy(int)
    p = frame["probability"].to_numpy(float)
    out = metric_bundle(y, p)
    intercept, slope = calibration_intercept_slope(y, p)
    _, ece = reliability(y, p)
    out.update(
        {
            "calibration_intercept": intercept,
            "calibration_slope": slope,
            "ece_10_fixed": ece,
        }
    )
    return out


def paired_loss_delta(candidate: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    a = candidate[["fight_id", "event_id", "target", "year", "probability"]].rename(
        columns={"probability": "candidate"}
    )
    b = baseline[["fight_id", "probability"]].rename(columns={"probability": "baseline"})
    data = a.merge(b, on="fight_id", validate="one_to_one")
    y = data["target"].to_numpy(int)
    pc = np.clip(data["candidate"].to_numpy(float), 1e-15, 1 - 1e-15)
    pb = np.clip(data["baseline"].to_numpy(float), 1e-15, 1 - 1e-15)
    candidate_loss = -(y * np.log(pc) + (1 - y) * np.log(1 - pc))
    baseline_loss = -(y * np.log(pb) + (1 - y) * np.log(1 - pb))
    data["delta"] = candidate_loss - baseline_loss
    return data


def comparison(candidate: pd.DataFrame, baseline: pd.DataFrame) -> dict[str, Any]:
    data = paired_loss_delta(candidate, baseline)
    yearly: list[dict[str, Any]] = []
    for year, group in data.groupby("year"):
        yearly.append(
            {
                "year": int(year),
                "N": len(group),
                "log_loss_delta": float(group["delta"].mean()),
                "summed_loss_delta": float(group["delta"].sum()),
            }
        )
    deltas = np.asarray([row["log_loss_delta"] for row in yearly])
    tolerance = 1e-12
    total_sum = float(data["delta"].sum())
    dominance = None
    if total_sum < 0:
        strongest_sum = min(row["summed_loss_delta"] for row in yearly)
        dominance = float(100 * abs(strongest_sum) / abs(total_sum))
    return {
        "aggregate_log_loss_delta": float(data["delta"].mean()),
        "per_year": yearly,
        "median_yearly_delta": float(np.median(deltas)),
        "better_years": int(np.sum(deltas < -tolerance)),
        "worse_years": int(np.sum(deltas > tolerance)),
        "tied_years": int(np.sum(np.abs(deltas) <= tolerance)),
        "strongest_favorable_year": min(yearly, key=lambda row: row["log_loss_delta"]),
        "strongest_unfavorable_year": max(yearly, key=lambda row: row["log_loss_delta"]),
        "single_strongest_favorable_year_percent_of_aggregate_gain": dominance,
    }


def paired_bootstrap(
    candidate: pd.DataFrame, baseline: pd.DataFrame, event_cluster: bool
) -> dict[str, Any]:
    data = paired_loss_delta(candidate, baseline)
    delta = data["delta"].to_numpy(float)
    rng = np.random.default_rng(SEED)
    replicates = np.empty(2000)
    if not event_cluster:
        for index in range(2000):
            sample = rng.integers(0, len(delta), len(delta))
            replicates[index] = float(np.mean(delta[sample]))
        kind = "fight_level_paired"
    else:
        event_values = data["event_id"].astype(str).to_numpy()
        events = pd.unique(event_values)
        groups = {event: np.flatnonzero(event_values == event) for event in events}
        for index in range(2000):
            sampled = rng.choice(events, size=len(events), replace=True)
            values = np.concatenate([delta[groups[event]] for event in sampled])
            replicates[index] = float(np.mean(values))
        kind = "event_cluster_paired"
    return {
        "kind": kind,
        "replicates": 2000,
        "seed": SEED,
        "point_estimate": float(delta.mean()),
        "ci95": [
            float(np.percentile(replicates, 2.5)),
            float(np.percentile(replicates, 97.5)),
        ],
    }


def sample_gate(n: int) -> str:
    if n >= 100:
        return "NORMAL"
    if n >= 50:
        return "MODERATE_UNCERTAINTY"
    if n >= 25:
        return "THIN_EXPLORATORY"
    return "INSUFFICIENT_SAMPLE"


def load_terrain_assignment(path: Path) -> pd.DataFrame:
    if file_sha256(path) != EXPECTED_TERRAIN_PHYSICAL:
        raise MOV0Error("frozen terrain physical hash mismatch")
    assignment = pd.read_csv(path)
    if assignment["fight_id"].duplicated().any():
        raise MOV0Error("duplicate terrain fight_id")
    return assignment


def join_terrain(oof: pd.DataFrame, assignment: pd.DataFrame) -> pd.DataFrame:
    merged = oof.merge(
        assignment,
        on="fight_id",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if not merged["_merge"].eq("both").all():
        raise MOV0Error("OOF fight missing from frozen terrain")
    return merged.drop(columns=["_merge"])


def terrain_report(
    oofs: dict[str, pd.DataFrame], assignment_path: Path
) -> dict[str, Any]:
    assignment = load_terrain_assignment(assignment_path)
    rows: list[dict[str, Any]] = []
    for model_surface, oof in oofs.items():
        merged = join_terrain(oof, assignment)
        for terrain_surface in TERRAIN_COLUMNS:
            for bucket, group in merged.groupby(terrain_surface, dropna=False):
                n = len(group)
                status = sample_gate(n)
                row: dict[str, Any] = {
                    "model_surface": model_surface,
                    "terrain_surface": terrain_surface,
                    "bucket": str(bucket),
                    "N": n,
                    "status": status,
                }
                if n >= 25:
                    row.update(metric_bundle(group["target"], group["probability"]))
                rows.append(row)
    watches = [row for row in rows if row["bucket"] in WATCHPOINTS]
    return {
        "terrain_regenerated": False,
        "assignment_sha256": file_sha256(assignment_path),
        "rows": rows,
        "watchpoints": watches,
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def run_experiment(
    f02_dir: Path,
    canonical_fights: Path,
    contract_dir: Path,
    terrain_assignment: Path,
    output_dir: Path,
) -> dict[str, Any]:
    contracts = load_contracts(contract_dir)
    validate_contracts(contracts)
    feature_surface = contracts["feature_surface_v1.json"]
    population = build_population(f02_dir, canonical_fights)
    output_dir.mkdir(parents=True, exist_ok=True)

    oofs: dict[str, pd.DataFrame] = {}
    fold_manifest: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    preprocessing_metadata: dict[str, Any] = {}
    invariance: dict[str, Any] = {}

    for surface_name in ("B0", "B1", "MOV0_MIN", "MOV0_FULL"):
        parts: list[pd.DataFrame] = []
        preprocessing_metadata[surface_name] = {}
        invariance[surface_name] = {}
        for year in OUTER_YEARS:
            train, valid = fold_frames(population, year)
            frozen_fold = next(
                row
                for row in contracts["validation_plan_v1.json"]["chronology"]["folds"]
                if row["outer_year"] == year
            )
            if len(train) != frozen_fold["outer_train_n"] or len(valid) != frozen_fold["outer_validation_n"]:
                raise MOV0Error(
                    f"frozen fold N mismatch for {year}: train={len(train)} valid={len(valid)}"
                )
            if surface_name == "B0":
                selected_C = None
                inner_scores: list[dict[str, Any]] = []
                probability = b0_probability(train, len(valid))
            else:
                selected_C, inner_scores = select_C(
                    population, year, feature_surface, surface_name
                )
                fitted = FittedSurface.fit(
                    train, feature_surface, surface_name, selected_C
                )
                probability = fitted.predict(valid)
                error = order_invariance_error(
                    fitted, valid, feature_surface, surface_name
                )
                if error > 1e-12:
                    raise MOV0Error(
                        f"fighter-order invariance failed {surface_name}/{year}: {error}"
                    )
                invariance[surface_name][str(year)] = error
                preprocessing_metadata[surface_name][str(year)] = {
                    "training_min_date": str(train["event_date"].min().date()),
                    "training_max_date": str(train["event_date"].max().date()),
                    "training_n": len(train),
                    "preprocessor": fitted.preprocessor.metadata(),
                }
                selected_rows.append(
                    {
                        "surface": surface_name,
                        "outer_year": year,
                        "selected_C": selected_C,
                        "inner_scores_json": json.dumps(inner_scores, sort_keys=True),
                    }
                )

            part = valid[["fight_id", "event_id", "event_date", "target"]].copy()
            part["year"] = year
            part["surface"] = surface_name
            part["selected_C"] = selected_C
            part["probability"] = probability
            parts.append(part)
            fold_manifest.append(
                {
                    "surface": surface_name,
                    "outer_year": year,
                    "train_n": len(train),
                    "validation_n": len(valid),
                    "train_min_date": str(train["event_date"].min().date()),
                    "train_max_date": str(train["event_date"].max().date()),
                    "validation_min_date": str(valid["event_date"].min().date()),
                    "validation_max_date": str(valid["event_date"].max().date()),
                    "inner_validation_years": list(inner_years(year)),
                }
            )

        oof = pd.concat(parts, ignore_index=True)
        if len(oof) != EXPECTED_OOF_N or oof["fight_id"].duplicated().any():
            raise MOV0Error(f"{surface_name} OOF identity or count failure")
        oofs[surface_name] = oof
        oof.to_csv(output_dir / f"oof_{surface_name}.csv", index=False)

    aggregate = {name: full_metrics(frame) for name, frame in oofs.items()}
    fold_metrics: list[dict[str, Any]] = []
    calibration: dict[str, Any] = {}
    for name, frame in oofs.items():
        reliability_rows, ece = reliability(
            frame["target"].to_numpy(int), frame["probability"].to_numpy(float)
        )
        calibration[name] = {
            "reliability": reliability_rows,
            "ece_10_fixed": ece,
            "calibration_intercept": aggregate[name]["calibration_intercept"],
            "calibration_slope": aggregate[name]["calibration_slope"],
        }
        for year, group in frame.groupby("year"):
            metrics = full_metrics(group)
            metrics.update({"surface": name, "year": int(year)})
            fold_metrics.append(metrics)

    comparisons: dict[str, Any] = {}
    bootstraps: dict[str, Any] = {}
    for candidate, baseline in (
        ("B1", "B0"),
        ("MOV0_MIN", "B1"),
        ("MOV0_FULL", "MOV0_MIN"),
    ):
        key = f"{candidate}_vs_{baseline}"
        comparisons[key] = comparison(oofs[candidate], oofs[baseline])
        bootstraps[key] = {
            "fight_level": paired_bootstrap(oofs[candidate], oofs[baseline], False),
            "event_cluster": paired_bootstrap(oofs[candidate], oofs[baseline], True),
        }

    terrain = terrain_report(oofs, terrain_assignment)

    write_json(
        output_dir / "execution_config.json",
        {
            "experiment": "MOV0_STANDARD_FINISH_PROBABILITY_V1",
            "seed": SEED,
            "C_grid": list(C_GRID),
            "outer_years": list(OUTER_YEARS),
            "modeling_era_start": "2015-01-01",
            "f02_logical_sha256": EXPECTED_F02_LOGICAL,
            "f02_table_sha256": EXPECTED_F02_TABLE,
            "terrain_assignment_sha256": EXPECTED_TERRAIN_PHYSICAL,
        },
    )
    write_json(output_dir / "fold_manifest.json", fold_manifest)
    pd.DataFrame(selected_rows).to_csv(
        output_dir / "selected_C_by_surface_year.csv", index=False
    )
    write_json(output_dir / "preprocessing_metadata.json", preprocessing_metadata)
    write_json(output_dir / "aggregate_metrics.json", aggregate)
    pd.DataFrame(fold_metrics).to_csv(output_dir / "fold_metrics.csv", index=False)
    write_json(output_dir / "calibration_reliability.json", calibration)
    write_json(output_dir / "comparisons.json", comparisons)
    write_json(output_dir / "bootstrap_report.json", bootstraps)
    write_json(output_dir / "validation_terrain_report.json", terrain)
    write_json(output_dir / "fighter_order_invariance.json", invariance)

    report = [
        "# MOV0 STANDARD_FINISH PROBABILITY V1 - FIRST FROZEN RUN",
        "",
        f"OOF N: {EXPECTED_OOF_N}",
        "",
        "## Aggregate metrics",
        "",
        "| Surface | Log loss | Brier | AUC | ECE | Cal intercept | Cal slope |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("B0", "B1", "MOV0_MIN", "MOV0_FULL"):
        metrics = aggregate[name]
        report.append(
            f"| {name} | {metrics['log_loss']:.9f} | {metrics['brier']:.9f} | "
            f"{metrics['roc_auc']:.9f} | {metrics['ece_10_fixed']:.9f} | "
            f"{metrics['calibration_intercept']:.6f} | {metrics['calibration_slope']:.6f} |"
        )
    report.extend(["", "## Primary comparisons", ""])
    for key, value in comparisons.items():
        report.append(
            f"- {key}: aggregate log-loss delta {value['aggregate_log_loss_delta']:.9f}; "
            f"yearly better/worse/tied {value['better_years']}/{value['worse_years']}/{value['tied_years']}; "
            f"median yearly delta {value['median_yearly_delta']:.9f}."
        )
    report.extend(
        [
            "",
            "Classification is assigned only after reviewing the complete frozen evidence package.",
            "",
            "No sportsbook odds, ROI or EV analysis, post-hoc feature changes, recalibration, MOV1 work, or merge was performed.",
        ]
    )
    (output_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    outputs: dict[str, str] = {}
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path.name not in {
            "manifest.json",
            "MOV0_STANDARD_FINISH_PROBABILITY_V1_RUN_COMPLETE.json",
        }:
            outputs[path.name] = file_sha256(path)
    write_json(
        output_dir / "manifest.json",
        {"status": "MOV0_FROZEN_RUN_ARTIFACT_MANIFEST_V1", "outputs": outputs},
    )
    class_balance = {
        "positive": int(oofs["B0"]["target"].sum()),
        "negative": int((1 - oofs["B0"]["target"]).sum()),
    }
    marker = {
        "status": "MOV0_STANDARD_FINISH_PROBABILITY_V1_RUN_COMPLETE",
        "classification": "PENDING_MASTER_PM_EVIDENCE_REVIEW",
        "oof_n": EXPECTED_OOF_N,
        "class_balance": class_balance,
        "market_data_used": False,
        "roi_ev_analyzed": False,
        "mov1_started": False,
        "merge_performed": False,
        "artifact_manifest_sha256": file_sha256(output_dir / "manifest.json"),
    }
    write_json(
        output_dir / "MOV0_STANDARD_FINISH_PROBABILITY_V1_RUN_COMPLETE.json",
        marker,
    )
    return {
        "aggregate": aggregate,
        "comparisons": comparisons,
        "bootstraps": bootstraps,
        "class_balance": class_balance,
        "invariance": invariance,
        "manifest_sha256": file_sha256(output_dir / "manifest.json"),
    }
