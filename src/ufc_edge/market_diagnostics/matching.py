from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd
from .core import (MARKET_SOURCE, MARKET_TIMING_LABEL, MarketDiagnosticError,
                   decimal_odds_to_raw_implied, fixed_blend, normalize_name, proportional_no_vig)


def build_unique_name_index(fighters: pd.DataFrame) -> tuple[dict[str, str], set[str]]:
    if not {"fighter_id", "canonical_name"}.issubset(fighters):
        raise MarketDiagnosticError("canonical fighters table missing identity columns")
    grouped: dict[str, set[str]] = {}
    for row in fighters[["fighter_id", "canonical_name"]].itertuples(index=False):
        key = normalize_name(str(row.canonical_name))
        if key: grouped.setdefault(key, set()).add(str(row.fighter_id))
    ambiguous = {k for k, ids in grouped.items() if len(ids) != 1}
    return {k: next(iter(ids)) for k, ids in grouped.items() if len(ids) == 1}, ambiguous


@dataclass(frozen=True)
class PreparedMarket:
    usable: pd.DataFrame
    invalid_odds_rows: int
    unresolved_name_rows: int
    ambiguous_name_rows: int
    conflicting_duplicate_groups: int
    identical_duplicate_rows_collapsed: int


def prepare_public_market_rows(raw: pd.DataFrame, fighters: pd.DataFrame) -> PreparedMarket:
    required = {"date", "favourite", "underdog", "favourite_odds", "underdog_odds"}
    if not required.issubset(raw):
        raise MarketDiagnosticError(f"market source missing columns: {sorted(required-set(raw))}")
    names, ambiguous_names = build_unique_name_index(fighters)
    rows, bad_odds, unresolved, ambiguous = [], 0, 0, 0
    for source_row, row in raw.reset_index(drop=True).iterrows():
        fk, dk = normalize_name(str(row.favourite)), normalize_name(str(row.underdog))
        if fk in ambiguous_names or dk in ambiguous_names:
            ambiguous += 1; continue
        fav, dog = names.get(fk), names.get(dk)
        if not fav or not dog or fav == dog:
            unresolved += 1; continue
        try:
            fr, dr = decimal_odds_to_raw_implied(row.favourite_odds), decimal_odds_to_raw_implied(row.underdog_odds)
            fp, dp = proportional_no_vig(fr, dr)
        except (MarketDiagnosticError, TypeError, ValueError):
            bad_odds += 1; continue
        date = pd.to_datetime(row.date, errors="coerce")
        if pd.isna(date):
            unresolved += 1; continue
        lo, hi = sorted((fav, dog))
        rows.append({"source_row": int(source_row), "event_date": str(date.date()), "pair_lo": lo, "pair_hi": hi,
                     "favorite_id": fav, "underdog_id": dog, "favorite_decimal_odds": float(row.favourite_odds),
                     "underdog_decimal_odds": float(row.underdog_odds), "favorite_no_vig": fp, "underdog_no_vig": dp})
    frame, keep, conflicts, collapsed = pd.DataFrame(rows), [], 0, 0
    if not frame.empty:
        keys = ["event_date", "pair_lo", "pair_hi"]
        for _, group in frame.sort_values(keys + ["source_row"]).groupby(keys, sort=True):
            sig = group[["favorite_id", "underdog_id", "favorite_decimal_odds", "underdog_decimal_odds"]].drop_duplicates()
            if len(sig) > 1: conflicts += 1; continue
            collapsed += len(group) - 1; keep.append(group.iloc[0].to_dict())
    usable = pd.DataFrame(keep)
    if not usable.empty: usable = usable.sort_values(["event_date", "pair_lo", "pair_hi"]).reset_index(drop=True)
    return PreparedMarket(usable, bad_odds, unresolved, ambiguous, conflicts, collapsed)


def attach_f02_identity(oof: pd.DataFrame, f02: pd.DataFrame) -> pd.DataFrame:
    required = {"fight_id", "event_id", "event_date", "fighter_1_id", "fighter_2_id", "promotion"}
    if not required.issubset(f02):
        raise MarketDiagnosticError(f"F02 modeling table missing identity columns: {sorted(required-set(f02))}")
    ids = f02[list(required)].copy()
    if ids.fight_id.duplicated().any(): raise MarketDiagnosticError("F02 fight_id is not unique")
    merged = oof.merge(ids, on="fight_id", how="left", validate="one_to_one", suffixes=("", "_f02"))
    if merged[["fighter_1_id", "fighter_2_id", "event_id"]].isna().any().any():
        raise MarketDiagnosticError("M0 OOF fight absent from F02 identity table")
    a = pd.to_datetime(merged.event_date).dt.date.astype(str); b = pd.to_datetime(merged.event_date_f02).dt.date.astype(str)
    if not a.equals(b) or not merged.promotion.eq("UFC").all(): raise MarketDiagnosticError("M0/F02 identity mismatch")
    return merged.drop(columns=["event_date_f02"])


def match_market(oof: pd.DataFrame, market: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    if market.empty: raise MarketDiagnosticError("no usable market rows")
    oof = oof.copy(); oof["event_date"] = pd.to_datetime(oof.event_date).dt.date.astype(str)
    pairs = [sorted((str(a), str(b))) for a, b in zip(oof.fighter_1_id, oof.fighter_2_id)]
    oof["pair_lo"], oof["pair_hi"] = [x[0] for x in pairs], [x[1] for x in pairs]
    keys = ["event_date", "pair_lo", "pair_hi"]
    if oof.duplicated(keys).any() or market.duplicated(keys).any(): raise MarketDiagnosticError("ambiguous duplicate match key")
    merged = oof.merge(market, on=keys, how="left", indicator=True, validate="one_to_one")
    matched = merged[merged._merge.eq("both")].copy()
    if matched.empty: raise MarketDiagnosticError("zero M0 OOF market matches")
    p = np.where(matched.fighter_1_id.eq(matched.favorite_id), matched.favorite_no_vig,
                 np.where(matched.fighter_1_id.eq(matched.underdog_id), matched.underdog_no_vig, np.nan))
    if np.isnan(p).any(): raise MarketDiagnosticError("market orientation mismatch")
    matched["market_probability"] = p; matched["m0_probability"] = matched.logistic_probability.astype(float)
    matched["blend_probability"] = fixed_blend(matched.m0_probability, matched.market_probability)
    matched["market_source"], matched["market_timing"] = MARKET_SOURCE, MARKET_TIMING_LABEL
    matched["market_side_orientation"] = np.where(matched.fighter_1_id.eq(matched.favorite_id), "fighter_1_is_favorite", "fighter_1_is_underdog")
    matched["fold_year"] = matched.fold_id.astype(str)
    by_year = matched.groupby(pd.to_datetime(matched.event_date).dt.year).size().to_dict()
    report = {"m0_oof_rows": int(len(oof)), "matched_rows": int(len(matched)), "matched_pct": float(len(matched)/len(oof)),
              "unmatched_rows": int(len(oof)-len(matched)), "matched_by_year": {str(k): int(v) for k,v in by_year.items()},
              "earliest_matched_date": str(matched.event_date.min()), "latest_matched_date": str(matched.event_date.max()),
              "orientation_favorite_rows": int(matched.market_side_orientation.eq("fighter_1_is_favorite").sum()),
              "orientation_underdog_rows": int(matched.market_side_orientation.eq("fighter_1_is_underdog").sum())}
    cols = ["fight_id","event_id","event_date","fold_year","target","fighter_1_id","fighter_2_id","m0_probability",
            "market_probability","blend_probability","market_source","market_timing","market_side_orientation"]
    return matched[cols].sort_values(["event_date","fight_id"]).reset_index(drop=True), report
