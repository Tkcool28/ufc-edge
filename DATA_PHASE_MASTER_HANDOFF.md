# UFC Edge — DATA Phase Complete Handoff to Master Chat

**Repository:** `Tkcool28/ufc-edge`  
**DATA phase completed:** 2026-08-22 19:57:54 MDT  
**Frozen canonical contract:** `0.4.0-draft`  
**Formal completion marker:** `DATA_PHASE_COMPLETE.md`  
**Freeze record:** `provenance/data_phase_freeze_v0.json`

---

## 1. Executive handoff

The UFC Edge DATA foundation is complete and frozen for the first modeling cycle.

The phase covered:

- raw-source acquisition and immutable snapshot storage;
- source-specific manifests and locks;
- source semantics research and QA;
- stable fighter/event/fight identity construction;
- source-field mapping;
- source precedence;
- canonical table construction;
- exclusion/quarantine handling;
- temporal-use rules;
- explicit accepted gaps;
- final freeze of the contracts, source map, precedence, canonical manifest, and provenance records.

The completion marker does **not** claim every conceivable MMA/UFC field is available or every source is exhaustive. It means the usable DATA baseline is now explicit, reproducible, fail-closed, and safe to hand to later feature/model work without silently guessing identities, inventing units, converting missing values to zero, or pulling future observations backward in time.

**Important phase correction:** feature engineering was accidentally started after the DATA completion marker. That work has been stopped and fully contained under `features/`. It is not part of the DATA freeze. No feature-specific workflow remains active under `.github/workflows/`.

---

## 2. Repo storage model — where the data lives

The repo intentionally separates source evidence, canonical data, derived QA/intermediates, provenance, schemas, acquisition/build code, and later feature work.

```text
ufc-edge/
├── DATA_PHASE_COMPLETE.md
├── DATA_PHASE_MASTER_HANDOFF.md
├── data/
│   ├── raw/                 # immutable provider/source-native snapshots
│   ├── canonical/
│   │   └── v0/             # source-neutral frozen canonical DATA tables
│   └── derived/             # reproducible QA/discovery/intermediate DATA artifacts
├── provenance/
│   ├── audits/              # DATA-source audits and semantic/coverage evidence
│   ├── runs/                # DATA acquisition/build run logs + status records
│   ├── *.lock.json          # pinned external-source revision/license manifests
│   ├── data_source_manifest.md
│   └── data_phase_freeze_v0.json
├── schemas/
│   ├── canonical_data_contract_v0.json/.md
│   ├── source_adapter_contract_v0.md
│   ├── source_field_map_v0.json
│   └── source_precedence_v0.json
├── pipelines/               # DATA ingestion, canonicalization, audit, validation code
├── src/ufc_edge/data/       # reusable DATA parsing/manifest utilities
└── features/                # INACTIVE; post-DATA feature work quarantined here only
```

### Storage rule: `data/raw/`

`data/raw/` is immutable and source-native.

Raw snapshots are **not rewritten to look canonical**. Provider field names, source IDs, source formatting, coarse units, nulls, article text, downloaded images, and source-specific quirks are retained so every later transformation can be traced back to original evidence.

The normal shape is:

```text
data/raw/<source_family>/<snapshot_or_revision>/...
```

Where appropriate, each snapshot has its own manifest. Source locks under `provenance/` pin external repo commit/version/license information.

### Storage rule: `data/canonical/v0/`

This is the main source-neutral DATA interface for later work.

Downstream code should consume canonical field names and IDs rather than provider-specific names. Provider vocabulary is expected to die at the adapter/canonical boundary.

The canonical manifest is:

`data/canonical/v0/manifest.json`

It records:

- canonical contract version;
- row counts;
- output file paths;
- byte sizes;
- SHA-256 hashes;
- snapshot IDs for key sources;
- final semantic rules.

### Storage rule: `data/derived/`

`data/derived/` is for reproducible non-feature intermediates, discovery outputs, exclusions, and QA.

It is **not** the trusted modeling interface and it is **not raw evidence**. It exists so audits and canonical-build decisions can be inspected and reproduced without polluting either `data/raw/` or canonical tables.

Important final exclusion/QA examples referenced by the canonical manifest include:

- `data/derived/qa/canonical_core_exclusions_v0.csv`
- `data/derived/qa/canonical_external_mma_exclusions_v0.csv`
- `data/derived/qa/canonical_fightmetric_position_exclusions_v0.csv`
- `data/derived/qa/canonical_rankings_exclusions_v0.csv`
- `data/derived/qa/canonical_ufc_profile_snapshot_exclusions_v0.csv`
- `data/derived/qa/canonical_ufc_weigh_in_exclusions_v0.csv`

### Storage rule: `provenance/`

Global `provenance/` is now DATA-only again.

It contains source locks, acquisition research, semantic audits, canonical-build evidence, status logs, source-manifest documentation, and the frozen DATA definition.

The most important file for establishing the exact DATA baseline is:

`provenance/data_phase_freeze_v0.json`

The freeze hashes the exact contract/source-map/precedence/manifest/provenance files that define the completed DATA baseline. Silent edits after this point are not allowed; changes require an explicit post-DATA migration/version change.

---

## 3. Frozen canonical v0 baseline

The final `data/canonical/v0/manifest.json` reports:

| Canonical family | Rows |
|---|---:|
| fighters | **4,600** |
| events | **1,014** |
| fights | **9,252** |
| fighter round classic stats | **41,218** |
| fighter round position/TIP | **32,156** |
| rankings | **99,077** |
| fighter profile snapshots | **2,466** |
| source identity links | **31,426** |
| field provenance | **57,531** |
| weigh-ins | **12,890** |
| canonical judge-round scores | **0** |

Additional exclusion counts recorded in the manifest include:

- core exclusions: **570**
- FightMetric position exclusions: **5,955**
- ranking exclusions: **1,400**
- official UFC profile snapshot exclusions: **5**
- official UFC weigh-in exclusions: **2**
- external-MMA exclusions: **9,965**

### Canonical files

The v0 manifest binds these principal source-neutral files:

- `data/canonical/v0/fighters.csv`
- `data/canonical/v0/events.csv`
- `data/canonical/v0/fights.csv`
- `data/canonical/v0/fighter_round_stats.csv`
- `data/canonical/v0/fighter_round_position.csv`
- `data/canonical/v0/rankings.csv`
- `data/canonical/v0/fighter_profile_snapshots.csv`
- `data/canonical/v0/source_identity_links.csv`
- `data/canonical/v0/field_provenance.csv`
- `data/canonical/v0/weigh_ins.csv`
- `data/canonical/v0/manifest.json`

The manifest carries exact SHA-256 hashes for the canonical outputs and referenced QA exclusions.

---

## 4. Source-by-source storage and final role

## 4.1 Greco1899 / UFCStats — canonical historical backbone

Pinned source:

- repository: `Greco1899/scrape_ufc_stats`
- source commit: `8e40eb945e1127bf0ef172ab211a34787948f312`
- lock: `provenance/greco1899.lock.json`
- raw snapshot: `data/raw/greco1899/8e40eb945e11/`

Raw files preserved there:

- `ufc_event_details.csv` — event identity/date/location
- `ufc_fight_details.csv` — event-to-bout identity + fight URL
- `ufc_fight_results.csv` — result, weight class, method, ending round/time, metadata
- `ufc_fight_stats.csv` — round-level fighter statistics
- `ufc_fighter_details.csv` — fighter identity/name/nickname/UFCStats URL
- `ufc_fighter_tott.csv` — tale-of-the-tape profile data such as height/reach/stance/DOB

Final DATA role:

- default historical transport for shared classic UFC round counts;
- stable UFCStats source URLs and trusted identity support;
- exact control time in seconds where available;
- outcomes/results/history backbone under the frozen source-precedence policy.

Important semantic rule: Greco red/blue ordering is transport structure, not a predictive feature or fighter identity.

---

## 4.2 Official UFC FightMetric — canonical positional/TIP bucket evidence

Raw snapshot:

`data/raw/ufc_fightmetric_official/20260820T123046Z/`

Observed source surface included:

- **57,382** raw `fight_stat` rows;
- **1,148** pages;
- **8,008** distinct non-null FightMetric IDs;
- **54,187** identified rows;
- rich positional/TIP fields with genuine era/field-specific missingness.

Critical resolved semantics:

### Round 0

`round=0` is the source-provided whole-fight/per-fighter summary row, **not a real round**.

Canonical rule:

- never emit round 0 as an actual canonical fighter-round row;
- preserve source-summary evidence for QA;
- derive fight totals from valid rounds 1+.

### Numeric color

Audit established source transport mapping:

- `0 = red`
- `1 = blue`

This mapping is transport-only.

### Position/control time

Official archived positional/TIP time fields are coarse/quantized bucket evidence. They are **not exact elapsed seconds**.

Canonical rule:

- do not manufacture precise seconds from bucket values;
- use Greco/UFCStats precise `control_sec` where exact control seconds are available;
- keep eligible official positional values with their true coarse semantics.

### Duplicate/conflicting source versions

Conflicting FightMetric source versions were audited rather than silently resolved with a blanket “newest row wins” rule. Ambiguous source-only values remain fail-closed/quarantined unless the canonical precedence rules explicitly allow them.

Final role:

- eligible rich positional/TIP fields are canonical with explicit quantized semantics;
- shared classic historical counts remain owned by the frozen Greco-based transport unless explicitly migrated.

---

## 4.3 Official UFC fights/events/athletes JSON resources — identity/context spine

Raw namespace:

`data/raw/ufc_com_resources/`

Resources are stored separately beneath that namespace, e.g.:

```text
data/raw/ufc_com_resources/
├── fights/<snapshot>/...
├── events/<snapshot>/...
└── athletes/<snapshot>/...
```

The per-resource acquisition design is deliberate: fights, events, and athletes commit independently so one slow/failing resource cannot erase completed raw collections.

The final athlete source snapshot referenced by the canonical manifest is:

`data/raw/ufc_com_resources/athletes/20260820T194553Z/`

Official resource relationships provide important stable identity bridges:

- official UFC resource UUIDs;
- FightMetric IDs where source-explicit;
- red/blue athlete relationships;
- event relationships;
- event/date context.

Final canonical athlete profile subset:

- official athlete nodes: **4,161**
- trusted official athlete links: **2,468**
- canonical profile snapshots: **2,466**

Official profiles are **point-in-time observations**, not historical backfill.

---

## 4.4 ESPN MMA — immutable raw/additive QA layer

Raw snapshot:

`data/raw/espn_mma/20260820T123114Z/`

Acquired coverage included:

- **911** UFC events;
- **9,412** competitions;
- event discovery spanning 1993–2026;
- officials;
- plays;
- competitor statistics;
- position advances;
- control time;
- striking splits;
- judge totals;
- result context.

Final role: `RAW_QA_ONLY` / additive QA.

ESPN may provide independent corroboration or later additive fields, but it does not silently overwrite higher-precedence canonical values merely because it has a similarly named field.

ESPN judge identities were used as independent reconciliation/spelling evidence during scorecard QA, never as score authority.

---

## 4.5 Historical rankings — canonical dated observations

Pinned source:

- repository: `rfordatascience/tidytuesday`
- source commit: `107ff6c70de02dd807169e13aee7dc9d86ff88b6`
- upstream lineage noted as `benyamindsmith/fightr`
- lock: `provenance/tidytuesday_ufc_rankings.lock.json`
- raw snapshot: `data/raw/tidytuesday_ufc_rankings/107ff6c70de0/`

Raw preserved files include:

- `ufc_rankings_dataset.csv`
- `ufc_rankings_dataset.md`
- `UPSTREAM_INTRO.md`

Canonical output:

- **99,077** dated ranking observations.

Critical time rule:

For historical use, only a ranking observation strictly before the target information cutoff may be used. **Nearest-future ranking is forbidden.**

Provenance/license note:

The lock explicitly records that a dataset-specific upstream license was not fully disambiguated. Keep the snapshot for private research/modeling unless upstream terms are clarified.

---

## 4.6 External MMA / cross-promotion history — canonical clean subset

Fight source:

- Kaggle handle: `binduvr/pro-mma-fights`
- version: 1
- CC0/Public Domain as displayed by Kaggle
- lock: `provenance/kaggle_pro_mma_fights.lock.json`
- raw snapshot: `data/raw/kaggle_pro_mma_fights/v1/`
- raw source rows: **10,448**

Companion fighter source:

- Kaggle handle: `binduvr/pro-mma-fighters`
- version: 1
- CC0/Public Domain
- lock: `provenance/kaggle_pro_mma_fighters.lock.json`
- raw snapshot: `data/raw/kaggle_pro_mma_fighters/v1/`
- raw source profiles: **5,151**

Final canonical fight contribution:

- **483 non-UFC fights** retained after identity/duplicate/UFC-overlap rules;
  - **466 Bellator**
  - **17 ONE**

Important safeguards:

- UFC-labelled external rows are lower precedence and do not repair/overwrite the canonical UFC historical spine;
- one duplicate source fight key / two rows was quarantined;
- source fighter profiles help identity resolution but their career totals are a 2021 snapshot and are **never historical backfill**;
- historical experience must be reconstructed chronologically from fight rows.

---

## 4.7 Official UFC weigh-ins — canonical fight-specific scale weights

Official article-family raw snapshot:

`data/raw/ufc_official_articles/20260821T210000Z/weigh_in/`

Acquisition produced a gap-free official family snapshot from public UFC news/index pages after the blocked JSON:API article route was correctly abandoned rather than bypassed.

Final source snapshot had **12,892** candidate scale-weight rows. Two contaminating Strikeforce-context rows were excluded, leaving:

- **12,890** canonical weigh-in observations;
- **6,445** fights;
- **2,249** fighters.

Canonical weigh-in output promotes only safely supported information such as:

- canonical observation ID;
- canonical fight ID;
- canonical fighter ID;
- source-explicit scale weight.

The following are **not globally inferred** unless source-explicit and safely modeled later:

- contract limit;
- missed-weight status;
- pounds over;
- catchweight semantics;
- attempt number;
- purse penalty;
- inferred weigh-in date from article publication time.

There were **172 marker-bearing raw values**. Markers remain page-local/source-native evidence; no global marker-code semantics were invented.

UFC fight-node red/blue corner weight fields were explicitly rejected as substitutes for actual scale weights.

---

## 4.8 Official UFC scorecards — archived raw evidence, no canonical scores

Official scorecard article-family raw snapshot:

`data/raw/ufc_official_articles/20260821T210000Z/scorecard/`

Official selected scorecard image archive:

`data/raw/ufc_official_scorecard_images/selected_v0/images/`

Final official image acquisition/identity state:

- 582 eligible official UFC news pages fetched;
- **578** high-confidence selected scorecard images;
- images mapped to **575 canonical fights**;
- archive approximately 39.9 MB;
- 492 JPEG / 86 PNG;
- hashes verified.

Raw images are authoritative evidence. OCR and geometry are QA only.

A large sequence of extraction strategies was tested, including whole-page OCR, targeted OCR, numeric grid geometry, adaptive round labels, physical grid detection, row topology, and strict physical-grid score-cell OCR.

The final strict three-round physical-grid sample produced:

- 15 eligible cards;
- 270 expected score cells;
- **82** strict accepted cells;
- accepted fraction ≈ 30.37%;
- **0/15** cards with all 18 cells;
- **0** complete nine-pair cards.

Therefore final disposition is intentionally:

**`RAW_QA_ONLY`**

Canonical judge-round score rows: **0**.

Rules:

- no missing-cell imputation;
- no OCR token-order semantics promoted to score truth;
- no partial-card canonicalization;
- no global fighter-side orientation assumption without a strict per-card gate;
- ESPN identity/judge spelling evidence is not score authority;
- UFC-DataLab OCR is QA-only due known association defects.

Do not restart scorecard OCR merely by lowering thresholds. A materially new source/method is required before reopening this gap.

---

## 5. Identity storage and rules

Canonical identity mapping is materialized primarily in:

`data/canonical/v0/source_identity_links.csv`

Final count: **31,426** source identity links.

The canonical layer uses stable source IDs/URLs/UUIDs and audited crosswalks whenever possible.

Hard rule:

**Display-name-only matching is not trusted identity.**

Name normalization can be used as a fail-closed transport/discovery aid, but it may not silently create a trusted canonical fighter link.

### Accepted official-athlete identity gap

Official athlete nodes: **4,161**  
Trusted official athlete links: **2,468**  
Unlinked official athlete nodes: **1,693**

Among unlinked nodes:

- 423 participate in official fight resources;
- 405/423 of those expose a source-explicit FightMetric ID;
- exact matching against already trusted source IDs found **0 unique exact candidates** and **0 ambiguous exact candidates**.

No URL-token matching or display-name matching was used to force those identities.

This gap is accepted and documented rather than hidden.

---

## 6. Field provenance and precedence

Canonical field-level sourcing/conflict evidence is stored in:

`data/canonical/v0/field_provenance.csv`

Final rows: **57,531**.

Machine-readable precedence authority:

`schemas/source_precedence_v0.json`

Machine-readable provider→canonical mapping authority:

`schemas/source_field_map_v0.json`

Core principle:

**Lower-precedence sources never silently overwrite a present higher-precedence canonical value.**

The field-provenance table is intentionally a sparse override/conflict ledger rather than a requirement to repeat trivial provenance on every canonical cell.

---

## 7. Canonical contract and hard semantic rules

Machine-readable canonical contract:

`schemas/canonical_data_contract_v0.json`

Human-readable companion:

`schemas/canonical_data_contract_v0.md`

Frozen version: **`0.4.0-draft`**.

Rules that must survive downstream:

1. **Missing is not zero.**
2. **No future leakage.** Dated rankings/profile observations retain their temporal meaning.
3. **Display-name-only identity is not trusted.**
4. **Raw snapshots are immutable.**
5. **Provider names die at the adapter boundary.** Downstream code consumes canonical semantics.
6. **Lower precedence cannot silently overwrite higher precedence.**
7. **FightMetric round 0 is not a real round.**
8. **FightMetric positional time is quantized evidence, not exact seconds.**
9. **Greco/UFCStats owns exact control seconds where available.**
10. **Official UFC profile data is point-in-time, not historical backfill.**
11. **Historical rankings are dated observations, not precomputed features.**
12. **Official weigh-in article publication time is not automatically the weigh-in date.**
13. **Weigh-in markers are not universal semantic codes.**
14. **Official scorecard OCR is not canonical score authority.**
15. **Ambiguous identities are quarantined rather than guessed.**
16. **Any silent change to frozen contract/map/precedence/manifest is prohibited.** Use an explicit migration/version change.

---

## 8. Freeze record — what exactly is immutable

`provenance/data_phase_freeze_v0.json` marks DATA as `complete` and records hashes for the files that define the baseline.

Frozen core files include:

- `schemas/canonical_data_contract_v0.json`
- `schemas/source_field_map_v0.json`
- `schemas/source_precedence_v0.json`
- `data/canonical/v0/manifest.json`
- `provenance/data_source_manifest.md`
- `provenance/free_source_sweep_2026-08-20.md`
- `provenance/greco1899.lock.json`
- `provenance/tidytuesday_ufc_rankings.lock.json`
- `provenance/kaggle_pro_mma_fights.lock.json`
- `provenance/kaggle_pro_mma_fighters.lock.json`

The freeze rule states that these exact files define the DATA baseline and changes require an explicit post-DATA migration rather than silent editing.

---

## 9. Accepted gaps — do not mistake these for unfinished tasks

### A. Judge round scores

Official pages/images are archived, but extraction did not satisfy the strict canonical gate. Result: **0 canonical judge-round rows**.

This is an accepted gap, not a reason to weaken OCR/validation.

### B. Official athlete identity completeness

**1,693** official athlete nodes remain unlinked; **423** participate in official fight resources. Exact stable-ID follow-up did not produce a safe crosswalk.

Accepted gap. Do not force names.

### C. Historical UFC spine completeness

Lower-precedence external MMA data surfaced UFC-labelled fights absent from the higher-precedence canonical UFC spine. Those are documented coverage gaps and were deliberately not used to repair UFC history.

### D. Ranking source-license ambiguity

The TidyTuesday/fightr snapshot is retained with explicit provenance, but dataset-specific upstream licensing was not fully disambiguated. Keep use private/research until clarified.

### E. Rich positional era missingness

Official rich positional fields have real era/field gaps. Missing values remain missing. DATA introduced no hidden zero or imputation semantics.

---

## 10. Sources intentionally deferred or rejected

### Deferred/access-gated

- FightGeek PRECISION/SPEED sequential-action data;
- IMG/Sportradar rich/live licensed feeds;
- Stats Fight bulk access until a reliable permitted route exists;
- BestFightOdds/historical prices for a separate later market/value track.

### Rejected / reference-only

- MMA Decisions bulk canonical ingestion under the current conservative robots policy;
- CageIntel dead/parked lead;
- live blogs as canonical chronology;
- roster/listed weights as fight-specific scale weights;
- UFC fight-node corner weights as official scale results;
- display-name-only identity creation.

---

## 11. DATA vs FEATURES boundary after cleanup

After DATA was correctly completed, feature work was accidentally started. That work has now been contained instead of deleted.

Everything from that accidental feature phase is under:

`features/`

including:

```text
features/
├── README.md                 # explicitly marks feature work INACTIVE/QUARANTINED
├── feature_contract_v0.json
├── family_a_striking_v0.json
├── build_*.py / validate_*.py
├── v0/                       # accidental materialized feature outputs
├── provenance/
│   ├── audits/               # feature-only audits
│   └── runs/                 # feature-only run logs/status
└── workflows/
    └── archive/              # disabled copies of former feature Actions workflows
```

The three feature-specific GitHub Actions workflows were removed from `.github/workflows/` and archived under `features/workflows/archive/`.

A diff from the DATA freeze commit forward now shows every net feature-phase file under `features/` only. No `data/raw/`, `data/canonical/`, DATA schema, or global DATA provenance file was changed by that feature work.

Therefore:

- `features/` is **not part of DATA**;
- feature work is **stopped**;
- the DATA baseline remains the freeze defined in `provenance/data_phase_freeze_v0.json`;
- master chat may decide separately when/how to reopen FEATURES.

---

## 12. What master chat should treat as the official DATA interface

For downstream project planning, start from these files in this order:

1. `DATA_PHASE_COMPLETE.md` — final completion marker and source-family dispositions.
2. `DATA_PHASE_MASTER_HANDOFF.md` — this storage/architecture handoff.
3. `provenance/data_phase_freeze_v0.json` — immutable freeze hashes/counts.
4. `data/canonical/v0/manifest.json` — canonical output inventory, row counts, file hashes, source snapshot IDs.
5. `schemas/canonical_data_contract_v0.json` — canonical grains/fields/semantics.
6. `schemas/source_field_map_v0.json` — provider→canonical field mapping/status.
7. `schemas/source_precedence_v0.json` — source ownership/override rules.
8. `data/canonical/v0/*.csv` — actual canonical DATA tables.
9. `data/canonical/v0/field_provenance.csv` — conflicts/overrides provenance.
10. `data/canonical/v0/source_identity_links.csv` — trusted source identity crosswalks.
11. `provenance/data_source_manifest.md` — deeper source acquisition/QA history.
12. Source-specific raw manifests/locks/audits only when tracing a canonical value back to evidence.

Do **not** start from `features/` when reviewing the completed DATA phase.

---

## 13. Final DATA-phase verdict

**DATA_PHASE_COMPLETE**

The repo now has a clean, frozen, source-traceable UFC/MMA DATA foundation with:

- immutable raw evidence;
- explicit source revisions;
- source-neutral canonical tables;
- audited identities;
- explicit source precedence;
- explicit null/missingness semantics;
- chronological/as-of rules;
- raw-vs-derived-vs-canonical separation;
- accepted gaps instead of guessed values;
- feature work physically/logically separated from DATA.

The correct next action for master chat is **project-level planning**: decide what phase to open next and what modeling/feature objective to authorize. DATA itself should not be reopened merely because a later feature would be convenient.
