#!/usr/bin/env python3
"""Final fail-closed DATA phase gate for UFC Edge.

Runs existing contract/data/source validators, verifies every manifest file hash/byte count,
checks additive canonical table counts, requires final accepted-gap evidence, and confirms
status docs were refreshed. With --require-complete-marker it additionally requires the
final phase marker and machine precedence status.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/canonical/v0/manifest.json"
CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
PRECEDENCE = ROOT / "schemas/source_precedence_v0.json"
AUDIT = ROOT / "provenance/audits/data_phase_final_gate_latest.json"

VALIDATORS = [
    "pipelines/validate_canonical_contract.py",
    "pipelines/validate_source_field_map.py",
    "pipelines/validate_source_precedence.py",
    "pipelines/validate_canonical_data_v0.py",
]
REQUIRED_LOCKS = [
    "provenance/greco1899.lock.json",
    "provenance/tidytuesday_ufc_rankings.lock.json",
    "provenance/kaggle_pro_mma_fights.lock.json",
    "provenance/kaggle_pro_mma_fighters.lock.json",
]
REQUIRED_EVIDENCE = [
    "provenance/audits/canonical_core_v0_latest.json",
    "provenance/audits/canonical_fightmetric_position_v0_latest.json",
    "provenance/audits/canonical_rankings_v0_latest.json",
    "provenance/audits/canonical_ufc_profile_snapshots_v0_latest.json",
    "provenance/audits/canonical_external_mma_v0_latest.json",
    "provenance/audits/canonical_ufc_weigh_ins_v0_latest.json",
    "provenance/audits/official_scorecards_final_disposition_v0.json",
    "provenance/audits/unlinked_ufc_athlete_identity_v0_latest.json",
    "provenance/audits/unlinked_ufc_fightmetric_crosswalk_v0_latest.json",
]
DOCS = [
    "provenance/data_source_manifest.md",
    "provenance/free_source_sweep_2026-08-20.md",
]
COUNT_BY_PATH = {
    "data/canonical/v0/events.csv": "events",
    "data/canonical/v0/field_provenance.csv": "field_provenance",
    "data/canonical/v0/fighter_profile_snapshots.csv": "fighter_profile_snapshots",
    "data/canonical/v0/fighter_round_position.csv": "fighter_round_position",
    "data/canonical/v0/fighter_round_stats.csv": "fighter_round_stats",
    "data/canonical/v0/fighters.csv": "fighters",
    "data/canonical/v0/fights.csv": "fights",
    "data/canonical/v0/rankings.csv": "rankings",
    "data/canonical/v0/source_identity_links.csv": "source_identity_links",
    "data/canonical/v0/weigh_ins.csv": "weigh_ins",
}


def load(rel: str | Path):
    path = rel if isinstance(rel, Path) else ROOT / rel
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def run_validator(rel: str) -> str:
    proc = subprocess.run(["python", rel], cwd=ROOT, text=True, capture_output=True)
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        raise RuntimeError(f"validator failed {rel}: {output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-complete-marker", action="store_true")
    args = parser.parse_args()

    validator_outputs = {rel: run_validator(rel) for rel in VALIDATORS}
    manifest = load(MANIFEST)
    contract = load(CONTRACT)
    precedence = load(PRECEDENCE)

    if manifest.get("canonical_contract_version") != contract.get("contract_version"):
        raise RuntimeError("manifest/contract version mismatch")

    file_checks = []
    seen_paths = set()
    for item in manifest.get("files") or []:
        rel = str(item.get("path") or "")
        if not rel or rel in seen_paths:
            raise RuntimeError(f"missing/duplicate manifest path {rel!r}")
        seen_paths.add(rel)
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"manifest file missing {rel}")
        actual_bytes = path.stat().st_size
        actual_sha = sha256(path)
        if actual_bytes != int(item.get("bytes")):
            raise RuntimeError(f"manifest byte mismatch {rel}: {actual_bytes} != {item.get('bytes')}")
        if actual_sha != item.get("sha256"):
            raise RuntimeError(f"manifest sha256 mismatch {rel}")
        row_count = None
        count_key = COUNT_BY_PATH.get(rel)
        if count_key:
            row_count = csv_rows(path)
            if row_count != manifest.get("counts", {}).get(count_key):
                raise RuntimeError(f"manifest row-count mismatch {rel}: {row_count} != {manifest.get('counts', {}).get(count_key)}")
        file_checks.append({"path": rel, "bytes": actual_bytes, "sha256": actual_sha, "rows": row_count})

    missing_canonical_files = sorted(set(COUNT_BY_PATH) - seen_paths)
    if missing_canonical_files:
        raise RuntimeError(f"canonical files absent from manifest: {missing_canonical_files}")

    for rel in REQUIRED_LOCKS + REQUIRED_EVIDENCE:
        if not (ROOT / rel).is_file():
            raise RuntimeError(f"required provenance/evidence missing: {rel}")

    scorecard = load("provenance/audits/official_scorecards_final_disposition_v0.json")
    athlete = load("provenance/audits/unlinked_ufc_athlete_identity_v0_latest.json")
    fmcross = load("provenance/audits/unlinked_ufc_fightmetric_crosswalk_v0_latest.json")
    score_rule = [r for r in precedence.get("rules") or [] if r.get("family") == "official_judge_round_scores"]
    if len(score_rule) != 1 or score_rule[0].get("status") != "raw_qa_only":
        raise RuntimeError("official scorecard precedence is not final raw_qa_only")
    if (ROOT / "data/canonical/v0/judge_round_scores.csv").exists():
        raise RuntimeError("judge_round_scores.csv exists despite accepted RAW_QA_ONLY disposition")
    if fmcross.get("decision", {}).get("safe_to_accept_remaining_fight_identity_gap") is not True:
        raise RuntimeError("unlinked athlete stable-ID gap is not safe to accept")
    if int(athlete.get("meaningful_fight_identity_gap_nodes") or 0) != 423:
        raise RuntimeError("athlete identity-gap cardinality drift")

    for rel in DOCS:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if "<!-- DATA_PHASE_CURRENT_STATUS_START -->" not in text or "<!-- DATA_PHASE_CURRENT_STATUS_END -->" not in text:
            raise RuntimeError(f"current DATA status block missing from {rel}")

    if args.require_complete_marker:
        marker = ROOT / "DATA_PHASE_COMPLETE.md"
        if not marker.is_file():
            raise RuntimeError("DATA_PHASE_COMPLETE.md missing")
        if precedence.get("status") != "data_phase_complete":
            raise RuntimeError("source precedence top-level status is not data_phase_complete")
        marker_text = marker.read_text(encoding="utf-8")
        for required in ("DATA PHASE COMPLETE", "Accepted gaps", "RAW_QA_ONLY", "423"):
            if required not in marker_text:
                raise RuntimeError(f"completion marker lacks required text {required!r}")

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "final" if args.require_complete_marker else "preclose",
        "status": "pass",
        "canonical_contract_version": contract.get("contract_version"),
        "manifest_files_verified": len(file_checks),
        "manifest_counts": manifest.get("counts"),
        "validator_outputs": validator_outputs,
        "required_locks_verified": REQUIRED_LOCKS,
        "required_evidence_verified": REQUIRED_EVIDENCE,
        "scorecards": {"status": "raw_qa_only", "canonical_rows": 0},
        "accepted_identity_gap_nodes": athlete.get("meaningful_fight_identity_gap_nodes"),
        "stable_id_crosswalk_safe_to_accept_gap": True,
        "completion_marker_required": args.require_complete_marker,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
