"""Outcome-free tests of stopping/ties, chronology and tree matrix reconstruction. Zero fits."""
import importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('boost',ROOT/'models/challengers/mov1_boosted_v1/implementation_v1.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def test_earliest_round_tie_and_patience():
    state=m.StopState();assert not state.update(.6)
    assert not state.update(.6-5e-13)
    assert state.rounds==1
    for _ in range(98):assert not state.update(.61)
    assert state.update(.61);assert len(state.trace)==101

def test_global_minimum_tolerance_not_sequential_drift():
    records=[{'inner_log_loss':.6000000000015,'candidate_id':'XGB_01'},{'inner_log_loss':.6000000000008,'candidate_id':'XGB_02'},{'inner_log_loss':.6,'candidate_id':'LGBM_01'}]
    assert m.choose(records)['candidate_id']=='XGB_02'

def test_rounds_weighted_half_up():
    assert m.refit_rounds([{'best_rounds':10,'N':1},{'best_rounds':11,'N':1}])==11
    assert m.refit_rounds([{'best_rounds':10,'N':3},{'best_rounds':20,'N':1}])==13

def test_contract_hash_and_counts():
    assert m.sha(m.DIRECTORY/'CONTRACT_MANIFEST.json')==m.CONTRACT_SHA
    assert len(m.load('mov1_min_allowlist.json')['literal_f02_columns'])==35
    assert [f['outer_year'] for f in m.load('chronological_fold_plan.json')['folds']]==list(range(2018,2027))
    for f in m.load('chronological_fold_plan.json')['folds']:
        assert [i['validation_year'] for i in f['inner_folds']]==[f['outer_year']-2,f['outer_year']-1]
    assert sum(len(m.load(f+'_candidates.json')) for f in ['xgb','lgbm','cat'])*18==972
