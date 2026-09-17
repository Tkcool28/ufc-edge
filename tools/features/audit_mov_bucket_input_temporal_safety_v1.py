#!/usr/bin/env python3
"""Read-only MOV bucket input temporal-safety + era-comparability audit V1.

This audit intentionally does not inspect model predictions, coefficients, calibration,
loss, ROI, odds, or threshold performance.  It audits only governed feature inputs,
point-in-time availability, source/support structure, and historical comparability.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ERAS = (("2015-2018", 2015, 2018), ("2019-2022", 2019, 2022), ("2023-2024", 2023, 2024), ("2025-2026", 2025, 2026))
STRIKING = {
    "sig_strike_flow", "sig_strike_efficiency", "sig_target_mix", "sig_environment_mix",
    "knockdown_rate", "knockdown_efficiency", "finish_method_win_profile",
    "finish_method_loss_profile", "early_finish_profile", "knockdown_creation_vs_vulnerability",
}
GRAPPLING = {
    "takedown_pressure", "takedown_conversion", "control_rate",
    "submission_attempt_rate", "reversal_rate", "finish_method_win_profile",
    "finish_method_loss_profile",
}
EXPECTED_CANDIDATES = STRIKING | GRAPPLING
REACH = "ctx__physical_size_profile__reach_cm"
PRIOR = "fs__prior_fight_count__career__raw"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--f02-dir", type=Path, required=True)
    p.add_argument("--old-f02-dir", type=Path)
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--source-precedence", type=Path, required=True)
    p.add_argument("--source-field-map", type=Path, required=True)
    p.add_argument("--canonical-root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    return p.parse_args()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def era(year: int) -> str | None:
    for label, lo, hi in ERAS:
        if lo <= int(year) <= hi:
            return label
    return None


def concept_from_materialized(name: str, active: set[str]) -> str | None:
    core = name
    if core.startswith("fs__") or core.startswith("ctx__"):
        core = core.split("__", 1)[1]
    if core.startswith("mx__"):
        core = core.split("__", 1)[1]
    matches = [c for c in active if core == c or core.startswith(c + "__")]
    return max(matches, key=len) if matches else None


def paired_dimensions(frame: pd.DataFrame, concepts: set[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for c in frame.columns:
        if not c.startswith("f1__"):
            continue
        base = c[4:]
        mate = "f2__" + base
        if mate not in frame.columns:
            continue
        concept = concept_from_materialized(base, concepts)
        if concept:
            out.append({"dimension": base, "concept": concept, "f1": c, "f2": mate, "orientation": "fighter_pair"})
    for c in frame.columns:
        if not c.startswith("mx__"):
            continue
        concept = concept_from_materialized(c, concepts)
        if concept:
            out.append({"dimension": c, "concept": concept, "f1": c, "f2": "", "orientation": "matchup_oriented"})
    return sorted(out, key=lambda x: (x["concept"], x["dimension"]))


def modeled(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame.copy()
    x["event_date"] = pd.to_datetime(x["event_date"], errors="raise")
    y = x["event_date"].dt.year
    return x[x["promotion"].eq("UFC") & x["binary_winner_eligible"].eq(True) & y.between(2015, 2026)].reset_index(drop=True)


def build_career_lookup(frame: pd.DataFrame) -> dict[tuple[str, str], dict[str, float | int]]:
    use = frame[frame["promotion"].eq("UFC") & frame["binary_winner_eligible"].eq(True)].copy()
    use["event_date"] = pd.to_datetime(use["event_date"], errors="raise")
    apps: list[dict[str, Any]] = []
    for r in use[["fight_id", "event_date", "event_id", "fighter_1_id", "fighter_2_id", "winner_id"]].itertuples(index=False):
        for side in (1, 2):
            fid = str(getattr(r, f"fighter_{side}_id"))
            apps.append({"fight_id": str(r.fight_id), "event_date": r.event_date, "event_id": str(r.event_id), "fighter_id": fid, "won": int(str(r.winner_id) == fid)})
    app = pd.DataFrame(apps).sort_values(["fighter_id", "event_date", "event_id", "fight_id"]).reset_index(drop=True)
    lookup: dict[tuple[str, str], dict[str, float | int]] = {}
    for fighter, g in app.groupby("fighter_id", sort=False):
        g = g.reset_index(drop=True)
        dates = pd.to_datetime(g["event_date"]).tolist()
        wins = g["won"].astype(int).to_numpy()
        prefix = np.concatenate(([0], np.cumsum(wins)))
        n = len(g)
        for i, row in g.iterrows():
            lookup[(str(row["fight_id"]), str(fighter))] = {
                "prior_fights": i,
                "prior_wins": int(prefix[i]),
                "prior_years": 0.0 if i == 0 else float((dates[i] - dates[0]).days / 365.25),
                "future_fights": n - i - 1,
                "future_wins": int(prefix[n] - prefix[i + 1]),
                "future_years": 0.0 if i == n - 1 else float((dates[-1] - dates[i]).days / 365.25),
            }
    return lookup


def availability_metrics(frame: pd.DataFrame, f1: str, f2: str, lookup: dict[tuple[str, str], dict[str, float | int]]) -> dict[str, Any]:
    a = pd.to_numeric(frame[f1], errors="coerce")
    b = pd.to_numeric(frame[f2], errors="coerce")
    both = a.notna().to_numpy() & b.notna().to_numpy()
    one = a.notna().to_numpy() ^ b.notna().to_numpy()
    neither = a.isna().to_numpy() & b.isna().to_numpy()
    pc1 = pd.to_numeric(frame.get("f1__" + PRIOR), errors="coerce").fillna(0).to_numpy(float)
    pc2 = pd.to_numeric(frame.get("f2__" + PRIOR), errors="coerce").fillna(0).to_numpy(float)
    rows: list[dict[str, float]] = []
    target = frame["fighter_1_win"].astype(int).to_numpy()
    for i in np.flatnonzero(one):
        observed = 1 if a.notna().iat[i] else 2
        missing = 2 if observed == 1 else 1
        fight = str(frame.at[i, "fight_id"])
        oa = lookup.get((fight, str(frame.at[i, f"fighter_{observed}_id"])))
        ma = lookup.get((fight, str(frame.at[i, f"fighter_{missing}_id"])))
        if oa is None or ma is None:
            continue
        item: dict[str, float] = {"observed_won": float(target[i] if observed == 1 else 1 - target[i])}
        item["observed_prior_count"] = float(pc1[i] if observed == 1 else pc2[i])
        item["missing_prior_count"] = float(pc2[i] if observed == 1 else pc1[i])
        for period in ("prior", "future"):
            for metric in ("fights", "wins", "years"):
                key = f"{period}_{metric}"
                item[f"delta_{key}"] = float(oa[key]) - float(ma[key])
                item[f"observed_{key}"] = float(oa[key])
                item[f"missing_{key}"] = float(ma[key])
        rows.append(item)
    d: dict[str, Any] = {
        "rows": int(len(frame)), "both_observed": int(both.sum()), "one_sided": int(one.sum()), "neither": int(neither.sum()),
        "both_observed_rate": float(both.mean()), "one_sided_rate": float(one.mean()), "neither_rate": float(neither.mean()),
    }
    if rows:
        z = pd.DataFrame(rows)
        d.update({
            "diagnostic_rows": int(len(z)),
            "observed_side_win_rate": float(z["observed_won"].mean()),
            "observed_more_prior_fights_rate": float((z["delta_prior_fights"] > 0).mean()),
            "observed_more_future_fights_rate": float((z["delta_future_fights"] > 0).mean()),
            "future_minus_prior_more_fights_rate": float((z["delta_future_fights"] > 0).mean() - (z["delta_prior_fights"] > 0).mean()),
            "mean_delta_prior_fights": float(z["delta_prior_fights"].mean()),
            "mean_delta_future_fights": float(z["delta_future_fights"].mean()),
            "both_sides_have_prior_fight_rate": float(((z["observed_prior_count"] > 0) & (z["missing_prior_count"] > 0)).mean()),
            "missing_side_zero_prior_fight_rate": float((z["missing_prior_count"] <= 0).mean()),
        })
    else:
        d.update({"diagnostic_rows": 0, "observed_side_win_rate": None, "observed_more_prior_fights_rate": None, "observed_more_future_fights_rate": None, "future_minus_prior_more_fights_rate": None, "mean_delta_prior_fights": None, "mean_delta_future_fights": None, "both_sides_have_prior_fight_rate": None, "missing_side_zero_prior_fight_rate": None})
    return d


def coverage_table(frame: pd.DataFrame, f1: str, f2: str) -> list[dict[str, Any]]:
    a = pd.to_numeric(frame[f1], errors="coerce"); b = pd.to_numeric(frame[f2], errors="coerce")
    years = frame["event_date"].dt.year
    out: list[dict[str, Any]] = []
    for yr in sorted(years.unique()):
        m = years.eq(yr)
        out.append({"year": int(yr), "rows": int(m.sum()), "both_observed": int((a[m].notna() & b[m].notna()).sum()), "both_observed_rate": float((a[m].notna() & b[m].notna()).mean()), "any_observed_rate": float((a[m].notna() | b[m].notna()).mean())})
    return out


def distribution(frame: pd.DataFrame, f1: str, f2: str) -> list[dict[str, Any]]:
    years = frame["event_date"].dt.year
    out: list[dict[str, Any]] = []
    for label, lo, hi in ERAS:
        m = years.between(lo, hi)
        vals = pd.concat([pd.to_numeric(frame.loc[m, f1], errors="coerce"), pd.to_numeric(frame.loc[m, f2], errors="coerce")], ignore_index=True).dropna()
        if vals.empty:
            out.append({"era": label, "observed_values": 0})
            continue
        q = vals.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
        out.append({"era": label, "observed_values": int(len(vals)), "mean": float(vals.mean()), "median": float(vals.median()), "std": float(vals.std(ddof=0)), "p05": float(q.loc[0.05]), "p25": float(q.loc[0.25]), "p75": float(q.loc[0.75]), "p95": float(q.loc[0.95]), "zero_rate": float((vals == 0).mean())})
    return out


def source_class(concept: str, meta: dict[str, Any], era_cov: dict[str, float]) -> tuple[str, list[str]]:
    tables = set(meta.get("canonical_inputs", {}))
    notes: list[str] = []
    if "fighter_round_position" in tables:
        return "ERA_NONCOMPARABLE", ["candidate depends on coarse positional/TIP surface with explicit era-dependent coverage; exact positional duration is not canonical"]
    if "fighter_round_stats" in tables:
        notes.append("canonical v0 shared round counts use pinned Greco/UFCStats transport; official overlap is QA/fallback, not silent mixed-primary history")
        if concept == "control_rate":
            notes.append("control_sec requires exact-seconds semantics from Greco/UFCStats; coarse FightMetric control_time is explicitly rejected for exact seconds")
    else:
        notes.append("fight/result history uses governed canonical fight/event semantics")
    vals = [v for v in era_cov.values() if v is not None]
    if not vals:
        return "ERA_COMPARABILITY_UNCERTAIN", notes + ["no observed modeled-era coverage"]
    spread = max(vals) - min(vals)
    modern = era_cov.get("2025-2026", 0.0)
    old = era_cov.get("2015-2018", 0.0)
    if old < 0.50 and modern >= 0.80:
        return "ERA_COMPARABLE_WITH_LIMITATIONS", notes + ["substantial older-era coverage limitation"]
    if spread > 0.25:
        return "ERA_COMPARABLE_WITH_LIMITATIONS", notes + ["material coverage shift across standard eras"]
    return "ERA_COMPARABLE", notes


def pit_class(metric: dict[str, Any]) -> tuple[str, list[str]]:
    n = int(metric.get("diagnostic_rows") or 0)
    if n == 0:
        return "PIT_SAFE", ["no one-sided historical availability state on modeled population"]
    future = metric.get("observed_more_future_fights_rate")
    prior = metric.get("observed_more_prior_fights_rate")
    gap = metric.get("future_minus_prior_more_fights_rate")
    fd = metric.get("mean_delta_future_fights")
    pdiff = metric.get("mean_delta_prior_fights")
    target = metric.get("observed_side_win_rate")
    both_prior = metric.get("both_sides_have_prior_fight_rate")
    future_dominant = bool(n >= 30 and future is not None and prior is not None and gap is not None and fd is not None and pdiff is not None and future >= 0.70 and gap >= 0.20 and fd >= pdiff + 1.0)
    target_sep = bool(n >= 30 and target is not None and abs(float(target) - 0.5) >= 0.15)
    unresolved_support = bool(both_prior is not None and both_prior >= 0.25)
    if future_dominant and (target_sep or unresolved_support):
        return "POTENTIAL_TEMPORAL_LEAKAGE", ["one-sided availability is substantially more associated with future UFC persistence than prior fight establishment", "candidate requires support/source follow-up before permanent-bucket use"]
    if n >= 20 and unresolved_support:
        return "PIT_SAFE_WITH_LIMITATIONS", ["one-sided missingness remains after both fighters have prior UFC history; no reach-like future-dominant signature detected"]
    return "PIT_SAFE", ["availability asymmetry is absent/small or primarily consistent with pre-fight history sparsity; no reach-like future-dominant signature detected"]


def support_lookup(root: Path) -> dict[str, dict[str, tuple[list[int], list[float], list[float]]]]:
    events = pd.read_csv(root / "events.csv", low_memory=False, usecols=["event_id", "event_date"])
    fights = pd.read_csv(root / "fights.csv", low_memory=False, usecols=["fight_id", "event_id"])
    stats = pd.read_csv(root / "fighter_round_stats.csv", low_memory=False)
    required = {"fight_id", "fighter_id", "round", "sig_strikes_attempted"}
    if not required.issubset(stats.columns):
        raise RuntimeError(f"canonical fighter_round_stats missing required negative-control fields: {sorted(required - set(stats.columns))}")
    events["event_date"] = pd.to_datetime(events["event_date"], errors="raise")
    joined = stats.merge(fights, on="fight_id", how="left", validate="many_to_one").merge(events, on="event_id", how="left", validate="many_to_one")
    if joined["event_date"].isna().any():
        raise RuntimeError("round-stat support cannot be dated")
    joined = joined[pd.to_numeric(joined["round"], errors="coerce").fillna(0).gt(0)].copy()
    joined["sig_strikes_attempted"] = pd.to_numeric(joined["sig_strikes_attempted"], errors="coerce")
    out: dict[str, dict[str, tuple[list[int], list[float], list[float]]]] = {}
    for fid, g in joined.sort_values(["fighter_id", "event_date", "fight_id", "round"]).groupby("fighter_id", sort=False):
        daily = g.groupby("event_date", as_index=False).agg(rounds=("round", "count"), sig_attempts=("sig_strikes_attempted", lambda s: float(s.dropna().sum()) if s.notna().any() else 0.0))
        ords = [int(pd.Timestamp(x).toordinal()) for x in daily["event_date"]]
        rounds = np.cumsum(daily["rounds"].to_numpy(float)).tolist()
        attempts = np.cumsum(daily["sig_attempts"].to_numpy(float)).tolist()
        out[str(fid)] = {"support": (ords, rounds, attempts)}
    return out


def support_before(index: dict[str, dict[str, tuple[list[int], list[float], list[float]]]], fighter: str, cutoff: pd.Timestamp) -> tuple[float, float]:
    rec = index.get(str(fighter))
    if not rec:
        return 0.0, 0.0
    ords, rounds, attempts = rec["support"]
    i = bisect.bisect_left(ords, int(cutoff.toordinal())) - 1
    return (0.0, 0.0) if i < 0 else (float(rounds[i]), float(attempts[i]))


def negative_control(frame: pd.DataFrame, support: dict[str, Any], key: str) -> dict[str, Any]:
    wins: list[int] = []
    deltas: list[float] = []
    for r in frame.itertuples(index=False):
        cutoff = pd.Timestamp(r.event_date)
        r1, a1 = support_before(support, str(r.fighter_1_id), cutoff)
        r2, a2 = support_before(support, str(r.fighter_2_id), cutoff)
        v1, v2 = (r1, r2) if key == "prior_observed_round_count" else (a1, a2)
        if v1 == v2:
            continue
        favored = 1 if v1 > v2 else 2
        wins.append(int(r.fighter_1_win) if favored == 1 else 1 - int(r.fighter_1_win))
        deltas.append(abs(v1 - v2))
    return {"feature": key, "classification": "PIT_SAFE", "construction": "strictly prior canonical fighter_round_stats only", "active_rows": len(wins), "higher_support_side_win_rate": None if not wins else float(np.mean(wins)), "mean_absolute_support_delta": None if not deltas else float(np.mean(deltas))}


def reach_positive(old: pd.DataFrame, new: pd.DataFrame) -> dict[str, Any]:
    need = ["f1__" + REACH, "f2__" + REACH]
    if any(c not in old.columns or c not in new.columns for c in need):
        raise RuntimeError("reach positive-control columns missing")
    oi = old.assign(_id=old["fight_id"].astype(str)).set_index("_id")
    ni = new.assign(_id=new["fight_id"].astype(str)).set_index("_id")
    ids = [x for x in ni.index if x in oi.index]
    o = oi.loc[ids].reset_index(drop=True); n = ni.loc[ids].reset_index(drop=True)
    o["event_date"] = pd.to_datetime(o["event_date"], errors="raise")
    a0 = pd.to_numeric(o[need[0]], errors="coerce"); b0 = pd.to_numeric(o[need[1]], errors="coerce")
    a1 = pd.to_numeric(n[need[0]], errors="coerce"); b1 = pd.to_numeric(n[need[1]], errors="coerce")
    one = a0.notna().to_numpy() ^ b0.notna().to_numpy()
    years = o["event_date"].dt.year.to_numpy()
    fill = one & (years >= 2015) & (years <= 2018) & a1.notna().to_numpy() & b1.notna().to_numpy()
    y = o["fighter_1_win"].astype("Int64")
    elig = fill & y.notna().to_numpy()
    observed = np.where(a0.notna().to_numpy(), 1, 2)
    yy = y.fillna(0).astype(int).to_numpy()
    win = np.where(observed == 1, yy, 1 - yy)
    rate = None if not elig.any() else float(win[elig].mean())
    reproduced = bool(int(elig.sum()) == 107 and rate is not None and abs(rate - 0.9626168224299065) < 1e-12)
    return {"feature": "historical_reach_availability", "rows": int(elig.sum()), "observed_side_win_rate": rate, "expected_rows": 107, "expected_win_rate": 0.9626168224299065, "reproduced": reproduced, "classification": "CONFIRMED_TEMPORAL_LEAKAGE" if reproduced else "CONTROL_FAILED"}


def main() -> None:
    a = parse_args(); a.output_dir.mkdir(parents=True, exist_ok=True)
    table_path = a.f02_dir / "winner_modeling_table.parquet"
    if not table_path.exists():
        raise RuntimeError("authoritative corrected F02 modeling table not found")
    full = pd.read_parquet(table_path)
    frame = modeled(full)
    catalog = load_json(a.catalog); inventory = load_json(a.inventory); precedence = load_json(a.source_precedence); field_map = load_json(a.source_field_map)
    active_meta = {x["canonical_name"]: x for x in inventory["concepts"] if x.get("lifecycle_state") == "ACTIVE"}
    missing = sorted(EXPECTED_CANDIDATES - set(active_meta))
    if missing:
        raise RuntimeError(f"candidate inventory no longer matches governed active surface: {missing}")
    by_name = {x["feature_name"]: x for x in catalog["features"]}
    dims = paired_dimensions(frame, EXPECTED_CANDIDATES)
    represented = {x["concept"] for x in dims}
    if represented != EXPECTED_CANDIDATES:
        raise RuntimeError(f"F02 candidate representation drift: missing={sorted(EXPECTED_CANDIDATES-represented)} extra={sorted(represented-EXPECTED_CANDIDATES)}")
    career = build_career_lookup(full)

    inventory_rows: list[dict[str, Any]] = []
    coverage_year_rows: list[dict[str, Any]] = []
    era_dist_rows: list[dict[str, Any]] = []
    dimension_metrics: dict[str, dict[str, Any]] = {}
    concept_dimensions: dict[str, list[dict[str, str]]] = {}

    for d in dims:
        concept_dimensions.setdefault(d["concept"], []).append(d)
        if d["orientation"] == "matchup_oriented":
            dimension_metrics[d["dimension"]] = {"orientation": "matchup_oriented", "rows": len(frame)}
            continue
        m = availability_metrics(frame, d["f1"], d["f2"], career)
        dimension_metrics[d["dimension"]] = m
        for r in coverage_table(frame, d["f1"], d["f2"]):
            coverage_year_rows.append({"concept": d["concept"], "feature": d["dimension"], **r})
        for r in distribution(frame, d["f1"], d["f2"]):
            era_dist_rows.append({"concept": d["concept"], "feature": d["dimension"], **r})

    classifications: list[dict[str, Any]] = []
    for concept in sorted(EXPECTED_CANDIDATES):
        meta = active_meta[concept]; cat = by_name[concept]; cdims = concept_dimensions[concept]
        paired = [d for d in cdims if d["orientation"] == "fighter_pair"]
        year_df = pd.DataFrame([r for r in coverage_year_rows if r["concept"] == concept])
        era_cov: dict[str, float] = {}
        for label, lo, hi in ERAS:
            sub = year_df[year_df["year"].between(lo, hi)] if not year_df.empty else pd.DataFrame()
            era_cov[label] = None if sub.empty else float(sub.groupby("year").first()["both_observed_rate"].mean())
        worst_metric: dict[str, Any] = {"diagnostic_rows": 0}
        worst_name = None
        for d in paired:
            m = dimension_metrics[d["dimension"]]
            score = (m.get("future_minus_prior_more_fights_rate") or 0.0, m.get("diagnostic_rows") or 0)
            wscore = (worst_metric.get("future_minus_prior_more_fights_rate") or 0.0, worst_metric.get("diagnostic_rows") or 0)
            if score > wscore:
                worst_metric, worst_name = m, d["dimension"]
        pit, pit_notes = pit_class(worst_metric)
        era_cls, era_notes = source_class(concept, meta, era_cov)
        orientation = "MATCHUP_ORIENTED_NOT_SWAP_INVARIANT" if any(d["orientation"] == "matchup_oriented" for d in cdims) else "FIGHTER_SIDE_SWAP_SAFE_INPUT"
        if orientation.startswith("MATCHUP"):
            eligibility = "NOT_ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"
            elig_reason = "current materialization is orientation-dependent; a future symmetric definition would be a separate bucket-contract transformation"
        elif pit in {"POTENTIAL_TEMPORAL_LEAKAGE", "CONFIRMED_TEMPORAL_LEAKAGE"}:
            eligibility = "NEEDS_FOLLOWUP" if pit == "POTENTIAL_TEMPORAL_LEAKAGE" else "NOT_ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"
            elig_reason = "availability safety unresolved"
        elif era_cls == "ERA_NONCOMPARABLE":
            eligibility = "NOT_ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"; elig_reason = "known cross-era measurement noncomparability"
        elif era_cls == "ERA_COMPARABILITY_UNCERTAIN":
            eligibility = "NEEDS_FOLLOWUP"; elig_reason = "source/measurement comparability unresolved"
        elif era_cls == "ERA_COMPARABLE_WITH_LIMITATIONS" or pit == "PIT_SAFE_WITH_LIMITATIONS":
            eligibility = "ELIGIBLE_WITH_EXPLICIT_ERA_LIMITATION"; elig_reason = "usable only with explicit coverage/era/support contract"
        else:
            eligibility = "ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"; elig_reason = "PIT-safe, era-comparable, governed/reproducible input"
        family = "striking" if concept in STRIKING and concept not in GRAPPLING else "grappling" if concept in GRAPPLING and concept not in STRIKING else "shared_finish_history"
        source = "greco1899_ufcstats canonical v0 historical backbone" if "fighter_round_stats" in meta.get("canonical_inputs", {}) else "governed canonical fight/event history"
        row = {
            "feature": concept, "family": family, "feature_id": meta["feature_id"], "candidate_type": "matchup-derived" if orientation.startswith("MATCHUP") else ("rate/efficiency/composite/history"),
            "f00_definition": cat.get("exact_formula_or_definition"), "f01_implementation_source": meta.get("implementation_locations"), "f02_representation": [d["dimension"] for d in cdims],
            "raw_source_dependency": meta.get("canonical_inputs"), "value_type": cat.get("unit"), "missingness_representation": cat.get("missingness_behavior"),
            "missingness_explicit_or_implicit": "implicit null/semantic state; F02 model matrix retains nulls, audit state is QA metadata", "required_historical_support": cat.get("minimum_sample"),
            "source_system": source, "first_plausible_reliable_era": next((e for e in [x[0] for x in ERAS] if era_cov.get(e) is not None and era_cov[e] >= 0.80), None),
            "current_downstream_consumers": meta.get("consumers", []), "coverage_by_era": era_cov,
            "pit_safety": pit, "pit_basis_feature": worst_name, "pit_diagnostic": worst_metric, "pit_notes": pit_notes,
            "era_comparability": era_cls, "era_notes": era_notes, "orientation_precheck": orientation,
            "permanent_bucket_eligibility": eligibility, "eligibility_reason": elig_reason,
        }
        inventory_rows.append(row); classifications.append(row)

    support = support_lookup(a.canonical_root)
    neg1 = negative_control(frame, support, "prior_observed_round_count")
    neg2 = negative_control(frame, support, "prior_sig_strike_attempt_support")
    prior_control = {"feature": "prior_fight_count", "classification": "PIT_SAFE", "construction": "F02 strict-prior canonical fight count", "strict_prior": True}
    positive = None
    if a.old_f02_dir:
        positive = reach_positive(pd.read_parquet(a.old_f02_dir / "winner_modeling_table.parquet"), full)
        if not positive["reproduced"]:
            raise RuntimeError(f"reach positive control failed: {positive}")

    # Joint maximum safe population: at least one eligible paired striking concept and at least one eligible paired grappling concept.
    eligible = {r["feature"] for r in classifications if r["permanent_bucket_eligibility"] in {"ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT", "ELIGIBLE_WITH_EXPLICIT_ERA_LIMITATION"}}
    strike_mask = np.zeros(len(frame), dtype=bool); grapple_mask = np.zeros(len(frame), dtype=bool)
    for d in dims:
        if d["orientation"] != "fighter_pair" or d["concept"] not in eligible:
            continue
        both = pd.to_numeric(frame[d["f1"]], errors="coerce").notna().to_numpy() & pd.to_numeric(frame[d["f2"]], errors="coerce").notna().to_numpy()
        if d["concept"] in STRIKING: strike_mask |= both
        if d["concept"] in GRAPPLING: grapple_mask |= both
    joint = strike_mask & grapple_mask
    years = frame["event_date"].dt.year.to_numpy()
    joint_summary = {"modeled_rows": int(len(frame)), "striking_assignable_rows": int(strike_mask.sum()), "grappling_assignable_rows": int(grapple_mask.sum()), "joint_assignable_rows": int(joint.sum()), "joint_assignable_rate": float(joint.mean()), "by_era": {}}
    for label, lo, hi in ERAS:
        m = (years >= lo) & (years <= hi)
        joint_summary["by_era"][label] = {"rows": int(m.sum()), "joint_rows": int((m & joint).sum()), "joint_rate": None if not m.any() else float((m & joint).sum() / m.sum())}

    pd.DataFrame(coverage_year_rows).to_csv(a.output_dir / "coverage_by_year.csv", index=False)
    era_rows: list[dict[str, Any]] = []
    for r in classifications:
        for label, value in r["coverage_by_era"].items():
            era_rows.append({"feature": r["feature"], "family": r["family"], "era": label, "both_observed_rate": value})
    pd.DataFrame(era_rows).to_csv(a.output_dir / "coverage_by_era.csv", index=False)
    pd.DataFrame(era_dist_rows).to_csv(a.output_dir / "era_distribution.csv", index=False)
    (a.output_dir / "candidate_inventory.json").write_text(json.dumps(inventory_rows, indent=2, sort_keys=True, default=str) + "\n")
    (a.output_dir / "availability_prior_vs_future.json").write_text(json.dumps(dimension_metrics, indent=2, sort_keys=True, default=str) + "\n")
    class_table = pd.DataFrame([{"Feature": r["feature"], "Family": r["family"], "Source": r["source_system"], **{f"Coverage {k}": v for k, v in r["coverage_by_era"].items()}, "PIT Safety": r["pit_safety"], "Era Comparability": r["era_comparability"], "Permanent-Bucket Eligibility": r["permanent_bucket_eligibility"], "Orientation": r["orientation_precheck"], "Notes": "; ".join(r["pit_notes"] + r["era_notes"])} for r in classifications])
    class_table.to_csv(a.output_dir / "candidate_classification.csv", index=False)

    deep = [r for r in classifications if r["pit_safety"] in {"POTENTIAL_TEMPORAL_LEAKAGE", "CONFIRMED_TEMPORAL_LEAKAGE"} or r["era_comparability"] in {"ERA_COMPARABILITY_UNCERTAIN", "ERA_NONCOMPARABLE"} or r["permanent_bucket_eligibility"] == "NEEDS_FOLLOWUP"]
    (a.output_dir / "deep_dives.json").write_text(json.dumps(deep, indent=2, sort_keys=True, default=str) + "\n")

    pit_counts = pd.Series([r["pit_safety"] for r in classifications]).value_counts().to_dict()
    era_counts = pd.Series([r["era_comparability"] for r in classifications]).value_counts().to_dict()
    elig_counts = pd.Series([r["permanent_bucket_eligibility"] for r in classifications]).value_counts().to_dict()
    if any(r["pit_safety"] == "CONFIRMED_TEMPORAL_LEAKAGE" for r in classifications):
        recommendation = "MOV_BUCKET_INPUTS_REQUIRE_TARGETED_EXCLUSIONS"
    elif any(r["pit_safety"] == "POTENTIAL_TEMPORAL_LEAKAGE" or r["permanent_bucket_eligibility"] == "NEEDS_FOLLOWUP" for r in classifications):
        recommendation = "MOV_BUCKET_INPUT_AUDIT_REQUIRES_FOLLOWUP"
    elif any(r["permanent_bucket_eligibility"] == "ELIGIBLE_WITH_EXPLICIT_ERA_LIMITATION" for r in classifications):
        recommendation = "MOV_BUCKET_INPUTS_REQUIRE_ERA_RESTRICTION"
    else:
        recommendation = "MOV_BUCKET_INPUTS_SAFE_FOR_BUCKET_CONTRACT_DESIGN"

    summary = {
        "status": "MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE",
        "source_state": {"corrected_f02_predictor_logical_sha256": load_json(a.f02_dir / "summary.json").get("predictor_logical_sha256"), "corrected_f02_table_sha256": sha256_file(table_path), "feature_catalog_sha256": sha256_file(a.catalog), "feature_inventory_sha256": sha256_file(a.inventory), "source_precedence_sha256": sha256_file(a.source_precedence), "source_field_map_sha256": sha256_file(a.source_field_map)},
        "candidate_inventory": {"total": len(classifications), "striking": len(STRIKING), "grappling": len(GRAPPLING), "shared_finish_history": len(STRIKING & GRAPPLING)},
        "availability_counts": pit_counts, "era_comparability_counts": era_counts, "eligibility_counts": elig_counts,
        "eligible_features": [r["feature"] for r in classifications if r["permanent_bucket_eligibility"] == "ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"],
        "era_limited_features": [r["feature"] for r in classifications if r["permanent_bucket_eligibility"] == "ELIGIBLE_WITH_EXPLICIT_ERA_LIMITATION"],
        "ineligible_features": [{"feature": r["feature"], "reason": r["eligibility_reason"]} for r in classifications if r["permanent_bucket_eligibility"] == "NOT_ELIGIBLE_FOR_PERMANENT_BUCKET_CONTRACT"],
        "followup_features": [{"feature": r["feature"], "reason": r["eligibility_reason"]} for r in classifications if r["permanent_bucket_eligibility"] == "NEEDS_FOLLOWUP"],
        "positive_control": positive, "negative_controls": [prior_control, neg1, neg2], "joint_strike_grapple_coverage": joint_summary,
        "guardrails": {"data_changed": False, "f00_changed": False, "f01_changed": False, "f02_changed": False, "m1_changed": False, "m1_retrained": False, "calibration_buckets_created": False, "thresholds_optimized": False, "m1b_started": False, "market_odds_used": False, "roi_betting_analysis": False, "automatic_merge": False},
        "final_recommendation": recommendation,
    }
    (a.output_dir / "audit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n")

    lines = ["# UFC EDGE — MOV Bucket Input Temporal Safety + Era Comparability Audit V1", "", "`MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE`", "", "## Boundary", "", "Read-only governed-input audit. No model-performance comparison, calibration inspection, threshold optimization, DATA/F00/F01/F02 change, retraining, market data, ROI, or betting analysis.", "", "## Candidate classification", "", class_table.to_markdown(index=False), "", "## Controls", ""]
    if positive:
        lines += [f"- Positive control reach availability: reproduced={positive['reproduced']}; rows={positive['rows']}; observed-side win rate={positive['observed_side_win_rate']:.6f}."]
    lines += [f"- Negative control prior_fight_count: {prior_control['classification']}.", f"- Negative control prior observed-round count: {neg1['classification']} ({neg1['active_rows']} active rows).", f"- Negative control prior significant-strike attempt support: {neg2['classification']} ({neg2['active_rows']} active rows).", "", "## Joint strike/grapple maximum safe population", "", f"- Modeled UFC rows 2015-2026: **{joint_summary['modeled_rows']}**", f"- Joint assignable rows: **{joint_summary['joint_assignable_rows']}** ({100*joint_summary['joint_assignable_rate']:.2f}%)", "", "## Deep-dive candidates", ""]
    if deep:
        for r in deep:
            lines += [f"### `{r['feature']}`", "", f"- PIT: **{r['pit_safety']}**", f"- Era comparability: **{r['era_comparability']}**", f"- Eligibility: **{r['permanent_bucket_eligibility']}**", f"- PIT basis: `{r['pit_basis_feature']}`", f"- PIT notes: {'; '.join(r['pit_notes'])}", f"- Era notes: {'; '.join(r['era_notes'])}", ""]
    else:
        lines += ["- None.", ""]
    lines += ["## Final recommendation", "", f"`{recommendation}`", "", "Do not construct validation buckets from this workflow. Return to MASTER/PM for acceptance first."]
    (a.output_dir / "audit_report.md").write_text("\n".join(lines) + "\n")

    hashes = [{"file": p.name, "sha256": sha256_file(p)} for p in sorted(a.output_dir.iterdir()) if p.is_file() and p.name not in {"manifest.json", "artifact_hashes.json"}]
    (a.output_dir / "artifact_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    manifest = {"status": "MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE", "files": hashes, "inputs": summary["source_state"], "final_recommendation": recommendation}
    (a.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE")
    print(json.dumps({"pit": pit_counts, "era": era_counts, "eligibility": elig_counts, "recommendation": recommendation, "joint_rows": joint_summary["joint_assignable_rows"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
