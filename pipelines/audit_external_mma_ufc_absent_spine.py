#!/usr/bin/env python3
"""Audit canonical fighter participation behind trusted UFC source pairs absent from canonical fights.

DATA PHASE ONLY. Read-only diagnostic; no canonical rows are written.
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
RAW = ROOT / "data/raw/kaggle_pro_mma_fights/v1/pro_mma_fights.csv"
XWALK = ROOT / "data/derived/identity/external_mma_canonical_crosswalk_candidate.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
FIGHTERS = ROOT / "data/canonical/v0/fighters.csv"
OUT = ROOT / "provenance/audits/external_mma_ufc_absent_spine_latest.json"
UFC_ORG = "Ultimate Fighting Championship (UFC)"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return " ".join(re.findall(r"[a-z0-9]+", value))


def main() -> int:
    raw = read_csv(RAW)
    xwalk = read_csv(XWALK)
    fights = read_csv(FIGHTS)
    fighters = read_csv(FIGHTERS)

    trusted: dict[str, str] = {}
    for r in xwalk:
        if (r.get("review_status") or "").strip() != "trusted":
            continue
        url = (r.get("external_fighter_url") or "").strip()
        fid = (r.get("canonical_fighter_id") or "").strip()
        if url and fid:
            previous = trusted.get(url)
            if previous and previous != fid:
                raise SystemExit(f"trusted URL collision: {url}")
            trusted[url] = fid

    fighter_by_id = {(r.get("fighter_id") or "").strip(): r for r in fighters}
    fighters_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in fighters:
        fighters_by_name[norm((r.get("canonical_name") or "").strip())].append(r)

    participation = Counter()
    canonical_pairs: set[tuple[str, str]] = set()
    for fight in fights:
        a = (fight.get("fighter_a_id") or "").strip()
        b = (fight.get("fighter_b_id") or "").strip()
        if a:
            participation[a] += 1
        if b:
            participation[b] += 1
        if a and b and a != b:
            canonical_pairs.add(tuple(sorted((a, b))))

    involved = Counter()
    source_names: dict[str, set[str]] = defaultdict(set)
    absent_rows = 0
    for r in raw:
        if (r.get("organisation") or "").strip() != UFC_ORG:
            continue
        u1 = (r.get("fighter1_url") or "").strip()
        u2 = (r.get("fighter2_url") or "").strip()
        f1, f2 = trusted.get(u1, ""), trusted.get(u2, "")
        if not f1 or not f2 or f1 == f2:
            continue
        if tuple(sorted((f1, f2))) in canonical_pairs:
            continue
        absent_rows += 1
        for side, fid in ((1, f1), (2, f2)):
            involved[fid] += 1
            source_names[fid].add((r.get(f"fighter{side}_name") or "").strip())

    rows = []
    for fid, absent_count in involved.most_common():
        fr = fighter_by_id.get(fid, {})
        name = (fr.get("canonical_name") or "").strip()
        same_name = fighters_by_name.get(norm(name), []) if name else []
        rows.append({
            "canonical_fighter_id": fid,
            "canonical_name": name,
            "canonical_dob": (fr.get("dob") or "").strip(),
            "source_names_in_absent_rows": sorted(source_names[fid]),
            "absent_pair_row_count": absent_count,
            "canonical_fight_participation_count": participation[fid],
            "same_normalized_canonical_name_count": len(same_name),
            "same_normalized_canonical_name_rows": [
                {
                    "fighter_id": (x.get("fighter_id") or "").strip(),
                    "canonical_name": (x.get("canonical_name") or "").strip(),
                    "dob": (x.get("dob") or "").strip(),
                    "canonical_fight_participation_count": participation[(x.get("fighter_id") or "").strip()],
                }
                for x in same_name
            ],
        })

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "absent_ufc_pair_rows": absent_rows,
        "involved_canonical_fighters": len(rows),
        "involved_with_zero_canonical_fight_participation": sum(r["canonical_fight_participation_count"] == 0 for r in rows),
        "involved_with_same_name_canonical_duplicates": sum(r["same_normalized_canonical_name_count"] > 1 for r in rows),
        "rows": rows,
        "decision": {
            "canonical_rows_written": False,
            "required_next": "If trusted fighters have zero canonical participation while a same-name canonical identity carries fights, repair identity before promotion. Otherwise treat remaining absent pairs as candidate canonical fight omissions requiring source-level verification."
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "absent_ufc_pair_rows": absent_rows,
        "involved_canonical_fighters": len(rows),
        "zero_participation": payload["involved_with_zero_canonical_fight_participation"],
        "same_name_duplicates": payload["involved_with_same_name_canonical_duplicates"],
        "top": rows[:10],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
