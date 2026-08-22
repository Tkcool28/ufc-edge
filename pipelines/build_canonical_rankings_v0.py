#!/usr/bin/env python3
"""Materialize dated UFC ranking observations into canonical v0.

DATA PHASE ONLY. This does not compute a pre-fight ranking feature. It preserves the
source's dated observations and source semantics so later feature code can apply strict
as-of joins without ever consulting a future ranking.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data/raw/tidytuesday_ufc_rankings"
CANON = ROOT / "data/canonical/v0"
FIGHTERS = CANON / "fighters.csv"
CONTRACT = ROOT / "schemas/canonical_data_contract_v0.json"
OUT = CANON / "rankings.csv"
EXCLUSIONS = ROOT / "data/derived/qa/canonical_rankings_exclusions_v0.csv"
AUDIT_JSON = ROOT / "provenance/audits/canonical_rankings_v0_latest.json"
AUDIT_MD = ROOT / "provenance/audits/canonical_rankings_v0_latest.md"
SOURCE = "tidytuesday_ufc_rankings"
RANKING_BODY = "UFC"
EXCLUSION_FIELDS = ["source_row_number", "date", "weightclass", "fighter", "rank", "reason", "details"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_snapshot() -> Path:
    candidates = sorted(p for p in RAW_ROOT.iterdir() if p.is_dir() and (p / "manifest.json").is_file())
    if not candidates:
        raise RuntimeError("No ranking snapshot")
    return candidates[-1]


def parse_rank(value: str) -> int:
    text = (value or "").strip()
    if not re.fullmatch(r"\d+(?:\.0+)?", text):
        raise ValueError(f"rank is not a nonnegative integer-like value: {value!r}")
    rank = int(float(text))
    if rank < 0:
        raise ValueError(f"negative rank: {value!r}")
    return rank


def main() -> int:
    snapshot = latest_snapshot()
    raw_path = snapshot / "ufc_rankings_dataset.csv"
    raw = read_csv(raw_path)
    canonical_fighters = read_csv(FIGHTERS)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    fields = list(contract["tables"]["rankings"]["fields"])

    by_norm: dict[str, set[str]] = defaultdict(set)
    for row in canonical_fighters:
        by_norm[norm(row["canonical_name"])].add(row["fighter_id"])
    unique = {name: next(iter(ids)) for name, ids in by_norm.items() if len(ids) == 1}

    candidates: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    exclusions: list[dict[str, Any]] = []
    stats = Counter()
    earliest: str | None = None
    latest: str | None = None

    def reject(i: int, row: dict[str, str], reason: str, details: str = "") -> None:
        exclusions.append({
            "source_row_number": i,
            "date": row.get("date") or "",
            "weightclass": row.get("weightclass") or "",
            "fighter": row.get("fighter") or "",
            "rank": row.get("rank") or "",
            "reason": reason,
            "details": details,
        })

    for i, row in enumerate(raw, start=2):
        raw_date = (row.get("date") or "").strip()
        weightclass = (row.get("weightclass") or "").strip()
        fighter = (row.get("fighter") or "").strip()
        if not raw_date or not weightclass or not fighter:
            stats["missing_required_transport"] += 1
            reject(i, row, "missing_required_transport")
            continue
        try:
            ranking_date = date.fromisoformat(raw_date).isoformat()
            rank = parse_rank(row.get("rank") or "")
        except ValueError as exc:
            stats["invalid_transport"] += 1
            reject(i, row, "invalid_transport", str(exc))
            continue

        name_key = norm(fighter)
        ids = by_norm.get(name_key, set())
        fighter_id = unique.get(name_key)
        if not fighter_id:
            reason = "ambiguous_exact_canonical_name" if len(ids) > 1 else "unmatched_exact_canonical_name"
            stats[reason] += 1
            reject(i, row, reason, f"canonical_candidate_count={len(ids)}")
            continue

        out = {
            "ranking_date": ranking_date,
            "fighter_id": fighter_id,
            "weight_class": weightclass,
            "rank_numeric": rank,
            "is_champion": rank == 0,
            "ranking_body": RANKING_BODY,
        }
        key = (ranking_date, fighter_id, weightclass, RANKING_BODY)
        candidates[key].append({"row": out, "source_row": i, "raw": row})
        earliest = ranking_date if earliest is None or ranking_date < earliest else earliest
        latest = ranking_date if latest is None or ranking_date > latest else latest

    rows: list[dict[str, Any]] = []
    for key, group in sorted(candidates.items()):
        ranks = {int(x["row"]["rank_numeric"]) for x in group}
        if len(ranks) > 1:
            stats["conflicting_duplicate_primary_key"] += len(group)
            for item in group:
                reject(item["source_row"], item["raw"], "conflicting_duplicate_primary_key", f"observed_ranks={sorted(ranks)}")
            continue
        rows.append(group[0]["row"])
        if len(group) > 1:
            stats["identical_duplicate_rows_suppressed"] += len(group) - 1

    rows.sort(key=lambda r: (r["ranking_date"], r["weight_class"], int(r["rank_numeric"]), r["fighter_id"]))
    exclusions.sort(key=lambda r: (int(r["source_row_number"]), r["reason"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="raise")
        w.writeheader()
        for row in rows:
            w.writerow({k: ("true" if row[k] is True else "false" if row[k] is False else row[k]) for k in fields})
    EXCLUSIONS.parent.mkdir(parents=True, exist_ok=True)
    with EXCLUSIONS.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=EXCLUSION_FIELDS)
        w.writeheader(); w.writerows(exclusions)

    audit = {
        "schema_version": 1,
        "canonical_contract_version": contract.get("contract_version"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": SOURCE,
        "source_snapshot_id": snapshot.name,
        "raw_rows": len(raw),
        "canonical_rows": len(rows),
        "excluded_rows": len(exclusions),
        "canonical_fighters_represented": len({r["fighter_id"] for r in rows}),
        "weight_classes": sorted({r["weight_class"] for r in rows}),
        "earliest_ranking_date": earliest,
        "latest_ranking_date": latest,
        "qa_counts": dict(sorted(stats.items())),
        "rules": {
            "creates_fighter_identity_from_name": False,
            "observation_assignment_rule": "exact normalized fighter name must map to exactly one existing canonical fighter",
            "future_ranking_lookup_performed": False,
            "interpolation_performed": False,
            "rank_zero_semantics": "source documentation says rank 0 typically designates reigning champion; canonical is_champion is rank==0 for this source",
        },
        "outputs": {"table": str(OUT.relative_to(ROOT)), "exclusions": str(EXCLUSIONS.relative_to(ROOT))},
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    AUDIT_MD.write_text(
        "# Canonical dated UFC rankings v0\n\n"
        f"- Raw rows: **{len(raw)}**\n"
        f"- Canonical dated observations: **{len(rows)}**\n"
        f"- Canonical fighters represented: **{audit['canonical_fighters_represented']}**\n"
        f"- Date range: **{earliest}** to **{latest}**\n"
        f"- Quarantined source rows: **{len(exclusions)}**\n\n"
        "This table contains dated observations only. No future lookup, interpolation, or pre-fight feature has been computed.\n",
        encoding="utf-8",
    )

    manifest_path = CANON / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("canonical_contract_version") != contract.get("contract_version"):
        raise RuntimeError("canonical manifest contract version mismatch")
    manifest.setdefault("counts", {})["rankings"] = len(rows)
    manifest.setdefault("counts", {})["rankings_exclusions"] = len(exclusions)
    manifest.setdefault("source_snapshots", {})[SOURCE] = snapshot.name
    paths = {str(OUT.relative_to(ROOT)), str(EXCLUSIONS.relative_to(ROOT))}
    entries = [x for x in manifest.get("files", []) if x.get("path") not in paths]
    for path in (OUT, EXCLUSIONS):
        entries.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest["files"] = sorted(entries, key=lambda x: x["path"])
    manifest["generated_at_utc"] = audit["generated_at_utc"]
    manifest.setdefault("rules", {})["rankings_are_dated_observations_not_features"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "raw": len(raw), "canonical": len(rows), "fighters": audit["canonical_fighters_represented"],
        "excluded": len(exclusions), "earliest": earliest, "latest": latest,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
