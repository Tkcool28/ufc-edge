# Measurement to hazard matrix

| Component | UFC EDGE measurement | Required quantity | Current mapping | Evidence quality | Likely bias | Priority | Holmes treatment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ground access | prior TD attempts/elapsed | entry per standing minute | access*sqrt(success*opponent failure complement) | observed numerator; wrong opportunity semantics | downward realized entries | high | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |
| ground occupancy | decision CTRL share | actor state minutes | bilateral CTMC with clipped geometric CTRL | proxy; no true ground target | shortfall against proxy | highest | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |
| control retention | decision CTRL and access | episode duration | stationary inverse | assumption; distinct rates for entry/return | inconsistent occupancy | highest | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |
| return-to-standing | no escape observation | state exit hazard | own access*conversion*(1-q)/q | estimated proxy only | too rapid relative proxy | highest | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |
| submission work | all-history attempts/elapsed | attempts/ground minute | sqrt(work/own CTRL * faced/allowed CTRL) | observed counts; denominator mismatch | under-reconstructed aggregate activity | highest | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |
| submission conversion | coherent successes/attempts | threat conversion | 50-attempt shrink then geometric pairing | tiny denominators; missing zero-attempt wins | extreme compression; not main mean deficit | medium | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |
| GnP activity | significant ground attempts/elapsed | actions/ground minute | same CTRL normalization | no bottom/action quality | opportunity undercount; noisier | medium | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |
| ground KO hazard | KO labels plus strike shares | KO/action | latent equal-attempt allocation pooled | finish location not observed | unknown | medium | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |
| standing KO hazard | KO/KD rates and vulnerability | KO/standing minute | geometric rates and latent ground subtraction | governed inputs; new mechanistic map | too much relative SUB in A1/A4 | high | See corresponding row in HOLMES_UFC_EDGE_COMPONENT_COMPARISON.md |

Directionality: entry, control, creation, conversion and GnP all include opponent histories; standing KO does too. It would be incorrect to call the entire simulator one-sided. Opponent SUB-creation multiplier median0.9892, interquartile0.7025–1.3221, 5th–95th0.4090–2.1608. Conversion defense support is only3.42% on average; ground KO conversion is population-level; return has no separate escape effect. These are allowed-behavior modifiers, not opponent-adjusted latent skills. Exactly one of the five ground mechanisms has no independently measured defender state: return/escape; pooled ground KO conversion also lacks personal finishing resistance. No causal fraction of accuracy attributable to missing defense is identifiable.

Diagnostic only. No constants selected, replacement model trained, frozen definitions changed, prospective outcomes accessed or promotion authorized.
