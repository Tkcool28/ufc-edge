#!/usr/bin/env python3
"""Audit official UFC athlete UUIDs not linked to canonical fighters.

DATA PHASE ONLY. No display-name matching is used. Evidence comes only from stable UFC
athlete UUIDs, official UFC fight red/blue UUID relationships, source-explicit athlete
identifiers, and the already-trusted canonical source_identity_links. The purpose is to
separate profile-only/legacy records from unlinked athlete nodes that actually participate
in official UFC fight resources. No identity links are written by this audit.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATH_MAN = ROOT / "data/raw/ufc_com_resources/athletes/20260820T194553Z/manifest.json"
FIGHT_MAN = ROOT / "data/raw/ufc_com_resources/fights/20260821T055500Z/manifest.json"
LINKS = ROOT / "data/canonical/v0/source_identity_links.csv"
OUT = ROOT / "data/derived/qa/unlinked_ufc_athlete_identity_v0.csv"
AUDIT = ROOT / "provenance/audits/unlinked_ufc_athlete_identity_v0_latest.json"
FIELDS = [
    "ufc_athlete_uuid", "title", "fightmetric_id", "old_id", "old_url",
    "athlete_status_text", "official_fight_appearances", "distinct_official_fights",
    "disposition",
]


def rcsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rel_id(obj, name: str) -> str:
    data = ((obj.get("relationships") or {}).get(name) or {}).get("data")
    if isinstance(data, dict):
        return str(data.get("id") or "")
    return ""


def status_map(page) -> dict[str, str]:
    result = {}
    for item in page.get("included") or []:
        xid = str(item.get("id") or "")
        attrs = item.get("attributes") or {}
        label = str(attrs.get("name") or attrs.get("title") or attrs.get("label") or "").strip()
        if xid and label:
            result[xid] = label
    return result


def main() -> int:
    aman = load(ATH_MAN)
    fman = load(FIGHT_MAN)
    links = rcsv(LINKS)

    athlete_pages = [ROOT / x["path"] for x in aman.get("files") or []]
    fight_pages = []
    for cm_rel in fman.get("chunk_manifests") or []:
        cm = load(ROOT / cm_rel)
        fight_pages.extend(ROOT / x["path"] for x in cm.get("files") or [])
    if len(athlete_pages) != 84 or len(fight_pages) != 242:
        raise RuntimeError(f"raw page count drift athletes={len(athlete_pages)} fights={len(fight_pages)}")

    # Match the canonical profile builder's already-audited identity-link contract exactly.
    trusted_athlete = {
        row["source_id"]: row["canonical_id"]
        for row in links
        if row.get("source_name") == "ufc_com"
        and row.get("entity_type") == "fighter"
        and row.get("review_status") == "trusted"
        and row.get("source_id")
        and row.get("canonical_id")
    }
    if len(trusted_athlete) != 2468:
        raise RuntimeError(f"trusted official athlete link cardinality drift {len(trusted_athlete)}")

    athletes = {}
    for path in athlete_pages:
        page = load(path)
        smap = status_map(page)
        for athlete in page.get("data") or []:
            uid = str(athlete.get("id") or "")
            attrs = athlete.get("attributes") or {}
            status_id = rel_id(athlete, "athlete_status")
            if not uid:
                raise RuntimeError(f"athlete without UUID in {path}")
            if uid in athletes:
                raise RuntimeError(f"duplicate athlete UUID {uid}")
            athletes[uid] = {
                "title": str(attrs.get("title") or attrs.get("name") or ""),
                "fightmetric_id": str(attrs.get("fightmetric_id") or ""),
                "old_id": str(attrs.get("old_id") or ""),
                "old_url": str(attrs.get("old_url") or ""),
                "athlete_status_text": smap.get(status_id, ""),
            }
    if len(athletes) != 4161:
        raise RuntimeError(f"athlete cardinality drift {len(athletes)}")

    appearances = Counter()
    fight_sets = defaultdict(set)
    official_fight_rows = 0
    for path in fight_pages:
        page = load(path)
        for fight in page.get("data") or []:
            official_fight_rows += 1
            fight_uid = str(fight.get("id") or "")
            for rel in ("red_corner", "blue_corner"):
                athlete_uid = rel_id(fight, rel)
                if not athlete_uid:
                    continue
                appearances[athlete_uid] += 1
                if fight_uid:
                    fight_sets[athlete_uid].add(fight_uid)
    if official_fight_rows != 12069:
        raise RuntimeError(f"fight resource cardinality drift {official_fight_rows}")

    unlinked = sorted(set(athletes) - set(trusted_athlete))
    if len(unlinked) != 1693:
        raise RuntimeError(f"expected 1693 unlinked official athletes, got {len(unlinked)}")

    rows = []
    dispositions = Counter()
    statuses = Counter()
    with_fightmetric_id = 0
    with_legacy = 0
    for uid in unlinked:
        athlete = athletes[uid]
        app = appearances[uid]
        if app > 0:
            disposition = "unlinked_with_official_fight_history"
        elif athlete["fightmetric_id"]:
            disposition = "profile_only_unlinked_with_fightmetric_id"
        elif athlete["old_id"] or athlete["old_url"]:
            disposition = "profile_only_legacy_identity"
        else:
            disposition = "profile_only_unlinked_no_stable_fight_bridge"
        dispositions[disposition] += 1
        statuses[athlete["athlete_status_text"] or "<missing>"] += 1
        with_fightmetric_id += bool(athlete["fightmetric_id"])
        with_legacy += bool(athlete["old_id"] or athlete["old_url"])
        rows.append({
            "ufc_athlete_uuid": uid,
            **athlete,
            "official_fight_appearances": app,
            "distinct_official_fights": len(fight_sets[uid]),
            "disposition": disposition,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    meaningful = dispositions["unlinked_with_official_fight_history"]
    payload = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "official_athlete_nodes": len(athletes),
        "trusted_official_athlete_links": len(trusted_athlete),
        "unlinked_official_athlete_nodes": len(unlinked),
        "official_fight_resources": official_fight_rows,
        "unlinked_with_fightmetric_id": with_fightmetric_id,
        "unlinked_with_legacy_old_id_or_url": with_legacy,
        "unlinked_status_text_counts": dict(statuses),
        "disposition_counts": dict(dispositions),
        "unlinked_with_any_official_fight_participation": meaningful,
        "meaningful_fight_identity_gap_nodes": meaningful,
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "display_name_matching_used": False,
            "canonical_identity_links_written": False,
            "official_uuid_relationships_are_evidence_only": True,
            "profile_only_unlinked_nodes_can_remain_accepted_gap": True,
            "fight_participating_unlinked_nodes_require_explicit_gap_documentation": meaningful > 0,
            "required_next": "Document fight-participating unlinked nodes as an accepted identity coverage gap unless a stable pre-existing source crosswalk resolves them. Do not create links by name similarity.",
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
