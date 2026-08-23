#!/usr/bin/env python3
"""Learn score-row interval topology from printed rules + existing numeric OCR evidence.

DATA PHASE ONLY. No new OCR is run. For each scorecard, the 21 vertical printed rules
identify the three narrow round-label columns. Existing whole-image numeric OCR tokens
inside those label columns are located between detected horizontal rules. The audit
measures whether round N maps to a deterministic horizontal interval for each template
line-count class. No score values are emitted.
"""
from __future__ import annotations

import csv,json
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GRID=ROOT/"data/derived/qa/ufc_scorecard_grid_lines_v0.csv"
NUM=ROOT/"data/derived/qa/ufc_scorecard_numeric_grid_geometry_v0.csv"
ELIG=ROOT/"data/derived/qa/ufc_scorecard_round_eligibility_v0.csv"
OUT=ROOT/"data/derived/qa/ufc_scorecard_grid_row_topology_v0.csv"
AUDIT=ROOT/"provenance/audits/ufc_scorecard_grid_row_topology_v0_latest.json"
FIELDS=["archive_key","fight_id","event_date","horizontal_line_count","round","label_token_count","interval_votes_json","dominant_interval","dominant_votes","total_votes","support_fraction","mapping_status"]

def rcsv(p):
    with Path(p).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def expected(t):return [int(x) for x in (t or "").split(",") if x.strip()]
def interval(y,h):
    for i in range(len(h)-1):
        if h[i] <= y <= h[i+1]:return i
    return None
def label_ranges(v):
    if len(v)!=21:return []
    return [(v[b*7+2],v[b*7+4]) for b in range(3)]
def main():
    grid={r["archive_key"]:r for r in rcsv(GRID)};elig={r["fight_id"]:r for r in rcsv(ELIG)};nums=rcsv(NUM)
    if len(grid)!=48 or len(elig)!=575:raise RuntimeError("input cardinality drift")
    byimg=defaultdict(list)
    for n in nums:byimg[n["archive_key"]].append(n)
    out=[];aggregate=defaultdict(Counter);agg_totals=Counter()
    for key,g in sorted(grid.items()):
        rs=expected(elig[g["fight_id"]]["expected_scored_rounds"])
        if not rs:continue
        v=[float(x) for x in json.loads(g["vertical_x_json"])];h=[float(x) for x in json.loads(g["horizontal_y_json"])];ranges=label_ranges(v)
        if not ranges:
            for r in rs:out.append({"archive_key":key,"fight_id":g["fight_id"],"event_date":g["event_date"],"horizontal_line_count":len(h),"round":r,"label_token_count":0,"interval_votes_json":"{}","dominant_interval":"","dominant_votes":0,"total_votes":0,"support_fraction":0,"mapping_status":"vertical_topology_outlier"})
            continue
        for r in rs:
            votes=Counter();count=0
            for n in byimg.get(key,[]):
                if int(n["value"])!=r:continue
                x=float(n["x"]);y=float(n["y"])
                if not any(lo<=x<=hi for lo,hi in ranges):continue
                ii=interval(y,h)
                if ii is not None:votes[ii]+=1;count+=1
            dom="";dv=0;support=0;status="no_label_evidence"
            if votes:
                ii,dv=votes.most_common(1)[0];total=sum(votes.values());support=dv/total;dom=ii
                status="card_mapping_supported" if dv>=1 and support>=0.75 else "card_mapping_ambiguous"
                aggregate[(len(h),r)][ii]+=dv;agg_totals[(len(h),r)]+=total
            out.append({"archive_key":key,"fight_id":g["fight_id"],"event_date":g["event_date"],"horizontal_line_count":len(h),"round":r,"label_token_count":count,"interval_votes_json":json.dumps(dict(sorted(votes.items())),sort_keys=True),"dominant_interval":dom,"dominant_votes":dv,"total_votes":sum(votes.values()),"support_fraction":round(support,6),"mapping_status":status})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");w.writeheader();w.writerows(out)
    template={};strict=True
    for key,votes in sorted(aggregate.items()):
        hc,r=key;ii,n=votes.most_common(1)[0];total=sum(votes.values());fraction=n/total
        template[f"h{hc}_r{r}"]={"interval":ii,"support_votes":n,"total_votes":total,"support_fraction":round(fraction,6),"alternatives":dict(sorted(votes.items()))}
        if n<3 or fraction<0.9:strict=False
    # Require contiguous increasing round intervals within every observed template class.
    byhc=defaultdict(list)
    for k,v in template.items():
        hc=int(k.split("_")[0][1:]);r=int(k.split("_r")[1]);byhc[hc].append((r,v["interval"]))
    contiguous={}
    for hc,pairs in byhc.items():
        pairs=sorted(pairs);ok=all(b[1]==a[1]+1 and b[0]==a[0]+1 for a,b in zip(pairs,pairs[1:]));contiguous[str(hc)]=ok;strict &= ok
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"sample_images":len(grid),"template_round_interval_mapping":template,"template_contiguous_round_rows":contiguous,"output":str(OUT.relative_to(ROOT)),"decision":{"canonical_judge_round_scores_written":False,"printed_rule_round_topology_audited":True,"template_mapping_strict_enough":strict,"required_next":"If template mapping is strict, use its horizontal intervals with physical outer score-cell boundaries. Do not OCR round labels per cell. Quarantine line-count/template classes without strict mapping."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
