#!/usr/bin/env python3
"""Map all numeric columns in the official UFC scorecard grid.

DATA PHASE ONLY. This distinguishes round-label columns (mostly 1..5) from fighter
score columns (mostly 7..10) using OCR coordinates across the existing deterministic
48-image spatial sample. It emits geometry evidence only, never canonical scores.
"""
from __future__ import annotations

import csv, json, re, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPATIAL = ROOT / "data/derived/qa/ufc_scorecard_spatial_structure_v0.csv"
IMAGES = ROOT / "data/raw/ufc_official_scorecard_images/selected_v0/images"
OUT = ROOT / "data/derived/qa/ufc_scorecard_numeric_grid_geometry_v0.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_numeric_grid_geometry_v0_latest.json"

GRID_Y_MIN, GRID_Y_MAX = 0.35, 0.67
X_TOL = 0.022
NUM_RE = re.compile(r"^(?:10|[0-9])$")
FIELDS = ["archive_key","fight_id","event_date","text","value","x","y","confidence","cluster_index","cluster_center_x","cluster_role"]


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def tsv(path: Path):
    p = subprocess.run(["tesseract",str(path),"stdout","-l","eng","--psm","11","tsv"],capture_output=True,text=True,check=False,timeout=120)
    if p.returncode != 0: raise RuntimeError(f"tesseract failed {path.name}: {p.stderr[-300:]}")
    rows=list(csv.DictReader(p.stdout.splitlines(),delimiter="\t")); w=h=0; out=[]
    for r in rows:
        try:
            level=int(r.get("level") or 0); left=int(r.get("left") or 0); top=int(r.get("top") or 0); ww=int(r.get("width") or 0); hh=int(r.get("height") or 0); conf=float(r.get("conf") or -1)
        except ValueError: continue
        if level==1: w=max(w,ww); h=max(h,hh)
        text=(r.get("text") or "").strip()
        if text and NUM_RE.fullmatch(text): out.append((text,left+ww/2,top+hh/2,conf))
    if not w or not h: raise RuntimeError(f"missing geometry {path.name}")
    return w,h,out


def cluster(xs):
    groups=[]
    for x in sorted(xs):
        if not groups or abs(x-sum(groups[-1])/len(groups[-1]))>X_TOL: groups.append([x])
        else: groups[-1].append(x)
    return groups


def main():
    spatial=read_csv(SPATIAL)
    if len(spatial)!=48: raise RuntimeError(f"sample drift {len(spatial)}")
    observations=[]
    for row in spatial:
        w,h,tokens=tsv(IMAGES/row["archive_key"])
        for text,cx,cy,conf in tokens:
            x=cx/w; y=cy/h
            if GRID_Y_MIN<=y<=GRID_Y_MAX:
                observations.append({"archive_key":row["archive_key"],"fight_id":row["candidate_fight_id"],"event_date":row["candidate_event_date"],"text":text,"value":int(text),"x":x,"y":y,"confidence":conf})
    groups=cluster([o["x"] for o in observations])
    centers=[sum(g)/len(g) for g in groups]
    stats=[]
    for i,c in enumerate(centers):
        vals=[o["value"] for o in observations if min(range(len(centers)),key=lambda j:abs(o["x"]-centers[j]))==i]
        counts=Counter(vals); score=sum(v in {7,8,9,10} for v in vals); rnd=sum(v in {1,2,3,4,5} for v in vals)
        if score>=max(5,2*rnd): role="score_candidate"
        elif rnd>=max(5,2*score): role="round_label_candidate"
        else: role="mixed_numeric"
        stats.append({"index":i,"center_x":round(c,5),"n":len(vals),"score_7_10":score,"round_1_5":rnd,"other_0_6":len(vals)-score-rnd,"role":role,"values":dict(sorted(counts.items()))})
    out=[]
    for o in observations:
        i=min(range(len(centers)),key=lambda j:abs(o["x"]-centers[j]))
        out.append({**o,"x":round(o["x"],5),"y":round(o["y"],5),"confidence":round(o["confidence"],1),"cluster_index":i,"cluster_center_x":round(centers[i],5),"cluster_role":stats[i]["role"]})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as fh:
        wr=csv.DictWriter(fh,fieldnames=FIELDS,extrasaction="raise"); wr.writeheader(); wr.writerows(out)
    score_centers=[s["center_x"] for s in stats if s["role"]=="score_candidate"]
    round_centers=[s["center_x"] for s in stats if s["role"]=="round_label_candidate"]
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"sample_images":48,"numeric_observations":len(observations),"x_cluster_tolerance":X_TOL,"clusters":stats,"score_candidate_centers":score_centers,"round_label_candidate_centers":round_centers,"output":str(OUT.relative_to(ROOT)),"decision":{"canonical_judge_round_scores_written":False,"numeric_grid_roles_audited":True,"score_and_round_columns_separable":len(score_centers)==6 and len(round_centers)>=1,"required_next":"Use only score_candidate columns, with crop widths bounded away from adjacent round-label clusters. Require multi-OCR agreement and 7..10 plausibility for strict score candidates; never infer missing cells."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True); AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"observations":len(observations),"clusters":stats,"score_centers":score_centers,"round_centers":round_centers},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())
