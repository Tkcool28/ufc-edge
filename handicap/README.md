# H00 Handicap Access

`handicap/` is UFC Edge's disposable, read-only handicapping access/cache layer.

It exists so a GitHub-only ChatGPT session can retrieve one compact fighter or matchup packet instead of opening and joining the large canonical CSVs during live fight analysis.

## Authority

Nothing under `handicap/` is canonical DATA, provenance authority, a feature artifact, or a model artifact.

Authoritative inputs remain:

- `data/canonical/v0/manifest.json`
- the canonical tables beneath `data/canonical/v0/`
- `schemas/canonical_data_contract_v0.json`
- `schemas/source_field_map_v0.json`
- `schemas/source_precedence_v0.json`
- `provenance/data_phase_freeze_v0.json`
- `data/canonical/v0/field_provenance.csv`

H00 validates the frozen `0.4.0-draft` contract and the freeze-bound contract/source-map/precedence/manifest hashes before reading DATA.

## Packet schema

H00 packet schema: `0.1.0`

Generated packet metadata records:

- generator version and Git commit;
- generation timestamp;
- explicit information cutoff;
- DATA contract version;
- canonical manifest path/hash;
- DATA freeze path/hash;
- canonical fighter/event identities;
- semantic and missing-data warnings.

Substantive packet content is deterministic for the same frozen DATA, generator version/commit, fighter IDs, and cutoff. `generated_at_utc` is intentionally excluded from the substantive content hash.

## Directory structure

```text
handicap/
├── README.md
├── H00_VALIDATION.md                  # acceptance report when generated
└── v0/
    ├── index/
    │   └── fighters.json
    ├── fighters/
    │   └── <canonical_fighter_id>.json
    ├── matchups/
    │   ├── <fighter_a_id>__<fighter_b_id>.json
    │   └── <fighter_a_id>__<fighter_b_id>.md
    └── cards/
        └── <canonical_event_id>/
            ├── manifest.json
            ├── fight_01_<A>_vs_<B>.json
            └── fight_01_<A>_vs_<B>.md
```

The fighter index is small enough to generate globally. Fighter, matchup, and card packets are generated on demand; H00 does not eagerly materialize thousands of fighter dossiers.

## Identity rules

Resolution order is:

1. exact canonical fighter ID;
2. exact canonical display name;
3. exact trusted alias already carried by canonical trusted identity-link data;
4. normalized text only when it maps uniquely to an already trusted canonical identity.

Ambiguous normalized names return candidates/fail closed. Unknown names fail clearly. H00 never performs fuzzy identity guessing and never promotes a display-name-only candidate to trusted identity.

## Cutoff semantics

Every fighter, matchup, and card build requires an explicit information cutoff.

- Fights require a canonical event strictly before the cutoff. If only a date is known and it equals the cutoff date, H00 fails closed and excludes it.
- Target/post-fight result and round data are exposed only through eligible pre-cutoff fights.
- Rankings must be strictly before the cutoff.
- Fighter profile snapshots may appear only at or before their `observed_at_utc`.
- A dated weigh-in must be on a strictly prior calendar date because canonical v0 does not provide an observation time-of-day.
- An undated weigh-in is included only after its associated fight is itself safely pre-cutoff.
- FightMetric round `0` is never emitted as a real round.

## Missingness and time semantics

Missing remains missing. Empty canonical values become JSON `null`; absent positional observations remain absent arrays, never synthetic zeros.

Classic `control_sec` is exact canonical control-time evidence. FightMetric positional/TIP evidence remains separate and is displayed as the canonical whole-minute bucket plus explicit lower/upper bounds. H00 never turns those coarse buckets into fake exact seconds.

## What packets contain

Where canonical v0 has eligible data, dossiers/matchups expose:

- canonical fighter identity, DOB, height, reach, stance, nickname, and age as of cutoff;
- trusted canonical source identity links and stable URLs;
- complete pre-cutoff observed fight history, including Bellator/ONE rows already canonicalized;
- event, opponent, promotion, result, method, finish round/time, weight class, and all other canonical fight fields;
- every canonical classic fighter-round field for fighter and opponent;
- head/body/leg and distance/clinch/ground significant-strike splits;
- knockdowns, takedowns, submissions, reversals, exact control seconds;
- all available canonical positional/TIP fields for fighter and opponent;
- all time-safe fight-specific weigh-in observations;
- complete pre-cutoff dated ranking history;
- all safe point-in-time official fighter profile snapshots;
- transparent descriptive summaries with observed/missing denominators;
- direct prior meetings in matchup packets;
- an opponent index with canonical IDs and fight context;
- canonical/provenance pointers for audit.

## What H00 intentionally does not contain

H00 does not include:

- predictive features or model-ready feature vectors;
- KO/power, durability, cardio/fade, style, similarity, or opponent-adjusted scores;
- expected win/method probabilities;
- Monte Carlo outputs;
- sportsbook odds or market/value data;
- scraped current-web data;
- canonical judge-round scores (DATA v0 has none);
- inferred missed-weight/catchweight/penalty/attempt semantics;
- copied raw archives or full canonical CSVs;
- embedded images.

Detailed primitive-level provenance is not duplicated into every packet. Packet row keys/source references point back to `data/canonical/v0/field_provenance.csv`.

## Generate

From repository root:

```bash
python tools/handicap/build_fighter_index.py
```

```bash
python tools/handicap/build_fighter_dossier.py \
  --fighter-id <canonical_fighter_id> \
  --cutoff <ISO_DATE_OR_TIMESTAMP>
```

A uniquely resolvable name may be used explicitly:

```bash
python tools/handicap/build_fighter_dossier.py \
  --fighter "Max Holloway" \
  --cutoff 2026-08-23T03:30:00Z
```

```bash
python tools/handicap/build_matchup_packet.py \
  --fighter-a <id-or-unambiguous-name> \
  --fighter-b <id-or-unambiguous-name> \
  --cutoff <ISO_DATE_OR_TIMESTAMP>
```

```bash
python tools/handicap/build_card_packets.py \
  --event-id <canonical_event_id> \
  --cutoff <ISO_DATE_OR_TIMESTAMP>
```

All normal CLI output is constrained beneath `handicap/`. `--output-root` exists only as an explicit alternate destination for tests/isolated validation.

## Cleanup

Generated cache contents are safe to delete. Keep the README:

```bash
rm -rf handicap/v0/index handicap/v0/fighters handicap/v0/matchups handicap/v0/cards
rm -f handicap/H00_VALIDATION.md
```

Regenerate the index:

```bash
python tools/handicap/build_fighter_index.py
```

Regenerate a fighter or matchup with the same explicit cutoff using the commands above.

Do **not** delete or alter canonical DATA, schemas, or provenance to clean H00.

## Separation from feature/model work

H00 organizes frozen canonical evidence for access. It does not interpret that evidence into predictors. Future feature/model fields must not be silently added to packet schema `0.1.0`; that requires an explicit H00 packet-schema/version decision.
