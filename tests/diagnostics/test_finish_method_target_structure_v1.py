"""Reference integrity, partition reconciliation and missingness invariance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'governance/finish_method_target_structure_v1'
spec=importlib.util.spec_from_file_location('audit',ROOT/'tools/diagnostics/run_finish_method_target_structure_v1.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def load(name):
    p=ART/(name+'.csv')
    return pd.read_csv(p if p.exists() else ART/(name+'.csv.gz'))


def test_every_committed_artifact_and_runner_matches_manifest():
    m=json.loads((ART/'EVIDENCE_MANIFEST.json').read_text())
    assert m['status']==audit.STATUS
    assert m['starting_main']=='44aa8dc97b57192ae90e847767051a03f38acd3d'
    assert set(m['files'])=={p.name for p in ART.iterdir() if p.is_file() and p.name!='EVIDENCE_MANIFEST.json'}
    for name,record in m['files'].items():
        data=(ART/name).read_bytes()
        assert hashlib.sha256(data).hexdigest()==record['sha256'],name
        assert len(data)==record['bytes'],name
    assert audit.sha(audit.__file__)==m['runner_sha256']
    c=json.loads((ART/'AUDIT_CONTRACT_V1.json').read_text())
    for p,h in c['source_sha256'].items():assert audit.sha(ROOT/p)==h,p


def test_exact_population_and_every_partition_reconciles():
    x=load('population_manifest');assert len(x)==5658 and x.fight_id.nunique()==5658
    assert x.method.value_counts().to_dict()=={'DECISION':2836,'KO_TKO':1812,'SUBMISSION':1010}
    assert x.result.eq('draw').sum()==45
    assert x.scheduled_rounds.value_counts().to_dict()=={3:5102,5:556}
    e=load('excluded_fights');assert len(e)==71 and e.fight_id.nunique()==71
    assert not set(e.fight_id)&set(x.fight_id)
    for name in ['weight_class_finish_method','weight_class_era','weight_class_rounds','weight_class_era_rounds']:
        t=load(name);t=t[t.division.ne('UFC-wide')]
        assert t.N.sum()==5658
        assert t.KO_TKO_N.sum()==1812 and t.SUBMISSION_N.sum()==1010 and t.DECISION_N.sum()==2836
    for name,keys in [('weight_class_archetype',['archetype']),('pathway_standardization_strata',['archetype']),('state_pathways',['concept']),('state_era',['concept']),('state_rounds',['concept']),('terrain_pathways',['dimension']),('weight_class_terrain',['dimension'])]:
        t=load(name);assert t.groupby(keys).N.sum().eq(5658).all(),name
    assert len(load('canonical_weight_class'))==46
    assert len(load('weight_class_archetype'))==585
    assert len(load('state_pathways'))==170


def test_intervals_denominators_gates_and_zero_cells():
    tables=json.loads((ART/'POPULATION_AND_EXECUTION.json').read_text())['tables']
    for name in tables:
        t=pd.read_csv(ART/name)
        if 'finish_N' not in t:continue
        assert (t.KO_TKO_N+t.SUBMISSION_N+t.DECISION_N).equals(t.N)
        assert (t.KO_TKO_N+t.SUBMISSION_N).equals(t.finish_N)
        assert t.sample_status.equals(t.N.map(audit.gate))
        assert t.finish_sample_status.equals(t.finish_N.map(audit.gate))
        for m,den in [('KO_TKO','N'),('SUBMISSION','N'),('DECISION','N'),('FINISH','N'),('KO_given_finish','finish_N'),('SUB_given_finish','finish_N')]:
            yes=t[den].gt(0)
            assert t.loc[~yes,m+'_rate'].isna().all()
            assert (t.loc[yes,m+'_wilson_low']<=t.loc[yes,m+'_rate']+1e-9).all()
            assert (t.loc[yes,m+'_wilson_high']>=t.loc[yes,m+'_rate']-1e-9).all()
        assert np.allclose(t.loc[t.finish_N.gt(0),'KO_given_finish_rate']+t.loc[t.finish_N.gt(0),'SUB_given_finish_rate'],1)
    assert audit.summary(pd.DataFrame({'method':[]}))['KO_given_finish_rate'] is None
    assert audit.gate(99)=='MODERATE_UNCERTAINTY' and audit.gate(100)=='NORMAL'
    assert audit.gate(24)=='INSUFFICIENT' and audit.gate(25)=='THIN_EXPLORATORY'
    low,high=audit.interval(5,10);assert low==pytest.approx(.23659309,abs=1e-7) and high==pytest.approx(.76340691,abs=1e-7)


def test_exact_known_archetype_formulas_and_fighter_order():
    rng=np.random.default_rng(601)
    thresholds=json.loads((ROOT/'docs/model_diagnostics/mov0_conditional_feature_interaction_archetype_v1/feature_state_thresholds.json').read_text())
    x=pd.DataFrame({'scheduled_rounds':rng.choice([3,5],1000)})
    for side in [1,2]:
        for t in thresholds.values():
            x[f'f{side}__{t["f02_suffix"]}']=rng.uniform(t['low_p33']-1,t['high_p67']+1,1000)
    a,b=audit.states(x,1,thresholds),audit.states(x,2,thresholds)
    new=audit.archetypes(x,a,b);old=audit.OLD.qualify(x,audit.OLD.side_state(x,1,thresholds),audit.OLD.side_state(x,2,thresholds))
    swap=audit.archetypes(x,b,a)
    assert set(new)=={k for k,_,_ in audit.OLD.ARCHETYPES}
    for k in new:
        assert np.array_equal(new[k].to_numpy(dtype=bool),old[k].to_numpy())
        assert new[k].equals(swap[k])
    # Unknown TD access must never be silently interpreted as poor/LOW access.
    t=thresholds['sub_pressure']; x.loc[0,'f1__'+t['f02_suffix']]=t['high_p67']+1
    x.loc[0,'f1__'+thresholds['td_pressure']['f02_suffix']]=np.nan
    x.loc[0,'f1__'+thresholds['td_conversion']['f02_suffix']]=thresholds['td_conversion']['high_p67']+1
    x.loc[0,'f2__'+t['f02_suffix']]=t['low_p33']-1
    r=audit.archetypes(x,audit.states(x,1,thresholds),audit.states(x,2,thresholds))
    assert pd.isna(r['B4_SUB_PRESSURE_POOR_TD_ACCESS'].iloc[0])
    assert audit.status_labels(r['B4_SUB_PRESSURE_POOR_TD_ACCESS']).iloc[0]=='UNASSIGNABLE'


def test_freeze_scope_and_no_model_or_market_consumption():
    c=json.loads((ART/'AUDIT_CONTRACT_V1.json').read_text())
    assert c['eras']==[[2015,2017],[2018,2020],[2021,2023],[2024,2026]]
    assert len(c['weight_classes'])==13
    import ast
    tree=ast.parse(Path(audit.__file__).read_text())
    imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any('ufc_edge.models' in s or 'sklearn' in s or 'pymc' in s for s in imports)
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['fit','predict','quantile'] for n in ast.walk(tree))
