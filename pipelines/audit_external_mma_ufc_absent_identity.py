#!/usr/bin/env python3
"""Audit trusted identity mappings behind UFC-labelled source pairs absent from canonical fights.

DATA PHASE ONLY. No canonical rows are written and no trusted mapping is mutated.
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
OUT = ROOT / "provenance/audits/external_mma_ufc_absent_identity_latest.json"
UFC_ORG = "Ultimate Fighting Championship (UFC)"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).lower()
    return " ".join(re.findall(r"[a-z0-9]+", value))


def main() -> int:
    raw = read_csv(RAW)
    xwalk = read_csv(XWALK)
    fights = read_csv(FIGHTS)

    trusted_rows = [r for r in xwalk if (r.get("review_status") or "").strip() == "trusted"]
    trusted_by_url: dict[str, dict[str, str]] = {}
    for row in trusted_rows:
        url = (row.get("external_fighter_url") or "").strip()
        fid = (row.get("canonical_fighter_id") or "").strip()
        if not url or not fid:
            continue
        if url in trusted_by_url and trusted_by_url[url].get("canonical_fighter_id") != fid:
            raise SystemExit(f"trusted URL collision: {url}")
        trusted_by_url[url] = row

    by_external_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_canonical_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in trusted_rows:
        by_external_name[norm_name(row.get("external_fighter_name") or "")].append(row)
        by_canonical_name[norm_name(row.get("canonical_name") or "")].append(row)

    canonical_pairs: set[tuple[str, str]] = set()
    for fight in fights:
        a = (fight.get("fighter_a_id") or "").strip()
        b = (fight.get("fighter_b_id") or "").strip()
        if a and b and a != b:
            canonical_pairs.add(tuple(sorted((a, b))))

    raw_names_by_url: dict[str, set[str]] = defaultdict(set)
    for row in raw:
        for side in ("1", "2"):
            url = (row.get(f"fighter{side}_url") or "").strip()
            name = (row.get(f"fighter{side}_name") or "").strip()
            if url and name:
                raw_names_by_url[url].add(name)

    absent: list[dict[str, object]] = []
    involved_urls: set[str] = set()
    involved_canonical_ids: Counter[str] = Counter()
    involved_external_names: Counter[str] = Counter()

    for row in raw:
        if (row.get("organisation") or "").strip() != UFC_ORG:
            continue
        url1 = (row.get("fighter1_url") or "").strip()
        url2 = (row.get("fighter2_url") or "").strip()
        map1 = trusted_by_url.get(url1)
        map2 = trusted_by_url.get(url2)
        if not map1 or not map2:
            continue
        id1 = (map1.get("canonical_fighter_id") or "").strip()
        id2 = (map2.get("canonical_fighter_id") or "").strip()
        if not id1 or not id2 or id1 == id2:
            continue
        pair = tuple(sorted((id1, id2)))
        if pair in canonical_pairs:
            continue

        involved_urls.update((url1, url2))
        involved_canonical_ids.update((id1, id2))
        involved_external_names.update(((row.get("fighter1_name") or "").strip(), (row.get("fighter2_name") or "").strip()))

        sides = []
        for side, url, mapping in ((1, url1, map1), (2, url2, map2)):
            ext_name = (mapping.get("external_fighter_name") or "").strip()
            can_name = (mapping.get("canonical_name") or "").strip()
            ext_same = by_external_name.get(norm_name(ext_name), [])
            can_same = by_canonical_name.get(norm_name(can_name), [])
            sides.append({
                "side": side,
                "source_name": (row.get(f"fighter{side}_name") or "").strip(),
                "external_url": url,
                "raw_names_seen_for_url": sorted(raw_names_by_url.get(url, set())),
                "crosswalk_external_name": ext_name,
                "crosswalk_external_birth_date": (mapping.get("external_birth_date") or "").strip(),
                "canonical_fighter_id": (mapping.get("canonical_fighter_id") or "").strip(),
                "canonical_name": can_name,
                "canonical_dob": (mapping.get("canonical_dob") or "").strip(),
                "match_method": (mapping.get("match_method") or "").strip(),
                "match_confidence": (mapping.get("match_confidence") or "").strip(),
                "trusted_same_external_normalized_name_count": len(ext_same),
                "trusted_same_external_normalized_name_mappings": [
                    {
                        "external_url": (r.get("external_fighter_url") or "").strip(),
                        "external_birth_date": (r.get("external_birth_date") or "").strip(),
                        "canonical_fighter_id": (r.get("canonical_fighter_id") or "").strip(),
                        "canonical_name": (r.get("canonical_name") or "").strip(),
                        "canonical_dob": (r.get("canonical_dob") or "").strip(),
                    }
                    for r in ext_same
                ],
                "trusted_same_canonical_normalized_name_count": len(can_same),
                "trusted_same_canonical_normalized_name_mappings": [
                    {
                        "external_url": (r.get("external_fighter_url") or "").strip(),
                        "external_name": (r.get("external_fighter_name") or "").strip(),
                        "external_birth_date": (r.get("external_birth_date") or "").strip(),
                        "canonical_fighter_id": (r.get("canonical_fighter_id") or "").strip(),
                        "canonical_dob": (r.get("canonical_dob") or "").strip(),
                    }
                    for r in can_same
                ],
            })

        absent.append({
            "event_title": (row.get("event_title") or "").strip(),
            "date": (row.get("date") or "").strip(),
            "source_event_url": (row.get("url") or "").strip(),
            "source_match_nr": (row.get("match_nr") or "").strip(),
            "fighter1_result": (row.get("fighter1_result") or "").strip(),
            "fighter2_result": (row.get("fighter2_result") or "").strip(),
            "win_method": (row.get("win_method") or "").strip(),
            "sides": sides,
        })

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "trusted_crosswalk_rows": len(trusted_rows),
        "absent_ufc_pair_rows": len(absent),
        "unique_involved_external_urls": len(involved_urls),
        "involved_canonical_id_frequency": involved_canonical_ids.most_common(),
        "involved_external_name_frequency": involved_external_names.most_common(),
        "trusted_external_urls_with_multiple_raw_names": {
            url: sorted(names) for url, names in raw_names_by_url.items()
            if url in involved_urls and len(names) > 1
        },
        "rows": absent,
        "decision": {
            "trusted_crosswalk_mutated": False,
            "canonical_rows_written": False,
            "required_next": "Determine whether absent-pair clusters are caused by trusted same-name identity collisions or true canonical fight omissions. Quarantine any suspect trusted mapping before external fight promotion."
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "absent_ufc_pair_rows": len(absent),
        "unique_involved_external_urls": len(involved_urls),
        "top_canonical_ids": involved_canonical_ids.most_common(10),
        "top_external_names": involved_external_names.most_common(10),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
