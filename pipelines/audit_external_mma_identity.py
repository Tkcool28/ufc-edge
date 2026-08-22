#!/usr/bin/env python3
"""Audit identity coverage for the CC0 UFC/Bellator/ONE Sherdog-derived snapshot.

The companion profile URL is the stable source identity. Profiles are reconciled to UFC
Edge canonical fighters using exact normalized display names and DOB corroboration where
available. Source slash dates are interpreted only according to the separately audited
DMY semantic; no fuzzy matching or career-total matching is used.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGHTERS = ROOT / "data/raw/kaggle_pro_mma_fighters/v1/pro_mma_fighters.csv"
FIGHTS = ROOT / "data/raw/kaggle_pro_mma_fights/v1/pro_mma_fights.csv"
CANONICAL = ROOT / "data/canonical/v0/fighters.csv"
DATE_AUDIT = ROOT / "provenance/audits/external_mma_date_semantics_latest.json"
OUT = ROOT / "data/derived/identity/external_mma_canonical_crosswalk_candidate.csv"
AUDIT = ROOT / "provenance/audits/external_mma_identity_latest.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def parse_source_date(value: str) -> str | None:
    """Parse the external source using the independently promoted DMY slash semantic."""
    text = (value or "").strip()
    if not text or text.lower() in {"na", "n/a", "none", "--"}:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%b %d, %Y", "%B %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else None


def parse_canonical_date(value: str) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def main() -> int:
    date_audit = json.loads(DATE_AUDIT.read_text(encoding="utf-8"))
    promoted = (date_audit.get("decision") or {}).get("promoted_source_slash_date_order")
    if promoted != "DMY":
        raise RuntimeError(f"External source slash-date semantic is not promoted as DMY: {promoted!r}")

    canonical = read_csv(CANONICAL)
    profiles = read_csv(FIGHTERS)
    fights = read_csv(FIGHTS)

    canon_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in canonical:
        canon_by_name[norm(row.get("canonical_name") or "")].append(row)

    crosswalk: list[dict[str, str]] = []
    status_counts = Counter()
    url_status: dict[str, tuple[str, str | None]] = {}
    examples: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in profiles:
        url = (row.get("url") or "").strip()
        name = (row.get("fighter_name") or "").strip()
        nd = norm(name)
        source_dob = parse_source_date(row.get("birth_date") or "")
        candidates = canon_by_name.get(nd, [])
        status = "unmatched_exact_name"
        canonical_id = ""
        match_method = ""
        confidence = ""
        canonical_name = ""
        canonical_dob = ""

        if len(candidates) == 1:
            cand = candidates[0]
            canonical_name = cand.get("canonical_name") or ""
            canonical_dob = parse_canonical_date(cand.get("dob") or "") or ""
            if source_dob and canonical_dob:
                if source_dob == canonical_dob:
                    status = "trusted"
                    match_method = "exact_normalized_name_plus_exact_dob_dmy_source"
                    confidence = "1.0"
                    canonical_id = cand["fighter_id"]
                else:
                    status = "dob_conflict"
                    match_method = "exact_normalized_name_but_dob_conflicts_after_dmy_parse"
            else:
                status = "candidate"
                match_method = "exact_normalized_name_unique_dob_not_jointly_observed"
                confidence = "0.95"
                canonical_id = cand["fighter_id"]
        elif len(candidates) > 1:
            dob_matches = [
                cand for cand in candidates
                if source_dob and parse_canonical_date(cand.get("dob") or "") == source_dob
            ]
            if len(dob_matches) == 1:
                cand = dob_matches[0]
                status = "trusted"
                match_method = "exact_normalized_name_collision_resolved_by_exact_dob_dmy_source"
                confidence = "1.0"
                canonical_id = cand["fighter_id"]
                canonical_name = cand.get("canonical_name") or ""
                canonical_dob = parse_canonical_date(cand.get("dob") or "") or ""
            else:
                status = "ambiguous_exact_name"
                match_method = "exact_normalized_name_multiple_canonical_candidates"

        status_counts[status] += 1
        if url:
            url_status[url] = (status, canonical_id or None)
        out_row = {
            "external_fighter_url": url,
            "external_fighter_name": name,
            "external_birth_date": source_dob or "",
            "canonical_fighter_id": canonical_id,
            "canonical_name": canonical_name,
            "canonical_dob": canonical_dob,
            "match_method": match_method,
            "review_status": status,
            "match_confidence": confidence,
        }
        crosswalk.append(out_row)
        if status not in {"trusted", "candidate"} and len(examples[status]) < 25:
            examples[status].append(out_row)

    fight_status = Counter()
    org_counts = Counter()
    usable_org_counts = Counter()
    overlap_ufc_rows = 0
    for fight in fights:
        u1 = (fight.get("fighter1_url") or "").strip()
        u2 = (fight.get("fighter2_url") or "").strip()
        s1 = url_status.get(u1, ("profile_missing", None))[0]
        s2 = url_status.get(u2, ("profile_missing", None))[0]
        org = (fight.get("organisation") or "").strip() or "UNKNOWN"
        org_counts[org] += 1
        if "ufc" in org.lower() or "ultimate fighting" in org.lower():
            overlap_ufc_rows += 1
        if s1 == "trusted" and s2 == "trusted":
            bucket = "both_trusted"
            usable_org_counts[org] += 1
        elif s1 in {"trusted", "candidate"} and s2 in {"trusted", "candidate"}:
            bucket = "both_resolved_at_least_candidate"
        elif s1 in {"trusted", "candidate"} or s2 in {"trusted", "candidate"}:
            bucket = "one_resolved"
        else:
            bucket = "neither_resolved"
        fight_status[bucket] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "external_fighter_url", "external_fighter_name", "external_birth_date", "canonical_fighter_id",
        "canonical_name", "canonical_dob", "match_method", "review_status", "match_confidence",
    ]
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(crosswalk)

    payload = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "profile_rows": len(profiles),
        "fight_rows": len(fights),
        "profile_status_counts": dict(status_counts),
        "fight_identity_status_counts": dict(fight_status),
        "organisation_counts": dict(org_counts),
        "both_trusted_fight_counts_by_organisation": dict(usable_org_counts),
        "ufc_overlap_rows_require_dedup": overlap_ufc_rows,
        "crosswalk_csv": str(OUT.relative_to(ROOT)),
        "source_date_semantics": {
            "slash_order": "DMY",
            "evidence": str(DATE_AUDIT.relative_to(ROOT)),
            "independent_gate_passed": True,
        },
        "examples": dict(examples),
        "decision": {
            "fuzzy_matching_used": False,
            "career_totals_used_for_identity": False,
            "trusted_rule": "Exact normalized name plus exact DOB under audited DMY source parsing, including DOB resolution of name collisions.",
            "candidate_rule": "Unique exact normalized name when DOB is not jointly observed; not canonical-promoted without further corroboration.",
            "canonical_fight_history_promoted": False,
            "next_gate": "Deduplicate UFC overlap and admit only both-trusted external fights into canonical external-history data; candidate-only identities remain quarantined.",
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "profiles": len(profiles),
        "trusted": status_counts["trusted"],
        "candidate": status_counts["candidate"],
        "dob_conflict": status_counts["dob_conflict"],
        "fights_both_trusted": fight_status["both_trusted"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
