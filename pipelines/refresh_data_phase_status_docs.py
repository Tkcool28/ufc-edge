#!/usr/bin/env python3
"""Refresh current DATA-phase status blocks while preserving historical source notes."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/canonical/v0/manifest.json"
SCORECARDS = ROOT / "provenance/audits/official_scorecards_final_disposition_v0.json"
ATHLETES = ROOT / "provenance/audits/unlinked_ufc_athlete_identity_v0_latest.json"
FMCROSS = ROOT / "provenance/audits/unlinked_ufc_fightmetric_crosswalk_v0_latest.json"
DOCS = [
    ROOT / "provenance/data_source_manifest.md",
    ROOT / "provenance/free_source_sweep_2026-08-20.md",
]
START = "<!-- DATA_PHASE_CURRENT_STATUS_START -->"
END = "<!-- DATA_PHASE_CURRENT_STATUS_END -->"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def replace_block(text: str, block: str) -> str:
    if START in text and END in text:
        before = text.split(START, 1)[0].rstrip()
        after = text.split(END, 1)[1].lstrip("\n")
        return before + "\n\n" + block + "\n\n" + after
    lines = text.splitlines()
    if not lines:
        return block + "\n"
    # Preserve the title as the first line, then place current truth before historical notes.
    return lines[0] + "\n\n" + block + "\n\n" + "\n".join(lines[1:]).lstrip("\n") + "\n"


def current_block(manifest, scorecards, athletes, fmcross) -> str:
    counts = manifest["counts"]
    local_date = datetime.now(ZoneInfo("America/Denver")).date().isoformat()
    score_sample = scorecards.get("strongest_failed_gate", scorecards.get("physical_grid_three_round_sample", {}))
    # The final disposition artifact may vary in nesting; retain verified headline numbers explicitly.
    return f"""{START}
## Current DATA-phase status — {local_date}

This block is the current operational truth. Material below it is retained as historical acquisition/research context and may describe earlier pending states.

### Canonical v0 now materialized

| Family | Final DATA-phase disposition | Current evidence |
|---|---|---|
| Core fighter/event/fight + classic round history | **CANONICAL** | `{counts['fighters']:,}` fighters; `{counts['events']:,}` events; `{counts['fights']:,}` fights; `{counts['fighter_round_stats']:,}` fighter-round rows. |
| Official FightMetric positional/TIP buckets | **CANONICAL** | `{counts['fighter_round_position']:,}` eligible fighter-round position rows; quantized bucket semantics only. |
| Historical rankings | **CANONICAL** | `{counts['rankings']:,}` dated ranking observations; future/nearest-future joins remain forbidden. |
| Official UFC athlete profiles | **CANONICAL point-in-time subset** | `{counts['fighter_profile_snapshots']:,}` dated profile snapshots; never historical backfill. |
| Cross-promotion fight history | **CANONICAL clean subset** | External MMA inserted only after stable identity/dedup gates; lower-precedence UFC-labelled rows never repair UFC history. |
| Official fight-specific weigh-ins | **CANONICAL** | `{counts['weigh_ins']:,}` scale-weight observations; non-explicit attempt/miss/penalty semantics remain null. |
| Official judge round scorecards | **RAW_QA_ONLY — accepted gap** | Verified official pages/images are archived, but strict extraction failed; **0 canonical judge-round rows**. |
| ESPN MMA | **RAW_QA_ONLY / additive QA** | Retained for officials, redundancy and future additive work; not allowed to overwrite canonical higher-precedence values. |
| UFC-DataLab OCR scorecards | **RAW_QA_ONLY** | Known OCR/fighter-pair association errors; never score authority. |
| Access-gated sequential/live sources | **DEFERRED_ACCESS_GATED** | FightGeek / IMG / Sportradar remain future licensed/access tracks, not DATA-phase blockers. |

### Accepted gaps carried forward explicitly

- **Official scorecards:** the strongest physical-grid three-round sample had 15 eligible cards / 270 expected score cells, only 82 strict accepted cells, 0/15 complete 18-cell cards, and 0 complete nine-pair cards. The source remains raw/QA-only; no inferred scores were written.
- **Official athlete identity coverage:** `{athletes['unlinked_official_athlete_nodes']:,}` of `{athletes['official_athlete_nodes']:,}` official athlete nodes are not trusted canonical identities. `{athletes['meaningful_fight_identity_gap_nodes']:,}` of those appear in official fight resources and are therefore a real identity-coverage gap rather than profile-only clutter.
- **FightMetric stable-ID follow-up:** `{fmcross['fight_history_unlinked_with_fightmetric_id']:,}` of the `{fmcross['fight_history_unlinked_rows']:,}` fight-participating unlinked athletes carry a source-explicit FightMetric ID, but the exact trusted-source-ID audit found **0** unique match candidates and **0** ambiguous exact matches. No name or URL-token matching was used.
- **UFC historical spine coverage:** lower-precedence external-MMA audits identified UFC-labelled trusted-pair rows absent from the canonical UFC spine, including ordinary win/loss bouts. They remain documented QA gaps; external data was deliberately not used to repair higher-precedence UFC history.

### Phase rule

No further free-source hunting, OCR threshold loosening, or identity guessing is authorized merely to make DATA appear complete. Remaining gaps above are explicit and durable. Feature engineering may use only canonical tables/semantics and must respect point-in-time and missingness rules.
{END}"""


def main() -> int:
    manifest = load(MANIFEST)
    scorecards = load(SCORECARDS)
    athletes = load(ATHLETES)
    fmcross = load(FMCROSS)
    block = current_block(manifest, scorecards, athletes, fmcross)
    for path in DOCS:
        if not path.exists():
            raise RuntimeError(f"missing status doc {path}")
        original = path.read_text(encoding="utf-8")
        path.write_text(replace_block(original, block), encoding="utf-8")
        print(f"refreshed {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
