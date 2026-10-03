# FightMetric / position-time decision

**Usable for coarse, partial positional diagnostics: yes. Usable as broad exact historical grounded-duration exposure for this mechanism experiment: no.** The repository contains actual measurements and completed ingestion/audits, not just a proposed source.

Source: official UFC.com Drupal JSON:API `fight_stat` snapshot `20260820T123046Z`, stored raw pages and manifest; builder `pipelines/build_canonical_fightmetric_position_v0.py`; output `data/canonical/v0/fighter_round_position.csv`. Identity, round-summary, corner, duplicate-version and bucket gates are documented in the lineage report. Canonical position source has 32,156 rows, 6,803 fights and 2,459 fighters; quarantine has 5,955 field/source items (4,806 missing fight identity, 996 duplicate-version source items, 153 out-of-range buckets). Quarantine items are not interchangeable with numbers of excluded fights.

## Available fields and units

Standing, neutral, distance, clinch, ground, ground control, guard, half guard, side, mount, back and misc ground-control buckets plus standups are stored. For each time bucket b, the canonical contract provides bounds b×60..b×60+59 seconds, to intersect with observed elapsed round time. These are quantization bounds, not measured exact duration. Raw generic `control_time` matched floor(Greco precise control seconds/60) in 97.454% of 23,876 comparisons; broader time-family relationships provide corroboration, not proof of independently documented vendor seconds. Values >5 and unresolved versions are withheld. The new duration-bound check additionally detects 6 impossible lower bounds for ground time; those pairs are excluded diagnostically.

Ground occupancy can include either fighter on top/bottom; ground control describes a fighter's control, not the common opportunity denominator. Back/mount buckets may describe positional occupancy at coarse resolution but not submission threat quality. Zero buckets do not prove absence of position; intervals allow short exposure. Standups are sourced from `grap_stand_land`; no escape/standup attempt or event-linked opportunity count is present.

## Canonical year coverage against expected rounds

| year | field | fights | expected_fighter_rounds | observed_rows | missing_pct | observed_zero_rows |
| --- | --- | --- | --- | --- | --- | --- |
| 2013 | ground_bucket_min | 383 | 1784 | 658 | 63.12 | 344 |
| 2013 | ground_control_bucket_min | 383 | 1784 | 720 | 59.64 | 539 |
| 2013 | standups | 383 | 1784 | 1536 | 13.90 | 1130 |
| 2014 | ground_bucket_min | 503 | 2402 | 1458 | 39.30 | 740 |
| 2014 | ground_control_bucket_min | 503 | 2402 | 1509 | 37.18 | 1122 |
| 2014 | standups | 503 | 2402 | 1828 | 23.90 | 1334 |
| 2015 | ground_bucket_min | 473 | 2256 | 1540 | 31.74 | 866 |
| 2015 | ground_control_bucket_min | 473 | 2256 | 1639 | 27.35 | 1258 |
| 2015 | standups | 473 | 2256 | 1896 | 15.96 | 1459 |
| 2016 | ground_bucket_min | 489 | 2402 | 1850 | 22.98 | 1082 |
| 2016 | ground_control_bucket_min | 489 | 2402 | 2030 | 15.49 | 1588 |
| 2016 | standups | 489 | 2402 | 2086 | 13.16 | 1597 |
| 2017 | ground_bucket_min | 455 | 2212 | 1670 | 24.50 | 1044 |
| 2017 | ground_control_bucket_min | 455 | 2212 | 1774 | 19.80 | 1445 |
| 2017 | standups | 455 | 2212 | 1798 | 18.72 | 1433 |
| 2018 | ground_bucket_min | 474 | 2300 | 1814 | 21.13 | 1086 |
| 2018 | ground_control_bucket_min | 474 | 2300 | 2047 | 11.00 | 1630 |
| 2018 | standups | 474 | 2300 | 2108 | 8.35 | 1667 |
| 2019 | ground_bucket_min | 512 | 2524 | 1156 | 54.20 | 742 |
| 2019 | ground_control_bucket_min | 512 | 2524 | 1429 | 43.38 | 1162 |
| 2019 | standups | 512 | 2524 | 1298 | 48.57 | 1061 |
| 2020 | ground_bucket_min | 452 | 2206 | 88 | 96.01 | 54 |
| 2020 | ground_control_bucket_min | 452 | 2206 | 406 | 81.60 | 325 |
| 2020 | standups | 452 | 2206 | 122 | 94.47 | 104 |
| 2021 | ground_bucket_min | 501 | 2506 | 0 | 100.00 | 0 |
| 2021 | ground_control_bucket_min | 501 | 2506 | 782 | 68.79 | 629 |
| 2021 | standups | 501 | 2506 | 0 | 100.00 | 0 |
| 2022 | ground_bucket_min | 508 | 2458 | 0 | 100.00 | 0 |
| 2022 | ground_control_bucket_min | 508 | 2458 | 2424 | 1.38 | 1919 |
| 2022 | standups | 508 | 2458 | 0 | 100.00 | 0 |
| 2023 | ground_bucket_min | 516 | 2482 | 0 | 100.00 | 0 |
| 2023 | ground_control_bucket_min | 516 | 2482 | 2462 | 0.81 | 1948 |
| 2023 | standups | 516 | 2482 | 0 | 100.00 | 0 |
| 2024 | ground_bucket_min | 508 | 2612 | 0 | 100.00 | 0 |
| 2024 | ground_control_bucket_min | 508 | 2612 | 2584 | 1.07 | 2048 |
| 2024 | standups | 508 | 2612 | 0 | 100.00 | 0 |
| 2025 | ground_bucket_min | 508 | 2432 | 0 | 100.00 | 0 |
| 2025 | ground_control_bucket_min | 508 | 2432 | 2360 | 2.96 | 1900 |
| 2025 | standups | 508 | 2432 | 0 | 100.00 | 0 |
| 2026 | ground_bucket_min | 333 | 1558 | 0 | 100.00 | 0 |
| 2026 | ground_control_bucket_min | 333 | 1558 | 1518 | 2.57 | 1234 |
| 2026 | standups | 333 | 1558 | 0 | 100.00 | 0 |

Full 1993–2026 annual data are in `year_field_coverage.csv`; `year_position_coverage.csv` additionally covers every stored positional family (including guard/half/side/mount/misc/clinch/standing/neutral/distance), not only the ground examples above; expected rounds for bouts with unknown terminal round are not invented. The prior raw dated-source audit spans 1993–2026; it is a different denominator from this canonical coverage table. Grounded time largely covers 2013–2018, partially 2019–2020, and is absent from recent source eras. Ground-control data persist but cannot repair the missing occupancy variable.

## Reproducibility and temporal governance

All original raw pages match their original manifest SHA256; all input tables, semantic code and source audits are enumerated in `SOURCE_IDENTITIES.json`. This audit reuses canonical transport identities and does not refresh external payloads. Historical states select only earlier event dates; source acquisition was in 2026, so old publication versions/revisions cannot be asserted. Missing years and ambiguous identities remain missing; no later stat fills an earlier gap.

## Incremental value and rights

Incremental beyond F02: partial coarse ground/position occupancy and stand-up counts. These could support an interval-aware, coverage-restricted *measurement diagnostic* after semantic review, but not exact activity per grounded minute across frozen folds. Generic CTRL, reversals and ground significant-strike composition already exist in F01/F02, so those are representation candidates rather than newly acquired measurements. Additional raw ground-strike splits need semantic review.

No source-specific grant for modeling/redistribution was located in the inspected repo manifests or candidate notes. A current read-only check of official UFC terms URLs on 2026-10-03 returned fetch failures/403; `EXTERNAL_SOURCE_CHECK.json` records that limitation. Public JSON access and the mirror's availability do not establish a transferable data license. No purchase, outreach, fresh data acquisition or legal conclusion was undertaken. The provider-entitlement sample gate must establish permissible storage/model-development use and future reproducibility.

## Exact missing measurements

Common ground-state elapsed seconds per bout/round (including bottom and scrambles); distinct attacker control/top duration; identifiable ground entries; escape/stand-up opportunity and successful returns-to-standing with actor/context; positional transition ordering if scramble classes are required; source definitions and version/availability dates. Exact ground duration is the central missing denominator, not another TD-defense percentage. Phase-tagged SUB attempts are additionally necessary if the claim is creation occurring specifically on the ground, rather than overall SUB activity normalized by ground exposure.
