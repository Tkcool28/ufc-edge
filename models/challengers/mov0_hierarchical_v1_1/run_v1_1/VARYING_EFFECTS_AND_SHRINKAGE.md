# Varying effects and partial pooling

Effects are conditional log-odds coefficients per training-standardized unit, not causal effects or hazards. Tables show the final 2026 prior-history fit only; machine evidence provides all folds and groups. Group-effect intervals incorporate global/deviation posterior covariance. Approximate pooling weights use frozen evaluator information and tau draws; larger means stronger pull to global. They are information diagnostics, not an independently fitted unpooled comparison or an exact shrinkage fraction.

| Group | Column | Train N | Global mean | Deviation mean [95%] | Resulting effect mean [95%] | Approximate pooling weight |
|---|---|---|---|---|---|---|
| Bantamweight | intercept | 567 | -0.0239 | 0.0042 [-0.1206, 0.1336] | -0.0196 [-0.1502, 0.0987] | 0.6351 |
| Catch Weight | intercept | 64 | -0.0239 | 0.0111 [-0.1548, 0.2144] | -0.0127 [-0.1981, 0.1829] | 0.9018 |
| Featherweight | intercept | 609 | -0.0239 | -0.0105 [-0.1400, 0.1051] | -0.0344 [-0.1697, 0.0720] | 0.6227 |
| Flyweight | intercept | 316 | -0.0239 | -0.0331 [-0.2177, 0.0890] | -0.0570 [-0.2528, 0.0685] | 0.7232 |
| Heavyweight | intercept | 393 | -0.0239 | 0.0206 [-0.1073, 0.2168] | -0.0033 [-0.1399, 0.1740] | 0.7002 |
| Light Heavyweight | intercept | 395 | -0.0239 | 0.0492 [-0.0639, 0.2623] | 0.0253 [-0.1001, 0.2216] | 0.6976 |
| Lightweight | intercept | 784 | -0.0239 | 0.0267 [-0.0715, 0.1707] | 0.0028 [-0.0987, 0.1206] | 0.5827 |
| Middleweight | intercept | 596 | -0.0239 | 0.0491 [-0.0513, 0.2321] | 0.0252 [-0.0861, 0.1772] | 0.6295 |
| Welterweight | intercept | 761 | -0.0239 | 0.0259 [-0.0765, 0.1669] | 0.0020 [-0.1024, 0.1245] | 0.5868 |
| Women's Bantamweight | intercept | 203 | -0.0239 | -0.0428 [-0.2611, 0.0848] | -0.0667 [-0.3114, 0.0723] | 0.7923 |
| Women's Featherweight | intercept | 30 | -0.0239 | -0.0209 [-0.2424, 0.1399] | -0.0448 [-0.2951, 0.1218] | 0.9478 |
| Women's Flyweight | intercept | 266 | -0.0239 | -0.0164 [-0.1951, 0.1216] | -0.0403 [-0.2346, 0.0957] | 0.7573 |
| Women's Strawweight | intercept | 342 | -0.0239 | -0.0692 [-0.3130, 0.0444] | -0.0931 [-0.3590, 0.0451] | 0.7244 |
| Bantamweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 567 | 0.0531 | -0.0193 [-0.1323, 0.0554] | 0.0338 [-0.1361, 0.1957] | 0.8357 |
| Catch Weight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 64 | 0.0531 | 0.0045 [-0.0855, 0.1061] | 0.0576 [-0.1108, 0.2354] | 0.9753 |
| Featherweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 609 | 0.0531 | 0.0084 [-0.0694, 0.1027] | 0.0615 [-0.1004, 0.2290] | 0.8577 |
| Flyweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 316 | 0.0531 | 0.0037 [-0.0839, 0.1043] | 0.0568 [-0.1138, 0.2384] | 0.9159 |
| Heavyweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 393 | 0.0531 | 0.0065 [-0.0743, 0.0993] | 0.0596 [-0.1052, 0.2285] | 0.8158 |
| Light Heavyweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 395 | 0.0531 | -0.0020 [-0.0916, 0.0834] | 0.0512 [-0.1116, 0.2216] | 0.8284 |
| Lightweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 784 | 0.0531 | -0.0074 [-0.1015, 0.0720] | 0.0457 [-0.1138, 0.2079] | 0.8240 |
| Middleweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 596 | 0.0531 | -0.0013 [-0.0910, 0.0836] | 0.0518 [-0.1105, 0.2180] | 0.8164 |
| Welterweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 761 | 0.0531 | -0.0197 [-0.1248, 0.0485] | 0.0334 [-0.1271, 0.1902] | 0.7492 |
| Women's Bantamweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 203 | 0.0531 | 0.0106 [-0.0746, 0.1195] | 0.0637 [-0.1034, 0.2454] | 0.9327 |
| Women's Featherweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 30 | 0.0531 | -0.0049 [-0.1101, 0.0878] | 0.0482 [-0.1287, 0.2227] | 0.9935 |
| Women's Flyweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 266 | 0.0531 | 0.0064 [-0.0794, 0.1060] | 0.0595 [-0.1083, 0.2318] | 0.9147 |
| Women's Strawweight | fs__knockdown_rate__created_per_15__career__shrunk::mean | 342 | 0.0531 | 0.0146 [-0.0674, 0.1296] | 0.0677 [-0.1021, 0.2514] | 0.8919 |
| Bantamweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 567 | 0.0965 | 0.0142 [-0.0590, 0.1174] | 0.1107 [-0.0422, 0.2759] | 0.8236 |
| Catch Weight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 64 | 0.0965 | 0.0121 [-0.0728, 0.1269] | 0.1086 [-0.0537, 0.2853] | 0.9787 |
| Featherweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 609 | 0.0965 | 0.0257 [-0.0413, 0.1393] | 0.1222 [-0.0310, 0.2926] | 0.8249 |
| Flyweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 316 | 0.0965 | 0.0117 [-0.0684, 0.1170] | 0.1082 [-0.0469, 0.2783] | 0.8965 |
| Heavyweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 393 | 0.0965 | -0.0048 [-0.0996, 0.0765] | 0.0917 [-0.0625, 0.2465] | 0.8562 |
| Light Heavyweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 395 | 0.0965 | -0.0154 [-0.1200, 0.0571] | 0.0811 [-0.0738, 0.2331] | 0.8079 |
| Lightweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 784 | 0.0965 | -0.0312 [-0.1425, 0.0318] | 0.0653 [-0.0929, 0.2141] | 0.7560 |
| Middleweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 596 | 0.0965 | -0.0244 [-0.1437, 0.0470] | 0.0721 [-0.0910, 0.2272] | 0.8457 |
| Welterweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 761 | 0.0965 | 0.0033 [-0.0788, 0.0888] | 0.0998 [-0.0483, 0.2514] | 0.7895 |
| Women's Bantamweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 203 | 0.0965 | 0.0053 [-0.0846, 0.1101] | 0.1018 [-0.0554, 0.2708] | 0.9466 |
| Women's Featherweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 30 | 0.0965 | -0.0044 [-0.1133, 0.0904] | 0.0921 [-0.0765, 0.2598] | 0.9925 |
| Women's Flyweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 266 | 0.0965 | 0.0093 [-0.0760, 0.1185] | 0.1058 [-0.0524, 0.2800] | 0.9225 |
| Women's Strawweight | fs__knockdown_rate__allowed_per_15__career__shrunk::mean | 342 | 0.0965 | 0.0018 [-0.0907, 0.0982] | 0.0983 [-0.0573, 0.2664] | 0.9073 |
| Bantamweight | directional_knockdown_matchup::mean | 567 | 0.0495 | -0.0083 [-0.0975, 0.0732] | 0.0413 [-0.0993, 0.1815] | 0.7980 |
| Catch Weight | directional_knockdown_matchup::mean | 64 | 0.0495 | -0.0010 [-0.0973, 0.0912] | 0.0485 [-0.1008, 0.2025] | 0.9816 |
| Featherweight | directional_knockdown_matchup::mean | 609 | 0.0495 | -0.0101 [-0.1081, 0.0701] | 0.0394 [-0.1009, 0.1793] | 0.8311 |
| Flyweight | directional_knockdown_matchup::mean | 316 | 0.0495 | -0.0078 [-0.1012, 0.0689] | 0.0417 [-0.0940, 0.1785] | 0.8461 |
| Heavyweight | directional_knockdown_matchup::mean | 393 | 0.0495 | -0.0080 [-0.1081, 0.0708] | 0.0416 [-0.1014, 0.1789] | 0.8505 |
| Light Heavyweight | directional_knockdown_matchup::mean | 395 | 0.0495 | -0.0008 [-0.0908, 0.0815] | 0.0487 [-0.0906, 0.1895] | 0.8179 |
| Lightweight | directional_knockdown_matchup::mean | 784 | 0.0495 | 0.0091 [-0.0665, 0.0960] | 0.0586 [-0.0748, 0.1997] | 0.7852 |
| Middleweight | directional_knockdown_matchup::mean | 596 | 0.0495 | 0.0120 [-0.0652, 0.1087] | 0.0616 [-0.0754, 0.2076] | 0.8071 |
| Welterweight | directional_knockdown_matchup::mean | 761 | 0.0495 | -0.0100 [-0.1021, 0.0631] | 0.0396 [-0.1004, 0.1761] | 0.7553 |
| Women's Bantamweight | directional_knockdown_matchup::mean | 203 | 0.0495 | 0.0152 [-0.0658, 0.1349] | 0.0647 [-0.0782, 0.2372] | 0.9680 |
| Women's Featherweight | directional_knockdown_matchup::mean | 30 | 0.0495 | 0.0027 [-0.0954, 0.1061] | 0.0523 [-0.0957, 0.2127] | 0.9948 |
| Women's Flyweight | directional_knockdown_matchup::mean | 266 | 0.0495 | 0.0013 [-0.0993, 0.1033] | 0.0509 [-0.0999, 0.2060] | 0.9746 |
| Women's Strawweight | directional_knockdown_matchup::mean | 342 | 0.0495 | 0.0059 [-0.0859, 0.1121] | 0.0555 [-0.0932, 0.2153] | 0.9594 |
| Bantamweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 567 | 0.1155 | 0.0090 [-0.0654, 0.1038] | 0.1245 [-0.0005, 0.2543] | 0.8669 |
| Catch Weight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 64 | 0.1155 | -0.0090 [-0.1155, 0.0699] | 0.1065 [-0.0407, 0.2400] | 0.9661 |
| Featherweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 609 | 0.1155 | 0.0121 [-0.0518, 0.1058] | 0.1277 [0.0114, 0.2510] | 0.7888 |
| Flyweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 316 | 0.1155 | -0.0054 [-0.0894, 0.0689] | 0.1101 [-0.0206, 0.2333] | 0.8434 |
| Heavyweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 393 | 0.1155 | -0.0199 [-0.1320, 0.0472] | 0.0957 [-0.0564, 0.2229] | 0.8869 |
| Light Heavyweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 395 | 0.1155 | 0.0071 [-0.0691, 0.1054] | 0.1226 [-0.0084, 0.2646] | 0.9047 |
| Lightweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 784 | 0.1155 | 0.0077 [-0.0607, 0.0926] | 0.1232 [-0.0001, 0.2525] | 0.8114 |
| Middleweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 596 | 0.1155 | -0.0005 [-0.0819, 0.0792] | 0.1150 [-0.0117, 0.2371] | 0.8306 |
| Welterweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 761 | 0.1155 | -0.0048 [-0.0876, 0.0686] | 0.1107 [-0.0188, 0.2394] | 0.8474 |
| Women's Bantamweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 203 | 0.1155 | -0.0003 [-0.0945, 0.0891] | 0.1152 [-0.0217, 0.2499] | 0.9503 |
| Women's Featherweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 30 | 0.1155 | 0.0048 [-0.0806, 0.1085] | 0.1204 [-0.0171, 0.2619] | 0.9943 |
| Women's Flyweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 266 | 0.1155 | 0.0058 [-0.0745, 0.1024] | 0.1213 [-0.0096, 0.2578] | 0.9377 |
| Women's Strawweight | fs__submission_attempt_rate__created_per_15__career__shrunk::mean | 342 | 0.1155 | -0.0071 [-0.0989, 0.0689] | 0.1085 [-0.0275, 0.2340] | 0.8779 |
| Bantamweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 567 | 0.1505 | 0.0188 [-0.0444, 0.1200] | 0.1693 [0.0514, 0.3072] | 0.8244 |
| Catch Weight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 64 | 0.1505 | -0.0001 [-0.0926, 0.0909] | 0.1504 [0.0214, 0.2883] | 0.9750 |
| Featherweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 609 | 0.1505 | -0.0244 [-0.1365, 0.0350] | 0.1260 [-0.0040, 0.2435] | 0.8143 |
| Flyweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 316 | 0.1505 | -0.0168 [-0.1181, 0.0469] | 0.1337 [0.0050, 0.2508] | 0.8366 |
| Heavyweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 393 | 0.1505 | -0.0074 [-0.1036, 0.0705] | 0.1431 [0.0124, 0.2707] | 0.9089 |
| Light Heavyweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 395 | 0.1505 | -0.0007 [-0.0843, 0.0800] | 0.1498 [0.0286, 0.2779] | 0.9012 |
| Lightweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 784 | 0.1505 | -0.0092 [-0.1001, 0.0575] | 0.1413 [0.0204, 0.2581] | 0.8156 |
| Middleweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 596 | 0.1505 | 0.0064 [-0.0654, 0.0913] | 0.1569 [0.0384, 0.2823] | 0.8454 |
| Welterweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 761 | 0.1505 | 0.0071 [-0.0643, 0.0969] | 0.1576 [0.0393, 0.2829] | 0.8326 |
| Women's Bantamweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 203 | 0.1505 | 0.0001 [-0.0861, 0.0882] | 0.1506 [0.0187, 0.2843] | 0.9386 |
| Women's Featherweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 30 | 0.1505 | 0.0123 [-0.0663, 0.1236] | 0.1628 [0.0326, 0.3122] | 0.9921 |
| Women's Flyweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 266 | 0.1505 | 0.0099 [-0.0656, 0.1115] | 0.1604 [0.0387, 0.2994] | 0.9194 |
| Women's Strawweight | fs__submission_attempt_rate__faced_per_15__career__shrunk::mean | 342 | 0.1505 | 0.0041 [-0.0726, 0.0912] | 0.1546 [0.0369, 0.2803] | 0.8816 |
| Bantamweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 567 | 0.0233 | -0.0737 [-0.2513, 0.0298] | -0.0504 [-0.2244, 0.0829] | 0.6026 |
| Catch Weight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 64 | 0.0233 | -0.0154 [-0.1940, 0.1384] | 0.0078 [-0.1845, 0.1812] | 0.8844 |
| Featherweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 609 | 0.0233 | -0.0220 [-0.1522, 0.0822] | 0.0013 [-0.1313, 0.1184] | 0.5856 |
| Flyweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 316 | 0.0233 | -0.0146 [-0.1553, 0.1071] | 0.0087 [-0.1339, 0.1418] | 0.6823 |
| Heavyweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 393 | 0.0233 | 0.0133 [-0.1124, 0.1548] | 0.0366 [-0.0992, 0.1869] | 0.6772 |
| Light Heavyweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 395 | 0.0233 | 0.0071 [-0.1221, 0.1416] | 0.0304 [-0.1092, 0.1818] | 0.6984 |
| Lightweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 784 | 0.0233 | 0.0475 [-0.0478, 0.1833] | 0.0708 [-0.0460, 0.2074] | 0.5253 |
| Middleweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 596 | 0.0233 | 0.0413 [-0.0631, 0.1888] | 0.0646 [-0.0589, 0.2195] | 0.6098 |
| Welterweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 761 | 0.0233 | -0.0362 [-0.1813, 0.0663] | -0.0129 [-0.1597, 0.1032] | 0.5833 |
| Women's Bantamweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 203 | 0.0233 | 0.0266 [-0.1142, 0.2256] | 0.0499 [-0.1072, 0.2625] | 0.8514 |
| Women's Featherweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 30 | 0.0233 | 0.0078 [-0.1684, 0.2047] | 0.0311 [-0.1612, 0.2477] | 0.9776 |
| Women's Flyweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 266 | 0.0233 | 0.0350 [-0.0984, 0.2351] | 0.0583 [-0.0931, 0.2644] | 0.8284 |
| Women's Strawweight | fs__takedown_pressure__created_per_15__career__shrunk::mean | 342 | 0.0233 | -0.0111 [-0.1644, 0.1258] | 0.0122 [-0.1494, 0.1620] | 0.7621 |
| Bantamweight | fs__prior_fight_count__career__raw::mean | 567 | -0.1357 | -0.0091 [-0.1573, 0.1285] | -0.1448 [-0.3052, 0.0010] | 0.6297 |
| Catch Weight | fs__prior_fight_count__career__raw::mean | 64 | -0.1357 | -0.0265 [-0.2417, 0.1378] | -0.1623 [-0.4002, 0.0217] | 0.8755 |
| Featherweight | fs__prior_fight_count__career__raw::mean | 609 | -0.1357 | -0.0024 [-0.1310, 0.1243] | -0.1381 [-0.2772, -0.0017] | 0.5625 |
| Flyweight | fs__prior_fight_count__career__raw::mean | 316 | -0.1357 | 0.0317 [-0.1153, 0.2268] | -0.1041 [-0.2791, 0.0976] | 0.7616 |
| Heavyweight | fs__prior_fight_count__career__raw::mean | 393 | -0.1357 | -0.0176 [-0.1689, 0.1139] | -0.1533 [-0.3191, -0.0091] | 0.6182 |
| Light Heavyweight | fs__prior_fight_count__career__raw::mean | 395 | -0.1357 | -0.0394 [-0.2043, 0.0873] | -0.1752 [-0.3514, -0.0296] | 0.6565 |
| Lightweight | fs__prior_fight_count__career__raw::mean | 784 | -0.1357 | 0.0484 [-0.0560, 0.1853] | -0.0873 [-0.2004, 0.0387] | 0.4363 |
| Middleweight | fs__prior_fight_count__career__raw::mean | 596 | -0.1357 | -0.0887 [-0.2732, 0.0307] | -0.2244 [-0.4147, -0.0693] | 0.5723 |
| Welterweight | fs__prior_fight_count__career__raw::mean | 761 | -0.1357 | 0.0602 [-0.0407, 0.2016] | -0.0756 [-0.1947, 0.0544] | 0.4381 |
| Women's Bantamweight | fs__prior_fight_count__career__raw::mean | 203 | -0.1357 | 0.0195 [-0.1450, 0.2209] | -0.1163 [-0.3083, 0.0947] | 0.8387 |
| Women's Featherweight | fs__prior_fight_count__career__raw::mean | 30 | -0.1357 | 0.0004 [-0.2017, 0.2057] | -0.1354 [-0.3660, 0.0886] | 0.9627 |
| Women's Flyweight | fs__prior_fight_count__career__raw::mean | 266 | -0.1357 | -0.0260 [-0.2138, 0.1274] | -0.1618 [-0.3704, 0.0095] | 0.7945 |
| Women's Strawweight | fs__prior_fight_count__career__raw::mean | 342 | -0.1357 | 0.0437 [-0.0961, 0.2325] | -0.0920 [-0.2554, 0.1037] | 0.7289 |

No H2 group slope deviation has a 95% interval excluding zero in any chronological fold. No stable class-specific varying slope is established. The only recorded credible intercept deviation occurs for Women's Strawweight in 2018, without persistence. Signed means alone are insufficient evidence.

Heavyweight knockdown creation deviation +.0065 [-.0743,.0993], allowed -.0048 [-.0996,.0765], directional matchup -.0080 [-.1081,.0708] do not establish a meaningfully different knockdown relationship. Flyweight knockdown slopes receive strong pooling (approximately .85–.92), but predictive quality still worsens. LHW final baseline deviation +.0492 [-.0639,.2623] is also uncertain; neither a distinct intercept explanation nor fighter-state slopes are established. Survival global mean is negative (-.1357); Heavyweight and LHW resulting effects are negative with final intervals excluding zero, but their class deviations include zero. This supports a conditional global survival association more than a credible change by class. Correlated regressors and overlapping cumulative training folds preclude treating repeated signs as independent replications.

The real-data sanity check compares Lightweight (training N784) with Women's Featherweight (N30). For directional KD, global .0495; Lightweight deviation .0091, resulting .0586, pooling .7852, group-effect SD .0694; small-class deviation .0027, resulting .0523, pooling .9948, SD .0775. Both receive distinct estimates, while the less informative group is more pooled and more uncertain. This pattern holds for every slope in shrinkage_sanity.json. Training information, predictor variance, finishes, tau and all uncertainty intervals are preserved there; N alone does not determine pooling.
