#!/usr/bin/env python3
"""Execute the merged MOV1 contract without modifying its decisions."""
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'models/mov1'))
from implementation_v1 import run_training, write_json
from evaluation_v1 import evaluate

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--f02-table',type=Path,required=True)
    parser.add_argument('--mov0-min-oof',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    try:
        values=run_training(args.f02_table,args.mov0_min_oof,args.output_dir)
        evaluate(*values,args.output_dir)
    except Exception as exc:
        args.output_dir.mkdir(parents=True,exist_ok=True)
        write_json(args.output_dir/'MOV1_IMPLEMENTATION_VALIDATION_FAILED.json',
                   {'status':'MOV1_IMPLEMENTATION_VALIDATION_FAILED','error_type':type(exc).__name__,
                    'error':str(exc),'performance_interpretation_permitted':False})
        raise
