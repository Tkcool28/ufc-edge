# Offline reproduction

Use repository commit `b8194cd37831348bd856900cba134d05ff21e430`. Copy these pinned files to this directory’s `inputs/`:

- `data/canonical/v0/events.csv`
- `data/canonical/v0/fights.csv`
- `data/canonical/v0/fighters.csv`
- `data/canonical/v0/fighter_round_stats.csv`
- `data/canonical/v0/fighter_round_position.csv`
- `data/canonical/v0/source_identity_links.csv`
- `docs/data_audits/ground_opportunity_competing_pathways_v1/EVIDENCE_MANIFEST.json`

Run `python reproduce_sample_audit.py`. Python standard library only; no network, credentials, models or ingestion. Compare generated CSVs and `VALIDATION.json` with the evidence manifest. Public-source discovery is time-sensitive and separately recorded in `SOURCE_CHECKS.json`; the offline script reproduces comparisons, not provider availability. Candidate blanks are unobserved. Sportradar facts were transcribed from its public documentation example, not acquired from a historical authenticated endpoint.
