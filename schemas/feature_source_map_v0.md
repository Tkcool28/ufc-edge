# Feature-to-Source Map v0

This document maps the UFC model master-plan feature inventory to the pinned Greco1899 UFCStats snapshot. It is a source-capability audit, **not yet the frozen feature formula contract**.

Statuses:

- **DIRECT** — required raw observation is present.
- **DERIVED** — computable from historical observations in the selected files once formula/window is frozen.
- **PARTIAL** — useful proxy inputs exist, but the named concept is not fully observed.
- **UNSUPPORTED** — Greco's UFCStats round aggregates do not contain the required information.

## Source files selected

| Source file | Keep? | Primary use |
|---|---:|---|
| `ufc_event_details.csv` | Yes | event date, location, event identity |
| `ufc_fight_details.csv` | Yes | bout identity, fight URL |
| `ufc_fight_results.csv` | Yes | outcome, weight class, method, finish round/time |
| `ufc_fight_stats.csv` | Yes | per-round strikes, takedowns, control, submission attempts, reversals |
| `ufc_fighter_details.csv` | Yes | fighter identity/name/URL |
| `ufc_fighter_tott.csv` | Yes | height, reach, DOB, weight snapshot, stance snapshot |

## Feature-family coverage

| Master-plan family | Status | Greco raw support / limitation |
|---|---|---|
| Duration and pace | DIRECT / DERIVED | Result finish round/time plus round-level stats support fight duration and per-minute/per-round pace. |
| Control and grappling | DIRECT / DERIVED | `CTRL`, `TD`, `SUB.ATT`, `REV.` available per round. |
| Opponent-adjusted control | DERIVED | Build from fighter/opponent historical control observations with strictly prior fights. |
| Takedown structure | DIRECT / DERIVED | `TD` contains landed/attempted and `TD %`; parse landed and attempts separately. |
| Submission family | DIRECT / DERIVED | Submission attempts per round plus result method/finish information. Exact feature formulas still need freezing. |
| Submission prevention family | PARTIAL / DERIVED | Opponent `SUB.ATT` and submission losses support attempts-conceded and finish-prevention measures. Named mechanics such as `safe_wrap_equivalent_rate` are not directly observed. |
| Striking family | DIRECT / DERIVED | Significant/total strikes, accuracy, head/body/leg, distance/clinch/ground, and knockdowns are present. |
| Active stride speed | UNSUPPORTED | No tracking, footwork, distance-traveled, or step/stride observations in UFCStats round aggregates. |
| Striking opportunity family | PARTIAL / DERIVED | Attempt counts by strike location/position allow several opportunity and realization rates. Concepts requiring unobserved possible opportunities or event-level thrust/counter states need a proxy or another source. |
| Age / physical / style | DIRECT / DERIVED | DOB + event date supports fight-time age; height/reach direct. `stance_snapshot` and `weight_lb_snapshot` are not guaranteed historical-at-fight values. |
| Damage family | PARTIAL / DERIVED | Knockdowns and strikes absorbed support damage proxies; impact severity, wobble, cut, and medical/tracking signals are absent. |
| Strike Markov state-transition family | UNSUPPORTED for true strike-event chain | Greco is round-level aggregate data, not ordered strike-event data. Round-to-round state transitions could be a separate proxy, but must not be mislabeled as strike-event Markov states. |
| Creation Over Expectation (COE) | DERIVED / MODEL-DEFINED | Historical observed inputs can support expected-vs-actual constructions after target and expectation model are precisely defined. Not a raw field. |
| Endurance / cardio | DERIVED | Round-level observations support pace/output/control change by round and late-vs-early degradation. |
| Opponent-adjusted cardio | DERIVED | Requires historical opponent baselines and strict pre-fight replay. |
| Fight-history family | DIRECT / DERIVED | Event dates + outcomes support fight number, days since last fight, recent W/L, streak, and rolling win rate. |

## Raw field inventory from Greco

### Events
`EVENT`, `URL`, `DATE`, `LOCATION`

### Fight details
`EVENT`, `BOUT`, `URL`

### Fight results
`EVENT`, `BOUT`, `OUTCOME`, `WEIGHTCLASS`, `METHOD`, `ROUND`, `TIME`, `TIME_FORMAT`, `REFEREE`, `DETAILS`, `URL`

### Round stats
`EVENT`, `BOUT`, `ROUND`, `FIGHTER`, `KD`, `SIG.STR.`, `SIG.STR. %`, `TOTAL STR.`, `TD`, `TD %`, `SUB.ATT`, `REV.`, `CTRL`, `HEAD`, `BODY`, `LEG`, `DISTANCE`, `CLINCH`, `GROUND`

### Fighter identity
`FIRST`, `LAST`, `NICKNAME`, `URL`

### Tale of the tape
`FIGHTER`, `HEIGHT`, `WEIGHT`, `REACH`, `STANCE`, `DOB`, `URL`

## Feature-contract gates still required

Before a feature is production-eligible, freeze all of the following, as required by the master plan:

1. exact feature name and formula;
2. window type and length;
3. mean vs median or other aggregation;
4. clean-fight vs all-fight inclusion rule;
5. missing-data policy;
6. zero-attempt policy;
7. exact possession/opportunity denominator;
8. cap/floor/winsorization rule;
9. whether slower-moving long-window totals remain when recent-form features are added;
10. proof that target-fight information cannot enter the feature calculation.

No feature with an undefined denominator should enter a production training matrix.
