#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd


def args():
    p=argparse.ArgumentParser()
    p.add_argument('--old-f02-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    return p.parse_args()


def main():
    a=args(); a.output_dir.mkdir(parents=True,exist_ok=True)
    df=pd.read_parquet(a.old_f02_dir/'winner_modeling_table.parquet').copy()
    df['event_date']=pd.to_datetime(df['event_date'])
    r1='f1__ctx__physical_size_profile__reach_cm'; r2='f2__ctx__physical_size_profile__reach_cm'
    elig=df['binary_winner_eligible'].astype(bool)
    early=df[elig & df.event_date.dt.year.between(2015,2018) & (df[r1].isna() ^ df[r2].isna())].copy()
    allf=df[elig].copy()

    # pre-index all appearances by fighter for deterministic point-in-time queries
    fighter_rows={}
    for side in (1,2):
        fid=f'fighter_{side}_id'
        for fighter, g in allf.groupby(fid, sort=False):
            fighter_rows.setdefault(fighter,[]).append(g)
    # same fight can only include fighter on one side, so concatenate safely
    fighter_hist={k:pd.concat(v,ignore_index=True).sort_values('event_date') for k,v in fighter_rows.items()}

    rows=[]
    for _,r in early.iterrows():
        known_side=1 if pd.notna(r[r1]) else 2
        miss_side=2 if known_side==1 else 1
        out={'fight_id':r['fight_id'],'event_date':r['event_date'],'known_side':known_side,
             'known_fighter_id':r[f'fighter_{known_side}_id'],'missing_fighter_id':r[f'fighter_{miss_side}_id'],
             'known_won':int(r['winner_id']==r[f'fighter_{known_side}_id'])}
        for label,side in [('known',known_side),('missing',miss_side)]:
            fighter=r[f'fighter_{side}_id']; h=fighter_hist[fighter]
            future=h[h.event_date>r.event_date]; prior=h[h.event_date<r.event_date]
            out[f'{label}_prior_fights']=int(len(prior))
            out[f'{label}_future_fights']=int(len(future))
            out[f'{label}_future_wins']=int((future['winner_id']==fighter).sum())
            out[f'{label}_future_years']=0.0 if future.empty else float((future.event_date.max()-r.event_date).days/365.25)
            out[f'{label}_final_date']=None if future.empty else future.event_date.max().date().isoformat()
        out['delta_future_fights']=out['known_future_fights']-out['missing_future_fights']
        out['delta_future_wins']=out['known_future_wins']-out['missing_future_wins']
        out['delta_future_years']=out['known_future_years']-out['missing_future_years']
        out['delta_prior_fights']=out['known_prior_fights']-out['missing_prior_fights']
        rows.append(out)
    x=pd.DataFrame(rows)
    def rate(col): return float((x[col]>0).mean()) if len(x) else None
    summary={
      'status':'REACH_MISSINGNESS_SURVIVORSHIP_PROBE_V1_COMPLETE',
      'n':int(len(x)),
      'known_side_win_rate':float(x.known_won.mean()),
      'known_more_future_fights_rate':rate('delta_future_fights'),
      'known_more_future_wins_rate':rate('delta_future_wins'),
      'known_longer_future_tenure_rate':rate('delta_future_years'),
      'known_more_prior_fights_rate':rate('delta_prior_fights'),
      'mean_known_future_fights':float(x.known_future_fights.mean()),
      'mean_missing_future_fights':float(x.missing_future_fights.mean()),
      'median_known_future_fights':float(x.known_future_fights.median()),
      'median_missing_future_fights':float(x.missing_future_fights.median()),
      'mean_known_future_wins':float(x.known_future_wins.mean()),
      'mean_missing_future_wins':float(x.missing_future_wins.mean()),
      'mean_known_future_years':float(x.known_future_years.mean()),
      'mean_missing_future_years':float(x.missing_future_years.mean()),
      'mean_known_prior_fights':float(x.known_prior_fights.mean()),
      'mean_missing_prior_fights':float(x.missing_prior_fights.mean()),
      'corr_known_indicator_with_future_fight_advantage':None
    }
    # paired permutation-style sign summaries are more interpretable than a pooled correlation.
    (a.output_dir/'survivorship_probe.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    x.to_csv(a.output_dir/'survivorship_rows.csv',index=False)
    lines=['# Reach Missingness Survivorship Probe V1','',f"Rows: **{len(x)}**",'',
      f"- Reach-known side win rate: **{100*summary['known_side_win_rate']:.1f}%**",
      f"- Reach-known side had more future UFC fights: **{100*summary['known_more_future_fights_rate']:.1f}%**",
      f"- Reach-known side had more future UFC wins: **{100*summary['known_more_future_wins_rate']:.1f}%**",
      f"- Reach-known side had longer remaining UFC tenure: **{100*summary['known_longer_future_tenure_rate']:.1f}%**",
      f"- Reach-known side already had more prior UFC fights: **{100*summary['known_more_prior_fights_rate']:.1f}%**",'',
      f"Mean future fights, known vs missing: **{summary['mean_known_future_fights']:.2f} vs {summary['mean_missing_future_fights']:.2f}**",
      f"Median future fights, known vs missing: **{summary['median_known_future_fights']:.1f} vs {summary['median_missing_future_fights']:.1f}**",
      f"Mean future wins, known vs missing: **{summary['mean_known_future_wins']:.2f} vs {summary['mean_missing_future_wins']:.2f}**",
      f"Mean remaining tenure (years), known vs missing: **{summary['mean_known_future_years']:.2f} vs {summary['mean_missing_future_years']:.2f}**",
      f"Mean prior fights, known vs missing: **{summary['mean_known_prior_fights']:.2f} vs {summary['mean_missing_prior_fights']:.2f}**"]
    (a.output_dir/'survivorship_probe.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))

if __name__=='__main__': main()
