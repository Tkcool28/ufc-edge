"""Validate the MOV1 preregistration against immutable inputs; never fit a model."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'models/mov1/contracts/ko_vs_submission_given_finish_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((CONTRACT / name).read_text())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def summarize(rows):
    return {
        'N': len(rows),
        **{method: sum(row['method'] == method for row in rows)
           for method in ['KO_TKO', 'SUBMISSION', 'DECISION']},
        'ordered_fight_id_sha256': hashlib.sha256(
            ''.join(row['fight_id'] + '\n' for row in rows).encode()).hexdigest(),
    }


def validate(f02_table, check_manifest=True):
    import numpy as np
    import pandas as pd

    foundation = load('foundation_manifest.json')
    for name, expected in foundation['source_files'].items():
        require(digest(ROOT / name) == expected, f'Foundation changed: {name}')
    if check_manifest:
        manifest = load('CONTRACT_MANIFEST.json')
        for name, expected in manifest['files'].items():
            require(digest(ROOT / name) == expected['sha256'], f'Contract changed: {name}')
    require(digest(f02_table) == foundation['corrected_F02']['physical_sha256'],
            'Incorrect corrected F02 bytes')
    f02 = pd.read_parquet(f02_table)
    require(not f02.fight_id.duplicated().any(), 'Duplicated F02 IDs')
    target = load('target_population.json')
    with gzip.open(ROOT / target['source_population_path'], 'rt') as stream:
        rows = sorted(csv.DictReader(stream), key=lambda r:
                      (r['event_date'], r['event_id'], r['fight_id']))
    require(summarize(rows) == target['all_modern_eligible'], 'Population drift')
    require(len(rows) == 5658, 'Wrong population')
    finish_rows = [r for r in rows if r['method'] in target['labels']]
    require(summarize(finish_rows) == target['conditional_training_population'],
            'Conditional population drift')
    require(len(finish_rows) == 2822, 'Wrong finish population')
    # Independently reconcile existing canonical method eligibility, not F02 winner labels.
    canonical = pd.read_csv(ROOT / 'data/canonical/v0/fights.csv', dtype=str)
    events = pd.read_csv(ROOT / 'data/canonical/v0/events.csv', dtype=str)
    canonical_modern = canonical.merge(events[['event_id','event_date']],on='event_id',validate='many_to_one')
    canonical_modern = canonical_modern[canonical_modern.promotion.eq('UFC') & canonical_modern.event_date.ge('2015-01-01')]
    governed = canonical_modern[
        (canonical_modern.result.eq('win_loss') & canonical_modern.method.isin(['KO_TKO','SUBMISSION'])) |
        (canonical_modern.result.isin(['win_loss','draw']) & canonical_modern.method.eq('DECISION'))]
    require(set(governed.fight_id) == set(r['fight_id'] for r in rows), 'Eligible canonical population not exact')
    canonical = canonical.set_index('fight_id')
    for row in rows:
        actual = canonical.loc[row['fight_id']]
        require(actual['method'] == row['method'], 'Canonical method mismatch')
        require(actual['result'] == row['result'], 'Canonical result mismatch')
        require(actual['result'] == 'win_loss' or
                (actual['result'] == 'draw' and actual['method'] == 'DECISION'),
                'Ineligible result in population')
    indexed = f02.set_index('fight_id')
    require(set(r['fight_id'] for r in rows) <= set(indexed.index), 'Scoring IDs missing')
    selected = indexed.loc[[r['fight_id'] for r in rows]]
    require(selected.promotion.eq('UFC').all(), 'Non-UFC row')
    require(selected.event_date.astype(str).tolist() == [r['event_date'] for r in rows],
            'F02 dates differ')
    require(selected.event_id.astype(str).tolist() == [r['event_id'] for r in rows],
            'F02 event IDs differ')
    cutoff = pd.to_datetime(selected.prediction_as_of, utc=True)
    event = pd.to_datetime(selected.event_date, utc=True)
    require(cutoff.eq(event).all(), 'Unexpected snapshot cutoff')
    require(event.ge(pd.Timestamp('2015-01-01', tz='UTC')).all(), 'Pre-modern input')

    allow = {name: load(name.lower() + '_allowlist.json')['literal_f02_columns']
             for name in ['C0', 'C1', 'MOV1_MIN', 'MOV1_FULL']}
    require([len(allow[n]) for n in allow] == [0, 5, 35, 55], 'Allowlist size drift')
    require(set(allow['C1']) < set(allow['MOV1_MIN']) < set(allow['MOV1_FULL']),
            'Ladder nesting violated')
    for name, columns in allow.items():
        require(len(columns) == len(set(columns)), f'Duplicate {name} predictor')
        require(set(columns) <= set(f02.columns), f'{name} F02 predictor absent')
    forbidden = {'fight_id', 'event_id', 'event_date', 'fighter1_win', 'winner_id',
                 'target_state', 'binary_winner_eligible', 'method', 'result'}
    require(not set(allow['MOV1_FULL']) & forbidden, 'Target/ID predictor')
    catalog = json.loads((ROOT / 'features/feature_catalog.yaml').read_text())
    features = {x['feature_name']: x for x in catalog['features']}
    temporal = json.loads((ROOT / 'governance/MOV_BUCKET_INPUT_TEMPORAL_SAFETY_AUDIT_V1_COMPLETE.json').read_text())
    require(temporal['availability_safety']['PIT_SAFE'] == 15, 'PIT audit drift')
    approved_families = {'early_finish_profile', 'finish_method_win_profile',
                        'finish_method_loss_profile', 'knockdown_rate',
                        'submission_attempt_rate', 'takedown_pressure',
                        'takedown_conversion', 'knockdown_creation_vs_vulnerability',
                        'knockdown_efficiency', 'sig_strike_flow',
                        'sig_strike_efficiency', 'sig_environment_mix', 'sig_target_mix'}
    for column in allow['MOV1_FULL'][3:]:
        family = column.split('__')[2] if column.startswith('f') else column.split('__')[1]
        require(family == 'prior_fight_count' or family in approved_families,
                f'Ungoverned family {family}')
        require(features[family]['career_variant'], f'Career ungoverned: {family}')
        require(features[family]['information_cutoff_rule'], f'No PIT rule {family}')
    with (CONTRACT / 'feature_rationale.csv').open() as stream:
        rationale = list(csv.DictReader(stream))
    require([r['column'] for r in rationale] == allow['MOV1_FULL'], 'Rationale coverage')
    require(all(all(r[k] for k in ['mechanism','orientation','missingness','nonredundancy','PIT_authority']) for r in rationale), 'Incomplete rationale')

    preprocessing = load('missingness_preprocessing.json')
    mapping = json.loads((ROOT / preprocessing['weight_class']['literal_map_path']).read_text())['literal_map']
    require(selected.ctx__weight_class.dropna().isin(mapping).all(), 'Unmapped weight class')
    normalized = selected.ctx__weight_class.map(mapping)
    require(normalized.tolist() == [r['division'] for r in rows], 'Division mapping mismatch')
    require(selected.scheduled_rounds.astype(float).tolist() == [float(r['scheduled_rounds']) for r in rows], 'Round context mismatch')
    require(preprocessing['weight_class']['ordinal'] is False, 'Ordinal division forbidden')
    pairs = load('fighter_order_transformation.json')['pairs']
    numeric_columns = [c for pair in pairs for c in pair['columns']]
    require(set(numeric_columns) | {'scheduled_rounds','ctx__title_bout','ctx__weight_class'} == set(allow['MOV1_FULL']), 'Symmetric coverage not exact')
    require(len(numeric_columns) == len(set(numeric_columns)), 'Duplicate pair column')
    for pair in pairs:
        a,b = pair['columns']
        expected = a.replace('f1__','f2__',1) if pair['kind']=='fighter_pair' else a.replace('__f1_vs_f2__','__f2_vs_f1__')
        require(b == expected, 'Pair is not swap closed')
        require(pair['transforms'] == ['mean','absolute_difference'], 'Nonsymmetric transform')
    numeric = selected[numeric_columns + ['scheduled_rounds']].astype(float)
    require(not np.isinf(numeric.to_numpy()).any(), 'Infinite F02 value')
    require(selected.ctx__title_bout.dropna().isin([True,False,0,1]).all(), 'Nonboolean title')

    folds = load('chronological_fold_plan.json')['folds']
    supports = []
    for fold in folds:
        y = fold['outer_year']
        train = [r for r in finish_rows if int(r['event_date'][:4]) < y]
        score = [r for r in rows if int(r['event_date'][:4]) == y]
        validation = [r for r in score if r['method'] in target['labels']]
        require(summarize(train) == fold['training'], 'Outer training drift')
        require(summarize(score) == fold['all_eligible_scoring'], 'Outer scoring drift')
        require(summarize(validation) == fold['conditional_validation'], 'Outer metric drift')
        require(not set(r['fight_id'] for r in train) & set(r['fight_id'] for r in score), 'Train score overlap')
        histories = [(f'outer_{y}', train)]
        for inner in fold['inner_folds']:
            iy = inner['validation_year']
            it = [r for r in finish_rows if int(r['event_date'][:4]) < iy]
            iv = [r for r in finish_rows if int(r['event_date'][:4]) == iy]
            require(summarize(it) == inner['training'] and summarize(iv) == inner['validation'], 'Inner fold drift')
            require(iy in [y-2,y-1], 'Inner year drift')
            histories.append((f'outer_{y}_inner_{iy}',it))
        for label, history in histories:
            require({r['method'] for r in history} == {'KO_TKO','SUBMISSION'}, 'Missing class / decisions in training')
            h = indexed.loc[[r['fight_id'] for r in history]]
            minimum = min(int(np.isfinite(h[pair['columns']].to_numpy(float)).sum()) for pair in pairs)
            require(minimum > 0, 'All-missing numeric training pair')
            require(h.scheduled_rounds.notna().any() and h.ctx__title_bout.notna().any()
                    and h.ctx__weight_class.notna().any(), 'All-missing training context')
            supports.append({'history':label,'finish_training_N':len(history),'minimum_finite_pooled_pair_values':minimum})
    require(sum(f['all_eligible_scoring']['N'] for f in folds)==4260 and sum(f['conditional_validation']['N'] for f in folds)==2115, 'Outer totals')
    # Illustrative algebra/specification checks only, no learned model or OOF metrics.
    F,K = np.meshgrid(np.array([0.,.2,.5,.8,1.]),np.array([0.,.1,.5,.9,1.]))
    require(np.allclose(F*K+F*(1-K)+(1-F),1,atol=1e-12,rtol=0), 'Composition identity')
    a,b = np.array([0.,1.,-2.,3.]),np.array([1.,0.,3.,-2.])
    require(np.array_equal((a+b)/2,(b+a)/2) and np.array_equal(abs(a-b),abs(b-a)), 'Symmetry algebra')
    require(load('conditional_probability_buckets.json')['edges']==[0,.3,.4,.5,.6,.7,.8,1], 'Bucket drift')
    require(len(load('terrain_archetype_evaluation.json')['archetypes'])==15, 'Panel drift')
    with (CONTRACT / 'expected_fold_counts.csv').open() as stream:
        count_rows = list(csv.DictReader(stream))
    require(len(count_rows)==9, 'Count CSV length')
    for row,fold in zip(count_rows,folds):
        t,v,s = fold['training'],fold['conditional_validation'],fold['all_eligible_scoring']
        require([int(x) for x in row.values()]==[fold['outer_year'],t['N'],t['KO_TKO'],t['SUBMISSION'],v['N'],v['KO_TKO'],v['SUBMISSION'],s['N'],s['DECISION']], 'CSV/JSON counts disagree')
    return {'status':'CONTRACT_INPUT_VALIDATION_PASSED','starting_main_sha':foundation['starting_main_sha'],
            'F02_physical_sha256':digest(f02_table),'F02_rows':len(f02),'F02_columns':len(f02.columns),
            'predictors_checked':55,'modern_all_eligible_N':5658,'conditional_finish_N':2822,
            'outer_all_scoring_N':4260,'outer_conditional_N':2115,'training_support':supports,
            'checks':['foundation hashes','canonical labels','literal corrected F02 schema','existing PIT-governed career families','symmetric pair closure','categorical mapping','outer and inner exact counts and ID digests','finish-only training, complete scoring coverage','finite training support','illustrative composition and symmetry algebra'],
            'no_model_fit_no_predictions_no_performance_evaluation':True,
            'future_runtime_checks':['fitted probability swap invariance1e-12','fitted preprocessing train-only behavior','convergence','conditional and complete-system metrics','immutable MOV0 OOF join hashes']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--f02-table',type=Path,required=True)
    parser.add_argument('--write-evidence',type=Path)
    parser.add_argument('--initial-manifest',action='store_true',help='Initial creation only: no contract manifest yet')
    args = parser.parse_args()
    evidence = validate(args.f02_table,check_manifest=not args.initial_manifest)
    if args.write_evidence:
        args.write_evidence.write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in evidence.items() if k!='training_support'},indent=2))
