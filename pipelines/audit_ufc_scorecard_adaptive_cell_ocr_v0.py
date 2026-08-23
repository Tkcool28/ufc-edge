#!/usr/bin/env python3
"""Audit adaptive score-cell OCR anchored to each scorecard's own round labels.

DATA PHASE ONLY. Per image, recognized round-number columns establish horizontal and
vertical grid anchors. Score cells are cropped about +/- the empirically audited score
offset. Multiple OCR/preprocessing variants must agree on a plausible 7..10 score.
No canonical judge-round scores are emitted here.
"""
from __future__ import annotations

import csv, json, re, statistics, subprocess, tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT=Path(__file__).resolve().parents[1]
SPATIAL=ROOT/"data/derived/qa/ufc_scorecard_spatial_structure_v0.csv"
ROUND_ELIG=ROOT/"data/derived/qa/ufc_scorecard_round_eligibility_v0.csv"
ORIENT=ROOT/"data/derived/qa/ufc_scorecard_fighter_column_orientation_v0.csv"
IMAGES=ROOT/"data/raw/ufc_official_scorecard_images/selected_v0/images"
OUT=ROOT/"data/derived/qa/ufc_scorecard_adaptive_cell_ocr_v0.csv"
AUDIT=ROOT/"provenance/audits/ufc_scorecard_adaptive_cell_ocr_v0_latest.json"

BLOCKS=[(0.11,0.25),(0.42,0.58),(0.74,0.90)]
SCORE_OFFSET=0.1095
X_HALF=0.026
Y_HALF=0.019
UPSCALE=8
NUM_RE=re.compile(r"^(?:10|[0-9])$")
FIELDS=["archive_key","fight_id","event_date","orientation_status","round","judge_block","source_side","round_anchor_x","round_anchor_y","score_x","variant_values","accepted_points","agreement_count","cell_status","pair_status"]


def rcsv(p):
    with Path(p).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))

def expected(text):
    if not (text or "").strip(): return []
    v=[int(x) for x in text.split(",") if x.strip()]
    if v!=list(range(1,len(v)+1)): raise RuntimeError(f"bad expected rounds {text}")
    return v

def run_tsv(path):
    p=subprocess.run(["tesseract",str(path),"stdout","-l","eng","--psm","11","tsv"],capture_output=True,text=True,check=False,timeout=120)
    if p.returncode: raise RuntimeError(f"tesseract failed {path.name}")
    rows=list(csv.DictReader(p.stdout.splitlines(),delimiter="\t")); w=h=0; out=[]
    for r in rows:
        try:
            lev=int(r.get("level") or 0); l=int(r.get("left") or 0); t=int(r.get("top") or 0); ww=int(r.get("width") or 0); hh=int(r.get("height") or 0); conf=float(r.get("conf") or -1)
        except ValueError: continue
        if lev==1:w=max(w,ww);h=max(h,hh)
        txt=(r.get("text") or "").strip()
        if txt and NUM_RE.fullmatch(txt):out.append({"v":int(txt),"x":(l+ww/2),"y":(t+hh/2),"conf":conf})
    if not w or not h:raise RuntimeError(f"no geometry {path.name}")
    for o in out:o["x"]/=w;o["y"]/=h
    return w,h,out

def anchors(tokens, rounds):
    # For each judge block and round, keep the best OCR token whose numeric value equals
    # that round in the known round-label x zone. Derive missing per-round y by median
    # across judge blocks; derive each block x by median across its observed round labels.
    obs={}
    for b,(lo,hi) in enumerate(BLOCKS,1):
        for r in rounds:
            cand=[t for t in tokens if t["v"]==r and lo<=t["x"]<=hi and 0.34<=t["y"]<=0.68]
            if cand: obs[(b,r)]=max(cand,key=lambda t:t["conf"])
    bx={b:statistics.median([t["x"] for (bb,_),t in obs.items() if bb==b]) for b in range(1,4) if any(bb==b for bb,_ in obs)}
    ry={r:statistics.median([t["y"] for (b,rr),t in obs.items() if rr==r]) for r in rounds if any(rr==r for _,rr in obs)}
    return obs,bx,ry

def crop(img,x,y,mode):
    w,h=img.size;l=max(0,int((x-X_HALF)*w));rr=min(w,int((x+X_HALF)*w));t=max(0,int((y-Y_HALF)*h));bb=min(h,int((y+Y_HALF)*h))
    c=img.crop((l,t,rr,bb)).convert("L");c=ImageOps.autocontrast(c);c=ImageEnhance.Contrast(c).enhance(2.0)
    if mode=="threshold": c=c.point(lambda p:255 if p>155 else 0)
    elif mode=="invert": c=ImageOps.invert(c)
    return c.resize((c.width*UPSCALE,c.height*UPSCALE),Image.Resampling.LANCZOS)

def ocr(c,psm):
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        c.save(f.name,"PNG")
        p=subprocess.run(["tesseract",f.name,"stdout","--psm",str(psm),"-l","eng","-c","tessedit_char_whitelist=0123456789"],capture_output=True,text=True,check=False)
    txt=re.sub(r"\s+","",p.stdout or "")
    m=re.search(r"10|[0-9]",txt); return int(m.group(0)) if m else None

def read_cell(img,x,y):
    vals=[]
    for mode in ("gray","threshold","invert"):
        c=crop(img,x,y,mode)
        for psm in (10,13): vals.append(ocr(c,psm))
    counts=Counter(v for v in vals if v in {7,8,9,10})
    if not counts:return vals,None,0
    value,n=counts.most_common(1)[0]
    # require agreement by at least two distinct OCR variants and no tied alternate
    tied=sum(1 for _,cnt in counts.items() if cnt==n)>1
    return vals,(value if n>=2 and not tied else None),n

def main():
    spatial=rcsv(SPATIAL); elig={r["fight_id"]:r for r in rcsv(ROUND_ELIG)}; orient={r["archive_key"]:r for r in rcsv(ORIENT)}
    if len(spatial)!=48 or len(elig)!=575 or len(orient)!=48:raise RuntimeError("input cardinality drift")
    out=[]; cardstats=[]; anchorstats=Counter()
    for s in spatial:
        e=elig[s["candidate_fight_id"]]; rounds=expected(e["expected_scored_rounds"])
        if not rounds: continue
        path=IMAGES/s["archive_key"]; w,h,toks=run_tsv(path); obs,bx,ry=anchors(toks,rounds)
        astat="full_anchor" if len(bx)==3 and len(ry)==len(rounds) else "partial_anchor"
        anchorstats[astat]+=1
        if astat!="full_anchor":
            cardstats.append({"key":s["archive_key"],"expected":6*len(rounds),"accepted":0,"pairs":0,"anchor":astat,"orientation":orient[s["archive_key"]]["orientation_status"]});continue
        img=Image.open(path); accepted=0; goodpairs=0; pending=[]
        for r in rounds:
            for b in range(1,4):
                for side,sign in (("left",-1),("right",1)):
                    x=bx[b]+sign*SCORE_OFFSET; vals,val,n=read_cell(img,x,ry[r]); status="accepted_7_10_consensus" if val is not None else "unresolved"
                    pending.append({"archive_key":s["archive_key"],"fight_id":s["candidate_fight_id"],"event_date":s["candidate_event_date"],"orientation_status":orient[s["archive_key"]]["orientation_status"],"round":r,"judge_block":b,"source_side":side,"round_anchor_x":round(bx[b],5),"round_anchor_y":round(ry[r],5),"score_x":round(x,5),"variant_values":json.dumps(vals,separators=(",",":")),"accepted_points":"" if val is None else val,"agreement_count":n,"cell_status":status,"pair_status":""})
                    accepted+=val is not None
        # Pair gate: two accepted scores, both 7..10, and at least one 10. This deliberately
        # excludes point-deduction / atypical pairs from the first strict candidate layer.
        bypair=defaultdict(list)
        for q in pending:bypair[(q["round"],q["judge_block"])].append(q)
        for pair in bypair.values():
            vals=[int(q["accepted_points"]) for q in pair if q["accepted_points"]!=""]
            ps="strict_pair" if len(vals)==2 and max(vals)==10 and min(vals)>=7 else "pair_unresolved_or_atypical"
            if ps=="strict_pair":goodpairs+=1
            for q in pair:q["pair_status"]=ps
        out.extend(pending); cardstats.append({"key":s["archive_key"],"expected":6*len(rounds),"accepted":accepted,"pairs":goodpairs,"expected_pairs":3*len(rounds),"anchor":astat,"orientation":orient[s["archive_key"]]["orientation_status"]})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:wr=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");wr.writeheader();wr.writerows(out)
    fullcells=sum(c["accepted"]==c["expected"] for c in cardstats if c["anchor"]=="full_anchor")
    fullpairs=sum(c.get("pairs",0)==c.get("expected_pairs",-1) for c in cardstats if c["anchor"]=="full_anchor")
    strict=sum(c["anchor"]=="full_anchor" and c["orientation"]=="supports_left_even_right_odd" and c["accepted"]==c["expected"] and c.get("pairs",0)==c.get("expected_pairs",-1) for c in cardstats)
    exp=sum(c["expected"] for c in cardstats if c["anchor"]=="full_anchor"); acc=sum(c["accepted"] for c in cardstats if c["anchor"]=="full_anchor")
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"scored_sample_cards":len(cardstats),"anchor_status_counts":dict(anchorstats),"score_offset_from_round_label":SCORE_OFFSET,"crop_half_width":X_HALF,"crop_half_height":Y_HALF,"full_anchor_expected_cells":exp,"accepted_cells":acc,"accepted_cell_fraction":round(acc/exp,6) if exp else 0,"cards_all_cells_recovered":fullcells,"cards_all_pairs_strict":fullpairs,"cards_all_cells_pairs_and_orientation_strict":strict,"output":str(OUT.relative_to(ROOT)),"decision":{"canonical_judge_round_scores_written":False,"per_image_round_label_anchors_used":True,"multi_variant_7_10_consensus_required":True,"strict_pair_requires_one_10":True,"point_deduction_or_atypical_pairs_excluded":True,"required_next":"Intersect strict adaptive-score cards with three-judge independently reconciled names. Validate source result totals before any canonical score rows."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
