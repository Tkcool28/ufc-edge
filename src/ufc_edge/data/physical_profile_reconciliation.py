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
    if checked.accepted and not allow_fill:
        return None, "official_validated_enrichment_disabled", checked
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


RECOVERY_FIELDS = {
    "height_cm": "height",
    "reach_cm": "reach_arm",
}
RECOVERY_UNITS = {"in", "cm"}
RECOVERY_REVIEW_STATUSES = {"accepted", "quarantined", "exhausted"}
RECOVERY_RESOLUTION_STATUSES = {
    "RESOLVED_TRUSTED_MEASUREMENT",
    "RESOLVED_CONFLICT_QUARANTINED",
    "EXHAUSTED_TRUSTED_SOURCES_NO_MEASUREMENT",
}


def validate_recovery_measurement(field_name: str, raw_value: object, raw_unit: object) -> Measurement:
    """Validate a governed supplemental height/reach measurement and normalize to cm."""
    if field_name not in RECOVERY_FIELDS:
        raise ValueError(f"unsupported recovery field: {field_name}")
    field = RECOVERY_FIELDS[field_name]
    text = _clean(raw_value)
    unit = (_clean(raw_unit) or "").lower()
    if text is None:
        return Measurement(field, None, None, False, "source_null")
    if unit not in RECOVERY_UNITS:
        return Measurement(field, text, None, False, "unsupported_or_missing_unit")
    try:
        value = Decimal(text)
    except InvalidOperation:
        return Measurement(field, text, None, False, "non_numeric")
    if not value.is_finite():
        return Measurement(field, text, None, False, "non_finite")
    if value == 0:
        return Measurement(field, text, None, False, "source_zero_missing")
    value_cm = value * INCH_TO_CM if unit == "in" else value
    lo_in, hi_in = PHYSICAL_BOUNDS_IN[field]
    lo_cm, hi_cm = lo_in * INCH_TO_CM, hi_in * INCH_TO_CM
    if not lo_cm <= value_cm <= hi_cm:
        return Measurement(field, text, None, False, f"outside_plausible_cm_{lo_cm}_{hi_cm}")
    return Measurement(field, text, value_cm, True, None)



LIVE_UFCSTATS_STATES = {"POPULATED", "CHECKED_STILL_NULL", "FETCH_OR_IDENTITY_FAILURE"}


def live_ufcstats_requirement(local_snapshot_value: object, *, pinned_live_checked: bool) -> str:
    """Classify whether a recent local-source null still requires a controlled live check."""
    if _clean(local_snapshot_value) is not None:
        return "LOCAL_SOURCE_POPULATED"
    if pinned_live_checked:
        return "LIVE_UFCSTATS_CHECKED"
    return "LIVE_UFCSTATS_CHECK_REQUIRED"


def live_ufcstats_selection(
    *,
    field_name: str,
    canonical_value: object,
    raw_value_inches: object,
    identity_verified: bool,
    live_state: str,
) -> tuple[Decimal | None, str, Measurement]:
    """Apply one pinned live UFCStats observation as NULL-FILL only.

    This function is deliberately network-free. Acquisition is handled separately;
    canonical reconciliation consumes only pinned observations.
    """
    checked = validate_recovery_measurement(field_name, raw_value_inches, "in")
    current = _clean(canonical_value)
    if current is not None:
        try:
            return Decimal(current), "prior_canonical_retained", checked
        except InvalidOperation as exc:
            raise ValueError(f"canonical {field_name} is non-numeric: {current!r}") from exc
    if live_state not in LIVE_UFCSTATS_STATES:
        return None, "live_ufcstats_invalid_state", checked
    if not identity_verified:
        return None, "live_ufcstats_untrusted_identity", checked
    if live_state == "CHECKED_STILL_NULL":
        return None, "live_ufcstats_checked_still_null", checked
    if live_state != "POPULATED":
        return None, "live_ufcstats_fetch_or_identity_failure", checked
    if not checked.accepted:
        return None, f"live_ufcstats_rejected_{checked.reason}", checked
    return checked.value_cm, "live_ufcstats_null_fill", checked

def recovery_selection(
    *,
    field_name: str,
    canonical_value: object,
    raw_value: object,
    raw_unit: object,
    review_status: str,
    resolution_status: str,
) -> tuple[Decimal | None, str, Measurement]:
    """Apply supplemental evidence only after prior canonical/official selection remains null."""
    checked = validate_recovery_measurement(field_name, raw_value, raw_unit)
    current = _clean(canonical_value)
    if current is not None:
        try:
            return Decimal(current), "prior_canonical_retained", checked
        except InvalidOperation as exc:
            raise ValueError(f"canonical {field_name} is non-numeric: {current!r}") from exc
    if review_status not in RECOVERY_REVIEW_STATUSES:
        return None, "supplemental_invalid_review_status", checked
    if resolution_status not in RECOVERY_RESOLUTION_STATUSES:
        return None, "supplemental_invalid_resolution_status", checked
    if review_status != "accepted" or resolution_status != "RESOLVED_TRUSTED_MEASUREMENT":
        label = "supplemental_conflict_quarantined" if review_status == "quarantined" else "supplemental_exhausted_no_measurement"
        return None, label, checked
    if not checked.accepted:
        return None, f"supplemental_rejected_{checked.reason}", checked
    return checked.value_cm, "supplemental_null_fill", checked
