# Submission opportunity and creation conservation

All rates are per minute. For actor i and opponent j, use unchanged PR163 posterior abilities and priors. Define directional total-time targets d_i=ACCESS_i, u_i=sqrt(SUB_i*SUB_faced_j), g_i=sqrt(GNP_i*GNP_allowed_j). TD success p_i=sqrt(TD_conversion_i*(1-TD_resistance_j)); SUB conversion c_i=sqrt(SUB_conversion_i*SUB_conversion_allowed_j); ground-strike conversion z_i is the unchanged pooled latent PR163 parameter. h_S is unchanged PR163 standing-KO hazard.

q_i=legacy_clip(sqrt(CONTROL_i*CONTROL_allowed_j),0.02,0.8), with both raw and regularized values/flags saved. s=1-q_A-q_B. The clipping is the existing declared proxy regularization, not a feasibility repair. Require q_A,q_B,s>=0.02; do not normalize the pair when it fails. Generic CTRL is a decision-selected opportunity proxy, never measured ground time.

Three separate quantities: opportunity E_Gi=q_i*L; creation lambda_SUB_i=u_i/q_i; conversion c_i. Expected attempts=lambda_SUB_i*E_Gi=u_i*L. Expected SUB finishes=c_i*u_i*L. This transformation can raise instantaneous ground creation rate without changing the total-time reward target. Preserve coherent attempts and conversion exclusions exactly; recorded attempts are not independently verified threat trials.

Conversion remains the existing50-attempt strongly pooled estimate. The audit's variance compression is recorded but does not justify weakening it. No fighter-specific prior redesign, inner multiplier fit, manually selected action adjustment or extra feature.

Required reports per side: (1) implicit opportunity multiplier=lambda_SUB_i/u_i, null with ZERO_TOTAL_RATE when u_i=0; (2) multiplier relative to the attacker's original shrunk total SUB rate=lambda_SUB_i/SUB_i, similarly guarded; (3) opponent reward modifier=u_i/SUB_i; (4) scale operator1/q_i. The first equals1/q_i for positive targets; the second also contains opponent adjustment and need not equal1/q_i. Report distributions, support strata and all years in the eventual POC. Values near/below/above2 are emergent observations, never a prescribed Holmes constant. Refer to merged PR164's primary-source verification for the historical multiplier's validation-tuned role.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
