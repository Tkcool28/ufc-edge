# UFC Edge — DATA PHASE COMPLETE

Completed: **2026-08-22 19:56:58 MDT**  
Canonical contract: **0.4.0-draft**  
Phase freeze: `provenance/data_phase_freeze_v0.json`

## DATA PHASE COMPLETE

The acquisition, identity, canonicalization, source-precedence, QA, and explicit-gap work required by `DATA_PHASE_HANDOFF.md` has reached its fail-closed phase boundary. This marker does **not** mean the dataset is perfect or exhaustive. It means unresolved items are now explicitly typed as accepted gaps or deferred/rejected sources rather than being silently pushed into feature engineering.

## Canonical v0 baseline

- Fighters: **4,600**
- Events: **1,014**
- Fights: **9,252**
- Classic fighter-round stats: **41,218**
- Official positional/TIP bucket rows: **32,156**
- Historical ranking observations: **99,077**
- Point-in-time official athlete profile snapshots: **2,466**
- Official fight-specific scale-weight observations: **12,890**
- Canonical identity links: **31,426**
- Field-provenance rows: **57,531**
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
2. **Official athlete identity coverage:** **1,693** official athlete nodes remain without a trusted canonical identity. **423** participate in official fight resources. This is explicitly accepted rather than resolved by names.
3. **FightMetric stable-ID follow-up:** **405/423** fight-participating unlinked athletes expose a FightMetric ID, but exact trusted source-ID matching produced **0** unique candidates and **0** ambiguous matches. No URL-token or name matching was used.
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
