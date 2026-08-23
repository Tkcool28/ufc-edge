# H01 GitHub Handicap Request Bridge

H01 is operational infrastructure around the existing H00 read-only packet generator. It does not change H00 packet schema `0.1.0`, canonical DATA, cutoff rules, identity rules, missingness, source precedence, features, modeling, odds, or research.

## Request API

A GitHub issue is the request API. H01 recognizes an issue when its title begins with `[H00 REQUEST]` or it carries the `h00-request` label. The workflow then validates the issue body with the strict `h00-request-0.1` JSON schema.

Supported kinds are exactly `fighter`, `matchup`, and `card`.

```json
{
  "schema": "h00-request-0.1",
  "kind": "matchup",
  "fighter_a": "Max Holloway",
  "fighter_b": "Dustin Poirier",
  "cutoff": "2026-08-23T03:30:00Z"
}
```

Fighter requests require only `fighter`; card requests require only `event_id`. Every request requires `cutoff`. Unknown fields are rejected. Control fields such as commands, scripts, output paths, refs, branches, repository paths, or environment injection are rejected.

## Authorization and trust

H01 v0.1 authorizes the repository owner only. The issue actor must match the repository owner's login. This deliberately narrower policy satisfies the initial owner/maintainer requirement without trying to infer mutable collaborator permissions inside untrusted issue processing. Maintainer expansion can be added later through an explicit allowlist or repository-permission lookup.

Issue data never selects code or Git refs. Issue-triggered execution checks out trusted `main`. Request values are parsed with Python's JSON parser and passed directly into H00 Python APIs; they are never evaluated, executed, or interpolated into a shell command.

## Processing

1. Check out trusted `main` and record its SHA.
2. Read the GitHub event JSON.
3. Verify repository, marker, actor, schema, kind, exact fields, and ISO cutoff.
4. Instantiate H00 `CanonicalStore`, preserving its frozen manifest/hash validation.
5. Invoke the existing H00 builders directly.
6. Write H00 output only to runner temporary storage.
7. Validate generated files are non-empty and JSON outputs parse as objects.
8. Build `h01-response-0.1` response metadata including source SHA, cutoff, request hash, packet schema, file SHA-256 values, and sizes.
9. Publish only the self-contained request directory to `handicap-cache`.
10. Comment a machine-readable result on the request issue.

## Cache layout

The `handicap-cache` branch is generated disposable state and must never be merged into `main`.

```text
handicap/
└── requests/
    └── <issue_number>/
        ├── request.json
        ├── manifest.json
        ├── fighter.json
        ├── matchup.json
        ├── matchup.md
        └── card/
            ├── manifest.json
            └── fight_*.{json,md}
```

Only the files relevant to the request kind are present.

## Retention and history

The current cache snapshot keeps the 20 highest completed request issue numbers. Pruning only considers numeric directories directly beneath `handicap/requests/` and refuses paths outside that root.

Publishing uses `git write-tree` plus `git commit-tree` to create a new root snapshot commit and force-updates only `refs/heads/handicap-cache`. The cache branch therefore does not accumulate an unbounded parent history. No normal development branch and never `main` is force-updated.

## Idempotency

Each canonical request has a stable SHA-256 request hash. Reprocessing the same issue replaces that issue's single request directory rather than creating another directory or uncontrolled history. The response records both the request hash and source `main` SHA.

## Concurrency

The issue-processing job uses the fixed concurrency group `h01-handicap-cache-writer` with `cancel-in-progress: false`. Cache writers are serialized and earlier valid requests are not cancelled by later ones.

## Permissions

Default workflow permission is `contents: read`. The issue-processing job alone elevates to:

- `contents: write` for the dedicated cache branch;
- `issues: write` for completion/failure comments and lifecycle labels.

No additional token scope is requested.

## Issue lifecycle

Success comments begin with `H00_REQUEST_COMPLETE`, include the source SHA, cache branch, cache commit, cutoff, manifest path, and generated packet paths, add `h00-complete`, remove `h00-request` when present, and close the issue.

Failure comments begin with `H00_REQUEST_FAILED`, contain a bounded safe category/message and source SHA, add `h00-failed`, and leave the issue open. Python tracebacks and secrets are not posted.

## Rollout constraint

GitHub `issues` workflows are loaded from the repository's default branch. Therefore a true issue-trigger acceptance test is not valid while H01 exists only on this feature branch.

Phase A is feature-branch review and pull-request CI (`compileall`, focused H01 tests, and a diff gate proving H00/DATA paths were not modified). `workflow_dispatch` is also available as a safe test-only entry point with no caller-controlled packet inputs.

Phase B begins only after review and merge to `main`: create the real Holloway/Poirier request issue at cutoff `2026-08-23T03:30:00Z`, verify issue→Action→H00→`handicap-cache`→comment, and retrieve the generated packet through the GitHub connector.
