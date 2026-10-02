# UFC EDGE — Fight Simulator Data Feasibility Deep Research Audit V1

**Status:** `UFC_FIGHT_SIMULATOR_DATA_FEASIBILITY_RESEARCH_V1_COMPLETE`
**Research cutoff:** September 18, 2026, America/Denver
**Repository audited:** `Tkcool28/ufc-edge`
**Authoritative commit:** `df2692934565b905f3b53380ec86b01bd42408fc`
**Hard verdict:** `ROUND_STATE_SIMULATOR_FEASIBLE`

The requested commit is the current post-PR-#71 foundation examined for this audit, including the corrected frozen M1 marker and the F00/F01/F02 feature infrastructure. The repository explicitly separates feature infrastructure from simulator implementation and already contains simulator-specific data-requirement contracts that refuse to reinterpret generic control time or coarse positional buckets as exact fight state.

The central conclusion is blunt:

> **UFC EDGE cannot honestly build the originally envisioned high-fidelity, event-by-event UFC simulator from broadly obtainable, reproducible historical data today. It can, however, build a genuine and defensible round-resolution fight-process simulator with competing finish hazards and simulated round statistics.**

A coarse within-round simulator can also be *constructed*, as prior academic work has demonstrated, but with the data UFC EDGE reproducibly possesses it would require assumed or inferred transitions that historical observations do not identify. That makes it an assumption-driven mechanistic model, not an empirically grounded reconstruction of UFC fight paths. The distinction matters.

## Executive verdict and original simulator requirement map

The original vision contains two very different classes of state: things a data provider could directly record, and things that are inherently latent even with perfect play-by-play.

**Directly observable fight process.** A genuinely high-fidelity historical training surface would ideally record, in chronological order, round clock; fighter identity; every strike attempt and landing; target; weapon/type; significance or some better impact descriptor; knockdown time; takedown attempt and completion; clinch entry and exit; standing-to-ground transitions; controlling fighter; guard, half guard, side control, mount and back control; submission attempt/type; reversal/sweep; stand-up/escape; referee reset; round boundary; finish mechanism; and final finish time. UFC EDGE's provisional `fight_action_events` schema already anticipates essentially this structure, including event order, clock, actor/target, positions before/after, strike detail and grappling detail—and, importantly, explicitly warns against inventing transitions when a provider only supplies aggregate exposure.

**Latent fight process.** Damage, accumulated fatigue, confidence/momentum, tactical intent, tactical adaptation, pain, injury severity and physiological recovery are not direct observations merely because a detailed action log exists. Even “significant strike” is a scoring/statistics classification, not a physical measurement of impact energy or biological damage. A simulator could maintain latent variables for some of these concepts, but they would be *modeled states* whose interpretation depends on validation, not historical ground truth.

A useful way to define the data boundary is:

| Simulator concept | Ideal observation | Is it intrinsically observable? | Requirement for a high-fidelity model |
|---|---|---:|---|
| Fight phase | Timestamped distance / clinch / ground entry and exit | Yes | Exact sequence or sufficiently dense state observations |
| Ground position | Guard / half / side / mount / back, controller/top-bottom | Yes | Timestamped position and controller |
| Striking | Attempt, landed, target, weapon/type, context, timestamp | Yes | Atomic action feed |
| Knockdowns | Actor and exact timestamp | Yes | Atomic event feed |
| Takedowns | Attempt and completion timestamps | Yes | Atomic event feed |
| Submissions | Attempt, technique, start/end, result | Yes | Atomic event feed |
| Control | Exact phase/position duration and controller | Yes | Exact exposure or transitions |
| Finish | Round, clock, mechanism | Yes | Already broadly available |
| Round score | Judge × fighter × round score | Yes | Official scorecards |
| Damage accumulation | True physical harm after each exchange | **No** | Latent state, ideally informed by sensors/medical data |
| Fatigue | Physiological depletion/recovery | **No** | Latent state; pace decay is only a proxy |
| Tactical adaptation | Intentional strategy change | **Mostly no** | Latent, unless separately annotated |
| Momentum/confidence | Psychological state | **No** | Latent |
| Injury during fight | Type/severity/onset | Usually no | Requires specialized annotation/medical evidence |

This gives an important principle for the rest of the audit: **more event data can solve chronology and position, but it still does not turn “damage” or “fatigue” into observed numerical quantities.**

The nearest peer-reviewed proof that an MMA “fight simulator” can be constructed from aggregate free data is Holmes, McHale and Żychaluk's 2023 Markov-chain paper, which estimated fighter skills from freely scraped historical indicators and then simulated fight paths rather than only predicting a binary result. That paper proves that simulation from aggregates is mathematically viable; it does **not** prove that the resulting fine-grained path is historically identified from observed transitions.

That difference drives this audit's final Level-1 boundary.

## UFC EDGE capability and missing-state map

The repository is considerably closer to the *statistical prerequisites* of a simulator than a table inventory alone suggests. Its canonical layer has fighter metadata, fight outcomes/context, actual fighter-round statistics and a separate positional-exposure structure. The F01/F02 layer then turns prior history into point-in-time fighter states while explicitly retaining missingness and preventing current-fight information from leaking backward.

The core canonical fighter-round record contains knockdowns; generic control seconds; reversals; submission attempts; significant and total strike attempts/landings; takedown attempts/landings; significant head/body/leg attempts/landings; and significant distance/clinch/ground attempts/landings. The fight record contains result, method, finish round, finish clock, scheduled rounds, weight class and title status.

The separate `fighter_round_position` surface is valuable but easy to overstate. The repository's own audit determined that archived UFC/FightMetric position-time fields are predominantly **whole-minute floor buckets**, not exact seconds. UFC EDGE therefore stores them as quantized intervals and explicitly says the lower/upper bounds are bounds rather than observed exact duration. Generic `control_sec`, by contrast, is exact to the second but does not say that those seconds were mount, back control, half guard, clinch or even universally “ground.”

That yields the following state audit.

| Potential simulator state | UFC EDGE status | What UFC EDGE actually knows | Critical limitation |
|---|---|---|---|
| Age at target fight | **AVAILABLE_AND_REPRODUCIBLE** | DOB + target date with PIT semantics | Missing DOB remains missing |
| Height | **AVAILABLE_AND_REPRODUCIBLE** | Governed physical profile | Some historical/source missingness |
| Reach | **AVAILABLE_BUT_SPARSE** | Governed reach plus matchup difference | Historical missingness was important enough to cause the now-corrected M1 contamination issue; missingness cannot become predictive hindsight |
| Weight class | **AVAILABLE_AND_REPRODUCIBLE** | Bout context | None material |
| Title status | **AVAILABLE_AND_REPRODUCIBLE** | Bout context | None material |
| Scheduled rounds | **AVAILABLE_AND_REPRODUCIBLE** | Bout context | Historical rules still matter to elapsed-time derivations |
| Stance | **TEMPORALLY_UNSAFE** / **PRESENT_ONLY_AS_DERIVED_PROXY** | Canonical/profile evidence exists | F00/F01 intentionally keeps stance `PROXY_ONLY`; a current stance/profile observation cannot silently be treated as historical truth |
| Prior UFC experience | **AVAILABLE_AND_REPRODUCIBLE** | Strict-prior canonical fight count | Zero canonical history does not prove a true MMA debut |
| Full MMA career experience | **AVAILABLE_BUT_SPARSE** | UFC plus acquired UFC/Bellator/ONE cross-promotion snapshot | Regional/worldwide career history is incomplete; no reliable “complete MMA debut” flag |
| Layoff | **AVAILABLE_AND_REPRODUCIBLE** | Difference from latest strict-prior known fight | Depends on completeness of known fight history |
| Significant strike attempts/landed | **AVAILABLE_AND_REPRODUCIBLE** | Fighter × round counts | No intra-round order/timestamps |
| Total strike attempts/landed | **AVAILABLE_AND_REPRODUCIBLE** | Fighter × round counts | No intra-round order/timestamps |
| Head/body/leg distribution | **AVAILABLE_AND_REPRODUCIBLE** | Significant strike attempt/land splits | Distribution, not event sequence |
| Distance/clinch/ground strike distribution | **AVAILABLE_AND_REPRODUCIBLE** at aggregate grain | Significant-strike contextual splits | Strike-context counts are not time spent in the context |
| Knockdowns | **AVAILABLE_AND_REPRODUCIBLE** | Count by fighter/round | Exact knockdown clock/order unavailable |
| Strike pace | **PRESENT_ONLY_AS_DERIVED_PROXY** | Historical rates such as landed-per-minute | A rate does not observe burstiness, tempo changes or exchange sequence |
| Strike accuracy/efficiency | **PRESENT_ONLY_AS_DERIVED_PROXY** | Attempt/landed ratios with governed shrinkage | Summary skill, not state |
| Defensive/vulnerability metrics | **PRESENT_ONLY_AS_DERIVED_PROXY** | Opponent attempts/landed, KD vulnerability etc. | Derived matchup tendency |
| Individual strike weapon/type | **NOT_AVAILABLE** | — | Punch/kick/knee/elbow sequence absent from current reproducible backbone |
| Strike power/impact | **NOT_AVAILABLE** | — | “Significant” ≠ physical impact measurement |
| Takedown attempts/landed | **AVAILABLE_AND_REPRODUCIBLE** | Fighter × round counts | No exact clock or entry state |
| Takedown pressure/conversion | **PRESENT_ONLY_AS_DERIVED_PROXY** | Historical/shrunk rates | Not an observed live pressure state |
| Generic control | **AVAILABLE_AND_REPRODUCIBLE** | Exact control seconds at round grain | Does not encode exact position or transition order |
| Submission attempts | **AVAILABLE_AND_REPRODUCIBLE** | Fighter × round count | Attempt type and clock generally absent |
| Reversals | **AVAILABLE_AND_REPRODUCIBLE** | Fighter × round count | Sequence/context absent |
| Stand-ups | **AVAILABLE_BUT_SPARSE** | Richer archived/provider evidence | Not a universal clean free historical action stream |
| Ground-strike activity | **AVAILABLE_BUT_COARSE** | Ground significant-strike counts | Does not establish top/bottom, position or duration |
| Standing / distance duration | **AVAILABLE_BUT_COARSE** | Legacy FightMetric whole-minute occupancy bounds | Not exact seconds; not chronological |
| Clinch duration | **AVAILABLE_BUT_COARSE** | Legacy positional bucket | Not an exact interval sequence |
| Guard / half / side / mount / back exposure | **AVAILABLE_BUT_COARSE** | Legacy whole-minute positional/control buckets | No exact duration or transition times |
| Top/bottom/controller at a moment | **NOT_AVAILABLE** | — | Aggregate fighter-side buckets cannot reconstruct instantaneous topology |
| Position transitions | **NOT_AVAILABLE** | — | No ordered historical transition stream |
| KO win/loss history | **PRESENT_ONLY_AS_DERIVED_PROXY** | Method history and KD/strike history | Useful risk tendency, not current damage state |
| Submission win/loss history | **PRESENT_ONLY_AS_DERIVED_PROXY** | Method history + grappling history | Same |
| Decision history | **PRESENT_ONLY_AS_DERIVED_PROXY** | Outcomes | Same |
| Early/late finish profile | **PRESENT_ONLY_AS_DERIVED_PROXY** | Finish round/clock history | Strongly conditioned by opposition and fight survival |
| Durability | **PRESENT_ONLY_AS_DERIVED_PROXY** | KD/KO loss and strike-vulnerability history | No biological durability measurement |
| Round number | **AVAILABLE_AND_REPRODUCIBLE** | Actual fighter-round grain | — |
| Finish round | **AVAILABLE_AND_REPRODUCIBLE** | Bout result | — |
| Finish round clock | **AVAILABLE_AND_REPRODUCIBLE** | Bout result | — |
| Total elapsed fight time | **PRESENT_ONLY_AS_DERIVED_PROXY** | Derivable from finish round/time plus ruleset | Must use historical round-rule semantics rather than blindly assuming modern five-minute rounds |
| Round-level statistical path | **AVAILABLE_AND_REPRODUCIBLE** | Yes | **This is the highest clean longitudinal resolution already possessed** |
| Timestamped interval/action path | **NOT_AVAILABLE** | — | Core Level-2/3 blocker |
| Damage | **NOT_AVAILABLE** as observed state | KD/strikes can proxy | Latent |
| Fatigue | **NOT_AVAILABLE** as observed state | Later-round pace can proxy | Latent |
| Tactical adaptation / momentum | **NOT_AVAILABLE** | — | Latent |

The feature contract reaches the same conclusion independently. UFC EDGE marks distance/standing as approximately available, wrestling entry and knockdown/damage proxies as available now, but ground/top control and escape/reversal simulator states as data-required; clinch is proxy-only; exact positional duration is a named simulator blocker.

The F02 replay layer is especially important because it prevents a false sense of readiness. F02 explicitly states that it does **not** infer top, ground, back control, clinch, transitions or exact positional duration from generic control, strike-location information, takedown timing or coarse FightMetric buckets. That is exactly the conservative rule a simulator audit should preserve.

### Method-of-victory terrain

UFC EDGE is already building useful MOV-adjacent structure even though it has not implemented the simulator requested here. Its governed validation bucket uses four rich pre-fight concepts—knockdown creation rate and significant-strike flow for striking pressure, plus submission-attempt rate and takedown pressure for grappling pressure—and converts them to frozen population percentiles. In the recorded 5,729-row validation population, 4,618 rows were MOV-environment assignable and 1,111 were explicitly unassignable because required rich data were missing. The contract also says outcomes/predictions were unavailable at that Stage-A construction point, so this should be understood as **validation terrain**, not an already-trained MOV model.

That surface is very useful for a future round simulator: it provides point-in-time priors for *how* a matchup tends to generate finish pressure without pretending to know intra-round action order.

## External source inventory and one-off dataset findings

The external search confirms the repository's suspicion: **the unusually rich UFC action/state data that would change the simulator's fidelity does exist in some form, but the best examples are commercial, manually logged, historically uncertain, or one-off research access—not a clean public reproducible UFC event stream.**

The main sources are below. “Reproducible for future fights” here means UFC EDGE could legitimately collect the same variable family for newly occurring fights under the stated access model—not merely that an old CSV still exists.

| Source / direct link | What it contains and granularity | Historical coverage verified in this audit | Access / update status | Reproducible for future UFC events? | Audit classification |
|---|---|---|---|---|---|
| [UFCStats](http://ufcstats.com/) / [Greco1899 scraper](https://github.com/Greco1899/scrape_ufc_stats) | Events, bouts, fighter data and detailed aggregate/round statistics; no atomic chronology. Greco's public scraper can rerun a full historical scrape and incremental refreshes; its README reports an automated daily update path. | Broad UFC history; exact rich-stat completeness varies by era | Public site + public GPL-3.0 scraper | **Yes**, operationally, subject to source/site stability and permissible access | `REPRODUCIBLE_PIPELINE` |
| UFC EDGE's archived official FightMetric/UFC `fight_stat` snapshot; historical FightMetric lineage documented by [UFC](https://www.ufc.com/news/ufc-offer-fighter-rankings) | Rich aggregate FightMetric fields including the legacy position-time family; repo audit has 57,382 raw rows and 8,005 overlapping FightMetric IDs, with positional times primarily quantized minute buckets rather than seconds. FightMetric was UFC's official stats provider. | Large historical snapshot, but not every UFC bout and not equivalent fidelity in every era | Snapshot physically preserved by UFC EDGE | **No guarantee** that the same legacy surface will continue for future fights | `STATIC_HISTORICAL_DATASET_ONLY` for the legacy rich fields |
| ESPN MMA / [FightCenter](https://www.espn.com/mma/fightcenter) | Fight/result statistics and public presentation of KD, strikes, target splits, control, TD, submissions and scorecards; UFC EDGE's acquired ESPN snapshot additionally found sparse structural plays and positional advances. Current FightCenter still publishes rich fight aggregates. | UFC EDGE snapshot covers 1993–2026, 911 UFC events / 9,412 competitions | Public-facing, but the underlying Core API is not a contractual public developer API | Collection appears possible, but dependency is **temporally unsafe** | Supplemental, not a simulator transition source |
| [FightGeek PRECISION](https://fightgeek.co/precision/) / [help](https://fightgeek.co/help/) | Post-bout slow-motion video logging with entries timestamped to source video; FightGeek advertises 288+ statistics, advanced combat reporting and source-video verification. PRECISION is currently managed by FightGeek data specialists rather than an open download. | Exact commercial archive size unknown. Independent research confirms a supplied sequential archive containing UFC bouts in the 2007–2022 period. | Managed commercial service | Potentially **yes**, if licensed and lawful source video is available; historical archive entitlement is unresolved | `COMMERCIAL_ACCESS_ONLY` |
| 2025 research project [“Analysing UFC play by play data”](https://rstudio-pubs-static.s3.amazonaws.com/1288698_cd551de2166f4fad9bd154f8853b9e62.html) | Researcher was supplied FightGeek `Precision_Data...` play-by-play files and analyzed sequential data/Markov transitions. UFC fights in the supplied material run from Nov. 23, 2007 to July 30, 2022; 487 UFC bouts remained only **after** the researcher further restricted the data to judge decisions, so 487 is not the full source archive size. | Demonstrated historical UFC sequential sample, 2007–2022 | Raw FightGeek CSVs were not found as a legitimate public download | **No** as an independent public production pipeline | Researcher's copy: `STATIC_HISTORICAL_DATASET_ONLY`; underlying provider: `COMMERCIAL_ACCESS_ONLY` |
| [FightGeek SPEED](https://fightgeek.co/speed/) / [pricing](https://fightgeek.co/speed-pricing/) | Human-operated live or retroactive logging of a smaller combat event vocabulary; FightGeek says MMA live collection requires multiple loggers, historical reports can be retained and an API plan exists. | Only data UFC EDGE itself logs or separately licenses; a SPEED subscription does not establish entitlement to PRECISION's historic UFC archive | Commercial subscription / trial | **Yes for future collection**, with human operation and lawful footage; not a free historical backfill | `REPRODUCIBLE_PIPELINE` conditionally, but not a historical solution |
| [Sportradar UFC Fight Stats](https://docs.sportradar.com/ufc/stream-endpoints-websocket/fight-stats) | Authenticated UFC WebSocket with sequence numbers, current round clock, fight and round stats, exact-looking TIP strings for distance, clinch, standing, ground, guard, half guard, side, mount, back, etc., plus submissions, reversals, standups and TD attempts/landings. | Public docs prove current live capability; they do **not** prove multi-year historical packet backfill | API-token / commercial access. IMG ARENA was acquired by Sportradar in Nov. 2025, and its rights portfolio is now under Sportradar. | **Yes prospectively if licensed**; historical archive availability unresolved | `COMMERCIAL_ACCESS_ONLY` |
| [Sportradar PFL Fight Details / Actions](https://docs.sportradar.com/pfl/stream-endpoints-websocket) | PFL product publicly documents <1-second event markers and detailed timestamped actions: TD attempts/landings, submissions, reversals, knockdowns, strikes and explicit DISTANCE/CLINCH position events. | PFL, not UFC | Commercial | Yes for the documented PFL product | For an equivalent **UFC** action endpoint: `UNVERIFIED_EXISTENCE` |
| [MMA Fighter Detection Dataset](https://data.mendeley.com/datasets/c456bnk8bm/1) and [Pose Dataset v2](https://data.mendeley.com/datasets/c456bnk8bm/2) | Roughly 5.1k stand-up UFC images from 20 fights; fighter bounding boxes and, in v2, 17-keypoint pose annotations. Ground and cage-clinch cases are intentionally excluded. License is CC BY-NC-SA 4.0. | 20 fights, stand-up frames only | Public research dataset | No—the dataset does not automatically label new UFC fights | `RESEARCH_ONLY_NOT_SCALABLE` / `STATIC_HISTORICAL_DATASET_ONLY` |
| [ViCoS Brazilian Jiu-Jitsu Positions Dataset](https://www2.vicos.si/resources/jiujitsu/) | 120,279 labeled BJJ images covering standing, TD, guard, half guard, side, mount, back, turtle and controller direction; approximately 30fps source sequences, manually position-labeled. | Six BJJ sparring sequences, **not UFC** | Public research, CC BY-NC-SA 4.0 | Not a UFC data pipeline | `RESEARCH_ONLY_NOT_SCALABLE` for UFC simulation |
| [UFC Fight Pass](https://www.ufc.com/faq-ufctv-ufcfightpass) / UFC video archive | UFC says its on-demand library contains every fight in UFC history. That makes video a theoretically very rich historical observation source. | UFC historical video archive | Consumer subscription/content service; availability can be territorial | **Not as an automated data-mining pipeline without separate rights** | Video source exists, but data extraction is `COMMERCIAL_ACCESS_ONLY` / rights-gated |
| [UFC Terms of Use](https://www.ufc.com/news/terms-use) | Not a statistical dataset, but critical to feasibility: UFC's published terms limit site materials to personal/noncommercial use, prohibit unauthorized copying/downloading/distribution and restrict access to authorized playback methods/automated systems. | Current access/legal constraint | Public terms | Automated archival mining should not be assumed permitted | Licensing blocker for a large historical CV program |

Two points from that table are particularly consequential.

First, **FightGeek PRECISION is the strongest evidence that the user's suspected “rich but perhaps one-off” UFC dataset really existed.** The independent 2025 analysis did not merely infer play-by-play from UFCStats—it loaded FightGeek-supplied sequential files and worked on UFC history from roughly 2007–2022. FightGeek's own documentation explains why that data is unusually rich: PRECISION is a retroactive video-scrubbing and logging workflow with source-video timestamps, currently operated as a managed service.

But the conclusion is not “problem solved.” The exact researcher files are not a public reproducible UFC feed. We did not verify a legitimate public download of them, a complete archive size, a UFC EDGE license, or a contractual guarantee that the provider will supply the same historic and future UFC coverage. **It is evidence of existence, not evidence of production availability.**

Second, **Sportradar's UFC feed materially changes phase-duration feasibility but does not, from currently public UFC documentation, solve atomic historical transitions.** The UFC-specific public docs verify rich Time-In-Position fields, round stats and grappling counts. They also expose `startPosition`, but the documentation describes this as a sequence position used to reconnect/replay the current fight stream—not evidence that clients can query a decade of old UFC live packets.

The public PFL documentation goes farther and exposes true Fight Actions / Fight Details. It would be unsafe to project that PFL entitlement onto UFC merely because the products share a vendor.

### The one-off / experimental findings

The audit therefore classifies the suspiciously rich sources as follows:

| Rich source | Finding |
|---|---|
| FightGeek researcher's Precision CSVs | **`STATIC_HISTORICAL_DATASET_ONLY`** from UFC EDGE's perspective. Demonstrated to exist, but raw researcher files are not a verified legitimate public source. |
| FightGeek PRECISION service | **`COMMERCIAL_ACCESS_ONLY`**. Potentially scalable forward because the managed service still exists, but it is manual/managed video annotation rather than a freely reproducible official UFC event feed. |
| FightGeek SPEED | **`REPRODUCIBLE_PIPELINE` conditionally for newly logged fights**, but requires operators and does not itself provide the old PRECISION archive. |
| Sportradar UFC Fight Stats | **`COMMERCIAL_ACCESS_ONLY`**. Strong future reproducibility if contracted; long-run historical backfill still unverified publicly. |
| UFC atomic “Fight Actions” feed equivalent to PFL | **`UNVERIFIED_EXISTENCE`** in the public UFC documentation examined. |
| Legacy official FightMetric positional-time data in UFC EDGE | **`STATIC_HISTORICAL_DATASET_ONLY`** for those legacy rich fields; valuable, but quantized and not enough to infer chronology. |
| Small UFC CV detection/pose releases | **`RESEARCH_ONLY_NOT_SCALABLE`** for simulator training; stand-up images, not complete temporal MMA action annotation. |
| BJJ position research dataset | **`RESEARCH_ONLY_NOT_SCALABLE`** as UFC ground truth; useful research transfer data only. |
| Previously located all-Sherdog-derived historical dataset | **`NO_LONGER_AVAILABLE`** as a defensible core dependency: UFC EDGE's acquisition audit records that the original dataset was deleted and rejects depending on an unverified mirror. |

The strongest possible interpretation of the evidence is thus **“rich UFC sequential data has existed and probably still can be generated under commercial arrangements.”** The evidence does **not** support “a broad, cheap, legal, historically complete, automatically renewable event-level UFC dataset is available to UFC EDGE today.”

## Video and computer-vision feasibility

Video is the obvious theoretical escape hatch, and it is also where it would be easiest to overpromise.

The good news is that the fundamental primitives are no longer science fiction. A 2025 UFC-specific public dataset contains 5,106 annotated stand-up images from 20 professional UFC fights, and its 2026 pose extension has approximately 5,109 images with 17-point skeleton annotations. The associated project reports high held-out detection/pose metrics in that narrow dataset and explicitly describes pose estimation as a foundation for future action recognition.

Ground-position recognition is also technically demonstrable in adjacent combat sports. The ViCoS BJJ dataset contains more than 120,000 images with labels such as standing, takedown, open/closed/half guard, side control, mount, back and turtle, including which athlete controls several asymmetric positions.

That still leaves a very large gap between “a classifier can recognize a position in curated data” and “UFC EDGE can reconstruct twenty-plus years of UFC action history accurately.”

**Broadcast geometry is the first problem.** UFC broadcasts change cameras, zoom, framing and viewpoint. A model must associate the same fighter through cuts and distinguish a real continuation from a replay. Ground grappling has severe mutual-body occlusion; cage mesh, referee obstruction and entangled limbs make standard keypoint estimates less reliable. The UFC-specific public pose dataset itself deliberately excludes ground grappling and cage-clinch situations—the exact cases UFC EDGE most needs to recover.

**Temporal labeling is the second problem.** Detecting two fighters in an image gives almost none of the missing transition semantics. A useful training corpus must say when a takedown begins and completes, when clinch becomes ground, who has control, when guard becomes half guard or mount, when a submission threat begins and ends, and which displayed broadcast clock corresponds to the action. The ViCoS example needed position-specific human labels even in much simpler three-camera BJJ sparring sequences.

**Action recognition is the third problem.** The desired simulator does not only need “someone threw a strike.” It needs the acting fighter, result, target/type if used, state before and after, and preferably action ordering around TDs/KDs/submissions. The current public UFC detection/pose project describes downstream action recognition as the next layer rather than presenting a completed comprehensive UFC action corpus.

**Rights are the fourth—and potentially decisive—problem.** UFC says Fight Pass carries every UFC fight historically, so a huge video corpus exists in a consumer-access sense. But UFC's published terms restrict site/video material to authorized/personal use and explicitly prohibit unauthorized copying/downloading/distribution and certain automated access. A production-scale computer-vision program should therefore require explicit data/video rights rather than treating a consumer Fight Pass subscription as permission to download thousands of fights into a machine-learning archive.

A realistic CV path would therefore look like this:

1. **Licensed footage first**, not “scrape Fight Pass.”
2. A few dozen deliberately chosen bouts spanning camera eras, fighter skin tones/body types, cage locations, southpaw/orthodox matchups, wrestling-heavy fights and ground-heavy fights.
3. Human annotation of a small, explicit state vocabulary.
4. Blind event-level validation against trained annotators.
5. Only if transition-time accuracy is genuinely adequate should historical scaling be considered.

The purpose of such a pilot would be to answer whether the missing data can be *created reliably*, not to assume that modern pose models already solve the problem.

Even successful CV would still leave damage and fatigue largely latent. Video may yield proxies—visible knockdowns, pace, posture, strike mechanics—but it does not produce validated joules of impact, neurological impairment, cardiovascular reserve or tissue injury. Any continuous `damage=0.71` or `fatigue=0.46` simulator state would therefore remain a model construct rather than an observed historical variable.

**Conclusion on video:** technically promising, but **not currently the practical foundation for UFC EDGE's first simulator**. The annotation burden, historical broadcast heterogeneity, ground-game difficulty and licensing problem make it a high-cost fallback behind licensed structured data.

## Simulator levels and the closest defensible architecture

The best way to expose the boundary is to separate what can be simulated from what can be empirically estimated.

| Level | Required data | UFC EDGE current data | External reproducible help | Feasibility | Why |
|---|---|---|---|---|---|
| **Level 0 — Pre-fight Monte Carlo** | Frozen pre-fight winner/MOV/round probabilities | Strong PIT F01/F02 fighter states and corrected winner-model foundation | None required | **FEASIBLE** | Can draw outcomes from estimated joint/conditional probabilities. It is probabilistic outcome simulation, not a fight-process model. |
| **Level 1 — Round-state simulator** | Round-grain output, grappling, KD, finish and survival observations; fighter/context priors | **Yes:** strikes, KD, TD, SUB attempts, reversals, generic control, finish round/time, contextual features, round histories | Public UFCStats/Greco can continue the same broad family | **FEASIBLE — highest defensible level** | Historical observations exist at exactly the resolution of the proposed state updates. |
| **Level 2 — Coarse within-round states** | Standing/clinch/ground/control entry/exit or sufficiently dense intervals from which transition hazards can be estimated | Occupancy buckets + round totals, but no ordering | Sportradar could add much better exact TIP prospectively; FightGeek could potentially provide historical sequential data commercially | **PARTIALLY FEASIBLE only under explicit assumptions; not defensible as empirically learned today** | Occupancy does not identify transition count/order. One 120-second ground spell and twelve 10-second spells can produce the same 120-second aggregate. |
| **Level 3 — Event-level simulator** | Timestamped strike/TD/KD/submission/position events over broad historical UFC coverage | No | FightGeek is access-gated; PFL atomic feed exists but UFC equivalent is publicly unverified; CV would have to create data | **INFEASIBLE from reproducible historical data currently available to the project** | No broad, legitimate, reproducible historical UFC atomic event stream has been verified. |
| **Level 4 — High-fidelity digital fight model** | Level 3 plus credible damage, fatigue, tactics, injury and detailed biomechanical/positional state | No | No audited source solves these latent states | **INFEASIBLE** | Several required variables are not merely inaccessible—they are not directly observed by ordinary fight statistics at all. |

### Why Level 2 cannot be quietly inferred from existing aggregates

Suppose a fighter has in one round:

- four takedown attempts;
- two completed takedowns;
- 120 seconds of control;
- six ground significant strikes;
- one submission attempt.

Those totals are compatible with many mutually different fights:

- one early takedown followed by nearly uninterrupted top control;
- repeated takedowns with immediate escapes;
- one long clinch-control period followed by short ground spells;
- a late scramble-heavy sequence with multiple control changes.

The aggregate likelihood can constrain *how much* wrestling occurred. It cannot tell UFC EDGE the empirical transition probability from standing → clinch → takedown → half guard → side control, because the intermediate sequence was never observed. Generating one such sequence is allowed as a simulation assumption; estimating it and calling it historically learned is not.

That is why Holmes et al.'s Markov approach is highly relevant but should be interpreted carefully. It proves that an MMA contest can be represented with a mechanistic Markov model whose transition parameters are derived from aggregate fighter skill estimates. UFC EDGE can absolutely learn from that approach. It should not use it as evidence that historical atomic transitions are present in UFCStats.

### Highest defensible simulator level

**Level 1 — round-state simulator.**

This can be a genuine stochastic fight-process simulator rather than a disguised classifier, because the state advances through units for which UFC EDGE actually has longitudinal historical observations.

The closest architecture to the original vision is:

**Pre-fight fighter state.** Initialize both fighters from F01/F02 point-in-time histories: strike flow and efficiency; target/environment mix; knockdown creation/vulnerability; takedown pressure and conversion; submission-attempt rate; reversal behavior; control; finish-method history; early-finish profile; physical/context features; prior UFC experience; layoff; scheduled rounds; title status; weight class and other governed inputs. UFC EDGE already has these families or their governed primitives.

**Round emission layer.** For each surviving round, jointly simulate observable round quantities such as significant strike attempts/landings, knockdowns, takedown attempts/landings, submission attempts, reversals and generic control seconds. The distributions should be matchup-conditioned and hierarchical, not independent Poisson dice for every stat.

**Competing finish hazards.** At the round—or finer finish-clock survival grid where defensible—estimate competing hazards for KO/TKO, submission and other terminal outcomes. Fighter identities, simulated current-round output, prior-round output and the pre-fight skill state can affect the hazards.

**Round progression.** The state may carry cumulative observed/simulated summaries: strikes absorbed, KD events, wrestling workload, control workload and prior-round pace. These are valid *history variables*. It should not rename them “brain damage,” “cardio remaining” or “confidence.”

**Pace/fatigue component.** Learn a round-index and prior-output effect on later output, properly conditioning on the fact that only fights surviving to later rounds can contribute later-round observations. This produces a **fatigue/pace-decay proxy**, not physiological fatigue.

**Decision trajectory.** Until judge-by-round scorecards are completely normalized and validated, the safest approach is a conditional decision-winner model based on simulated performance histories plus pre-fight state. Once official judge-round data are canonicalized, a separate round-scoring layer could be validated without pretending aggregate strike totals completely determine a 10-point-must score.

**Finish timing.** Historical final finish clocks are real observations. A conditional within-finishing-round time distribution can therefore be learned without simulating fake strike-by-strike timestamps. That means Level 1 can still produce round-of-finish and approximate time-of-finish distributions.

**Joint output.** Repeated simulated fights can yield coherent:

\[
P(\text{fighter wins}),
\quad
P(\text{KO/TKO}),
\quad
P(\text{submission}),
\quad
P(\text{decision}),
\]

\[
P(\text{inside distance}),
\quad
P(\text{goes distance}),
\quad
P(\text{finish in round }r),
\quad
P(T_{\text{finish}}\le t)
\]

and, crucially, joint quantities such as fighter × MOV × round.

That recovers a large part of the original *probability-product* vision without inventing a fake second-by-second martial-arts movie.

### What Level 1 must not claim

It cannot validly output paths such as:

> “At 3:42 of Round 2, Fighter A enters the clinch, completes a single-leg at 3:31, passes to half guard at 3:18 and takes the back at 2:44”

unless a future sequential source actually supports calibrating those transitions.

It can validly output something more like:

> “Round 2 produces elevated wrestling pressure, two simulated takedown attempts, significant control exposure, one submission threat and an increased submission finish hazard.”

The second is genuinely consistent with the historical resolution available.

## Acquisition priorities, unsupported ideas, and the higher-value alternative

Additional data should only be pursued where it changes the simulator level or materially repairs an important output. On that basis, the acquisition order is narrower than “collect everything.”

| Priority | Candidate acquisition | Exact information gained | Historical coverage / reproducibility | Licensing/cost risk | Capability actually unlocked |
|---|---|---|---|---|---|
| **Highest** | **FightGeek PRECISION archive access audit + licensed sample** | Timestamped actions linked to source video; potentially strike sequence, stance/position, combinations and other advanced combat events | Independent evidence shows UFC sequential data from 2007–2022, but full archive size and future UFC terms are unknown. | Commercial, managed annotation; rights and pricing unresolved | **Only audited lead with a plausible path to broad historical Level 2/possibly Level 3** |
| **High** | **Sportradar UFC Fight Stats historical-backfill entitlement** | Exact TIP-style duration for distance, clinch, ground and detailed ground control; standups/reversals/subs/TDs and live round state | Future reproducibility appears strong under contract; public docs do not prove old-event backfill | Commercial/API-token dependency | Greatly strengthens phase-duration modeling and Level-2 occupancy, though it still may not provide transition order |
| **High but narrower** | **Official judge-round scorecard normalization already within UFC EDGE's data track** | Judge × fighter × round scores | Official scorecard acquisition is already part of repo source work; quality/identity parsing still required | Much lower conceptual risk than video CV | Better decision-state and round-winner modeling; does not advance positional simulator level |
| **Fallback only** | **Licensed UFC video + small human/CV annotation pilot** | Exact fight phase, position and action timestamps if annotation succeeds | Historical coverage could in principle be very broad because the video archive exists, but data would have to be newly generated | **Very high** annotation/QA burden plus explicit video-rights requirement | Potential Level 3, but only after evidence that accuracy and cost are acceptable |

A purchase of commercial data should **not** be recommended merely because it is rich. The key gate is whether it comes with both **historical backfill and future reproducibility**. A beautiful 2010–2022 archive that cannot be continued produces a research experiment, not a production simulator.

### What UFC EDGE should not attempt

Several attractive ideas fail the hard-truth test.

**Do not convert generic control time into exact ground time.** The repository already correctly refuses this. Control is a real statistic; “ground,” “clinch,” “mount” and “back” are different state concepts.

**Do not turn legacy FightMetric 0–5 positional buckets into exact seconds.** The source audit found the bucket behavior empirically and UFC EDGE's contract correctly stores interval bounds instead.

**Do not treat significant ground-strike counts as ground duration.** Six ground strikes could occur in seconds or across a long control sequence.

**Do not estimate an “empirical” standing↔clinch↔ground transition matrix from unordered round totals.** Such a matrix is underidentified without stronger chronological observations.

**Do not invent top/bottom position from takedown success alone.** Completed TD does not tell UFC EDGE the entire subsequent positional sequence.

**Do not make literal damage or stamina variables from ordinary statistics.** `damage += landed_head_strikes * 0.02` may be a game mechanic, but it is not a historically measured damage model unless independently validated.

**Do not silently backfill current mutable fighter profile fields.** UFC EDGE's data and feature contracts are specifically designed to avoid treating acquisition-time stance, gym, rank, listed weight or other mutable profile facts as historical truth.

**Do not treat the FightGeek research sample as a public database.** It proves rich data existed; it does not establish UFC EDGE's redistribution or production rights.

**Do not assume the PFL Fight Actions product is available for UFC.** The rich action endpoint is directly documented for PFL; the current UFC documentation examined here verifies Fight Stats, not the same atomic Fight Actions contract.

**Do not depend on a vanished Sherdog-derived bulk dataset or an unverified mirror.** UFC EDGE has already documented that free-source dead end.

**Do not mine Fight Pass at scale under the assumption that subscription access equals machine-learning/data-mining rights.** UFC's published terms make that assumption unsafe.

**Do not market a Holmes-style synthetic one-second trajectory as observed historical fight dynamics.** The academic approach is valid modeling; its generated path and an empirically observed transition process are different claims.

### The alternative that probably captures most of the practical value

There is a strong possibility that **UFC EDGE does not need Level 2 or Level 3 to obtain most of the useful probabilistic output originally expected from the simulator.**

The practical core can be expressed as a **hierarchical competing-risks survival system** rather than a cinematic event simulator:

\[
\lambda_{\mathrm{KO},A}(t),\;
\lambda_{\mathrm{KO},B}(t),\;
\lambda_{\mathrm{SUB},A}(t),\;
\lambda_{\mathrm{SUB},B}(t)
\]

plus survival to decision and a conditional decision-winner model.

The hazards can depend on point-in-time fighter skill state, matchup interactions, weight class, scheduled rounds, round index and accumulated simulated round outputs. Those ingredients line up closely with data UFC EDGE actually possesses: knockdowns, significant-strike flow, TD pressure, submission-attempt pressure, reversals, control and finish timing.

Such a family could consist of:

| Model component | Historical support | Products derived |
|---|---|---|
| Winner model | Already has corrected frozen M1 foundation | Moneyline probability |
| KO/TKO competing hazard | KD creation/vulnerability, sig-strike pace/efficiency, KO histories, finish clocks | KO/TKO, fighter-by-KO, KO round |
| Submission competing hazard | TD pressure/conversion, sub attempts, reversals, control, submission histories | Submission, fighter-by-sub, submission round |
| Overall finish/survival hazard | Finish round/time + above skills/context | Inside distance, goes distance, finish round/time |
| Decision-conditional winner | Pre-fight state + simulated/expected round performance; eventually judge scores | Fighter by decision |
| Round-output models | Actual fighter-round counts | Round-specific pace and finish conditioning |
| Joint Monte Carlo wrapper | All calibrated components | Coherent winner × MOV × round/time distribution |

This architecture captures the simulator's most valuable statistical outputs while avoiding the single hardest unavailable asset: an empirical intra-round state-transition history.

It also has a conceptual advantage. If UFC EDGE predicts `P(A wins by submission in Round 2)`, the model can be evaluated directly against observed outcomes. A detailed synthetic path such as “clinch → double-leg → half guard → back → rear-naked choke” has far fewer historical examples at any precise state combination and is much harder to calibrate. More state is not automatically more predictive information.

This is an inference from the audited data—not a claim that betting profitability has been established. Architecture should remain market-blind, consistent with the user's constraint not to use odds or ROI to choose it.

## Final hard-truth test and recommended next action

**Is the original high-fidelity simulator vision realistically achievable for UFC EDGE with data that can be obtained and reproduced today?**

**No—not in its original high-fidelity form.**

The blocking issue is not that UFC EDGE lacks ordinary MMA statistics. It has a strong round-statistical backbone and unusually careful temporal governance. The blocking issue is that the original vision requires **chronology and topology**:

- when phase changes happened;
- how many times they happened;
- what position existed before/after each change;
- who controlled it;
- when each TD/KD/submission/strike occurred;
- how those events affected the next state.

The freely reproducible historical backbone does not contain those observations. Coarse occupancy and round totals are many-to-one summaries of innumerable possible action paths. They cannot uniquely recover the lost sequence.

Furthermore, the top end of the vision—physical damage, fatigue, injury and tactical psychology—would remain latent even if UFC EDGE acquired perfect timestamped action logs.

**What is the closest defensible simulator UFC EDGE can actually build?**

A **hierarchical round-state competing-risk simulator**:

1. initialize fighters with frozen point-in-time skill/context states;
2. simulate one round of observable output at a time;
3. simulate competing KO/TKO and submission hazards;
4. carry prior simulated output forward as explicit history;
5. model later-round pace decay as a learned proxy, not literal fatigue;
6. if no finish occurs, resolve the decision through a separately calibrated decision model;
7. sample finish round and finish time from observed historical timing distributions;
8. aggregate thousands of draws into coherent winner/MOV/distance/round/time probabilities.

This is materially more than Level 0 Monte Carlo. The simulated state actually evolves through the fight. But it evolves at the resolution historical data supports: **rounds, not invented second-by-second positional transitions.**

### Simulator-level final determination

| Level | Final audit disposition |
|---|---|
| Level 0 — pre-fight Monte Carlo | **FEASIBLE NOW** |
| Level 1 — round-state simulator | **FEASIBLE NOW FROM REPRODUCIBLE HISTORICAL DATA** |
| Level 2 — coarse within-round state | **PARTIALLY FEASIBLE ONLY WITH STRUCTURAL ASSUMPTIONS; NOT CURRENTLY DEFENSIBLE AS EMPIRICALLY LEARNED** |
| Level 3 — event-level simulator | **INFEASIBLE WITHOUT ACCESS-GATED OR NEWLY CREATED SEQUENTIAL DATA** |
| Level 4 — high-fidelity digital fight model | **INFEASIBLE WITH CURRENTLY OBTAINABLE OBSERVATIONAL DATA** |

**Final verdict: `ROUND_STATE_SIMULATOR_FEASIBLE`**

That is the highest level UFC EDGE can honestly claim **without fabricating unavailable information**.

A Holmes-style coarse Markov simulator can be retained as a research comparator because published work establishes that aggregate skills can parameterize such a system. But UFC EDGE should label the within-round transition assumptions explicitly and should not make that architecture the canonical simulator until empirical sequential data exists.

**Recommended next action — one bounded research task:**
Create `SEQUENTIAL_UFC_DATA_ENTITLEMENT_AND_SAMPLE_AUDIT_V1`: obtain, without integrating or purchasing blindly, written schema/coverage/licensing answers and a representative historical sample from **FightGeek PRECISION and Sportradar UFC**. The gate should ask only five questions: whether historical UFC data can be licensed; exact years/bout counts; whether action/position records are timestamped and ordered; whether the same schema can be collected for future UFC events; and whether UFC EDGE may retain/model from the data. If neither provider can demonstrate **broad historical sequential coverage + forward reproducibility + usable modeling rights**, formally freeze Level 1 as the simulator ceiling and proceed with the round-state/competing-risk architecture rather than continuing to search for a dataset that may not be operationally obtainable.
