# UFC Edge — Data Phase Handoff

**Handoff date:** 2026-08-22 America/Denver  
**Repository:** `Tkcool28/ufc-edge`  
**Current project architecture:** one repo for data → features → models → backtests.  
**Current chat/phase boundary:** DATA FOUNDATION ONLY. Do not start feature engineering until the data checklist below is explicitly closed.

> **START HERE IN THE NEXT CHAT:** Re-read this file, then inspect current `main` HEAD and recent bot commits before doing anything. At handoff, the latest observed commit was `cd890788daa2113ecf8cb0ebe9fff469763b7979` (`Audit official UFC weigh-in annotation semantics`). GitHub Actions previously triggered may have advanced `main`, so repo state always wins over this timestamp.

---

## 1. Operating discipline that worked well and should continue

The most important part of this phase has been process, not just scraping data.

1. **Fail closed.** A source, mapping, or transformation is not accepted because it looks plausible.
2. **Distinguish three states:**
   - code exists;
   - runner completed;
   - canonical output accepted.
   Never collapse those into one status.
3. **Green GitHub Action is not sufficient.** Verify the committed raw/canonical artifact and manifest.
4. **Self-report runners.** Long or important Actions should commit a compact result JSON + log even on failure. Do not allow silent timeouts.
5. **Raw stays immutable and source-native.** Normalize through adapters; never rewrite raw provider data to “look canonical.”
6. **Missing is not zero.** Missing/404/null is coverage evidence unless the source explicitly encodes zero.
7. **No display-name-only trusted identity.** Use stable source IDs/URLs/UUIDs and audited crosswalks. Name normalization can be a fail-closed transport aid, not primary identity truth.
8. **No look-ahead.** Dated rankings/profile observations must remain observations. Historical use must use only information available before the target cutoff.
9. **Do not invent units.** If a source gives coarse/quantized measurements, preserve that resolution. Never convert a minute bucket into fake exact seconds.
10. **Search before reverse-engineering semantics when possible.** Example: FightMetric `round=0` was searched externally, then internally proved.
11. **If an audit gives a technically successful but semantically empty result, treat it as failure.** Example: the first UFC↔Greco script aligned 6,904 fights but compared zero round keys because `color` was numeric 0/1 rather than strings.
12. **Keep the repo shallow and traceable.**
    - `data/raw/` = immutable provider snapshots
    - `data/canonical/` = source-neutral contracted tables
    - `data/derived/` = reproducible non-feature intermediates/QA/discovery
    - `provenance/` = sourcing rules, audits, logs, manifests, research notes
    - `schemas/` = canonical contracts, source maps, precedence rules
    - `pipelines/` = ingestion/audit/build code
    - `src/ufc_edge/data/` = reusable normalization/manifest utilities
    - `features/` = reserved for the NEXT chat/phase
13. **Do not weaken a validator to make data pass.** Fix the mapping/data assumption instead.
14. **Document mistakes/corrections.** Several errors caught during this phase prevented bad definitions from becoming permanent.

---

## 2. One-repo architecture / canonical flow

The intended flow is:

```text
SOURCE-NATIVE RAW
  UFC / Greco / ESPN / rankings / external MMA / official content
        ↓
SOURCE ADAPTERS + IDENTITY RESOLUTION
        ↓
SOURCE FIELD MAP + SOURCE PRECEDENCE
        ↓
CANONICAL CONTRACT
        ↓
CANONICAL TABLES
        ↓
FEATURES (NEXT CHAT)
        ↓
MODELS / SIMULATOR
```

Provider-specific field names must die at the adapter boundary. Downstream code should see one definition, e.g. `sig_strikes_landed`, not `SIG.STR.` vs `sig_str_land` vs ESPN naming.

---

## 3. Core contracts and guards already built

Important durable files:

- `schemas/canonical_data_contract_v0.md`
- `schemas/canonical_data_contract_v0.json`
- `schemas/source_adapter_contract_v0.md`
- `schemas/source_field_map_v0.json`
- `schemas/source_precedence_v0.json`
- `pipelines/validate_canonical_contract.py`
- `pipelines/validate_source_field_map.py`
- source-precedence validator/workflow
- `src/ufc_edge/data/parsing.py`
- `src/ufc_edge/data/manifest_readers.py`
- tests for strict parsing/manifest behavior

Current canonical contract observed in repo: **`0.3.0-draft`**.  
Current source-precedence contract observed: **`0.2.0-draft`**.

The source-map validation previously reported a clean gate and deliberately retains verified/provisional/unresolved/rejected states instead of coercing unknown mappings.

---

## 4. Canonical v0 already exists

Current `data/canonical/v0/manifest.json` reports:

| Table / artifact | Rows |
|---|---:|
| `fighters` | 4,600 |
| `events` | 784 |
| `fights` | 8,769 |
| `fighter_round_stats` | 41,218 |
| `fighter_round_position` | 32,156 |
| `fighter_profile_snapshots` | 2,466 |
| `rankings` | 99,077 |
| `source_identity_links` | 30,347 |
| core exclusions | 570 |
| position exclusions | 5,955 |
| ranking exclusions | 1,400 |
| UFC profile snapshot exclusions | 5 |

Current manifest rules include:

- Greco is the default historical transport for **shared classic round counts** in canonical v0.
- Greco provides **exact control seconds** where available.
- Official UFC FightMetric positional data is preserved as **quantized buckets**, not falsely converted to exact seconds.
- round 0 is forbidden from actual canonical fighter-round rows.
- rankings are dated observations, not features.
- UFC athlete profiles are point-in-time snapshots, not historical backfill.
- ambiguous identities are quarantined.

### Canonical profile snapshot build

Official UFC athlete profile snapshot build completed successfully:

- raw official athletes: 4,161
- trusted official athlete links: 2,468
- canonical profile rows: 2,466
- exclusions: 5
- no display-name matching
- no historical backfill
- `stats_weight == 0` treated as missing
- current status/style/gym/weight-class/profile fields remain point-in-time observations

---

## 5. Sources acquired and what they are for

### A. Greco1899 / UFCStats — INGESTED, currently canonical shared-round backbone

Pinned source repo: `Greco1899/scrape_ufc_stats`  
Pinned source commit: `8e40eb945e1127bf0ef172ab211a34787948f312`

Raw namespace:
`data/raw/greco1899/8e40eb945e11/`

Files:
- event details
- fight details
- fight results
- fight round stats
- fighter details
- fighter TOTT

Current role:
- primary canonical v0 transport for shared historical round counts;
- precise control time seconds;
- stable UFCStats URLs/identity fallback;
- QA/redundancy against official UFC.

Do **not** silently replace this transport in canonical v0. Source precedence explicitly says changing the shared-round primary requires an explicit dataset version/migration.

### B. Official UFC FightMetric `fight_stat` — INGESTED + SEMANTICS AUDITED

Raw snapshot:
`data/raw/ufc_fightmetric_official/20260820T123046Z/`

Verified raw surface:
- 57,382 rows
- 1,148 pages
- 8,008 distinct non-null FightMetric IDs
- 54,187 identified rows (94.432%)
- 3,195 unidentified rows are effectively empty Drupal placeholders: only internal ID populated, no fightmetric ID/color/round; raw/QA-only
- rich positional/TIP fields exist, though coverage is era/field dependent

Important semantics proven:

#### `round=0`
Externally searched; no explicit modern UFC sentence found. Historical FightMetric datasets showed whole-fight totals stored separately from round-specific values. Internal full-data additivity audits strongly prove modern `round=0` is the per-fighter **fight-summary row**, not a real round.

Canonical rule:
- exclude round 0 from fighter-round tables;
- preserve as QA/source summary;
- derive modeling totals from actual rounds 1+.

#### Numeric `color`
Proven by audit over 250,782 shared comparisons:
- `0 = red`
- `1 = blue`
- correct orientation exact fraction: **99.566%**
- reversed orientation: **11.725%**

This is a transport mapping only; canonical data should use red/blue semantics, not 0/1.

#### UFC FightMetric vs Greco shared round counts
Conservative identity alignment:
- 6,904 exact aligned fights
- 32,638 aligned Greco fighter-round keys
- **32,612** matched FightMetric fighter-round keys
- most shared count fields agree around **99.35%–100% exact**
- examples: TD landed ~99.923%, TD attempts ~99.802%, most strike splits ~99.5%+

This demonstrates the official archive and Greco/UFCStats are fundamentally the same underlying stat lineage with small version/correction differences.

#### Archived TIP/control time resolution
The Drupal FightMetric time fields are small integers, not exact M:SS seconds.

Direct comparison of archived `control_time` to Greco precise seconds:
- `raw == floor(Greco_seconds / 60)` on **97.454%** of 23,876 comparisons
- other candidate interpretations were much worse

Rule:
- do not convert these buckets into fake exact seconds;
- Greco precise `control_sec` owns precise control where available;
- official positional bucket data may still be valuable for simulator state/exposure, with explicit coarse resolution.

#### Conflicting official FightMetric versions
Full raw duplicate audit found **714 conflicting `(fightmetric_id,color,round)` keys across 109 fight IDs**. Newer Drupal rows usually contain more populated/TIP fields, but no blanket “newest wins” rule is allowed.

The later Greco-scored overlap found among the compared duplicate keys:
- newest strict best: 268
- newest tied best: 1
- newest not best: 1

This is strong evidence of enrichment/correction but **not enough for an automatic global newest-row rule**. Current canonical policy keeps clean Greco shared counts and quarantines ambiguous official-only TIP fields until a dedicated resolver is explicitly promoted.

### C. Official UFC fights/events/athletes JSON:API — INGESTED

After fixing pagination and all-or-nothing acquisition problems, complete official resources landed.

Key lessons:
- initial monolithic collector successfully got athletes/events then timed out on fights;
- resource-scoped commits fixed that;
- `created` sorting was not unique and caused offset page overlap;
- deterministic Drupal NID ordering solved full fight pagination;
- manifests, not assumed directory shapes, are the source of truth.

Official fight nodes provide the direct identity bridge:
- UFC fight UUID
- FightMetric ID on a large majority of fights
- red/blue athlete UUID relationships
- event relationships/date bridge

Official UFC should be the preferred identity spine where relationships are direct and unambiguous. Canonical v0 can retain trusted Greco identity where official relations are missing/conflicting.

### D. ESPN MMA — INGESTED RAW / ADDITIVE-QA

Snapshot:
`data/raw/espn_mma/20260820T123114Z/`

Coverage:
- 911 UFC events
- 9,412 competitions
- 1993–2026 discovery
- officials + plays for all competitions
- 18,794 successful competitor-stat responses / 28 404s

Useful surfaces:
- officials/referees
- position advances (`advanceToBack`, `advanceToMount`, etc.)
- control time
- distance/clinch/ground splits
- judge totals
- result context
- sparse structural play events

Role remains additive/QA unless a specific ESPN field/grain gets separately promoted. Do not map by matching field names alone.

### E. Historical UFC rankings — INGESTED + CANONICALIZED

Raw TidyTuesday/fightr snapshot begins 2013-02-04.

Canonical rows: 99,077; exclusions: 1,400.

Rule: store dated observations. Historical downstream use may use only observations strictly **before** target cutoff. Never nearest future ranking.

### F. Cross-promotion history — INGESTED RAW, semantics audited, canonical insertion still pending

`binduvr/pro-mma-fights`:
- 10,448 UFC/Bellator/ONE fights
- source through 2021-08-11
- CC0

`binduvr/pro-mma-fighters`:
- 5,151 profiles
- 22 fields
- CC0

Latest transport audit:
- all 10,448 fight dates match abbreviated-month MDY such as `Aug 7, 2021`
- 1,006 distinct source event URLs map to 1,006 event signatures
- no event URL maps to multiple event signatures
- `(event URL, match_nr)` is a strong fight-key candidate except **1 duplicate pair / 2 rows**, which must be quarantined

**IMPORTANT OPEN CONSISTENCY BUG:** `schemas/source_precedence_v0.json` was written before the latest external-MMA date correction and contains older wording about slash-date DMY interpretation. The latest transport audit shows the actual dataset uses abbreviated-month MDY for all 10,448 rows. Reconcile the precedence contract to the latest audit before canonicalizing external fights.

Career totals in the companion fighter dataset are 2021 snapshot values and remain forbidden as historical backfill.

### G. Official UFC weigh-in pages — RAW ARCHIVE ACQUIRED

The blocked JSON:API article collection (403) was not bypassed. A legitimate public path was found through UFC sitemap/index pages.

Raw family snapshot:
`data/raw/ufc_official_articles/20260821T210000Z/weigh_in/`

Manifest:
- **716 candidate pages/items**
- all **716 HTTP 200**
- complete gap-free family snapshot
- source: official UFC public news pages

Earlier shortcut rejected:
`red_corner_fight_weight` / `blue_corner_fight_weight` on fight nodes are **not actual scale weights**. Real examples showed contracted/class weights rather than official scale results (e.g. Chase Hooper node 155 vs official 157.5; Kevin Borjas 126 vs official 129). Never map those fight-node fields into canonical weigh-ins.

Structured candidate extraction exists (`data/derived/discovery/ufc_weigh_in_rows_candidate.csv`).

Latest observed code-only stopping point:
`pipelines/audit_ufc_weigh_in_annotations.py` was added at commit `cd890788...` to inventory explicit miss/catchweight/purse/second-attempt language. **At handoff this audit script exists, but no completed audit result was observed yet.** Do not claim its annotation rules are promoted.

Scale weights are source-explicit candidates. Contract limit/miss/pounds-over/catchweight/purse/attempt semantics must be promoted only after exact fight/fighter identity + language/marker QA.

### H. Official UFC scorecard pages — RAW ARCHIVE ACQUIRED

Raw family snapshot:
`data/raw/ufc_official_articles/20260821T210000Z/scorecard/`

Manifest:
- 583 catalog family rows before URL gate
- 582 eligible official UFC news URLs
- 1 navigation/non-news row excluded
- **582 pages/items**
- all **582 HTTP 200**
- complete family snapshot

Current rule:
- raw page acquisition is complete;
- canonical judge-round scores are NOT complete;
- scorecard image/text extraction must resolve fight + fighter + judge + round and pass plausibility checks;
- OCR output alone is never canonical.

UFC-DataLab OCR scorecard snapshot remains raw/QA-only because obvious OCR/fighter-pair association errors were found.

MMA Decisions was investigated but kept reference-only under the conservative robots policy.

### I. Other/deferred sources

- BestFightOdds: later market-data track only, never core forecast input.
- FightGeek PRECISION/SPEED: future access-gated sequential source.
- IMG/Sportradar: future licensed rich/live source.
- Stats Fight: rich but bulk access unresolved.
- CageIntel: dead lead/domain parked.

Sequential action data is NOT blocking initial models because official rich TIP/position data is much stronger than expected.

---

## 6. Source precedence currently intended

Current `schemas/source_precedence_v0.json` should remain the machine-readable authority after it is refreshed for the external-MMA date correction and any weigh-in/scorecard promotions.

Current conceptual ownership:

| Data family | Canonical/current owner | Secondary / QA |
|---|---|---|
| UFC fight/event/fighter identity | official UFC when direct/unambiguous | Greco, ESPN |
| Shared classic round counts | **Greco/UFCStats in canonical v0** | official UFC, ESPN |
| Exact control seconds | **Greco/UFCStats** | ESPN QA |
| Rich positional/TIP buckets | **Official UFC FightMetric**, only where identity/version eligibility passes | ESPN position advances; future IMG |
| Current profile snapshots | official UFC | other sources QA |
| Historical rankings | TidyTuesday/fightr dated snapshot | external benchmark only |
| Cross-promotion fights | CC0 dataset, **pending canonical identity/dedup** | broader future source |
| Fight-specific weigh-ins | official UFC content, **raw acquired / QA pending** | no canonical fallback yet |
| Judge round scores | official UFC scorecard content, **raw acquired / QA pending** | OCR raw/QA only |

---

## 7. Important mistakes caught — preserve these lessons

These are not embarrassing footnotes; they are why the architecture is safer now.

1. **Advertised UFC `node/article` JSON:API resource ≠ readable collection.** It returned 403. We rejected that route instead of bypassing it and later found legitimate sitemap/index routes.
2. **OCR scorecards looked usable until sample inspection exposed wrong fighter-pair associations.** Kept raw-only.
3. **FightMetric `round=0` looked mysterious.** External search + full-data additivity proved it is a fight summary, not an actual round.
4. **First UFC fight bulk job looked like an endpoint problem.** It was really an all-or-nothing/timeout architecture problem.
5. **Lean fight requests still timed out.** The collection was simply large.
6. **Chunked fight pagination using non-unique `created` ordering produced cross-page duplicate IDs.** We did not dedupe them away; deterministic NID ordering fixed pagination correctly.
7. **First UFC↔Greco audit technically succeeded but compared zero round rows.** Cause: official `color` is numeric 0/1, not red/blue strings.
8. **Color orientation was not guessed.** 0=red/1=blue was proven over 250k shared comparisons.
9. **Archived UFC position/control fields looked like times but were small integers.** We did not assume seconds. Greco comparison proved they behave like floored whole-minute buckets.
10. **UFC fight-node weight fields looked like perfect weigh-in data.** Real examples disproved it; shortcut rejected.
11. **Manifest-reader assumptions broke one audit.** Fixed by reading declared manifest page paths instead of relying on directory shape.
12. **A remembered FightMetric count seemed inconsistent with repo docs.** Re-reading the immutable manifest showed memory was wrong; good docs were left untouched.
13. **External MMA date interpretation was corrected.** Latest audit shows `Aug 7, 2021` style abbreviated-month MDY for all 10,448 rows. Update stale precedence wording before canonical insertion.

---

## 8. Known stale documentation

`provenance/data_source_manifest.md` is valuable historically but its top-level status table is **stale** relative to current repo state. It still describes official fights acquisition as running and weigh-ins/scorecards as unresolved, while those raw archives are now complete and canonical v0 exists.

**Early next-chat task:** refresh `provenance/data_source_manifest.md` and `provenance/free_source_sweep_2026-08-20.md` from current manifests/audits. Do not throw away the historical notes; update statuses and evidence paths.

---

## 9. Exact remaining work before this DATA chat/phase can be closed

### Priority 1 — finish official weigh-in canonicalization

1. Run/inspect `pipelines/audit_ufc_weigh_in_annotations.py` with durable diagnostics.
2. Audit structured candidate rows for exact page/event/fight/fighter identity.
3. Promote only source-explicit semantics:
   - scale weight
   - actual attempt number if explicit
   - missed weight only if explicit or supported by a separately audited contract-limit rule
   - pounds over only when source-explicit or separately justified
   - catchweight only when source-explicit
   - purse penalty only when source-explicit
4. Never infer contract limits from weight class until a separate rules table handles title/non-title/commission allowances correctly.
5. Build canonical `weigh_ins` table + exclusions + manifest + provenance.

### Priority 2 — finish official scorecard canonicalization

1. Audit page structure and scorecard image/source links across the 582 archived official pages.
2. Determine whether official scorecard content can be parsed without risky OCR; if images require OCR, keep source image identity and validate aggressively.
3. Resolve event/fight/fighter/judge identities.
4. Enforce score plausibility (0–10, paired judge-round structure, actual fight rounds only).
5. Build canonical `judge_round_scores` + exclusions + provenance.
6. Keep UFC-DataLab OCR only as QA/recovery, never authority.

### Priority 3 — canonicalize cross-promotion fight history

1. Fix `schemas/source_precedence_v0.json` to reflect the latest abbreviated-month MDY audit.
2. Promote audited source event URL as event identity candidate.
3. Promote `(event URL, match_nr)` fight identity with the 1 duplicate pair quarantined.
4. Resolve external fighter profile URLs ↔ canonical fighters.
5. Deduplicate UFC overlap against canonical UFC fights.
6. Insert only clean outside-UFC history into canonical events/fights/identity links.
7. Preserve source organization and method/detail strings; normalize through explicit mapping, not ad hoc text rules.

### Priority 4 — close identity/profile gaps intentionally

Official profile build links 2,468 of 4,161 UFC athlete nodes into canonical identities; 1,693 remain unlinked. Decide whether those are mostly inactive/legacy/non-UFC/no-Greco-history records or whether a meaningful identity gap remains.

Do not solve by global name matching. Use fight relationships, FightMetric IDs, Greco URLs, ESPN IDs, or explicit reviewed crosswalks.

### Priority 5 — refresh documentation/contracts

After the above:
- refresh `provenance/data_source_manifest.md`;
- refresh free-source sweep/status docs;
- update `schemas/source_precedence_v0.json` statuses;
- update source-field map where newly promoted weigh-in/scorecard/external fields become verified;
- run canonical contract validator + source field-map validator + precedence validator;
- run canonical build(s) and verify manifests/checksums/exclusions.

### Priority 6 — data-phase closeout gate

Before starting the Features chat, produce a final `DATA_PHASE_COMPLETE.md` only when:

- core canonical identity/fight/round tables validate;
- rankings are canonicalized with dated-observation semantics;
- official profile snapshots are canonicalized;
- external pre-UFC/cross-promotion history is either canonicalized or explicitly deferred with rationale;
- fight-specific weigh-ins are canonicalized or explicitly declared an accepted gap;
- judge-round scorecards are canonicalized or explicitly declared an accepted gap;
- every source family is one of: `CANONICAL`, `RAW_QA_ONLY`, `DEFERRED_ACCESS_GATED`, or `REJECTED`;
- source precedence and source map validators pass;
- no unresolved contract-definition issue is being deferred casually to feature engineering.

Then STOP this phase. The next chat should begin feature-family design from the canonical contracts and manifests, not resume source hunting.

---

## 10. Suggested first sequence in the new chat

Do this in order:

1. Inspect current `main` HEAD/recent bot commits for anything after this handoff.
2. Read:
   - `DATA_PHASE_HANDOFF.md`
   - `data/canonical/v0/manifest.json`
   - `schemas/canonical_data_contract_v0.json`
   - `schemas/source_precedence_v0.json`
   - latest weigh-in/scorecard/external-MMA audit artifacts
3. Reconcile the stale external-MMA date wording in source precedence.
4. Finish weigh-in annotation audit and identity mapping.
5. Finish scorecard structure/identity audit.
6. Canonicalize external MMA history.
7. Rebuild/validate canonical v0.
8. Refresh source manifest/status docs.
9. Perform final DATA phase closeout checklist.
10. Only then create `DATA_PHASE_COMPLETE.md` and move to the Features chat.

---

## 11. Collaboration style to preserve

The user specifically values this mode of work:

- one agent owning the full chain rather than bouncing between models/tools;
- proactive repo organization and durable documentation;
- multiple independent workstreams when they do not conflict;
- self-reporting GitHub runners used as remote compute;
- skepticism about one’s own assumptions;
- catching errors through preplanned validation rather than explaining them away afterward;
- plain-language explanations of modeling/data-engineering decisions;
- clean phase boundaries: finish DATA here, start FEATURES in a new chat.

Do not sacrifice correctness to make the phase look finished. Partial completion with explicit gaps is preferable to silent coercion.
