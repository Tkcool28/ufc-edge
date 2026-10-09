# Failure interpretation and measurement support

The frozen primary POC fails the Arm C comparison: conditional LL difference +0.020172 (paired event95 +0.009393 to +0.031100). Identity beats population-ground behavior by -0.021370 (event95 -0.029958 to -0.013036), establishing a useful signal within this specific model, not usefulness beyond Arm C. Classification B is deliberately limited: representation contains signal but the fixed measurement-to-hazard approximations do not deliver the required improvement. No automatic promotion.

Return-rate sensitivity was preregistered: halving return hazard produces LL0.612866; doubling gives0.670128. Neither beats Arm C0.607777. This localizes sensitivity to assumed episode length, but cannot prove that return rates alone cause the failure. The slower-return variant is not selected or substituted for the primary. SUB conversion pooling-only LL0.628936 versus personalized0.627949 shows a small conversion contribution in this run. It does not establish reliable individual conversion skill.

B3: SUB34.86% vs observed54.02%; B5:39.58% vs54.93%. Both losses worsen versus C. A2 improves, A1/A4 worsen: this is not merely uniform suppression of KO. Broad SUB underprediction and return sensitivity point toward the ground opportunity/hazard mapping as a diagnostic target; they do not identify exact missing positional effects.

At outer fighter states, median coherent prior SUB-attempt denominator is 1.0; median effective fighter support is 0.020 with a fixed50-attempt pseudo-prior. Debut states receive population priors. Missing and zero-exposure support remain visible in fighter_abilities.csv.gz. Ground KO fraction is latent, control is decision-selected generic CTRL, and only TD entry is represented.

Next authorized recommendation: UFC_EDGE_GROUND_PATHWAY_POC_MEASUREMENT_AND_HAZARD_AUDIT_V1, diagnostic only; inspect attempt inconsistencies, decision-control selection, omitted non-TD entry and latent ground-KO allocation before a new frozen experiment. No new training or constants chosen here.
