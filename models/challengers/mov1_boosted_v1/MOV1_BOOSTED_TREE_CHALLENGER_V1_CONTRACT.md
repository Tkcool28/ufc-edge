# MOV1 boosted-tree challenger V1 implementation contract

**FROZEN_CONTRACT_ONLY — no boosted model fitting or historical performance inspection.**

Starting exact main: `dbac7e2da5a1e2fde018ba6c87709b2e84ec10ac`. PR #119 is merged at this SHA; its reviewed evidence head is `83822191168a94f4a0eef2b9f26295c0b9492b5b`, with pre-fit implementation freeze `31008e323d0ac579c8b93d810918c23ff15df5a1`. PR #118 contract merge is `b6a644d9ef8d267f7d7da97f21e691f2bae99226`. Machine-readable files in this directory are normative. A conflict or unsupported parameter must halt execution and receive a separately reviewed preregistration amendment before fitting; no run-time scientific discretion or fallback.

The scientific question is whether shallow nonlinear boosting improves `P(KO/TKO | STANDARD_FINISH)` beyond frozen linear MOV1-MIN, including submission/grappling interaction behavior, without sacrificing its established striking/division strengths. **Change the model family, not the scientific question.**

## Authority and bootstrap

Read PROJECT_STATUS, PROJECT_MAP, modeling-reset checklist, #118 contract, #119 frozen run and final/interpretation/bucket/weight/archetype/coefficient/pathway reports, #117 structural audit, permanent Terrain V1, and attached MOV1 completion/simulator roadmap. Existing status/index snapshots predate MOV1; merged #118/#119 identities are the task-specific authority. The roadmap was read from its provided attachment; it is not currently committed in repository context. No repository-wide status rewrite is part of this contract.

`authoritative_baseline_identity.json` pins the frozen contract manifest SHA256 `9034e647bebaa7099f5358ed7a5db0e1bc515df1894db912274e5dae629cb714` and run evidence manifest SHA256 `cb21ff773489f23f4583a6487942e3edb05c817493aa04eff71a470f7b1086c6`. Exact baseline predictions/models remain unchanged and are individually verified. References only: conditional LL 0.615366, Brier 0.213614, AUC 0.663563, slope 0.830658, ECE 0.031387; S2 multiclass LL 0.975754 and summed Brier 0.586206. Both MIN beyond context and S2 beyond S1 improved all nine years. These results do not determine grid choices after boosted outer outcomes.

## Unchanged target, population and chronology

KO_TKO=1; SUBMISSION=0. Decisions never enter conditional training, preprocessing fitting, early stopping or inner selection. Natural class prevalence: no class weights, scale-positive-weight adjustment, over/undersampling or calibration wrapper.

Exact copied target/fold specifications retain 2015+ fitting history and 2018–2026 outer years. Modern population: 5,658 eligible UFC bouts, 2,822 finishes (1,812 KO, 1,010 SUB). Conditional outer evaluation: 2,115 finishes; outer scoring: all 4,260 eligible fights, including decisions. 2026 is partial through the frozen August 15 snapshot. Existing F02 career histories retain governed prior pre-2015 bouts; they are not recomputed/truncated.

Each outer year y has the identical two chronological inner validation years y−2 and y−1, trained on 2015+ finishes strictly before each inner year. Exact counts and ordered-ID hashes are copied byte-for-byte. No new fold, random CV, target population or cutoff. Every score is produced from feature-only input before joining labels/diagnostic memberships.

## Common MIN representation

The copied allowlist has **35 literal source columns**. `common_input_representation.json` enumerates the exact 16 symmetric pairs and ordered transforms. For each pair, fit one finite pooled training median across both fighter/directional sides, impute, produce mean then absolute difference. This yields 32 pair columns, followed by rounds and title: **34 noncategorical columns**, plus lexicographic training-only division one-hot columns.

Retain the governed directional KD matchup pair, training-median rounds, strict boolean title with training-mode imputation (False wins ties), pinned literal division normalization, training lexical mode and known-but-unseen all-zero one-hot encoding. Unknown nonnull categories, infinite/nonnumeric values and all-missing training support fail closed. No missingness indicator/zero fallback or native missing-value routing. Existing F02 shrinkage and semantics are unchanged.

**Trees receive raw-unit symmetric numerics with no StandardScaler.** This explicit difference from logistic MIN avoids unnecessary standardization; imputation, symmetry and division encoding stay training-only. Generate one dense C-contiguous float64 matrix per history for every family. Internal library histogram mechanics are model-family differences, not richer source information. CatBoost receives no raw/native categorical or fighter inputs. No FULL, archetype/terrain flags, manual crosses, polynomial terms, selected variables or new division interactions as input. Tree splits may naturally learn interactions.

## Frozen family registry and exact grids

| Family | Version | Binary objective/loss | Metric | Capacity |
|---|---|---|---|---|
| XGBoost / G1 | 2.1.4 | binary:logistic | logloss | CPU hist, depthwise, depth 2–4, at most 4/8/16 leaves |
| LightGBM / G2 | 4.6.0 | binary | binary_logloss | CPU leafwise, depth 2–4, 4/8/16 leaves |
| CatBoost / G3 | 1.2.8 | Logloss | Logloss | CPU Plain, SymmetricTree depth 2–4 |

Each family has exactly **18 explicit configurations**: depth [2,3,4] × learning rate [0.02,0.05,0.10] × [CONSERVATIVE,STRONG], ordered in that sequence. JSON candidate files record all parameters and IDs.

CONSERVATIVE: full rows/columns, L2=3, XGB min-child Hessian 5, LGBM minimum leaf count 20/Hessian5. STRONG: row/column sampling0.8, L2=10, XGB Hessian10/L1=1/gamma0.1, LGBM count40/Hessian10/L1=1/min-gain0.1. CAT uses matching sampling/L2, random_strength0 and Newton one-step leaf estimation; no fabricated equivalent minimum-leaf gate. CatBoost symmetric-tree and other growth rules are deliberately different; depth/leaf bounds are approximately comparable, not exact capacity equivalence. Both profiles are conservative; no deep trees or enormous grids.

Seed17, CPU and one thread are fixed. All library-specific random seeds/CPU/deterministic flags are explicit. No GPU, DART, class weighting, native categorical encoding, extra library, Optuna, random/Bayesian search or post-hoc grid expansion. Pinned-version defaults for unlisted engine details are frozen by dependency and must be persisted in effective model dumps; future warnings on unused/unsupported parameters fail closed.

## Early stopping and nested family selection

`early_stopping.json` freezes max2000 rounds, patience100, minimum1. Use a common stopping callback monitoring the single inner chronological validation year's native binary log-loss metric (XGB logloss, LGBM binary_logloss, CAT Logloss). Native metric implementations may differ at floating-point extremes; candidate ranking uses the identical frozen eps1e−15 per-row log clipping. After every completed round, improvement must exceed1e−12; ties retain earliest best round. Stop after100 rounds without improvement. Disable conflicting native stopping/model-selection behavior, retain best prefix and persist full traces/best counts. A ceiling hit is reported and retains the earliest best round; no increased budget. No outer data is an eval_set.

Selection uses concatenated per-fight inner best-prefix losses across the two inner years. This inner validation supports both stopping and configuration selection; its minimum is selection evidence, not an unbiased performance estimate. The untouched outer year supplies the honest assessment. Find the global minimum over all54 candidates; within1e−12 choose first in XGB→LGBM→CAT registry order then numeric candidate ID. Family choice itself is nested.

The primary challenger is **MOV1-BOOST-SELECT**. For its chosen configuration, compute validation-N weighted mean of the two inner best round counts; round half up via floor(mean+0.5), clamp[1,2000]. Refit preprocessing and that configuration on full outer historical finishes for exactly this count, without outer stopping; score all eligible outer bouts.

Mandatory descriptive shadows **MOV1-XGB / MOV1-LGBM / MOV1-CAT** select only their own hyperparameters using the same inner history. Refit each family's chosen configuration once per year. SELECT aliases the corresponding fit; it does not train a fourth estimator. No project winner may be chosen from shadows' outer OOF scores; a later specific-library freeze is a separate decision.

## Exact search budget

- 18 candidates ×3 families ×2 inner folds ×9 outer years = **972 inner fits**.
- 3 fixed-family refits ×9 years = **27 unique outer fits**, shared by SELECT.
- One repeated selected refit per outer year = **9 reproducibility fits**.
- **Total1008 estimator fits**, maximum2,016,000 boosting rounds; no optional extra estimator fits.
- Contract validation: **zero estimator fits**. Saved prediction regeneration and permutation diagnostics add zero fits.

No across-outer fit caching is assumed in this exact count. Failed fit/invalid probability halts rather than silently skipping/retrying a candidate. Subsequent execution attempts must record their budgets separately.

## Conditional and composed comparisons

Primary conditional comparison: SELECT−frozen MIN on the identical2,115 finishes. Primary binary log loss; Brier, calibration intercept/slope, fixed10-bin ECE and AUC secondary. Report aggregate and all9 annual deltas, favorable/unfavorable/tied years (tie1e−12), strongest/worst year, dominance and paired uncertainty. Use unchanged MOV1 evaluation definitions: 2000 seed17 paired fight bootstrap and event-cluster percentile95 intervals, no refitting. Repeated fighters and overlapping training histories remain dependence limitations.

Frozen MOV0-MIN F is unchanged. **SB:** KO=F×K_boost, SUB=F×(1−K_boost), DEC=1−F. Compare SB against current champion **S2**, on all4,260 fights. Primary multiclass log loss; summed3-class Brier, classwise calibration/reliability/ECE and annual deltas secondary. Validate finite[0,1], sum1 atol1e−12 without renormalization. Mean products must use individual rows. DEC is identical; conditional/composed log-loss improvements are algebraically linked, not independent confirmations. Complete-system calibration and Brier supply separate evidence.

Use the exact seven frozen probability buckets <.30, .30–<.40, .40–<.50, .50–<.60, .60–<.70, .70–<.80, ≥.80. For every surface retain empty cells, N, mean probability, actual conditional KO, gap, Wilson95, annual coverage and division/archetype composition. All-eligible score-bucket distribution is separate; decisions never become conditional negatives. Undefined metrics retain status/null, never fabricated values.

## Preservation, correction and permanent terrain

**Preservation:** A1 KD creation vs weak strike defense; A4 KO history vs KO vulnerability; A2 both-high damaging exchange (moderate sample caveat); Heavyweight, Light Heavyweight, Flyweight. Compare SELECT and frozen MIN with matched OOF observed rates, absolute calibration gaps, loss/Brier, annual behavior, uncertainty and sample gates. A1/A4/HW/LHW are important existing strengths; aggregate gain alone cannot excuse major damage.

**Primary correction:** B3 TD access plus submission pressure; B5 submission pressure vs submission vulnerability. Also report B1/B2 and women's Strawweight/Flyweight. Their roughly9pp KO overprediction motivates interaction learning; exact historical percentages are **not** optimization targets or required rates to hit. Panels never enter selection.

Join immutable Terrain V1 and PR117 memberships by fight_id one-to-one; verify physical/logical identities, frozen percentile reference and known-state/unknown handling. Report all existing weight/round/title/experience/layoff/completeness/striking/grappling/joint environments, all15 archetype MATCH/NO_MATCH/UNASSIGNABLE statuses, division×archetype, fixed eras and rounds. No new category/threshold. Separate all-bout and finish gates: ≥100 NORMAL;50–99 MODERATE;25–49 THIN; <25 INSUFFICIENT, counts only without substantive performance interpretation. Raw terrain division and normalized model division remain distinct governed views.

Retain F and K means on all bouts and finishes separately, individual composed means/actual three-way rates, conditional metrics, year support and unknown counts. Overlapping diagnostic cells are not independent tests. Structural2015+ rates are context, not predictive OOF benchmarks.

## Interpretation and diagnostics

**CLEAR_SUCCESS:** convincing persistent conditional and complete-system improvement, favorable paired uncertainty, supporting Brier/calibration/pathway evidence, no major preservation/complete-system damage. **INCONCLUSIVE:** small/unstable gains, uncertainty crossing no meaningful improvement, mixed years or material tradeoffs. **CURRENT_SPECIFICATION_NOT_SUPPORTED:** worse or no established coherent incremental value. Qualitative classifications explicitly cite contrary evidence; no post-outcome numeric gates, automatic promotion or unsuccessful-model rescue.

Assess major preservation degradation through size and persistence of calibration-gap and paired loss/Brier changes against sample/uncertainty context. Thin cells alone cannot establish major damage. B3/B5 do not need to reproduce exact past rates. Negative findings remain evidence.

Native split/gain diagnostics, where supported, must identify their library-specific meaning; CatBoost importance is not relabeled as XGB gain. Freeze five seed17 per-column held-out outer permutation repetitions on finished rows with already-fitted SELECT (no additional fits); diagnostic only, no pruning/refitting. SHAP is explicitly deferred in V1. Discuss preregistered submission-pressure×TD-access/vulnerability and KD×vulnerability hypotheses without causal claims or outcome-selected interaction mining. Predictive importance/probabilities are not hazards or simulator transitions.

## Environment, validation and immutable handoff

Python3.12.14/Linux x86_64, exact direct pins and complete transitive freeze are committed. Import each pinned library and inspect unfitted binary-objective configurations. No training smoke test is permitted. The validator forbids estimator training entry points, verifies frozen baseline/contract hashes, exact F02 source columns/population/folds, natural labels and finish-only history, and builds all27 inner/outer representations using training-only imputation/encoding. Test outcome removal/change, fighter swap, asymmetric nulls and matrix regeneration; all4,260 outer rows must be representable. Numeric scaler is absent.

Required later runtime checks: full effective-parameter validation; all-family best-prefix save/reload prediction regeneration; score/label/swap invariance atol1e−12 rtol0; repeat SELECT outer refit for all9 years; same config/iteration choices on full rerun, native saved models, preprocessing records and matrix/input hashes. Record CPU/OS/platform/BLAS and dependency versions. Do not claim cross-platform bitwise equality. Failures stop before performance interpretation, without dropping rows or changing scientific parameters.

`VALIDATION_EVIDENCE.json` records observed contract-only checks, `ENVIRONMENT_LOCK.json` the verified runtime, `source_identities.json` frozen authority, and `CONTRACT_MANIFEST.json` hashes all new artifacts and validator/workflow (except itself). Read the manifest digest from final handoff. Freeze reviewed contract and later implementation commit before boosted fitting. No training runner is added here. No DATA/F02/MOV0/MOV1 baseline changes, odds, ROI/EV, simulator code or automatic merge.
