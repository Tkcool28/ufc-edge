# UFC EDGE — Missingness Point-in-Time Safety V1

Status: audit governance addition

## Rule

**Missingness and data availability must be audited independently for point-in-time safety.**

A feature value can be historically legitimate while the fact that the value is present or absent in a reconstructed dataset can still encode information learned only after the target event.

## Known reference case

M1 reach missingness demonstrated the failure mode. Historical reach availability in affected 2015–2018 rows strongly tracked the fighter's later UFC career persistence even when the completed true reach advantage did not explain the winner separation. The underlying reach measurement was a static athlete attribute; the missing/not-missing state was not temporally safe.

## Prohibited assumption

Do **not** assume:

> static attribute backfill means missingness is safe.

Static-value semantics and availability semantics are separate contracts.

## Required review for every modeled feature family

For the underlying value, verify the information cutoff, canonical provenance, historical semantics, and whether backfill is allowed.

Separately for missingness / availability, verify:

- what causes a value to be absent;
- whether absence can depend on later profile enrichment, later source coverage, roster survival, future career duration, identity reconciliation performed with later evidence, or another future-derived process;
- whether missing/not-missing state has unusually strong target association;
- whether availability is more strongly associated with future career outcomes than with pre-fight history;
- whether the effect is concentrated in older sparse-source eras and disappears in recent/live data;
- whether completed underlying values explain the apparent signal.

## Support and history features

Pre-fight support is not inherently leakage. Prior fight count, prior observed rounds, prior attempts, and similar quantities are allowed when they are accumulated strictly from information available before the target fight.

A support feature becomes suspect when its existence or completeness depends on later source enrichment rather than only prior observations.

## Model review requirement

Any new model feature family that emits an explicit missingness channel, relies on imputation, or has source-dependent eligibility must document both:

1. value point-in-time safety; and
2. missingness / availability point-in-time safety.

A successful value-level leakage check does not satisfy the missingness check.

## Audit evidence

The authoritative quantitative evidence for M1 is produced by the read-only `M1 Missingness Temporal Leakage Audit V1` workflow and its frozen artifact. This governance document records the rule; it does not alter DATA, F00, F01, F02, or model methodology.
