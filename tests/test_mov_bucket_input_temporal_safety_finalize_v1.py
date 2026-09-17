from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).parents[1] / "tools" / "features" / "finalize_mov_bucket_input_audit_v1.py"
spec = importlib.util.spec_from_file_location("mov_finalize", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_prior_dominant_missingness_is_pit_safe():
    metric = {
        "diagnostic_rows": 922,
        "observed_side_win_rate": 0.5488,
        "observed_more_prior_fights_rate": 0.9848,
        "observed_more_future_fights_rate": 0.3742,
        "future_minus_prior_more_fights_rate": -0.6106,
        "mean_delta_prior_fights": 4.42,
        "mean_delta_future_fights": -0.82,
        "both_sides_have_prior_fight_rate": 0.0,
        "missing_side_zero_prior_fight_rate": 1.0,
    }
    cls, notes = m.pit_class(metric)
    assert cls == "PIT_SAFE"
    assert any("zero prior UFC fights" in x for x in notes)


def test_future_dominant_missingness_stays_potential_leakage():
    metric = {
        "diagnostic_rows": 100,
        "observed_side_win_rate": 0.70,
        "observed_more_prior_fights_rate": 0.45,
        "observed_more_future_fights_rate": 0.82,
        "future_minus_prior_more_fights_rate": 0.37,
        "mean_delta_prior_fights": 0.5,
        "mean_delta_future_fights": 3.0,
        "both_sides_have_prior_fight_rate": 0.6,
        "missing_side_zero_prior_fight_rate": 0.1,
    }
    assert m.pit_class(metric)[0] == "POTENTIAL_TEMPORAL_LEAKAGE"


def test_reach_helper_recognizes_broad_known_failure_pattern():
    old = pd.DataFrame({
        "fight_id": [str(i) for i in range(100)],
        "event_date": ["2017-01-01"] * 100,
        "fighter_1_win": [1] * 91 + [0] * 9,
        "f1__ctx__physical_size_profile__reach_cm": [180.0] * 100,
        "f2__ctx__physical_size_profile__reach_cm": [None] * 100,
    })
    new = old.copy()
    new["f2__ctx__physical_size_profile__reach_cm"] = 175.0
    result = m.full_f02_reach_control(old, new)
    assert result["framework_recognized_known_failure"] is True
    assert result["classification"] == "CONFIRMED_TEMPORAL_LEAKAGE"
