from __future__ import annotations

import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .builders import build_matchup_packet, generator_commit, write_json
from .render import render_matchup_markdown
from .store import CanonicalStore, iso_utc, parse_cutoff

def _slug(value: str) -> str:
    import re
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value[:60] or "fighter"

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_card_packets(
    store: CanonicalStore,
    event_id: str,
    cutoff: str | datetime | date,
    output_root: Path,
    *,
    generated_at: datetime | None = None,
    generator_commit_sha: str | None = None,
) -> dict[str, Any]:
    store.ensure_indexes()
    event = store.events_by_id.get(event_id)
    if event is None:
        raise KeyError(
            f"canonical event not found: {event_id}; H00 does not acquire or repair missing events"
        )
    cutoff_dt = parse_cutoff(cutoff)
    from datetime import timezone
    generated_at = generated_at or datetime.now(timezone.utc)
    generator_commit_sha = generator_commit_sha if generator_commit_sha is not None else generator_commit(store.root)

    card_dir = output_root / "v0" / "cards" / event_id
    card_dir.mkdir(parents=True, exist_ok=True)

    fights = list(store.fights_by_event.get(event_id, []))
    fights.sort(
        key=lambda row: (
            int(row.get("bout_order")) if row.get("bout_order") is not None else 9999,
            str(row.get("fight_id") or ""),
        )
    )
    generated: list[dict[str, Any]] = []
    for index, fight in enumerate(fights, start=1):
        a_id = fight["fighter_a_id"]
        b_id = fight["fighter_b_id"]
        a_name = store.canonical_name(a_id)
        b_name = store.canonical_name(b_id)
        packet = build_matchup_packet(
            store,
            a_id,
            b_id,
            cutoff_dt,
            generated_at=generated_at,
            generator_commit_sha=generator_commit_sha,
        )
        stem = f"fight_{index:02d}_{_slug(a_name)}_vs_{_slug(b_name)}"
        json_path = card_dir / f"{stem}.json"
        md_path = card_dir / f"{stem}.md"
        write_json(packet, json_path, pretty=True)
        md_path.write_text(render_matchup_markdown(packet), encoding="utf-8")
        generated.append(
            {
                "fight_id": fight["fight_id"],
                "fighter_a": {"id": a_id, "name": a_name},
                "fighter_b": {"id": b_id, "name": b_name},
                "json_path": json_path.relative_to(store.root).as_posix()
                    if store.root in json_path.parents else json_path.as_posix(),
                "markdown_path": md_path.relative_to(store.root).as_posix()
                    if store.root in md_path.parents else md_path.as_posix(),
                "json_bytes": json_path.stat().st_size,
                "markdown_bytes": md_path.stat().st_size,
                "json_sha256": _sha256(json_path),
                "markdown_sha256": _sha256(md_path),
            }
        )
    manifest = {
        "packet_schema_version": "0.1.0",
        "artifact_type": "card_manifest",
        "canonical_event_id": event_id,
        "event": event,
        "generated_at_utc": iso_utc(generated_at),
        "information_cutoff": iso_utc(cutoff_dt),
        "generator_commit": generator_commit_sha,
        "data_contract_version": store.manifest["canonical_contract_version"],
        "canonical_manifest": {
            "path": "data/canonical/v0/manifest.json",
            "sha256": store.manifest_sha256,
        },
        "data_freeze": {
            "path": "provenance/data_phase_freeze_v0.json",
            "sha256": store.freeze_sha256,
        },
        "fights": generated,
    }
    write_json(manifest, card_dir / "manifest.json", pretty=True)
    return manifest
