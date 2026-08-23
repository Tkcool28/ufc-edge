#!/usr/bin/env python3
"""Independent fail-closed validator for Feature Family A striking environment v0."""
from __future__ import annotations

import csv
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "features/v0/fighter_state_primitives.csv"
STATE_MANIFEST = ROOT / "features/v0/manifest.json"
FAMILY = ROOT / "features/family_a_striking_v0.json"
OUT = ROOT / "features/v0/striking_environment.csv"
MANIFEST = ROOT / "features/v0/striking_environment_manifest.json"

ID_FIELDS = [
    "target_fight_id", "target_event_id", "target_event_date", "fighter_id", "opponent_id",
    "recent3_boundary_ambiguous", "recent5_boundary_ambiguous", "observed_prior_fight_count",
    "observed_prior_loss_count", "observed_prior_ko_loss_count",
]
CAREER_OUTCOME = [
    "ko_tko_loss_per_observed_fight", "ko_tko_share_of_observed_losses", "ko_tko_win_per_observed_fight"
]
WINDOW_SUFFIXES = [
    "stat_fight_count", "sig_exposure_min", "head_exposure_min", "body_exposure_min", "leg_exposure_min",
    "distance_exposure_min", "clinch_exposure_min", "ground_exposure_min", "knockdown_exposure_min",
    "sig_attempts_per_min", "sig_landed_per_min", "sig_absorbed_per_min", "opp_sig_attempts_faced_per_min",
    "distance_attempts_per_min", "clinch_attempts_per_min", "ground_attempts_per_min",
    "exchange_pace_per_min", "sig_differential_per_min", "knockdowns_per_15",
    "knockdowns_per_sig_landed", "knockdowns_per_head_landed", "head_landed_per_min",
    "head_attempts_per_min", "head_accuracy", "body_landed_per_min", "body_attempts_per_min",
    "body_attempt_share", "leg_landed_per_min", "leg_attempts_per_min", "leg_attempt_share",
    "distance_landed_per_min", "distance_attempt_share", "clinch_landed_per_min", "clinch_attempt_share",
    "ground_landed_per_min", "ground_attempt_share", "head_attempt_share", "sig_accuracy",
    "head_absorbed_per_min", "opp_head_accuracy", "sig_defense", "head_defense",
    "knockdowns_suffered_per_15", "knockdowns_suffered_per_head_absorbed",
    "distance_strike_defense", "clinch_strike_defense_proxy", "ground_strike_defense_proxy",
]
BOUNDED_01 = {
    "head_accuracy", "body_attempt_share", "leg_attempt_share", "distance_attempt_share",
    "clinch_attempt_share", "ground_attempt_share", "head_attempt_share", "sig_accuracy",
    "opp_head_accuracy", "sig_defense", "head_defense", "distance_strike_defense",
    "clinch_strike_defense_proxy", "ground_strike_defense_proxy",
}
NONNEGATIVE = set(WINDOW_SUFFIXES) - {"sig_differential_per_min"}


def fail(msg: str) -> None:
    raise SystemExit(f"STRIKING_ENVIRONMENT_INVALID: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def d(raw: str | None) -> Decimal | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return Decimal(str(raw))
    except InvalidOperation:
        fail(f"invalid decimal {raw!r}")
    raise AssertionError


def calc_div(num: Decimal | None, den: Decimal | None, scale: Decimal = Decimal(1)) -> Decimal | None:
    if num is None or den is None or den <= 0:
        return None
    return scale * num / den


def calc_defense(landed: Decimal | None, attempted: Decimal | None) -> Decimal | None:
    ratio = calc_div(landed, attempted)
    return None if ratio is None else Decimal(1) - ratio


def calc_same_coverage_ratio(
    num: Decimal | None, den: Decimal | None, num_exp: Decimal | None, den_exp: Decimal | None
) -> Decimal | None:
    if num_exp is None or den_exp is None or num_exp <= 0 or den_exp <= 0 or num_exp != den_exp:
        return None
    return calc_div(num, den)


def close(a: Decimal | None, b: Decimal | None, tolerance: Decimal = Decimal("1e-9")) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tolerance


def require_close(actual_raw: str, expected: Decimal | None, context: str) -> None:
    actual = d(actual_raw)
    if not close(actual, expected):
        fail(f"formula mismatch {context}: actual={actual} expected={expected}")


def V(row: dict[str, str], prefix: str, suffix: str) -> Decimal | None:
    return d(row.get(f"{prefix}_{suffix}"))


def expected_window(row: dict[str, str], p: str) -> dict[str, Decimal | None]:
    stat_count = V(row, p, "stat_fight_count")
    if stat_count is None:
        return {suffix: None for suffix in WINDOW_SUFFIXES}

    sigx = V(row, p, "sig_exposure_sec")
    headx = V(row, p, "head_exposure_sec")
    bodyx = V(row, p, "body_exposure_sec")
    legx = V(row, p, "leg_exposure_sec")
    distx = V(row, p, "distance_exposure_sec")
    clinx = V(row, p, "clinch_exposure_sec")
    groundx = V(row, p, "ground_exposure_sec")
    kdx = V(row, p, "knockdown_exposure_sec")

    sigl, siga = V(row, p, "sig_landed"), V(row, p, "sig_attempted")
    osigl, osiga = V(row, p, "opp_sig_landed"), V(row, p, "opp_sig_attempted")
    headl, heada = V(row, p, "head_landed"), V(row, p, "head_attempted")
    oheadl, oheada = V(row, p, "opp_head_landed"), V(row, p, "opp_head_attempted")
    bodyl, bodya = V(row, p, "body_landed"), V(row, p, "body_attempted")
    legl, lega = V(row, p, "leg_landed"), V(row, p, "leg_attempted")
    distl, dista = V(row, p, "distance_landed"), V(row, p, "distance_attempted")
    odistl, odista = V(row, p, "opp_distance_landed"), V(row, p, "opp_distance_attempted")
    clinl, clina = V(row, p, "clinch_landed"), V(row, p, "clinch_attempted")
    oclinl, oclina = V(row, p, "opp_clinch_landed"), V(row, p, "opp_clinch_attempted")
    groundl, grounda = V(row, p, "ground_landed"), V(row, p, "ground_attempted")
    ogroundl, ogrounda = V(row, p, "opp_ground_landed"), V(row, p, "opp_ground_attempted")
    kd, okd = V(row, p, "knockdowns"), V(row, p, "knockdowns_suffered")

    per_min = Decimal(60)
    per_15 = Decimal(900)
    exchange_num = siga + osiga if siga is not None and osiga is not None else None
    differential_num = sigl - osigl if sigl is not None and osigl is not None else None
    return {
        "stat_fight_count": stat_count,
        "sig_exposure_min": calc_div(sigx, Decimal(60)),
        "head_exposure_min": calc_div(headx, Decimal(60)),
        "body_exposure_min": calc_div(bodyx, Decimal(60)),
        "leg_exposure_min": calc_div(legx, Decimal(60)),
        "distance_exposure_min": calc_div(distx, Decimal(60)),
        "clinch_exposure_min": calc_div(clinx, Decimal(60)),
        "ground_exposure_min": calc_div(groundx, Decimal(60)),
        "knockdown_exposure_min": calc_div(kdx, Decimal(60)),
        "sig_attempts_per_min": calc_div(siga, sigx, per_min),
        "sig_landed_per_min": calc_div(sigl, sigx, per_min),
        "sig_absorbed_per_min": calc_div(osigl, sigx, per_min),
        "opp_sig_attempts_faced_per_min": calc_div(osiga, sigx, per_min),
        "distance_attempts_per_min": calc_div(dista, distx, per_min),
        "clinch_attempts_per_min": calc_div(clina, clinx, per_min),
        "ground_attempts_per_min": calc_div(grounda, groundx, per_min),
        "exchange_pace_per_min": calc_div(exchange_num, sigx, per_min),
        "sig_differential_per_min": calc_div(differential_num, sigx, per_min),
        "knockdowns_per_15": calc_div(kd, kdx, per_15),
        "knockdowns_per_sig_landed": calc_same_coverage_ratio(kd, sigl, kdx, sigx),
        "knockdowns_per_head_landed": calc_same_coverage_ratio(kd, headl, kdx, headx),
        "head_landed_per_min": calc_div(headl, headx, per_min),
        "head_attempts_per_min": calc_div(heada, headx, per_min),
        "head_accuracy": calc_div(headl, heada),
        "body_landed_per_min": calc_div(bodyl, bodyx, per_min),
        "body_attempts_per_min": calc_div(bodya, bodyx, per_min),
        "body_attempt_share": calc_same_coverage_ratio(bodya, siga, bodyx, sigx),
        "leg_landed_per_min": calc_div(legl, legx, per_min),
        "leg_attempts_per_min": calc_div(lega, legx, per_min),
        "leg_attempt_share": calc_same_coverage_ratio(lega, siga, legx, sigx),
        "distance_landed_per_min": calc_div(distl, distx, per_min),
        "distance_attempt_share": calc_same_coverage_ratio(dista, siga, distx, sigx),
        "clinch_landed_per_min": calc_div(clinl, clinx, per_min),
        "clinch_attempt_share": calc_same_coverage_ratio(clina, siga, clinx, sigx),
        "ground_landed_per_min": calc_div(groundl, groundx, per_min),
        "ground_attempt_share": calc_same_coverage_ratio(grounda, siga, groundx, sigx),
        "head_attempt_share": calc_same_coverage_ratio(heada, siga, headx, sigx),
        "sig_accuracy": calc_div(sigl, siga),
        "head_absorbed_per_min": calc_div(oheadl, headx, per_min),
        "opp_head_accuracy": calc_div(oheadl, oheada),
        "sig_defense": calc_defense(osigl, osiga),
        "head_defense": calc_defense(oheadl, oheada),
        "knockdowns_suffered_per_15": calc_div(okd, kdx, per_15),
        "knockdowns_suffered_per_head_absorbed": calc_same_coverage_ratio(okd, oheadl, kdx, headx),
        "distance_strike_defense": calc_defense(odistl, odista),
        "clinch_strike_defense_proxy": calc_defense(oclinl, oclina),
        "ground_strike_defense_proxy": calc_defense(ogroundl, ogrounda),
    }


def main() -> int:
    state_manifest = json.loads(STATE_MANIFEST.read_text(encoding="utf-8"))
    family = json.loads(FAMILY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    state_rows = read_csv(STATE)
    out_rows = read_csv(OUT)

    expected_state_hash = next(
        (item.get("sha256") for item in state_manifest.get("files", []) if item.get("path") == "features/v0/fighter_state_primitives.csv"),
        None,
    )
    if expected_state_hash != sha256(STATE):
        fail("fighter-state input hash drift")
    if manifest.get("family") != "A" or manifest.get("family_version") != family.get("version"):
        fail("family manifest identity/version mismatch")
    if manifest.get("input", {}).get("sha256") != sha256(STATE):
        fail("family manifest input SHA mismatch")
    if manifest.get("input", {}).get("state_manifest_sha256") != sha256(STATE_MANIFEST):
        fail("family manifest state-manifest SHA mismatch")
    if len(out_rows) != len(state_rows):
        fail(f"row count mismatch output={len(out_rows)} state={len(state_rows)}")
    if manifest.get("counts", {}).get("rows") != len(out_rows):
        fail("manifest row count mismatch")

    windows = list(family.get("windows") or [])
    expected_fields = ID_FIELDS + CAREER_OUTCOME + [f"{p}_{s}" for p in windows for s in WINDOW_SUFFIXES]
    got_fields = list(out_rows[0]) if out_rows else []
    if got_fields != expected_fields:
        fail(f"output header mismatch missing={sorted(set(expected_fields)-set(got_fields))[:10]} extra={sorted(set(got_fields)-set(expected_fields))[:10]}")
    if manifest.get("counts", {}).get("columns") != len(expected_fields):
        fail("manifest column count mismatch")

    state_by_key = {(r["target_fight_id"], r["fighter_id"]): r for r in state_rows}
    if len(state_by_key) != len(state_rows):
        fail("duplicate fighter-state key in input")
    seen = set()
    null_counts: dict[str, int] = {}

    for out in out_rows:
        key = (out["target_fight_id"], out["fighter_id"])
        if key in seen:
            fail(f"duplicate output key {key}")
        seen.add(key)
        state = state_by_key.get(key)
        if state is None:
            fail(f"output key missing in fighter state {key}")
        for field in ID_FIELDS:
            if out[field] != state[field]:
                fail(f"inherited field mismatch {key}/{field}: {out[field]!r} != {state[field]!r}")

        prior = d(state["observed_prior_fight_count"])
        losses = d(state["observed_prior_loss_count"])
        ko_losses = d(state["observed_prior_ko_loss_count"])
        ko_wins = d(state["observed_prior_ko_win_count"])
        require_close(out["ko_tko_loss_per_observed_fight"], calc_div(ko_losses, prior), f"{key}/ko_tko_loss_per_observed_fight")
        require_close(out["ko_tko_share_of_observed_losses"], calc_div(ko_losses, losses), f"{key}/ko_tko_share_of_observed_losses")
        require_close(out["ko_tko_win_per_observed_fight"], calc_div(ko_wins, prior), f"{key}/ko_tko_win_per_observed_fight")

        for p in windows:
            expected = expected_window(state, p)
            for suffix in WINDOW_SUFFIXES:
                column = f"{p}_{suffix}"
                require_close(out[column], expected[suffix], f"{key}/{column}")
                value = d(out[column])
                if value is None:
                    null_counts[column] = null_counts.get(column, 0) + 1
                    continue
                if suffix in NONNEGATIVE and value < 0:
                    fail(f"negative nonnegative feature {key}/{column}={value}")
                if suffix in BOUNDED_01 and not (Decimal(0) <= value <= Decimal(1)):
                    fail(f"bounded feature outside [0,1] {key}/{column}={value}")

            # Exchange pace must be own attempt pace + opponent attempt pace whenever both exist.
            a = d(out[f"{p}_sig_attempts_per_min"])
            b = d(out[f"{p}_opp_sig_attempts_faced_per_min"])
            exchange = d(out[f"{p}_exchange_pace_per_min"])
            if a is not None and b is not None and not close(exchange, a + b):
                fail(f"exchange pace identity failed {key}/{p}")

            # When split-domain coverage equals overall significant-strike coverage, attempt shares
            # must add to one across head/body/leg and distance/clinch/ground.
            sx = V(state, p, "sig_exposure_sec")
            if sx is not None and sx > 0:
                anatomical_exp = [V(state, p, f"{x}_exposure_sec") for x in ("head", "body", "leg")]
                location_exp = [V(state, p, f"{x}_exposure_sec") for x in ("distance", "clinch", "ground")]
                if all(x == sx for x in anatomical_exp):
                    shares = [d(out[f"{p}_{x}_attempt_share"]) for x in ("head", "body", "leg")]
                    if all(x is not None for x in shares) and not close(sum(shares, Decimal(0)), Decimal(1), Decimal("1e-8")):
                        fail(f"head/body/leg shares do not sum to one {key}/{p}: {shares}")
                if all(x == sx for x in location_exp):
                    shares = [d(out[f"{p}_{x}_attempt_share"]) for x in ("distance", "clinch", "ground")]
                    if all(x is not None for x in shares) and not close(sum(shares, Decimal(0)), Decimal(1), Decimal("1e-8")):
                        fail(f"distance/clinch/ground shares do not sum to one {key}/{p}: {shares}")

    if set(state_by_key) != seen:
        fail("output key set does not equal fighter-state key set")

    if manifest.get("null_counts") != dict(sorted(null_counts.items())) and manifest.get("null_counts") != null_counts:
        fail("manifest null-count map mismatch")
    files = manifest.get("files") or []
    if len(files) != 1 or files[0].get("path") != "features/v0/striking_environment.csv":
        fail("manifest output file declaration mismatch")
    if files[0].get("bytes") != OUT.stat().st_size or files[0].get("sha256") != sha256(OUT):
        fail("manifest output bytes/hash mismatch")
    if manifest.get("rules") != family.get("rules"):
        fail("manifest rules drift from family contract")
    if manifest.get("deferred") != family.get("deferred_from_family_a_v0"):
        fail("manifest deferred-scope drift from family contract")

    print(
        f"STRIKING_ENVIRONMENT_OK family_version={family.get('version')} rows={len(out_rows)} "
        f"columns={len(expected_fields)} windows={','.join(windows)} sha256={sha256(OUT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
