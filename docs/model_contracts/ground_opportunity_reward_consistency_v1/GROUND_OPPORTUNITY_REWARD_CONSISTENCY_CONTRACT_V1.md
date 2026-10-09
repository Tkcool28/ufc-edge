# Ground opportunity & reward consistency contract V1

Authoritative main: `675da47d6ad9b937c4b01dcd3986250b72308948`. PR164 verified merged; PR162 excluded. This freezes one opportunity mapping and exactly two future arms. It does not authorize running those arms in this task. Scope is mathematical contract, machine config, synthetic validation and immutable evidence.

## Scientific anchor

PR160/161 support continuous access, decision-only control, all-history SUB seeking and noisier GnP; no hard identities or measured escape. PR163 identity LL0.627949 beats population0.649319 but loses Arm C0.607777. Full SUB12.74% versus17.70%. PR164 identified coupled denominator errors: total-time TD access gated again by standing, bilateral occupancy inconsistency, return sensitivity2.38→2.95 minutes recovering~42% of SUB deficit, and existing opportunity normalization failing to reconstruct its denominator. Conversion variance compression~99.69% was not the principal deficit. Occupancy/attempt/conversion/combined oracle LL0.610802/0.608726/0.625456/0.608541 are diagnostics, never selectable arms. Old112/117 infeasible CTRL targets must remain an unresolved feasibility warning; this contract makes no claim of resolving them on real states.

## One frozen approach

Option A: retain generic decision CTRL as a declared opportunity proxy. No technique-weighted estimator, new latent fit, empirical multiplier or ground-time claim. Every state-action count target is defined on total elapsed alive time; each eligible hazard is obtained by division by a jointly feasible share. Keep conversion, original priors, source identity definitions, standing KO and ground KO attribution fixed. Returns are jointly inverted through finite five-minute-round occupation equations, with no performance-selected constant.

All rates are per minute. For actor i and opponent j, use unchanged PR163 posterior abilities and priors. Define directional total-time targets d_i=ACCESS_i, u_i=sqrt(SUB_i*SUB_faced_j), g_i=sqrt(GNP_i*GNP_allowed_j). TD success p_i=sqrt(TD_conversion_i*(1-TD_resistance_j)); SUB conversion c_i=sqrt(SUB_conversion_i*SUB_conversion_allowed_j); ground-strike conversion z_i is the unchanged pooled latent PR163 parameter. h_S is unchanged PR163 standing-KO hazard.

q_i=legacy_clip(sqrt(CONTROL_i*CONTROL_allowed_j),0.02,0.8), with both raw and regularized values/flags saved. s=1-q_A-q_B. The clipping is the existing declared proxy regularization, not a feasibility repair. Require q_A,q_B,s>=0.02; do not normalize the pair when it fails. Generic CTRL is a decision-selected opportunity proxy, never measured ground time.

Eligible hazards are lambda_TD_i=d_i/s, entry e_i=lambda_TD_i*p_i, lambda_SUB_i=u_i/q_i, lambda_GNP_i=g_i/q_i. Ground terminal hazard h_i=lambda_SUB_i*c_i+lambda_GNP_i*z_i. Failed TD, unsuccessful SUB and nonfinishing ground strikes are counted marked self events; they do not add positions or waiting states.

T is the transient 3x3 generator for S/GA/GB: row S=[-(e_A+e_B+h_S),e_A,e_B]; row GA=[b_A,-(b_A+h_A),0]; row GB=[b_B,0,-(b_B+h_B)]. For tau=5 minutes, M=exp(tau*T), J=integral_0^tau exp(t*T)dt. Compute J by the upper-right block of exp(tau*[[T,I],[0,0]]), avoiding inversion of possibly singular T.

For R=3 or5 rounds, v=[1,0,0], a=v*M*1, w=sum_{k=0}^{R-1} a^k. E=(v*J)*w and L=sum(E). Enforce E_GA/L=q_A, E_GB/L=q_B, hence E_S/L=s. Expected rewards are lambda_TD_i*E_S=d_i*L; lambda_SUB_i*E_Gi=u_i*L; lambda_GNP_i*E_Gi=g_i*L. They are expectations over elapsed alive exposure, not scheduled duration or an average of per-trajectory ratios.

## Interpretation limit

Exact conservation implies conditional finish method equals a closed-form conserved reward ratio (see NEXT_POC_FROZEN_ARMS.md). Under unchanged external MOV0 and time-homogeneous round resets, additional state timing does not independently change that conditional ratio. A future improvement would establish the benefit of consistent reward mapping, not independent predictive value of timing/positions. Mechanistic feasibility and timing records are still required. No empirical improvement is established here.

## Freeze hierarchy

contract.json is the machine specification; documents explain it; synthetic_math.py demonstrates the equations only on invented fixtures. Any scientific/config amendment requires a new reviewed contract before future outer scoring. Synthetic validation is not permission to bypass real-state preflight. No projection or outcome-dependent fallback. Explicit unavailable states block full scoring. NEXT_POC_SUCCESS_GATES.md fixes all acceptance thresholds. Exactly POC-A/POC-B; no new identity ablation, sensitivity arm or model search.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
