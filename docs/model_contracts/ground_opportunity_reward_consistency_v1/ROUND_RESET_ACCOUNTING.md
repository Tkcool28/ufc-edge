# Finite round reset accounting

Eligible hazards are lambda_TD_i=d_i/s, entry e_i=lambda_TD_i*p_i, lambda_SUB_i=u_i/q_i, lambda_GNP_i=g_i/q_i. Ground terminal hazard h_i=lambda_SUB_i*c_i+lambda_GNP_i*z_i. Failed TD, unsuccessful SUB and nonfinishing ground strikes are counted marked self events; they do not add positions or waiting states.

T is the transient 3x3 generator for S/GA/GB: row S=[-(e_A+e_B+h_S),e_A,e_B]; row GA=[b_A,-(b_A+h_A),0]; row GB=[b_B,0,-(b_B+h_B)]. For tau=5 minutes, M=exp(tau*T), J=integral_0^tau exp(t*T)dt. Compute J by the upper-right block of exp(tau*[[T,I],[0,0]]), avoiding inversion of possibly singular T.

For R=3 or5 rounds, v=[1,0,0], a=v*M*1, w=sum_{k=0}^{R-1} a^k. E=(v*J)*w and L=sum(E). Enforce E_GA/L=q_A, E_GB/L=q_B, hence E_S/L=s. Expected rewards are lambda_TD_i*E_S=d_i*L; lambda_SUB_i*E_Gi=u_i*L; lambda_GNP_i*E_Gi=g_i*L. They are expectations over elapsed alive exposure, not scheduled duration or an average of per-trajectory ratios.

At each of the first R-1 round boundaries, reset surviving live mass to S. Absorbing mass remains terminal. At the final boundary, surviving live mass becomes raw DEC. The occupation integral's B_i includes both kinds of boundary removal; expected forced returns report only the first R-1 resets. For round survival a and ground endpoint m_i=(v*M)_Gi: interround reset mass=m_i*sum_{k=0}^{R-2}a^k; final grounded expiry=m_i*a^(R-1); their sum=B_i.

Because each identical five-minute round starts standing and contributes the same occupation vector times a scalar survival weight, live exposure shares are independent of scheduled R under these fixed hazards. Expected counts, elapsed minutes and terminal probabilities still differ for3 versus5 rounds. Validate both explicitly. This renewal property does not justify using stationary occupancy; one finite round includes its start/reset transient.

For zero terminal hazards only, a certified total-ground ceiling at zero returns is1-(1-exp(-5*(e_A+e_B)))/(5*(e_A+e_B)). Requested total occupancy above it is impossible under the fixed entries. Do not apply that finish-free bound to a generator with absorption; preferential early death changes the alive-time denominator.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
