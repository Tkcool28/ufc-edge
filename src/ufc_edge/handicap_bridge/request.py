from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from typing import Any

REQUEST_SCHEMA = "h00-request-0.1"
_ALLOWED_KINDS = {"fighter", "matchup", "card"}
_REQUIRED_KEYS = {
    "fighter": {"schema", "kind", "fighter", "cutoff"},
    "matchup": {"schema", "kind", "fighter_a", "fighter_b", "cutoff"},
    "card": {"schema", "kind", "event_id", "cutoff"},
}
_FORBIDDEN_CONTROL_KEYS = {
    "command", "cmd", "script", "shell", "output", "output_path", "output_root",
    "branch", "ref", "git_ref", "repo", "repo_path", "env", "environment",
}


class RequestError(ValueError):
    """Safe validation failure for an H01 request."""


@dataclass(frozen=True)
class H01Request:
    schema: str
    kind: str
    cutoff: str
    payload: dict[str, str]
    request_hash: str


def _validate_cutoff(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestError("cutoff must be a non-empty ISO date or timestamp")
    text = value.strip()
    try:
        if "T" in text or text.endswith("Z"):
            datetime.fromisoformat(text.replace("Z", "+00:00"))
        else:
            date.fromisoformat(text)
    except ValueError as exc:
        raise RequestError("cutoff must be a valid ISO date or timestamp") from exc
    return text


def _string_field(obj: dict[str, Any], key: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RequestError(f"{key} must be a non-empty string")
    if "\x00" in value:
        raise RequestError(f"{key} contains an invalid character")
    return value.strip()


def parse_request(body: str) -> H01Request:
    try:
        obj = json.loads(body)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RequestError("request body must be valid JSON") from exc
    if not isinstance(obj, dict):
        raise RequestError("request body must be a JSON object")

    dangerous = sorted(_FORBIDDEN_CONTROL_KEYS.intersection(obj))
    if dangerous:
        raise RequestError(f"unsupported control field: {dangerous[0]}")

    schema = obj.get("schema")
    if schema != REQUEST_SCHEMA:
        raise RequestError(f"unsupported schema: {schema!r}")
    kind = obj.get("kind")
    if kind not in _ALLOWED_KINDS:
        raise RequestError(f"unsupported kind: {kind!r}")

    expected = _REQUIRED_KEYS[kind]
    unknown = sorted(set(obj) - expected)
    missing = sorted(expected - set(obj))
    if missing:
        raise RequestError(f"missing required field: {missing[0]}")
    if unknown:
        raise RequestError(f"unknown field: {unknown[0]}")

    cutoff = _validate_cutoff(obj["cutoff"])
    payload: dict[str, str] = {}
    if kind == "fighter":
        payload["fighter"] = _string_field(obj, "fighter")
    elif kind == "matchup":
        payload["fighter_a"] = _string_field(obj, "fighter_a")
        payload["fighter_b"] = _string_field(obj, "fighter_b")
    else:
        payload["event_id"] = _string_field(obj, "event_id")

    canonical = {"schema": REQUEST_SCHEMA, "kind": kind, **payload, "cutoff": cutoff}
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return H01Request(REQUEST_SCHEMA, kind, cutoff, payload, digest)


def actor_is_authorized(actor: str, repository_owner: str) -> bool:
    """Phase-1 authorization: repository owner only; fail closed for everyone else."""
    return bool(actor) and bool(repository_owner) and actor.casefold() == repository_owner.casefold()
