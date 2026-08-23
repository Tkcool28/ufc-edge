#!/usr/bin/env python3
"""Audit physical table-line geometry in archived UFC scorecard images.

DATA PHASE ONLY. Uses morphology on the deterministic 48-image scorecard sample to
measure whether printed score grids provide a safer cell anchor than OCR text boxes.
No score values are parsed or canonicalized.
"""
from __future__ import annotations
import csv,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import cv2, numpy as np

ROOT=Path(__file__).resolve().parents[1]
SPATIAL=ROOT/"data/derived/qa/ufc_scorecard_spatial_structure_v0.csv"
IMAGES=ROOT/"data/raw/ufc_official_scorecard_images/selected_v0/images"
OUT=ROOT/"data/derived/qa/ufc_scorecard_grid_lines_v0.csv"
AUDIT=ROOT/"provenance/audits/ufc_scorecard_grid_lines_v0_latest.json"
FIELDS=["archive_key","fight_id","event_date","width","height","vertical_line_count","horizontal_line_count","vertical_x_json","horizontal_y_json","grid_status"]

def rcsv(p):
    with Path(p).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def cluster(vals,tol):
    groups=[]
    for v in sorted(vals):
        if not groups or abs(v-sum(groups[-1])/len(groups[-1]))>tol:groups.append([v])
        else:groups[-1].append(v)
    return [sum(g)/len(g) for g in groups]
def lines(path):
    img=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
    if img is None:raise RuntimeError(f"cannot read {path}")
    h,w=img.shape
    blur=cv2.GaussianBlur(img,(3,3),0)
    bw=cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,31,13)
    # Long-rule extraction; kernels scale with image size.
    vk=cv2.getStructuringElement(cv2.MORPH_RECT,(1,max(12,h//16)))
    hk=cv2.getStructuringElement(cv2.MORPH_RECT,(max(18,w//28),1))
    vert=cv2.morphologyEx(bw,cv2.MORPH_OPEN,vk)
    horiz=cv2.morphologyEx(bw,cv2.MORPH_OPEN,hk)
    vx=[];hy=[]
    for mask,kind in ((vert,"v"),(horiz,"h")):
        cnts,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            x,y,ww,hh=cv2.boundingRect(c);cx=(x+ww/2)/w;cy=(y+hh/2)/h
            if kind=="v":
                if hh>=0.10*h and 0.20<=cy<=0.72:vx.append(cx)
            else:
                if ww>=0.12*w and 0.20<=cy<=0.72:hy.append(cy)
    return w,h,cluster(vx,0.008),cluster(hy,0.008)
def main():
    sample=rcsv(SPATIAL)
    if len(sample)!=48:raise RuntimeError(f"sample drift {len(sample)}")
    rows=[];st=Counter();vc=[];hc=[]
    for r in sample:
        w,h,vx,hy=lines(IMAGES/r["archive_key"]);vc.append(len(vx));hc.append(len(hy))
        status="rich_grid" if len(vx)>=8 and len(hy)>=4 else "partial_grid" if len(vx)>=4 and len(hy)>=2 else "grid_not_resolved"
        st[status]+=1
        rows.append({"archive_key":r["archive_key"],"fight_id":r["candidate_fight_id"],"event_date":r["candidate_event_date"],"width":w,"height":h,"vertical_line_count":len(vx),"horizontal_line_count":len(hy),"vertical_x_json":json.dumps([round(x,5) for x in vx]),"horizontal_y_json":json.dumps([round(y,5) for y in hy]),"grid_status":status})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");w.writeheader();w.writerows(rows)
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"sample_images":48,"grid_status_counts":dict(st),"vertical_line_count_distribution":dict(Counter(vc)),"horizontal_line_count_distribution":dict(Counter(hc)),"output":str(OUT.relative_to(ROOT)),"decision":{"canonical_judge_round_scores_written":False,"printed_grid_geometry_audited":True,"physical_grid_viable_for_followup":st["rich_grid"]>0,"required_next":"If rich-grid cards exist, derive cell interiors from detected rules and test digit OCR only inside bounded cells. If not, record OCR/grid extraction as insufficient and keep scorecards QA-pending."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(payload,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
