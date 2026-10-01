"""Zero-fit split co-use diagnostic for only the three preregistered hypotheses."""
import importlib.util,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('saved_boost',ROOT/'tools/experiments/verify_mov1_boosted_saved_v1.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)

def paths(node,family,used=frozenset()):
    if family=='XGB':
        if 'leaf' in node:return [used]
        feature=int(node['split'][1:]);children=node['children']
    else:
        if 'split_feature' not in node:return [used]
        feature=node['split_feature'];children=[node['left_child'],node['right_child']]
    return [p for child in children for p in paths(child,family,used|{feature})]

def diagnostic(directory):
    directory=Path(directory);result=[]
    for r in json.loads((directory/'SELECTED_BY_YEAR.json').read_text()):
        y=r['outer_year'];family=r['family'];names=json.loads((directory/'MODELS'/f'{y}_outer.preprocessing.json').read_text())['feature_names']
        model=v.native(family,directory/'MODELS'/f'{y}_outer_{r["candidate_id"]}')
        if family=='XGB':trees=[paths(json.loads(t),'XGB') for t in model.get_dump(dump_format='json')]
        elif family=='LGBM':trees=[paths(t['tree_structure'],'LGBM') for t in model.dump_model()['tree_info']]
        else:
            with tempfile.TemporaryDirectory() as temp:
                p=Path(temp)/'cat.json';model.save_model(str(p),format='json');d=json.loads(p.read_text())
            indices={f['feature_index']:f['flat_feature_index'] for f in d['features_info']['float_features']}
            trees=[[frozenset(indices[s['float_feature_index']] for s in t['splits'])] for t in d['oblivious_trees']]
        groups={
            'submission_pressure_x_TD_access':(['submission_attempt_rate__created'],['takedown_pressure__created','takedown_conversion__success']),
            'submission_pressure_x_vulnerability':(['submission_attempt_rate__created'],['submission_attempt_rate__faced','finish_method_loss_profile__submission']),
            'KD_creation_x_vulnerability':(['knockdown_rate__created'],['knockdown_rate__allowed','finish_method_loss_profile__ko_tko'])}
        for hypothesis,(a,b) in groups.items():
            A={i for i,n in enumerate(names) if any(k in n for k in a)};B={i for i,n in enumerate(names) if any(k in n for k in b)}
            count=sum(any(bool(path&A) and bool(path&B) for path in tree) for tree in trees)
            result.append({'outer_year':y,'family':family,'hypothesis':hypothesis,'tree_count':len(trees),'trees_with_both_on_a_path_or_oblivious_tree':count,'group_A':[names[i] for i in sorted(A)],'group_B':[names[i] for i in sorted(B)]})
    return {'rows':result,'additional_fits':0,'scope':'Only preregistered hypotheses; native selected outer models. XGB/LGBM root-to-leaf paths, CAT oblivious-tree split sets. Co-use is descriptive structure, not causal evidence or a measured interaction effect. No outcome-selected search, pruning or refitting.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--run-dir',required=True);a=p.parse_args();v.m.write_json(Path(a.run_dir)/'HYPOTHESIS_SPLIT_CO_USE.json',diagnostic(a.run_dir))
