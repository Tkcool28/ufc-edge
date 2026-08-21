#!/usr/bin/env python3
"""Build and audit a derived official UFC fight -> event/date bridge.

This follows only official UFC event relationships to official UFC fight UUIDs. It does
not infer event membership by title/name. The output remains derived QA evidence until
canonical identity reconciliation is complete.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENT_ROOT = Path("data/raw/ufc_com_resources/events")
FIGHT_ROOT = Path("data/raw/ufc_com_resources/fights")
OUT_CSV = Path("data/derived/identity/ufc_fight_event_bridge_candidate.csv")
OUT_JSON = Path("provenance/audits/ufc_fight_event_bridge_latest.json")
OUT_MD = Path("provenance/audits/ufc_fight_event_bridge_latest.md")


def latest_complete(root: Path) -> Path:
    candidates = sorted(p for p in root.iterdir() if p.is_dir() and (p / "manifest.json").exists())
    if not candidates:
        raise RuntimeError(f"No complete snapshot under {root}")
    for p in reversed(candidates):
        manifest = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("complete_collection_snapshot") is True or manifest.get("semantics", {}).get("complete_collection_snapshot") is True:
            return p
    raise RuntimeError(f"No snapshot marked complete under {root}")


def event_pages(snapshot: Path) -> list[Path]:
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    pages = [Path(str(x["path"])) for x in manifest.get("files", []) if isinstance(x, dict) and x.get("path")]
    if len(pages) != int(manifest.get("pages") or 0):
        raise RuntimeError(f"Event page count mismatch: {len(pages)} vs {manifest.get('pages')}")
    return pages


def fight_pages(snapshot: Path) -> list[Path]:
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    pages: list[Path] = []
    for chunk_manifest_raw in manifest.get("chunk_manifests") or []:
        chunk_manifest = Path(str(chunk_manifest_raw))
        chunk = json.loads(chunk_manifest.read_text(encoding="utf-8"))
        for info in chunk.get("files") or []:
            pages.append(Path(str(info["path"])))
    if len(pages) != int(manifest.get("pages") or 0):
        raise RuntimeError(f"Fight page count mismatch: {len(pages)} vs {manifest.get('pages')}")
    return pages


def rel_ids(item: dict[str, Any], name: str) -> list[str]:
    rel = (item.get("relationships") or {}).get(name)
    data = rel.get("data") if isinstance(rel, dict) else None
    if isinstance(data, dict) and data.get("id") is not None:
        return [str(data["id"])]
    if isinstance(data, list):
        return [str(x["id"]) for x in data if isinstance(x, dict) and x.get("id") is not None]
    return []


def parse_event_date(attrs: dict[str, Any]) -> tuple[str | None, str | None]:
    # Prefer the actual scheduled main-card timestamp. Keep the raw selected field.
    for field in ("fight_card_time_main", "main_card_time_localized", "fight_card_time_prelims", "fight_card_time_early"):
        value = attrs.get(field)
        if not value:
            continue
        text = str(value)
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return dt.date().isoformat(), field
        except ValueError:
            continue
    return None, None


def main() -> int:
    event_snapshot = latest_complete(EVENT_ROOT)
    fight_snapshot = latest_complete(FIGHT_ROOT)

    fight_ids: set[str] = set()
    fight_meta: dict[str, dict[str, Any]] = {}
    for page in fight_pages(fight_snapshot):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            uid = str(item["id"])
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            fight_ids.add(uid)
            fight_meta[uid] = {
                "fightmetric_id": attrs.get("fightmetric_id"),
                "fight_title": attrs.get("title"),
                "fight_nid": attrs.get("drupal_internal__nid"),
            }

    event_membership: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_rows = 0
    dated_events = 0
    linked_fight_refs = 0
    linked_unknown_fight_refs = 0
    date_field_counts: Counter[str] = Counter()
    for page in event_pages(event_snapshot):
        payload = json.loads(page.read_text(encoding="utf-8"))
        for item in payload.get("data") or []:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            event_rows += 1
            attrs = item.get("attributes") if isinstance(item.get("attributes"), dict) else {}
            event_date, date_field = parse_event_date(attrs)
            if event_date:
                dated_events += 1
                date_field_counts[str(date_field)] += 1
            event = {
                "ufc_event_uuid": str(item["id"]),
                "event_nid": attrs.get("drupal_internal__nid"),
                "event_fightmetric_id": attrs.get("fightmetric_id"),
                "event_name": attrs.get("title"),
                "event_date": event_date,
                "event_date_source_field": date_field,
            }
            for fight_uid in rel_ids(item, "fights"):
                linked_fight_refs += 1
                if fight_uid not in fight_ids:
                    linked_unknown_fight_refs += 1
                event_membership[fight_uid].append(event)

    duplicate_membership = {k: v for k, v in event_membership.items() if len(v) != 1}
    rows: list[dict[str, Any]] = []
    for fight_uid in sorted(fight_ids):
        memberships = event_membership.get(fight_uid, [])
        if len(memberships) != 1:
            continue
        event = memberships[0]
        row = {
            "ufc_fight_uuid": fight_uid,
            **fight_meta[fight_uid],
            **event,
        }
        rows.append(row)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ufc_fight_uuid", "fight_nid", "fightmetric_id", "fight_title",
        "ufc_event_uuid", "event_nid", "event_fightmetric_id", "event_name",
        "event_date", "event_date_source_field",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    dated_rows = sum(1 for r in rows if r.get("event_date"))
    fights_with_membership = len(event_membership)
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event_snapshot": event_snapshot.as_posix(),
        "fight_snapshot": fight_snapshot.as_posix(),
        "event_rows": event_rows,
        "dated_events": dated_events,
        "date_source_field_counts": dict(date_field_counts),
        "official_fight_rows": len(fight_ids),
        "event_fight_relationship_refs": linked_fight_refs,
        "relationship_refs_not_in_complete_fight_snapshot": linked_unknown_fight_refs,
        "distinct_fights_referenced_by_events": fights_with_membership,
        "fight_uuid_with_multiple_event_memberships": len(duplicate_membership),
        "fight_uuid_without_event_membership": len(fight_ids - set(event_membership)),
        "unique_fight_event_bridge_rows": len(rows),
        "unique_bridge_rows_with_date": dated_rows,
        "candidate_csv": OUT_CSV.as_posix(),
        "decision": {
            "canonical_promoted": False,
            "name_only_matching_used": False,
            "safe_for_calendar_coverage_audit": len(duplicate_membership) == 0 and dated_rows > 0,
            "rule": "Only direct UFC event.relationships.fights membership is emitted. Missing fights remain missing rather than inferred by titles.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(
        "# Official UFC fight → event/date bridge\n\n"
        f"- Official fight rows: **{len(fight_ids)}**\n"
        f"- Fights referenced by an official event: **{fights_with_membership}**\n"
        f"- Unique bridge rows: **{len(rows)}**\n"
        f"- Unique bridge rows with event date: **{dated_rows}**\n"
        f"- Multiple-event fight UUIDs: **{len(duplicate_membership)}**\n"
        f"- Fights without event membership: **{len(fight_ids - set(event_membership))}**\n\n"
        "Missing event membership is preserved as missing. No title/name inference is used.\n",
        encoding="utf-8",
    )
    print(json.dumps({"bridge_rows": len(rows), "dated": dated_rows, "multi_event": len(duplicate_membership)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
