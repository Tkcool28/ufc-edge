"""Render the frozen textual contract. No historical data or predictions read."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
C=json.loads((P/'contract.json').read_text())
def doc(name,title,body):
 (P/(name+'.md')).write_text('# '+title+'\n\n'+body.strip()+'\n\nContract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.\n')
notation='''All rates are per minute. For actor i and opponent j, use unchanged PR163 posterior abilities and priors. Define directional total-time targets d_i=ACCESS_i, u_i=sqrt(SUB_i*SUB_faced_j), g_i=sqrt(GNP_i*GNP_allowed_j). TD success p_i=sqrt(TD_conversion_i*(1-TD_resistance_j)); SUB conversion c_i=sqrt(SUB_conversion_i*SUB_conversion_allowed_j); ground-strike conversion z_i is the unchanged pooled latent PR163 parameter. h_S is unchanged PR163 standing-KO hazard.

q_i=legacy_clip(sqrt(CONTROL_i*CONTROL_allowed_j),0.02,0.8), with both raw and regularized values/flags saved. s=1-q_A-q_B. The clipping is the existing declared proxy regularization, not a feasibility repair. Require q_A,q_B,s>=0.02; do not normalize the pair when it fails. Generic CTRL is a decision-selected opportunity proxy, never measured ground time.'''
math='''Eligible hazards are lambda_TD_i=d_i/s, entry e_i=lambda_TD_i*p_i, lambda_SUB_i=u_i/q_i, lambda_GNP_i=g_i/q_i. Ground terminal hazard h_i=lambda_SUB_i*c_i+lambda_GNP_i*z_i. Failed TD, unsuccessful SUB and nonfinishing ground strikes are counted marked self events; they do not add positions or waiting states.

T is the transient 3x3 generator for S/GA/GB: row S=[-(e_A+e_B+h_S),e_A,e_B]; row GA=[b_A,-(b_A+h_A),0]; row GB=[b_B,0,-(b_B+h_B)]. For tau=5 minutes, M=exp(tau*T), J=integral_0^tau exp(t*T)dt. Compute J by the upper-right block of exp(tau*[[T,I],[0,0]]), avoiding inversion of possibly singular T.

For R=3 or5 rounds, v=[1,0,0], a=v*M*1, w=sum_{k=0}^{R-1} a^k. E=(v*J)*w and L=sum(E). Enforce E_GA/L=q_A, E_GB/L=q_B, hence E_S/L=s. Expected rewards are lambda_TD_i*E_S=d_i*L; lambda_SUB_i*E_Gi=u_i*L; lambda_GNP_i*E_Gi=g_i*L. They are expectations over elapsed alive exposure, not scheduled duration or an average of per-trajectory ratios.'''
doc('GROUND_OPPORTUNITY_REWARD_CONSISTENCY_CONTRACT_V1','Ground opportunity & reward consistency contract V1',f'''Authoritative main: `{C['starting_main_sha']}`. PR164 verified merged; PR162 excluded. This freezes one opportunity mapping and exactly two future arms. It does not authorize running those arms in this task. Scope is mathematical contract, machine config, synthetic validation and immutable evidence.

## Scientific anchor

PR160/161 support continuous access, decision-only control, all-history SUB seeking and noisier GnP; no hard identities or measured escape. PR163 identity LL0.627949 beats population0.649319 but loses Arm C0.607777. Full SUB12.74% versus17.70%. PR164 identified coupled denominator errors: total-time TD access gated again by standing, bilateral occupancy inconsistency, return sensitivity2.38→2.95 minutes recovering~42% of SUB deficit, and existing opportunity normalization failing to reconstruct its denominator. Conversion variance compression~99.69% was not the principal deficit. Occupancy/attempt/conversion/combined oracle LL0.610802/0.608726/0.625456/0.608541 are diagnostics, never selectable arms. Old112/117 infeasible CTRL targets must remain an unresolved feasibility warning; this contract makes no claim of resolving them on real states.

## One frozen approach

Option A: retain generic decision CTRL as a declared opportunity proxy. No technique-weighted estimator, new latent fit, empirical multiplier or ground-time claim. Every state-action count target is defined on total elapsed alive time; each eligible hazard is obtained by division by a jointly feasible share. Keep conversion, original priors, source identity definitions, standing KO and ground KO attribution fixed. Returns are jointly inverted through finite five-minute-round occupation equations, with no performance-selected constant.

{notation}

{math}

## Interpretation limit

Exact conservation implies conditional finish method equals a closed-form conserved reward ratio (see NEXT_POC_FROZEN_ARMS.md). Under unchanged external MOV0 and time-homogeneous round resets, additional state timing does not independently change that conditional ratio. A future improvement would establish the benefit of consistent reward mapping, not independent predictive value of timing/positions. Mechanistic feasibility and timing records are still required. No empirical improvement is established here.

## Freeze hierarchy

contract.json is the machine specification; documents explain it; synthetic_math.py demonstrates the equations only on invented fixtures. Any scientific/config amendment requires a new reviewed contract before future outer scoring. Synthetic validation is not permission to bypass real-state preflight. No projection or outcome-dependent fallback. Explicit unavailable states block full scoring. NEXT_POC_SUCCESS_GATES.md fixes all acceptance thresholds. Exactly POC-A/POC-B; no new identity ablation, sensitivity arm or model search.''')
doc('STATE_EXPOSURE_DEFINITIONS','State exposure definitions','''| State | Eligibility / actions | Entry | Exit | Exposure denominator |
|---|---|---|---|---|
| STANDING | Both actors may attempt TD; unchanged standing KO pathway | Fight/round start; ground return | Successful TD to corresponding actor-ground; standing KO | E_S minutes for both TD streams |
| GROUND_A_ACTIVE | A SUB and significant GnP; continued control is self occupation | Successful A TD | A ground SUB/KO; derived return | E_GA, not either fighter's whole fight time |
| GROUND_B_ACTIVE | B SUB and significant GnP | Successful B TD | B ground SUB/KO; derived return | E_GB |
| KO | Absorbing | Standing/ground KO | None | Terminal probability, no action opportunity |
| SUB | Absorbing | Converting ground attempt | None | Terminal probability |

GA/GB identify the active actor only; no mount/guard/back or verified top/bottom position. Bottom submissions and non-TD ground entry remain unmodeled. Reset maps surviving S/GA/GB mass to S between rounds; KO/SUB remain absorbing. Final surviving mass becomes raw DEC by expiration. Mandatory clock expiration is not measured escape. Conditional method and three-way composition keep archived MOV0 F external.

Exposure shares use E_state/E_alive (ratio of expectations). They sum to1 across live states; calendar-time probabilities sum to1 including terminal mass. These are different normalizations; do not divide action rewards by scheduled 15/25 minutes after simulated early finishes.''')
doc('TOTAL_TO_STATE_RATE_TRANSFORM','Total-time to eligible-state transformation',notation+'\n\n'+math+'''

Both raw fighter rates and opponent-adjusted total-time targets must be retained. Opponent adjustment may change a matchup reward target relative to the fighter's individual history; conservation applies to that explicitly frozen target, not to two incompatible rates simultaneously. TD target uses own access; its opponent modifier affects success, not an invented TD-quality feature. SUB/GnP pairing keeps the existing geometric directional rule, but divides once by the common actor opportunity q_i. It no longer divides each side by a separate historical control denominator.

Conversion multiplies the action hazard once. Do not multiply counts by occupancy twice, use infinite-horizon shares, or attach a Holmes-derived numeric factor. Division by eligible shares preserves units actions/minute of that state. Standing-KO h_S is a frozen legacy eligible hazard, not a newly conserved TD/SUB/GnP action target; do not redesign its estimated denominator or fit it anew in POC-B.''')
doc('GROUND_ENTRY_CONSERVATION','Ground entry conservation',notation+'''

TD attempts occur only in S. Set lambda_TD_i=d_i/s and e_i=lambda_TD_i*p_i. Expected attempts=lambda_TD_i*E_S=d_i*L; successful entries=p_i*d_i*L. Count failed attempts as self events at lambda_TD_i*(1-p_i), not omitted TD reward. Ground entry remains TD-only, with no knockdown/guard-pull feature added.

Original access definition is unchanged: matched prior TD attempts/elapsed minutes, all-history, posterior30-minute prior. TD success/resistance keep20-attempt priors. No new standing-share statistical model is fitted: s is the simultaneous complement of the two CTRL opportunity targets, and must be reproduced by the finite-round solve. Require s>=0.02, bounding the opportunity division at50x. Invalid s is unavailable; never use max(s,epsilon) secretly or cap/drop the TD reward.''')
doc('GROUND_OCCUPANCY_CONSERVATION','Ground occupancy conservation',notation+'\n\n'+math+'''

The requested targets are q_A,q_B jointly, not two independent two-state stationary shares. Accept only when absolute error of each ground share is<=1e-8 and rewards meet relative1e-7 using denominator max(1,target count). These are numerical tolerances, not empirical agreement with true grounded duration. Source measurement uncertainty persists.

Choose Option A now. Generic CTRL includes possible clinch/cage control and is decision-selected; neutral ground, bottom offense and scrambles are unobserved. No source-derived technique weighting is fitted. Raw proxy, existing regularization, target, achieved share, input support and reason code must all be reported. Failed targets are explicitly unavailable. Do not lower occupancy until a desired loss is obtained, silently renormalize A+B, or reuse the audit's nearly-zero-return oracle.''')
doc('SUBMISSION_OPPORTUNITY_CONSERVATION','Submission opportunity and creation conservation',notation+'''

Three separate quantities: opportunity E_Gi=q_i*L; creation lambda_SUB_i=u_i/q_i; conversion c_i. Expected attempts=lambda_SUB_i*E_Gi=u_i*L. Expected SUB finishes=c_i*u_i*L. This transformation can raise instantaneous ground creation rate without changing the total-time reward target. Preserve coherent attempts and conversion exclusions exactly; recorded attempts are not independently verified threat trials.

Conversion remains the existing50-attempt strongly pooled estimate. The audit's variance compression is recorded but does not justify weakening it. No fighter-specific prior redesign, inner multiplier fit, manually selected action adjustment or extra feature.

Required reports per side: (1) implicit opportunity multiplier=lambda_SUB_i/u_i, null with ZERO_TOTAL_RATE when u_i=0; (2) multiplier relative to the attacker's original shrunk total SUB rate=lambda_SUB_i/SUB_i, similarly guarded; (3) opponent reward modifier=u_i/SUB_i; (4) scale operator1/q_i. The first equals1/q_i for positive targets; the second also contains opponent adjustment and need not equal1/q_i. Report distributions, support strata and all years in the eventual POC. Values near/below/above2 are emergent observations, never a prescribed Holmes constant. Refer to merged PR164's primary-source verification for the historical multiplier's validation-tuned role.''')
doc('GNP_OPPORTUNITY_CONSERVATION','Ground-striking opportunity conservation',notation+'''

lambda_GNP_i=g_i/q_i, so expected significant ground-strike attempts=g_i*L. Both SUB and GnP use exactly the same actor-state opportunity. Their nonfinishing events are marked self actions; converting events compete in the terminal generator. This conserves both activities rather than reallocating a fixed action count from one to the other.

z_i is unchanged PR163 pooled latent ground-KO conversion, estimated only from permitted pre-boundary history with1000 ground-attempt division pooling and20-KO ground-fraction pooling. No verified ground-KO location or individual ground-KO defense is invented. Preserve latent numerator, denominator and attribution assumption. Future records must separately report GnP actions, ground KO, SUB attempts/finishes and standing KO. Higher activity never implies every strike is a KO hazard.''')
doc('RETURN_RATE_DERIVATION','Joint finite-round return-rate derivation',math+'''

For actor i, integrate dp_Gi/dt=e_i*p_S-(b_i+h_i)*p_Gi within each round starting from zero ground mass. Summing rounds gives:

`e_i*E_S - (b_i+h_i)*E_Gi = B_i`

Here B_i is ground mass removed at all round boundaries: actual interround resets PLUS grounded survivor mass at final fight expiration. Final expiration is not another stand-up. Substituting target shares yields:

`b_i = (d_i*p_i - u_i*c_i - g_i*z_i)/q_i - B_i/(q_i*L)`

Therefore U_i=(d_i*p_i-u_i*c_i-g_i*z_i)/q_i is a strict upper bound because positive target occupancy with TD entry leaves positive boundary removal. U_i<=0 is a necessary-flow contradiction. Positive U_i<=1e-12 is a numerical-resolution failure, not proof of physical impossibility.

Solve b_i=gamma_i*U_i jointly for both actor shares, gamma in[0,1]. Fixed bounded TRF least-squares, initial[0.5,0.5], ftol/xtol/gtol1e-12, max_nfev400, no multistart. Accept a successful solve only with occupation/reward/flux tolerances satisfied. If several roots exist, the first accepted root from that fixed pinned deterministic algorithm is the rule; no loss-based choice or extra search. Save solution, residual, Jacobian and evaluation count. Failure is UNRESOLVED_FINITE_ROUND_TARGET; do not claim a globally proven impossibility from optimizer failure alone.

The return process is ESTIMATED_RETURN_TO_STANDING_PROXY, not measured escape. It is jointly constrained by entries, both occupancy targets, absorbing hazards and round boundaries. No half-rate multiplier or independently selected stand-up constant is permitted.''')
doc('ROUND_RESET_ACCOUNTING','Finite round reset accounting',math+'''

At each of the first R-1 round boundaries, reset surviving live mass to S. Absorbing mass remains terminal. At the final boundary, surviving live mass becomes raw DEC. The occupation integral's B_i includes both kinds of boundary removal; expected forced returns report only the first R-1 resets. For round survival a and ground endpoint m_i=(v*M)_Gi: interround reset mass=m_i*sum_{k=0}^{R-2}a^k; final grounded expiry=m_i*a^(R-1); their sum=B_i.

Because each identical five-minute round starts standing and contributes the same occupation vector times a scalar survival weight, live exposure shares are independent of scheduled R under these fixed hazards. Expected counts, elapsed minutes and terminal probabilities still differ for3 versus5 rounds. Validate both explicitly. This renewal property does not justify using stationary occupancy; one finite round includes its start/reset transient.

For zero terminal hazards only, a certified total-ground ceiling at zero returns is1-(1-exp(-5*(e_A+e_B)))/(5*(e_A+e_B)). Requested total occupancy above it is impossible under the fixed entries. Do not apply that finish-free bound to a generator with absorption; preferential early death changes the alive-time denominator.''')
doc('BILATERAL_OCCUPANCY_CONSTRAINTS','Bilateral occupancy and probability constraints','''At all calendar times: P(S)+P(GA)+P(GB)+P(KO)+P(SUB)=1. Reset preserves this mass. At final expiry DEC equals remaining S+GA+GB mass. No negative hazards, transition entries below-1e-12, transition entries above1+1e-12, or normalization error above1e-10 may be repaired into a scored prediction.

Live expected shares satisfy s+q_A+q_B=1. Require each>=0.02; actor CTRL target uses existing upper regularization0.8. Preserve raw targets and flags. Combined infeasibility is not repaired by proportional renormalization. A positive residual tolerance never permits probability mass above1.

TD/SUB/GnP reward conservation must hold for both sides simultaneously. Swap actors and their defenders: ground-state exposures, rates, supports and return rates must exchange; aggregate finish probabilities must agree. There is no symmetric mean/absolute-difference collapse and no competing independently computed ground durations that exceed elapsed time.''')
doc('SUPPORT_AND_SHRINKAGE_RULES','Support-aware estimates and stable transformations','''All source measurements, chronology and posterior strengths remain PR163 implementations of PR161 identities. No categorical styles. Posterior mean=(numerator+k*population mean)/(denominator+k), support=denominator/(denominator+k). Save numerator, denominator, prior fights, prior decisions, observed TD count/support, matched/missing bouts, posterior, prior mean/strength and broad support flag.

| Quantity | Prior strength | Source denominator |
|---|---:|---|
| ACCESS, SUB work/faced |30 minutes|Matched all-history elapsed exposure|
| Decision CTRL/allowed |30 minutes|Matched decision elapsed exposure; correlated duration pseudo-prior|
| GnP/allowed |60 minutes|Matched all-history elapsed exposure|
| TD conversion/resistance |20 attempts|Matched recorded TD attempts|
| SUB conversion/allowed |50 attempts|Coherent recorded SUB attempts|
| KO created/allowed |60 minutes|Legacy exposure, unchanged standing model|
| KD created/allowed |30 minutes|Legacy exposure, unchanged standing model|

Division means pool toward global with300 minutes for duration/control rates and100 attempts for conversion/resistance. Population priors freeze Jan1 each outer year using governed2015+ training history; fighter histories use strict event_date<target, exclude target/same date, and remain sealed through2026-08-15. Broad support: control>=1 measured decision and>=15 decision minutes; ACCESS/SUB/GnP>=3 matched bouts and>=15 minutes. Retain unsupported flags even with prior estimates.

Debuts receive population posterior means, not zero skill. Missing pairs contribute neither numerator nor denominator; measured zeros do contribute. Submission successes with zero attempts remain excluded from coherent conversion trials only. No prior strengths are revised here.

Eligible shares>=0.02 bound each opportunity-scale operator at50, avoiding explosive division for sparse actors. This floor retains the prior POC's declared opportunity resolution, is not a measured physical minimum, and does not license clipping infeasible targets during the solve. Base shrunk reward rates remain unchanged. Nonfinite transforms or unstable numerical solutions are unavailable; no action hazard is silently capped. Fixed-solver equality is a mathematical count identity, not calibrated individual uncertainty or proof CTRL measures ground time.''')
doc('FEASIBILITY_AND_PROJECTION_RULES','Feasibility and explicit unavailable-state policy','''Selected handling: **NO_PROJECTION**. Existing ability shrinkage/population fallbacks operate before hazard construction. There is no solver-dependent shrinkage, reward reduction, proportional CTRL normalization, numerical cap presented as success, or reference-probability substitution.

| Failure | Meaning | Behavior |
|---|---|---|
| INVALID_INPUT / INVALID_CONVERSION |Invalid counts/rates/probabilities|Stop; fix governed implementation, not constants|
| INVALID_PROXY_TARGET / INFEASIBLE_SIMPLEX |Opportunity targets violate declared domain or bilateral sum|Save raw targets and flags; unavailable|
| NO_POSITIVE_RESET_BUDGET |Successful entry flow cannot cover ground finish reward plus positive boundary removal|Certified necessary-flow failure for these measurements/architecture|
| NUMERICAL_RESET_BUDGET |Positive budget<=1e-12/minute|Numerically unresolved, not a physical impossibility claim|
| INFEASIBLE_FINITE_ROUND_CEILING |Zero-terminal occupancy target exceeds certified finite-round maximum|Unavailable; no longer episodes can fix fixed-entry ceiling|
| UNRESOLVED_FINITE_ROUND_TARGET |Joint bounded solver fails convergence/tolerance|Unavailable; not globally certified infeasibility|
| REWARD_RESIDUAL / RESET_FLUX_RESIDUAL / NUMERICAL_TRANSITION |Conservation or probability validation fails|Fail closed|

Save all failures, support levels and annual/division counts before any future scoring. At least99% of supported training/preflight states must be feasible, but **every** one of the4260 scored fight states must yield a valid construction before scoring is allowed. Any unavailable outer row blocks the full run, including unsupported/debut rows; no selective population drop or silently mixed-arm fallback. Near-all coverage is a scientific gate, not permission to fabricate the remaining predictions. If this cannot be met, report BLOCKED_OPPORTUNITY_FEASIBILITY with all reasons and await a separately reviewed contract amendment; do not tune using outer loss.

Synthetic success does not establish real-state feasibility. Contradictory measurements could reflect proxy semantics, missing non-TD entry or scarce support rather than the impossibility of every generic-ground architecture. Distinguish certified constraints from solver failures.''')
doc('REWARD_CONSERVATION_TEST_SPEC','Reward-conservation validation specification','''Invented fixtures only in this task. test_contract.py and synthetic_math.py contain no fighter loader, outcome scorer, fit pipeline or POC runner. Current tests cover:

- Three TD attempts, four SUB attempts and20 ground-strike attempts per15 elapsed minutes, both actors,30% combined ground share; an additional30% actor-ground fixture distinguishes actor versus combined occupancy.
- Low2%, asymmetric10%/30%, and high40%/40% actor shares; both3-round and5-round structure.
- Absorption: expected actions equal rate*expected alive minutes, not rate*scheduled minutes.
- Joint side swaps, deterministic repeated solves, independent quadrature and round-renewal identities.
- Probability normalization/bounds throughout one-second propagation and resets; singular zero-terminal integral support.
- Infeasible bilateral sums, tiny opportunity, finite-round ceilings, terminal-reward flow contradictions, unresolved asymmetric target, invalid inputs/conversions/rounds.
- Population debut prior and1/1 strongly pooled conversion; no weakening of support priors.
- Closed-form conditional conserved-reward ratio versus state-integrated terminal rewards; interround resets separated from final expiry.

Required tolerances: each occupation error<=1e-8; action error/max(1,target count)<=1e-7; boundary-flow error<=1e-8; probability normalization<=1e-10; machine roundoff may be removed only within1e-12. Negative substantive values fail closed. Use pinned numpy2.3.5, scipy1.17.0 in Python3.12. Save test result and fixture reward records. Zero SUB reward has a null ratio and a separately defined opportunity operator.

Future execution additionally requires upstream exact hashes, strict-prior and target/same-date/future mutation tests, exact ordered4260 identity match, real actor-order swaps, saved-record regeneration, unchanged F01/F02/source/model evidence and all nine annual preflight summaries. No future input may influence priors or targets. Prediction-only records must be frozen and hashed before scoring. Exact propagation requires no Monte Carlo convergence budget or random seed; bootstrap uses seed164165 after authorized scoring only.''')
doc('NEXT_POC_FROZEN_ARMS','Exactly two future frozen POC arms','''Primary hypothesis: opportunity-consistent construction will reduce systematic SUB underproduction and improve conditional finish-method estimates without damaging validated striking pathways.

**POC-A:** Exact PR163 primary identity-enabled POC. Reuse saved predictions, abilities and transitions; reference evidence head5121b4ebe45cffb8b15610a4998f62b79e4ff030, evidence manifest839587507aa470f8d0cf8df7b66f13c04a665790ebde1b2802abfc0c99f07d8b. Verify reproduction only; no refit or changed specification. PR164 oracle and half-return predictions are diagnostics, not arms.

**POC-B:** Same source measurements/abilities, priors, basic S/GA/GB/KO/SUB generator, conversions, latent ground-KO attribution, unchanged standing h_S, round structure and external archived MOV0 F. Change only total-to-eligible opportunity mapping and finite bilateral return inversion from this contract. No new features, positions, families, fits, calibrated postprocessor or empirical multiplier. Implementation belongs to a later explicitly authorized execution task.

Primary comparison B versus A. Secondary B versus saved Arm C from PR125. Original MOV1-MIN may be reported as the existing archival reference but is not another mechanistic variant. Exact sealed2018–2026 population and ordered scoring IDs:4260 fights/2115 finishes, cutoff2026-08-15. Frozen B3/B5/A1/A2/A4 memberships. No exclusions for poor outcomes or unavailable states.

Full composition unchanged: K=raw_KO/(raw_KO+raw_SUB); KO=F*K, SUB=F*(1-K), DEC=1-F. MOV0 remains external.

## Required conditional-method equivalence

Let z=sum(g_i*z_i), u=sum(u_i*c_i). Exact reward conservation implies:

`K=(h_S*s+z)/(h_S*s+z+u)`

The exact state engine must agree within1e-8. Under fixed conversions and identical reset rounds, this ratio does not gain a separate duration effect from returns or3 versus5 rounds; elapsed L cancels. Round structure still controls feasible occupancy, actual action totals and raw finish/decision probabilities. Require this equivalence as a validation identity, not an additional selectable shortcut arm. With external MOV0, opportunity correction is a test of conserved measurement representation, not proof that state timing provides independent conditional predictive information.

Freeze all expected state/reward records before scoring: supports; raw/regularized q; achieved E/L; eligible hazards; return solution/bounds/residual/Jacobian; all action rewards; boundary/reset/expiry mass; terminal contributions; both implicit multiplier definitions; F/K/raw/composed probabilities; source/fold hashes and failure reasons. No automatic promotion even if gates pass.''')
rows=[]
for key,value in C['gates'].items():rows.append('| '+key+' | '+str(value)+' |')
gate_table='| Machine gate | Frozen threshold |\n|---|---|\n'+'\n'.join(rows)
doc('NEXT_POC_SUCCESS_GATES','Frozen next-POC metrics, gates and handoff','''Score only after mechanical/conservation/preflight gates pass and prediction-only artifacts are hashed. These thresholds are frozen now; no POC-B outer results exist or were inspected. Thresholds express scientific effect/preservation tolerances, not selected hazard constants.

Metrics: conditional LL/Brier on standard finishes; full multiclass LL and summed Brier; mean KO/SUB/DEC; B3/B5 conditional SUB and individual losses; A1/A2/A4; exact expected standing/actor-ground occupancy, TD/SUB/GnP rewards, return transitions and implicit multiplier distributions; every outer year, division and minimum-pair history support stratum. Fixed10 equal-width reliability bins; diagnostic calibration intercept/slope where N>=100 and>=25 positives/negatives. No calibration fit changes predictions. Point subgroup gates need>=25 finishes, otherwise unsupported/unmet, never silently passed.

Use paired event bootstrap2000 draws, seed164165, percentile2.5/97.5; contrasts B-A and B-C with rows/memberships fixed. Overall SUB means use all4260 fights; B3/B5 use their unchanged standard-finish cohorts. A1/A2/A4 losses likewise conditional. Report unfavorable years and uncertainty; no multiple-testing discovery claim.

For d_model=observed mean SUB-predicted mean SUB and d+=max(d,0): overall d+_B<=0.5*d+_A, absolute gap<=0.025 and KO absolute gap no more than A+0.005. Each B3/B5 d+_B<=0.75*d+_A and absolute gap no larger than A; both losses must not worsen; at least one improves LL by>=0.010 with event-bootstrap upper<0. Conditional overall LL improves by>=0.010 versus A with upper<0; Brier increase<=0.002. Full LL improves>=0.003; summed Brier increase<=0.003.

For A1/A4, max(LL_B-LL_C,0)<=0.5*max(LL_A-LL_C,0). Also every A1/A2/A4 LL_B<=LL_C+0.010 and Brier_B<=Brier_C+0.005. Thus repairing mean SUB cannot excuse A2 damage. Annual LL improves over A in>=6/9 years, no annual worsening>0.010. Require all reward tests; supported feasible share>=99% and100% outer rows for scoring. Original DEC is unchanged to numerical tolerance.

Arm C competitiveness is a separate gate: B-C LL<=-0.005 with event upper<0, Brier increase<=0.002 and LL improvement in>=6 years. Beating Arm C is not required to conclude the opportunity correction helped versus A.

'''+gate_table+'''

## Failure interpretation and decision

D: certified reward/occupancy contradictions prevent the frozen generic-state mapping on supported contexts; this is relative to the selected proxy/entry architecture, not proof all coarse architectures fail. E: sparse support or numerical instability prevents construction; distinguish this from certified D. Both block scoring; do not use optimizer failure alone as D.

For valid scoring, C if the submission-deficit correction gates fail. B if opportunity correction works but full Arm C/preservation qualification remains incomplete; enumerate failed gates, even when individual aggregate losses improve. A only if all scientific success/preservation gates and competitiveness pass. No automatic next challenger, source purchase, production promotion or merge for any classification.

## Exact next execution handoff

**UFC_EDGE_OPPORTUNITY_CONSISTENT_GROUND_PATHWAY_POC_V2_IMPLEMENTATION_AND_FROZEN_RUN**. Begin only after this contract PR is merged and a separate execution instruction is given. Verify live main contains the exact frozen contract/config/manifest. Suggested branch feat/ground-opportunity-consistent-poc-v2. Open a draft PR; no automatic merge.

Read PR160/161/163/164 and this contract. Reuse immutable ability/source/reference artifacts. Implement only POC-B opportunity mapping in new isolated code; leave original code unchanged. Reproduce A/reference hashes. Run synthetic/chronology/order tests; reconstruct training-only targets and solve preflight without outcomes. If any outer row is unavailable, report BLOCKED_OPPORTUNITY_FEASIBILITY and stop before scoring. Otherwise save all4260 outcome-free predictions and support/hazard/reward records, hash them, then score once under these gates. Report both arms, Arm C, all years/cells, calibration, support, source manifest and completion marker. No extra variants, tuning, outer-selected constants or prospective confirmation access.''')
doc('README','Contract artifact guide','''Read GROUND_OPPORTUNITY_REWARD_CONSISTENCY_CONTRACT_V1.md, RETURN_RATE_DERIVATION.md and NEXT_POC_SUCCESS_GATES.md first. contract.json is the machine-readable freeze. synthetic_math.py is a synthetic demonstration with no data loader or scorer. Run test_contract.py from repository root; verify.py checks publication hashes and unchanged source locks. Run write_contract.py only to regenerate the explanatory text from the already frozen specification. No real-state feasibility or predictive performance was evaluated in this task.

All15 requested contract documents, source-lineage metadata/lock, config, synthetic tests/records, manifest and completion marker accompany the draft PR. Existing PR163/164 evidence remains unchanged. Literature context refers to merged PR164's direct primary-source verification; neither the audit oracle nor the published2x adjustment is a model arm.''')
