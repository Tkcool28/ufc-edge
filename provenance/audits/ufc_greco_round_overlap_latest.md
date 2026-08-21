# Official UFC FightMetric vs Greco/UFCStats round audit

- Exact aligned fights: **6904**
- Matched fighter-round keys: **32612**
- Single-version keys: **32342**
- Multi-version keys: **270**

## Shared count-field agreement

- `knock_down`: 66/66 exact (100.000%)
- `sig_str_land`: 32175/32342 exact (99.484%)
- `sig_str_att`: 24229/24388 exact (99.348%)
- `tot_str_land`: 32171/32342 exact (99.471%)
- `tot_str_att`: 32167/32342 exact (99.459%)
- `grap_take_land`: 32317/32342 exact (99.923%)
- `grap_take_att`: 32278/32342 exact (99.802%)
- `grap_sub_att`: 66/66 exact (100.000%)
- `grap_rev_land`: 66/66 exact (100.000%)
- `head_sig_str_land`: 32184/32342 exact (99.511%)
- `head_sig_str_att`: 32173/32342 exact (99.477%)
- `body_sig_str_land`: 32206/32342 exact (99.579%)
- `body_sig_str_att`: 32201/32342 exact (99.564%)
- `legs_sig_str_land`: 32233/32342 exact (99.663%)
- `legs_sig_str_att`: 32245/32342 exact (99.700%)
- `dist_str_land`: 32179/32342 exact (99.496%)
- `dist_str_att`: 32180/32342 exact (99.499%)
- `clinch_sig_str_land`: 32229/32342 exact (99.651%)
- `clinch_sig_str_att`: 32218/32342 exact (99.617%)
- `ground_sig_str_land`: 24380/24428 exact (99.804%)
- `ground_sig_str_att`: 24378/24428 exact (99.795%)

## Archived `control_time` candidate semantics

- `raw_equals_seconds`: 7522/23876 (31.504%)
- `raw_times_60_equals_seconds`: 7631/23876 (31.961%)
- `raw_equals_floor_minutes`: 23268/23876 (97.454%)
- `raw_equals_nearest_minute`: 17791/23876 (74.514%)
- `raw_equals_ceil_minutes`: 7849/23876 (32.874%)

No FightMetric time-unit mapping and no duplicate-version selection are automatically promoted by this audit.
