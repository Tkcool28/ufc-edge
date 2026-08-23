#!/usr/bin/env python3
"""Audit OCR inside score cells bounded by the printed UFC scorecard grid.

DATA PHASE ONLY. The physical line audit established 21 stable vertical rules: three
judge blocks of seven rules. Within each block, the fighter score cells are the two
outer cells (rules 0..1 and 5..6); narrow center cells carry round labels. Horizontal
row intervals are selected by OCR of those center round-label cells, never by global
coordinates. Score values require multi-variant OCR consensus and 7..10 plausibility.
No canonical score rows are emitted.
"""
from __future__ import annotations

import csv,json,re,subprocess,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

from PIL import Image,ImageEnhance,ImageOps

ROOT=Path(__file__).resolve().parents[1]
GRID=ROOT/"data/derived/qa/ufc_scorecard_grid_lines_v0.csv"
ELIG=ROOT/"data/derived/qa/ufc_scorecard_round_eligibility_v0.csv"
ORIENT=ROOT/"data/derived/qa/ufc_scorecard_fighter_column_orientation_v0.csv"
IMAGES=ROOT/"data/raw/ufc_official_scorecard_images/selected_v0/images"
OUT=ROOT/"data/derived/qa/ufc_scorecard_physical_cell_ocr_v0.csv"
AUDIT=ROOT/"provenance/audits/ufc_scorecard_physical_cell_ocr_v0_latest.json"

INSET_X=0.004
INSET_Y=0.003
UPSCALE=8
FIELDS=["archive_key","fight_id","event_date","round","judge_block","source_side","x0","x1","y0","y1","round_label_votes","score_variant_values","accepted_points","score_agreement_count","cell_status","pair_status","orientation_status"]

def rcsv(p):
    with Path(p).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def rounds(text):
    if not (text or "").strip():return []
    v=[int(x) for x in text.split(",") if x.strip()]
    if v!=list(range(1,len(v)+1)):raise RuntimeError(f"bad rounds {text}")
    return v

def crop_norm(img,x0,x1,y0,y1,mode="gray"):
    w,h=img.size;l=max(0,int((x0+INSET_X)*w));r=min(w,int((x1-INSET_X)*w));t=max(0,int((y0+INSET_Y)*h));b=min(h,int((y1-INSET_Y)*h))
    if r<=l or b<=t:raise RuntimeError("invalid crop")
    c=img.crop((l,t,r,b)).convert("L");c=ImageOps.autocontrast(c);c=ImageEnhance.Contrast(c).enhance(2.0)
    if mode=="threshold":c=c.point(lambda p:255 if p>155 else 0)
    elif mode=="invert":c=ImageOps.invert(c)
    return c.resize((max(8,c.width*UPSCALE),max(8,c.height*UPSCALE)),Image.Resampling.LANCZOS)
def ocr(c,psm,whitelist="0123456789"):
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        c.save(f.name,"PNG")
        p=subprocess.run(["tesseract",f.name,"stdout","--psm",str(psm),"-l","eng","-c",f"tessedit_char_whitelist={whitelist}"],capture_output=True,text=True,check=False)
    txt=re.sub(r"\s+","",p.stdout or "");m=re.search(r"10|[0-9]",txt);return int(m.group(0)) if m else None
def variants(img,x0,x1,y0,y1):
    vals=[]
    for mode in ("gray","threshold","invert"):
        c=crop_norm(img,x0,x1,y0,y1,mode)
        for psm in (10,13):vals.append(ocr(c,psm))
    return vals
def consensus(vals,allowed,min_votes=2):
    c=Counter(v for v in vals if v in allowed)
    if not c:return None,0
    value,n=c.most_common(1)[0]
    if n<min_votes or sum(1 for _,m in c.items() if m==n)>1:return None,n
    return value,n

def label_cell_bounds(v,b):
    # Each seven-rule judge block: central round label lies across the two narrow cells
    # bounded by local rules 2..4. Use the combined interior to improve OCR recall.
    base=(b-1)*7;return v[base+2],v[base+4]
def score_bounds(v,b,side):
    base=(b-1)*7
    return (v[base],v[base+1]) if side=="left" else (v[base+5],v[base+6])
def detect_round_rows(img,v,h,expected_rounds):
    candidates=[]
    for i in range(len(h)-1):
        if h[i+1]-h[i]<0.018:continue
        votes=Counter()
        raw=[]
        for b in range(1,4):
            x0,x1=label_cell_bounds(v,b);vals=variants(img,x0,x1,h[i],h[i+1]);raw.append(vals)
            val,n=consensus(vals,set(expected_rounds),2)
            if val is not None:votes[val]+=1
        best=None
        if votes:
            r,n=votes.most_common(1)[0]
            if n>=2 and sum(1 for _,m in votes.items() if m==n)==1:best=r
        candidates.append({"interval":i,"y0":h[i],"y1":h[i+1],"round":best,"votes":dict(votes),"raw":raw})
    chosen={}
    for r in expected_rounds:
        hits=[x for x in candidates if x["round"]==r]
        if len(hits)==1:chosen[r]=hits[0]
    # Require each expected round exactly once and vertical order to agree with round order.
    if set(chosen)!=set(expected_rounds):return {},candidates
    ordered=[chosen[r]["interval"] for r in expected_rounds]
    if ordered!=sorted(ordered):return {},candidates
    return chosen,candidates

def main():
    grid=rcsv(GRID);elig={r["fight_id"]:r for r in rcsv(ELIG)};orient={r["archive_key"]:r for r in rcsv(ORIENT)}
    if len(grid)!=48 or len(elig)!=575 or len(orient)!=48:raise RuntimeError("input cardinality drift")
    out=[];cardstats=[];rowstats=Counter()
    for g in grid:
        rs=rounds(elig[g["fight_id"]]["expected_scored_rounds"])
        if not rs:continue
        v=[float(x) for x in json.loads(g["vertical_x_json"])];h=[float(x) for x in json.loads(g["horizontal_y_json"])]
        if len(v) not in {21,22}:raise RuntimeError(f"unexpected vertical count {g['archive_key']} {len(v)}")
        # 22-line outliers need a separate resolver; do not guess which duplicate line belongs.
        if len(v)!=21:
            rowstats["vertical_outlier"]+=1;cardstats.append({"key":g["archive_key"],"expected":6*len(rs),"accepted":0,"pairs":0,"expected_pairs":3*len(rs),"rows":"vertical_outlier","orientation":orient[g["archive_key"]]["orientation_status"]});continue
        img=Image.open(IMAGES/g["archive_key"]);chosen,diagnostic=detect_round_rows(img,v,h,rs)
        if not chosen:
            rowstats["round_rows_unresolved"]+=1;cardstats.append({"key":g["archive_key"],"expected":6*len(rs),"accepted":0,"pairs":0,"expected_pairs":3*len(rs),"rows":"unresolved","orientation":orient[g["archive_key"]]["orientation_status"]});continue
        rowstats["round_rows_resolved"]+=1;pending=[];accepted=0
        for rnd in rs:
            rr=chosen[rnd];y0,y1=rr["y0"],rr["y1"]
            for b in range(1,4):
                for side in ("left","right"):
                    x0,x1=score_bounds(v,b,side);vals=variants(img,x0,x1,y0,y1);val,n=consensus(vals,{7,8,9,10},2)
                    status="accepted_7_10_consensus" if val is not None else "unresolved";accepted+=val is not None
                    pending.append({"archive_key":g["archive_key"],"fight_id":g["fight_id"],"event_date":g["event_date"],"round":rnd,"judge_block":b,"source_side":side,"x0":round(x0,5),"x1":round(x1,5),"y0":round(y0,5),"y1":round(y1,5),"round_label_votes":json.dumps(rr["votes"],sort_keys=True,separators=(",",":")),"score_variant_values":json.dumps(vals,separators=(",",":")),"accepted_points":"" if val is None else val,"score_agreement_count":n,"cell_status":status,"pair_status":"","orientation_status":orient[g["archive_key"]]["orientation_status"]})
        bypair=defaultdict(list)
        for q in pending:bypair[(q["round"],q["judge_block"])].append(q)
        goodpairs=0
        for pair in bypair.values():
            vals=[int(q["accepted_points"]) for q in pair if q["accepted_points"]!=""]
            ps="strict_pair" if len(vals)==2 and max(vals)==10 and min(vals)>=7 else "pair_unresolved_or_atypical"
            goodpairs+=ps=="strict_pair"
            for q in pair:q["pair_status"]=ps
        out.extend(pending);cardstats.append({"key":g["archive_key"],"expected":6*len(rs),"accepted":accepted,"pairs":goodpairs,"expected_pairs":3*len(rs),"rows":"resolved","orientation":orient[g["archive_key"]]["orientation_status"]})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");w.writeheader();w.writerows(out)
    resolved=[c for c in cardstats if c["rows"]=="resolved"];exp=sum(c["expected"] for c in resolved);acc=sum(c["accepted"] for c in resolved)
    allcells=sum(c["accepted"]==c["expected"] for c in resolved);allpairs=sum(c["pairs"]==c["expected_pairs"] for c in resolved);strict=sum(c["accepted"]==c["expected"] and c["pairs"]==c["expected_pairs"] and c["orientation"]=="supports_left_even_right_odd" for c in resolved)
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"scored_sample_cards":len(cardstats),"round_row_status_counts":dict(rowstats),"cards_with_resolved_round_rows":len(resolved),"resolved_cards_expected_cells":exp,"accepted_cells":acc,"accepted_cell_fraction":round(acc/exp,6) if exp else 0,"cards_all_cells_recovered":allcells,"cards_all_pairs_strict":allpairs,"cards_all_cells_pairs_and_orientation_strict":strict,"vertical_rule_topology":"3 judge blocks x 7 rules; score cells are outer intervals [0,1] and [5,6], round label spans [2,4]","output":str(OUT.relative_to(ROOT)),"decision":{"canonical_judge_round_scores_written":False,"printed_grid_cell_bounds_used":True,"round_rows_require_two_of_three_label_block_consensus":True,"score_cells_require_multi_variant_7_10_consensus":True,"strict_pair_requires_one_10":True,"safe_sample_subset_exists":strict>0,"required_next":"If strict sample subset exists, intersect it with three reconciled judges and decision/official-total checks. Otherwise stop score extraction and record official scorecards as acquired QA-only gap."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
