# Grappling identity source lineage

Starting main: `b8194cd37831348bd856900cba134d05ff21e430`, exact supplied anchor; no intervening commits. PR #125 head `f39a525312dbc920002a93faf48edb53770510c0`, merge `3e2b14a8391ed17d072b4bbb9570b31bc6d12b85`; PR #158 head `caaa20b7e1f565b2749b3be95cb512eff27f743f`, merge is starting main. Metadata independently read through the connected GitHub plugin.

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

No attempt/strike/control weighted composition is defined: SUB counts and strike counts have different units. SUB/ground-strike counts are only a transparent proxy ratio. A control-with-low-offense share would require a separately frozen round-level low-offense definition; none is manufactured here. Control per TD is generic retention proxy and can include control entered without a TD. A prior fight with a landed TD can be selected as an access-positive context, but no universal 'grappling-heavy fight' threshold or true sustained stretch is identified.

Histories use event_date < target date, excluding the target and same-date bouts. The sealed source ends 2026-08-15. No predictive fits, source changes, hard fighter labels, prospective outcomes, threshold optimization or Arm C promotion. These are retrospective event-date histories; current acquisition snapshots do not prove historical publication vintages. A denominator screen means descriptive support, not proven reliability. Repeated fighter states and nested annual boundaries are not independent samples.
