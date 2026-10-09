# Reward-conservation validation specification

Invented fixtures only in this task. test_contract.py and synthetic_math.py contain no fighter loader, outcome scorer, fit pipeline or POC runner. Current tests cover:

- Three TD attempts, four SUB attempts and20 ground-strike attempts per15 elapsed minutes, both actors,30% combined ground share; an additional30% actor-ground fixture distinguishes actor versus combined occupancy.
- Low2%, asymmetric10%/30%, and high40%/40% actor shares; both3-round and5-round structure.
- Absorption: expected actions equal rate*expected alive minutes, not rate*scheduled minutes.
- Joint side swaps, deterministic repeated solves, independent quadrature and round-renewal identities.
- Probability normalization/bounds throughout one-second propagation and resets; singular zero-terminal integral support.
- Infeasible bilateral sums, tiny opportunity, finite-round ceilings, terminal-reward flow contradictions, unresolved asymmetric target, invalid inputs/conversions/rounds.
- Population debut prior and1/1 strongly pooled conversion; no weakening of support priors.
- Closed-form conditional conserved-reward ratio versus state-integrated terminal rewards; interround resets separated from final expiry.

Required tolerances: each occupation error<=1e-8; action error/max(1,target count)<=1e-7; boundary-flow error<=1e-8; probability normalization<=1e-10; machine roundoff may be removed only within1e-12. Negative substantive values fail closed. Use pinned numpy2.3.5, scipy1.17.0 in Python3.12. Save test result and fixture reward records. Zero SUB reward has a null ratio and a separately defined opportunity operator.

Future execution additionally requires upstream exact hashes, strict-prior and target/same-date/future mutation tests, exact ordered4260 identity match, real actor-order swaps, saved-record regeneration, unchanged F01/F02/source/model evidence and all nine annual preflight summaries. No future input may influence priors or targets. Prediction-only records must be frozen and hashed before scoring. Exact propagation requires no Monte Carlo convergence budget or random seed; bootstrap uses seed164165 after authorized scoring only.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
