# Joint finite-round return-rate derivation

Eligible hazards are lambda_TD_i=d_i/s, entry e_i=lambda_TD_i*p_i, lambda_SUB_i=u_i/q_i, lambda_GNP_i=g_i/q_i. Ground terminal hazard h_i=lambda_SUB_i*c_i+lambda_GNP_i*z_i. Failed TD, unsuccessful SUB and nonfinishing ground strikes are counted marked self events; they do not add positions or waiting states.

T is the transient 3x3 generator for S/GA/GB: row S=[-(e_A+e_B+h_S),e_A,e_B]; row GA=[b_A,-(b_A+h_A),0]; row GB=[b_B,0,-(b_B+h_B)]. For tau=5 minutes, M=exp(tau*T), J=integral_0^tau exp(t*T)dt. Compute J by the upper-right block of exp(tau*[[T,I],[0,0]]), avoiding inversion of possibly singular T.

For R=3 or5 rounds, v=[1,0,0], a=v*M*1, w=sum_{k=0}^{R-1} a^k. E=(v*J)*w and L=sum(E). Enforce E_GA/L=q_A, E_GB/L=q_B, hence E_S/L=s. Expected rewards are lambda_TD_i*E_S=d_i*L; lambda_SUB_i*E_Gi=u_i*L; lambda_GNP_i*E_Gi=g_i*L. They are expectations over elapsed alive exposure, not scheduled duration or an average of per-trajectory ratios.

For actor i, integrate dp_Gi/dt=e_i*p_S-(b_i+h_i)*p_Gi within each round starting from zero ground mass. Summing rounds gives:

`e_i*E_S - (b_i+h_i)*E_Gi = B_i`

Here B_i is ground mass removed at all round boundaries: actual interround resets PLUS grounded survivor mass at final fight expiration. Final expiration is not another stand-up. Substituting target shares yields:

`b_i = (d_i*p_i - u_i*c_i - g_i*z_i)/q_i - B_i/(q_i*L)`

Therefore U_i=(d_i*p_i-u_i*c_i-g_i*z_i)/q_i is a strict upper bound because positive target occupancy with TD entry leaves positive boundary removal. U_i<=0 is a necessary-flow contradiction. Positive U_i<=1e-12 is a numerical-resolution failure, not proof of physical impossibility.

Solve b_i=gamma_i*U_i jointly for both actor shares, gamma in[0,1]. Fixed bounded TRF least-squares, initial[0.5,0.5], ftol/xtol/gtol1e-12, max_nfev400, no multistart. Accept a successful solve only with occupation/reward/flux tolerances satisfied. If several roots exist, the first accepted root from that fixed pinned deterministic algorithm is the rule; no loss-based choice or extra search. Save solution, residual, Jacobian and evaluation count. Failure is UNRESOLVED_FINITE_ROUND_TARGET; do not claim a globally proven impossibility from optimizer failure alone.

The return process is ESTIMATED_RETURN_TO_STANDING_PROXY, not measured escape. It is jointly constrained by entries, both occupancy targets, absorbing hazards and round boundaries. No half-rate multiplier or independently selected stand-up constant is permitted.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
