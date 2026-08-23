from __future__ import annotations

import json
from pathlib import Path

import pytest

from ufc_edge.handicap_bridge.cache import prune_cache, replace_request_dir, request_dir
from ufc_edge.handicap_bridge.request import RequestError, actor_is_authorized, parse_request
from ufc_edge.handicap_bridge.response import build_response_manifest, failure_comment

CUTOFF = "2026-08-23T03:30:00Z"


def body(**values: str) -> str:
    return json.dumps(values)


def test_valid_fighter_request() -> None:
    req = parse_request(body(schema="h00-request-0.1", kind="fighter", fighter="Max Holloway", cutoff=CUTOFF))
    assert req.kind == "fighter"
    assert req.payload == {"fighter": "Max Holloway"}


def test_valid_matchup_request() -> None:
    req = parse_request(body(schema="h00-request-0.1", kind="matchup", fighter_a="Max Holloway", fighter_b="Dustin Poirier", cutoff=CUTOFF))
    assert req.kind == "matchup"
    assert len(req.request_hash) == 64


def test_valid_card_request() -> None:
    req = parse_request(body(schema="h00-request-0.1", kind="card", event_id="event-123", cutoff="2026-08-23"))
    assert req.payload["event_id"] == "event-123"


@pytest.mark.parametrize("payload", [
    {"schema": "wrong", "kind": "fighter", "fighter": "Max Holloway", "cutoff": CUTOFF},
    {"schema": "h00-request-0.1", "kind": "shell", "fighter": "Max Holloway", "cutoff": CUTOFF},
    {"schema": "h00-request-0.1", "kind": "fighter", "cutoff": CUTOFF},
])
def test_invalid_contract_rejected(payload: dict[str, str]) -> None:
    with pytest.raises(RequestError):
        parse_request(json.dumps(payload))


def test_malformed_json_rejected() -> None:
    with pytest.raises(RequestError):
        parse_request("{not json")


@pytest.mark.parametrize("key", ["command", "script", "output_path", "output_root", "branch", "ref", "env"])
def test_control_fields_rejected(key: str) -> None:
    payload = {"schema": "h00-request-0.1", "kind": "fighter", "fighter": "Max Holloway", "cutoff": CUTOFF, key: "evil"}
    with pytest.raises(RequestError, match="control field"):
        parse_request(json.dumps(payload))


def test_unknown_field_rejected() -> None:
    with pytest.raises(RequestError, match="unknown field"):
        parse_request(body(schema="h00-request-0.1", kind="fighter", fighter="Max Holloway", cutoff=CUTOFF, surprise="x"))


@pytest.mark.parametrize("event_id", ["../escape", "a/b", "a\\b", ".."])
def test_card_event_id_cannot_be_path_like(event_id: str) -> None:
    with pytest.raises(RequestError, match="canonical ID"):
        parse_request(body(schema="h00-request-0.1", kind="card", event_id=event_id, cutoff=CUTOFF))


def test_authorization_is_owner_only_and_case_insensitive() -> None:
    assert actor_is_authorized("Tkcool28", "Tkcool28")
    assert actor_is_authorized("tkcool28", "Tkcool28")
    assert not actor_is_authorized("someone-else", "Tkcool28")


def test_request_hash_is_stable_and_key_order_independent() -> None:
    one = parse_request('{"schema":"h00-request-0.1","kind":"matchup","fighter_a":"Max Holloway","fighter_b":"Dustin Poirier","cutoff":"2026-08-23T03:30:00Z"}')
    two = parse_request('{"cutoff":"2026-08-23T03:30:00Z","fighter_b":"Dustin Poirier","fighter_a":"Max Holloway","kind":"matchup","schema":"h00-request-0.1"}')
    assert one.request_hash == two.request_hash


def test_issue_workflow_lifecycle_gate_is_event_specific() -> None:
    workflow = Path(".github/workflows/h01-handicap-request.yml").read_text(encoding="utf-8")
    assert "github.event.issue.state == 'open'" in workflow
    assert "github.event.action == 'opened'" in workflow
    assert "startsWith(github.event.issue.title, '[H00 REQUEST]')" in workflow
    assert "github.event.action == 'labeled'" in workflow
    assert "github.event.label.name == 'h00-request'" in workflow
    assert "contains(github.event.issue.labels.*.name, 'h00-request')" not in workflow


def test_completion_and_failure_labels_cannot_qualify_labeled_trigger() -> None:
    workflow = Path(".github/workflows/h01-handicap-request.yml").read_text(encoding="utf-8")
    gate = workflow.split("  process-request:\n", 1)[1].split("    runs-on:", 1)[0]
    assert "github.event.label.name == 'h00-request'" in gate
    assert "h00-complete" not in gate
    assert "h00-failed" not in gate


def test_replace_same_issue_is_idempotent_snapshot(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    staged = tmp_path / "staged"
    staged.mkdir()
    (staged / "matchup.json").write_text("{}", encoding="utf-8")
    first = replace_request_dir(cache, 27, staged)
    (staged / "matchup.json").write_text('{"same_issue":true}', encoding="utf-8")
    second = replace_request_dir(cache, 27, staged)
    assert first == second
    assert [p.name for p in (cache / "handicap" / "requests").iterdir()] == ["27"]
    assert (second / "matchup.json").read_text(encoding="utf-8") == '{"same_issue":true}'


def test_response_manifest_has_source_cutoff_hash_size_and_packet_path(tmp_path: Path) -> None:
    root = tmp_path / "stage"
    packet = root / "handicap" / "requests" / "27" / "matchup.json"
    packet.parent.mkdir(parents=True)
    packet.write_text('{"packet_schema":"0.1.0"}\n', encoding="utf-8")
    manifest = build_response_manifest(
        issue_number=27,
        kind="matchup",
        request_hash="a" * 64,
        source_main_sha="b" * 40,
        h00_generator_commit="b" * 40,
        information_cutoff=CUTOFF,
        packet_schema_version="0.1.0",
        response_root=root,
        generated_paths=[packet],
    )
    assert manifest["source_main_sha"] == "b" * 40
    assert manifest["information_cutoff"] == CUTOFF
    assert manifest["files"][0]["path"] == "handicap/requests/27/matchup.json"
    assert len(manifest["files"][0]["sha256"]) == 64
    assert manifest["files"][0]["bytes"] == packet.stat().st_size


def test_cache_retention_keeps_most_recent_issue_numbers(tmp_path: Path) -> None:
    root = tmp_path / "cache"
    requests = root / "handicap" / "requests"
    for n in range(1, 26):
        path = requests / str(n)
        path.mkdir(parents=True)
        (path / "manifest.json").write_text("{}", encoding="utf-8")
    unrelated = requests / "README.txt"
    unrelated.write_text("keep", encoding="utf-8")
    removed = prune_cache(root, keep=20)
    assert removed == ["5", "4", "3", "2", "1"]
    assert sorted(int(p.name) for p in requests.iterdir() if p.is_dir()) == list(range(6, 26))
    assert unrelated.exists()


def test_cache_path_cannot_escape_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        request_dir(tmp_path, 0)
    root = tmp_path / "cache"
    assert request_dir(root, 27).resolve().is_relative_to(root.resolve())


def test_failure_comment_is_machine_readable_and_single_line_safe() -> None:
    text = failure_comment(27, "request_rejected", "bad\nsecret-looking trace", "abc")
    assert text.startswith("H00_REQUEST_FAILED\n")
    assert "Traceback" not in text
    assert "message: bad secret-looking trace" in text
