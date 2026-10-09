# Ground entry conservation

All rates are per minute. For actor i and opponent j, use unchanged PR163 posterior abilities and priors. Define directional total-time targets d_i=ACCESS_i, u_i=sqrt(SUB_i*SUB_faced_j), g_i=sqrt(GNP_i*GNP_allowed_j). TD success p_i=sqrt(TD_conversion_i*(1-TD_resistance_j)); SUB conversion c_i=sqrt(SUB_conversion_i*SUB_conversion_allowed_j); ground-strike conversion z_i is the unchanged pooled latent PR163 parameter. h_S is unchanged PR163 standing-KO hazard.

q_i=legacy_clip(sqrt(CONTROL_i*CONTROL_allowed_j),0.02,0.8), with both raw and regularized values/flags saved. s=1-q_A-q_B. The clipping is the existing declared proxy regularization, not a feasibility repair. Require q_A,q_B,s>=0.02; do not normalize the pair when it fails. Generic CTRL is a decision-selected opportunity proxy, never measured ground time.

TD attempts occur only in S. Set lambda_TD_i=d_i/s and e_i=lambda_TD_i*p_i. Expected attempts=lambda_TD_i*E_S=d_i*L; successful entries=p_i*d_i*L. Count failed attempts as self events at lambda_TD_i*(1-p_i), not omitted TD reward. Ground entry remains TD-only, with no knockdown/guard-pull feature added.

Original access definition is unchanged: matched prior TD attempts/elapsed minutes, all-history, posterior30-minute prior. TD success/resistance keep20-attempt priors. No new standing-share statistical model is fitted: s is the simultaneous complement of the two CTRL opportunity targets, and must be reproduced by the finite-round solve. Require s>=0.02, bounding the opportunity division at50x. Invalid s is unavailable; never use max(s,epsilon) secretly or cap/drop the TD reward.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
