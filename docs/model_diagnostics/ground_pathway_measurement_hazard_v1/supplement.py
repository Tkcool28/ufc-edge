import sys,json
from pathlib import Path
import pandas as pd,numpy as np
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p));import audit
D=pd.read_csv(p/'fight_hazard_accounting.csv.gz',float_precision='round_trip');A=pd.read_csv(audit.SRC/'run_v1/fighter_abilities.csv.gz',float_precision='round_trip')
merged=A.merge(D[['fight_id','method','outer_year',*audit.CELLS.values()]],on=['fight_id','outer_year'],validate='many_to_one')
rows=[]
for group,col in [('ALL',None),*audit.CELLS.items()]:
 z=merged[merged.method.isin(['KO_TKO','SUBMISSION'])];z=z if col is None else z[z[col].eq('MATCH')]
 for k in ['access','control','submission','gnp','td_resistance','control_allowed','sub_faced','ground_allowed','sub_conversion','sub_conversion_allowed']:
  rows.append(dict(group=group,ability=k,n=len(z),mean=z[k].mean(),mean_prior=z[k+'_prior_mean'].mean(),mean_effective_support=z[k+'_effective_support'].mean(),median_den=z[k+'_den'].median()))
pd.DataFrame(rows).to_csv(p/'cohort_abilities.csv',index=False)
cols=['prior_fights','prior_decisions','conversion_excluded_bouts']+[k+'_missing_bouts' for k in ['access','control','submission','gnp']]+[k+'_effective_support' for k in ['access','control','submission','gnp','sub_conversion']]
A.groupby('outer_year')[cols].mean().to_csv(p/'annual_support_coverage.csv')
# Relative opponent modulation, exactly from frozen construction, never new probabilities
B=A.sort_values(['fight_id','side']);B['opp_sub']=B.groupby('fight_id').sub_faced.transform(lambda x:x.iloc[::-1].to_numpy());B['opp_ctrl']=B.groupby('fight_id').control_allowed.transform(lambda x:x.iloc[::-1].to_numpy());B['creation_attacker_only']=B.submission/B.control.clip(.02,.8);B['creation_directional']=np.sqrt(B.creation_attacker_only*B.opp_sub/B.opp_ctrl.clip(.02,.8));B['opponent_creation_multiplier']=B.creation_directional/B.creation_attacker_only
B[['opponent_creation_multiplier','sub_conversion_effective_support','sub_conversion_allowed_effective_support']].describe(percentiles=[.05,.25,.5,.75,.95]).to_csv(p/'directional_defense_distribution.csv')

R=[]
for name,col in [("ALL_FINISH",None),*audit.CELLS.items()]:
 z=D[D.method.isin(["KO_TKO","SUBMISSION"])];z=z if col is None else z[z[col].eq("MATCH")]
 R.append(dict(group=name,n=len(z),**{c:z[c].mean() for c in ["ever_entry","entries","ground_minutes","returns","sub_attempts","ground_actions","sub_finishes","ground_ko","standing_ko","conversion_weighted"]}))
pd.DataFrame(R).to_csv(p/"finish_cohort_rewards.csv",index=False)
import matplotlib;matplotlib.use("Agg");import matplotlib.pyplot as plt
S=pd.read_csv(p/"diagnostic_summary.csv");fig,axes=plt.subplots(1,2,figsize=(10,4))
for ax,group in zip(axes,["B3","B5"]):
 for key in ["entry","return","attempt","conversion","strike"]:
  z=S[S.group.eq(group)&S.diagnostic.isin([f"{key}_{f:g}" for f in audit.FACTORS])];ax.plot(audit.FACTORS,z.conditional_SUB,marker="o",label=key)
 ax.set(title=group,xlabel="isolated hazard factor",ylabel="conditional SUB");ax.grid(alpha=.2)
axes[0].legend(fontsize=8);fig.tight_layout();fig.savefig(p/"B3_B5_sensitivity.png",dpi=150)
