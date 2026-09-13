"""M1 broad regularized UFC winner model.

Market-blind, chronological, deterministic, orientation-safe, and built only
from the frozen governed F02 predictor surface. M0 remains a frozen benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

MODEL_ERA_START = pd.Timestamp("2010-01-01")
OUTER_YEARS = tuple(range(2015, 2027))
DEVELOPMENT_YEARS = tuple(range(2015, 2024))
CONFIRMATION_YEARS = (2024, 2025, 2026)
INNER_VALIDATION_YEARS = 2
RANDOM_SEED = 17

F02_IDENTITY = {
    "replay_schema_version": "1.0.1",
    "schema_sha256": "488c96eed4d86a75da8b763c879a65d6b85959393ec7b6c59f7051b0c03836a8",
    "predictor_logical_sha256": "ac55fd6fc1f19be7afac2007fccceb43b5c3f98327554d0c58fbe6cb0b164383",
    "predictor_manifest_sha256": "27b26736079bba7f5bc811bc96798f35ece36d54f1b0632cbd5e37f57ebd3c07",
    "target_contract_sha256": "fe34f7fd2b70611ec0602d9c9208debf8ec11d7eb8ea1adc0a4104ddb46ffd52",
    "target_logical_sha256": "02b735aabcb354fa16cd3800f72e5ccd504f5fb6dc9963510987c57438a44956",
}

M0_IDENTITY = {
    "rows": 5626,
    "logical_sha256": "708c616f69f153a8d9df0f0835b61c5bada96d2c5d37c6c55a69cf658178c44c",
    "log_loss": 0.6641703423957961,
    "brier": 0.2358933842952002,
}

CANDIDATE_GRID: tuple[dict[str, Any], ...] = (
    {"family": "l2", "C": 0.03, "l1_ratio": None},
    {"family": "l2", "C": 0.10, "l1_ratio": None},
    {"family": "l2", "C": 0.30, "l1_ratio": None},
    {"family": "l2", "C": 1.00, "l1_ratio": None},
    {"family": "elasticnet", "C": 0.03, "l1_ratio": 0.10},
    {"family": "elasticnet", "C": 0.03, "l1_ratio": 0.50},
    {"family": "elasticnet", "C": 0.03, "l1_ratio": 0.90},
    {"family": "elasticnet", "C": 0.10, "l1_ratio": 0.10},
    {"family": "elasticnet", "C": 0.10, "l1_ratio": 0.50},
    {"family": "elasticnet", "C": 0.10, "l1_ratio": 0.90},
    {"family": "elasticnet", "C": 0.30, "l1_ratio": 0.10},
    {"family": "elasticnet", "C": 0.30, "l1_ratio": 0.50},
    {"family": "elasticnet", "C": 0.30, "l1_ratio": 0.90},
)

ACCEPTANCE_GATES = {
    "clear_min_log_loss_improvement": 0.005,
    "clear_min_brier_improvement": 0.0025,
    "clear_min_both_fold_wins": 8,
    "clear_confirmation_requires_both_positive": True,
    "max_material_ece_deterioration": 0.010,
    "modest_requires_aggregate_both_positive": True,
    "modest_min_log_loss_fold_wins": 7,
    "max_confirmation_log_loss_regression_for_modest": 0.0025,
    "max_confirmation_brier_regression_for_modest": 0.00125,
    "regression_log_loss_threshold": 0.005,
    "regression_brier_threshold": 0.0025,
}

FORBIDDEN_TOKENS = (
    "odds", "sportsbook", "bookmaker", "price", "closing", "opening",
    "market_probability", "roi", "kelly", "implied_probability",
)

SOURCE_FAMILY = {
    "age_at_fight": "experience_context",
    "layoff_days": "experience_context",
    "prior_fight_count": "experience_context",
    "physical_size_profile": "experience_context",
    "prior_scale_weight_lbs": "experience_context",
    "sig_strike_efficiency": "striking",
    "sig_target_mix": "striking",
    "sig_environment_mix": "striking",
    "sig_strike_flow": "pace_output",
    "takedown_conversion": "wrestling",
    "takedown_pressure": "wrestling",
    "reversal_rate": "wrestling",
    "submission_attempt_rate": "submission",
    "control_rate": "control_grappling",
    "knockdown_efficiency": "durability_finish_history",
    "knockdown_rate": "durability_finish_history",
    "early_finish_profile": "durability_finish_history",
    "finish_method_loss_profile": "durability_finish_history",
    "finish_method_win_profile": "durability_finish_history",
}

ABLATION_FAMILIES = (
    "experience_context",
    "striking",
    "pace_output",
    "wrestling",
    "submission",
    "control_grappling",
    "durability_finish_history",
    "sample_support_missingness",
    "existing_matchup",
)


class M1Error(ValueError):
    """Raised when M1 contracts or inputs fail closed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise M1Error(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise M1Error(f"{path} must contain a JSON object")
    return value


def feature_surface_hash(surface: dict[str, Any]) -> str:
    payload = dict(surface)
    payload.pop("feature_surface_logical_sha256", None)
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def candidate_name(spec: dict[str, Any]) -> str:
    if spec["family"] == "l2":
        return f"l2_C={spec['C']:.2f}"
    return f"elasticnet_C={spec['C']:.2f}_l1={spec['l1_ratio']:.2f}"


def validate_candidate_grid() -> None:
    if len(CANDIDATE_GRID) != 13:
        raise M1Error("candidate grid size changed")
    names = [candidate_name(spec) for spec in CANDIDATE_GRID]
    if len(set(names)) != len(names):
        raise M1Error("candidate grid names are not unique")
    allowed_c = {0.03, 0.10, 0.30, 1.00}
    allowed_ratio = {0.10, 0.50, 0.90}
    for spec in CANDIDATE_GRID:
        if spec["C"] not in allowed_c:
            raise M1Error("candidate C outside frozen grid")
        if spec["family"] == "l2":
            if spec["l1_ratio"] is not None:
                raise M1Error("L2 candidate cannot have l1_ratio")
        elif spec["family"] == "elasticnet":
            if spec["C"] == 1.00 or spec["l1_ratio"] not in allowed_ratio:
                raise M1Error("elastic-net candidate outside frozen grid")
        else:
            raise M1Error(f"unexpected candidate family {spec['family']}")


def validate_f02_identity(f02_dir: Path) -> dict[str, Any]:
    schema = _read_json(f02_dir / "schema.json")
    manifest = _read_json(f02_dir / "manifest.json")
    target_manifest = _read_json(f02_dir / "target_manifest.json")
    summary = _read_json(f02_dir / "summary.json")
    if schema.get("replay_schema_version") != F02_IDENTITY["replay_schema_version"]:
        raise M1Error("F02 replay schema version mismatch")
    if schema.get("schema_sha256") != F02_IDENTITY["schema_sha256"]:
        raise M1Error("F02 schema hash mismatch")
    if summary.get("predictor_logical_sha256") != F02_IDENTITY["predictor_logical_sha256"]:
        raise M1Error("F02 predictor logical hash mismatch")
    if summary.get("predictor_manifest_sha256") != F02_IDENTITY["predictor_manifest_sha256"]:
        raise M1Error("F02 predictor manifest hash mismatch")
    target_det = target_manifest.get("deterministic", {})
    target_contract = manifest.get("deterministic", {}).get("target_contract", {})
    if target_contract.get("contract_sha256") != F02_IDENTITY["target_contract_sha256"]:
        raise M1Error("F02 target contract hash mismatch")
    if target_det.get("target_logical_sha256") != F02_IDENTITY["target_logical_sha256"]:
        raise M1Error("F02 target logical hash mismatch")
    return {"schema": schema, "manifest": manifest, "target_manifest": target_manifest, "summary": summary}


def surface_pairs(surface: dict[str, Any]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    concepts = surface["paired_fighter_predictors"]["concepts"]
    for source_concept in sorted(concepts):
        for key in concepts[source_concept]:
            pairs.append({
                "semantic_key": key,
                "source_concept": source_concept,
                "f1_column": f"f1__{key}",
                "f2_column": f"f2__{key}",
            })
    return pairs


def validate_surface(surface: dict[str, Any], schema: dict[str, Any]) -> None:
    expected_hash = surface.get("feature_surface_logical_sha256")
    actual_hash = feature_surface_hash(surface)
    if expected_hash != actual_hash:
        raise M1Error(f"feature surface hash mismatch: {actual_hash}")
    if surface.get("status") != "M1_FEATURE_SURFACE_V1_FROZEN":
        raise M1Error("feature surface is not frozen")
    schema_predictors = [c for c in schema.get("columns", []) if c.get("predictor") is True]
    if len(schema_predictors) != 200:
        raise M1Error(f"expected 200 F02 predictors, found {len(schema_predictors)}")
    schema_by_name = {c["name"]: c for c in schema_predictors}
    if any(any(token in name.casefold() for token in FORBIDDEN_TOKENS) for name in schema_by_name):
        raise M1Error("forbidden market/sportsbook token appears in F02 predictor schema")

    pairs = surface_pairs(surface)
    if len(pairs) != 96:
        raise M1Error("feature surface must contain 96 fighter semantic pairs")
    used: set[str] = set()
    for pair in pairs:
        f1 = pair["f1_column"]
        f2 = pair["f2_column"]
        if f1 not in schema_by_name or f2 not in schema_by_name:
            raise M1Error(f"feature-surface pair absent from F02 schema: {f1}, {f2}")
        if schema_by_name[f1].get("role") != "f1" or schema_by_name[f2].get("role") != "f2":
            raise M1Error(f"fighter pair role mismatch: {f1}, {f2}")
        if schema_by_name[f1].get("source_concept") != pair["source_concept"]:
            raise M1Error(f"source concept mismatch: {f1}")
        if schema_by_name[f2].get("source_concept") != pair["source_concept"]:
            raise M1Error(f"source concept mismatch: {f2}")
        used.update((f1, f2))
    fighter_predictors = {c["name"] for c in schema_predictors if c.get("role") in {"f1", "f2"}}
    if used != fighter_predictors:
        raise M1Error("feature surface does not exactly cover all F02 fighter predictors")

    reviewed_mx = set()
    for item in surface["matchup_predictors"]["review"]:
        for name in item["columns"]:
            reviewed_mx.add(name)
            if name not in schema_by_name or schema_by_name[name].get("role") != "mx":
                raise M1Error(f"matchup review column invalid: {name}")
    actual_mx = {c["name"] for c in schema_predictors if c.get("role") == "mx"}
    if reviewed_mx != actual_mx:
        raise M1Error("matchup predictor review does not exactly cover F02 matchup predictors")

    context_names = {item["column"] for item in surface["shared_context_diagnostic_only"]}
    actual_context = {c["name"] for c in schema_predictors if c.get("role") == "fight_context"}
    if context_names != actual_context:
        raise M1Error("shared-context exclusions do not exactly cover F02 fight context predictors")
    if any(item.get("accepted") for item in surface["shared_context_diagnostic_only"]):
        raise M1Error("shared context cannot enter M1 V1")
    if surface["projection"]["final_projected_dimensions"] != 197:
        raise M1Error("M1 V1 projected dimension count changed")


def load_modeling_table(f02_dir: Path, surface_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    identity = validate_f02_identity(f02_dir)
    surface = _read_json(surface_path)
    validate_surface(surface, identity["schema"])
    path = f02_dir / "winner_modeling_table.parquet"
    if not path.exists():
        raise M1Error(f"missing F02 modeling table: {path}")
    frame = pd.read_parquet(path)
    frame["event_date"] = pd.to_datetime(frame["event_date"], errors="raise")
    frame = frame.sort_values(["event_date", "event_id", "fight_id"]).reset_index(drop=True)
    return frame, surface


def primary_population(frame: pd.DataFrame) -> pd.DataFrame:
    mask = (
        frame["promotion"].eq("UFC")
        & frame["binary_winner_eligible"].eq(True)
        & frame["fighter_1_win"].notna()
        & frame["event_date"].ge(MODEL_ERA_START)
    )
    out = frame.loc[mask].copy()
    if out.empty:
        raise M1Error("primary UFC population is empty")
    if not out["fighter_1_win"].isin([True, False]).all():
        raise M1Error("primary target contains non-binary values")
    return out


def fold_frames(population: pd.DataFrame, validation_year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = population[population["event_date"].dt.year < validation_year].copy()
    valid = population[population["event_date"].dt.year == validation_year].copy()
    if train.empty or valid.empty:
        raise M1Error(f"empty train/validation fold for {validation_year}")
    if train["event_date"].max() >= valid["event_date"].min():
        raise M1Error(f"chronological overlap in fold {validation_year}")
    if set(train["fight_id"]) & set(valid["fight_id"]):
        raise M1Error(f"fight overlap in fold {validation_year}")
    return train, valid


def _inner_years(outer_year: int) -> tuple[int, ...]:
    years = tuple(range(outer_year - INNER_VALIDATION_YEARS, outer_year))
    if years[0] < 2012:
        raise M1Error(f"inner validation boundary too early for outer {outer_year}")
    return years


def metric_bundle(target: Iterable[int | bool], prob: Iterable[float]) -> dict[str, float | int | None]:
    y = np.asarray(list(target), dtype=int)
    p = np.clip(np.asarray(list(prob), dtype=float), 1e-12, 1 - 1e-12)
    if len(y) != len(p):
        raise M1Error("metric length mismatch")
    try:
        auc: float | None = float(roc_auc_score(y, p))
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
        rows.append({"bin": label, "rows": n, "mean_predicted": mean_p, "actual_win_rate": actual})
    return rows, float(ece)


@dataclass(frozen=True)
class OutputMeta:
    name: str
    source_concept: str
    family: str
    role: str
    is_missingness: bool


class M1Projector:
    """Orientation-safe broad projection discovered from the frozen surface."""

    def __init__(self, surface: dict[str, Any], *, ablate_family: str | None = None):
        self.surface = surface
        self.ablate_family = ablate_family
        self.pair_medians: dict[str, float] = {}
        self.mx_medians: dict[str, float] = {}
        self.output_meta: list[OutputMeta] = []
        self._build_meta()

    def _build_meta(self) -> None:
        meta: list[OutputMeta] = []
        for pair in surface_pairs(self.surface):
            concept = pair["source_concept"]
            family = SOURCE_FAMILY.get(concept)
            if family is None:
                raise M1Error(f"unmapped M1 source concept: {concept}")
            key = pair["semantic_key"]
            meta.append(OutputMeta(f"pair::{key}::diff", concept, family, "fighter_pair", False))
            meta.append(OutputMeta(f"pair::{key}::missing_diff", concept, family, "fighter_pair", True))
        for item in self.surface["matchup_predictors"]["review"]:
            columns = item["columns"]
            if len(columns) == 2:
                key = columns[0].replace("mx__", "").replace("__f1_vs_f2", "")
                meta.append(OutputMeta(f"mx::{key}::diff", item["source_concept"], "existing_matchup", "matchup", False))
                meta.append(OutputMeta(f"mx::{key}::missing_diff", item["source_concept"], "existing_matchup", "matchup", True))
            elif len(columns) == 1:
                meta.append(OutputMeta(f"mx::{item['source_concept']}::signed", item["source_concept"], "existing_matchup", "matchup", False))
            else:
                raise M1Error("unsupported matchup review shape")
        if len(meta) != 197:
            raise M1Error(f"projected metadata dimension mismatch: {len(meta)}")
        self.output_meta = meta

    @property
    def output_names(self) -> list[str]:
        return [m.name for m in self.output_meta if self._keep(m)]

    def _keep(self, meta: OutputMeta) -> bool:
        if self.ablate_family is None:
            return True
        if self.ablate_family == "sample_support_missingness":
            return not meta.is_missingness
        return meta.family != self.ablate_family

    def fit(self, frame: pd.DataFrame) -> "M1Projector":
        self.pair_medians = {}
        for pair in surface_pairs(self.surface):
            a = pd.to_numeric(frame[pair["f1_column"]], errors="coerce")
            b = pd.to_numeric(frame[pair["f2_column"]], errors="coerce")
            pooled = pd.concat([a, b], ignore_index=True)
            median = pooled.median(skipna=True)
            if pd.isna(median):
                median = 0.0
            self.pair_medians[pair["semantic_key"]] = float(median)
        self.mx_medians = {}
        for item in self.surface["matchup_predictors"]["review"]:
            if len(item["columns"]) != 2:
                continue
            a = pd.to_numeric(frame[item["columns"][0]], errors="coerce")
            b = pd.to_numeric(frame[item["columns"][1]], errors="coerce")
            median = pd.concat([a, b], ignore_index=True).median(skipna=True)
            if pd.isna(median):
                median = 0.0
            self.mx_medians[item["columns"][0]] = float(median)
        return self

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        if len(self.pair_medians) != 96:
            raise M1Error("projector must be fit before transform")
        arrays: list[np.ndarray] = []
        metas: list[OutputMeta] = []
        meta_iter = iter(self.output_meta)
        for pair in surface_pairs(self.surface):
            value_meta = next(meta_iter)
            missing_meta = next(meta_iter)
            a = pd.to_numeric(frame[pair["f1_column"]], errors="coerce")
            b = pd.to_numeric(frame[pair["f2_column"]], errors="coerce")
            med = self.pair_medians[pair["semantic_key"]]
            diff = (a.fillna(med) - b.fillna(med)).to_numpy(dtype=float)
            missing_diff = a.isna().to_numpy(dtype=float) - b.isna().to_numpy(dtype=float)
            if self._keep(value_meta):
                arrays.append(diff); metas.append(value_meta)
            if self._keep(missing_meta):
                arrays.append(missing_diff); metas.append(missing_meta)
        for item in self.surface["matchup_predictors"]["review"]:
            if len(item["columns"]) == 2:
                value_meta = next(meta_iter)
                missing_meta = next(meta_iter)
                a = pd.to_numeric(frame[item["columns"][0]], errors="coerce")
                b = pd.to_numeric(frame[item["columns"][1]], errors="coerce")
                med = self.mx_medians[item["columns"][0]]
                diff = (a.fillna(med) - b.fillna(med)).to_numpy(dtype=float)
                missing_diff = a.isna().to_numpy(dtype=float) - b.isna().to_numpy(dtype=float)
                if self._keep(value_meta):
                    arrays.append(diff); metas.append(value_meta)
                if self._keep(missing_meta):
                    arrays.append(missing_diff); metas.append(missing_meta)
            else:
                value_meta = next(meta_iter)
                values = pd.to_numeric(frame[item["columns"][0]], errors="coerce").fillna(0.0).to_numpy(dtype=float)
                if self._keep(value_meta):
                    arrays.append(values); metas.append(value_meta)
        if list(meta_iter):
            raise M1Error("projector metadata iterator did not exhaust")
        if not arrays:
            raise M1Error("projection produced no dimensions")
        return np.column_stack(arrays)

    def kept_meta(self) -> list[OutputMeta]:
        return [m for m in self.output_meta if self._keep(m)]


@dataclass
class FittedM1:
    projector: M1Projector
    scaler: StandardScaler
    model: LogisticRegression
    spec: dict[str, Any]

    @classmethod
    def fit(cls, frame: pd.DataFrame, target: pd.Series, surface: dict[str, Any], spec: dict[str, Any], *, ablate_family: str | None = None) -> "FittedM1":
        projector = M1Projector(surface, ablate_family=ablate_family).fit(frame)
        matrix = projector.transform(frame)
        scaler = StandardScaler(with_mean=False)
        scaled = scaler.fit_transform(matrix)
        if spec["family"] == "l2":
            model = LogisticRegression(penalty="l2", C=float(spec["C"]), solver="lbfgs", max_iter=3000, random_state=RANDOM_SEED, fit_intercept=False)
        elif spec["family"] == "elasticnet":
            model = LogisticRegression(penalty="elasticnet", C=float(spec["C"]), l1_ratio=float(spec["l1_ratio"]), solver="saga", max_iter=5000, tol=1e-5, random_state=RANDOM_SEED, fit_intercept=False)
        else:
            raise M1Error(f"unsupported candidate family {spec['family']}")
        model.fit(scaled, target.astype(int).to_numpy())
        return cls(projector, scaler, model, dict(spec))

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        matrix = self.projector.transform(frame)
        return self.model.predict_proba(self.scaler.transform(matrix))[:, 1]

    def coefficient_rows(self) -> list[dict[str, Any]]:
        rows = []
        for meta, coefficient in zip(self.projector.kept_meta(), self.model.coef_[0], strict=True):
            rows.append({"feature": meta.name, "source_concept": meta.source_concept, "family": meta.family, "role": meta.role, "is_missingness": meta.is_missingness, "coefficient": float(coefficient)})
        return rows


def swap_frame(frame: pd.DataFrame, surface: dict[str, Any]) -> pd.DataFrame:
    swapped = frame.copy()
    for pair in surface_pairs(surface):
        swapped[pair["f1_column"]] = frame[pair["f2_column"]].to_numpy()
        swapped[pair["f2_column"]] = frame[pair["f1_column"]].to_numpy()
    for item in surface["matchup_predictors"]["review"]:
        if len(item["columns"]) == 2:
            a, b = item["columns"]
            swapped[a] = frame[b].to_numpy()
            swapped[b] = frame[a].to_numpy()
        else:
            col = item["columns"][0]
            swapped[col] = -pd.to_numeric(frame[col], errors="coerce")
    return swapped


def orientation_error(model: FittedM1, frame: pd.DataFrame, surface: dict[str, Any]) -> float:
    p = model.predict_proba(frame)
    q = model.predict_proba(swap_frame(frame, surface))
    return float(np.max(np.abs(p + q - 1.0)))


def _candidate_inner_predictions(population: pd.DataFrame, surface: dict[str, Any], spec: dict[str, Any], outer_year: int, *, ablate_family: str | None = None) -> tuple[np.ndarray, np.ndarray, list[int]]:
    targets: list[np.ndarray] = []
    probs: list[np.ndarray] = []
    years: list[int] = []
    outer_train = population[population["event_date"].dt.year < outer_year].copy()
    for inner_year in _inner_years(outer_year):
        inner_train = outer_train[outer_train["event_date"].dt.year < inner_year].copy()
        inner_valid = outer_train[outer_train["event_date"].dt.year == inner_year].copy()
        if inner_train.empty or inner_valid.empty:
            raise M1Error(f"empty inner fold {inner_year} for outer {outer_year}")
        if inner_train["event_date"].max() >= inner_valid["event_date"].min():
            raise M1Error(f"inner chronology failure {inner_year}/{outer_year}")
        if set(inner_train["fight_id"]) & set(inner_valid["fight_id"]):
            raise M1Error(f"inner fight overlap {inner_year}/{outer_year}")
        model = FittedM1.fit(inner_train, inner_train["fighter_1_win"].astype(int), surface, spec, ablate_family=ablate_family)
        targets.append(inner_valid["fighter_1_win"].astype(int).to_numpy())
        probs.append(model.predict_proba(inner_valid))
        years.append(inner_year)
    return np.concatenate(targets), np.concatenate(probs), years


def select_candidate(population: pd.DataFrame, surface: dict[str, Any], outer_year: int, *, ablate_family: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scores: list[dict[str, Any]] = []
    for index, spec in enumerate(CANDIDATE_GRID):
        y, p, inner_years = _candidate_inner_predictions(population, surface, spec, outer_year, ablate_family=ablate_family)
        score = float(log_loss(y, np.clip(p, 1e-12, 1 - 1e-12), labels=[0, 1]))
        scores.append({"grid_index": index, "candidate": candidate_name(spec), "family": spec["family"], "C": spec["C"], "l1_ratio": spec["l1_ratio"], "inner_years": inner_years, "inner_rows": int(len(y)), "inner_log_loss": score})
    winner = min(scores, key=lambda row: (row["inner_log_loss"], row["grid_index"]))
    return dict(CANDIDATE_GRID[int(winner["grid_index"])]), scores


def load_frozen_m0_oof(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise M1Error(f"missing frozen M0 OOF artifact: {path}")
    oof = pd.read_parquet(path).copy()
    required = {"fight_id", "event_date", "fold_id", "target", "naive_probability", "empirical_probability", "logistic_probability"}
    missing = sorted(required - set(oof.columns))
    if missing:
        raise M1Error(f"frozen M0 OOF missing columns: {missing}")
    from ufc_edge.models.m0 import oof_logical_hash as m0_oof_logical_hash
    actual_hash = m0_oof_logical_hash(oof)
    if len(oof) != M0_IDENTITY["rows"] or actual_hash != M0_IDENTITY["logical_sha256"]:
        raise M1Error(f"frozen M0 OOF identity mismatch: rows={len(oof)} hash={actual_hash}")
    metrics = metric_bundle(oof["target"], oof["logistic_probability"])
    if abs(float(metrics["log_loss"]) - M0_IDENTITY["log_loss"]) > 1e-12:
        raise M1Error("frozen M0 log loss mismatch")
    if abs(float(metrics["brier"]) - M0_IDENTITY["brier"]) > 1e-12:
        raise M1Error("frozen M0 Brier mismatch")
    oof["event_date"] = pd.to_datetime(oof["event_date"], errors="raise")
    return oof.sort_values(["event_date", "fight_id"]).reset_index(drop=True)


def _subset_metrics(oof: pd.DataFrame, years: Sequence[int], prob_col: str) -> dict[str, Any]:
    subset = oof[oof["event_date"].dt.year.isin(years)]
    return metric_bundle(subset["target"], subset[prob_col])


def _compare_metrics(m0: dict[str, Any], m1: dict[str, Any]) -> dict[str, Any]:
    return {"m0": m0, "m1": m1, "delta_m1_minus_m0": {"log_loss": float(m1["log_loss"] - m0["log_loss"]), "brier": float(m1["brier"] - m0["brier"]), "accuracy": float(m1["accuracy"] - m0["accuracy"]), "auc": None if m0["auc"] is None or m1["auc"] is None else float(m1["auc"] - m0["auc"])}}


def classify_verdict(aggregate_compare: dict[str, Any], confirmation_compare: dict[str, Any], both_fold_wins: int, log_loss_fold_wins: int, m0_ece: float, m1_ece: float) -> str:
    d = aggregate_compare["delta_m1_minus_m0"]
    c = confirmation_compare["delta_m1_minus_m0"]
    log_improve = -float(d["log_loss"])
    brier_improve = -float(d["brier"])
    ece_deterioration = m1_ece - m0_ece
    clear = (log_improve >= ACCEPTANCE_GATES["clear_min_log_loss_improvement"] and brier_improve >= ACCEPTANCE_GATES["clear_min_brier_improvement"] and both_fold_wins >= ACCEPTANCE_GATES["clear_min_both_fold_wins"] and float(c["log_loss"]) < 0.0 and float(c["brier"]) < 0.0 and ece_deterioration <= ACCEPTANCE_GATES["max_material_ece_deterioration"])
    if clear:
        return "M1_CLEAR_IMPROVEMENT"
    regression = (float(d["log_loss"]) >= ACCEPTANCE_GATES["regression_log_loss_threshold"] or float(d["brier"]) >= ACCEPTANCE_GATES["regression_brier_threshold"])
    if regression:
        return "M1_REGRESSION"
    modest = (float(d["log_loss"]) < 0.0 and float(d["brier"]) < 0.0 and log_loss_fold_wins >= ACCEPTANCE_GATES["modest_min_log_loss_fold_wins"] and float(c["log_loss"]) <= ACCEPTANCE_GATES["max_confirmation_log_loss_regression_for_modest"] and float(c["brier"]) <= ACCEPTANCE_GATES["max_confirmation_brier_regression_for_modest"] and ece_deterioration <= ACCEPTANCE_GATES["max_material_ece_deterioration"])
    if modest:
        return "M1_MODEST_IMPROVEMENT"
    return "M1_NO_MEANINGFUL_IMPROVEMENT"


def oof_logical_hash(oof: pd.DataFrame) -> str:
    digest = sha256()
    columns = ("fight_id", "event_date", "fold_id", "target", "m0_probability", "m1_probability", "chosen_spec")
    ordered = oof.sort_values(["event_date", "fight_id"])
    for row in ordered.loc[:, columns].itertuples(index=False, name=None):
        payload = list(row)
        payload[1] = str(payload[1].date() if hasattr(payload[1], "date") else payload[1])
        digest.update(canonical_json(payload).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def coefficient_diagnostics(fold_coefficients: list[dict[str, Any]]) -> dict[str, Any]:
    by_feature: dict[str, list[float]] = {}
    meta_by_feature: dict[str, dict[str, Any]] = {}
    selected_family: dict[str, int] = {"l2": 0, "elasticnet": 0}
    for fold in fold_coefficients:
        selected_family[fold["selected_spec"]["family"]] += 1
        for row in fold["coefficients"]:
            by_feature.setdefault(row["feature"], []).append(row["coefficient"])
            meta_by_feature[row["feature"]] = row
    stability = {}
    for name, values in by_feature.items():
        signs = {int(np.sign(v)) for v in values if abs(v) > 1e-10}
        stability[name] = {"mean": float(np.mean(values)), "min": float(np.min(values)), "max": float(np.max(values)), "nonzero_folds": int(sum(abs(v) > 1e-10 for v in values)), "positive_folds": int(sum(v > 1e-10 for v in values)), "negative_folds": int(sum(v < -1e-10 for v in values)), "direction_consistent": len(signs) <= 1}
    mean_abs = sorted(((name, float(np.mean(np.abs(values)))) for name, values in by_feature.items()), key=lambda x: (-x[1], x[0]))
    family_mass: dict[str, float] = {}
    for name, values in by_feature.items():
        family = meta_by_feature[name]["family"]
        family_mass[family] = family_mass.get(family, 0.0) + float(np.mean(np.abs(values)))
    missing_mass = sum(float(np.mean(np.abs(by_feature[name]))) for name, meta in meta_by_feature.items() if meta["is_missingness"])
    total_mass = sum(float(np.mean(np.abs(v))) for v in by_feature.values())
    top10_mass = sum(value for _, value in mean_abs[:10])
    return {
        "selected_model_family_counts": selected_family,
        "feature_stability": stability,
        "strongest_mean_absolute_standardized_terms": [{"feature": name, "mean_abs_coefficient": value, **{k: meta_by_feature[name][k] for k in ("source_concept", "family", "role", "is_missingness")}} for name, value in mean_abs[:25]],
        "family_coefficient_mass": dict(sorted(family_mass.items())),
        "missingness_coefficient_mass_fraction": 0.0 if total_mass == 0 else float(missing_mass / total_mass),
        "top10_coefficient_mass_fraction": 0.0 if total_mass == 0 else float(top10_mass / total_mass),
        "elasticnet_retention_frequency": {name: int(sum(abs(v) > 1e-10 for v in values)) / len(values) for name, values in by_feature.items()},
    }


def _run_primary(population: pd.DataFrame, surface: dict[str, Any], frozen_m0: pd.DataFrame, *, ablate_family: str | None = None, collect_coefficients: bool = True) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    parts: list[pd.DataFrame] = []
    fold_results: list[dict[str, Any]] = []
    coefficient_rows: list[dict[str, Any]] = []
    for year in OUTER_YEARS:
        train, valid = fold_frames(population, year)
        selected, tuning = select_candidate(population, surface, year, ablate_family=ablate_family)
        model = FittedM1.fit(train, train["fighter_1_win"].astype(int), surface, selected, ablate_family=ablate_family)
        p = model.predict_proba(valid)
        swap_error = orientation_error(model, valid, surface)
        if swap_error > 1e-10:
            raise M1Error(f"swap complement failure in {year}: {swap_error}")
        part = pd.DataFrame({"fight_id": valid["fight_id"].to_numpy(), "event_date": valid["event_date"].to_numpy(), "fold_id": str(year), "target": valid["fighter_1_win"].astype(int).to_numpy(), "m1_probability": p, "chosen_spec": candidate_name(selected)})
        m0_cols = frozen_m0[frozen_m0["fold_id"].astype(str).eq(str(year))][["fight_id", "target", "logistic_probability"]].copy()
        merged = part.merge(m0_cols, on="fight_id", how="left", suffixes=("", "_m0"), validate="one_to_one")
        if merged["logistic_probability"].isna().any():
            raise M1Error(f"M0 OOF alignment failure in {year}")
        if not np.array_equal(merged["target"].to_numpy(), merged["target_m0"].astype(int).to_numpy()):
            raise M1Error(f"M0 target mismatch in {year}")
        merged = merged.rename(columns={"logistic_probability": "m0_probability"}).drop(columns=["target_m0"])
        parts.append(merged)
        fold_results.append({"fold_id": str(year), "train_start": str(train["event_date"].min().date()), "train_end": str(train["event_date"].max().date()), "validation_start": str(valid["event_date"].min().date()), "validation_end": str(valid["event_date"].max().date()), "train_rows": int(len(train)), "validation_rows": int(len(valid)), "selected_spec": selected, "selected_candidate": candidate_name(selected), "inner_selection_objective": "chronological_log_loss_only", "inner_scores": tuning, "orientation_max_abs_error": swap_error, "m0": metric_bundle(merged["target"], merged["m0_probability"]), "m1": metric_bundle(merged["target"], merged["m1_probability"])})
        if collect_coefficients:
            coefficient_rows.append({"fold_id": str(year), "selected_spec": selected, "coefficients": model.coefficient_rows()})
    oof = pd.concat(parts, ignore_index=True).sort_values(["event_date", "fight_id"]).reset_index(drop=True)
    if len(oof) != M0_IDENTITY["rows"] or oof["fight_id"].duplicated().any():
        raise M1Error("M1 OOF population does not exactly match frozen M0")
    return oof, fold_results, coefficient_rows



def run_ablation_family(
    f02_dir: Path,
    m0_oof_path: Path,
    surface_path: Path,
    primary_result_path: Path,
    output_dir: Path,
    family: str,
) -> dict[str, Any]:
    """Run one predeclared post-freeze M1 feature-family ablation."""
    validate_candidate_grid()
    if family not in ABLATION_FAMILIES:
        raise M1Error(f"unknown ablation family: {family}")

    frame, surface = load_modeling_table(f02_dir, surface_path)
    population = primary_population(frame)
    frozen_m0 = load_frozen_m0_oof(m0_oof_path)
    primary = _read_json(primary_result_path)

    if primary.get("status") != "M1_REGULARIZED_SHARED_FEATURE_WINNER_V1_COMPLETE":
        raise M1Error("primary M1 result is not complete")
    if primary.get("source", {}).get("feature_surface_logical_sha256") != surface["feature_surface_logical_sha256"]:
        raise M1Error("primary M1 feature-surface identity mismatch")
    if primary.get("source", {}).get("m0", {}).get("logical_sha256") != M0_IDENTITY["logical_sha256"]:
        raise M1Error("primary M1 frozen M0 identity mismatch")
    if primary.get("source", {}).get("f02", {}).get("predictor_logical_sha256") != F02_IDENTITY["predictor_logical_sha256"]:
        raise M1Error("primary M1 frozen F02 identity mismatch")

    primary_metrics = primary.get("aggregate", {}).get("m1", {})
    if "log_loss" not in primary_metrics or "brier" not in primary_metrics:
        raise M1Error("primary M1 aggregate metrics missing")

    ab_oof, ab_folds, _ = _run_primary(
        population,
        surface,
        frozen_m0,
        ablate_family=family,
        collect_coefficients=False,
    )
    metrics = metric_bundle(ab_oof["target"], ab_oof["m1_probability"])
    result = {
        "status": "M1_FEATURE_FAMILY_ABLATION_V1_COMPLETE",
        "family": family,
        "source": {
            "f02": F02_IDENTITY,
            "m0": M0_IDENTITY,
            "feature_surface_logical_sha256": surface["feature_surface_logical_sha256"],
            "primary_oof_logical_sha256": primary.get("oof", {}).get("logical_sha256"),
        },
        "metrics": metrics,
        "delta_vs_primary_m1": {
            "log_loss": float(metrics["log_loss"] - float(primary_metrics["log_loss"])),
            "brier": float(metrics["brier"] - float(primary_metrics["brier"])),
        },
        "selected_candidates": {
            row["fold_id"]: row["selected_candidate"] for row in ab_folds
        },
        "folds": ab_folds,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"m1_ablation_{family}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result

def run_validation(f02_dir: Path, m0_oof_path: Path, surface_path: Path, output_dir: Path, *, run_ablations: bool = True) -> dict[str, Any]:
    validate_candidate_grid()
    frame, surface = load_modeling_table(f02_dir, surface_path)
    population = primary_population(frame)
    frozen_m0 = load_frozen_m0_oof(m0_oof_path)

    oof, folds, fold_coefficients = _run_primary(population, surface, frozen_m0)
    aggregate_m0 = metric_bundle(oof["target"], oof["m0_probability"])
    aggregate_m1 = metric_bundle(oof["target"], oof["m1_probability"])
    aggregate_compare = _compare_metrics(aggregate_m0, aggregate_m1)
    development_compare = _compare_metrics(_subset_metrics(oof, DEVELOPMENT_YEARS, "m0_probability"), _subset_metrics(oof, DEVELOPMENT_YEARS, "m1_probability"))
    confirmation_compare = _compare_metrics(_subset_metrics(oof, CONFIRMATION_YEARS, "m0_probability"), _subset_metrics(oof, CONFIRMATION_YEARS, "m1_probability"))

    _, m0_ece = calibration_table(oof["target"], oof["m0_probability"])
    m1_calibration, m1_ece = calibration_table(oof["target"], oof["m1_probability"])
    log_loss_wins = sum(row["m1"]["log_loss"] < row["m0"]["log_loss"] for row in folds)
    brier_wins = sum(row["m1"]["brier"] < row["m0"]["brier"] for row in folds)
    both_wins = sum(row["m1"]["log_loss"] < row["m0"]["log_loss"] and row["m1"]["brier"] < row["m0"]["brier"] for row in folds)
    verdict = classify_verdict(aggregate_compare, confirmation_compare, both_wins, log_loss_wins, m0_ece, m1_ece)

    ablations: dict[str, Any] = {}
    if run_ablations:
        primary_ll = float(aggregate_m1["log_loss"])
        primary_brier = float(aggregate_m1["brier"])
        requested_family = os.environ.get("M1_ABLATION_FAMILY")
        if requested_family:
            if requested_family not in ABLATION_FAMILIES:
                raise M1Error(f"unknown ablation family: {requested_family}")
            ablation_families = (requested_family,)
        else:
            ablation_families = ABLATION_FAMILIES
        for family in ablation_families:
            ab_oof, ab_folds, _ = _run_primary(population, surface, frozen_m0, ablate_family=family, collect_coefficients=False)
            metrics = metric_bundle(ab_oof["target"], ab_oof["m1_probability"])
            ablations[family] = {"metrics": metrics, "delta_vs_primary_m1": {"log_loss": float(metrics["log_loss"] - primary_ll), "brier": float(metrics["brier"] - primary_brier)}, "selected_candidates": {row["fold_id"]: row["selected_candidate"] for row in ab_folds}}

    result = {
        "status": "M1_REGULARIZED_SHARED_FEATURE_WINNER_V1_COMPLETE",
        "verdict": verdict,
        "source": {"f02": F02_IDENTITY, "m0": M0_IDENTITY, "feature_surface_logical_sha256": surface["feature_surface_logical_sha256"]},
        "guardrails": {"market_used_in_training": False, "market_used_for_feature_selection": False, "market_used_for_hyperparameter_selection": False, "roi_used": False, "m0_altered": False, "individual_features_outcome_shopped": False, "m1_frozen_before_sportsbook_comparison": True},
        "population": {"modeling_era_start": str(MODEL_ERA_START.date()), "rows": int(len(population)), "oof_rows": int(len(oof)), "outer_years": list(OUTER_YEARS), "development_years": list(DEVELOPMENT_YEARS), "confirmation_years": list(CONFIRMATION_YEARS)},
        "feature_surface": {"f02_predictors_reviewed": 200, "fighter_semantic_pairs": 96, "matchup_predictors_reviewed": 5, "shared_context_held_diagnostic_only": 3, "projected_dimensions": 197, "logical_sha256": surface["feature_surface_logical_sha256"]},
        "model": {"families": ["l2_logistic", "elasticnet_logistic"], "candidate_grid": list(CANDIDATE_GRID), "selection_objective": "chronological log loss only", "inner_validation_years_per_outer_fold": INNER_VALIDATION_YEARS, "preprocessing": surface["preprocessing"], "fit_intercept": False, "random_seed": RANDOM_SEED},
        "acceptance_gates": ACCEPTANCE_GATES,
        "folds": folds,
        "development": development_compare,
        "confirmation": confirmation_compare,
        "aggregate": aggregate_compare,
        "calibration": {"m0_expected_calibration_error": m0_ece, "m1_expected_calibration_error": m1_ece, "delta_m1_minus_m0": float(m1_ece - m0_ece), "m1_bins": m1_calibration},
        "stability": {"log_loss_fold_wins": int(log_loss_wins), "brier_fold_wins": int(brier_wins), "both_metric_fold_wins": int(both_wins), "fold_count": len(folds), "max_swap_probability_error": float(max(row["orientation_max_abs_error"] for row in folds))},
        "coefficient_diagnostics": coefficient_diagnostics(fold_coefficients),
        "feature_family_ablations": ablations,
        "oof": {"rows": int(len(oof)), "logical_sha256": oof_logical_hash(oof), "columns": ["fight_id", "event_date", "fold_id", "target", "m0_probability", "m1_probability", "chosen_spec"]},
        "limitations": ["M1 is a general fight-pricing model, not a sportsbook-edge or ROI model.", "Symmetric shared fight context remains diagnostic-only in M1 V1.", "No new context interactions are engineered in this task.", "Known missing positional-duration, sequence, escape-hazard, and judge-round features are not fabricated.", "2026 is a partial confirmation fold as represented in frozen F02."],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "m1_result.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    oof.to_parquet(output_dir / "m1_oof_predictions.parquet", index=False)
    (output_dir / "m1_coefficients.json").write_text(json.dumps(fold_coefficients, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return result
