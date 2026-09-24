# MOV0 CONDITIONAL FEATURE INTERACTION + FIGHT ARCHETYPE DIAGNOSTIC V1

Status: **MOV0_CONDITIONAL_FEATURE_INTERACTION_ARCHETYPE_DIAGNOSTIC_V1_COMPLETE**

## Scope and immutability

This is a descriptive join over checked frozen OOF files. It does not import, fit, select, calibrate, or predict with MOV0. The F02 table supplies only pre-fight state labels; thresholds are predictor-only pooled 2015+ percentiles, set before OOF outcomes are joined.

## Sources

- frozen_MOV0_source_HEAD: `dd4e7de7de4baa24090388fcf845c996564f2bf8`
- workflow_run: `35376956316`
- artifact_id: `10561085362`
- artifact_name: `mov0-standard-finish-probability-v1`
- MOV0_MIN_OOF_SHA256: `786bee7cce8a41eed6a8e7f82fe031a592ed081a10b3a97f85afc31be61d1c57`
- MOV0_FULL_OOF_SHA256: `9d543356b157fefaabe27f7f4d1b5663536e4cf659fdf11fedd8531c4b13faa0`
- corrected_F02_SHA256: `d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580`
- terrain_SHA256: `d3358cfc468a791861ee6fb87473f119f949d705c54abfcb504d9ebbecdcb5d2`
- proof_predictions_not_regenerated: `program imports no MOV0 training/prediction code; only reads and SHA-verifies frozen OOF CSVs`

## Fixed state thresholds

LOW is <= p33; HIGH is >= p67; MID is between. Thresholds are written in `feature_state_thresholds.json`.

## Model says X / reality says Y

| Fight archetype | N | Mean MIN p(finish) | Mean FULL p(finish) | Actual finish rate | Interpretation |
|---|---:|---:|---:|---:|---|
| A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE | 763 | 55.7% | 59.1% | 59.9% | FULL aligned within 5pp; NORMAL |
| A2_BOTH_HIGH_DAMAGE_EXCHANGE | 143 | 55.0% | 57.4% | 55.2% | FULL aligned within 5pp; NORMAL |
| A3_ACCURACY_VS_ABSORPTION | 973 | 47.9% | 50.6% | 48.0% | FULL aligned within 5pp; NORMAL |
| A4_KO_HISTORY_VS_KO_VULNERABILITY | 789 | 57.7% | 59.8% | 61.3% | FULL aligned within 5pp; NORMAL |
| B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE | 662 | 48.4% | 50.7% | 53.2% | FULL aligned within 5pp; NORMAL |
| B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE | 698 | 47.3% | 49.1% | 48.9% | FULL aligned within 5pp; NORMAL |
| B3_TD_ACCESS_PLUS_SUB_PRESSURE | 412 | 51.3% | 53.6% | 54.4% | FULL aligned within 5pp; NORMAL |
| B4_SUB_PRESSURE_POOR_TD_ACCESS | 1628 | 49.9% | 51.9% | 52.9% | FULL aligned within 5pp; NORMAL |
| B5_SUB_PRESSURE_VS_SUB_VULNERABILITY | 591 | 53.5% | 55.6% | 60.1% | FULL aligned within 5pp; NORMAL |
| C2_BOTH_HIGH_FINISH_HISTORY | 1483 | 54.0% | 55.9% | 55.7% | FULL aligned within 5pp; NORMAL |
| C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS | 417 | 59.4% | 61.6% | 55.6% | FULL overpredicts; NORMAL |
| D1_LOW_DAMAGE_STRONG_DEFENSE | 74 | 31.2% | 29.4% | 27.0% | FULL aligned within 5pp; MODERATE_UNCERTAINTY |
| D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE | 499 | 43.0% | 44.8% | 44.5% | FULL aligned within 5pp; NORMAL |
| D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE | 124 | 43.0% | 42.5% | 31.5% | FULL overpredicts; NORMAL |

## All preregistered archetypes

### A1_KD_CREATION_VS_WEAK_STRIKE_DEFENSE

A side has HIGH KD creation and opponent LOW strike defense.

N=763 (NORMAL).
Observed 59.9% (Wilson 95% 56.4%–63.3%); MIN 55.7% (gap +4.2%); FULL 59.1% (gap +0.8%). FULL−MIN mean +3.4%, median +3.5%, up/down 81.3%/18.7%.

### A2_BOTH_HIGH_DAMAGE_EXCHANGE

Both fighters have HIGH KD creation and HIGH significant-strike flow.

N=143 (NORMAL).
Observed 55.2% (Wilson 95% 47.1%–63.2%); MIN 55.0% (gap +0.3%); FULL 57.4% (gap -2.1%). FULL−MIN mean +2.4%, median +2.3%, up/down 67.8%/32.2%.

### A3_ACCURACY_VS_ABSORPTION

A side has HIGH striking accuracy and opponent HIGH significant-strike absorption.

N=973 (NORMAL).
Observed 48.0% (Wilson 95% 44.9%–51.1%); MIN 47.9% (gap +0.1%); FULL 50.6% (gap -2.6%). FULL−MIN mean +2.6%, median +2.7%, up/down 75.1%/24.9%.

### A4_KO_HISTORY_VS_KO_VULNERABILITY

A side has HIGH KO/TKO win history and opponent HIGH KO/TKO loss history.

N=789 (NORMAL).
Observed 61.3% (Wilson 95% 57.9%–64.7%); MIN 57.7% (gap +3.6%); FULL 59.8% (gap +1.5%). FULL−MIN mean +2.1%, median +2.3%, up/down 70.6%/29.4%.

### B1_TD_PRESSURE_VS_WEAK_TD_DEFENSE

A side has HIGH takedown pressure and opponent LOW takedown defense.

N=662 (NORMAL).
Observed 53.2% (Wilson 95% 49.4%–56.9%); MIN 48.4% (gap +4.8%); FULL 50.7% (gap +2.4%). FULL−MIN mean +2.4%, median +2.5%, up/down 72.1%/27.9%.

### B2_TD_CONVERSION_VS_WEAK_TD_DEFENSE

A side has HIGH takedown conversion and opponent LOW takedown defense.

N=698 (NORMAL).
Observed 48.9% (Wilson 95% 45.2%–52.6%); MIN 47.3% (gap +1.5%); FULL 49.1% (gap -0.3%). FULL−MIN mean +1.8%, median +2.1%, up/down 67.8%/32.2%.

### B3_TD_ACCESS_PLUS_SUB_PRESSURE

A side has HIGH takedown pressure, HIGH takedown conversion, and HIGH submission pressure.

N=412 (NORMAL).
Observed 54.4% (Wilson 95% 49.5%–59.1%); MIN 51.3% (gap +3.0%); FULL 53.6% (gap +0.8%). FULL−MIN mean +2.2%, median +2.4%, up/down 74.8%/25.2%.

### B4_SUB_PRESSURE_POOR_TD_ACCESS

A side has HIGH submission pressure but not HIGH takedown access (pressure and conversion are not both HIGH).

N=1628 (NORMAL).
Observed 52.9% (Wilson 95% 50.5%–55.3%); MIN 49.9% (gap +3.0%); FULL 51.9% (gap +1.0%). FULL−MIN mean +1.9%, median +2.0%, up/down 70.1%/29.9%.

### B5_SUB_PRESSURE_VS_SUB_VULNERABILITY

A side has HIGH submission pressure and opponent HIGH submission attempts faced.

N=591 (NORMAL).
Observed 60.1% (Wilson 95% 56.1%–63.9%); MIN 53.5% (gap +6.6%); FULL 55.6% (gap +4.5%). FULL−MIN mean +2.1%, median +2.1%, up/down 71.4%/28.6%.

### C1_DAMAGE_PLUS_SUBMISSION_ACCESS

A side has HIGH damaging-exchange creation and HIGH takedown access plus HIGH submission pressure.

N=29 (THIN_EXPLORATORY).
Observed 65.5% (Wilson 95% 47.3%–80.1%); MIN 61.8% (gap +3.7%); FULL 64.2% (gap +1.4%). FULL−MIN mean +2.4%, median +2.5%, up/down 79.3%/20.7%.

### C2_BOTH_HIGH_FINISH_HISTORY

Both fighters have HIGH finish history: HIGH KO/TKO or submission win history or HIGH early-finish history.

N=1483 (NORMAL).
Observed 55.7% (Wilson 95% 53.2%–58.2%); MIN 54.0% (gap +1.7%); FULL 55.9% (gap -0.2%). FULL−MIN mean +2.0%, median +2.1%, up/down 70.2%/29.8%.

### C3_HIGH_FINISH_PRESSURE_FIVE_ROUNDS

At least one side has HIGH finish history and the bout is scheduled for five rounds.

N=417 (NORMAL).
Observed 55.6% (Wilson 95% 50.8%–60.3%); MIN 59.4% (gap -3.7%); FULL 61.6% (gap -6.0%). FULL−MIN mean +2.2%, median +2.2%, up/down 74.8%/25.2%.

### D1_LOW_DAMAGE_STRONG_DEFENSE

Both fighters are LOW KD creation and HIGH striking defense.

N=74 (MODERATE_UNCERTAINTY).
Observed 27.0% (Wilson 95% 18.2%–38.1%); MIN 31.2% (gap -4.2%); FULL 29.4% (gap -2.4%). FULL−MIN mean -1.8%, median -0.9%, up/down 33.8%/66.2%.

### D2_LOW_TD_ACCESS_LOW_SUB_PRESSURE

Both fighters lack HIGH takedown access and are LOW submission pressure.

N=499 (NORMAL).
Observed 44.5% (Wilson 95% 40.2%–48.9%); MIN 43.0% (gap +1.5%); FULL 44.8% (gap -0.4%). FULL−MIN mean +1.9%, median +1.9%, up/down 69.5%/30.5%.

### D3_EXPERIENCE_STRONG_DEFENSIVE_PROFILE

Both fighters are HIGH prior-fight experience and HIGH striking defense.

N=124 (NORMAL).
Observed 31.5% (Wilson 95% 23.9%–40.1%); MIN 43.0% (gap -11.5%); FULL 42.5% (gap -11.1%). FULL−MIN mean -0.5%, median -0.3%, up/down 43.5%/56.5%.

## Broad bucket → archetype composition

The JSON mapping reports overlapping family coverage for each immutable FULL probability bucket; a fight may match more than one pathway family.

- <0.30: N=355; striking 29.0%, grappling 49.3%, mixed 10.4%, survival 35.5%.
- 0.30–<0.40: N=766; striking 28.5%, grappling 49.7%, mixed 24.2%, survival 20.0%.
- 0.40–<0.50: N=1210; striking 31.1%, grappling 48.1%, mixed 27.3%, survival 13.4%.
- 0.50–<0.60: N=975; striking 44.4%, grappling 57.8%, mixed 43.8%, survival 11.2%.
- 0.60–<0.70: N=640; striking 60.0%, grappling 62.7%, mixed 57.8%, survival 10.5%.
- >=0.70: N=314; striking 75.5%, grappling 71.3%, mixed 78.0%, survival 8.3%.

## PATHWAYS_TO_FINISH_FOR_FUTURE_SIMULATOR

Striking: the diagnostic tests pre-fight offensive damage access against defensive vulnerability, not causal event transitions. Grappling: it keeps takedown access, opponent resistance, and submission pressure separate; any future round model should preserve that ordering. Exposure: five-round scheduling supplies additional opportunity but is not a causal hazard estimate. These archetypes are a stable comparison panel for MOV1, hierarchical challengers, and a future coarse simulator—not model features or optimized rules.

## Limitations

Overlapping, non-causal descriptive archetypes; percentile state loss of information; historical F02 coverage/missingness; small weight-class cross-cells; OOF years 2018–2026 only. No odds, ROI, EV, threshold optimization, new model feature, or prediction regeneration is present.

**MOV0_CONDITIONAL_FEATURE_INTERACTION_ARCHETYPE_DIAGNOSTIC_V1_COMPLETE**
