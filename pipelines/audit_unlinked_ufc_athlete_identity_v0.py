#!/usr/bin/env python3
"""Audit official UFC athlete UUIDs not linked to canonical fighters.

DATA PHASE ONLY. No display-name matching is used. Evidence comes only from stable UFC
athlete UUIDs, official UFC fight red/blue UUID relationships, official FightMetric IDs,
and existing trusted source_identity_links. This audit decides whether the known 1,693
unlinked athlete nodes are an accepted profile/legacy identity gap or expose meaningful
fight-spine coverage that must remain explicitly documented.
"""
from __future__ import annotations

import csv,json
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ATH_MAN=ROOT/"data/raw/ufc_com_resources/athletes/20260820T194553Z/manifest.json"
FIGHT_MAN=ROOT/"data/raw/ufc_com_resources/fights/20260821T055500Z/manifest.json"
LINKS=ROOT/"data/canonical/v0/source_identity_links.csv"
OUT=ROOT/"data/derived/qa/unlinked_ufc_athlete_identity_v0.csv"
AUDIT=ROOT/"provenance/audits/unlinked_ufc_athlete_identity_v0_latest.json"
FIELDS=["ufc_athlete_uuid","title","fightmetric_id","old_id","old_url","athlete_status_text","official_fight_appearances","canonically_linked_official_fight_appearances","distinct_official_fights","distinct_canonical_fights","disposition"]

def rcsv(path):
    with path.open("r",encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def load(path):return json.loads(path.read_text(encoding="utf-8"))
def rel_id(obj,name):
    d=((obj.get("relationships") or {}).get(name) or {}).get("data")
    if isinstance(d,dict):return str(d.get("id") or "")
    return ""
def status_map(page):
    m={}
    for x in page.get("included") or []:
        xid=str(x.get("id") or "");attrs=x.get("attributes") or {}
        label=str(attrs.get("name") or attrs.get("title") or attrs.get("label") or "").strip()
        if xid and label:m[xid]=label
    return m

def main():
    aman=load(ATH_MAN);fman=load(FIGHT_MAN);links=rcsv(LINKS)
    athlete_pages=[ROOT/x["path"] for x in aman.get("files") or []]
    fight_pages=[]
    for cm_rel in fman.get("chunk_manifests") or []:
        cm=load(ROOT/cm_rel)
        fight_pages.extend(ROOT/x["path"] for x in cm.get("files") or [])
    if len(athlete_pages)!=84 or len(fight_pages)!=242:raise RuntimeError(f"raw page count drift athletes={len(athlete_pages)} fights={len(fight_pages)}")

    trusted_athlete={r["source_id"]:r["canonical_id"] for r in links if r.get("source")=="ufc_com_official" and r.get("entity_type")=="fighter" and r.get("link_status")=="trusted"}
    trusted_fight={r["source_id"]:r["canonical_id"] for r in links if r.get("source")=="ufc_com_official" and r.get("entity_type")=="fight" and r.get("link_status")=="trusted"}

    athletes={}
    for p in athlete_pages:
        page=load(p);sm=status_map(page)
        for a in page.get("data") or []:
            uid=str(a.get("id") or "");attrs=a.get("attributes") or {};sid=rel_id(a,"athlete_status")
            if not uid:raise RuntimeError(f"athlete without UUID in {p}")
            if uid in athletes:raise RuntimeError(f"duplicate athlete UUID {uid}")
            athletes[uid]={"title":str(attrs.get("title") or attrs.get("name") or ""),"fightmetric_id":str(attrs.get("fightmetric_id") or ""),"old_id":str(attrs.get("old_id") or ""),"old_url":str(attrs.get("old_url") or ""),"athlete_status_text":sm.get(sid,"")}
    if len(athletes)!=4161:raise RuntimeError(f"athlete cardinality drift {len(athletes)}")

    appearances=Counter();canonical_appearances=Counter();fight_sets=defaultdict(set);canonical_fight_sets=defaultdict(set)
    official_fight_rows=0
    for p in fight_pages:
        page=load(p)
        for f in page.get("data") or []:
            official_fight_rows+=1;fuid=str(f.get("id") or "");cfid=trusted_fight.get(fuid,"")
            for rel in ("red_corner","blue_corner"):
                auid=rel_id(f,rel)
                if not auid:continue
                appearances[auid]+=1;fight_sets[auid].add(fuid)
                if cfid:
                    canonical_appearances[auid]+=1;canonical_fight_sets[auid].add(cfid)
    if official_fight_rows!=12069:raise RuntimeError(f"fight resource cardinality drift {official_fight_rows}")

    unlinked=sorted(set(athletes)-set(trusted_athlete))
    if len(unlinked)!=1693:raise RuntimeError(f"expected 1693 unlinked official athletes, got {len(unlinked)}")
    rows=[];disp=Counter();status=Counter();fm=0;legacy=0
    for uid in unlinked:
        a=athletes[uid];app=appearances[uid];capp=canonical_appearances[uid]
        if capp>0:d="unlinked_but_participates_in_canonical_linked_official_fight"
        elif app>0:d="unlinked_with_official_fight_history_not_on_trusted_official_fight_spine"
        elif a["fightmetric_id"]:d="profile_only_unlinked_with_fightmetric_id"
        elif a["old_id"] or a["old_url"]:d="profile_only_legacy_identity"
        else:d="profile_only_unlinked_no_stable_fight_bridge"
        disp[d]+=1;status[a["athlete_status_text"] or "<missing>"]+=1;fm+=bool(a["fightmetric_id"]);legacy+=bool(a["old_id"] or a["old_url"])
        rows.append({"ufc_athlete_uuid":uid,**a,"official_fight_appearances":app,"canonically_linked_official_fight_appearances":capp,"distinct_official_fights":len(fight_sets[uid]),"distinct_canonical_fights":len(canonical_fight_sets[uid]),"disposition":d})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",encoding="utf-8",newline="") as f:w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="raise");w.writeheader();w.writerows(rows)
    meaningful=sum(v for k,v in disp.items() if k.startswith("unlinked_but") or k.startswith("unlinked_with"))
    payload={"schema_version":1,"generated_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"official_athlete_nodes":len(athletes),"trusted_official_athlete_links":len(trusted_athlete),"unlinked_official_athlete_nodes":len(unlinked),"official_fight_resources":official_fight_rows,"trusted_official_fight_links":len(trusted_fight),"unlinked_with_fightmetric_id":fm,"unlinked_with_legacy_old_id_or_url":legacy,"unlinked_status_text_counts":dict(status),"disposition_counts":dict(disp),"unlinked_with_any_official_fight_participation":sum(appearances[u]>0 for u in unlinked),"unlinked_with_canonical_linked_official_fight_participation":sum(canonical_appearances[u]>0 for u in unlinked),"meaningful_fight_identity_gap_nodes":meaningful,"output":str(OUT.relative_to(ROOT)),"decision":{"display_name_matching_used":False,"canonical_identity_links_written":False,"official_uuid_relationships_are_evidence_only":True,"profile_only_unlinked_nodes_can_remain_accepted_gap":True,"fight_participating_unlinked_nodes_require_explicit_gap_documentation":meaningful>0,"required_next":"Document fight-participating unlinked nodes as an accepted identity coverage gap unless a stable pre-existing source crosswalk resolves them. Do not create links by name similarity."}}
    AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(payload,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
