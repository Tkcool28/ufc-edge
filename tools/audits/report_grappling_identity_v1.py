#!/usr/bin/env python3
"""Render descriptive tables and semantic conclusions; never fit a model."""
from pathlib import Path
import json
import pandas as pd
from audit_grappling_identity_v1 import OUT, METRICS, upstream
P=OUT
COMMON='''
Histories use event_date < target date, excluding the target and same-date bouts. The sealed source ends 2026-08-15. No predictive fits, source changes, hard fighter labels, prospective outcomes, threshold optimization or Arm C promotion. These are retrospective event-date histories; current acquisition snapshots do not prove historical publication vintages. A denominator screen means descriptive support, not proven reliability. Repeated fighter states and nested annual boundaries are not independent samples.
'''
def read(n):return pd.read_csv(P/n)
def table(d,cols=None):
 if cols:d=d[cols]
 def fmt(v):return 'NA' if pd.isna(v) else f'{v:.3f}' if isinstance(v,float) else str(v)
 return '| '+' | '.join(d.columns)+' |\n| '+' | '.join(['---']*len(d.columns))+' |\n'+''.join('| '+' | '.join(fmt(v) for v in row)+' |\n' for row in d.itertuples(index=False,name=None))
def report(n,title,text):(P/n).write_text('# '+title+'\n\n'+text.strip()+'\n'+COMMON)
def main():
 cov=read('chronological_support.csv');st=read('nonoverlapping_stability.csv');match=read('matched_access_dimensions.csv');tim=read('finish_timing.csv');repeat=read('repeat_finish_timing.csv');dc=read('paired_decision_finish_control.csv');assoc=read('duration_associations.csv');cells=read('B3_B5_identity_distributions.csv')
 def stability(ms):return table(st[st.year.isin([2018,2026])&st.screen.eq('supported_both_blocks')&st.metric.isin(ms)],['year','metric','unique_fighters','spearman'])
 def access(ms):return table(match[match.year.eq(2018)&match.metric.isin(ms)],['access_quartile','metric','supported_fighters','p25','p50','p75'])
 definitions=pd.DataFrame([dict(metric=m,numerator=a,denominator=b,scale=c,denominator_screen=d,minimum_matched_bouts=e) for m,(a,b,c,d,e) in METRICS.items()])
 definitions.to_csv(P/'measurement_definitions.csv',index=False)
 report('GRAPPLING_IDENTITY_SOURCE_LINEAGE.md','Grappling identity source lineage','''Starting main: `b8194cd37831348bd856900cba134d05ff21e430`, exact supplied anchor; no intervening commits. PR #125 head `f39a525312dbc920002a93faf48edb53770510c0`, merge `3e2b14a8391ed17d072b4bbb9570b31bc6d12b85`; PR #158 head `caaa20b7e1f565b2749b3be95cb512eff27f743f`, merge is starting main. Metadata independently read through the connected GitHub plugin.

The complete PR #158 manifest (`6fe5387b3d4b184fc61e2c1c1ca1fe0844daa8b6b6e056ac83e62c86d5dd447b`), its source identities, scripts and saved outputs are hash-verified before analysis. Core bout counts are independently reconciled to complete canonical rounds; see VALIDATION.json. PR #125 evaluation archive hash and frozen membership equality are checked by the upstream saved-only reader. Original bytes remain untouched.

| Measurement | Source and transport | Actual interpretation |
|---|---|---|
| TD attempts/landed/failed | Greco `TD` -> `pipelines/build_canonical_core_v0.py` -> `data/canonical/v0/fighter_round_stats.csv` | Attempt/completion activity; failed=attempted-landed, not ground entries |
| Opponent TD defense | Opponent same-bout TD counts | Failed opponent attempts / opponent attempts; not escape skill |
| Generic CTRL | Greco `CTRL` -> `control_sec` | Recorded generic control seconds, includes no validated top-only guarantee |
| SUB created/faced | Greco `SUB.ATT`, paired opponent round rows | Recorded attack counts; no threat quality or phase tags |
| Significant ground strikes | Greco `GROUND` attempted/landed | Ground-context significant strikes; not all GnP, impact, or ground KO attribution |
| Outcomes/finish timing | `fights.csv`, `events.csv`, governed `elapsed_exposure.py` and rules registry | Bout method, ending round/clock and true elapsed fight time where rules support it; no time since ground access |
| Reversals | `REV.` -> reversals | Action counts, not escape trials |
| Position/standups | official FightMetric -> `fighter_round_position.csv` | Partial coarse floor-minute buckets/landed standups; no complete escape opportunity denominator |

The raw source is pinned under `data/raw/greco1899/8e40eb945e11/`; detailed owner precedence, raw mappings, F01 windows, priors and chronology remain documented in PR #158's GROUND_OPPORTUNITY_SOURCE_LINEAGE.md. This audit does not replay or alter F01/F02. It separately derives unshrunk diagnostic career histories from complete paired bouts. No partial-round numerator is divided by a full-bout denominator. Partial careers remain explicit in coverage, and sums across a career exclude missing bouts rather than filling zeros.

`measurement_definitions.csv` specifies every candidate, units, scale and fixed support screen. `identity_states.csv.gz` retains numerator, denominator, matched bouts, support and latest prior date. `outcome_separated_prior_states.csv.gz` separates prior decisions, all prior SUB finishes and all prior KO finishes including losses. Own finish-win comparisons are separately reported. No observed historical UFC bouts means no prior UFC history, not proof of professional debut.

No attempt/strike/control weighted composition is defined: SUB counts and strike counts have different units. SUB/ground-strike counts are only a transparent proxy ratio. A control-with-low-offense share would require a separately frozen round-level low-offense definition; none is manufactured here. Control per TD is generic retention proxy and can include control entered without a TD. A prior fight with a landed TD can be selected as an access-positive context, but no universal 'grappling-heavy fight' threshold or true sustained stretch is identified.''')
 report('CONTROL_BEHAVIOR_DIAGNOSTIC.md','Control behavior diagnostic','''Generic control contains repeatable behavioral information. In disjoint first-three versus next-three prior bouts, elapsed control share has substantially stronger rank persistence than CTRL per landed TD. This supports studying control tendency; it does not measure top retention after a specific entry.

'''+stability(['td_attempts_per15','control_share','control_sec_per_fight','control_sec_per_td','control_allowed_share'])+'''
Comparable TD-attempt activity still leaves a wide continuous control-share distribution:

'''+access(['control_share'])+'''
These are training-fighter boundary snapshots with three matched bouts and at least 15 elapsed minutes. Access quartiles are outcome-blind descriptive strata, not style labels. Opponent selection, TD conversion, clinch control and career development are unadjusted. Control allowed is useful as an opponent-history measurement, with weaker persistence; it cannot become a standup/escape probability.''')
 report('SUBMISSION_ORIENTATION_DIAGNOSTIC.md','Submission orientation diagnostic','''Recorded submission activity has moderate repeatability and measurable variation among similar-access histories. Together with control it supports a partial continuous submission-seeking representation. Low SUB counts alongside high CTRL are observable behavior, not proof of deliberate safe grinding.

'''+stability(['sub_attempts_per_fight','sub_attempts_per_min','sub_attempts_per_td','sub_attempts_per_control_min_PROXY','sub_wins_per_fight','sub_to_ground_attempts_PROXY'])+'''
'''+access(['sub_attempts_per_min','sub_attempts_per_td'])+'''
SUB per TD retains a small selected cohort; SUB per control minute is less repeatable and control is not submission opportunity. The median original training-date SUB count is only one in the 2018 and 2026 folds. Sparse rates need substantial pooling. SUB wins per prior fight are legal prior outcomes but overlap existing finish-profile information. Do not estimate finish-per-attempt probability: PR #158 documents wins with zero recorded attempts and no verified Bernoulli attempt trials. No attempt quality or access-to-attempt timing is identified.''')
 report('GROUND_AND_POUND_ORIENTATION_DIAGNOSTIC.md','Ground-and-pound orientation diagnostic','''Significant ground-striking orientation is observable but less persistent than control or submission activity in equal-length disjoint histories. This is evidence for a cautiously pooled ground-striking tendency, not a reliable standalone GnP-wrestler class or ground-KO hazard.

'''+stability(['ground_attempts_per_fight','ground_attempts_per_min','ground_landed_per_fight','ground_attempts_per_td','ground_attempts_per_control_min_PROXY','ground_attempts_allowed_per_min'])+'''
'''+access(['ground_attempts_per_min','ground_attempts_per_td'])+'''
Ground activity can also follow knockdowns, opponent takedowns or bottom exchanges. A KO/TKO method does not say the finish occurred on the ground. Significant counts omit nonsignificant punches and do not measure damage. Per-control-minute activity is explicitly a generic-control proxy; its higher early persistence does not establish a true exposure rate. No optimized mixture of SUB and strike counts is used.''')
 tt=tim[tim.scope.eq('modern_2015_prior')&tim.scheduled_rounds.eq('ALL')&tim.year.isin([2018,2026])]
 report('FINISH_TIMING_DIAGNOSTIC.md','Finish timing diagnostic','''Modern historical submissions are not generally earlier than KO/TKO. The proposed 'submission hunters end immediately after access' explanation is unsupported by these bout-level clocks: access timing is unobserved.

'''+table(tt,['year','method','bouts','elapsed_known','R1_pct','R2_pct','R3plus_pct','median_elapsed_min'])+'''
All-UFC, modern-era and scheduled-round strata are retained in finish_timing.csv. Early UFC single-round formats cannot be pooled as though R1 always means five minutes; governed elapsed exposure is left missing where unsupported.

First versus second historical finish wins, unique fighters, strict event-date ordering:

'''+table(repeat[repeat.year.isin([2018,2026])])+'''
This is a selected repeated-winner sample, not conditional hazard or a calibrated ability estimate. Three prior submission wins occur in only a small share of original training histories; first-three/next-three blocks have insufficient repeated-win support for the screened early-finish-share coefficient. Finish timing mostly adds duration/outcome context here, rather than a robust new identity dimension. No elapsed time from TD/access to submission or KO is inferable.''')
 dd=dc[dc.year.eq(2026)].groupby('finish_subset').agg(fighters=('fighter_id','size'),decision_control_sec=('decision_control_sec_per_fight','median'),finish_control_sec=('finish_control_sec_per_fight','median'),decision_share=('decision_control_share','median'),finish_share=('finish_control_share','median'),decision_min=('decision_duration_min','median'),finish_min=('finish_duration_min','median')).reset_index()
 report('DECISION_VS_FINISH_CONTROL_ANALYSIS.md','Decision versus finish control','''Separating outcomes materially clarifies the meaning of control totals. Within the same fighters, decision and own-finish-win histories show much different raw accumulation and exposure. These are medians across paired fighter-history means, not independent bout observations or causal effects.

'''+table(dd)+'''
The all-prior, decision-only, prior KO/TKO and prior submission states remain separate in outcome_separated_prior_states.csv.gz. The table above compares own finish wins specifically, preventing losses from being presented as the fighter's offensive success. At least one measured bout in each category is enough for this exploratory comparison; many fighters remain sparse.

'''+table(assoc[assoc.year.isin([2018,2026])])+'''
A short SUB win ends control accumulation; low total CTRL in such a win is not low retention ability. Decision-only control removes terminal-duration truncation within that subset, but conditioning on decisions selects opponent, durability and scheduled-length environments. It does not remove every bias. Both raw seconds and elapsed share must remain visible. A first experiment should isolate decision-only control rather than add finish timing, finish conversion and several proxies simultaneously.''')
 for cell in ['B3','B5']:
  frozen=json.loads((P/(cell+'_FROZEN.json')).read_text());d=cells[cells.scope.eq(cell)&cells.year.eq('ALL')&cells.metric.isin(['control_share','sub_attempts_per_min','ground_attempts_per_min','sub_attempts_per_td','sub_to_ground_attempts_PROXY'])]
  text=f"Frozen cell: {frozen['all_bouts']} all-scored bouts; {frozen['standard_finishes']} standard finishes. Observed SUB {100*frozen['observed_sub']:.3f}%; saved Arm A {100*frozen['Arm_A_sub']:.3f}%; saved Arm C {100*frozen['Arm_C_sub']:.3f}%. Membership and probabilities are unchanged. Both fighter sides of every cell bout are retained.\n\n"
  text+=table(d,['metric','states','nonmissing_histories','supported_pct','ratio_p25','ratio_p50','ratio_p75'])
  text+='\nContinuous profiles vary across control, SUB and significant ground offense. Annual distributions and original numerator/denominator counts are retained. These summaries mix both sides: frozen MATCH does not uniquely identify a criterion-supplying attacker. They cannot prove a grinder/GnP mixture caused the calibration gap.\n'
  if cell=='B3':text+='B3 is not a homogeneous submission identity despite access plus pressure membership. Variation is visible, but no new outcomes-based cut or subgroup performance test is created. Weak ground-strike repeatability limits the proposed GnP explanation.\n'
  else:text+='B5\'s saved improvement supports its existing directional pressure/vulnerability representation. Its pooled median prior SUB rate (0.064/min) is similar to B3 (0.066/min), while median generic control share is lower (0.241 versus 0.326); the SUB/ground-strike proxy median is only slightly higher (0.071 versus 0.068). These two-side histories do not establish a categorically more coherent submission-attacker identity. Neither cell is a manual fighter taxonomy, and this diagnostic cannot attribute Arm C\'s improvement to newly measured identity.\n'
  report(cell+'_GRAPPLING_IDENTITY_ANALYSIS.md',cell+' grappling identity analysis',text)
 # Saved prediction movement association only, never target-outcome fitting.
 evidence,_=upstream.recover_evidence();panel=read('B3_B5_identity_states.csv.gz');movement=[]
 for cell,g in panel.groupby('cell'):
  z=g.groupby('target_fight_id')[['control_share','sub_attempts_per_min','ground_attempts_per_min']].agg(['mean','count'])
  ev=evidence.set_index('fight_id');delta=ev.K_A-ev.K_C
  for metric in ['control_share','sub_attempts_per_min','ground_attempts_per_min']:
   v=pd.DataFrame({'mean_two_sides':z.loc[z[(metric,'count')].eq(2),(metric,'mean')],'saved_C_minus_A_sub':delta}).dropna()
   movement.append(dict(cell=cell,metric=metric,bouts_both_sides_measured=len(v),spearman=v.corr(method='spearman').iloc[0,1]))
 md=pd.DataFrame(movement);md.to_csv(P/'B3_B5_saved_prediction_movement.csv',index=False,float_format='%.10g')
 for cell,g in md.groupby('cell'):
  dest=P/(cell+'_GRAPPLING_IDENTITY_ANALYSIS.md')
  with dest.open('a') as fh:fh.write('\n## Association with saved prediction movement\n\n'+table(g)+'\nSigned movement is saved P_C(SUB)-P_A(SUB). Both fighter sides must have measured values. This outcome-free association uses overlapping historical fight profiles; it does not identify which actor drove Arm C, establish style coherence, or explain individual loss improvement.\n')
 early=cov[cov.scope.eq('training_prefight')&cov.division.eq('ALL')&cov.metric.isin(['control_share','sub_attempts_per_min','ground_attempts_per_min','sub_attempts_per_td','early_sub_win_share'])]
 report('EARLY_FOLD_IDENTITY_SUPPORT.md','Early-fold identity support','''Support is reported at all nine January 1 boundaries, unique training-fighter snapshots, original training-date states and outer scoring-date states. Original-date tables avoid falsely giving early fights the fighter's later boundary history. Every division is retained in chronological_support.csv, including thin divisions; no pooled percentage proves division-level reliability.

'''+table(early,['year','metric','states','nonmissing_histories','zero_denominators','median_prior_fights','median_td','median_control_sec','median_sub_attempts','median_ground_attempts','no_prior_ufc_pct','supported_pct'])+'''
Control/total-time and SUB/total-time are the most defensible candidate dimensions when history exists; significant ground activity is well transported but noisier. Completion/control-denominator ratios substantially reduce usable support. Finish-timing identities are especially sparse. Three bouts and a small denominator do not make a stable fighter estimate; these screen percentages are sensitivity descriptions. Preserve numerator, denominator, missing bouts and uncertainty, and pool sparse fighters heavily. Debut percentages mean no prior UFC history only.''')
 report('DIRECTIONAL_MATCHUP_IDENTITY_FEASIBILITY.md','Directional matchup identity feasibility','''**Partial feasibility.** Fighter-side observed tendencies can later be paired with opponent-side measurements without pretending to observe intentions or exact ground transitions.

| Intended future comparison | Measurable sides | Missing mechanism |
|---|---|---|
| Control imposition | A TD attempts/conversion and generic decision control; B TD defense/control allowed | Exact retention after entry, clinch/top separation, escape opportunities |
| Submission-seeking versus exposure | A prior SUB activity; B attempts faced and prior SUB losses | Attack quality, genuine submission-defense trials, bottom access/escape |
| Ground offense versus vulnerability | A significant ground-strike activity; B significant ground attempts allowed | Top/bottom context, all ground punches, ground KO attribution/damage |
| Scramble/escape identity | Reversal counts and partial official standups | Ordered entries/exits, opportunity denominator, modern standup continuity |

These comparisons are compatible with actor/opponent orientation but are not implemented. Retain an explicit unavailable escape/scramble dimension rather than a filled zero. A simulator may use a future validated tendency distribution; it cannot translate these ratios directly into transition rates or tactical intent. No current quantitative simulator parameter is authorized.''')
 report('NEXT_EXPERIMENT_RECOMMENDATION.md','Next experiment recommendation','''**B — PARTIAL IDENTITY IS SUPPORTABLE**

1. **Control wrestler versus submission-focused grappler:** partially distinguishable through generic control share and recorded SUB activity on matched prior histories, with moderate disjoint-block repeatability. No hard class or intention is established.
2. **Versus GnP wrestler:** significant ground offense is observed, but its much weaker persistence and missing finish location only support a noisy pooled ground-striking dimension.
3. **Control stability:** yes, generic elapsed control share is repeatable behavior despite not being true grounded exposure.
4. **Decision separation:** yes, it clarifies outcome-truncated accumulation; it adds selection bias and is sparser, so it is not automatically superior as a predictor.
5. **Finish timing:** primarily contextual here. Submissions are not generally earlier than KO; time after access is unavailable and repeated-win histories are thin.
6. **Early folds:** TD activity, control share and SUB activity have usable but incomplete support. TD-normalized and control-normalized ratios need substantial pooling; early-submission identity does not have broad support.
7. **Directional representation:** action tendencies versus opponent observed resistance/exposure are feasible as future hypotheses; escape, top retention, threat quality and causally located GnP finishing remain unavailable.
8. **Next test:** one frozen, nonpredictive measurement experiment below.

## One recommended frozen experiment

**GRAPPLING_IDENTITY_DECISION_CONTROL_VS_SUB_ACTIVITY_REPLICATION_V1** — first test whether decision-only generic control share adds repeatable fighter-side information distinct from total-time SUB attempt rate among similar TD-access histories. Freeze exactly three transparent dimensions: TD attempts per governed total elapsed minute (access); generic control seconds / elapsed seconds **in prior decisions only** (decision control); SUB attempts / governed elapsed minutes **across all prior complete measured UFC bouts** (SUB activity). Preserve matched numerator/denominator support separately; do not combine units into a weighted score.

Freeze chronology, within-division prior-only population priors, uncertainty policy, fixed nonoverlapping history-block selectors, access-comparison rules and numeric acceptance gates in a separate contract BEFORE new replication results. Test repeatability, missingness and decision-selection sensitivity using disjoint earlier-history blocks with all-history CTRL as the prespecified comparator. Do not select thresholds using B3/B5 outcomes. Retain fighters lacking prior decisions as missing/prior-dependent, not zero control. No MOV0/MOV1 fit, prediction change, interaction or simulator in that first experiment.

For later regularization, use prior-only partial pooling: count/exposure rates suit a Gamma-Poisson or hierarchical overdispersed count model; TD completion probability may use beta-binomial; SUB win per fight is a fight-outcome rate, not SUB-win-per-attempt conversion. Generic control seconds are correlated duration, not independent Bernoulli seconds: use a suitable bounded-duration/hierarchical model or transparent prior-exposure estimator with uncertainty rather than a literal beta-binomial trial count. Freeze strengths from prior-only measurement evidence, never outer outcomes. Prior UFC absence alone cannot authorize a confident debut prior without the existing completeness governance.

The next frozen replication is concrete and achievable with existing data. It does not postpone behavioral work until exact ground data arrives, and it does not authorize a predictive challenger yet. GnP/control-ratio/finish-timing expansion is deferred until it independently meets a frozen stability and support gate.

## Limitations

The historical population/cells have already been repeatedly inspected; this is developmental evidence, not fresh prospective confirmation. Equal three-fight blocks are small and select experienced survivors; opponents, division transitions, aging and tactical development are unadjusted. Boundary cohorts overlap. Ratios from partial careers can differ from complete histories. Control includes unspecified phase, SUB attempts have no quality tags, significant ground strikes omit some GnP, and no bout KO label identifies location. Published timing describes completed finishes, not risk-set hazards. Rights and original provider vintages are not newly established. No label accuracy, predictive benefit or causal mechanism is claimed.''')
 report('README.md','Grappling identity and competing ground pathways V1','''**B — PARTIAL IDENTITY IS SUPPORTABLE.** Existing history supports a cautious continuous control/SUB behavioral representation. Significant ground striking is measurable but less persistent; escape, position-specific retention and tactical intent remain unidentified.

Starting main: `b8194cd37831348bd856900cba134d05ff21e430`. Branch: `audit/grappling-identity-competing-pathways-v1`. All twelve requested reports and machine-readable descriptive tables are in this directory. TRAINING_BACKGROUND_FEASIBILITY.md contains separately verified primary-source feasibility; no biographies enter the numeric audit.

Run `python tools/audits/audit_grappling_identity_v1.py` then `python tools/audits/report_grappling_identity_v1.py`. Verify with `python tools/audits/verify_grappling_identity_v1.py`. Requirements are pinned in requirements.txt. The manifest hashes artifacts, scripts, upstream evidence identities and contextual references. The completion marker records the manifest digest, so it is deliberately outside its own manifest.

PR #158's ground-exposure conclusion is preserved. This narrower behavior conclusion does not claim exact grounded exposure or authorize a new MOV1 experiment.''')
if __name__=='__main__':main()
