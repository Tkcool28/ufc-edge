# Feature migrations

This directory is the durable evolution ledger for the shared feature system.

Machine authority: `feature_migrations.json`.

Every semantic or methodology migration must record:

- from/to contract version;
- date and reason;
- affected durable feature IDs;
- added/removed/renamed names;
- semantic and methodology changes;
- new DATA/canonical dependencies;
- replay requirement;
- compatibility/old-artifact interpretation;
- PR and commit reference.

Do not rely on pull-request discussion alone to explain historical feature meaning.
