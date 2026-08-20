# Official UFC FightMetric semantics audit

Generated: 2026-08-20T17:36:07.273156Z
Snapshot: `data/raw/ufc_fightmetric_official/20260820T123046Z`

## Round 0

Verdict: **SUPPORTED AS SOURCE FIGHT SUMMARY**.
Count support: 15/16 fields; time support: 13/13 fields.

Count fields use exact additivity after duplicate-round groups are excluded. Time fields use explicit tolerance because the source summary frequently differs from summed rounded round values by ~1 second.

| Field | Groups | Exact | Within 2s | Mean abs diff | P99 abs diff |
|---|---:|---:|---:|---:|---:|
| knock_down | 10954 | 0.987402 | 0.999909 | 0.0133 | 1.00 |
| sig_str_att | 10953 | 0.999817 | 0.999817 | 0.0226 | 0.00 |
| sig_str_land | 15793 | 0.999873 | 0.999873 | 0.0063 | 0.00 |
| tot_str_att | 15793 | 0.999873 | 0.999873 | 0.0157 | 0.00 |
| tot_str_land | 15793 | 0.999873 | 0.999873 | 0.0063 | 0.00 |
| grap_take_att | 15793 | 0.999873 | 0.999873 | 0.0008 | 0.00 |
| grap_take_land | 15793 | 1.000000 | 1.000000 | 0.0000 | 0.00 |
| grap_sub_att | 15793 | 1.000000 | 1.000000 | 0.0000 | 0.00 |
| grap_rev_land | 14091 | 1.000000 | 1.000000 | 0.0000 | 0.00 |
| grap_stand_land | 10447 | 1.000000 | 1.000000 | 0.0000 | 0.00 |
| dist_str_att | 15793 | 0.999873 | 0.999873 | 0.0154 | 0.00 |
| dist_str_land | 15793 | 0.999873 | 0.999873 | 0.0062 | 0.00 |
| clinch_str_att | 11000 | 0.999818 | 0.999909 | 0.0004 | 0.00 |
| clinch_str_land | 11000 | 0.999909 | 1.000000 | 0.0001 | 0.00 |
| ground_str_att | 15793 | 1.000000 | 1.000000 | 0.0000 | 0.00 |
| ground_str_land | 15793 | 1.000000 | 1.000000 | 0.0000 | 0.00 |
| standing_time | 10640 | 0.529887 | 0.991541 | 0.6389 | 2.00 |
| neutral_time | 10636 | 0.469725 | 0.990410 | 0.7287 | 2.00 |
| distance_time | 10640 | 0.445677 | 0.988910 | 0.7568 | 3.00 |
| clinch_time | 10640 | 0.675752 | 0.997180 | 0.3703 | 2.00 |
| ground_time | 4880 | 0.688525 | 0.996311 | 0.5414 | 2.00 |
| control_time | 10640 | 0.725470 | 0.997650 | 0.3404 | 2.00 |
| ground_ctl_time | 10640 | 0.840320 | 0.998966 | 0.1969 | 2.00 |
| guard_ctl_time | 10640 | 0.958365 | 1.000000 | 0.0449 | 1.00 |
| half_guard_ctl_time | 10640 | 0.965226 | 0.999906 | 0.0374 | 1.00 |
| side_ctl_time | 10640 | 0.987500 | 1.000000 | 0.0133 | 1.00 |
| mount_ctl_time | 10640 | 0.974718 | 0.999906 | 0.0327 | 1.00 |
| back_ctl_time | 10640 | 0.985808 | 1.000000 | 0.0149 | 1.00 |
| msc_ground_ctl__time | 10488 | 0.925629 | 0.999905 | 0.0800 | 1.00 |

## Duplicate source rounds

Duplicate fighter/round keys: **714**; exact duplicate keys: **0**; conflicting keys: **714**.

No duplicate row is silently dropped by this audit.

## Identity status

No FightMetric↔Greco crosswalk is asserted yet. FightMetric rows have FightMetric ID + corner but no fighter/date identity. The next acquisition step is the official fight-node bridge; display-name-only matching remains prohibited.

## Coverage-order warning

The JSON report includes coverage by Drupal internal-ID bins to locate where rich fields turn on/off. Those bins are **not calendar eras**. Calendar-year coverage requires a verified fight/date identity bridge.

## Greco identity inventory

Pinned raw snapshot: `data/raw/greco1899/8e40eb945e11`

- `ufc_event_details.csv` identity candidates: EVENT, URL
- `ufc_fight_details.csv` identity candidates: EVENT, URL
- `ufc_fight_results.csv` identity candidates: EVENT, URL
- `ufc_fight_stats.csv` identity candidates: EVENT, FIGHTER
- `ufc_fighter_details.csv` identity candidates: URL
- `ufc_fighter_tott.csv` identity candidates: FIGHTER, URL
