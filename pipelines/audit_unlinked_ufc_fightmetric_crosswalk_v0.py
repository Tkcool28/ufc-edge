#!/usr/bin/env python3
"""Check unlinked official UFC athletes for exact pre-existing FightMetric identity links.

DATA PHASE ONLY. This is a strict stable-ID audit: no display names, fuzzy matching, URL
basename guessing, or new identity links. It asks whether a source-explicit official UFC
athlete fightmetric_id exactly equals an existing trusted fighter source_id elsewhere in
the canonical identity-link ledger.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINKS = ROOT / "data/canonical/v0/source_identity_links.csv"
UNLINKED = ROOT / "data/derived/qa/unlinked_ufc_athlete_identity_v0.csv"
OUT = ROOT / "data/derived/qa/unlinked_ufc_fightmetric_crosswalk_v0.csv"
AUDIT = ROOT / "provenance/audits/unlinked_ufc_fightmetric_crosswalk_v0_latest.json"
FIELDS = [
    "ufc_athlete_uuid", "fightmetric_id", "official_fight_appearances", "disposition",
    "exact_trusted_match_count", "matched_canonical_ids", "matched_source_names", "crosswalk_disposition",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    links = read_csv(LINKS)
    unlinked = read_csv(UNLINKED)
    if len(unlinked) != 1693:
        raise RuntimeError(f"unlinked audit cardinality drift {len(unlinked)}")

    trusted_by_source_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    fighter_link_source_counts = Counter()
    for row in links:
        if row.get("entity_type") != "fighter" or row.get("review_status") != "trusted":
            continue
        source_id = (row.get("source_id") or "").strip()
        source_name = (row.get("source_name") or "").strip()
        if not source_id:
            continue
        fighter_link_source_counts[source_name or "<missing>"] += 1
        # Exclude the official UFC athlete UUID source itself; we are seeking another stable bridge.
        if source_name == "ufc_com":
            continue
        trusted_by_source_id[source_id].append(row)

    rows = []
    dispositions = Counter()
    fight_history_rows = 0
    fight_history_with_fm = 0
    unique_exact = 0
    ambiguous_exact = 0
    for row in unlinked:
        fm = (row.get("fightmetric_id") or "").strip()
        fight_history = row.get("disposition") == "unlinked_with_official_fight_history"
        if fight_history:
            fight_history_rows += 1
            fight_history_with_fm += bool(fm)

        matches = trusted_by_source_id.get(fm, []) if fm else []
        canonical_ids = sorted({m.get("canonical_id") or "" for m in matches if m.get("canonical_id")})
        source_names = sorted({m.get("source_name") or "" for m in matches if m.get("source_name")})
        if not fm:
            disposition = "no_source_explicit_fightmetric_id"
        elif not matches:
            disposition = "no_exact_trusted_source_id_match"
        elif len(canonical_ids) == 1:
            disposition = "unique_exact_trusted_source_id_match_candidate"
            unique_exact += 1
        else:
            disposition = "ambiguous_exact_trusted_source_id_match"
            ambiguous_exact += 1
        dispositions[disposition] += 1
        rows.append({
            "ufc_athlete_uuid": row.get("ufc_athlete_uuid") or "",
            "fightmetric_id": fm,
            "official_fight_appearances": row.get("official_fight_appearances") or "",
            "disposition": row.get("disposition") or "",
            "exact_trusted_match_count": len(matches),
            "matched_canonical_ids": ";".join(canonical_ids),
            "matched_source_names": ";".join(source_names),
            "crosswalk_disposition": disposition,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    fight_history_candidates = sum(
        r["crosswalk_disposition"] == "unique_exact_trusted_source_id_match_candidate"
        and r["disposition"] == "unlinked_with_official_fight_history"
        for r in rows
    )
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "unlinked_rows": len(unlinked),
        "fight_history_unlinked_rows": fight_history_rows,
        "fight_history_unlinked_with_fightmetric_id": fight_history_with_fm,
        "fighter_identity_link_source_counts": dict(fighter_link_source_counts),
        "crosswalk_disposition_counts": dict(dispositions),
        "unique_exact_trusted_source_id_match_candidates": unique_exact,
        "ambiguous_exact_trusted_source_id_matches": ambiguous_exact,
        "fight_history_unique_exact_match_candidates": fight_history_candidates,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "display_name_matching_used": False,
            "url_token_or_basename_matching_used": False,
            "canonical_identity_links_written": False,
            "exact_source_id_equality_only": True,
            "safe_to_accept_remaining_fight_identity_gap": fight_history_candidates == 0 and ambiguous_exact == 0,
            "required_next": (
                "Review unique exact stable-ID candidates before final gap disposition."
                if fight_history_candidates or ambiguous_exact
                else "No pre-existing exact trusted FightMetric source-id bridge resolves the fight-participating unlinked nodes; document them as an accepted identity coverage gap."
            ),
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
