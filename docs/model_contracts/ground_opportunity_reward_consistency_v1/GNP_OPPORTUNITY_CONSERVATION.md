# Ground-striking opportunity conservation

All rates are per minute. For actor i and opponent j, use unchanged PR163 posterior abilities and priors. Define directional total-time targets d_i=ACCESS_i, u_i=sqrt(SUB_i*SUB_faced_j), g_i=sqrt(GNP_i*GNP_allowed_j). TD success p_i=sqrt(TD_conversion_i*(1-TD_resistance_j)); SUB conversion c_i=sqrt(SUB_conversion_i*SUB_conversion_allowed_j); ground-strike conversion z_i is the unchanged pooled latent PR163 parameter. h_S is unchanged PR163 standing-KO hazard.

q_i=legacy_clip(sqrt(CONTROL_i*CONTROL_allowed_j),0.02,0.8), with both raw and regularized values/flags saved. s=1-q_A-q_B. The clipping is the existing declared proxy regularization, not a feasibility repair. Require q_A,q_B,s>=0.02; do not normalize the pair when it fails. Generic CTRL is a decision-selected opportunity proxy, never measured ground time.

lambda_GNP_i=g_i/q_i, so expected significant ground-strike attempts=g_i*L. Both SUB and GnP use exactly the same actor-state opportunity. Their nonfinishing events are marked self actions; converting events compete in the terminal generator. This conserves both activities rather than reallocating a fixed action count from one to the other.

z_i is unchanged PR163 pooled latent ground-KO conversion, estimated only from permitted pre-boundary history with1000 ground-attempt division pooling and20-KO ground-fraction pooling. No verified ground-KO location or individual ground-KO defense is invented. Preserve latent numerator, denominator and attribution assumption. Future records must separately report GnP actions, ground KO, SUB attempts/finishes and standing KO. Higher activity never implies every strike is a KO hazard.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
