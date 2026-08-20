# Official UFC FightMetric semantics audit

Generated: 2026-08-20T17:30:28.583936Z
Snapshot: `data/raw/ufc_fightmetric_official/20260820T123046Z`

## Round 0

Additivity verdict: **NOT YET SUPPORTED**.
Decisive fields: 29; near-unanimous exact fields: 15.

| Field | Compared groups | Exact fraction | Mean abs diff |
|---|---:|---:|---:|
| knock_down | 10954 | 0.987402 | 0.0133 |
| sig_str_att | 10953 | 0.999817 | 0.0226 |
| sig_str_land | 15795 | 0.999747 | 0.0068 |
| tot_str_att | 15794 | 0.999810 | 0.0170 |
| tot_str_land | 15794 | 0.999810 | 0.0073 |
| grap_take_att | 15795 | 0.999747 | 0.0010 |
| grap_take_land | 15795 | 0.999937 | 0.0001 |
| grap_sub_att | 15795 | 0.999937 | 0.0001 |
| grap_rev_land | 14093 | 0.999858 | 0.0001 |
| grap_stand_land | 10447 | 1.000000 | 0.0000 |
| dist_str_att | 15793 | 0.999873 | 0.0154 |
| dist_str_land | 15793 | 0.999873 | 0.0062 |
| clinch_str_att | 11000 | 0.999818 | 0.0004 |
| clinch_str_land | 11000 | 0.999909 | 0.0001 |
| ground_str_att | 15793 | 1.000000 | 0.0000 |
| ground_str_land | 15793 | 1.000000 | 0.0000 |
| standing_time | 10640 | 0.529887 | 0.6389 |
| neutral_time | 10636 | 0.469725 | 0.7287 |
| distance_time | 10640 | 0.445677 | 0.7568 |
| clinch_time | 10640 | 0.675752 | 0.3703 |
| ground_time | 4880 | 0.688525 | 0.5414 |
| control_time | 10640 | 0.725470 | 0.3404 |
| ground_ctl_time | 10640 | 0.840320 | 0.1969 |
| guard_ctl_time | 10640 | 0.958365 | 0.0449 |
| half_guard_ctl_time | 10640 | 0.965226 | 0.0374 |
| side_ctl_time | 10640 | 0.987500 | 0.0133 |
| mount_ctl_time | 10640 | 0.974718 | 0.0327 |
| back_ctl_time | 10640 | 0.985808 | 0.0149 |
| msc_ground_ctl__time | 10488 | 0.925629 | 0.0800 |

## Identity status

No FightMetric↔Greco crosswalk is asserted by this audit. FightMetric rows have fightmetric ID + corner but no fighter/date identity. The next acquisition step is an official fight-node bridge; display-name-only matching remains prohibited.

## Coverage-order warning

The JSON report includes coverage by Drupal internal-ID bins to locate where rich fields turn on/off. Those bins are **not calendar eras**. Calendar-year coverage must wait for a verified fight/date identity bridge.

## Greco identity inventory

Pinned raw snapshot: `data/raw/greco1899/8e40eb945e11`

- `ufc_event_details.csv` identity candidates: EVENT, URL
- `ufc_fight_details.csv` identity candidates: EVENT, URL
- `ufc_fight_results.csv` identity candidates: EVENT, URL
- `ufc_fight_stats.csv` identity candidates: EVENT, FIGHTER
- `ufc_fighter_details.csv` identity candidates: URL
- `ufc_fighter_tott.csv` identity candidates: FIGHTER, URL
