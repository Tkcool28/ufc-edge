# Preflight feasibility

Starting main: `222c7a76bc75bd66e0517930863ebeab41baf99f`. Branch: `feat/ground-opportunity-consistent-poc-v2`.

Status: **BLOCKED_OPPORTUNITY_FEASIBILITY**. No target outcomes recovered for scoring; zero outcomes scored.

Supported: 1008/2047 = 49.242794%. All outer: 2422/4260 valid; **1838 unavailable**. Required: supported >=99%, outer 100%.

| code | count |
| --- | --- |
| INVALID_INPUT | 0 |
| INVALID_CONVERSION | 0 |
| INVALID_PROXY_TARGET | 0 |
| INFEASIBLE_SIMPLEX | 0 |
| NO_POSITIVE_RESET_BUDGET | 0 |
| NUMERICAL_RESET_BUDGET | 0 |
| INFEASIBLE_FINITE_ROUND_CEILING | 0 |
| UNRESOLVED_FINITE_ROUND_TARGET | 1838 |
| REWARD_RESIDUAL | 0 |
| RESET_FLUX_RESIDUAL | 0 |
| NUMERICAL_TRANSITION | 0 |

## outer_year

| cell | rows | valid | invalid | certified_structural |
| --- | --- | --- | --- | --- |
| 2018 | 470 | 286 | 184 | 0 |
| 2019 | 507 | 277 | 230 | 0 |
| 2020 | 443 | 237 | 206 | 0 |
| 2021 | 492 | 244 | 248 | 0 |
| 2022 | 505 | 279 | 226 | 0 |
| 2023 | 505 | 297 | 208 | 0 |
| 2024 | 502 | 297 | 205 | 0 |
| 2025 | 504 | 294 | 210 | 0 |
| 2026 | 332 | 211 | 121 | 0 |

## division

| cell | rows | valid | invalid | certified_structural |
| --- | --- | --- | --- | --- |
| Bantamweight | 488 | 349 | 139 | 0 |
| Catch Weight | 59 | 41 | 18 | 0 |
| Featherweight | 502 | 347 | 155 | 0 |
| Flyweight | 252 | 219 | 33 | 0 |
| Heavyweight | 316 | 113 | 203 | 0 |
| Light Heavyweight | 319 | 111 | 208 | 0 |
| Lightweight | 576 | 369 | 207 | 0 |
| Middleweight | 476 | 297 | 179 | 0 |
| Welterweight | 546 | 259 | 287 | 0 |
| Women's Bantamweight | 158 | 40 | 118 | 0 |
| Women's Featherweight | 27 | 8 | 19 | 0 |
| Women's Flyweight | 266 | 133 | 133 | 0 |
| Women's Strawweight | 275 | 136 | 139 | 0 |

## support_stratum

| cell | rows | valid | invalid | certified_structural |
| --- | --- | --- | --- | --- |
| 0 | 843 | 644 | 199 | 0 |
| 1-2 | 1178 | 691 | 487 | 0 |
| 3-7 | 1416 | 694 | 722 | 0 |
| 8+ | 823 | 393 | 430 | 0 |

## scheduled_rounds

| cell | rows | valid | invalid | certified_structural |
| --- | --- | --- | --- | --- |
| 3 | 3837 | 2210 | 1627 | 0 |
| 5 | 423 | 212 | 211 | 0 |

Certified necessary-flow/simplex/zero-terminal ceiling failures: 0. Other unresolved/numerical rows: 1838. Solver nonconvergence is not a proof of mathematical impossibility. Full code-by-cell counts are in breakdown.json.

Classification **E**: construction is blocked by unresolved numerical inversion; no structural impossibility is certified. This concerns this fixed generic-state mapping and proxy targets, not every possible coarse ground architecture.
