"""Point-in-time canonical history access for F01.

Only frozen canonical tables are read. Event-date chronology is deliberately
coarse: all same-date target history is excluded and bounded recent windows
fail closed when an unresolved same-date group crosses the selection boundary.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
import csv
from pathlib import Path
from typing import Iterable


class HistoryError(ValueError):
    """Raised when canonical history cannot be interpreted safely."""


class AmbiguousWindowBoundary(HistoryError):
    """Raised when last-N selection would require inventing same-day order."""


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def as_int(value: str | None) -> int | None:
    value = _blank_to_none(value)
    return None if value is None else int(value)


def as_float(value: str | None) -> float | None:
    value = _blank_to_none(value)
    return None if value is None else float(value)


def as_bool(value: str | None) -> bool | None:
    value = _blank_to_none(value)
    if value is None:
        return None
    normalized = value.lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise HistoryError(f"invalid canonical boolean: {value!r}")


def parse_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = value.strip()
    if "T" in text:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    return date.fromisoformat(text)


def parse_cutoff(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.strip()
        if "T" not in text:
            text += "T00:00:00+00:00"
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@dataclass(frozen=True)
class FightRef:
    fight_id: str
    event_id: str
    event_date: date
    fighter_a_id: str
    fighter_b_id: str
    promotion: str | None
    weight_class: str | None
    scheduled_rounds: int | None
    title_bout: bool | None
    winner_id: str | None
    result: str | None
    method: str | None
    finish_round: int | None
    finish_time_sec: int | None

    def includes(self, fighter_id: str) -> bool:
        return fighter_id in {self.fighter_a_id, self.fighter_b_id}

    def opponent_of(self, fighter_id: str) -> str:
        if fighter_id == self.fighter_a_id:
            return self.fighter_b_id
        if fighter_id == self.fighter_b_id:
            return self.fighter_a_id
        raise HistoryError(f"fighter {fighter_id} is not in fight {self.fight_id}")


@dataclass(frozen=True)
class WindowSelection:
    window: str
    fight_ids: tuple[str, ...]
    weights: dict[str, float]


class CanonicalStore:
    """Small in-memory index over canonical v0 tables needed by F01."""

    def __init__(self, root: Path):
        self.root = root
        canonical = root / "data/canonical/v0"

        event_rows = _read_csv(canonical / "events.csv")
        self.events: dict[str, dict[str, str]] = {row["event_id"]: row for row in event_rows}
        self.fighters: dict[str, dict[str, str]] = {
            row["fighter_id"]: row for row in _read_csv(canonical / "fighters.csv")
        }

        self.fights: dict[str, FightRef] = {}
        self.fights_by_fighter: dict[str, list[FightRef]] = defaultdict(list)
        for row in _read_csv(canonical / "fights.csv"):
            event = self.events.get(row["event_id"])
            if event is None:
                raise HistoryError(f"fight {row['fight_id']} references missing event {row['event_id']}")
            ref = FightRef(
                fight_id=row["fight_id"],
                event_id=row["event_id"],
                event_date=parse_date(event["event_date"]),
                fighter_a_id=row["fighter_a_id"],
                fighter_b_id=row["fighter_b_id"],
                promotion=_blank_to_none(row.get("promotion")) or _blank_to_none(event.get("promotion")),
                weight_class=_blank_to_none(row.get("weight_class")),
                scheduled_rounds=as_int(row.get("scheduled_rounds")),
                title_bout=as_bool(row.get("title_bout")),
                winner_id=_blank_to_none(row.get("winner_id")),
                result=_blank_to_none(row.get("result")),
                method=_blank_to_none(row.get("method")),
                finish_round=as_int(row.get("finish_round")),
                finish_time_sec=as_int(row.get("finish_time_sec")),
            )
            self.fights[ref.fight_id] = ref
            self.fights_by_fighter[ref.fighter_a_id].append(ref)
            self.fights_by_fighter[ref.fighter_b_id].append(ref)

        for fighter_id in self.fights_by_fighter:
            self.fights_by_fighter[fighter_id].sort(key=lambda item: (item.event_date, item.fight_id))

        self.round_rows_by_fighter: dict[str, list[dict[str, str]]] = defaultdict(list)
        self.round_row_by_key: dict[tuple[str, str, int], dict[str, str]] = {}
        for row in _read_csv(canonical / "fighter_round_stats.csv"):
            round_no = as_int(row.get("round"))
            if round_no is None or round_no < 1:
                raise HistoryError("canonical fighter_round_stats contains non-actual round")
            key = (row["fight_id"], row["fighter_id"], round_no)
            if key in self.round_row_by_key:
                raise HistoryError(f"duplicate round-stat key {key}")
            self.round_row_by_key[key] = row
            self.round_rows_by_fighter[row["fighter_id"]].append(row)

        self.weigh_ins_by_fighter: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in _read_csv(canonical / "weigh_ins.csv"):
            self.weigh_ins_by_fighter[row["fighter_id"]].append(row)

    def require_fighter(self, fighter_id: str) -> dict[str, str]:
        try:
            return self.fighters[fighter_id]
        except KeyError as exc:
            raise HistoryError(f"unknown canonical fighter_id {fighter_id}") from exc

    def require_fight(self, fight_id: str) -> FightRef:
        try:
            return self.fights[fight_id]
        except KeyError as exc:
            raise HistoryError(f"unknown canonical fight_id {fight_id}") from exc

    @staticmethod
    def cutoff_date(prediction_as_of: str | datetime) -> date:
        return parse_cutoff(prediction_as_of).date()

    def prior_fights(self, fighter_id: str, prediction_as_of: str | datetime) -> list[FightRef]:
        """Return fights whose event date is strictly before the cutoff date.

        Same-date contests are excluded even for an intra-day cutoff because
        canonical v0 does not supply trusted bout-order chronology.
        """
        self.require_fighter(fighter_id)
        cutoff = self.cutoff_date(prediction_as_of)
        return [item for item in self.fights_by_fighter.get(fighter_id, []) if item.event_date < cutoff]

    def all_prior_fights(self, prediction_as_of: str | datetime) -> list[FightRef]:
        cutoff = self.cutoff_date(prediction_as_of)
        return [item for item in self.fights.values() if item.event_date < cutoff]

    def round_rows_for_fight(self, fighter_id: str, fight_id: str) -> list[dict[str, str]]:
        rows = [row for row in self.round_rows_by_fighter.get(fighter_id, []) if row["fight_id"] == fight_id]
        return sorted(rows, key=lambda row: int(row["round"]))

    def opponent_round_row(self, fight_id: str, fighter_id: str, round_no: int) -> dict[str, str] | None:
        fight = self.require_fight(fight_id)
        return self.round_row_by_key.get((fight_id, fight.opponent_of(fighter_id), round_no))

    def prior_scale_weight(self, fighter_id: str, prediction_as_of: str | datetime) -> dict[str, str] | None:
        prior_ids = {item.fight_id for item in self.prior_fights(fighter_id, prediction_as_of)}
        candidates = [
            row
            for row in self.weigh_ins_by_fighter.get(fighter_id, [])
            if row.get("fight_id") in prior_ids and _blank_to_none(row.get("scale_weight_lbs")) is not None
        ]
        if not candidates:
            return None

        # Linked fight date proves strict prior eligibility. Within eligible
        # history, explicit weigh-in date and attempt number define ordering;
        # the opaque observation id is used only as a deterministic final tie key.
        def key(row: dict[str, str]) -> tuple[date, date, int, str]:
            fight = self.require_fight(row["fight_id"])
            weigh_in_date = (
                parse_date(row["weigh_in_date"])
                if _blank_to_none(row.get("weigh_in_date"))
                else fight.event_date
            )
            attempt = as_int(row.get("attempt_number")) or 0
            return (fight.event_date, weigh_in_date, attempt, row.get("weigh_in_observation_id", ""))

        return max(candidates, key=key)

    def select_window(
        self,
        fights: Iterable[FightRef],
        window: str,
        prediction_as_of: str | datetime,
    ) -> WindowSelection:
        unique = {item.fight_id: item for item in fights}
        ordered = sorted(unique.values(), key=lambda item: (item.event_date, item.fight_id), reverse=True)

        if window == "career":
            ids = tuple(item.fight_id for item in reversed(ordered))
            return WindowSelection(window, ids, {fight_id: 1.0 for fight_id in ids})

        if window == "ewma_365d":
            cutoff = self.cutoff_date(prediction_as_of)
            ids = tuple(item.fight_id for item in reversed(ordered))
            weights = {
                item.fight_id: 2.0 ** (-((cutoff - item.event_date).days) / 365.0)
                for item in ordered
            }
            return WindowSelection(window, ids, weights)

        if window not in {"last3", "last5"}:
            raise HistoryError(f"unsupported contract window {window}")

        limit = 3 if window == "last3" else 5
        groups: dict[date, list[FightRef]] = defaultdict(list)
        for item in ordered:
            groups[item.event_date].append(item)

        selected: list[FightRef] = []
        for fight_date in sorted(groups, reverse=True):
            group = groups[fight_date]
            remaining = limit - len(selected)
            if remaining <= 0:
                break
            if len(group) > remaining:
                raise AmbiguousWindowBoundary(
                    f"{window} unavailable: unresolved same-date group on {fight_date} crosses boundary"
                )
            # fight_id is serialization order only after the whole tied group is
            # accepted; it never decides which tied fight enters the window.
            selected.extend(sorted(group, key=lambda item: item.fight_id))

        ids = tuple(item.fight_id for item in selected)
        return WindowSelection(window, ids, {fight_id: 1.0 for fight_id in ids})

    def fight_count_in_weight_class(self, weight_class: str, prediction_as_of: str | datetime) -> int:
        return sum(
            1
            for item in self.all_prior_fights(prediction_as_of)
            if item.weight_class == weight_class
        )
