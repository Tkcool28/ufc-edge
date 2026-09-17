#!/usr/bin/env python3
"""Stage A: construct V1 terrain using the permanently frozen percentile reference."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

VERSION = "MODEL_VALIDATION_BUCKET_CONTRACT_V1"
REFERENCE_VERSION = "MODEL_VALIDATION_PERCENTILE_REFERENCE_V1"
REFERENCE_GENERATION_METHOD = "POOLED_UFC_2015_2026_FIGHTER_SIDE_MIDRANK_RLE_V1"
REFERENCE_SHA256 = "c5a54e23e61c5b59f6e7c44c4de2c19652bdd664733001b126cddd41d66f89aa"
DEFAULT_REFERENCE_PATH = Path("governance/model_validation_bucket_v1/MODEL_VALIDATION_PERCENTILE_REFERENCE_V1.json")
PRESSURE_PERCENTILE_CUT = 0.75
OUTCOME_RE = re.compile(
    r"winner|(^|__)result($|__)|outcome|finish_method|(^|__)target($|__)|"
    r"probab|predict|correct|brier|log.loss|calibr",
    re.I,
)
RICH = {
    "strike": [
        "fs__knockdown_rate__created_per_15__career__shrunk",
        "fs__sig_strike_flow__landed_per_min__career__shrunk",
    ],
    "grapple": [
        "fs__submission_attempt_rate__created_per_15__career__shrunk",
        "fs__takedown_pressure__created_per_15__career__shrunk",
    ],
}
BASE = [
    "fight_id", "event_id", "event_date", "promotion", "fighter_1_id", "fighter_2_id",
    "scheduled_rounds", "ctx__title_bout", "f1__ctx__layoff_days", "f2__ctx__layoff_days",
    "f1__fs__prior_fight_count__career__raw", "f2__fs__prior_fight_count__career__raw",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), default=str) + "\n").encode()


def logical_hash(df: pd.DataFrame) -> str:
    rows = df.where(pd.notna(df), None).to_dict("records")
    return hashlib.sha256(canonical_json(rows)).hexdigest()


def safe_columns(schema: Path) -> list[str]:
    names = [x["name"] for x in json.loads(schema.read_text())["columns"]]
    cols = BASE + [f"f{side}__{name}" for side in (1, 2) for family in RICH.values() for name in family]
    missing = sorted(set(cols) - set(names))
    if missing:
        raise RuntimeError(f"required Stage-A F02 columns missing: {missing}")
    bad = [name for name in cols if OUTCOME_RE.search(name)]
    if bad:
        raise RuntimeError(f"prohibited Stage-A columns requested: {bad}")
    return cols


def bucket_experience(a: float, b: float) -> str:
    x = min(a, b)
    return "0" if x == 0 else "1–2" if x <= 2 else "3–5" if x <= 5 else "6–10" if x <= 10 else "11+"


def bucket_layoff(a: float, b: float) -> str:
    if pd.isna(a) or pd.isna(b):
        return "STRUCTURAL_NA_OR_UNKNOWN"
    x = max(float(a), float(b))
    return "< 6 months" if x < 183 else "6–12 months" if x < 365 else "12–18 months" if x < 548 else "18+ months"


def empirical_percentile(value: float, reference: np.ndarray) -> float:
    if pd.isna(value):
        return float("nan")
    if reference.size == 0:
        raise RuntimeError("empty percentile reference distribution")
    left = np.searchsorted(reference, float(value), side="left")
    right = np.searchsorted(reference, float(value), side="right")
    return float((left + right) / (2.0 * reference.size))


def pressure_score(values: list[float], references: list[np.ndarray]) -> float:
    if len(values) != len(references) or any(pd.isna(v) for v in values):
        return float("nan")
    return float(np.mean([empirical_percentile(v, ref) for v, ref in zip(values, references)]))


def classify(a: float, b: float, cut: float, prefix: str, f1: str, f2: str) -> tuple[str, str]:
    if pd.isna(a) or pd.isna(b):
        return "UNASSIGNABLE_BY_CONTRACT", "UNASSIGNABLE"
    left, right = float(a) >= cut, float(b) >= cut
    state = "LOW" if not left and not right else "ONE_SIDED" if left != right else "TWO_SIDED"
    direction = "BOTH" if left and right else f1 if left else f2 if right else "NONE"
    return f"{prefix}_{state}", direction


def distribution_summary(reference: np.ndarray, total_side_rows: int) -> dict[str, Any]:
    return {
        "observed": int(reference.size), "missing": int(total_side_rows - reference.size),
        "q25": float(np.quantile(reference, 0.25)), "q50": float(np.quantile(reference, 0.50)),
        "q75": float(np.quantile(reference, 0.75)), "q90": float(np.quantile(reference, 0.90)),
        "min": float(reference.min()), "max": float(reference.max()),
    }


def load_frozen_references(path: Path = DEFAULT_REFERENCE_PATH, expected_sha256: str = REFERENCE_SHA256) -> dict[str, np.ndarray]:
    path = Path(path)
    if not path.is_file():
        raise RuntimeError(f"frozen V1 percentile reference missing: {path}")
    actual_sha = sha(path)
    if actual_sha != expected_sha256:
        raise RuntimeError(f"frozen V1 percentile reference hash mismatch: {actual_sha}")
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:
        raise RuntimeError("frozen V1 percentile reference malformed JSON") from exc
    if payload.get("version") != REFERENCE_VERSION or payload.get("contract_version") != VERSION:
        raise RuntimeError("frozen V1 percentile reference version mismatch")
    if payload.get("generation_method_identity") != REFERENCE_GENERATION_METHOD:
        raise RuntimeError("frozen V1 percentile reference generation-method mismatch")
    expected_features = [name for family in RICH.values() for name in family]
    if set(payload.get("features", {})) != set(expected_features):
        raise RuntimeError("frozen V1 percentile reference feature set mismatch")
    references: dict[str, np.ndarray] = {}
    for family, names in RICH.items():
        for name in names:
            spec = payload["features"][name]
            runs = spec.get("run_length_values")
            if not isinstance(runs, list) or not runs:
                raise RuntimeError(f"malformed frozen percentile runs: {name}")
            values, counts = [], []
            previous = None
            for item in runs:
                if not isinstance(item, list) or len(item) != 2:
                    raise RuntimeError(f"malformed frozen percentile run: {name}")
                value, count = float(item[0]), int(item[1])
                if not np.isfinite(value) or count <= 0 or (previous is not None and value <= previous):
                    raise RuntimeError(f"invalid frozen percentile run ordering/value: {name}")
                previous = value
                values.append(value)
                counts.append(count)
            observed = int(spec.get("observed", -1))
            if sum(counts) != observed or observed <= 0:
                raise RuntimeError(f"frozen percentile observed count mismatch: {name}")
            references[f"{family}:{name}"] = np.repeat(np.asarray(values, dtype=float), np.asarray(counts, dtype=int))
    return references


def score_mov_environment_v1(fighter_1_values: dict[str, float], fighter_2_values: dict[str, float], reference_path: Path = DEFAULT_REFERENCE_PATH) -> dict[str, Any]:
    references = load_frozen_references(reference_path)
    component_percentiles: dict[str, dict[str, float]] = {"fighter_1": {}, "fighter_2": {}}
    for side_name, values in (("fighter_1", fighter_1_values), ("fighter_2", fighter_2_values)):
        for family, names in RICH.items():
            for name in names:
                component_percentiles[side_name][name] = empirical_percentile(values.get(name, float("nan")), references[f"{family}:{name}"])
    strike_refs = [references[f"strike:{n}"] for n in RICH["strike"]]
    grapple_refs = [references[f"grapple:{n}"] for n in RICH["grapple"]]
    sp1 = pressure_score([fighter_1_values.get(n, float("nan")) for n in RICH["strike"]], strike_refs)
    sp2 = pressure_score([fighter_2_values.get(n, float("nan")) for n in RICH["strike"]], strike_refs)
    gp1 = pressure_score([fighter_1_values.get(n, float("nan")) for n in RICH["grapple"]], grapple_refs)
    gp2 = pressure_score([fighter_2_values.get(n, float("nan")) for n in RICH["grapple"]], grapple_refs)
    strike_env, _ = classify(sp1, sp2, PRESSURE_PERCENTILE_CUT, "STRIKE", "fighter_1", "fighter_2")
    grapple_env, _ = classify(gp1, gp2, PRESSURE_PERCENTILE_CUT, "GRAPPLE", "fighter_1", "fighter_2")
    joint = "UNASSIGNABLE_BY_CONTRACT" if "UNASSIGNABLE_BY_CONTRACT" in (strike_env, grapple_env) else f"{strike_env}__{grapple_env}"
    return {"component_percentiles": component_percentiles, "strike_pressure": [sp1, sp2], "grapple_pressure": [gp1, gp2], "striking_environment": strike_env, "grappling_environment": grapple_env, "joint_mov_environment": joint}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--f02-dir", type=Path, required=True)
    ap.add_argument("--audit-marker", type=Path, required=True)
    ap.add_argument("--canonical-fights", type=Path, required=True)
    ap.add_argument("--percentile-reference", type=Path, default=DEFAULT_REFERENCE_PATH)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    marker = json.loads(args.audit_marker.read_text())
    if marker.get("final_recommendation") != "MOV_BUCKET_INPUTS_SAFE_FOR_BUCKET_CONTRACT_DESIGN":
        raise RuntimeError("approved MOV audit recommendation missing")
    f02_summary = json.loads((args.f02_dir / "summary.json").read_text())
    expected_logical = marker["governed_inputs"]["corrected_f02_predictor_logical_sha256"]
    expected_table = marker["governed_inputs"]["corrected_f02_table_sha256"]
    actual_logical = f02_summary.get("predictor_logical_sha256")
    actual_table = sha(args.f02_dir / "winner_modeling_table.parquet")
    if actual_logical != expected_logical or actual_table != expected_table:
        raise RuntimeError("corrected F02 identity does not match accepted MOV audit marker")

    references = load_frozen_references(args.percentile_reference)
    ref_payload = json.loads(args.percentile_reference.read_text())
    if ref_payload.get("source_f02_logical_sha256") != expected_logical or ref_payload.get("source_f02_table_sha256") != expected_table:
        raise RuntimeError("frozen V1 percentile reference source F02 identity mismatch")

    cols = safe_columns(args.f02_dir / "schema.json")
    df = pd.read_parquet(args.f02_dir / "winner_modeling_table.parquet", columns=cols)
    if any(OUTCOME_RE.search(c) for c in df.columns):
        raise RuntimeError("prohibited column entered Stage A")
    df["event_date"] = pd.to_datetime(df.event_date, errors="raise")
    df = df[df.promotion.eq("UFC") & df.event_date.dt.year.between(2015, 2026)].copy()
    if df.fight_id.duplicated().any():
        raise RuntimeError("duplicate canonical fight_id")
    if df[["fight_id", "event_date", "fighter_1_id", "fighter_2_id"]].isna().any().any():
        raise RuntimeError("malformed identity/date row")

    canonical_meta = pd.read_csv(args.canonical_fights, usecols=["fight_id", "weight_class"])
    if canonical_meta.fight_id.duplicated().any():
        raise RuntimeError("duplicate fight_id in canonical fights metadata")
    df = df.merge(canonical_meta, on="fight_id", how="left", validate="one_to_one")
    if df.weight_class.isna().any():
        raise RuntimeError(f"{int(df.weight_class.isna().sum())} Stage-A fights missing governed canonical weight class")

    total_side_rows = 2 * len(df)
    feature_evidence = {name: distribution_summary(references[f"{family}:{name}"], total_side_rows) for family, names in RICH.items() for name in names}
    rows: list[dict[str, Any]] = []
    strike_refs = [references[f"strike:{n}"] for n in RICH["strike"]]
    grapple_refs = [references[f"grapple:{n}"] for n in RICH["grapple"]]
    for record in df.itertuples(index=False):
        d = record._asdict()
        f1, f2 = str(d["fighter_1_id"]), str(d["fighter_2_id"])
        sp1 = pressure_score([d[f"f1__{n}"] for n in RICH["strike"]], strike_refs)
        sp2 = pressure_score([d[f"f2__{n}"] for n in RICH["strike"]], strike_refs)
        gp1 = pressure_score([d[f"f1__{n}"] for n in RICH["grapple"]], grapple_refs)
        gp2 = pressure_score([d[f"f2__{n}"] for n in RICH["grapple"]], grapple_refs)
        strike_env, strike_side = classify(sp1, sp2, PRESSURE_PERCENTILE_CUT, "STRIKE", f1, f2)
        grapple_env, grapple_side = classify(gp1, gp2, PRESSURE_PERCENTILE_CUT, "GRAPPLE", f1, f2)
        joint = "UNASSIGNABLE_BY_CONTRACT" if "UNASSIGNABLE_BY_CONTRACT" in (strike_env, grapple_env) else f"{strike_env}__{grapple_env}"
        present = sum(pd.notna(d[f"f{side}__{name}"]) for side in (1, 2) for name in RICH["strike"] + RICH["grapple"])
        completeness = "LOW_MISSINGNESS" if present == 8 else "MODERATE_MISSINGNESS" if present >= 6 else "HIGH_MISSINGNESS"
        rounds = d["scheduled_rounds"]
        if rounds not in (3, 5):
            raise RuntimeError(f"malformed scheduled_rounds for {d['fight_id']}")
        title = d["ctx__title_bout"]
        if title not in (True, False, 0, 1):
            raise RuntimeError(f"malformed title status for {d['fight_id']}")
        rows.append({
            "fight_id": d["fight_id"], "event_id": d["event_id"], "event_date": d["event_date"].date().isoformat(), "year": int(d["event_date"].year),
            "fighter_1_id": f1, "fighter_2_id": f2,
            "experience_bucket": bucket_experience(float(d["f1__fs__prior_fight_count__career__raw"]), float(d["f2__fs__prior_fight_count__career__raw"])),
            "layoff_bucket": bucket_layoff(d["f1__ctx__layoff_days"], d["f2__ctx__layoff_days"]),
            "scheduled_duration_bucket": f"{int(rounds)}_ROUND", "title_status": "TITLE_BOUT" if bool(title) else "NON_TITLE_BOUT", "weight_class": str(d["weight_class"]),
            "completeness_tier": completeness, "striking_environment": strike_env, "strike_pressure_side": strike_side,
            "grappling_environment": grapple_env, "grapple_pressure_side": grapple_side, "joint_mov_environment": joint,
            "mov_eligibility_status": "ASSIGNABLE" if joint != "UNASSIGNABLE_BY_CONTRACT" else "UNASSIGNABLE_BY_CONTRACT",
            "contract_version": VERSION, "source_f02_logical_sha256": expected_logical,
        })

    out = pd.DataFrame(rows).sort_values(["event_date", "fight_id"], kind="mergesort").reset_index(drop=True)
    if out.fight_id.duplicated().any():
        raise RuntimeError("duplicate fight identity after assignment")
    env_counts = {
        "striking_environment": out.striking_environment.value_counts(dropna=False).to_dict(),
        "grappling_environment": out.grappling_environment.value_counts(dropna=False).to_dict(),
        "joint_mov_environment": out.joint_mov_environment.value_counts(dropna=False).to_dict(),
        "mov_eligibility_status": out.mov_eligibility_status.value_counts(dropna=False).to_dict(),
        "completeness_tier": out.completeness_tier.value_counts(dropna=False).to_dict(),
    }
    evidence = {
        "status": "STAGE_A_THRESHOLD_SELECTION_EVIDENCE_V1",
        "inputs": "allowlisted corrected F02 pre-fight columns plus canonical fight_id/weight_class only",
        "outcomes_predictions_available": False,
        "method": "Each rich-stat component is independently converted to a pooled fighter-side mid-rank empirical percentile. Fighter pressure is the mean of the two dimensionless component percentiles. Elevated pressure is score >= 0.75.",
        "pressure_percentile_cut": PRESSURE_PERCENTILE_CUT,
        "rich_feature_subset": RICH,
        "feature_distributions": feature_evidence,
        "rows": len(df),
        "resulting_cell_counts": env_counts,
        "rejected_construction": "Direct averaging/pooling of unlike raw units is prohibited; the pre-acceptance Stage-A draft was replaced structurally without consulting bucket-specific model performance or MOV outcome rates.",
    }
    contract = {
        "version": VERSION, "canonical_order": "event_date ASC, fight_id ASC",
        "confidence_bins": [[0.50,0.55],[0.55,0.60],[0.60,0.65],[0.65,0.70],[0.70,0.75],[0.75,0.80],[0.80,0.85],[0.85,1.00]],
        "experience": "minimum fighter strict prior UFC count", "layoff": "maximum known strict pre-fight layoff; missing is explicit N/A",
        "weight_class": "exact governed canonical fights.csv weight_class joined by fight_id",
        "completeness": "approved four rich-stat concepts, 8 side-values: 8 LOW_MISSINGNESS, 6-7 MODERATE_MISSINGNESS, <=5 HIGH_MISSINGNESS; MODERATE_MISSINGNESS is a valid permanent V1 state with current frozen population N=0",
        "mov": evidence, "missing_rich_data": "UNASSIGNABLE_BY_CONTRACT; never LOW",
        "percentile_reference": {"path": str(DEFAULT_REFERENCE_PATH), "version": REFERENCE_VERSION, "sha256": REFERENCE_SHA256, "source_f02_logical_sha256": expected_logical, "source_f02_table_sha256": expected_table, "generation_method_identity": REFERENCE_GENERATION_METHOD, "scoring_rule": "V1 scoring MUST load this frozen reference and MUST NOT derive percentile references from the incoming scoring population"},
        "version_policy": "V1 is immutable after acceptance; changed thresholds or sources require V2",
        "sample_size_governance": {"normal":100,"moderate":50,"thin":25,"insufficient_below":25,"applies_to_all_future_models":True,"insufficient_interpretation":"N-only; suppress substantive performance interpretation while N<25"},
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    contract_path = args.output_dir / "MODEL_VALIDATION_BUCKET_CONTRACT_V1.json"
    evidence_path = args.output_dir / "threshold_selection_evidence_v1.json"
    assignment_path = args.output_dir / "MODEL_VALIDATION_BUCKET_ASSIGNMENTS_V1.csv"
    contract_path.write_bytes(canonical_json(contract))
    evidence_path.write_bytes(canonical_json(evidence))
    out.to_csv(assignment_path, index=False, lineterminator="\n")
    manifest = {
        "status":"MODEL_VALIDATION_BUCKET_CONTRACT_V1_COMPLETE","rows":len(out),"assignment_logical_sha256":logical_hash(out),"assignment_physical_sha256":sha(assignment_path),
        "contract_sha256":sha(contract_path),"threshold_evidence_sha256":sha(evidence_path),"source_f02_logical_sha256":expected_logical,"source_f02_table_sha256":actual_table,
        "canonical_fights_sha256":sha(args.canonical_fights),"audit_marker_sha256":sha(args.audit_marker),"generator_code_sha256":sha(Path(__file__)),
        "percentile_reference_path":str(DEFAULT_REFERENCE_PATH),"percentile_reference_version":REFERENCE_VERSION,"percentile_reference_sha256":REFERENCE_SHA256,"percentile_reference_generation_method_identity":REFERENCE_GENERATION_METHOD,
    }
    (args.output_dir / "manifest.json").write_bytes(canonical_json(manifest))
    print("MODEL_VALIDATION_BUCKET_CONTRACT_V1_COMPLETE")

if __name__ == "__main__":
    main()
