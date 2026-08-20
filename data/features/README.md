# Feature Data

Feature tables are pre-fight views derived from canonical history. They must be reproducible as of the target fight date.

## `shared/`

Reusable features whose definitions are frozen in the canonical feature contract. Examples will include historical pace, control, takedown, striking, age, cardio, and fight-history measures once formulas are locked.

A shared feature must have one repository-wide meaning. Models may choose whether to use it, but may not silently redefine it.

## `model_specific/`

Model-only transformations, interactions, embeddings, calibration inputs, or experimental features that should not alter the canonical/shared meaning of the source data.

## Target grain

The master-plan training grain is one row per fighter per fight, identified by `fighter_id`, `opponent_id`, `fight_date`, and `fight_id` for uniqueness.

## Mandatory contract for every shared feature

- exact formula;
- source fields;
- history window;
- aggregation statistic;
- clean/all inclusion rule;
- missing-data behavior;
- zero-attempt behavior;
- denominator/opportunity definition;
- cap/floor/winsorization behavior;
- whether a long-window companion remains alongside recent form;
- no-look-ahead test.

Same-fight result/statistics may be labels or future history, never predictors for that target row.
