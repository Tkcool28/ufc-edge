#!/usr/bin/env python3
"""Render research reports and seal source/output hashes; performs zero predictive fits."""
from __future__ import annotations
import argparse,hashlib,json,sys,lzma
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[2]
DEFAULT=R/'docs/data_audits/ground_opportunity_competing_pathways_v1'
BASE='3e2b14a8391ed17d072b4bbb9570b31bc6d12b85'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(d):
 def fmt(x):
  if pd.isna(x):return 'unavailable'
  if isinstance(x,float):return f'{x:.2f}'
  return str(x).replace('|','\\|').replace('\n',' ')
 return '\n'.join(['| '+' | '.join(map(str,d.columns))+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(fmt(x) for x in row)+' |' for row in d.itertuples(index=False,name=None)])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=DEFAULT);out=ap.parse_args().output_dir
 (out/'RESEARCH_REFERENCE_ORIGINS.json').write_text(json.dumps([{'reference': 'UFC_FIGHT_SIMULATOR_DATA_FEASIBILITY_RESEARCH_V1.md', 'original_uploaded_SHA256': '8ca3a7f9e3dae7adee2bc17eb7a8e3150f58438df426e6095e62a7bcd74c5e4f', 'repository_reference_SHA256': '56ed971ae861d7530ae08cf0cbc1d17d2106a177ad2e0064d085b48c2d9d0339', 'normalization': 'remove Markdown trailing line whitespace; content preserved'}, {'reference': 'UFC_EDGE_SUBMISSION_MECHANISM_AND_GRAPPLING_DATA_RESEARCH_V1.md', 'original_uploaded_SHA256': 'e6cda2d1f165fab4fc1523cb56c5e9540896c2addc3d55f7581504861de0d39c', 'repository_reference_SHA256': 'e6cda2d1f165fab4fc1523cb56c5e9540896c2addc3d55f7581504861de0d39c', 'normalization': 'remove Markdown trailing line whitespace; content preserved'}],indent=2,sort_keys=True)+'\n')
 (out/'requirements.txt').write_text('numpy==2.3.5\npandas==2.2.3\nscipy==1.17.0\n')
 def csv(n):return pd.read_csv(out/n)
 def obj(n):return json.loads((out/n).read_text())
 def md(n,s):(out/n).write_text(s.strip()+'\n')
 boundary=csv('boundary_coverage.csv');fold=csv('fold_state_coverage.csv');year=csv('year_field_coverage.csv');bins=csv('conversion_support_bins.csv');cell=csv('B3_B5_candidate_coverage.csv');dist=csv('B3_B5_measurement_distributions.csv');corr=csv('B3_B5_descriptive_correlations.csv');checks=obj('CONVERSION_MEASUREMENT_CHECK.json');quality=obj('POSITION_INTERVAL_QUALITY.json')
 states=csv('strict_prior_fighter_states.csv.gz');bouts=csv('bout_measurements.csv.gz'); panels=csv('B3_B5_strict_prior_states.csv.gz')
 # Full positional-year coverage, including all additive position families.
 meta=bouts[['fight_id','event_date','expected_rounds']].drop_duplicates('fight_id')
 po=pd.read_csv(R/'data/canonical/v0/fighter_round_position.csv')
 po=po[po.fight_id.isin(meta.fight_id)].merge(meta,on='fight_id',how='left',validate='many_to_one')
 positional=[]
 for y,mg in meta.groupby(meta.event_date.str[:4]):
  g=po[po.event_date.str[:4].eq(y)];expected=int(2*mg.expected_rounds.sum())
  for field in [c for c in po.columns if c.endswith('_bucket_min')]+['standups']:
   v=g[field];positional.append({'year':int(y),'field':field,'expected_fighter_rounds':expected,'observed_rows':int(v.notna().sum()),'missing_pct':100*(1-v.notna().sum()/expected) if expected else None,'zero_rows':int(v.eq(0).sum()),'sum_in_source_units':v.sum()})
 pd.DataFrame(positional).to_csv(out/'year_position_coverage.csv',index=False,float_format='%.10g',lineterminator='\n')
 # Per-field support includes standups/control allowed/positions, beyond ratio candidates.
 fields=['takedowns_attempted','takedowns_landed','submission_attempts','submission_attempts_faced','sig_ground_attempted','sig_ground_landed','control_sec','control_sec_allowed','reversals','reversals_faced','elapsed_min','ground_bucket_min','ground_control_bucket_min','back_control_bucket_min','standups','sub_win','sub_loss']
 foldids=json.loads(lzma.decompress((R/'models/challengers/mov1_three_arm_directional_v1/ordered_fold_fight_ids.json.xz').read_bytes()))['folds']
 fieldrows=[]
 def field_summary(z,scope,y,w,division):
  for field in fields:
   v=z[field].dropna()
   fieldrows.append({'scope':scope,'outer_year':y,'window':w,'division':division,'field':field,'fighter_states':len(z),'unique_fighters':z.fighter_id.nunique(),'observed_states':len(v),'missing_pct':100*(1-len(v)/len(z)) if len(z) else None,'zero_observed_pct':100*v.eq(0).mean() if len(v) else None,'observed_sum_state_weighted':v.sum(),'complete_history_pct':100*((z[field+'_complete_bouts']==z.prior_ufc_bouts)&z.prior_ufc_bouts.gt(0)).mean(),'p10':v.quantile(.1),'p25':v.quantile(.25),'p50':v.quantile(.5),'p75':v.quantile(.75),'p90':v.quantile(.9)})
 for fl in foldids:
  y=fl['outer_year'];cut=f'{y}-01-01';train=set(fl['training'])
  people=set(bouts[bouts.fight_id.isin(train)].fighter_id)
  prior=bouts[(bouts.event_date<cut)&bouts.fighter_id.isin(people)]
  grouped=prior.groupby('fighter_id');z=grouped[fields].sum(min_count=1).reindex(sorted(people));z['prior_ufc_bouts']=grouped.size().reindex(z.index,fill_value=0)
  for field in fields:z[field+'_complete_bouts']=grouped[field].count().reindex(z.index,fill_value=0)
  z=z.reset_index();field_summary(z,'training_fighters_at_boundary',y,'career','ALL')
  for scope,ids in [('frozen_training_prefight',train),('frozen_outer_scoring_prefight',set(fl['scoring']))]:
   for w in ['career','last5']:
    z=states[states.target_fight_id.isin(ids)&states.window.eq(w)]
    for division,g in [('ALL',z)]+list(z.groupby('division')):field_summary(g,scope,y,w,division)
 pd.DataFrame(fieldrows).to_csv(out/'fold_field_support.csv',index=False,float_format='%.10g',lineterminator='\n')
 exact=[{'outer_year':fl['outer_year'],'measurement':candidate,'eligible_exact_ground_exposure_states':0,'missing_exact_ground_exposure_pct':100,'reason':'no validated exact ground-duration field; coarse partial buckets withheld as exact exposure'} for fl in foldids for candidate in ['SUB attempts per grounded minute','ground significant strikes per grounded minute','opponent escape opportunity rate']]
 pd.DataFrame(exact).to_csv(out/'exact_ground_denominator_feasibility.csv',index=False,lineterminator='\n')
 # Count and field windows are reported directly from governed catalog; no guessed variants.
 catalog=json.loads((R/'features/feature_catalog.yaml').read_text())
 names=['takedown_pressure','takedown_conversion','submission_attempt_rate','control_rate','reversal_rate','sig_environment_mix','finish_method_win_profile','finish_method_loss_profile']
 windows=[]
 for x in catalog['features']:
  if x['feature_name'] in names:
   windows.append({'concept':x['feature_name'],'windows':', '.join(k for flag,k in [('career_variant','career'),('recent_3_variant','last3'),('recent_5_variant','last5'),('ewma_variant','EWMA365d')] if x[flag]),'shrinkage':x['shrinkage_rule'],'minimum_support':x['minimum_sample']})
 pd.DataFrame(windows).to_csv(out/'existing_F01_windows.csv',index=False,lineterminator='\n')
 common='''All audit histories use event_date < target event date; the target and every same-date bout are excluded. Only pinned UFC history through 2026-08-15 is used. No prospective confirmation outcomes, model fitting, feature promotion or frozen-source edits occur. This is retrospective event-date governance: 2026 acquisition snapshots cannot prove what a provider published before every old fight. Preserve that publication-vintage limitation.

The modern population is the unchanged 5,658-fight PR #125 universe; its 4,260 outer-scored bouts and exact conditional training/scoring fight IDs are reused. Historical measurements retain earlier UFC bouts where available. Boundary rows describe unique fighters appearing in the frozen conditional training set at January 1. Training-prefight rows describe their original historical prediction dates, not values accumulated at the later boundary. Scoring rows include all eligible bouts, with 2026 truncated at the existing August 15 boundary. Division rows follow frozen target division, without inferring sex from unsupported metadata.

`career` here means available prior UFC history for the candidate measurement audit. `last5` means the last five prior UFC bouts, including measurement-missing bouts; tied dates crossing the boundary fail closed. This deliberately conservative coverage window is not an exact replay of F01's component-specific last5 eligible-observation selector. F01's available windows are inventoried separately and remain unchanged. Prior non-UFC outcome history cannot supply a UFC round-stat denominator. No prior UFC history is reported separately; it does not prove a professional debut. F01 likewise withholds automatic debut-prior substitution when debut/completeness is unproven.

A full-bout count requires all rounds 1..finish_round and nonmissing field values. Pair candidates sum only rounds with both measurements; conversion requires a complete attempted-submission bout before attaching the result. Ground-bucket pairs additionally require governed elapsed duration and a lower bound within that duration. Partial paired histories remain explicitly partial. `complete_history_pct` requires every prior UFC bout to have the relevant complete pair; observed-pair availability alone is insufficient. Zero denominator is distinct from missing history, and zero minute bucket means less than one minute under the contract, not necessarily no exposure. The contract's interval model is empirical evidence, not an independently published vendor unit guarantee.

Counts summed across target fighter states repeat a fighter's prior events at different prediction dates: columns explicitly say state-weighted. They are support distributions, not independent trial totals or confidence intervals. Bout-level records supply unique event counts; no statistical uncertainty calculation treats repeated fighter states as independent. Quantiles and missingness are descriptive; no style thresholds are chosen from outcomes.'''
 md('GROUND_OPPORTUNITY_SOURCE_LINEAGE.md',f'''# Ground opportunity source lineage

Starting main: `{BASE}`. Main matched the supplied PR #125 merge; no intervening commits. Audit only. The supplied submission-mechanism research and simulator feasibility research are preserved as reference text in `research_context/` (Markdown trailing spaces normalized; original upload hashes retained in `RESEARCH_REFERENCE_ORIGINS.json`) as scientific starting references, not evidence that a candidate field is already operational.

## Actual inventory and disposition

| Surface | Exact path | Status and role |
| --- | --- | --- |
| Pinned UFCStats mirror | `data/raw/greco1899/8e40eb945e11/ufc_fight_stats.csv` and `manifest.json` | Actual historical per-fighter round measurements; Greco1899/scrape_ufc_stats commit 8e40eb945e1127bf0ef172ab211a34787948f312 |
| Canonical core | `data/canonical/v0/fighter_round_stats.csv`, `fights.csv`, `events.csv` | Actual normalized measurements and dated outcomes; field owner specified in `provenance/source_precedence_v0.md` |
| Raw official FightMetric | `data/raw/ufc_fightmetric_official/20260820T123046Z/fight_stat/page_*.json` | Actual UFC.com Drupal JSON:API snapshot, 57,382 raw rows including summaries/duplicates/unidentified payloads |
| Canonical position | `data/canonical/v0/fighter_round_position.csv` | Actual additive data: 32,156 fighter-round rows / 6,803 fights / 2,459 fighters. Coarse buckets and standups, not exact position seconds |
| Identity governance | `data/canonical/v0/source_identity_links.csv`; `data/derived/identity/ufc_greco_fight_alignment_candidate.csv` | Trusted canonical/provider IDs plus audited UFC athlete UUID corner mapping |
| Prior audits | `provenance/audits/fightmetric_*`; `canonical_fightmetric_position_v0_latest.*` | Completed semantic, overlap, era, duplicate, color and quality audits; not merely proposed ingestion |
| F01 | `src/ufc_edge/features/state.py`, `history.py`, `aggregations.py`; `features/feature_catalog.yaml` | Production formulas/windows/shrinkage; exact positional duration deliberately withheld |
| F02 / corrected physical profile | `features/f02/README.md`; `models/challengers/mov1_three_arm_directional_v1/SOURCE_LINEAGE_VALIDATION.json` | F01 replay inherits chronology. Corrected physical F02 SHA256 d8a82dc7baf3d6e85c987e7fbfc63bb6329d59407cd8a66e5f228e0012e6b580, verified by prior frozen contract. This audit does not download or modify that matrix |
| PR #123 | `docs/model_diagnostics/mov1_directional_representation_v1/` | Completed representation/lineage audit; establishes lost directional alignment, not missing-ground-data causation |
| PR #124 | `models/challengers/mov1_three_arm_directional_v1/` | Frozen feature/fold/target contract and exact ordered fight IDs |
| PR #125 | `models/challengers/mov1_three_arm_directional_run_v1/run_v1/` | Frozen predictions, membership and diagnostics; evaluation archive SHA256 verified before selectively reading saved fight evidence |
| Simulator source leads | `provenance/source_inventory.md`, `features/data_requirements.json`, `schemas/fight_action_event_v0.md` | TIP/live-feed references and proposed event schema. No licensed exact-duration archive or populated atomic transition table is established by these documents |

## Measurement definitions and transformations

All core fields below share raw Greco CSV → `pipelines/build_canonical_core_v0.py` → canonical fighter-round statistics. Exact raw-to-canonical mappings are shown; annual depth/missingness/observed sums/zeros are in `year_field_coverage.csv`. First/last observed years are available there rather than assumed modern coverage.

| Measurement | Raw field → canonical field | Units and denominator | Existing F01/F02 representation |
| --- | --- | --- | --- |
| TD attempts | `TD` attempted → `takedowns_attempted` | Recorded count, activity per governed total fight minutes | takedown_pressure created/faced per15 |
| TD landed | `TD` landed → `takedowns_landed` | Recorded count; success denominator is TD attempts | takedown_conversion.success; raw landed count reconstructible, not a standalone ground-exposure feature |
| TD defense | Paired opponent `TD` counts | (opponent attempts − landed)/opponent attempts | takedown_conversion.defense; no escape interpretation |
| SUB attempts created | `SUB.ATT` → `submission_attempts` | Provider-recorded attempts; /total fight minutes | submission_attempt_rate.created_per15; threat quality and attempt phase not observed |
| SUB attempts faced | Opponent same fight/round `SUB.ATT` | Actual opponent count on matching total exposure | submission_attempt_rate.faced_per15; exposure-confounded, not pure defense |
| SUB finishes | Raw results `METHOD` plus winner → `fights.method=SUBMISSION`, winner_id/result | Complete bout outcome; F01 wins/losses /prior fight count | finish_method_win/loss_profile, not finish/attempt conversion |
| Ground significant ATT | `GROUND` attempted → `sig_ground_attempted` | Significant ground-strike count; not all ground-and-pound | sig_environment_mix.ground_share = ground/(distance+clinch+ground attempts), not per ground minute |
| Ground significant land | `GROUND` landed → `sig_ground_landed` | Recorded significant count | Raw available; no dedicated F01 ground-location landed rate |
| Elapsed exposure | results terminal round/time + dated rules registry | Seconds/minutes via `src/ufc_edge/features/elapsed_exposure.py`; never ground time | Existing governed time denominators |
| Generic control | `CTRL` M:SS → `control_sec` | Generic control seconds, includes no guaranteed top-only/ground-only definition | control_rate.created_share/allowed_share versus total elapsed exposure |
| Reversals | `REV.` → `reversals` | Recorded counts; opponent paired counts | reversal_rate created/faced per15, not escape probability |
| Ground/position duration | Official `ground_time`, `ground_ctl_time`, guard/half/side/mount/back fields → position buckets and bounds | Coarse floor-minute model; bounds b×60..b×60+59, intersect known round time; ground occupancy differs from one fighter's control | Not materialized as exact F01/F02 duration; DATA_REQUIRED |
| Standups | Official `grap_stand_land` → `fighter_round_position.standups` | Source landed-count transport; no attempted standups/escape trials or standardized opportunity denominator | Canonical only, not F01/F02 feature |
| Escapes/ground entries/transitions | No validated canonical field/table | Ground entries are not equivalent to TD completions; escape and event-sequence opportunity absent | Not available |

Official raw count equivalents include `grap_take_att/land`, `grap_sub_att`, `grap_rev_land`, `ground_sig_str_att/land`. `control_time` in that archive is coarse and never replaces precise Greco CTRL. Additional stored `ground_str_att/land`, ground head/body/leg and sparse ground weapon splits are **raw candidate fields**. Their names do not prove all-ground offense semantics or finish quality. Prior summary-additivity evidence supports `ground_str_att/land` as counts, but this audit does not promote their clinical/weapon/total-versus-significant definitions. `raw_additive_inventory.csv` reports transport coverage including raw summaries and duplicates; it is not eligible fighter-state coverage.

Core fighter mapping first uses canonical Greco fight URL and exact event/bout context, then a unique normalized fighter-name mapping with participant validation; ambiguous names are excluded. Official position mapping uses trusted FightMetric fight IDs, athlete UUIDs and audited numeric 0=red/1=blue mapping (99.566% exact in 250,782 shared count comparisons), not display-name inference. Round 0 is source summary, never another actual round. Unresolved duplicates and identity failures are quarantined. Core and position builders, their source manifests and ID crosswalks are all hash-identified.

## Existing windows, shrinkage and minimum support

{table(pd.DataFrame(windows))}

Time-rate prior strength is 15 exposure-minutes, attempt-probability strength 20 attempts, composition strength 30 attempts, fight-rate strength 6 fights. F01 population priors are built from strictly prior history (weight-class then governed fallback), not whole-sample outcomes; EWMA half-life is 365 days. No new shrinkage or conversion prior is fitted in this audit. Any future rate requires a separately frozen definition and support/uncertainty policy.

## Chronology and reconstruction

{common}

All requested count proxies, generic control allowed, reversals and coarse position/standup histories can be reconstructed into **separate diagnostic files** from immutable inputs. A new exact grounded-duration field cannot be reconstructed from these aggregates without assumptions. No canonical/F01/F02/frozen prediction artifact changes are needed or authorized.''')
 md('GROUND_EXPOSURE_COVERAGE.md',f'''# Ground exposure coverage

**No broadly usable exact historical ground-exposure denominator is present.** Existing positional records are real, but incomplete and coarse. Do not confuse an observed positive bucket sum with a complete fighter career denominator.

{common}

## Every frozen outer training boundary

SUB / completed TD fallback, paired counts:

{table(boundary[boundary.candidate=='sub_per_td'][['outer_year','eligible_training_fights','eligible_prior_ufc_fights','unique_fighters','num_observed_states','den_observed_states','zero_den_pct_observed','den_p10','den_p25','den_p50','den_p75','den_p90','complete_history_pct']])}

SUB / ground-bucket candidate (bucket units; **not SUB per grounded minute**):

{table(boundary[boundary.candidate=='sub_per_ground_bucket'][['outer_year','unique_fighters','missing_pair_pct','zero_den_pct_observed','den_p10','den_p25','den_p50','den_p75','den_p90','complete_history_pct']])}

`boundary_coverage.csv` includes all eight denominator/support candidates, numerators and denominators, missingness, zero numerators/denominators and exposure quantiles. `fold_state_coverage.csv` adds original training-date and scoring-date support, career/recent windows and every division at every boundary. This prevents later boundary history from masquerading as early training support. `fold_field_support.csv` separately reports every raw count/position/control-allowed/SUB-finish field at all boundaries, original-date scopes, divisions and windows. `exact_ground_denominator_feasibility.csv` explicitly marks the unavailable true denominators at every boundary. `year_field_coverage.csv` counts observed measurements against expected fighter-round keys, including absent stat/position rows.

## Interval-quality safeguards

{table(pd.DataFrame(quality))}

Only positional pairs with a known elapsed duration and lower bound no greater than that duration enter bucket support. These additional conflicts are diagnostic exclusions, not modifications to the canonical source. An upper bucket bound must be intersected with round duration, never used as an exact observed number. A zero bucket can hide up to 59 seconds. SUB or ground-strike counts divided by the bucket integer have zero/quantization problems; exact candidate rates remain unavailable at **every** boundary.

Overall SUB.ATT counts are not phase-coded: standing/clinch attempts may be included. Even with exact ground seconds, overall SUB attempts / ground time would require an explicit proxy interpretation; a genuine ground-only activity rate needs phase-matched SUB attempts.

CTRL/TD can be formed on matched rounds but is generic control retention proxy, can include clinch/control entered without a TD, and cannot identify time per ground entry. Standups and reversals are real counts with uncertain opportunity conditioning; neither yields an escape probability. Ground-control buckets are not substitute ground exposure, especially for bottom-position submissions.''')
 early=fold[(fold.outer_year==2018)&(fold.division=='ALL')&(fold.window=='career')]
 earlycols=['scope','candidate','fighter_states','missing_pair_pct','zero_den_pct_observed','den_p10','den_p25','den_p50','den_p75','den_p90','complete_history_pct','no_prior_ufc_states']
 md('EARLY_FOLD_SUPPORT_REPORT.md',f'''# Earliest fold support

The 2018 outer boundary has **707 frozen conditional training fights and 662 unique training fighters**. Training states are from 2015–2017; they must not borrow the extra exposure those fighters accrued before January 2018. The 2018 outer scoring universe is **470 bouts / 940 oriented fighter states**.

{table(early[earlycols])}

## What survives

Recorded submission activity, completed/attempted TDs, ground significant-strike activity, generic CTRL and reversals have enough *measurement coverage* for conservative diagnostic count comparisons. This is not proof of predictive value or individual-fighter precision. SUB/TD and CTRL/TD require positive TD denominators, paired round coverage and regularization if ever used predictively. True grounded-minute rates fail semantic/coverage requirements; source buckets are not exact minutes and complete ground history at the earliest boundary is only 22.51% of training fighters.

Conversion support must be judged at the original 2015–2017 dates too. The attempt bins in `conversion_support_bins.csv` separately report training-prefight, scoring-prefight and unique boundary-fighter support; missing observations are separate from zero. Per-division and recent-window figures are in `fold_state_coverage.csv`, not pooled away.

No prior UFC history flags in the outer set cannot establish a professional debut. Outcome-only pre-UFC records exist but cannot fill missing submission-attempt or grounded-time histories. Entirely missing history and no completed TD exposure stay unavailable rather than becoming zeros.

{common}''')
 # Descriptive rate summaries only for nonmissing positive support; retain sparse conversion as counts.
 rates=[]
 for c,g in panels.groupby('cell'):
  for w,z in g.groupby('window'):
   for name in ['sub_per_elapsed_min','ground_strikes_per_elapsed_min','sub_per_td','control_per_td']:
    valid=z[name+'_den'].gt(0)&z[name+'_num'].notna();v=z.loc[valid,name+'_diagnostic_ratio']
    rates.append({'cell':c,'window':w,'candidate':name,'positive_den_states':len(v),'zero_or_missing_den_states':len(z)-len(v),'p10':v.quantile(.1),'p25':v.quantile(.25),'p50':v.quantile(.5),'p75':v.quantile(.75),'p90':v.quantile(.9)})
 pd.DataFrame(rates).to_csv(out/'B3_B5_proxy_ratio_distributions.csv',index=False,float_format='%.10g',lineterminator='\n')
 for c in ['B3','B5']:
  frozen=obj(c+'_FROZEN_CELL.json');z=cell[(cell.scope==c)&(cell.outer_year==0)&(cell.window=='career')]
  q=dist[(dist.cell==c)&(dist.year.astype(str)=='ALL')&(dist.window=='career')]
  cc=corr[(corr.cell==c)&(corr.window=='career')]
  md(c+'_MECHANISM_HETEROGENEITY.md',f'''# {c} mechanism heterogeneity

Unchanged PR #125 cell: **{frozen['all_scored_bouts']} all-scored bouts**, **{frozen['standard_finishes']} standard finishes**. Frozen observed SUB among finishes: **{100*frozen['observed_SUB']:.2f}%**; saved Arm C conditional predicted SUB: **{100*frozen['Arm_C_predicted_SUB']:.2f}%**. All cell bouts are described, including decisions; the finish-only result is retained only as the existing diagnostic context. No membership, threshold or prediction changed.

## Strict-prior support

{table(z[['candidate','fighter_states','missing_pair_pct','zero_den_pct_observed','den_p50','complete_history_pct']])}

## Continuous count distributions, no outcome-selected style bins

{table(q[['field','states','observed_states','zero_observed_pct','p10','p25','p50','p75','p90']])}

{table(cc)}

Correlations are descriptive associations of repeated prior-history counts, affected by fighter experience and overlap; they are not independent-sample tests or evidence of causation. `B3_B5_proxy_ratio_distributions.csv` reports supported nonzero-denominator descriptive ratios alongside availability, with underlying numerator/denominator counts in `B3_B5_strict_prior_states.csv.gz`. Total fight minute is explicitly a general-time normalization, never ground opportunity. Sparse diagnostic ratios are not recommended production values; no conversion ratio performance is calculated.

## What can actually be distinguished

| Proposed style | Measurable evidence now | Unresolved distinction |
| --- | --- | --- |
| Submission-oriented grappler | Prior recorded SUB attempts alongside ground-strike activity and TD counts | Attempt quality, bottom/scramble context and actual opportunity time absent |
| Control wrestler | Generic CTRL, coarse ground-control buckets and low recorded offensive counts can describe a proxy profile | Generic control is not top retention; low observed activity may reflect missing opportunity |
| Ground-and-pound wrestler | Significant ground-strike ATT/land available, relative to SUB counts | Not all ground-and-pound, not damage or grounded-minute offensive intensity |
| Scramble grappler | Reversals and partial standup counts | No transition sequence, ground-entry count, exposure per scramble or validated escape rate |
| Takedown-volume fighter | Attempt and completion counts with generic CTRL/TD proxy | Completion does not establish stable entry; alternate ground-entry mechanisms absent |

The cells contain descriptive variation in measurable offensive activity, but the audit **cannot assign verified mechanism classes** or establish that an unobserved mixture causes the residual calibration gap. B3/B5 differences in support are not new subgroup performance estimates. Both cells use identical source rules, and their annual/recent distributions are retained without pooling away era gaps. No individual fights were selected to illustrate a preferred hypothesis.

{common}''')
 cv=bins[(bins.outer_year.isin([2018,2026]))&(bins.scope.isin(['training_fighters_at_boundary','frozen_training_prefight']))&(bins.window=='career')&bins.field.isin(['submission_attempts','submission_attempts_faced'])]
 md('SUBMISSION_CONVERSION_SUPPORT.md',f'''# Submission conversion support

**Recorded SUB finish / recorded SUB attempts is not yet a defensible fighter-level conversion probability.** It combines bout results with provider-coded attempt counts and does not supply an event-linked success/failure trial definition.

Across historical UFC bouts through the existing boundary: **{checks['prior_ufc_submission_wins']} submission wins**, **{checks['complete_attempt_bouts']} with complete attempt observations**, **{checks['wins_with_zero_recorded_attempts']} wins despite zero recorded SUB attempts**, and **{checks['missing_attempt_bouts']} wins with incomplete/missing attempts**. Raw recorded attempts total **{checks['all_ufc_attempts']:.0f}**. These are broader historical-support counts, not the modern conditional training outcome counts and not newly scored evaluation results.

The zero-attempt finish cases make a literal event-level Bernoulli conversion interpretation invalid without a separately reviewed semantic correction. Do not add an attempt automatically for a successful finish: that would modify measurement definitions. Zero-success histories with observed attempts remain distinct from zero attempts and missing attempts.

## Earliest and latest support bins

{table(cv[['outer_year','scope','field','support_bin','states','total_states','pct']])}

Complete 2018–2026 tables include 0, 1, 2–4, 5–9 and 10+ attempt/faced bins, separate missingness, and SUB wins/losses at original training and scoring dates. Full tables: `conversion_support_bins.csv`. Bout pairing and preserved counts: `bout_measurements.csv.gz`; measurement conflicts: `CONVERSION_MEASUREMENT_CHECK.json`.

A future conversion experiment must first settle whether a finish implies an observed successful attempt and whether failed attempts share a consistent event definition. Then a prior-only hierarchical/shrunk count model with support and uncertainty would be required; an unregularized raw ratio is not a production recommendation. No shrinkage hyperparameter is selected or estimated here. Many fighters have fewer than five prior attempts, so any future individual conversion estimate would often be prior-dominated. Submission attempts faced also confound opponent access and activity; they do not independently measure defensive skill.

{common}''')
 yp=year[year.field.isin(['ground_bucket_min','ground_control_bucket_min','standups']) & (year.year>=2013)]
 md('FIGHTMETRIC_POSITION_TIME_DECISION.md',f'''# FightMetric / position-time decision

**Usable for coarse, partial positional diagnostics: yes. Usable as broad exact historical grounded-duration exposure for this mechanism experiment: no.** The repository contains actual measurements and completed ingestion/audits, not just a proposed source.

Source: official UFC.com Drupal JSON:API `fight_stat` snapshot `20260820T123046Z`, stored raw pages and manifest; builder `pipelines/build_canonical_fightmetric_position_v0.py`; output `data/canonical/v0/fighter_round_position.csv`. Identity, round-summary, corner, duplicate-version and bucket gates are documented in the lineage report. Canonical position source has 32,156 rows, 6,803 fights and 2,459 fighters; quarantine has 5,955 field/source items (4,806 missing fight identity, 996 duplicate-version source items, 153 out-of-range buckets). Quarantine items are not interchangeable with numbers of excluded fights.

## Available fields and units

Standing, neutral, distance, clinch, ground, ground control, guard, half guard, side, mount, back and misc ground-control buckets plus standups are stored. For each time bucket b, the canonical contract provides bounds b×60..b×60+59 seconds, to intersect with observed elapsed round time. These are quantization bounds, not measured exact duration. Raw generic `control_time` matched floor(Greco precise control seconds/60) in 97.454% of 23,876 comparisons; broader time-family relationships provide corroboration, not proof of independently documented vendor seconds. Values >5 and unresolved versions are withheld. The new duration-bound check additionally detects 6 impossible lower bounds for ground time; those pairs are excluded diagnostically.

Ground occupancy can include either fighter on top/bottom; ground control describes a fighter's control, not the common opportunity denominator. Back/mount buckets may describe positional occupancy at coarse resolution but not submission threat quality. Zero buckets do not prove absence of position; intervals allow short exposure. Standups are sourced from `grap_stand_land`; no escape/standup attempt or event-linked opportunity count is present.

## Canonical year coverage against expected rounds

{table(yp[['year','field','fights','expected_fighter_rounds','observed_rows','missing_pct','observed_zero_rows']])}

Full 1993–2026 annual data are in `year_field_coverage.csv`; `year_position_coverage.csv` additionally covers every stored positional family (including guard/half/side/mount/misc/clinch/standing/neutral/distance), not only the ground examples above; expected rounds for bouts with unknown terminal round are not invented. The prior raw dated-source audit spans 1993–2026; it is a different denominator from this canonical coverage table. Grounded time largely covers 2013–2018, partially 2019–2020, and is absent from recent source eras. Ground-control data persist but cannot repair the missing occupancy variable.

## Reproducibility and temporal governance

All original raw pages match their original manifest SHA256; all input tables, semantic code and source audits are enumerated in `SOURCE_IDENTITIES.json`. This audit reuses canonical transport identities and does not refresh external payloads. Historical states select only earlier event dates; source acquisition was in 2026, so old publication versions/revisions cannot be asserted. Missing years and ambiguous identities remain missing; no later stat fills an earlier gap.

## Incremental value and rights

Incremental beyond F02: partial coarse ground/position occupancy and stand-up counts. These could support an interval-aware, coverage-restricted *measurement diagnostic* after semantic review, but not exact activity per grounded minute across frozen folds. Generic CTRL, reversals and ground significant-strike composition already exist in F01/F02, so those are representation candidates rather than newly acquired measurements. Additional raw ground-strike splits need semantic review.

No source-specific grant for modeling/redistribution was located in the inspected repo manifests or candidate notes. A current read-only check of official UFC terms URLs on 2026-10-03 returned fetch failures/403; `EXTERNAL_SOURCE_CHECK.json` records that limitation. Public JSON access and the mirror's availability do not establish a transferable data license. No purchase, outreach, fresh data acquisition or legal conclusion was undertaken. The provider-entitlement sample gate must establish permissible storage/model-development use and future reproducibility.

## Exact missing measurements

Common ground-state elapsed seconds per bout/round (including bottom and scrambles); distinct attacker control/top duration; identifiable ground entries; escape/stand-up opportunity and successful returns-to-standing with actor/context; positional transition ordering if scramble classes are required; source definitions and version/availability dates. Exact ground duration is the central missing denominator, not another TD-defense percentage. Phase-tagged SUB attempts are additionally necessary if the claim is creation occurring specifically on the ground, rather than overall SUB activity normalized by ground exposure.''')
 md('NEXT_EXPERIMENT_FEASIBILITY.md',f'''# Next experiment feasibility

**B — EXTERNAL GROUND-EXPOSURE SOURCE REQUIRED**

The repository has useful offensive counts and real coarse position data. It cannot currently deliver broadly complete, semantically defensible activity per genuine grounded opportunity through the frozen chronological experiment. This is a measurement conclusion; it does not establish the cause of B3's historical bias or reject all useful count-based hypotheses.

## Plain-English answers

1. **Control versus genuine SUB opportunity:** limited proxy description only. Control and SUB attempts are observed, but actual time in a submission-capable environment and threat quality are not.
2. **SUB-oriented activity versus ground-and-pound:** recorded SUB attempts versus significant ground strikes can be compared. They do not measure finish quality, all grounded strikes or offense per ground minute. Broad tendency is observable; the requested fully grounded mechanism distinction is not established.
3. **Sustained access and escapes:** generic CTRL and CTRL/completed-TD are retention proxies; coarse positional buckets and standups add partial information. Ground entries, transition timing and opportunity-normalized escape ability remain unavailable.
4. **Existing ground-exposure data:** actual coarse partial records exist; no broadly usable exact grounded-duration source exists. Therefore neither 'there is nothing' nor 'we already have exact ground minutes' is correct.
5. **Surviving candidates:** paired SUB/TD, generic CTRL/TD, total-time-normalized SUB and significant ground activity survive retrospective chronology as explicitly limited diagnostics, including early-fold measurement coverage. Grounded-minute candidates fail. Conversion has sparse support and zero-attempt finish conflicts; standup/reversal counts survive as counts, not escape rates. No candidate is promoted.
6. **Still missing:** common grounded seconds across historical eras; distinct control/bottom context; ground entries and meaningful escape opportunities; quality/event semantics for SUB attempts and conversion; proven source vintages and rights.
7. **Narrowest justified next work:** verify a historical ground-exposure source/sample. Do not launch another MOV1 representation or classifier to explain this gap by assumption.

## One immediate milestone

**UFC_EDGE_GROUND_EXPOSURE_BACKFILL_AND_SEMANTICS_SAMPLE_AUDIT_V1**

Obtain and audit a reproducible, legitimately usable historical sample/schema that supplies **ground-state seconds separately from top/control seconds**, identity-matched to current UFCStats rounds. Existing exact-TIP/sequence provider mentions in `provenance/source_inventory.md` and the supplied simulator report are leads, not established sources. A source with only TD counts, generic CTRL, coarse minutes or modern-only positional stats fails this purpose.

Minimum historical scope: the full 2015–2026-08-15 frozen modeling era, **plus earlier UFC bouts contributing to the contemplated prior histories**, especially all earlier observations used by fighters in the 2015–2017 training cohort. `bout_measurements.csv.gz` and exact fold IDs define that required bout list; do not silently drop pre-2015 history or fill its denominator with later statistics. For a full-career candidate, every included numerator observation needs same-source/compatible ground exposure; otherwise it is an explicitly restricted matched-history candidate and must pass original-date early-fold coverage. The sample must span earliest training-era history and 2018, 2021, 2024 and 2026, all represented divisions, bottom-position submissions, short finishes and zero-ground bouts. Sampling is measurement/era-based, not selected for B3 outcome agreement; only pre-boundary outcomes may be used for identity reconciliation.

Required fields: stable fight/fighter IDs, event date, actual round, elapsed round seconds, **common ground-state seconds**, definition of ground/clinch/scramble boundaries, separate controller/top/bottom duration if supplied, units, missing/zero meaning, source version/acquisition/availability timestamps and revision policy. Obtain SUB-attempt phase labels if claiming grounded-only creation; otherwise preregister the overall-SUB/ground-time proxy limitation. For retention/escape claims also require identifiable entries and standup/escape opportunities/completions with actor. Otherwise freeze that narrower claim as unsupported. Counts of total ground strikes or standups without this denominator do not pass.

Proposed acceptance gates to freeze **before requesting/inspecting performance**: matched numerators and denominators; no impossible duration/identity collisions; year/division missingness explicitly enumerated; no selective modern backfill; reproducible frozen exports; written permissible research/modeling retention rights; original-date support and uncertainty demonstrably adequate in the 2018 fold. Numeric missingness/support tolerances must be preregistered in that separate source contract from coverage requirements, not chosen to improve B3 results. Passing the source gate would authorize drafting a new **small frozen mechanism implementation contract**, not fitting immediately.

No predictive implementation-contract handoff is issued now because conclusion A was not reached. This milestone is a source/measurement audit only. It does not promote Arm C, recover unrelated MOV0 models, change F01/F02, revise B3/B5, unseal forward results or implement a simulator.

## Limits

The same historical outcomes/cells have been inspected repeatedly. Heterogeneity describes availability and activity variation, not causal mechanisms, new predictive performance or a fresh holdout. Common ground time alone would not establish submission opportunity quality, all offensive actions or tactical intent. If a richer sample still cannot operationalize those concepts, conclusion C may become necessary in the next source audit. No fitted result or hypothetical classifier score is calculated here.''')
 md('README.md','''# Ground opportunity & competing finish-pathway data audit V1

Read `NEXT_EXPERIMENT_FEASIBILITY.md` first, then source lineage, coverage and the dedicated FightMetric decision. Conclusion B. Zero model fits; no frozen source changes.

Reproduce from the audit branch (Python 3.12 with the pinned numpy/pandas/scipy dependencies in `requirements.txt`):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python tools/audits/audit_ground_opportunity_competing_pathways_v1.py
PYTHONDONTWRITEBYTECODE=1 python tools/audits/report_ground_opportunity_competing_pathways_v1.py
```

Research-context documents are preserved source inputs (in the source manifest), not generated outputs. Both scripts support `--output-dir /tmp/ufc-ground-audit-reproduction`; run both with that same directory to compare all output hashes. Gzip outputs have deterministic timestamp metadata. Source pages and PR #125 archive parts are SHA-verified; only the saved evaluation member is decoded, not native models. No training packages or external data are used.

Tables preserve numerator/denominator/support/missingness and explicit zero opportunities. `boundary_coverage.csv`, `fold_state_coverage.csv`, `conversion_support_bins.csv` and `year_field_coverage.csv` are the primary coverage tables. `B3_B5_*` use frozen cell membership. State tables repeat prior observations across prediction times and must not be interpreted as independent samples. No numeric style classes were selected.

`STRICT_PRIOR_VERIFICATION.json` contains executable chronology and future-mutation gates; the evidence manifest seals source/code/report/table bytes. The completion marker records the manifest digest. Historical publication vintages and licensing are unresolved, not declared to pass by the retrospective event-date check.''')
 # Save raw transport inventory, without promoting semantics.
 fm=R/'data/raw/ufc_fightmetric_official/20260820T123046Z/manifest.json';m=json.loads(fm.read_text())
 attrs=next(a['attribute_coverage'] for a in m['collections'] if a['name']=='fight_stat') if any(a.get('name')=='fight_stat' for a in m['collections']) else m['collections'][0]['attribute_coverage']
 rows=[dict(field=k,**v,status='raw transport only; summaries/duplicates included') for k,v in attrs.items() if 'ground' in k or 'grap_' in k]
 pd.DataFrame(rows).to_csv(out/'raw_additive_inventory.csv',index=False,lineterminator='\n')
 ext={'checked_on':'2026-10-03','scope':'rights ascertainability only; after existing-repository ground-exposure gap established','official_urls':['https://www.ufc.com/terms','https://www.ufc.com/news/terms-use'],'result':'terms URL fetch failed; news/terms-use 403. Search excerpt does not establish a data/modeling license.','licensing_conclusion':'UNVERIFIED; no legal interpretation or grant asserted','external_data_ingested':False,'provider_backfill_claims_verified':False}
 (out/'EXTERNAL_SOURCE_CHECK.json').write_text(json.dumps(ext,indent=2,sort_keys=True)+'\n')
 identities=obj('SOURCE_IDENTITIES.json')
 for a in identities['sources']:assert sha(R/a['path'])==a['sha256']
 assert identities['script_SHA256']==sha(R/'tools/audits/audit_ground_opportunity_competing_pathways_v1.py')
 artifacts={str(p.relative_to(out)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file() and 'research_context' not in p.parts and p.name not in ['EVIDENCE_MANIFEST.json','UFC_EDGE_GROUND_OPPORTUNITY_AND_COMPETING_PATHWAY_DATA_AUDIT_V1_COMPLETE.json']}
 scripts={str(p.relative_to(R)):sha(p) for p in [R/'tools/audits/audit_ground_opportunity_competing_pathways_v1.py',Path(__file__)]}
 manifest={'starting_repository_SHA':BASE,'branch':'audit/ground-opportunity-competing-pathways-v1','feasibility_conclusion':'B','fits':0,'sources':identities['sources'],'scripts':scripts,'artifacts':artifacts,'source_governance':'retrospective strict event-date prior only; publication vintages unverified'}
 (out/'EVIDENCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
 digest=sha(out/'EVIDENCE_MANIFEST.json')
 marker={'status':'UFC_EDGE_GROUND_OPPORTUNITY_AND_COMPETING_PATHWAY_DATA_AUDIT_V1_COMPLETE','starting_repository_SHA':BASE,'evidence_manifest_SHA256':digest,'conclusion':'B','fits':0,'frozen_models_changed':False,'merged':False}
 (out/'UFC_EDGE_GROUND_OPPORTUNITY_AND_COMPETING_PATHWAY_DATA_AUDIT_V1_COMPLETE.json').write_text(json.dumps(marker,indent=2,sort_keys=True)+'\n')
 print(json.dumps(marker,indent=2))
if __name__=='__main__':main()
