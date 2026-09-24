from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "diagnostics" / "run_mov0_conditional_feature_interaction_archetype_v1.py"


def load():
    spec = importlib.util.spec_from_file_location("mov0_archetype_diag", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_is_frozen_oof_only_and_preregistered():
    mod = load()
    text = SCRIPT.read_text(encoding="utf-8")
    assert mod.STATUS == "MOV0_CONDITIONAL_FEATURE_INTERACTION_ARCHETYPE_DIAGNOSTIC_V1_COMPLETE"
    assert "from ufc_edge.models.mov0 import" not in text
    assert "FittedSurface" not in text
    assert len(mod.ARCHETYPES) == 15
    assert {family for _, family, _ in mod.ARCHETYPES} == {"striking", "grappling", "mixed", "survival"}
    assert [label for label, _, _ in mod.BUCKETS] == ["<0.30", "0.30–<0.40", "0.40–<0.50", "0.50–<0.60", "0.60–<0.70", ">=0.70"]


def test_fixed_governance_and_wilson_interval():
    mod = load()
    assert [mod.gate(n) for n in (100, 50, 25, 24)] == ["NORMAL", "MODERATE_UNCERTAINTY", "THIN_EXPLORATORY", "INSUFFICIENT"]
    lo, hi = mod.wilson(50, 100)
    assert 0 < lo < .5 < hi < 1
