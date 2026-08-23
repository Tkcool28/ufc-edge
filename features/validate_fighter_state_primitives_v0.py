#!/usr/bin/env python3
"""Independent fail-closed validation for fighter-state primitives v0."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/canonical/v0"
FEATURE_DIR = ROOT / "features/v0"
CONTRACT = ROOT / "features/feature_contract_v0.json"
FREEZE = ROOT / "provenance/data_phase_freeze_v0.json"
STATE = FEATURE_DIR / "fighter_state_primitives.csv"
LINEAGE = FEATURE_DIR / "fighter_state_history_lineage.csv"
MANIFEST = FEATURE_DIR / "manifest.json"


def fail(msg: str) -> None:
    raise SystemExit(f"FIGHTER_STATE_INVALID: {msg}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file(): fail(f"missing {path.relative_to(ROOT)}")
    with path.open("r", encoding="utf-8-sig", newline="") as fh: return list(csv.DictReader(fh))


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()


def dec(raw: str) -> Decimal | None:
    if raw == "": return None
    try: return Decimal(raw)
    except InvalidOperation: fail(f"invalid decimal {raw!r}")


def integer(raw: str) -> int | None:
    if raw == "": return None
    try: return int(raw)
    except ValueError: fail(f"invalid integer {raw!r}")


def boolean(raw: str) -> bool:
    if raw == "true": return True
    if raw == "false": return False
    fail(f"invalid boolean {raw!r}")
    raise AssertionError


def main() -> int:
    contract=json.loads(CONTRACT.read_text()); manifest=json.loads(MANIFEST.read_text()); freeze=json.loads(FREEZE.read_text())
    state=read_csv(STATE); lineage=read_csv(LINEAGE)
    fights={r["fight_id"]:r for r in read_csv(DATA/"fights.csv")}; events={r["event_id"]:r for r in read_csv(DATA/"events.csv")}
    event_dates={eid:date.fromisoformat(r["event_date"]) for eid,r in events.items()}; targets={fid:r for fid,r in fights.items() if r.get("promotion")=="UFC"}

    if manifest.get("feature_contract_version") != contract.get("contract_version"): fail("manifest feature contract version mismatch")
    if manifest.get("data_phase_freeze_sha256") != sha256(FREEZE): fail("manifest DATA freeze hash mismatch")
    if freeze.get("phase") != "DATA" or freeze.get("status") != "complete": fail("DATA freeze not complete")
    expected_rows=2*len(targets)
    if len(state)!=expected_rows: fail(f"state cardinality {len(state)} != {expected_rows}")
    if manifest.get("counts",{}).get("fighter_state_rows") != len(state): fail("manifest state row count mismatch")
    if manifest.get("counts",{}).get("history_lineage_rows") != len(lineage): fail("manifest lineage row count mismatch")
    if manifest.get("counts",{}).get("ufc_target_fights") != len(targets): fail("manifest UFC target fight count mismatch")
    for item in manifest.get("files") or []:
        p=ROOT/item["path"]
        if not p.is_file(): fail(f"manifest output missing {item['path']}")
        if p.stat().st_size != item["bytes"]: fail(f"byte mismatch {item['path']}")
        if sha256(p) != item["sha256"]: fail(f"hash mismatch {item['path']}")

    spec=contract["fighter_state_primitives"]; prefixes=list(spec["stat_window_prefixes"]); suffixes=list(spec["stat_primitive_suffixes"])
    expected_stat_cols={f"{p}_{s}" for p in prefixes for s in suffixes}; got_cols=set(state[0]) if state else set(); missing=sorted(expected_stat_cols-got_cols)
    if missing: fail(f"missing stat columns {missing[:10]}")

    by_target=defaultdict(list); state_by_key={}
    for row in state:
        key=(row["target_fight_id"],row["fighter_id"])
        if key in state_by_key: fail(f"duplicate state key {key}")
        state_by_key[key]=row; by_target[row["target_fight_id"]].append(row)
        fight=targets.get(row["target_fight_id"])
        if not fight: fail(f"non-UFC or missing target {row['target_fight_id']}")
        td=event_dates[fight["event_id"]]
        if row["target_event_date"] != td.isoformat(): fail(f"target date mismatch {key}")
        participants={fight["fighter_a_id"],fight["fighter_b_id"]}
        if {row["fighter_id"],row["opponent_id"]} != participants or row["fighter_id"]==row["opponent_id"]: fail(f"participant mismatch {key}")
        if row["latest_prior_event_date"]:
            pd=date.fromisoformat(row["latest_prior_event_date"])
            if pd>=td: fail(f"latest prior leaks target/future {key}")
            if integer(row["days_since_last_fight"]) != (td-pd).days: fail(f"days-since mismatch {key}")
        elif row["days_since_last_fight"]!="": fail(f"days since without prior date {key}")
        if row["latest_prior_stat_event_date"] and date.fromisoformat(row["latest_prior_stat_event_date"])>=td: fail(f"latest prior stat leaks target/future {key}")

        prior_count=integer(row["observed_prior_fight_count"]); ufc_count=integer(row["observed_prior_ufc_fight_count"]); ext_count=integer(row["observed_prior_external_fight_count"])
        if prior_count is None or ufc_count is None or ext_count is None: fail(f"null history counts {key}")
        if prior_count != ufc_count+ext_count: fail(f"promotion history counts do not sum {key}")
        result_sum=sum(integer(row[name]) or 0 for name in ["observed_prior_win_count","observed_prior_loss_count","observed_prior_draw_count","observed_prior_no_contest_count"])
        if result_sum>prior_count: fail(f"result counts exceed prior fights {key}")
        eligible=integer(row["eligible_prior_stat_fight_count"])
        if eligible is None or eligible>prior_count: fail(f"bad eligible stat count {key}")
        if integer(row["career_stat_fight_count"]) != eligible or integer(row["ewm365_stat_fight_count"]) != eligible: fail(f"career/EWM stat counts mismatch {key}")

        amb3=boolean(row["recent3_boundary_ambiguous"]); amb5=boolean(row["recent5_boundary_ambiguous"])
        for p,amb in [("recent3",amb3),("recent5",amb5)]:
            values=[row[f"{p}_{s}"] for s in suffixes]
            if amb and any(v!="" for v in values): fail(f"ambiguous {p} not null {key}")
            if not amb and any(v=="" for v in values): fail(f"non-ambiguous {p} contains null primitive {key}")

        for p in prefixes:
            if p in {"recent3","recent5"} and boolean(row[f"{p}_boundary_ambiguous"]): continue
            for s in suffixes:
                v=dec(row[f"{p}_{s}"])
                if v is None: fail(f"unexpected null {p}_{s} {key}")
                if v<0: fail(f"negative primitive {p}_{s}={v} {key}")
            for landed,attempted in [
                ("sig_landed","sig_attempted"),("opp_sig_landed","opp_sig_attempted"),("head_landed","head_attempted"),("opp_head_landed","opp_head_attempted"),
                ("body_landed","body_attempted"),("opp_body_landed","opp_body_attempted"),("leg_landed","leg_attempted"),("opp_leg_landed","opp_leg_attempted"),
                ("distance_landed","distance_attempted"),("opp_distance_landed","opp_distance_attempted"),("clinch_landed","clinch_attempted"),("opp_clinch_landed","opp_clinch_attempted"),
                ("ground_landed","ground_attempted"),("opp_ground_landed","opp_ground_attempted"),("takedowns_landed","takedowns_attempted"),("opp_takedowns_landed","opp_takedowns_attempted")]:
                if dec(row[f"{p}_{landed}"]) > dec(row[f"{p}_{attempted}"]): fail(f"landed>attempted {p}/{landed} {key}")

    if set(by_target)!=set(targets): fail("target fight key set mismatch")
    if any(len(v)!=2 for v in by_target.values()): fail("target fight without exactly two state rows")

    lineage_seen=set(); lineage_by_key=defaultdict(list)
    for row in lineage:
        pk=(row["target_fight_id"],row["fighter_id"],row["history_fight_id"])
        if pk in lineage_seen: fail(f"duplicate lineage key {pk}")
        lineage_seen.add(pk); lineage_by_key[(row["target_fight_id"],row["fighter_id"])].append(row)
        target=targets.get(row["target_fight_id"]); hist=fights.get(row["history_fight_id"])
        if not target or not hist: fail(f"lineage missing fight {pk}")
        td=event_dates[target["event_id"]]; hd=event_dates[hist["event_id"]]
        if hd>=td: fail(f"lineage cutoff violation {pk}: {hd} >= {td}")
        if integer(row["days_before_target"]) != (td-hd).days: fail(f"lineage day mismatch {pk}")
        if row["fighter_id"] not in {hist["fighter_a_id"],hist["fighter_b_id"]}: fail(f"lineage fighter not historical participant {pk}")
        if row["history_fight_id"]==row["target_fight_id"]: fail(f"target fight in lineage {pk}")
        if boolean(row["history_stat_eligible"]):
            w=dec(row["ewm365_weight"])
            if w is None or not (Decimal(0)<w<Decimal(1)): fail(f"bad EWM weight {pk}: {w}")
        elif row["ewm365_weight"]!="": fail(f"EWM weight on stat-ineligible lineage {pk}")

    amb_counts=Counter(); same_day_rows=0
    for key,row in state_by_key.items():
        lin=lineage_by_key.get(key,[])
        if len(lin)!=(integer(row["observed_prior_fight_count"]) or 0): fail(f"lineage/prior count mismatch {key}")
        stat_count=sum(boolean(x["history_stat_eligible"]) for x in lin)
        if stat_count!=(integer(row["eligible_prior_stat_fight_count"]) or 0): fail(f"lineage/stat count mismatch {key}")
        for p,n in [("recent3",3),("recent5",5)]:
            amb=boolean(row[f"{p}_boundary_ambiguous"]); selected=sum(boolean(x[f"included_{p}"]) for x in lin)
            if amb:
                amb_counts[p]+=1
                if selected: fail(f"ambiguous {p} has selected lineage {key}")
            else:
                expected=min(n,stat_count)
                if selected!=expected: fail(f"{p} selected {selected} != {expected} {key}")
                if integer(row[f"{p}_stat_fight_count"])!=expected: fail(f"{p} state count mismatch {key}")
        if (integer(row["same_day_other_fights_excluded"]) or 0)>0: same_day_rows+=1

    counts=manifest.get("counts",{})
    if counts.get("recent3_boundary_ambiguous_rows")!=amb_counts["recent3"]: fail("manifest recent3 ambiguity count mismatch")
    if counts.get("recent5_boundary_ambiguous_rows")!=amb_counts["recent5"]: fail("manifest recent5 ambiguity count mismatch")
    if counts.get("rows_with_same_day_other_fights_excluded")!=same_day_rows: fail("manifest same-day exclusion count mismatch")

    print(f"FIGHTER_STATE_OK contract={contract.get('contract_version')} targets={len(targets)} state_rows={len(state)} lineage_rows={len(lineage)} recent3_ambiguous={amb_counts['recent3']} recent5_ambiguous={amb_counts['recent5']} same_day_exclusion_rows={same_day_rows}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
