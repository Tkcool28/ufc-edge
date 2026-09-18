from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOV0 = ROOT / "models" / "mov0"


def load(name: str):
    return json.loads((MOV0 / name).read_text(encoding="utf-8"))


def test_target_contract_and_draw_decision_handling():
    c = load("target_contract_v1.json")
    assert c["target_name"] == "STANDARD_FINISH"
    assert c["label"]["positive_when"]["method"] == ["KO_TKO", "SUBMISSION"]
    assert c["label"]["negative_when"]["method"] == ["DECISION"]
    assert "draw" in c["label"]["negative_when"]["result"]
    n = c["governed_evaluation_population"]["exact_counts"]
    assert (n["STANDARD_FINISH_1"], n["DECISION_0"], n["TOTAL"]) == (2822, 2836, 5658)
    assert n["DECISION_DRAWS_INCLUDED_AS_0"] == 45


def test_nc_dq_other_unknown_are_never_coerced():
    c = load("target_contract_v1.json")
    excluded = c["exclusions"]["method"]
    for method in ["DQ", "DRAW", "NO_CONTEST", "OTHER", "UNKNOWN", None]:
        assert method in excluded
    assert c["exclusions"]["no_coercion"] is True
    assert c["canonical_schema"]["overturned_enum_present"] is False


def test_surface_ladder_is_strict_and_career_only():
    s = load("feature_surface_v1.json")
    b0 = set(s["surfaces"]["B0"]["literal_f02_columns"])
    b1 = set(s["surfaces"]["B1"]["literal_f02_columns"])
    mn = set(s["surfaces"]["MOV0_MIN"]["literal_f02_columns"])
    full = set(s["surfaces"]["MOV0_FULL"]["literal_f02_columns"])
    assert b0 == set()
    assert b1 < mn < full
    for column in full:
        assert "__last3__" not in column
        assert "__last5__" not in column
        assert "__ewma_365d__" not in column
    assert len(full) == len(s["surfaces"]["MOV0_FULL"]["literal_f02_columns"])


def test_unapproved_ambiguous_concepts_are_absent():
    s = load("feature_surface_v1.json")
    full = s["surfaces"]["MOV0_FULL"]["literal_f02_columns"]
    assert not any("control_rate" in c for c in full)
    assert not any("reversal_rate" in c for c in full)
    decisions = {r["concept"]: r["decision"] for r in s["concept_review"]}
    assert decisions["control_rate"] == "DEFER"
    assert decisions["reversal_rate"] == "DEFER"


def test_fighter_order_invariance_is_mandatory():
    s = load("feature_surface_v1.json")
    inv = s["fighter_order_invariance"]
    assert inv["paired_numeric_transformations"] == ["mean(f1,f2)", "abs(f1-f2)"]
    assert "atol=1e-12" in inv["mandatory_future_test"]
    assert "rtol=0" in inv["mandatory_future_test"]


def test_no_new_missingness_predictors():
    s = load("feature_surface_v1.json")
    m = load("model_contract_v1.json")
    assert s["new_missingness_predictors_allowed"] is False
    assert m["preprocessing"]["missingness_indicators"] is False
    assert m["preprocessing"]["global_preprocessing"] is False


def test_ridge_grid_and_b0_are_frozen():
    m = load("model_contract_v1.json")
    spec = m["specification"]
    assert spec["penalty"] == "l2"
    assert spec["solver"] == "lbfgs"
    assert spec["C_grid"] == [0.03, 0.1, 0.3, 1.0]
    assert spec["selection_objective"] == "concatenated inner chronological log loss only"
    assert m["B0"]["global_future_prevalence_forbidden"] is True


def test_chronological_fold_integrity_and_counts():
    v = load("validation_plan_v1.json")
    folds = v["chronology"]["folds"]
    assert [f["outer_year"] for f in folds] == list(range(2015, 2027))
    assert sum(f["outer_validation_n"] for f in folds) == 5658
    for f in folds:
        assert len(f["inner_validation_years"]) == 2
        assert all(inner["year"] < f["outer_year"] for inner in f["inner_validation_years"])
    assert v["chronology"]["random_cv"] is False
    assert v["chronology"]["shuffle"] is False


def test_validation_terrain_is_join_only_and_immutable():
    v = load("validation_plan_v1.json")
    t = v["validation_terrain"]
    assert t["immutable_version"] == "MODEL_VALIDATION_BUCKET_CONTRACT_V1"
    assert t["regenerate"] is False
    assert t["join_key"] == "fight_id"
    assert t["assignment_logical_sha256"] == "a23b138ea103a751ae988cce5f90369b265547bfeec1c0e708484b4428015665"


def test_acceptance_framework_uses_only_allowed_classifications():
    a = load("acceptance_framework_v1.json")
    assert a["numeric_hard_thresholds"] is False
    assert a["allowed_classifications"] == [
        "CLEAR_SUCCESS", "INCONCLUSIVE", "CURRENT_SPECIFICATION_NOT_SUPPORTED"
    ]
    assert a["forbidden_conclusion"] == "FINISH_MODELING_FAILED"
