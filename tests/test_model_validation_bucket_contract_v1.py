import math

import numpy as np
import pandas as pd

from tools.validation.build_bucket_assignment_v1 import (
    OUTCOME_RE,
    bucket_experience,
    bucket_layoff,
    classify,
    empirical_percentile,
    logical_hash,
    pressure_score,
)
from tools.validation.run_m1_calibration_diagnostic_v1 import (
    confidence_bucket,
    gate,
    method_category,
)


def test_experience_boundaries_are_exact():
    assert [bucket_experience(x, x) for x in (0, 1, 2, 3, 5, 6, 10, 11)] == [
        "0",
        "1–2",
        "1–2",
        "3–5",
        "3–5",
        "6–10",
        "6–10",
        "11+",
    ]


def test_layoff_boundaries_are_exact():
    assert [bucket_layoff(x, x) for x in (182, 183, 364, 365, 547, 548)] == [
        "< 6 months",
        "6–12 months",
        "6–12 months",
        "12–18 months",
        "12–18 months",
        "18+ months",
    ]
    assert bucket_layoff(float("nan"), 100) == "STRUCTURAL_NA_OR_UNKNOWN"


def test_confidence_bin_edges_are_exact():
    assert confidence_bucket(0.50) == "50–55%"
    assert confidence_bucket(0.5499999) == "50–55%"
    assert confidence_bucket(0.55) == "55–60%"
    assert confidence_bucket(0.60) == "60–65%"
    assert confidence_bucket(0.65) == "65–70%"
    assert confidence_bucket(0.70) == "70–75%"
    assert confidence_bucket(0.75) == "75–80%"
    assert confidence_bucket(0.80) == "80–85%"
    assert confidence_bucket(0.85) == "85%+"
    assert confidence_bucket(1.0) == "85%+"


def test_environment_is_swap_invariant_and_direction_follows_fighter_identity():
    left = classify(0.8, 0.2, 0.5, "STRIKE", "a", "b")
    right = classify(0.2, 0.8, 0.5, "STRIKE", "b", "a")
    assert left[0] == right[0] == "STRIKE_ONE_SIDED"
    assert left[1] == right[1] == "a"
    assert classify(0.8, 0.8, 0.5, "STRIKE", "a", "b") == (
        "STRIKE_TWO_SIDED",
        "BOTH",
    )
    assert classify(0.2, 0.2, 0.5, "STRIKE", "a", "b") == (
        "STRIKE_LOW",
        "NONE",
    )


def test_missing_rich_component_is_unassignable_not_low():
    assert classify(float("nan"), 0.1, 0.5, "GRAPPLE", "a", "b") == (
        "UNASSIGNABLE_BY_CONTRACT",
        "UNASSIGNABLE",
    )
    refs = [np.asarray([1.0, 2.0, 3.0]), np.asarray([10.0, 20.0, 30.0])]
    assert math.isnan(pressure_score([1.0, float("nan")], refs))


def test_component_normalization_is_scale_invariant():
    ref_a = np.asarray([1.0, 2.0, 3.0, 4.0])
    ref_b = np.asarray([10.0, 20.0, 30.0, 40.0])
    assert empirical_percentile(3.0, ref_a) == empirical_percentile(30.0, ref_b)
    score_a = pressure_score([3.0, 30.0], [ref_a, ref_b])
    score_b = pressure_score([300.0, 0.03], [ref_a * 100.0, ref_b / 1000.0])
    assert score_a == score_b


def test_stage_a_prohibited_column_families_are_detected():
    prohibited = [
        "winner_id",
        "finish_method",
        "target",
        "m1_probability",
        "brier",
        "calibration_gap",
    ]
    assert all(OUTCOME_RE.search(name) for name in prohibited)
    assert not OUTCOME_RE.search("fs__knockdown_rate__created_per_15__career__shrunk")


def test_sample_size_gates():
    assert gate(100) == "NORMAL"
    assert gate(99) == "MODERATE_UNCERTAINTY"
    assert gate(50) == "MODERATE_UNCERTAINTY"
    assert gate(49) == "THIN_EXPLORATORY"
    assert gate(25) == "THIN_EXPLORATORY"
    assert gate(24) == "INSUFFICIENT_SAMPLE"


def test_mov_method_categories_are_explicit():
    assert method_category("KO_TKO") == "KO_TKO"
    assert method_category("SUBMISSION") == "SUBMISSION"
    assert method_category("DECISION") == "DECISION"
    assert method_category("DQ") == "OTHER"
    assert method_category(None) == "OTHER"


def test_logical_hash_is_stable_for_identical_canonical_rows():
    df = pd.DataFrame(
        [
            {"event_date": "2026-01-01", "fight_id": "a", "bucket": "LOW"},
            {"event_date": "2026-01-02", "fight_id": "b", "bucket": "HIGH"},
        ]
    )
    assert logical_hash(df) == logical_hash(df.copy())


def test_logical_hash_changes_when_assignment_changes():
    left = pd.DataFrame([{"fight_id": "a", "bucket": "LOW"}])
    right = pd.DataFrame([{"fight_id": "a", "bucket": "HIGH"}])
    assert logical_hash(left) != logical_hash(right)
