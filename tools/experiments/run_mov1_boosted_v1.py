"""Import the boosted module under a unique name; baseline imports remain frozen."""
import importlib.util
from pathlib import Path
import argparse
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('mov1_boost_execution',ROOT/'models/challengers/mov1_boosted_v1/implementation_v1.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--f02-table',required=True);p.add_argument('--mov0-min-oof',required=True);p.add_argument('--output-dir',required=True)
    module.run(p.parse_args())
