#!/usr/bin/env python3
"""Build a strict derived judge-round candidate subset from audited scorecard sample.

DATA PHASE ONLY. This is not canonical materialization. Every accepted card must pass
all independent gates: round eligibility, per-image fighter orientation, adaptive
multi-variant score OCR, three reconciled judge identities, strict paired 10-point-must
scores, single source image per fight, and decision-verdict consistency.
"""
from __future__ import annotations

import csv,json,re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ADAPT=ROOT/"data/derived/qa/ufc_scorecard_adaptive_cell_ocr_v0.csv"
JUDGES=ROOT/"data/derived/qa/ufc_scorecard_judge_identity_reconciliation_v0.csv"
ORIENT=ROOT/"data/derived/qa/ufc_scorecard_fighter_column_orientation_v0.csv"
ELIG=ROOT/"data/derived/qa/ufc_scorecard_round_eligibility_v0.csv"
PLAN=ROOT/"data/derived/identity/ufc_scorecard_archive_plan_v0.csv"
FIGHTS=ROOT/"data/canonical/v0/fights.csv"
MANIFEST=ROOT/"data/raw/ufc_official_scorecard_images/selected_v0/manifest.json"
OUT=ROOT/"data/derived/qa/ufc_scorecard_judge_round_candidate_sample_v0.csv"
EXCL=ROOT/"data/derived/qa/ufc_scorecard_judge_round_candidate_sample_exclusions_v0.csv"
AUDIT=ROOT/"provenance/audits/ufc_scorecard_judge_round_candidate_sample_v0_latest.json"
FIELDS=["archive_key","image_sha256","fight_id","round","judge_block","judge_name","espn_official_ids","fighter_id","opponent_id","source_side","points","score_agreement_count","fighter_orientation_status","judge_identity_status","source_image_url"]
EXFIELDS=["archive_key","fight_id","reason","details"]

def rcsv(p):
    with Path(p).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def alt_pairs(text):return [(int(a),int(b)) for a,b in re.findall(r"\b(\d{2})\s*-\s*(\d{2})\b",text or "")]
def pairkey(a,b):return tuple(sorted((a,b)))

def main():
    adapt=rcsv(ADAPT); judges=rcsv(JUDGES); orient={r["archive_key"]:r for r in rcsv(ORIENT)}; elig={r["fight_id"]:r for r in rcsv(ELIG)}
    plan=rcsv(PLAN); fights={r["fight_id"]:r for r in rcsv(FIGHTS)}; manifest=json.loads(MANIFEST.read_text(encoding="utf-8")); meta={x["archive_key"]:x for x in manifest["images"]}
    pkey={r["archive_key"]:r for r in plan}; image_counts=Counter(r["candidate_fight_id"] for r in plan)
    bycard=defaultdict(list); jcard=defaultdict(list)
    for r in adapt:bycard[r["archive_key"]].append(r)
    for r in judges:jcard[r["archive_key"]].append(r)
    accepted=[];ex=[];cardstats=Counter();altchecks=Counter()
    for key,rows in sorted(bycard.items()):
        fid=rows[0]["fight_id"]; reasons=[]; details=[]
        if image_counts[fid]!=1:reasons.append("multi_image_fight")
        o=orient.get(key)
        if not o or o["orientation_status"]!="supports_left_even_right_odd":reasons.append("fighter_orientation_not_strict")
        expected=[int(x) for x in elig[fid]["expected_scored_rounds"].split(",") if x]
        if not expected:reasons.append("zero_expected_scored_rounds")
        expected_cells=6*len(expected)
        if len(rows)!=expected_cells:reasons.append("adaptive_card_not_full_anchor")
        if any(r["cell_status"]!="accepted_7_10_consensus" for r in rows):reasons.append("not_all_score_cells_consensus")
        if any(r["pair_status"]!="strict_pair" for r in rows):reasons.append("not_all_judge_round_pairs_strict")
        jj=jcard.get(key,[]); goodj=[r for r in jj if r["identity_status"]=="reconciled_unique_espn_judge"]
        if len(goodj)!=3 or len({r["judge_block"] for r in goodj})!=3 or len({r["espn_judge_name"] for r in goodj})!=3:reasons.append("three_distinct_judges_not_reconciled")
        if reasons:
            ex.append({"archive_key":key,"fight_id":fid,"reason":";".join(sorted(set(reasons))),"details":"pre_candidate_gate"});cardstats["excluded_pre_candidate"]+=1;continue
        judge_by_block={r["judge_block"]:r for r in goodj};left=o["left_fighter_id"];right=o["right_fighter_id"]
        cand=[]
        for r in rows:
            fighter=left if r["source_side"]=="left" else right;opp=right if fighter==left else left;j=judge_by_block[str(r["judge_block"])]
            cand.append({"archive_key":key,"image_sha256":meta[key]["sha256"],"fight_id":fid,"round":int(r["round"]),"judge_block":int(r["judge_block"]),"judge_name":j["espn_judge_name"],"espn_official_ids":j["espn_official_ids"],"fighter_id":fighter,"opponent_id":opp,"source_side":r["source_side"],"points":int(r["accepted_points"]),"score_agreement_count":int(r["agreement_count"]),"fighter_orientation_status":o["orientation_status"],"judge_identity_status":j["identity_status"],"source_image_url":pkey[key]["image_url"]})
        # Exact paired structure and decision-result gate.
        pairgroups=defaultdict(list)
        for r in cand:pairgroups[(r["round"],r["judge_name"])].append(r)
        if len(pairgroups)!=3*len(expected) or any(len(v)!=2 or {x["fighter_id"] for x in v}!={left,right} for v in pairgroups.values()):
            ex.append({"archive_key":key,"fight_id":fid,"reason":"paired_structure_failed","details":"candidate"});continue
        fight=fights[fid]
        if fight["method"]=="DECISION":
            votes=Counter()
            for jname in {r["judge_name"] for r in cand}:
                totals=Counter()
                for r in cand:
                    if r["judge_name"]==jname:totals[r["fighter_id"]]+=r["points"]
                if totals[left]>totals[right]:votes[left]+=1
                elif totals[right]>totals[left]:votes[right]+=1
                else:votes["draw"]+=1
            if fight["result"]=="win_loss" and (not fight["winner_id"] or votes[fight["winner_id"]]<2):
                ex.append({"archive_key":key,"fight_id":fid,"reason":"decision_verdict_mismatch","details":json.dumps(votes,sort_keys=True)});cardstats["excluded_verdict"]+=1;continue
            if fight["result"]=="draw" and max(votes[left],votes[right])>=2:
                ex.append({"archive_key":key,"fight_id":fid,"reason":"draw_verdict_mismatch","details":json.dumps(votes,sort_keys=True)});cardstats["excluded_verdict"]+=1;continue
        # If official page alt exposes three final cards, compare unordered total-pair multiset.
        ap=alt_pairs(pkey[key].get("image_alt") or "")
        if len(ap)==3:
            totals=[]
            for jname in sorted({r["judge_name"] for r in cand}):
                a=sum(r["points"] for r in cand if r["judge_name"]==jname and r["fighter_id"]==left);b=sum(r["points"] for r in cand if r["judge_name"]==jname and r["fighter_id"]==right);totals.append(pairkey(a,b))
            if sorted(totals)!=sorted(pairkey(a,b) for a,b in ap):
                ex.append({"archive_key":key,"fight_id":fid,"reason":"official_alt_final_totals_mismatch","details":json.dumps({"candidate":totals,"alt":ap})});altchecks["mismatch"]+=1;continue
            altchecks["match"]+=1
        else:altchecks["not_available"]+=1
        accepted.extend(cand);cardstats["accepted"]+=1
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");w.writeheader();w.writerows(accepted)
    with EXCL.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=EXFIELDS,extrasaction="raise");w.writeheader();w.writerows(ex)
    pks=[(r["fight_id"],r["round"],r["judge_name"],r["fighter_id"]) for r in accepted]
    if len(pks)!=len(set(pks)):raise RuntimeError("duplicate candidate PK")
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"sample_cards_considered":len(bycard),"accepted_cards":cardstats["accepted"],"accepted_judge_round_rows":len(accepted),"accepted_fights":len({r["fight_id"] for r in accepted}),"exclusion_rows":len(ex),"card_status_counts":dict(cardstats),"official_alt_total_checks":dict(altchecks),"output":str(OUT.relative_to(ROOT)),"exclusions":str(EXCL.relative_to(ROOT)),"decision":{"canonical_judge_round_scores_written":False,"all_candidate_rows_are_derived_qa_only":True,"all_independent_gates_required":True,"decision_verdict_consistency_required":True,"official_alt_totals_match_when_available":altchecks["mismatch"]==0,"sample_candidate_subset_can_advance":cardstats["accepted"]>0,"required_next":"Manually/audit-programmatically inspect accepted sample rows. If coherent, scale the identical strict parser gates to all 578 archived images; unresolved cards remain exclusions."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
