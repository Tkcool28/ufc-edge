# Direct component comparison

Primary source: Holmes, McHale & Żychaluk, DOI 10.1016/j.ijforecast.2022.01.007, publisher PDF, sections 3–4,7, Appendix B. Download URL: https://prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com/05bdcbd7-50e1-4f75-95e5-693192fd2708 . No betting analysis performed.

| Component | Holmes treatment | UFC EDGE frozen POC |
|---|---|---|
| TD work | Poisson; standing-opportunity offset | Frozen total-time TD attempts/min applied only in standing |
| TD success | Binomial attack/defense | Geometric shrunk offense/complement defense |
| Ground control | CTRL times ground/(ground+clinch) technique share | Decision-only generic CTRL share; no positional advances |
| Persistence | Gamma control/landed TD | Stationary inverse from own access and directional share |
| SUB work | Poisson; estimated ground-control offset | Total-time shrunk rate divided by clipped decision CTRL |
| SUB conversion | Binomial attack/defense | Geometric 50-attempt pseudo-priors |
| Ground striking | Strike work, target, accuracy, power stages | Conditional significant-ground activity; latent pooled ground KO attribution |
| Return | Reciprocal predicted control/TD | Access*(1-q)/q; no measured escape |
| Attack effects | Fitted action coefficients | Descriptive shrunk histories |
| Defense effects | Fitted action coefficients | Allowed behavior; missing escape |
| Sparse history | Weak Cauchy priors; debuts excluded from test | Fixed support priors; debuts retained |
| Opportunity adjustment | SUB rate multiplier | No explicit multiplier; control normalization already present |

Submission formula: adjusted smr = 2*smr; conversion unchanged. They reported too few attempts, attributing this to missing submission-capable positions. The factor was selected for winner accuracy on 2017 validation after 2001–2016 fitting, alongside KO factor 0.4; final fitting used 2001–2017. No multiplier-specific sensitivity curve was published. This is empirical validation tuning, not a universal denominator correction.

Our inference: superficially similar undercount does not prove the same cause. UFC EDGE already normalizes SUB activity by control, but its reconstructed opportunity need not equal that denominator. The paper's validation-tuned correction cannot be copied into this audit or production. Its different population, debut policy, action model and target prevent a controlled performance comparison.
