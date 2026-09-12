#!/usr/bin/env python3
"""Generate deterministic human/machine feature-governance reference views."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ufc_edge.features.contract import load_feature_catalog, materialized_feature_names  # noqa: E402
from ufc_edge.features.governance import load_governance, validate_repository_governance  # noqa: E402
from ufc_edge.features.state import active_v1_features, selected_v1_names  # noqa: E402


def load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build_inventory() -> dict[str, Any]:
    catalog = load_feature_catalog(ROOT)
    governance = load_governance(ROOT)
    by_name = {x["canonical_name"]: x for x in governance["features"]}
    active_names = {x["feature_name"] for x in active_v1_features(catalog)}
    f01_names = selected_v1_names(catalog)
    theoretical = materialized_feature_names(catalog)
    active_theoretical = [
        name for name in theoretical
        if any("__" + concept in name or name.endswith("__" + concept) for concept in active_names)
    ]
    concepts = []
    for feature in catalog["features"]:
        gov = by_name[feature["feature_name"]]
        concepts.append({
            "feature_id": gov["feature_id"],
            "canonical_name": feature["feature_name"],
            "semantic_version": gov["semantic_version"],
            "methodology_version": gov["methodology_version"],
            "layer": feature["layer"],
            "family": feature["family"],
            "contract_status": feature["status"],
            "lifecycle_state": gov["lifecycle_state"],
            "components": feature.get("components", []),
            "windows": [
                name for flag, name in (
                    ("career_variant", "career"), ("recent_3_variant", "last3"),
                    ("recent_5_variant", "last5"), ("ewma_variant", "ewma_365d")
                ) if feature[flag]
            ],
            "round_specific": feature["round_specific_variant"],
            "shrinkage_policy": feature["shrinkage_rule"],
            "canonical_inputs": feature["canonical_input_fields"],
            "elapsed_exposure_dependency": (feature.get("elapsed_exposure_source") or {}).get("source"),
            "matchup_dependency": feature["matchup_interaction_variant"],
            "opponent_adjusted_capability": feature["opponent_adjusted_variant"],
            "consumers": feature["intended_model_consumers"],
            "simulator_relevance": gov["simulator_relevance"],
            "implementation_locations": gov["implementation_locations"],
            "source_feature_ids": gov["source_feature_ids"],
        })
    return {
        "generated_view_version": 1,
        "feature_contract_version": catalog["feature_contract_version"],
        "governance_version": governance["governance_version"],
        "concept_count": len(concepts),
        "active_v1_concept_count": len(active_names),
        "f01_selected_value_count": len(f01_names),
        "catalog_declared_active_variant_count": len(active_theoretical),
        "fighter_state_context_value_count": 99,
        "matchup_interaction_value_count": 5,
        "concepts": concepts,
    }


def build_markdown(inventory: dict[str, Any]) -> str:
    requirements = load_json("features/data_requirements.json")
    simulator = load_json("features/simulator_requirements.json")
    rows = [
        "# UFC Edge Feature System Reference",
        "",
        "> GENERATED from the authoritative feature catalog + governance registries. Do not hand-edit.",
        "",
        f"- Feature contract: {inventory['feature_contract_version']}",
        f"- Governance version: {inventory['governance_version']}",
        f"- Durable concepts: **{inventory['concept_count']}**",
        f"- Active V1 concepts: **{inventory['active_v1_concept_count']}**",
        f"- F01-selected values: **{inventory['f01_selected_value_count']}** = 99 fighter-state/context + 5 matchup interactions",
        f"- Catalog-declared active variants (including round-specific declarations): **{inventory['catalog_declared_active_variant_count']}**",
        "",
        "## Authority map",
        "",
        "- Semantics/formulas/eligibility: features/feature_catalog.yaml",
        "- Stable IDs/lifecycle/methodology identity: features/feature_governance.json",
        "- Terminology: features/terminology.json",
        "- Dependency graph: features/dependencies.json",
        "- Known missing data: features/data_requirements.json",
        "- Simulator needs: features/simulator_requirements.json",
        "- Evolution history: features/migrations/feature_migrations.json",
        "- Runtime implementation: src/ufc_edge/features/",
        "- Generated inventory: features/feature_inventory.json",
        "",
        "## Concept inventory",
        "",
        "| Feature ID | Canonical name | Layer | Lifecycle | Contract status | Methodology | Consumers |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in inventory["concepts"]:
        consumers = ", ".join(item["consumers"]) or "—"
        rows.append(
            f"| {item['feature_id']} | {item['canonical_name']} | {item['layer']} | "
            f"{item['lifecycle_state']} | {item['contract_status']} | {item['methodology_version']} | {consumers} |"
        )
    rows += ["", "## Known missing-data requirements", ""]
    for item in requirements["requirements"]:
        rows += [
            f"### {item['requirement_id']} — {item['name']}",
            "",
            f"Status: **{item['status']}**. Priority: **{item['priority']}**.",
            "",
            "Forbidden substitutions: " + "; ".join(item["forbidden_substitutions"]) + ".",
            "",
        ]
    rows += ["## Simulator contract", ""]
    for state in simulator["states"]:
        blocked = ", ".join(state.get("blocked_by", []))
        suffix = f" Blocked by: {blocked}." if blocked else ""
        rows.append(f"- **{state['state']}** — {state['availability']}.{suffix}")
    rows += [
        "",
        "## Repository hygiene",
        "",
        "features/v0/, features/provenance/, legacy v0 builders/validators, and archived feature workflows are quarantined pre-F00 prior art. They are not semantic authorities and may not be consumed by new models without an explicit reviewed migration.",
        "",
        "New generated matrices, replay outputs, run directories, and feature stores remain runtime artifacts and are not committed by this foundation milestone.",
        "",
    ]
    return "\n".join(rows)


def render() -> tuple[str, str]:
    inventory = build_inventory()
    machine = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
    human = build_markdown(inventory)
    return machine, human


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    validate_repository_governance(ROOT)
    machine, human = render()
    outputs = {
        ROOT / "features/feature_inventory.json": machine,
        ROOT / "features/FEATURE_REFERENCE.md": human,
    }
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, expected in outputs.items()
                 if not path.exists() or path.read_text(encoding="utf-8") != expected]
        if stale:
            print("STALE_GENERATED_FEATURE_REFERENCE: " + ", ".join(stale))
            return 1
        print("FEATURE_REFERENCE_CURRENT")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print("FEATURE_REFERENCE_GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
