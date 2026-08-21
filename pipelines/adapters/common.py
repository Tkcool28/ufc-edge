#!/usr/bin/env python3
"""Strict shared parsing primitives for UFC Edge provider adapters.

These helpers implement source-to-canonical *syntax* conversions only. They do not
resolve fighter identity, choose source precedence, backfill historical state, or infer
missing values. A parser returns ``None`` only for an explicitly recognized missing
marker; malformed non-missing values raise ``ValueError``.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

DEFAULT_MISSING_MARKERS = frozenset({"", "--", "---"})


def normalize_text(value: Any, *, missing_markers: frozenset[str] = DEFAULT_MISSING_MARKERS) -> str | None:
    """Return stripped text or ``None`` for a recognized missing marker."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"boolean is not text: {value!r}")
    text = str(value).strip()
    if text in missing_markers:
        return None
    return text


def parse_integral_count(value: Any) -> int | None:
    """Parse a non-negative whole-number count, including observed ``0.0`` strings."""
    text = normalize_text(value)
    if text is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        parsed = value
    elif isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            raise ValueError(f"count is not a finite integer: {value!r}")
        parsed = int(value)
    elif re.fullmatch(r"\d+", text):
        parsed = int(text)
    elif re.fullmatch(r"\d+\.0+", text):
        parsed = int(Decimal(text))
    else:
        raise ValueError(f"invalid integral count: {value!r}")
    if parsed < 0:
        raise ValueError(f"negative count: {value!r}")
    return parsed


def parse_landed_attempted(value: Any) -> tuple[int, int] | None:
    """Parse UFCStats-style ``landed of attempted`` into ``(landed, attempted)``."""
    text = normalize_text(value)
    if text is None:
        return None
    match = re.fullmatch(r"(\d+)\s+of\s+(\d+)", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"invalid landed/attempted pair: {value!r}")
    landed, attempted = (int(match.group(1)), int(match.group(2)))
    if landed > attempted:
        raise ValueError(f"landed exceeds attempted: {value!r}")
    return landed, attempted


def parse_mmss(value: Any) -> int | None:
    """Parse observed UFCStats ``M:SS`` duration into integer seconds."""
    text = normalize_text(value)
    if text is None:
        return None
    match = re.fullmatch(r"(\d+):(\d{2})", text)
    if not match:
        raise ValueError(f"invalid M:SS duration: {value!r}")
    minutes, seconds = int(match.group(1)), int(match.group(2))
    if seconds >= 60:
        raise ValueError(f"invalid seconds component: {value!r}")
    return minutes * 60 + seconds


def parse_percent_qa(value: Any) -> int | None:
    """Parse an integer percentage for QA only; canonical counts remain preferred."""
    text = normalize_text(value)
    if text is None:
        return None
    match = re.fullmatch(r"(\d{1,3})%", text)
    if not match:
        raise ValueError(f"invalid percentage: {value!r}")
    percent = int(match.group(1))
    if not 0 <= percent <= 100:
        raise ValueError(f"percentage outside [0,100]: {value!r}")
    return percent


def parse_round_number(value: Any) -> int | None:
    """Parse a positive round from either ``Round N`` or an integer-like count."""
    text = normalize_text(value)
    if text is None:
        return None
    match = re.fullmatch(r"Round\s+(\d+)", text, flags=re.IGNORECASE)
    if match:
        parsed = int(match.group(1))
    else:
        parsed = parse_integral_count(value)
        if parsed is None:
            return None
    if parsed < 1:
        raise ValueError(f"round must be >= 1: {value!r}")
    return parsed


def parse_height_cm(value: Any) -> float | None:
    """Parse observed UFCStats height like ``5' 11\"`` to centimeters."""
    text = normalize_text(value)
    if text is None:
        return None
    match = re.fullmatch(r"(\d+)\s*'\s*(\d+)\s*\"", text)
    if not match:
        raise ValueError(f"invalid UFCStats height: {value!r}")
    feet, inches = int(match.group(1)), int(match.group(2))
    if inches >= 12:
        raise ValueError(f"invalid inch component in height: {value!r}")
    total_inches = feet * 12 + inches
    return round(total_inches * 2.54, 2)


def parse_reach_cm(value: Any) -> float | None:
    """Parse observed UFCStats reach like ``66\"`` to centimeters."""
    text = normalize_text(value)
    if text is None:
        return None
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*\"", text)
    if not match:
        raise ValueError(f"invalid UFCStats reach: {value!r}")
    inches = Decimal(match.group(1))
    if inches <= 0:
        raise ValueError(f"reach must be positive: {value!r}")
    return round(float(inches * Decimal("2.54")), 2)


def parse_weight_lbs(value: Any) -> float | None:
    """Parse observed UFCStats listed weight like ``155 lbs.`` to pounds."""
    text = normalize_text(value)
    if text is None:
        return None
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*lbs?\.?", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"invalid UFCStats weight: {value!r}")
    pounds = float(Decimal(match.group(1)))
    if pounds <= 0:
        raise ValueError(f"weight must be positive: {value!r}")
    return pounds


def parse_ufcstats_date(value: Any) -> date | None:
    """Parse observed UFCStats dates like ``Jul 03, 1983``."""
    text = normalize_text(value)
    if text is None:
        return None
    try:
        return datetime.strptime(text, "%b %d, %Y").date()
    except ValueError as exc:
        raise ValueError(f"invalid UFCStats date: {value!r}") from exc
