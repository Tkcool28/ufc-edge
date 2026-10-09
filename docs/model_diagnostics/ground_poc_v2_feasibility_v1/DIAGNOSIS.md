# Ground POC V2 feasibility diagnosis

This is the outcome-blind follow-up authorized after blocked PR166, using its exact frozen records at c811bd0d0a3a5efc150a50f3308ffbd74021eb47. It adds mathematical diagnoses, not a revised POC arm. The original V2 solver, contracts, records, failure codes, classification marker and evidence manifest remain unchanged. No scoring outcomes or external F were read.

## Resolved result

| Original unavailable rows | Diagnosis | Count |
|---|---|---:|
| UNRESOLVED_FINITE_ROUND_TARGET | Certified analytic occupancy ceiling | 1,590 |
| UNRESOLVED_FINITE_ROUND_TARGET | Certified exhaustive interval cover of return domain | 247 |
| UNRESOLVED_FINITE_ROUND_TARGET | Valid physical root missed by stopping rule | 1 |
| Remaining unresolved | None | 0 |

There are **1,837 certified contradictions**, including **1,038 supported contexts**, and one supported numerical miss. The original 2,422 valid constructions remain unchanged. A numerical repair alone can supply at most **2,423/4,260 = 56.8779%** of the frozen population; supported coverage would be only 1,009/2,047 = 49.2916%. It cannot make V2 scoreable.

The initial E classification was appropriate when optimizer rejection alone did not prove infeasibility. This separate diagnosis now supports **D for the frozen mapping**, with one additional numerical issue. It does not establish that every generic-ground architecture is impossible or that more detailed positions are required.

## Analytic certificate

Within each five-minute round, let S(t) be standing live probability; G_i(t) actor-ground live probability; e_i fixed successful entry; h_i fixed ground terminal hazard; h_S fixed standing terminal hazard; b_i any nonnegative return. Start each round standing.

The ground balance equation gives

`integral G_i = e_i * integral S(t) * f_(b_i+h_i)(5-t) dt`,

where `f_h(a)=(1-exp(-h*a))/h`. Since b_i>=0, this is at most `e_i * integral S(t)*f_hi(5-t) dt`.

Standing inflow is nonnegative, so `S(t)>=exp(-alpha*t)` with `alpha=e_A+e_B+h_S`. Total alive probability has terminal hazard at least `m=min(h_S,h_A,h_B)`, hence `S(t)<=exp(-m*t)`. All these terminal hazards are positive on the real frozen rows. An upper-rounded alpha favors feasibility.

We maximize weighted residence `integral S*f / integral S` over the larger class of all functions between those two envelopes. At candidate R, the maximum signed integral H(R) chooses the upper standing envelope where f>R and the lower envelope where f<R. Since f decreases, this is one analytic threshold. A 60-digit interval evaluation certifies H(R_upper)<0, making R_upper a rigorous upper bound. The root locator only proposes an upper bracket; the interval sign, not optimizer convergence, supplies the certificate.

Any tolerated target must satisfy `q_i - 1e-8 <= e_i*(s+2e-8)*R_upper`. The 2e-8 allowance admits the largest standing-share change permitted by the two ground residual tolerances. A strictly positive interval lower bound on the opposite difference proves contradiction. This relaxed bound rules out 1,590 rows even with arbitrary nonnegative return rates. All 4,260 rows were checked; none of the 2,422 accepted original rows was falsely excluded.

## Exhaustive return-domain certificate

For the remaining failed cases without a positive root witness, the frozen normalized return domain is exactly [0,1]^2, with b_i=gamma_i*U_i. The two-dimensional rectangle is subdivided without gaps. Each box encloses all possible finite-round ground occupation shares using nonnegative uniformization of the transient CTMC.

Fixed Poisson-integral weights and matrix entries use 60-digit interval arithmetic. Binary64 multiplication, addition, subtraction and division in vector occupation propagation are rounded outward with nextafter. The omitted Poisson tail has an explicit conservative bound. Probabilities are intersected only with their mathematically proven [0,1] domain; inputs, hazards, requested rewards and targets are not altered. Target windows are also rounded outward.

A box is removed only when its rigorous occupation interval cannot overlap at least one frozen target's +/-1e-8 window. Exhausting the entire domain certifies that no allowed pair of return rates can satisfy the target. All 247 remaining non-witness rows are certified; the largest proof needed 167 boxes. Expected alive exposure shares are invariant between three and five identical reset rounds, so the one-round occupation proof applies to both schedules, while validation retains actual schedules.

This is a feasibility proof, not a projected model or additional challenger arm. Numerical root searches and negative roots are never used as impossibility certificates.

## One numerical miss

Fight ID: `47abea85-6f5a-54e9-ab10-fc83e0690b97`.

Original maximum occupancy error: 3.2814268525e-8, above the required 1e-8. Its scaled gradient was 9.9491766433e-13, below frozen gtol=1e-12. Bounded TRF can therefore terminate successfully near the lower-return boundary before satisfying the separately required occupancy criterion.

An independent algebraic root with analytic Frechet Jacobian supplies nonnegative returns approximately [0.0339055225551, 0.0000912556634836] per minute. It meets the original return bounds, occupancy, reward, reset-flux, normalization and conditional identity checks. A diagnostic TRF run with the same bounds/initialization/ftol/xtol/max_nfev and gtol=1e-15 also reaches an occupancy residual of 2.7756e-17. This numerical diagnostic is not applied to POC-B and is not a replacement frozen arm.

## Implementation review and practical repair

No measurement-loader or matrix-engine bug explains the bulk failure. The original equations and fixed solver were implemented as frozen. In 1,836 of 1,838 rejected fits, at least one normalized return was already below 1e-6; both achieved ground targets were undershot in every rejected fit. Certified proofs confirm that eliminating return time or improving minimization cannot supply the missing occupancy on 1,837 rows.

The problematic combination is independently prescribed generic decision-control occupancy plus takedown-only entries, competing absorption and five-minute standing resets. Decision CTRL is explicitly not observed ground time; forcing it to be an exact actor-ground occupancy constraint is incompatible with these fixed measured entry flows on many rows.

The next substantive repair needs a separately frozen opportunity-mapping contract. It should investigate using control identity as uncertain retention evidence with occupancy determined by a physically coherent entry/persistence process, or verify justified additional entry mechanisms before adding them. It must preserve support and action-reward semantics, prove real-state feasibility before scoring, and avoid outcome-selected clipping or multipliers. This diagnosis does not identify which replacement is scientifically best; it does establish that a larger solver budget cannot fix the current frozen mapping.

## Validation

Three mathematical tests cover hundreds of real interval boxes, a known feasible construction and a known impossible zero-terminal construction. All 4,260 analytic certificates/enclosures and all 247 exhaustive covers regenerate from prediction-only records. The numerical witness independently satisfies every relevant frozen physical/conservation tolerance. Original PR165/166 evidence stays hash-locked. No outcomes were scored, no failed fight was dropped, and no probability was substituted.
