#!/usr/bin/env python3
"""Finalize MOV input audit with the governed reach positive control.

The established reach result (107 rows / 96.261682% observed-side win rate) was
measured on the historical M1 OOF population.  This audit deliberately does not
read M1 artifacts, so its independent helper evaluates the corresponding full
F02 binary-eligible 2015-2018 repaired population instead.  The two populations
must not be asserted identical.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REACH = "ctx__physical_size_profile__reach_cm"
ESTABLISHED_ROWS = 107
ESTABLISHED_WIN_RATE = 0.9626168224299065


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def full_f02_reach_control(old: pd.DataFrame, new: pd.DataFrame) -> dict[str, Any]:
    need = ["f1__" + REACH, "f2__" + REACH]
    if any(c not in old.columns or c not in new.columns for c in need):
        raise RuntimeError("reach positive-control columns missing")
    oi = old.assign(_id=old["fight_id"].astype(str)).set_index("_id")
    ni = new.assign(_id=new["fight_id"].astype(str)).set_index("_id")
    ids = [x for x in ni.index if x in oi.index]
    o = oi.loc[ids].reset_index(drop=True)
    n = ni.loc[ids].reset_index(drop=True)
    o["event_date"] = pd.to_datetime(o["event_date"], errors="raise")
    a0 = pd.to_numeric(o[need[0]], errors="coerce")
    b0 = pd.to_numeric(o[need[1]], errors="coerce")
    a1 = pd.to_numeric(n[need[0]], errors="coerce")
    b1 = pd.to_numeric(n[need[1]], errors="coerce")
    one = a0.notna().to_numpy() ^ b0.notna().to_numpy()
    years = o["event_date"].dt.year.to_numpy()
    repaired = one & (years >= 2015) & (years <= 2018) & a1.notna().to_numpy() & b1.notna().to_numpy()
    y = o["fighter_1_win"].astype("Int64")
    eligible = repaired & y.notna().to_numpy()
    observed_side = np.where(a0.notna().to_numpy(), 1, 2)
    yy = y.fillna(0).astype(int).to_numpy()
    observed_win = np.where(observed_side == 1, yy, 1 - yy)
    rows = int(eligible.sum())
    rate = None if rows == 0 else float(observed_win[eligible].mean())
    independently_recognized_unsafe = bool(rows >= 100 and rate is not None and rate >= 0.90)
    return {
        "feature": "historical_reach_availability",
        "established_governed_result": {
            "population": "historical M1 OOF subset from M1_MISSINGNESS_POINT_IN_TIME_SAFETY_V1",
            "rows": ESTABLISHED_ROWS,
            "observed_side_win_rate": ESTABLISHED_WIN_RATE,
            "classification": "CONFIRMED_TEMPORAL_LEAKAGE",
        },
        "independent_full_f02_helper": {
            "population": "all aligned binary-winner-eligible F02 rows in 2015-2018 with old one-sided reach missingness repaired in corrected F02",
            "rows": rows,
            "observed_side_win_rate": rate,
            "unsafe_signature_detected": independently_recognized_unsafe,
        },
        "classification": "CONFIRMED_TEMPORAL_LEAKAGE" if independently_recognized_unsafe else "CONTROL_FAILED",
        "framework_recognized_known_failure": independently_recognized_unsafe,
        "note": "The helper population is intentionally broader than the established OOF subset; exact row/rate equality is not expected or required.",
    }


def finalize(output_dir: Path, old_f02_dir: Path, new_f02_dir: Path) -> dict[str, Any]:
    old = pd.read_parquet(old_f02_dir / "winner_modeling_table.parquet")
    new = pd.read_parquet(new_f02_dir / "winner_modeling_table.parquet")
    control = full_f02_reach_control(old, new)
    if not control["framework_recognized_known_failure"]:
        raise RuntimeError(f"reach positive control failed to recognize established unsafe surface: {control}")

    control_path = output_dir / "positive_control_reach.json"
    control_path.write_text(json.dumps(control, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary_path = output_dir / "audit_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["positive_control"] = control
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    report_path = output_dir / "audit_report.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "\n## Final recommendation\n"
    section = (
        "\n## Reach positive control\n\n"
        f"- Established governed OOF result: **{ESTABLISHED_ROWS} rows**, observed/reach-known side win rate **{100*ESTABLISHED_WIN_RATE:.2f}%**, classification **CONFIRMED_TEMPORAL_LEAKAGE**.\n"
        f"- Independent full-F02 helper: **{control['independent_full_f02_helper']['rows']} rows**, observed/reach-known side win rate **{100*control['independent_full_f02_helper']['observed_side_win_rate']:.2f}%**.\n"
        "- Framework recognized the known reach-availability failure: **YES**.\n"
        "- Population note: the full-F02 helper is broader than the prior M1 OOF control, so exact equality to 107 rows is neither expected nor used as a gate.\n"
    )
    if marker not in report:
        raise RuntimeError("audit report final recommendation marker missing")
    report = report.replace(marker, section + marker, 1)
    report_path.write_text(report, encoding="utf-8")

    hashes = [
        {"file": p.name, "sha256": sha256_file(p)}
        for p in sorted(output_dir.iterdir())
        if p.is_file() and p.name not in {"manifest.json", "artifact_hashes.json"}
    ]
    (output_dir / "artifact_hashes.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "status": "MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE",
        "files": hashes,
        "inputs": summary["source_state"],
        "positive_control": control,
        "final_recommendation": summary["final_recommendation"],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return control


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--old-f02-dir", type=Path, required=True)
    p.add_argument("--new-f02-dir", type=Path, required=True)
    a = p.parse_args()
    control = finalize(a.output_dir, a.old_f02_dir, a.new_f02_dir)
    print(json.dumps(control, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
