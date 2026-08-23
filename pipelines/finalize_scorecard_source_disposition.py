#!/usr/bin/env python3
"""Finalize official scorecards as RAW_QA_ONLY after strict promotion gates failed."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "schemas/source_precedence_v0.json"
EVIDENCE = "provenance/audits/official_scorecards_final_disposition_v0.json"


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    matches = [r for r in data.get("rules") or [] if r.get("family") == "official_judge_round_scores"]
    if len(matches) != 1:
        raise RuntimeError(f"expected one official_judge_round_scores rule, got {len(matches)}")
    rule = matches[0]
    rule["status"] = "raw_qa_only"
    rule["evidence"] = EVIDENCE
    rule["notes"] = (
        "Official UFC scorecard pages and selected immutable image bytes are acquired and identity-audited, "
        "but strict OCR/geometry promotion failed. The strongest physical-grid three-round sample recovered "
        "82/270 score cells, 0/15 complete cards, and 0 complete nine-pair cards. No canonical judge-round rows "
        "are written. Images/OCR/geometry/judge reconciliation remain QA assets only."
    )
    rule["selection_gate"] = (
        "RAW_QA_ONLY final disposition for canonical v0. Promotion requires a future extraction method that "
        "independently recovers complete judge-round pairs from verified official source images with resolved "
        "fight/fighter/judge identity and passes result/round plausibility. Existing OCR output is not canonical."
    )
    data.setdefault("evidence", {})["official_scorecards_final_disposition"] = EVIDENCE
    data["precedence_version"] = "0.4.0-draft"
    PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCORECARD_SOURCE_DISPOSITION_OK status=raw_qa_only canonical_rows=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
