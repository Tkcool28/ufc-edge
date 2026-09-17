#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd


def args():
    p=argparse.ArgumentParser()
    p.add_argument('--old-f02-dir',type=Path,required=True)
    p.add_argument('--new-f02-dir',type=Path,required=True)
    p.add_argument('--feature-surface',type=Path,required=True)
    p.add_argument('--fighters-csv',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    return p.parse_args()

def equal(a,b):
    av,bv=a.to_numpy(),b.to_numpy()
    return (pd.isna(av)&pd.isna(bv))|np.asarray(av==bv,dtype=bool)

def source_cols(surface):
    cols=[]
    for keys in surface['paired_fighter_predictors']['concepts'].values():
        for key in keys: cols += [f'f1__{key}',f'f2__{key}']
    for item in surface['matchup_predictors']['review']:
        if item['accepted']: cols += list(item['columns'])
    if len(cols)!=197: raise RuntimeError(len(cols))
    return cols

def main():
    a=args(); a.output_dir.mkdir(parents=True,exist_ok=True)
    old=pd.read_parquet(a.old_f02_dir/'winner_modeling_table.parquet')
    new=pd.read_parquet(a.new_f02_dir/'winner_modeling_table.parquet')
    surface=json.loads(a.feature_surface.read_text())
    changed=np.zeros(len(old),dtype=bool)
    for c in source_cols(surface): changed |= ~equal(old[c],new[c])
    year=pd.to_datetime(old.event_date).dt.year
    use=changed & year.between(2015,2018) & old.binary_winner_eligible.astype(bool).to_numpy()
    cols=['fight_id','event_date','fighter_1_id','fighter_2_id','fighter_1_win',
          'f1__ctx__physical_size_profile__reach_cm','f2__ctx__physical_size_profile__reach_cm']
    d=old.loc[use,cols].copy()
    nn=new.loc[use,['fight_id','f1__ctx__physical_size_profile__reach_cm','f2__ctx__physical_size_profile__reach_cm']].copy()
    nn=nn.rename(columns={'f1__ctx__physical_size_profile__reach_cm':'new_f1_reach','f2__ctx__physical_size_profile__reach_cm':'new_f2_reach'})
    d=d.merge(nn,on='fight_id',validate='one_to_one')
    fighters=pd.read_csv(a.fighters_csv,dtype=str).fillna('')
    names=dict(zip(fighters.fighter_id,fighters.canonical_name))
    d['f1_name']=d.fighter_1_id.map(names); d['f2_name']=d.fighter_2_id.map(names)
    old1=d['f1__ctx__physical_size_profile__reach_cm']; old2=d['f2__ctx__physical_size_profile__reach_cm']
    one_known=old1.notna() ^ old2.notna(); d=d[one_known].copy()
    d['known_side']=np.where(old1.loc[d.index].notna(),'f1','f2')
    d['known_name']=np.where(d.known_side.eq('f1'),d.f1_name,d.f2_name)
    d['missing_name']=np.where(d.known_side.eq('f1'),d.f2_name,d.f1_name)
    d['known_won']=np.where(d.known_side.eq('f1'),d.fighter_1_win.astype(bool),~d.fighter_1_win.astype(bool))
    d['known_reach']=np.where(d.known_side.eq('f1'),d.new_f1_reach,d.new_f2_reach).astype(float)
    d['missing_reach']=np.where(d.known_side.eq('f1'),d.new_f2_reach,d.new_f1_reach).astype(float)
    d['known_reach_adv_cm']=d.known_reach-d.missing_reach
    d['known_actually_longer']=d.known_reach_adv_cm>0
    d['known_same_reach']=np.isclose(d.known_reach_adv_cm,0)
    summary={
      'n':int(len(d)),
      'known_side_win_rate':float(d.known_won.mean()),
      'known_side_actually_longer_rate':float(d.known_actually_longer.mean()),
      'known_side_mean_reach_adv_cm':float(d.known_reach_adv_cm.mean()),
      'known_side_median_reach_adv_cm':float(d.known_reach_adv_cm.median()),
      'known_side_win_rate_when_actually_longer':None if not d.known_actually_longer.any() else float(d.loc[d.known_actually_longer,'known_won'].mean()),
      'known_side_win_rate_when_not_longer':None if d.known_actually_longer.all() else float(d.loc[~d.known_actually_longer,'known_won'].mean()),
    }
    agg=d.groupby('known_name',dropna=False).agg(fights=('fight_id','size'),wins=('known_won','sum'),mean_reach_adv_cm=('known_reach_adv_cm','mean')).reset_index()
    agg['win_rate']=agg.wins/agg.fights
    agg=agg.sort_values(['fights','wins','known_name'],ascending=[False,False,True])
    targets=['Jon Jones','Max Holloway','Anthony Pettis','Robbie Lawler','Anderson Silva','Urijah Faber','Georges St-Pierre']
    target_rows=[]
    for name in targets:
        hit=d[(d.f1_name.eq(name))|(d.f2_name.eq(name))]
        target_rows.append({'name':name,'affected_fights':int(len(hit)),'reach_known_side_fights':int((hit.known_name.eq(name)).sum()),'reach_missing_side_fights':int((hit.missing_name.eq(name)).sum())})
    out={'summary':summary,'target_names':target_rows,'top_known_side_fighters':agg.head(30).to_dict('records')}
    (a.output_dir/'early_reach_known_probe.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    d.sort_values('event_date').to_csv(a.output_dir/'early_reach_known_fights.csv',index=False)
    lines=['# Early Reach-Known Fighter Probe','',f"Rows: **{summary['n']}**",f"Known-side win rate: **{summary['known_side_win_rate']:.1%}**",f"Known side actually had longer corrected reach: **{summary['known_side_actually_longer_rate']:.1%}**",f"Mean corrected reach advantage of known side: **{summary['known_side_mean_reach_adv_cm']:+.2f} cm**",'', '## Requested names','', '| Fighter | affected | known side | missing side |','|---|---:|---:|---:|']
    for r in target_rows: lines.append(f"| {r['name']} | {r['affected_fights']} | {r['reach_known_side_fights']} | {r['reach_missing_side_fights']} |")
    lines += ['', '## Most frequent reach-known fighters','', '| Fighter | fights | wins | win rate | mean actual reach adv |','|---|---:|---:|---:|---:|']
    for _,r in agg.head(20).iterrows(): lines.append(f"| {r.known_name} | {int(r.fights)} | {int(r.wins)} | {r.win_rate:.1%} | {r.mean_reach_adv_cm:+.2f} cm |")
    (a.output_dir/'early_reach_known_probe.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))
if __name__=='__main__': main()
