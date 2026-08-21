"""Strict parsing primitives for UFC Edge canonical data adapters.

These helpers normalize transport syntax only. They do not resolve source identity,
choose between conflicting sources, or invent values for missing observations.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

_NULL_TEXT = {"", "--", "n/a", "na", "null", "none"}
_LA_RE = re.compile(r"^\s*(\d+)\s+of\s+(\d+)\s*$", re.IGNORECASE)
_MMSS_RE = re.compile(r"^\s*(\d+):(\d{2})\s*$")
_ROUND_RE = re.compile(r"^\s*Round\s+(\d+)\s*$", re.IGNORECASE)
_FEET_IN_RE = re.compile(r"^\s*(\d+)\s*'\s*(\d+(?:\.\d+)?)\s*(?:\"|in)?\s*$", re.IGNORECASE)
_INCH_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:\"|in|inches?)?\s*$", re.IGNORECASE)
_LB_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*(?:lb|lbs|pounds?)?\s*$", re.IGNORECASE)


def text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _NULL_TEXT:
        return None
    return text


def nonnegative_int(value: Any) -> int | None:
    text = text_or_none(value)
    if text is None:
        return None
    if not re.fullmatch(r"\d+", text):
        raise ValueError(f"expected non-negative integer, got {value!r}")
    return int(text)


def round_number(value: Any) -> int | None:
    text = text_or_none(value)
    if text is None:
        return None
    if text.isdigit():
        out = int(text)
    else:
        match = _ROUND_RE.fullmatch(text)
        if not match:
            raise ValueError(f"expected round like 'Round 1' or integer, got {value!r}")
        out = int(match.group(1))
    if out < 1:
        raise ValueError(f"actual round must be >= 1, got {out}")
    return out


def mmss_to_seconds(value: Any) -> int | None:
    text = text_or_none(value)
    if text is None:
        return None
    match = _MMSS_RE.fullmatch(text)
    if not match:
        raise ValueError(f"expected M:SS duration, got {value!r}")
    minutes = int(match.group(1))
    seconds = int(match.group(2))
    if seconds >= 60:
        raise ValueError(f"invalid seconds component in {value!r}")
    return minutes * 60 + seconds


def landed_attempted(value: Any) -> tuple[int, int] | None:
    text = text_or_none(value)
    if text is None:
        return None
    match = _LA_RE.fullmatch(text)
    if not match:
        raise ValueError(f"expected 'landed of attempted', got {value!r}")
    landed = int(match.group(1))
    attempted = int(match.group(2))
    if landed > attempted:
        raise ValueError(f"landed exceeds attempted in {value!r}")
    return landed, attempted


def inches_to_cm(value: Any) -> Decimal | None:
    text = text_or_none(value)
    if text is None:
        return None
    match = _INCH_RE.fullmatch(text)
    if not match:
        raise ValueError(f"expected inches, got {value!r}")
    inches = Decimal(match.group(1))
    if inches < 0:
        raise ValueError(f"negative inches not allowed: {value!r}")
    return inches * Decimal("2.54")


def feet_inches_to_cm(value: Any) -> Decimal | None:
    text = text_or_none(value)
    if text is None:
        return None
    match = _FEET_IN_RE.fullmatch(text)
    if not match:
        raise ValueError(f"expected feet/inches like 5' 11\" , got {value!r}")
    feet = Decimal(match.group(1))
    inches = Decimal(match.group(2))
    if inches >= 12:
        raise ValueError(f"inches component must be < 12: {value!r}")
    return (feet * Decimal(12) + inches) * Decimal("2.54")


def pounds(value: Any, *, zero_is_missing: bool = False) -> Decimal | None:
    text = text_or_none(value)
    if text is None:
        return None
    match = _LB_RE.fullmatch(text)
    if not match:
        raise ValueError(f"expected pounds, got {value!r}")
    try:
        out = Decimal(match.group(1))
    except InvalidOperation as exc:
        raise ValueError(f"invalid pounds value {value!r}") from exc
    if out < 0:
        raise ValueError(f"negative pounds not allowed: {value!r}")
    if zero_is_missing and out == 0:
        return None
    return out
