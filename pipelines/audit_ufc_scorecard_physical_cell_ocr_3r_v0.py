#!/usr/bin/env python3
"""Strict physical-grid OCR audit for common three-round UFC scorecards.

DATA PHASE ONLY. This deliberately narrows scope to the physical template classes whose
round-row mapping has independent 100% support: 21 vertical rules, 7 or 9 horizontal
rules, expected rounds exactly 1..3. Five-round and outlier templates remain excluded.
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
TOPO=ROOT/"provenance/audits/ufc_scorecard_grid_row_topology_v0_latest.json"
IMAGES=ROOT/"data/raw/ufc_official_scorecard_images/selected_v0/images"
OUT=ROOT/"data/derived/qa/ufc_scorecard_physical_cell_ocr_3r_v0.csv"
AUDIT=ROOT/"provenance/audits/ufc_scorecard_physical_cell_ocr_3r_v0_latest.json"
FIELDS=["archive_key","fight_id","event_date","horizontal_line_count","round","judge_block","source_side","x0","x1","y0","y1","variant_values","accepted_points","agreement_count","cell_status","pair_status","orientation_status"]
INSET_X=.004;INSET_Y=.003;UPSCALE=9

def rcsv(p):
    with Path(p).open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def crop(img,x0,x1,y0,y1,mode):
    w,h=img.size;l=int((x0+INSET_X)*w);r=int((x1-INSET_X)*w);t=int((y0+INSET_Y)*h);b=int((y1-INSET_Y)*h)
    c=img.crop((max(0,l),max(0,t),min(w,r),min(h,b))).convert("L");c=ImageOps.autocontrast(c);c=ImageEnhance.Contrast(c).enhance(2.2)
    if mode=="threshold":c=c.point(lambda p:255 if p>155 else 0)
    return c.resize((max(8,c.width*UPSCALE),max(8,c.height*UPSCALE)),Image.Resampling.LANCZOS)
def ocr(c,psm):
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        c.save(f.name,"PNG");p=subprocess.run(["tesseract",f.name,"stdout","--psm",str(psm),"-l","eng","-c","tessedit_char_whitelist=0123456789"],capture_output=True,text=True,check=False)
    m=re.search(r"10|[0-9]",re.sub(r"\s+","",p.stdout or ""));return int(m.group(0)) if m else None
def readcell(img,x0,x1,y0,y1):
    vals=[]
    for mode in ("gray","threshold"):
        c=crop(img,x0,x1,y0,y1,mode)
        for psm in (10,13):vals.append(ocr(c,psm))
    cc=Counter(v for v in vals if v in {7,8,9,10})
    if not cc:return vals,None,0
    v,n=cc.most_common(1)[0]
    tied=sum(1 for _,m in cc.items() if m==n)>1
    return vals,(v if n>=2 and not tied else None),n
def bounds(v,b,side):
    base=(b-1)*7;return (v[base],v[base+1]) if side=="left" else (v[base+5],v[base+6])
def main():
    grid=rcsv(GRID);elig={r["fight_id"]:r for r in rcsv(ELIG)};orient={r["archive_key"]:r for r in rcsv(ORIENT)};top=json.loads(TOPO.read_text())
    # Hard proof gate for the only template/rounds this audit is allowed to touch.
    for hc in (7,9):
        for rnd in (1,2,3):
            ev=top["template_round_interval_mapping"].get(f"h{hc}_r{rnd}")
            if not ev or ev["interval"]!=rnd+1 or ev["support_fraction"]!=1.0 or ev["support_votes"]<5:
                raise RuntimeError(f"row topology proof insufficient h{hc} r{rnd}: {ev}")
    out=[];cards=[];ex=Counter()
    for g in grid:
        rs=[int(x) for x in elig[g["fight_id"]]["expected_scored_rounds"].split(",") if x]
        if rs!=[1,2,3]:ex["not_exact_three_scored_rounds"]+=1;continue
        v=[float(x) for x in json.loads(g["vertical_x_json"])];h=[float(x) for x in json.loads(g["horizontal_y_json"])]
        if len(v)!=21:ex["vertical_rule_outlier"]+=1;continue
        if len(h) not in {7,9}:ex["horizontal_template_outlier"]+=1;continue
        img=Image.open(IMAGES/g["archive_key"]);pending=[];acc=0
        for rnd in (1,2,3):
            idx=rnd+1;y0,y1=h[idx],h[idx+1]
            for b in (1,2,3):
                for side in ("left","right"):
                    x0,x1=bounds(v,b,side);vals,val,n=readcell(img,x0,x1,y0,y1);acc+=val is not None
                    pending.append({"archive_key":g["archive_key"],"fight_id":g["fight_id"],"event_date":g["event_date"],"horizontal_line_count":len(h),"round":rnd,"judge_block":b,"source_side":side,"x0":round(x0,5),"x1":round(x1,5),"y0":round(y0,5),"y1":round(y1,5),"variant_values":json.dumps(vals,separators=(",",":")),"accepted_points":"" if val is None else val,"agreement_count":n,"cell_status":"accepted_7_10_consensus" if val is not None else "unresolved","pair_status":"","orientation_status":orient[g["archive_key"]]["orientation_status"]})
        pairs=defaultdict(list)
        for q in pending:pairs[(q["round"],q["judge_block"])].append(q)
        gp=0
        for pair in pairs.values():
            vals=[int(q["accepted_points"]) for q in pair if q["accepted_points"]!=""]
            ps="strict_pair" if len(vals)==2 and max(vals)==10 and min(vals)>=7 else "pair_unresolved_or_atypical";gp+=ps=="strict_pair"
            for q in pair:q["pair_status"]=ps
        out.extend(pending);cards.append({"key":g["archive_key"],"accepted":acc,"pairs":gp,"orientation":orient[g["archive_key"]]["orientation_status"],"h":len(h)})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");w.writeheader();w.writerows(out)
    full=sum(c["accepted"]==18 for c in cards);pairs=sum(c["pairs"]==9 for c in cards);strict=sum(c["accepted"]==18 and c["pairs"]==9 and c["orientation"]=="supports_left_even_right_odd" for c in cards)
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"eligible_three_round_sample_cards":len(cards),"excluded_card_reason_counts":dict(ex),"expected_cells":18*len(cards),"accepted_cells":sum(c["accepted"] for c in cards),"accepted_cell_fraction":round(sum(c["accepted"] for c in cards)/(18*len(cards)),6) if cards else 0,"cards_all_18_cells_recovered":full,"cards_all_9_pairs_strict":pairs,"cards_all_cells_pairs_and_orientation_strict":strict,"template_card_counts":dict(Counter(str(c["h"]) for c in cards)),"output":str(OUT.relative_to(ROOT)),"decision":{"canonical_judge_round_scores_written":False,"scope_exact_three_scored_rounds_only":True,"physical_row_mapping_independently_proven":True,"physical_score_box_bounds_used":True,"five_round_cards_excluded":True,"safe_three_round_sample_subset_exists":strict>0,"required_next":"Intersect any strict three-round cards with three reconciled judges and decision/official-total consistency. If zero survive, stop score extraction and record accepted gap."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(payload,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
