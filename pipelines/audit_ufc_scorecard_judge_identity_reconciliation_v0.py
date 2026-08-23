#!/usr/bin/env python3
"""Reconcile scorecard judge OCR candidates against acquired ESPN structured judges.

DATA PHASE ONLY. ESPN is an identity/spelling aid here, never score authority. Only
scorecard blocks already passing dual-OCR consensus are considered. A candidate is
accepted when both OCR renderings map to the same uniquely best ESPN judge name with
strong similarity and a clear margin over the runner-up.
"""
from __future__ import annotations

import csv,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import datetime,timezone
from difflib import SequenceMatcher
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BLOCKS=ROOT/"data/derived/qa/ufc_scorecard_judge_blocks_v0.csv"
ESPN=ROOT/"data/raw/espn_mma/20260820T123114Z"
OUT=ROOT/"data/derived/qa/ufc_scorecard_judge_identity_reconciliation_v0.csv"
AUDIT=ROOT/"provenance/audits/ufc_scorecard_judge_identity_reconciliation_v0_latest.json"
FIELDS=["archive_key","fight_id","event_date","judge_block","psm7_text","psm11_text","scorecard_candidate","espn_judge_name","espn_official_ids","similarity_psm7","similarity_psm11","runner_up_similarity","margin","identity_status"]

def rcsv(p):
    with Path(p).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def norm(s):
    s=unicodedata.normalize("NFKD",s or "").encode("ascii","ignore").decode("ascii").lower()
    return " ".join(re.findall(r"[a-z0-9]+",s))
def sim(a,b):return SequenceMatcher(None,norm(a),norm(b)).ratio()
def lexicon():
    ids=defaultdict(set); raw=0
    for p in sorted(ESPN.glob("*/officials.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():continue
            raw+=1; outer=json.loads(line)
            if int(outer.get("http_status") or 0)!=200:continue
            body=json.loads(outer.get("body") or "{}")
            for item in body.get("items") or []:
                if ((item.get("position") or {}).get("name") or "").lower()!="judge":continue
                name=" ".join(x for x in [item.get("firstName") or "",item.get("lastName") or ""] if x).strip()
                oid=str(item.get("id") or "").strip()
                if name and oid:ids[name].add(oid)
    bynorm=defaultdict(list)
    for name,v in ids.items():bynorm[norm(name)].append((name,sorted(v)))
    collisions={k:v for k,v in bynorm.items() if len(v)>1}
    if collisions:raise RuntimeError(f"normalized ESPN judge-name collisions: {list(collisions)[:5]}")
    return [(v[0][0],v[0][1]) for _,v in sorted(bynorm.items())],raw

def main():
    rows=rcsv(BLOCKS); lex,raw=lexicon()
    if len(rows)!=114:raise RuntimeError(f"judge block row drift {len(rows)}")
    out=[]; status=Counter(); cards=defaultdict(list)
    for r in rows:
        st="upstream_not_dual_consensus";best_name="";best_ids=[];s7=s11=runner=margin=0.0
        if r["block_status"]=="dual_ocr_consensus":
            ranked=[]
            for name,ids in lex:
                a=sim(r["psm7_text"],name);b=sim(r["psm11_text"],name);joint=min(a,b)
                ranked.append((joint,(a+b)/2,name,ids,a,b))
            ranked.sort(reverse=True)
            best=ranked[0];second=ranked[1]
            joint,avg,best_name,best_ids,s7,s11=best;runner=second[0];margin=joint-runner
            # Both OCR passes must independently fit the same structured name; a clear
            # runner-up margin prevents a near-name fuzzy correction from becoming identity.
            if s7>=0.82 and s11>=0.82 and margin>=0.07:
                st="reconciled_unique_espn_judge"
            else:
                st="fuzzy_identity_not_strict_enough";best_name="";best_ids=[]
        status[st]+=1
        rec={"archive_key":r["archive_key"],"fight_id":r["fight_id"],"event_date":r["event_date"],"judge_block":r["judge_block"],"psm7_text":r["psm7_text"],"psm11_text":r["psm11_text"],"scorecard_candidate":r["candidate_judge_name"],"espn_judge_name":best_name,"espn_official_ids":"|".join(best_ids),"similarity_psm7":round(s7,5),"similarity_psm11":round(s11,5),"runner_up_similarity":round(runner,5),"margin":round(margin,5),"identity_status":st}
        out.append(rec);cards[r["archive_key"]].append(rec)
    full=sum(len(v)==3 and all(x["identity_status"]=="reconciled_unique_espn_judge" for x in v) and len({x["espn_judge_name"] for x in v})==3 for v in cards.values())
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");w.writeheader();w.writerows(out)
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"espn_official_files":len(list(ESPN.glob("*/officials.jsonl"))),"espn_raw_response_rows":raw,"espn_distinct_judge_names":len(lex),"scorecard_judge_blocks":len(rows),"identity_status_counts":dict(status),"cards_with_three_distinct_reconciled_judges":full,"output":str(OUT.relative_to(ROOT)),"decision":{"canonical_judge_round_scores_written":False,"espn_used_as_identity_spelling_aid_only":True,"score_authority_remains_official_ufc_scorecard":True,"unique_structured_judge_identity_required":True,"three_reconciled_judge_subset_can_advance":full>0,"required_next":"Intersect cards with three distinct reconciled judges, strict fighter orientation and complete strict score pairs. Preserve ESPN official IDs as identity evidence; do not use ESPN judge totals as score authority."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
