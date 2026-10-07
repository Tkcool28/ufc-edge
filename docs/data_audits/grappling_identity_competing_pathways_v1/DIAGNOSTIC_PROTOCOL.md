# Grappling identity diagnostic protocol V1

Fixed before computing new descriptive results. This is not a predictive preregistration and the historical PR #125 outcomes have already been inspected.

Use immutable PR #158 source tables, verify their entire manifest, independently reconcile complete bout counts to canonical rounds, and retain the 2026-08-15 seal. All states require event_date strictly less than target event date; same-date bouts are excluded. Do not train, cluster, label fighters, optimize thresholds, or alter predictions or memberships.

Candidate definitions are enumerated in tools/audits/audit_grappling_identity_v1.py. Every ratio uses complete bouts jointly observed for its numerator and denominator, and reports matched bouts and missingness. Generic control minutes are behavioral proxies only. SUB attempts and ground significant strikes have unequal units; their ratio is exploratory, not a probability or share. No weighted activity composition is invented.

Support screens are sensitivity descriptions, not reliability gates: three matched bouts plus 15 total elapsed minutes for time rates, five attempts/completions for TD ratios, five control minutes for control proxies, 20 significant ground attempts for SUB/ground comparison, and three finish wins for early-finish share. These screens do not select B3/B5 subgroups or model inputs. Report positive-denominator and screened results together.

Stability: unique fighters with six prior bouts at each January 1 boundary; compare first three versus next three NONOVERLAPPING bouts, excluding same-date split boundaries. Spearman coefficients are reported only for at least 25 fighters. Repeated boundary cohorts are not independent replications. Full prior-history coverage, fighter development and opponent selection remain caveats.

Comparable access: outcome-blind TD-attempt-rate quartiles within each boundary's supported training-fighter snapshot; report continuous control/SUB/ground dimensions within each quartile. Quartiles are diagnostic strata only, never fixed style thresholds. They do not match opponent strength or ground opportunity.

Timing: unique prior bouts, method and scheduled-length strata; repeat R1 tendency using first and second strictly ordered finish wins. No attempt timestamps or time from access to finish can be inferred. Compare decision control to own SUB/KO wins within the same fighter, both raw totals and elapsed shares. Also preserve all prior SUB/KO/decision subsets including losses in separate pre-fight state tables.

B3/B5: all unchanged outer-scored cell bouts, both fighter sides, annual distributions and support; retain frozen finish-only calibration context without estimating new subgroup performance. A cell match does not identify which side supplied every criterion, so two-side tables do not label an attacker.

Conclusion must assess observable tendencies separately from ground-state mechanisms and intent. One next frozen experiment recommendation only; no automatic authorization to fit.
