#!/usr/bin/env python3
"""Determine date transport semantics in the CC0 external MMA fighter snapshot.

The source uses slash-formatted dates whose day/month ordering must be established from
independent canonical DOB evidence before those dates can be used for identity matching.
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
EXT = ROOT / "data/raw/kaggle_pro_mma_fighters/v1/pro_mma_fighters.csv"
CANON = ROOT / "data/canonical/v0/fighters.csv"
OUT = ROOT / "provenance/audits/external_mma_birth_date_semantics_latest.json"


def read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def canonical_date(value: str) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def parse_slash(value: str, mode: str) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    for sep in ("/", "-"):
        m = re.fullmatch(rf"(\d{{1,2}}){re.escape(sep)}(\d{{1,2}}){re.escape(sep)}(\d{{4}})", text)
        if not m:
            continue
        a, b, y = map(int, m.groups())
        day, month = (a, b) if mode == "DMY" else (b, a)
        try:
            return datetime(y, month, day).date().isoformat()
        except ValueError:
            return None
    # unambiguous ISO-like source strings are not part of the DMY/MDY decision.
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return None


def main() -> int:
    ext = read(EXT)
    canon = read(CANON)
    by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in canon:
        by_name[norm(row.get("canonical_name") or "")].append(row)

    counts = Counter()
    raw_shapes = Counter()
    examples: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in ext:
        name = row.get("fighter_name") or ""
        raw = (row.get("birth_date") or "").strip()
        if raw:
            if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}", raw): raw_shapes["slash_D_M_Y_unknown"] += 1
            elif re.fullmatch(r"\d{1,2}-\d{1,2}-\d{4}", raw): raw_shapes["dash_D_M_Y_unknown"] += 1
            elif re.match(r"^\d{4}-\d{2}-\d{2}", raw): raw_shapes["iso"] += 1
            else: raw_shapes["other"] += 1
        candidates = by_name.get(norm(name), [])
        if len(candidates) != 1:
            continue
        canonical = canonical_date(candidates[0].get("dob") or "")
        if not canonical or not raw:
            continue
        dmy = parse_slash(raw, "DMY")
        mdy = parse_slash(raw, "MDY")
        counts["exact_name_with_both_dobs"] += 1
        if dmy == canonical: counts["dmy_matches"] += 1
        if mdy == canonical: counts["mdy_matches"] += 1
        if dmy == canonical and mdy != canonical: counts["dmy_only_matches"] += 1
        if mdy == canonical and dmy != canonical: counts["mdy_only_matches"] += 1
        if dmy == canonical and mdy == canonical: counts["both_match"] += 1
        if dmy != canonical and mdy != canonical: counts["neither_match"] += 1
        bucket = (
            "dmy_only" if dmy == canonical and mdy != canonical else
            "mdy_only" if mdy == canonical and dmy != canonical else
            "both" if dmy == canonical and mdy == canonical else "neither"
        )
        if len(examples[bucket]) < 25:
            examples[bucket].append({
                "fighter": name, "raw_birth_date": raw, "canonical_dob": canonical,
                "dmy_interpretation": dmy or "", "mdy_interpretation": mdy or "",
            })

    decisive = counts["dmy_only_matches"] + counts["mdy_only_matches"]
    winner = None
    if decisive >= 100:
        if counts["dmy_only_matches"] >= 10 * max(1, counts["mdy_only_matches"]): winner = "DMY"
        elif counts["mdy_only_matches"] >= 10 * max(1, counts["dmy_only_matches"]): winner = "MDY"
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "raw_date_shape_counts": dict(raw_shapes),
        "comparison_counts": dict(counts),
        "examples": dict(examples),
        "decision": {
            "promoted_source_slash_date_order": winner,
            "gate": "At least 100 decisive comparisons and winning exclusive-match count >=10x losing exclusive-match count.",
            "identity_audit_must_be_rebuilt_if_promoted": bool(winner),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"winner": winner, **dict(counts)}, sort_keys=True))
    return 0 if winner else 2


if __name__ == "__main__":
    raise SystemExit(main())
