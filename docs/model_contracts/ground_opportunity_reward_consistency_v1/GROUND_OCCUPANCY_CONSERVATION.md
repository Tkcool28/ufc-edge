# Ground occupancy conservation

All rates are per minute. For actor i and opponent j, use unchanged PR163 posterior abilities and priors. Define directional total-time targets d_i=ACCESS_i, u_i=sqrt(SUB_i*SUB_faced_j), g_i=sqrt(GNP_i*GNP_allowed_j). TD success p_i=sqrt(TD_conversion_i*(1-TD_resistance_j)); SUB conversion c_i=sqrt(SUB_conversion_i*SUB_conversion_allowed_j); ground-strike conversion z_i is the unchanged pooled latent PR163 parameter. h_S is unchanged PR163 standing-KO hazard.

q_i=legacy_clip(sqrt(CONTROL_i*CONTROL_allowed_j),0.02,0.8), with both raw and regularized values/flags saved. s=1-q_A-q_B. The clipping is the existing declared proxy regularization, not a feasibility repair. Require q_A,q_B,s>=0.02; do not normalize the pair when it fails. Generic CTRL is a decision-selected opportunity proxy, never measured ground time.

Eligible hazards are lambda_TD_i=d_i/s, entry e_i=lambda_TD_i*p_i, lambda_SUB_i=u_i/q_i, lambda_GNP_i=g_i/q_i. Ground terminal hazard h_i=lambda_SUB_i*c_i+lambda_GNP_i*z_i. Failed TD, unsuccessful SUB and nonfinishing ground strikes are counted marked self events; they do not add positions or waiting states.

T is the transient 3x3 generator for S/GA/GB: row S=[-(e_A+e_B+h_S),e_A,e_B]; row GA=[b_A,-(b_A+h_A),0]; row GB=[b_B,0,-(b_B+h_B)]. For tau=5 minutes, M=exp(tau*T), J=integral_0^tau exp(t*T)dt. Compute J by the upper-right block of exp(tau*[[T,I],[0,0]]), avoiding inversion of possibly singular T.

For R=3 or5 rounds, v=[1,0,0], a=v*M*1, w=sum_{k=0}^{R-1} a^k. E=(v*J)*w and L=sum(E). Enforce E_GA/L=q_A, E_GB/L=q_B, hence E_S/L=s. Expected rewards are lambda_TD_i*E_S=d_i*L; lambda_SUB_i*E_Gi=u_i*L; lambda_GNP_i*E_Gi=g_i*L. They are expectations over elapsed alive exposure, not scheduled duration or an average of per-trajectory ratios.

The requested targets are q_A,q_B jointly, not two independent two-state stationary shares. Accept only when absolute error of each ground share is<=1e-8 and rewards meet relative1e-7 using denominator max(1,target count). These are numerical tolerances, not empirical agreement with true grounded duration. Source measurement uncertainty persists.

Choose Option A now. Generic CTRL includes possible clinch/cage control and is decision-selected; neutral ground, bottom offense and scrambles are unobserved. No source-derived technique weighting is fitted. Raw proxy, existing regularization, target, achieved share, input support and reason code must all be reported. Failed targets are explicitly unavailable. Do not lower occupancy until a desired loss is obtained, silently renormalize A+B, or reuse the audit's nearly-zero-return oracle.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
