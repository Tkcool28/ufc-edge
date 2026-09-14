"""Validated, provenance-preserving reconciliation of official UFC physical profiles.

This module deliberately supports NULL-FILL only. It never overwrites a populated
canonical measurement: a future official-first policy needs a separately reviewed
overlap decision.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

INCH_TO_CM = Decimal("2.54")
PHYSICAL_BOUNDS_IN = {
    "height": (Decimal("48"), Decimal("90")),
    "reach_arm": (Decimal("48"), Decimal("96")),
    "reach_leg": (Decimal("24"), Decimal("72")),
}


@dataclass(frozen=True)
class Measurement:
    field: str
    raw_value: str | None
    value_cm: Decimal | None
    accepted: bool
    reason: str | None


def _clean(raw: object) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def validate_official_inches(field: str, raw: object) -> Measurement:
    """Validate a UFC official numeric profile value whose verified unit is inches."""
    if field not in PHYSICAL_BOUNDS_IN:
        raise ValueError(f"unsupported physical field: {field}")
    text = _clean(raw)
    if text is None:
        return Measurement(field, None, None, False, "source_null")
    try:
        inches = Decimal(text)
    except InvalidOperation:
        return Measurement(field, text, None, False, "non_numeric")
    if not inches.is_finite():
        return Measurement(field, text, None, False, "non_finite")
    if inches == Decimal("0"):
        return Measurement(field, text, None, False, "source_zero_missing")
    lo, hi = PHYSICAL_BOUNDS_IN[field]
    if not lo <= inches <= hi:
        return Measurement(field, text, None, False, f"outside_plausible_inches_{lo}_{hi}")
    return Measurement(field, text, inches * INCH_TO_CM, True, None)


def selection(*, field: str, canonical_value: object, official_raw: object, trusted_identity: bool, mapping_verified: bool = True, allow_fill: bool = True) -> tuple[Decimal | None, str, Measurement]:
    """Return NULL-FILL selection and a truthful, stable selection label."""
    current = _clean(canonical_value)
    checked = validate_official_inches(field, official_raw)
    if current is not None:
        try:
            return Decimal(current), "greco_retained_populated", checked
        except InvalidOperation as exc:
            raise ValueError(f"canonical {field} is non-numeric: {current!r}") from exc
    if not trusted_identity:
        return None, "canonical_null_untrusted_official_identity", checked
    if not mapping_verified:
        return None, "canonical_null_unverified_official_mapping", checked
    if checked.accepted:
        return checked.value_cm, "official_null_fill", checked
    return None, f"canonical_null_official_rejected_{checked.reason}", checked


def agreement_category(left_cm: object, right_cm: object) -> tuple[Decimal | None, str]:
    """Classify comparable centimetre measurements by inch-scale absolute distance."""
    if _clean(left_cm) is None or _clean(right_cm) is None:
        return None, "not_comparable"
    try:
        diff = abs(Decimal(str(left_cm)) - Decimal(str(right_cm))) / INCH_TO_CM
    except InvalidOperation:
        return None, "not_comparable"
    if diff == 0:
        return diff, "exact_agreement"
    if diff < Decimal("0.5"):
        return diff, "small_rounding_difference"
    if diff == Decimal("0.5"):
        return diff, "half_inch_difference"
    if diff <= Decimal("1"):
        return diff, "one_inch_or_less_difference"
    return diff, "greater_than_one_inch_difference"


def walk_records(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_records(child)


def official_stats(record: dict[str, Any]) -> dict[str, Any] | None:
    """Return one record's profile-stat mapping across known official envelope shapes."""
    for candidate in (record.get("stats"), record.get("profileStats"), record.get("profile_stats")):
        if isinstance(candidate, dict) and any(k in candidate for k in ("height", "reach_arm", "reach_leg")):
            return candidate
    attrs = record.get("attributes") if isinstance(record.get("attributes"), dict) else {}
    candidate = record if any(k in record for k in ("stats_height", "stats_reach_arm", "stats_reach_leg")) else attrs
    if any(k in candidate for k in ("stats_height", "stats_reach_arm", "stats_reach_leg")):
        return {
            "height": candidate.get("stats_height"),
            "reach_arm": candidate.get("stats_reach_arm"),
            "reach_leg": candidate.get("stats_reach_leg"),
        }
    return None


def official_uuid(record: dict[str, Any]) -> str | None:
    for key in ("id", "uuid", "athlete_id", "athleteId", "fighter_id", "fighterId"):
        value = _clean(record.get(key))
        if value:
            return value
    return None
