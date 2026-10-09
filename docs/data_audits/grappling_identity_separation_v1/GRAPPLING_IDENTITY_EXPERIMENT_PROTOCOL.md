# Frozen grappling identity separation experiment V1

Frozen before running new separation evidence. Starting main: 4a202a2eeb599b790323d1463288690addf3bd47. PR160 head d0ca33c89b63edd0517ea233454a17f295ae5b2c; manifest 8c2c660722743607733f77b5c86013d36dcca46daa2417ed39487e31d1cfa849. Developmental historical experiment; not untouched confirmation.

## Definitions and chronology

ACCESS = TD attempts / governed elapsed minutes in all prior complete measured bouts. CONTROL = generic control seconds / elapsed seconds in prior DECISION bouts only. SUBMISSION = recorded SUB attempts / elapsed minutes across all prior complete measured bouts. Preserve jointly observed numerator/denominator, matched bouts, missing bouts, prior decisions, prior UFC fights, TD landed and observed activity counts. Missing control is not zero. No composite score. All-history generic control share is the decision-selection comparator.

Secondary GNP = significant ground-strike attempts / governed elapsed minutes, following PR160's existing total-time measure. This is descriptive only: PR160 deferred expansion; it cannot authorize a third identity or affect the primary classification. No ground exposure, intention, threat quality or ground KO attribution is inferred.

Use PR158 immutable bout measurements with PR160 verification; source ends 2026-08-15. Only event_date < cutoff. Same-date and target bouts excluded. No prospective source expansion. At January 1 boundaries 2018–2026, use exact frozen fold training/scoring IDs and population memberships. Boundary snapshots use training fighters; original training-date and outer scoring-date support remain separate.

## Nonoverlapping replication

Exactly PR160 first three versus next three chronological prior UFC bouts, not first three qualifying decisions. Require strictly earlier third versus fourth event dates. No replacement for missing bouts. Each metric requires complete observed numerator/denominator in all three block bouts (decision control requires all decision bouts in that block observed). Primary support: >=1 decision and >=15 decision minutes for control; >=3 jointly measured bouts and >=15 minutes for access/SUB/GNP/all-history control. Sensitivity: >=2 decisions in each block; boundary/original states additionally >=6 total prior fights. Report positive-denominator, primary-supported and stricter-supported coefficients. N<25 suppresses coefficients; no silent exclusion. Pearson, Spearman, 95% fighter bootstrap CIs (2000 draws, seed 160161), and above/below fixed first-block median sign agreement, with ties excluded. Repeated annual cohorts are not independent. First block 1–3 and second 4–6 never share bouts.

## Comparable access and descriptive regions

Use PR160 outcome-blind quartiles of supported ACCESS at each boundary, average-rank qcut with duplicate edges dropped. No new access metric. Report each quartile's continuous control/SUB distributions, Spearman redundancy and four median-defined descriptive regions, not fighter labels. For block replication freeze ACCESS quartile edges and within-quartile CONTROL/SUB medians using first-block supported histories only; apply unchanged to second blocks. Equality goes to low; no jitter. Primary separation includes the same access quartile on both blocks; separately show all eligible fighters and access drift. Region retention compared to second-block marginal region prevalence in that same stratum. Bootstrap fighters within first-block access strata; retain fixed cuts. No thresholds selected using outcomes. Replicate within division where N>=25 and remove each division in turn; count-support sensitivity and boundary evidence use the same rules. No manual names or hard classes.

## Prior exposure shrinkage (descriptive sensitivity only)

Boundary and original-date states: transparent prior-exposure estimator (numerator + prior mean * exposure)/(denominator + exposure). Fixed prior strength 15 elapsed minutes for count rates; 900 elapsed seconds for decision control. Within current target division, pool only other fighters' observed bouts strictly earlier than cutoff; exclude focal fighter. No eligible prior => missing pooled estimate. Keep raw support/missingness flags even when a pooled value exists. This is not a beta-binomial count of independent seconds, no tuned hyperparameters or predictive fit. Replication gates use raw values, avoiding common-prior induced correlation. Bootstrap uncertainty concerns population persistence, not a calibrated individual posterior. No confident debut identity. Strength is one nominal three-round fight, chosen for transparency, not optimized.

## Frozen quantitative gates

These numeric gates were not supplied by PR160 and are fixed here before new computation. Moderate persistence is required rather than label accuracy; 0.30 rank correlation denotes useful but noisy repeatability, 0.80 redundancy is deliberately permissive, and support/retention gates prevent a full endorsement from a small survivor subset.

For A, ALL of:
1. 2026 primary-supported CONTROL and SUB Spearman >=0.30 with 95% lower bound >0.15, N>=100 each; same-access cohort each rho>=0.25 with lower bound >0.
2. 2026 boundary and both block same-access within-stratum residual rank correlations abs<0.80. Rank-center within access quartile (no outcome regression).
3. Same-access first-block high-control/low-SUB and low-control/high-SUB each >=25 fighters and >=5% of joint cohort; each retention excess over stratum-specific second-block prevalence >=0.05, bootstrap lower bound >0.
4. Stricter two-decision same-access sensitivity N>=50, both rho>=0.25; at EVERY 2018–2026 outer scoring boundary >=50% of fighter states support both dimensions. At 2018 primary repeatability N>=50, both rho>=0.25.
5. At least four divisions with N>=25 joint same-access fighters have both rho>=0.20; leave-one-division-out each rho>=0.25. Eras defined by first-block end date before 2015 versus >=2015 each N>=50 and both rho>=0.25. No era tuned after inspection.

B if A fails but 2026 same-access both rho>=0.20, bootstrap lower bounds >0, N>=50, abs residual rank correlation<0.80, and each discordant region >=10. Specify every failed A gate and restrictions; no automatic predictive authorization.
C otherwise: insufficient stable distinct identity; do not proceed to predictive challenger. Insufficient support counts as unmet gate; do not relax thresholds. Secondary GnP never changes A/B/C.

## B3/B5 and boundaries

Use exact frozen memberships on all scored bouts, both fighter sides; never target outcomes. Join new strict-prior dimensions to frozen membership IDs only. Continuous p10/p25/p50/p75/p90, missingness and support, annual distributions. B3 heterogeneity and B5 concentration interpreted relative to supported full scored cohort without fitted outcomes or cell-specific cuts. Do not claim causality or identify an attacker from cell membership.

## Guardrails and outputs

No MOV0/MOV1, outcome predictor, F01/F02 change, B3/B5 revision, sportsbook/ROI, prospective outcomes, labels, acquisition, simulator code, Arm C promotion or merge. Publish all twelve requested reports, raw/pooled fighter states, block states and IDs, support/replication/separation/region/division/era/cell tables, exact gate decisions, verification, evidence manifest and completion marker. Hash upstream evidence, protocol and scripts; verify independent scalar states and chronology mutation invariance; rerun deterministic tables byte-identically. Manifest excludes itself and completion marker to avoid circular hashes.
