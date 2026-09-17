from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).parents[1] / "tools" / "features" / "audit_mov_bucket_input_temporal_safety_v1.py"
spec = importlib.util.spec_from_file_location("mov_audit", SCRIPT)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_era_assignment_boundaries():
    assert m.era(2015) == "2015-2018"
    assert m.era(2018) == "2015-2018"
    assert m.era(2019) == "2019-2022"
    assert m.era(2022) == "2019-2022"
    assert m.era(2023) == "2023-2024"
    assert m.era(2025) == "2025-2026"
    assert m.era(2014) is None


def test_missingness_calculation_is_pair_symmetric():
    f = pd.DataFrame({
        "event_date": pd.to_datetime(["2023-01-01", "2024-01-02", "2025-01-03"]),
        "x1": [1.0, None, None],
        "x2": [2.0, 3.0, None],
    })
    # coverage_table is independent of target/model outputs and counts the three states by year.
    rows = m.coverage_table(f.rename(columns={"x1": "a", "x2": "b"}), "a", "b")
    assert rows[0]["year"] == 2023 and rows[0]["both_observed"] == 1
    assert rows[1]["year"] == 2024 and rows[1]["both_observed"] == 0 and rows[1]["any_observed_rate"] == 1.0
    assert rows[2]["year"] == 2025 and rows[2]["any_observed_rate"] == 0.0


def test_pit_classifier_does_not_flag_on_target_association_alone():
    metric = {
        "diagnostic_rows": 100,
        "observed_side_win_rate": 0.90,
        "observed_more_future_fights_rate": 0.55,
        "observed_more_prior_fights_rate": 0.50,
        "future_minus_prior_more_fights_rate": 0.05,
        "mean_delta_future_fights": 0.4,
        "mean_delta_prior_fights": 0.3,
        "both_sides_have_prior_fight_rate": 0.10,
    }
    cls, _ = m.pit_class(metric)
    assert cls == "PIT_SAFE"


def test_future_dominant_availability_is_only_potential_without_provenance_confirmation():
    metric = {
        "diagnostic_rows": 100,
        "observed_side_win_rate": 0.70,
        "observed_more_future_fights_rate": 0.82,
        "observed_more_prior_fights_rate": 0.45,
        "future_minus_prior_more_fights_rate": 0.37,
        "mean_delta_future_fights": 3.0,
        "mean_delta_prior_fights": 0.5,
        "both_sides_have_prior_fight_rate": 0.60,
    }
    cls, _ = m.pit_class(metric)
    assert cls == "POTENTIAL_TEMPORAL_LEAKAGE"


def test_candidate_inventory_is_real_active_surface_contract():
    # This is intentionally exact: promotion/removal of a governed candidate must force audit review.
    assert "sig_strike_flow" in m.EXPECTED_CANDIDATES
    assert "control_rate" in m.EXPECTED_CANDIDATES
    assert "submission_attempt_rate" in m.EXPECTED_CANDIDATES
    assert "exact_ground_standing_time" not in m.EXPECTED_CANDIDATES


def test_orientation_metadata_distinguishes_matchup_from_fighter_pair():
    frame = pd.DataFrame(columns=[
        "f1__fs__knockdown_rate__created_per_15__career__shrunk",
        "f2__fs__knockdown_rate__created_per_15__career__shrunk",
        "mx__knockdown_creation_vs_vulnerability__f1_vs_f2__career__shrunk",
    ])
    dims = m.paired_dimensions(frame, m.EXPECTED_CANDIDATES)
    assert {d["orientation"] for d in dims} == {"fighter_pair", "matchup_oriented"}


def test_source_comparability_fails_positional_duration_closed():
    cls, _ = m.source_class("fake", {"canonical_inputs": {"fighter_round_position": []}}, {"2015-2018": 1.0, "2019-2022": 1.0, "2023-2024": 1.0, "2025-2026": 1.0})
    assert cls == "ERA_NONCOMPARABLE"


def test_hash_is_stable(tmp_path: Path):
    p = tmp_path / "x"
    p.write_text("deterministic\n", encoding="utf-8")
    assert m.sha256_file(p) == m.sha256_file(p)


def test_malformed_support_input_fails_closed(tmp_path: Path):
    root = tmp_path
    pd.DataFrame({"event_id": ["e1"], "event_date": ["2025-01-01"]}).to_csv(root / "events.csv", index=False)
    pd.DataFrame({"fight_id": ["f1"], "event_id": ["e1"]}).to_csv(root / "fights.csv", index=False)
    pd.DataFrame({"fight_id": ["f1"], "fighter_id": ["a"], "round": [1]}).to_csv(root / "fighter_round_stats.csv", index=False)
    with pytest.raises(RuntimeError, match="missing required negative-control fields"):
        m.support_lookup(root)
