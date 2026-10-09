# Bilateral occupancy and probability constraints

At all calendar times: P(S)+P(GA)+P(GB)+P(KO)+P(SUB)=1. Reset preserves this mass. At final expiry DEC equals remaining S+GA+GB mass. No negative hazards, transition entries below-1e-12, transition entries above1+1e-12, or normalization error above1e-10 may be repaired into a scored prediction.

Live expected shares satisfy s+q_A+q_B=1. Require each>=0.02; actor CTRL target uses existing upper regularization0.8. Preserve raw targets and flags. Combined infeasibility is not repaired by proportional renormalization. A positive residual tolerance never permits probability mass above1.

TD/SUB/GnP reward conservation must hold for both sides simultaneously. Swap actors and their defenders: ground-state exposures, rates, supports and return rates must exchange; aggregate finish probabilities must agree. There is no symmetric mean/absolute-difference collapse and no competing independently computed ground durations that exceed elapsed time.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
