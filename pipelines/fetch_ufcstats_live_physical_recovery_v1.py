#!/usr/bin/env python3
"""Bounded live UFCStats physical-profile recovery fetch.

Networked acquisition only. This script does not build canonical DATA.
It fetches only the governed target cohort and writes a timestamped raw snapshot.
"""
from __future__ import annotations
import argparse, csv, hashlib, html, json, re, time
from http.cookiejar import CookieJar
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import HTTPCookieProcessor, Request, build_opener

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_TARGETS=ROOT/"data/supplemental/ufcstats_live_recovery_targets_v1.csv"

def read_csv(path):
    with path.open(encoding="utf-8-sig",newline="") as fh: return list(csv.DictReader(fh))

def text_value(doc,label):
    # UFCStats puts the label inside <i> and the displayed value as sibling
    # text in the same profile-list <li>; never cross into the next row.
    items=re.findall(r'<li[^>]*b-list__box-list-item[^>]*>(.*?)</li>',doc,re.I|re.S)
    for item in items:
        m=re.search(r'<i[^>]*>\s*([^<]+?)\s*</i>(.*)$',item,re.I|re.S)
        if not m:
            continue
        item_label=html.unescape(m.group(1)).strip().rstrip(":").upper()
        if item_label != label.upper():
            continue
        v=html.unescape(re.sub(r"<[^>]+>","",m.group(2))).strip()
        return None if v in {"","--"} else v
    return None

def profile_name(doc):
    for pat in (r'b-content__title-highlight[^>]*>\s*(.*?)\s*</',r'<h2[^>]*>\s*(.*?)\s*</h2>'):
        m=re.search(pat,doc,re.I|re.S)
        if m: return html.unescape(re.sub(r"<[^>]+>","",m.group(1))).strip()
    return ""

def inches(v):
    if not v: return None
    s=v.strip().replace("″",'"')
    m=re.fullmatch(r"(\d+)\s*'\s*(\d+(?:\.\d+)?)\s*\"?",s)
    if m: return float(m.group(1))*12+float(m.group(2))
    m=re.fullmatch(r"(\d+(?:\.\d+)?)\s*\"?",s)
    return float(m.group(1)) if m else None

def fetch_live_page(url):
    jar=CookieJar()
    opener=build_opener(HTTPCookieProcessor(jar))
    headers={"User-Agent":"Mozilla/5.0 UFC-Edge governed recovery/1.0"}
    def get():
        with opener.open(Request(url,headers=headers),timeout=30) as r:
            return getattr(r,"status",200), r.read().decode("utf-8","replace")
    status, body=get()
    if "Checking your browser" in body and '"/__c"' in body:
        nonce_match=re.search(r'var nonce="([0-9a-f]+)"',body)
        diff_match=re.search(r'target=new Array\((\d+)\+1\)',body)
        if not nonce_match or not diff_match:
            raise RuntimeError("unrecognized UFCStats browser challenge")
        nonce=nonce_match.group(1); difficulty=int(diff_match.group(1))
        prefix="0"*difficulty; n=0
        while not hashlib.sha256(f"{nonce}:{n}".encode()).hexdigest().startswith(prefix):
            n+=1
        challenge=urljoin(url,"/__c")
        data=urlencode({"nonce":nonce,"n":n}).encode()
        req=Request(challenge,data=data,headers={**headers,"Content-Type":"application/x-www-form-urlencoded","Referer":url})
        with opener.open(req,timeout=30) as r:
            r.read()
        status, body=get()
    return status, body

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--targets",type=Path,default=DEFAULT_TARGETS)
    ap.add_argument("--out-root",type=Path,default=ROOT/"data/raw/ufcstats_live_recovery")
    ap.add_argument("--snapshot-id")
    args=ap.parse_args()
    rows=read_csv(args.targets)
    snapshot=args.snapshot_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out=args.out_root/snapshot; raw=out/"raw_html"; raw.mkdir(parents=True,exist_ok=False)
    retrieved=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    page_cache={}; obs=[]
    for target in rows:
        url=target["ufcstats_url"]
        if url not in page_cache:
            try:
                status,body=fetch_live_page(url)
                page_cache[url]=(status,body,None)
            except Exception as exc:
                page_cache[url]=(None,"",f"{type(exc).__name__}: {exc}")
            time.sleep(0.25)
        status,body,error=page_cache[url]
        fid=target["ufcstats_fighter_id"]
        if body: (raw/f"{fid}.html").write_text(body,encoding="utf-8")
        name=profile_name(body) if body else ""
        norm=lambda s: re.sub(r"[^a-z0-9]","",s.lower())
        identity_ok=bool(name) and norm(name)==norm(target["fighter_name"])
        raw_display=text_value(body,"HEIGHT" if target["field_name"]=="height_cm" else "REACH") if body else None
        raw_in=inches(raw_display)
        state="POPULATED" if raw_in is not None and identity_ok else ("CHECKED_STILL_NULL" if body and identity_ok else "FETCH_OR_IDENTITY_FAILURE")
        normalized=f"{raw_in*2.54:.2f}" if raw_in is not None and identity_ok else ""
        obs.append({**target,"http_status":status or "","page_fighter_name":name,
          "identity_verified":"true" if identity_ok else "false","raw_display_value":raw_display or "",
          "raw_value_inches":("" if raw_in is None or not identity_ok else f"{raw_in:g}"),
          "normalized_value_cm":normalized,"live_state":state,"retrieved_at":retrieved,"fetch_error":error or ""})
    fields=list(obs[0])
    with (out/"observations.csv").open("w",encoding="utf-8",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(obs)
    manifest={"schema_version":1,"snapshot_id":snapshot,"retrieved_at":retrieved,"source":"ufcstats.com",
      "networked_acquisition":True,"target_file":str(args.targets.relative_to(ROOT)),"target_rows":len(rows),
      "unique_pages":len(page_cache),"states":{s:sum(r["live_state"]==s for r in obs) for s in sorted({r["live_state"] for r in obs})},"files":{}}
    for p in sorted(out.rglob("*")):
        if p.is_file(): manifest["files"][str(p.relative_to(out))]=hashlib.sha256(p.read_bytes()).hexdigest()
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(manifest,sort_keys=True))
    if any(r["live_state"]=="FETCH_OR_IDENTITY_FAILURE" for r in obs): return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
