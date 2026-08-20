# UFC Edge — Acquisition Closeout — 2026-08-20

Status time: 2026-08-20 closeout (America/Denver)

Purpose: preserve the evidence-based stopping point for the free-source acquisition sweep. A workflow trigger or green job is not counted as ingestion; a source is considered landed only when the immutable raw snapshot and its manifest are committed and auditable.

## Closeout rules applied

- No source was promoted based only on a trigger commit.
- A successful snapshot pipeline is expected to create a timestamped raw directory and therefore a bot commit containing the raw snapshot/manifest.
- Absence of that result commit means the source remains unverified/not landed.
- No new long-running acquisition work was started during closeout.

## Pipeline status

### Official UFC FightMetric rich stats

Trigger commit: `af42270858ba782e7dfde58e0fcd45dcbb4c7c11` (`Run official UFC FightMetric rich-stat snapshot`)
Workflow timeout: 120 minutes.
Expected result commit: `Snapshot official UFC FightMetric rich stats [skip ci]`.
Expected raw namespace: `data/raw/ufc_fightmetric_official/<snapshot_id>/` with `manifest.json`.

Closeout result: **UNVERIFIED / RESULT NOT YET COMMITTED**.

At closeout, repository history contained no expected bot snapshot commit after the trigger. The trigger was still within the workflow's 120-minute maximum runtime, so this is not classified as a confirmed failure. Schema-level probes remain valid evidence that `fight_stat` and `fight_roundboard` are readable, but historical coverage is still unknown until a real raw manifest lands and is inspected.

### General UFC.com athlete/event/fight snapshot

Pipeline commit: `bb6c5cd84f557f6667ec7dac78b51184d24935b1` (`Add UFC.com additive raw snapshot pipeline`). The workflow is path-triggered by that pipeline/workflow change.
Workflow timeout: 45 minutes.
Expected result commit: `Snapshot free UFC.com additive data [skip ci]`.
Expected raw namespace: `data/raw/ufc_com/<snapshot_id>/` with `manifest.json`.

Closeout result: **NOT LANDED**.

More than the 45-minute workflow window had elapsed and repository history contained no expected snapshot commit. Because each successful run creates a new timestamped immutable snapshot, a successful no-change outcome is not expected here. The exact in-job failure/timeout reason was not available through the current connector view, so do not invent one. Tomorrow's first action should be to inspect the workflow job/log and determine whether this was a request failure, pagination/runtime issue, or another pipeline exception before retrying.

### ESPN MMA additive snapshot

Trigger commit: `a18df5f3fccaff4432c2102140c34418eed481bc` (`Run ESPN MMA additive snapshot on main`).
Workflow timeout: 120 minutes.
Expected result commit: `Snapshot free ESPN MMA additive data [skip ci]`.
Expected raw namespace: `data/raw/espn_mma/<snapshot_id>/` with `manifest.json`.

Closeout result: **UNVERIFIED / RESULT NOT YET COMMITTED**.

At closeout, repository history contained no expected bot snapshot commit. The run was still within its 120-minute maximum runtime, so this is not classified as a confirmed failure. ESPN remains additive/QA only until a committed manifest demonstrates event-year coverage, endpoint success rates, officials/stat vocabularies, and sparse-play behavior.

### Official UFC weigh-in / scorecard article snapshot

Trigger commit: `4c56dc22233867f39f789c3ca230009224fdbed7` (`Run official UFC weigh-in and scorecard snapshot`).
Workflow timeout: 45 minutes.
Expected result commit: `Snapshot official UFC weigh-ins and scorecards [skip ci]`.
Expected raw namespace: `data/raw/ufc_official_articles/<snapshot_id>/`.

Closeout result: **FAILED TO LAND / BLOCKED PATH**.

More than the 45-minute workflow window had elapsed and repository history contained no expected snapshot commit. Independent bounded probing already established that `/jsonapi/node/article` returns HTTP 403 even though the resource is advertised by the UFC JSON:API catalog. Therefore this JSON:API article-collection route remains blocked and must not be treated as acquired. Do not bypass the 403; use a legitimate UFC index/search/sitemap route or another permitted source later.

## Sources that did land earlier in the sweep

The following already have immutable bot commits and remain raw/QA according to their source-specific rules:

- UFC JSON:API resource catalog: `bf07a7cbeccd3eb2dcb7467990df598cceefe33d`.
- Partial UFC JSON:API surface evidence / samples: `3b7f220cd1fc7d678e72922385e0e560858e5745` and `ba1217618dbb0b4019a2751002f5d4ed0e2b60a3`.
- UFC-DataLab scorecard snapshot: `dc3b95322f40233c5edd2ed9830611fcce11bd6d` (RAW / QA REQUIRED because sample OCR/match associations are unreliable).
- Historical UFC rankings snapshot: `d9649f9100defca126284f4a3a261fdb2ac16cda` (RAW / provenance + identity QA required; strict historical as-of usage only).
- CC0 cross-promotion MMA history: `3d8c8a5e82cf91f7245462f1c4b25bc28dcfe58a` (RAW / identity + dedup QA required).

## Tomorrow's resume point

1. Inspect the final state/logs of the two 120-minute jobs before triggering anything again.
2. If a FightMetric snapshot commit appeared after this closeout, inspect its `manifest.json` first and quantify field/TIP non-null coverage by era before promoting it.
3. If an ESPN snapshot appeared, inspect its manifest coverage/failure counts before use.
4. Diagnose the UFC.com general snapshot failure from the workflow log before retrying.
5. Treat official article JSON:API collection as blocked; pursue only a clean alternate enumeration route.
6. After acquisition statuses are stable, proceed to canonical data-contract design before feature engineering.
