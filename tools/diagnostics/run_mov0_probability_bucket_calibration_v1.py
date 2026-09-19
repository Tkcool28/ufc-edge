#!/usr/bin/env python3
"""MOV0 fixed probability-bucket calibration diagnostic V1.

Consumes only the authoritative frozen MOV0 V1 Actions artifact ZIP.
It does not train, refit, recalibrate, or regenerate predictions.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

import pandas as pd

EXPECTED_ARTIFACT_SHA256 = "03e8651b2e34c656daadb2d789ba0cbf298d0dcad14ec3a08bd5d0d6ce64e866"
EXPECTED_OOF_SHA256 = {
    "MOV0_MIN": "786bee7cce8a41eed6a8e7f82fe031a592ed081a10b3a97f85afc31be61d1c57",
    "MOV0_FULL": "9d543356b157fefaabe27f7f4d1b5663536e4cf659fdf11fedd8531c4b13faa0",
}
PREFIX = "ufc-edge/ufc-edge/models/mov0/run_v1/"
BUCKETS = [
    ("< 0.30", None, 0.30),
    ("0.30–<0.40", 0.30, 0.40),
    ("0.40–<0.50", 0.40, 0.50),
    ("0.50–<0.60", 0.50, 0.60),
    ("0.60–<0.70", 0.60, 0.70),
    (">= 0.70", 0.70, None),
]

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def wilson_95(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = k / n
    den = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / den
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / den
    return center - half, center + half

def interpretation(n: int) -> str:
    if n >= 100:
        return "NORMAL"
    if n >= 50:
        return "MODERATE_UNCERTAINTY"
    if n >= 25:
        return "THIN_EXPLORATORY"
    return "INSUFFICIENT"

def summarize(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for label, lo, hi in BUCKETS:
        mask = pd.Series(True, index=df.index)
        if lo is not None:
            mask &= df["probability"] >= lo
        if hi is not None:
            mask &= df["probability"] < hi
        d = df.loc[mask].copy()
        n = len(d)
        k = int(d["target"].sum())
        low, high = wilson_95(k, n)
        mean_pred = float(d["probability"].mean())
        observed = k / n
        years = sorted(int(x) for x in d["year"].unique())
        counts = d.groupby("year").size()
        out.append({
            "bucket": label,
            "N": n,
            "standard_finish": k,
            "decision": n - k,
            "mean_predicted_finish_probability": mean_pred,
            "observed_finish_rate": observed,
            "calibration_gap": observed - mean_pred,
            "wilson_95_low": low,
            "wilson_95_high": high,
            "min_oof_year": min(years),
            "max_oof_year": max(years),
            "distinct_oof_years": len(years),
            "largest_single_year_share": float(counts.max() / n),
            "sample_size_interpretation": interpretation(n),
        })
    return pd.DataFrame(out)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact-zip", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    args = ap.parse_args()

    raw_zip = args.artifact_zip.read_bytes()
    actual_zip_sha = sha256_bytes(raw_zip)
    if actual_zip_sha != EXPECTED_ARTIFACT_SHA256:
        raise SystemExit(f"artifact SHA256 mismatch: {actual_zip_sha}")

    outputs = {}
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        manifest = json.loads(zf.read(PREFIX + "manifest.json"))
        for model, filename in (("MOV0_MIN", "oof_MOV0_MIN.csv"), ("MOV0_FULL", "oof_MOV0_FULL.csv")):
            raw = zf.read(PREFIX + filename)
            actual = sha256_bytes(raw)
            expected = EXPECTED_OOF_SHA256[model]
            if actual != expected or manifest["outputs"][filename] != expected:
                raise SystemExit(f"{model} frozen OOF identity mismatch")
            df = pd.read_csv(io.BytesIO(raw))
            if len(df) != 4260 or set(df["year"]) != set(range(2018, 2027)):
                raise SystemExit(f"{model} unexpected OOF population")
            outputs[model] = summarize(df)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs["MOV0_MIN"].to_csv(args.output_dir / "min_buckets.csv", index=False)
    outputs["MOV0_FULL"].to_csv(args.output_dir / "full_buckets.csv", index=False)

    comparison = outputs["MOV0_MIN"][["bucket","N","mean_predicted_finish_probability","observed_finish_rate","calibration_gap"]].merge(
        outputs["MOV0_FULL"][["bucket","N","mean_predicted_finish_probability","observed_finish_rate","calibration_gap"]],
        on="bucket", suffixes=("_MIN","_FULL")
    )
    comparison.to_csv(args.output_dir / "comparison.csv", index=False)
    print(json.dumps({
        "status": "MOV0_PROBABILITY_BUCKET_CALIBRATION_DIAGNOSTIC_V1_COMPLETE",
        "artifact_sha256": actual_zip_sha,
        "predictions_regenerated": False,
        "buckets": [b[0] for b in BUCKETS],
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
