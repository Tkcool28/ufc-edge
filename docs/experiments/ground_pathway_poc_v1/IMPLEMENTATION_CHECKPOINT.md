# GROUND PATHWAY POC V1 — implementation checkpoint (NOT RESULTS)

Status: ENGINE_SCAFFOLD_ONLY. Not a frozen predictive contract, not a validated or completed POC.
Starting main: `f70848818005e54d2db000ec73677f2fd27be033` (merged PR #161).
Source PR #161 evidence head: `57a0dbbcd460d4c46fc5683fee17742fe0e4c9a3`.
Branch: `feat/ground-pathway-simulator-poc-v1`. Never modify main or automatically merge.

## Engine boundary

`ground_pathway_poc/engine.py` propagates nonnegative, externally supplied
cause-specific intensities through Standing, Generic Ground (fighter A active),
Generic Ground (fighter B active), terminal KO, terminal Submission and
fight-expiration Decision. It uses a competing-exponential-event discretization
and sums state mass deterministically rather than sampling outcomes.
Hazards are **not estimated, trained, tuned or supplied here**. Fighter A/B
ground-state distinction preserves directional composition, not detailed positions.
One fixed 900-second scheduled duration is only an engine test default,
not the complete 3/5-round historical fight plan. There are no round breaks yet.

Critically, raw takedown attempts are not verified ground entries; generic CTRL
includes possible clinch and is not top-control/ground time; submission attempts
have recording discrepancies relative to finishes; GnP attempts are not observed
ground KO conversions; and escape/scramble is not measured. No rate may be
renamed as a transition hazard without a frozen, train-only calibration.
PR #161 concluded B, not authorization of a validated predictive system.

## Mandatory remaining work before any scored POC

1. Verify all pinned source bytes and saved Arm A/C/MOV0 prediction identities.
2. Freeze exact ability reconstruction from event_date < cutoff, numerator,
   denominator, completeness, prior fight/decision counts and division priors.
3. Freeze exposure, ESTIMATED_RETURN_TO_STANDING_PROXY, shrinkage,
   conversion/standing KO hazards, train-only calibration, prefit metrics,
   B3/B5 and A1/A2/A4 sample gates and identity ablation. No outer-outcome tuning.
4. Implement round schedule and exact historical 2018–2026 fight IDs;
   ensure 2015+ governed training, 2026-08-15 historical outcome seal and
   zero same-date or target-history leakage.
5. Produce saved fighter state/hazard predictions, baseline-equal-population
   comparisons, annual scores, calibration, uncertainty, ablations, tests,
   complete manifest and completion marker only after independent regeneration.

## Frozen references (not rerun)

PR #125: Arm A conditional LL 0.615366 / Brier 0.213614;
Arm C conditional LL 0.607777 / Brier 0.210100;
Arm C composed 3-way LL 0.971987 / summed Brier 0.584547.
Arm C B3: 224 finishes, actual SUB 54.02% vs mean predicted 44.01%.
Arm C B5: 355 finishes, actual SUB 54.93% vs predicted 48.06%.
These are **historical references, not simulator scores**.

## Source references

- PR #161 protocol and simulator recommendation under
  `docs/data_audits/grappling_identity_separation_v1/`.
- PR #160 source lineage under
  `docs/data_audits/grappling_identity_competing_pathways_v1/`.
- PR #125 `run_v1/FINAL_REPORT.md`.

No success classification A/B/C/D/E can legitimately be assigned yet.
No machine-readable prediction record, POC evidence digest, or completion marker exists.
