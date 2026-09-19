from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ufc_edge.models.mov0 import (
    C_GRID,
    ERA_START,
    OUTER_YEARS,
    FittedSurface,
    MOV0Error,
    SurfacePreprocessor,
    b0_probability,
    deterministic_tie_break,
    inner_years,
    join_terrain,
    order_invariance_error,
    standard_finish_label,
    surface_columns,
    swap_fighters,
    validate_requested_columns,
)

SURFACE_PATH = ROOT / "models" / "mov0" / "feature_surface_v1.json"


@pytest.fixture(scope="module")
def surface() -> dict:
    return json.loads(SURFACE_PATH.read_text(encoding="utf-8"))


def synthetic_frame(surface: dict, name: str, rows: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(17)
    requested = surface_columns(surface, name)
    data: dict[str, object] = {
        "fight_id": [f"f{i}" for i in range(rows)],
        "event_id": [f"e{i // 10}" for i in range(rows)],
        "event_date": pd.to_datetime(["2017-06-01"] * rows),
        "target": np.asarray(([0, 1] * ((rows + 1) // 2))[:rows], dtype=int),
    }
    for column in requested:
        if column == "scheduled_rounds":
            data[column] = np.where(np.arange(rows) % 7 == 0, np.nan, 3.0)
        elif column == "ctx__title_bout":
            values = np.asarray([False, True] * ((rows + 1) // 2), dtype=object)[:rows]
            values[::11] = None
            data[column] = values
        elif column == "ctx__weight_class":
            values = np.asarray(["Lightweight", "Welterweight", "Featherweight"] * ((rows + 2) // 3), dtype=object)[:rows]
            values[::13] = None
            data[column] = values
        else:
            values = rng.normal(size=rows)
            values[::9] = np.nan
            data[column] = values
    return pd.DataFrame(data)


def test_target_determinism_and_exact_class_handling() -> None:
    assert standard_finish_label("win_loss", "KO_TKO") == 1
    assert standard_finish_label("win_loss", "SUBMISSION") == 1
    assert standard_finish_label("win_loss", "DECISION") == 0
    assert standard_finish_label("draw", "DECISION") == 0
    for result, method in [
        ("win_loss", "DQ"),
        ("draw", "DRAW"),
        ("no_contest", "NO_CONTEST"),
        ("no_contest", "OTHER"),
        ("unknown", "UNKNOWN"),
        ("win_loss", None),
    ]:
        assert standard_finish_label(result, method) is None


def test_outer_years_and_grid_are_exact() -> None:
    assert OUTER_YEARS == tuple(range(2018, 2027))
    assert C_GRID == (0.03, 0.1, 0.3, 1.0)
    assert inner_years(2018) == (2016, 2017)
    assert inner_years(2026) == (2024, 2025)


def test_allowlists_are_exact_and_unauthorized_feature_fails(surface: dict) -> None:
    for name in ("B0", "B1", "MOV0_MIN", "MOV0_FULL"):
        frozen = surface_columns(surface, name)
        validate_requested_columns(surface, name, frozen)
        if name != "B0":
            with pytest.raises(MOV0Error):
                validate_requested_columns(surface, name, frozen + ["unauthorized_column"])


def test_fighter_order_invariance_exact(surface: dict) -> None:
    frame = synthetic_frame(surface, "MOV0_FULL")
    fitted = FittedSurface.fit(frame, surface, "MOV0_FULL", 0.1)
    error = order_invariance_error(fitted, frame, surface, "MOV0_FULL")
    assert error <= 1e-12
    np.testing.assert_allclose(
        fitted.predict(frame),
        fitted.predict(swap_fighters(frame, surface, "MOV0_FULL")),
        atol=1e-12,
        rtol=0.0,
    )


def test_preprocessing_is_training_only(surface: dict) -> None:
    train = synthetic_frame(surface, "B1", rows=50)
    valid = synthetic_frame(surface, "B1", rows=10)
    valid["scheduled_rounds"] = 999.0
    prep = SurfacePreprocessor.fit(train, surface, "B1")
    before = prep.metadata()
    _ = prep.transform(valid)
    after = prep.metadata()
    assert before == after
    assert before["singleton_medians"]["scheduled_rounds"] != 999.0


def test_pre_2015_fit_fails_closed(surface: dict) -> None:
    frame = synthetic_frame(surface, "B1")
    frame.loc[0, "event_date"] = ERA_START - pd.Timedelta(days=1)
    with pytest.raises(MOV0Error, match="pre-2015"):
        FittedSurface.fit(frame, surface, "B1", 0.1)


def test_b0_uses_training_prevalence_only() -> None:
    train = pd.DataFrame(
        {
            "event_date": pd.to_datetime(["2015-01-01", "2015-02-01", "2016-01-01"]),
            "target": [1, 0, 1],
        }
    )
    p = b0_probability(train, 4)
    np.testing.assert_allclose(p, np.repeat(2 / 3, 4), atol=0.0, rtol=0.0)


def test_grid_tie_break_is_first_frozen_value() -> None:
    assert deterministic_tie_break([0.5, 0.5, 0.5, 0.5]) == 0.03
    assert deterministic_tie_break([0.5, 0.4, 0.4, 0.6]) == 0.1


def test_model_fit_is_reproducible(surface: dict) -> None:
    frame = synthetic_frame(surface, "MOV0_MIN")
    a = FittedSurface.fit(frame, surface, "MOV0_MIN", 0.3).predict(frame)
    b = FittedSurface.fit(frame, surface, "MOV0_MIN", 0.3).predict(frame)
    np.testing.assert_allclose(a, b, atol=0.0, rtol=0.0)


def test_terrain_is_joined_not_regenerated() -> None:
    oof = pd.DataFrame(
        {
            "fight_id": ["a", "b"],
            "event_id": ["e1", "e2"],
            "target": [0, 1],
            "year": [2018, 2018],
            "probability": [0.4, 0.6],
        }
    )
    assignment = pd.DataFrame(
        {
            "fight_id": ["a", "b"],
            "experience_bucket": ["0", "1-2"],
        }
    )
    merged = join_terrain(oof, assignment)
    assert merged["experience_bucket"].tolist() == ["0", "1-2"]
    assert list(assignment.columns) == ["fight_id", "experience_bucket"]
    with pytest.raises(MOV0Error):
        join_terrain(oof, assignment.iloc[:1].copy())
