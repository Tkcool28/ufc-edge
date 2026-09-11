"""Fail-closed round-duration eligibility and elapsed-exposure helpers.

This layer derives no new canonical facts. It combines frozen canonical fight/event metadata
with a versioned human-audited rules registry. Unknown/ambiguous rules stay unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any


REGISTRY_RELATIVE_PATH = Path("provenance/rulesets/elapsed_exposure_ruleset_registry_v1.json")
ELIGIBLE_STATUSES = {"verified", "inferred_from_verified_ruleset", "known_nonstandard"}
VALID_STATUSES = ELIGIBLE_STATUSES | {"ambiguous", "unknown", "not_applicable"}


class ElapsedExposureError(ValueError):
    """Raised when an apparently eligible observation violates duration semantics."""


@dataclass(frozen=True)
class RulesetAssignment:
    ruleset_id: str | None
    elapsed_exposure_status: str
    round_duration_sec: int | None
    round_durations_sec: tuple[int, ...] | None
    evidence_source: tuple[str, ...]
    reason: str

    @property
    def eligible(self) -> bool:
        return self.elapsed_exposure_status in ELIGIBLE_STATUSES


@dataclass(frozen=True)
class FightExposure:
    fight_id: str
    ruleset_id: str | None
    elapsed_exposure_status: str
    round_duration_vector: tuple[int, ...] | None
    elapsed_sec: int | None
    evidence_source: tuple[str, ...]
    reason: str

    @property
    def eligible(self) -> bool:
        return self.elapsed_exposure_status in ELIGIBLE_STATUSES and self.elapsed_sec is not None


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def registry_path(root: Path | None = None) -> Path:
    return (root or repository_root()) / REGISTRY_RELATIVE_PATH


def load_registry(root: Path | None = None) -> dict[str, Any]:
    path = registry_path(root)
    value = json.loads(path.read_text(encoding="utf-8"))
    validate_registry(value)
    return value


def registry_sha256(root: Path | None = None) -> str:
    return hashlib.sha256(registry_path(root).read_bytes()).hexdigest()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") not in {1, 2}:
        raise ElapsedExposureError("ruleset registry schema_version must be 1 or 2")
    if not registry.get("registry_version"):
        raise ElapsedExposureError("ruleset registry version is required")
    source_refs = registry.get("source_refs")
    rulesets = registry.get("rulesets")
    if not isinstance(source_refs, dict) or not source_refs:
        raise ElapsedExposureError("ruleset registry requires source_refs")
    if not isinstance(rulesets, list) or not rulesets:
        raise ElapsedExposureError("ruleset registry requires rulesets")

    ids: set[str] = set()
    for rule in rulesets:
        required = {
            "ruleset_id", "promotion", "effective_start", "effective_end", "bout_scope",
            "scheduled_round_options", "classification", "source_refs",
            "finish_time_semantics", "finish_time_source_refs", "confidence", "notes",
        }
        missing = sorted(required - set(rule))
        if missing:
            raise ElapsedExposureError(f"ruleset missing keys: {missing}")
        rid = rule["ruleset_id"]
        if rid in ids:
            raise ElapsedExposureError(f"duplicate ruleset_id: {rid}")
        ids.add(rid)

        fixed = _positive_int(rule.get("round_duration_sec"))
        vector_raw = rule.get("round_durations_sec")
        vector = None
        if vector_raw is not None:
            if not isinstance(vector_raw, list) or not vector_raw:
                raise ElapsedExposureError(f"{rid} round_durations_sec must be a non-empty list")
            parsed = tuple(_positive_int(value) for value in vector_raw)
            if any(value is None for value in parsed):
                raise ElapsedExposureError(f"{rid} has invalid explicit round duration")
            vector = tuple(int(value) for value in parsed if value is not None)
        if (fixed is None) == (vector is None):
            raise ElapsedExposureError(
                f"{rid} must declare exactly one of round_duration_sec or round_durations_sec"
            )

        options = rule["scheduled_round_options"]
        if not isinstance(options, list) or not options or any(_positive_int(x) is None for x in options):
            raise ElapsedExposureError(f"{rid} scheduled_round_options invalid")
        if vector is not None and any(int(x) != len(vector) for x in options):
            raise ElapsedExposureError(
                f"{rid} explicit duration vector requires scheduled_round_options={len(vector)}"
            )

        if rule["finish_time_semantics"] != "elapsed_within_terminal_round":
            raise ElapsedExposureError(f"{rid} finish time semantics are not contract-safe")
        for source_ref in list(rule["source_refs"]) + list(rule["finish_time_source_refs"]):
            if source_ref not in source_refs:
                raise ElapsedExposureError(f"{rid} references unknown evidence {source_ref}")
        start = _parse_date(rule["effective_start"])
        end = _parse_date(rule["effective_end"])
        if rule["effective_start"] is not None and start is None:
            raise ElapsedExposureError(f"{rid} invalid effective_start")
        if rule["effective_end"] is not None and end is None:
            raise ElapsedExposureError(f"{rid} invalid effective_end")
        if start and end and end < start:
            raise ElapsedExposureError(f"{rid} effective range is inverted")


def assign_ruleset(
    promotion: str | None,
    event_date: str | None,
    registry: dict[str, Any],
) -> RulesetAssignment:
    """Assign only from promotion + historically applicable effective dates.

    scheduled_rounds, finish_round, stats, and control values can never authorize a ruleset.
    """
    validate_registry(registry)
    promo = (promotion or "").strip()
    when = _parse_date(event_date)
    if not promo or when is None:
        return RulesetAssignment(None, "unknown", None, None, (), "missing promotion or valid event_date")

    matches: list[dict[str, Any]] = []
    for rule in registry["rulesets"]:
        if rule["promotion"] != promo:
            continue
        start = _parse_date(rule["effective_start"])
        end = _parse_date(rule["effective_end"])
        if start and when < start:
            continue
        if end and when > end:
            continue
        matches.append(rule)

    if len(matches) > 1:
        raise ElapsedExposureError(f"overlapping rulesets for {promo} on {event_date}")
    if len(matches) == 1:
        rule = matches[0]
        status = (
            "known_nonstandard"
            if rule["classification"] == "VERIFIED_NONSTANDARD_FIXED"
            else "inferred_from_verified_ruleset"
        )
        refs = tuple(rule["source_refs"] + rule["finish_time_source_refs"])
        fixed = _positive_int(rule.get("round_duration_sec"))
        vector = (
            tuple(int(x) for x in rule["round_durations_sec"])
            if rule.get("round_durations_sec") is not None
            else None
        )
        return RulesetAssignment(
            rule["ruleset_id"],
            status,
            fixed,
            vector,
            refs,
            f"promotion/era matches {rule['ruleset_id']}",
        )

    if promo == "UFC" and when < date(2000, 11, 17):
        return RulesetAssignment(
            None,
            "ambiguous",
            None,
            None,
            ("ufc_28_modern_boundary",),
            "pre-UFC-28 rules could vary by event or bout",
        )
    return RulesetAssignment(None, "unknown", None, None, (), "no verified promotion/era ruleset match")


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rule_for(assignment: RulesetAssignment, registry: dict[str, Any]) -> dict[str, Any] | None:
    if assignment.ruleset_id is None:
        return None
    return next(
        (rule for rule in registry["rulesets"] if rule["ruleset_id"] == assignment.ruleset_id),
        None,
    )


def _duration_for_round(assignment: RulesetAssignment, round_number: int) -> int | None:
    if round_number < 1:
        return None
    if assignment.round_durations_sec is not None:
        if round_number > len(assignment.round_durations_sec):
            return None
        return assignment.round_durations_sec[round_number - 1]
    return assignment.round_duration_sec


def scheduled_duration_vector(
    assignment: RulesetAssignment,
    scheduled_rounds: Any,
    registry: dict[str, Any],
) -> tuple[int, ...] | None:
    if not assignment.eligible or assignment.ruleset_id is None:
        return None
    n = _as_int(scheduled_rounds)
    if n is None:
        return None
    rule = _rule_for(assignment, registry)
    if rule is None or n not in {int(x) for x in rule["scheduled_round_options"]}:
        return None
    durations = tuple(_duration_for_round(assignment, rnd) or 0 for rnd in range(1, n + 1))
    if any(value <= 0 for value in durations):
        return None
    return durations


def infer_fight_exposure(
    fight: dict[str, Any],
    event_date: str | None,
    registry: dict[str, Any],
) -> FightExposure:
    fight_id = str(fight.get("fight_id") or "")
    assignment = assign_ruleset(fight.get("promotion"), event_date, registry)
    if not assignment.eligible:
        return FightExposure(
            fight_id, assignment.ruleset_id, assignment.elapsed_exposure_status,
            None, None, assignment.evidence_source, assignment.reason,
        )

    finish_round = _as_int(fight.get("finish_round"))
    finish_time = _as_int(fight.get("finish_time_sec"))
    if finish_round is None or finish_round < 1 or finish_time is None:
        return FightExposure(
            fight_id, assignment.ruleset_id, "ambiguous", None, None,
            assignment.evidence_source, "missing/invalid canonical finish_round or finish_time_sec",
        )

    terminal_duration = _duration_for_round(assignment, finish_round)
    if terminal_duration is None:
        return FightExposure(
            fight_id, assignment.ruleset_id, "ambiguous", None, None,
            assignment.evidence_source, "verified ruleset does not define the terminal round duration",
        )
    if not 0 <= finish_time <= terminal_duration:
        raise ElapsedExposureError(
            f"{fight_id}: finish_time_sec={finish_time} outside 0..{terminal_duration}"
        )

    scheduled = scheduled_duration_vector(assignment, fight.get("scheduled_rounds"), registry)
    method = str(fight.get("method") or "").upper()
    if method == "DECISION":
        if scheduled is None:
            return FightExposure(
                fight_id, assignment.ruleset_id, "ambiguous", None, None,
                assignment.evidence_source,
                "decision requires verified ruleset plus canonical scheduled_rounds; scheduled duration unavailable",
            )
        if finish_round != len(scheduled) or finish_time != scheduled[-1]:
            return FightExposure(
                fight_id, assignment.ruleset_id, "ambiguous", scheduled, None,
                assignment.evidence_source,
                "decision terminal timing does not equal full verified scheduled duration",
            )
        return FightExposure(
            fight_id, assignment.ruleset_id, assignment.elapsed_exposure_status,
            scheduled, sum(scheduled), assignment.evidence_source,
            "full scheduled duration from verified ruleset",
        )

    contested = tuple(
        _duration_for_round(assignment, rnd) or 0
        for rnd in range(1, finish_round + 1)
    )
    if any(value <= 0 for value in contested):
        return FightExposure(
            fight_id, assignment.ruleset_id, "ambiguous", None, None,
            assignment.evidence_source, "verified ruleset lacks a contested-round duration",
        )
    elapsed = sum(contested[:-1]) + finish_time
    return FightExposure(
        fight_id, assignment.ruleset_id, assignment.elapsed_exposure_status,
        contested, elapsed, assignment.evidence_source,
        "completed prior verified-duration rounds plus canonical elapsed terminal-round time",
    )


def infer_round_exposure(
    fight: dict[str, Any],
    event_date: str | None,
    round_number: Any,
    registry: dict[str, Any],
) -> int | None:
    exposure = infer_fight_exposure(fight, event_date, registry)
    if not exposure.eligible or exposure.round_duration_vector is None:
        return None
    rnd = _as_int(round_number)
    finish_round = _as_int(fight.get("finish_round"))
    finish_time = _as_int(fight.get("finish_time_sec"))
    if rnd is None or finish_round is None or finish_time is None or rnd < 1 or rnd > finish_round:
        return None
    if rnd < finish_round:
        return exposure.round_duration_vector[rnd - 1]
    return finish_time


def control_share(control_sec: Any, elapsed_sec: Any) -> float | None:
    """Return exact generic-control share; missing is never converted to zero."""
    control = _as_int(control_sec)
    elapsed = _as_int(elapsed_sec)
    if control is None:
        return None
    if elapsed is None or elapsed <= 0:
        return None
    if control < 0:
        raise ElapsedExposureError("control_sec cannot be negative")
    if control > elapsed:
        raise ElapsedExposureError(
            f"control_sec={control} exceeds compatible elapsed_sec={elapsed}"
        )
    return control / elapsed
