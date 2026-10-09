# State exposure definitions

| State | Eligibility / actions | Entry | Exit | Exposure denominator |
|---|---|---|---|---|
| STANDING | Both actors may attempt TD; unchanged standing KO pathway | Fight/round start; ground return | Successful TD to corresponding actor-ground; standing KO | E_S minutes for both TD streams |
| GROUND_A_ACTIVE | A SUB and significant GnP; continued control is self occupation | Successful A TD | A ground SUB/KO; derived return | E_GA, not either fighter's whole fight time |
| GROUND_B_ACTIVE | B SUB and significant GnP | Successful B TD | B ground SUB/KO; derived return | E_GB |
| KO | Absorbing | Standing/ground KO | None | Terminal probability, no action opportunity |
| SUB | Absorbing | Converting ground attempt | None | Terminal probability |

GA/GB identify the active actor only; no mount/guard/back or verified top/bottom position. Bottom submissions and non-TD ground entry remain unmodeled. Reset maps surviving S/GA/GB mass to S between rounds; KO/SUB remain absorbing. Final surviving mass becomes raw DEC by expiration. Mandatory clock expiration is not measured escape. Conditional method and three-way composition keep archived MOV0 F external.

Exposure shares use E_state/E_alive (ratio of expectations). They sum to1 across live states; calendar-time probabilities sum to1 including terminal mass. These are different normalizations; do not divide action rewards by scheduled 15/25 minutes after simulated early finishes.

Contract-only freeze. This task uses no real fighter/fight inputs in the inverse solver, generates no POC-B predictions, and scores no outcomes.
