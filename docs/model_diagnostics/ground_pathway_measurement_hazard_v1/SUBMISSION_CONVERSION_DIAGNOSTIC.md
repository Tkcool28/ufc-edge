# Submission conversion diagnostic

Conversion preserves coherent successes and recorded attempts; finishes with zero recorded attempts are excluded from conversion trials, not repaired. Attempt records are not independent threat trials. Of 8520 fighter sides, 4795 have positive prior denominators. Median denominator 1; median effective support 1/51=0.019608. Fixed prior is 50 attempts; population/division means are training-only.

Within-division/year residual raw variance 0.108936 falls to 0.000337; removed fraction 99.690557%. This is empirical variance compression on supported rows, not a posterior uncertainty calculation. Raw variance is strongly inflated by tiny supports. Weakening this prior was not tested as a replacement.

| diagnostic | conversion_weighted | full_SUB | LL | Brier |
| --- | --- | --- | --- | --- |
| primary | 0.293697 | 0.127442 | 0.627949 | 0.217752 |
| oracle_conversion_pool | 0.307234 | 0.128964 | 0.625456 | 0.217339 |

The original pooled-conversion ablation LL 0.628936 versus identity0.627949 shows only a small fighter-conversion contribution. Training aggregate replacement LL 0.625456 recovers 12.36% of the Arm C LL gap and 3.07% of mean SUB deficit; this is far less than opportunity checks. Broad compression alone does not support classification C. Raw supports, priors, coherent trial counts and posterior distribution are saved.

Diagnostic only. No constants selected, replacement model trained, frozen definitions changed, prospective outcomes accessed or promotion authorized.
