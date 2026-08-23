#!/usr/bin/env python3
"""Create the DATA phase completion marker and immutable phase-boundary hash freeze."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PRECEDENCE = ROOT / "schemas/source_precedence_v0.json"
MANIFEST = ROOT / "data/canonical/v0/manifest.json"
ATHLETES = ROOT / "provenance/audits/unlinked_ufc_athlete_identity_v0_latest.json"
FMCROSS = ROOT / "provenance/audits/unlinked_ufc_fightmetric_crosswalk_v0_latest.json"
FREEZE = ROOT / "provenance/data_phase_freeze_v0.json"
MARKER = ROOT / "DATA_PHASE_COMPLETE.md"
FREEZE_FILES = [
    "schemas/canonical_data_contract_v0.json",
    "schemas/source_field_map_v0.json",
    "schemas/source_precedence_v0.json",
    "data/canonical/v0/manifest.json",
    "provenance/data_source_manifest.md",
    "provenance/free_source_sweep_2026-08-20.md",
    "provenance/greco1899.lock.json",
    "provenance/tidytuesday_ufc_rankings.lock.json",
    "provenance/kaggle_pro_mma_fights.lock.json",
    "provenance/kaggle_pro_mma_fighters.lock.json",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    precedence = load(PRECEDENCE)
    manifest = load(MANIFEST)
    athletes = load(ATHLETES)
    fmcross = load(FMCROSS)

    rules = {r.get("family"): r for r in precedence.get("rules") or []}
    if rules.get("official_judge_round_scores", {}).get("status") != "raw_qa_only":
        raise RuntimeError("scorecards are not finalized raw_qa_only")
    if fmcross.get("decision", {}).get("safe_to_accept_remaining_fight_identity_gap") is not True:
        raise RuntimeError("identity gap is not finalizable")

    precedence["status"] = "data_phase_complete"
    PRECEDENCE.write_text(json.dumps(precedence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    frozen = []
    for rel in FREEZE_FILES:
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"freeze file missing: {rel}")
        frozen.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})

    completed_local = datetime.now(ZoneInfo("America/Denver"))
    freeze_payload = {
        "schema_version": 1,
        "phase": "DATA",
        "status": "complete",
        "completed_at_local": completed_local.isoformat(),
        "timezone": "America/Denver",
        "canonical_contract_version": manifest.get("canonical_contract_version"),
        "canonical_manifest_counts": manifest.get("counts"),
        "frozen_files": frozen,
        "freeze_rule": "These exact contract/source-map/precedence/manifest/status/provenance files define the DATA baseline for the first FEATURES phase. Changes require an explicit post-DATA migration, not silent editing.",
    }
    FREEZE.write_text(json.dumps(freeze_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    c = manifest["counts"]
    marker = f"""# UFC Edge — DATA PHASE COMPLETE

Completed: **{completed_local.strftime('%Y-%m-%d %H:%M:%S %Z')}**  
Canonical contract: **{manifest.get('canonical_contract_version')}**  
Phase freeze: `provenance/data_phase_freeze_v0.json`

## DATA PHASE COMPLETE

The acquisition, identity, canonicalization, source-precedence, QA, and explicit-gap work required by `DATA_PHASE_HANDOFF.md` has reached its fail-closed phase boundary. This marker does **not** mean the dataset is perfect or exhaustive. It means unresolved items are now explicitly typed as accepted gaps or deferred/rejected sources rather than being silently pushed into feature engineering.

## Canonical v0 baseline

- Fighters: **{c['fighters']:,}**
- Events: **{c['events']:,}**
- Fights: **{c['fights']:,}**
- Classic fighter-round stats: **{c['fighter_round_stats']:,}**
- Official positional/TIP bucket rows: **{c['fighter_round_position']:,}**
- Historical ranking observations: **{c['rankings']:,}**
- Point-in-time official athlete profile snapshots: **{c['fighter_profile_snapshots']:,}**
- Official fight-specific scale-weight observations: **{c['weigh_ins']:,}**
- Canonical identity links: **{c['source_identity_links']:,}**
- Field-provenance rows: **{c['field_provenance']:,}**
- Official judge-round scores: **0** — intentionally not promoted.

## Final source-family dispositions

### CANONICAL

- Greco1899/UFCStats historical identity, fight, result and classic round-count backbone under audited precedence.
- Official UFC FightMetric eligible positional/TIP **quantized bucket** fields; exact control seconds remain Greco/UFCStats.
- TidyTuesday/fightr historical rankings as dated observations with strict past-only use.
- Official UFC athlete profile point-in-time subset linked through trusted stable identity.
- `binduvr/pro-mma-fights` clean Bellator/ONE cross-promotion subset after identity, duplicate and UFC-overlap gates.
- `binduvr/pro-mma-fighters` only where it supplies trusted external fighter identity links; later career-total snapshot fields are not historical backfill.
- Official UFC fight-specific weigh-in scale weights after article/fight/fighter context gates.

### RAW_QA_ONLY

- Official UFC scorecard pages/images and every derived OCR/geometry/judge-reconciliation artifact. Strict promotion failed, so no judge-round scores are canonical.
- UFC-DataLab scorecard OCR; known OCR/fighter-pair association defects prohibit authority use.
- ESPN MMA raw additive layer except where used strictly as independent QA evidence; it does not overwrite higher-precedence canonical values.
- Any source fields whose semantics remain provisional/unresolved in `schemas/source_field_map_v0.json`.

### DEFERRED_ACCESS_GATED

- FightGeek PRECISION/SPEED sequential action data.
- IMG/Sportradar licensed live/rich feeds.
- Stats Fight bulk extraction until a reliable permitted bulk route exists.
- BestFightOdds market data, intentionally deferred to a later market/value track rather than core fight-outcome inputs.

### REJECTED

- MMA Decisions bulk canonical acquisition under the current conservative robots policy; reference-only unless access policy changes.
- CageIntel as a dead/parked lead.
- Live blogs as canonical event chronology.
- Roster/listed weights and UFC fight-node corner weight fields as substitutes for fight-specific scale weights.
- Any display-name-only fighter identity construction.

## Accepted gaps

1. **Judge scorecards:** official material is archived, but the strongest physical-grid three-round extraction test recovered only 82/270 strict score cells, with **0/15** complete cards and **0** complete nine-pair cards. This remains **RAW_QA_ONLY**.
2. **Official athlete identity coverage:** **{athletes['unlinked_official_athlete_nodes']:,}** official athlete nodes remain without a trusted canonical identity. **{athletes['meaningful_fight_identity_gap_nodes']:,}** participate in official fight resources. This is explicitly accepted rather than resolved by names.
3. **FightMetric stable-ID follow-up:** **{fmcross['fight_history_unlinked_with_fightmetric_id']:,}/{fmcross['fight_history_unlinked_rows']:,}** fight-participating unlinked athletes expose a FightMetric ID, but exact trusted source-ID matching produced **0** unique candidates and **0** ambiguous matches. No URL-token or name matching was used.
4. **Historical UFC spine:** lower-precedence external-MMA QA identified UFC-labelled trusted-pair bouts absent from the canonical UFC spine. They remain documented coverage gaps; lower-precedence data was deliberately not used to repair higher-precedence UFC history.
5. **Rankings provenance/use constraint:** the TidyTuesday source lock records that a dataset-specific upstream license was not fully disambiguated. Keep this snapshot to private research/modeling unless upstream terms are clarified.
6. **Missingness and era coverage:** official rich positional fields are genuinely sparse in older eras and some fields disappear in recent eras. Missing remains missing; no zero/imputation semantics are introduced by DATA.

## Frozen rules carried into FEATURES

- Missing is not zero.
- No future leakage; rankings/profiles are point-in-time observations.
- Display-name-only identity is not trusted.
- Raw snapshots are immutable.
- Lower-precedence sources never silently overwrite higher-precedence present values.
- Page-local weigh-in markers are not global semantic codes.
- Official scorecard OCR is not canonical score authority.
- FightMetric positional time is quantized bucket evidence, not exact seconds.
- Any change to the frozen contract/source map/precedence/manifest baseline requires an explicit migration.

## Next phase

**STOP DATA here.** The next work should begin feature-family design from the frozen canonical contracts and manifest. Do not resume source hunting merely because a feature would be convenient to have.
"""
    MARKER.write_text(marker, encoding="utf-8")
    print(f"DATA_PHASE_FINALIZED contract={manifest.get('canonical_contract_version')} freeze_files={len(frozen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
