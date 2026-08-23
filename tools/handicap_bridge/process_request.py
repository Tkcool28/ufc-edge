from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ufc_edge.handicap.builders import build_fighter_dossier, build_matchup_packet, write_json
from ufc_edge.handicap.cards import build_card_packets
from ufc_edge.handicap.render import render_matchup_markdown
from ufc_edge.handicap.store import CanonicalStore
from ufc_edge.handicap_bridge.request import RequestError, actor_is_authorized, parse_request
from ufc_edge.handicap_bridge.response import build_response_manifest, write_manifest

PACKET_SCHEMA = "0.1.0"
TITLE_PREFIX = "[H00 REQUEST]"
REQUEST_LABEL = "h00-request"


def _write_result(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_trigger(issue: dict[str, object]) -> None:
    title = str(issue.get("title") or "")
    labels = issue.get("labels") or []
    label_names = {
        str(item.get("name")) for item in labels if isinstance(item, dict) and item.get("name")
    }
    if not title.startswith(TITLE_PREFIX) and REQUEST_LABEL not in label_names:
        raise RequestError("issue is not marked as an H00 request")


def process(args: argparse.Namespace) -> dict[str, object]:
    event = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
    repo = event.get("repository") or {}
    issue = event.get("issue") or {}
    if not isinstance(repo, dict) or not isinstance(issue, dict):
        raise RequestError("GitHub event is missing repository or issue data")
    if str(repo.get("full_name") or "") != args.repository:
        raise RequestError("request repository does not match trusted repository")
    owner = ((repo.get("owner") or {}).get("login") if isinstance(repo.get("owner"), dict) else None)
    actor = ((issue.get("user") or {}).get("login") if isinstance(issue.get("user"), dict) else None)
    if not actor_is_authorized(str(actor or ""), str(owner or "")):
        raise RequestError("issue actor is not authorized for H01")
    _validate_trigger(issue)

    issue_number = int(issue.get("number") or 0)
    if issue_number <= 0:
        raise RequestError("invalid issue number")
    request = parse_request(str(issue.get("body") or ""))

    repo_root = Path(args.repo_root).resolve()
    temp_root = Path(args.output_root).resolve()
    stage_root = Path(args.stage_root).resolve()
    if repo_root == temp_root or repo_root in temp_root.parents:
        raise RequestError("H01 output root must be outside the trusted repository")
    if repo_root == stage_root or repo_root in stage_root.parents:
        raise RequestError("H01 staging root must be outside the trusted repository")

    store = CanonicalStore(repo_root)
    request_dir = stage_root / "handicap" / "requests" / str(issue_number)
    if request_dir.exists():
        shutil.rmtree(request_dir)
    request_dir.mkdir(parents=True, exist_ok=True)

    canonical_request = {"schema": request.schema, "kind": request.kind, **request.payload, "cutoff": request.cutoff}
    (request_dir / "request.json").write_text(
        json.dumps(canonical_request, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    generated: list[Path] = []
    if request.kind == "fighter":
        fighter_id = store.resolve_fighter(request.payload["fighter"])
        packet = build_fighter_dossier(store, fighter_id, request.cutoff)
        out = request_dir / "fighter.json"
        write_json(packet, out, pretty=True)
        generated.append(out)
    elif request.kind == "matchup":
        a_id = store.resolve_fighter(request.payload["fighter_a"])
        b_id = store.resolve_fighter(request.payload["fighter_b"])
        packet = build_matchup_packet(store, a_id, b_id, request.cutoff)
        json_out = request_dir / "matchup.json"
        md_out = request_dir / "matchup.md"
        write_json(packet, json_out, pretty=True)
        md_out.write_text(render_matchup_markdown(packet), encoding="utf-8")
        generated.extend([json_out, md_out])
    else:
        event_id = request.payload["event_id"]
        build_card_packets(store, event_id, request.cutoff, temp_root)
        source_card = temp_root / "v0" / "cards" / event_id
        if not source_card.is_dir():
            raise RuntimeError("H00 card generator did not create the expected card directory")
        card_out = request_dir / "card"
        shutil.copytree(source_card, card_out)
        generated.extend(sorted(p for p in card_out.rglob("*") if p.is_file()))

    for path in generated:
        if path.suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError("H00 generated a non-object JSON packet")
        if path.stat().st_size == 0:
            raise RuntimeError("H00 generated an empty packet file")

    manifest = build_response_manifest(
        issue_number=issue_number,
        kind=request.kind,
        request_hash=request.request_hash,
        source_main_sha=args.source_main_sha,
        h00_generator_commit=args.source_main_sha,
        information_cutoff=request.cutoff,
        packet_schema_version=PACKET_SCHEMA,
        response_root=stage_root,
        generated_paths=generated,
    )
    manifest_path = request_dir / "manifest.json"
    write_manifest(manifest, manifest_path)
    return {
        "status": "complete",
        "issue_number": issue_number,
        "kind": request.kind,
        "request_hash": request.request_hash,
        "manifest_path": manifest_path.relative_to(stage_root).as_posix(),
        "request_dir": request_dir.relative_to(stage_root).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Process one trusted H01 GitHub issue request.")
    parser.add_argument("--event-path", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--stage-root", required=True)
    parser.add_argument("--source-main-sha", required=True)
    parser.add_argument("--result-path", required=True)
    args = parser.parse_args()
    result_path = Path(args.result_path)
    try:
        result = process(args)
        _write_result(result_path, result)
        return 0
    except RequestError as exc:
        _write_result(result_path, {"status": "failed", "failure_category": "request_rejected", "message": str(exc)})
        return 2
    except Exception as exc:  # safe outer boundary; no traceback is persisted or commented
        _write_result(result_path, {"status": "failed", "failure_category": "generation_failed", "message": str(exc)[:500]})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
