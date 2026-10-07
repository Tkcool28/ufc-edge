#!/usr/bin/env python3
"""Support and secondary dimension descriptions; no acceptance-gate changes."""
import pandas as pd
from grappling_identity_separation_v1 import OUT,cuts,corr_result,save

def main():
 b=pd.read_csv(OUT/'boundary_states.csv.gz');rows=[]
 for year,s in b.groupby('year'):
  q=cuts(s)
  for screen in ['primary','strict']:
   suffix='_supported' if screen=='primary' else '_strict'
   z=q[q['control'+suffix]&q['submission'+suffix]].copy()
   for representation in ['raw','pooled']:
    k='_pooled' if representation=='pooled' else ''
    for x,y in [('control','submission'),('gnp','control'),('gnp','submission')]:
     h=z[z[x+'_supported']&z[y+'_supported']].copy()
     for name in [x,y]:h[name+'_rank']=h.groupby('access_quartile')[name+k].transform(lambda v:v.rank(pct=True)-v.rank(pct=True).mean())
     rows.append(dict(year=year,screen=screen,representation=representation,x=x,y=y,**corr_result(h,x+'_rank',y+'_rank',False)))
 save(OUT,'support_secondary_separation.csv',pd.DataFrame(rows))
if __name__=='__main__':main()
