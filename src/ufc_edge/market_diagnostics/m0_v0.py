"""M0-MD0 bare-bones historical market diagnostic V0."""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .analysis import chronological_incremental_test, classify_verdict, diagnostic_table_logical_hash, disagreement_report
from .core import *  # re-export narrow tested contract helpers
from .matching import PreparedMarket, attach_f02_identity, build_unique_name_index, match_market, prepare_public_market_rows


def run_diagnostic(*,m0_oof_path:Path,m0_freeze_path:Path,f02_modeling_path:Path,canonical_fighters_path:Path,market_csv_path:Path,output_dir:Path)->dict:
    freeze=json.loads(m0_freeze_path.read_text()); oof=pd.read_parquet(m0_oof_path); validate_m0_freeze(freeze,oof)
    frozen=oof.set_index("fight_id").logistic_probability.copy()
    f02=pd.read_parquet(f02_modeling_path); fighters=pd.read_csv(canonical_fighters_path); raw=pd.read_csv(market_csv_path)
    prepared=prepare_public_market_rows(raw,fighters); identity=attach_f02_identity(oof,f02); matched,matching=match_market(identity,prepared.usable)
    if not np.array_equal(frozen.loc[matched.fight_id].to_numpy(float),matched.m0_probability.to_numpy(float)):
        raise MarketDiagnosticError("M0 probability changed during diagnostic")
    y=matched.target.astype(int); naive=np.full(len(matched),.5)
    same={"naive_50_50":metric_bundle(y,naive),"m0":metric_bundle(y,matched.m0_probability),"market":metric_bundle(y,matched.market_probability),"blend_50_50":metric_bundle(y,matched.blend_probability)}
    cal,ece=calibration_table(y,matched.market_probability)
    matching.update({"market_source_rows":int(len(raw)),"market_usable_unique_rows":int(len(prepared.usable)),"market_invalid_odds_rows":prepared.invalid_odds_rows,
                     "market_unresolved_name_rows":prepared.unresolved_name_rows,"market_ambiguous_name_rows":prepared.ambiguous_name_rows,
                     "market_conflicting_duplicate_groups":prepared.conflicting_duplicate_groups,"market_identical_duplicate_rows_collapsed":prepared.identical_duplicate_rows_collapsed})
    result={"status":"M0_MARKET_DIAGNOSTIC_V0_COMPLETE","m0_identity":{"freeze_version":M0_FREEZE_VERSION,"oof_rows":M0_OOF_ROWS,"oof_logical_sha256":M0_OOF_LOGICAL_SHA256,"m0_probability_unchanged":True},
            "market_construction":{"source":MARKET_SOURCE,"source_file_sha256":sha256(market_csv_path.read_bytes()).hexdigest(),"source_odds_format":"decimal","timing":MARKET_TIMING_LABEL,
                                   "raw_implied_formula":"1 / decimal_odds","devig":"proportional_normalization","aggregation":"single listed source; no cross-book aggregation required","blend_weight_m0":BLEND_WEIGHT,"blend_weight_market":BLEND_WEIGHT},
            "matching":matching,"same_sample_metrics":same,"market_calibration":{"expected_calibration_error":ece,"bins":cal},
            "correlation_and_disagreement":disagreement_report(matched.m0_probability,matched.market_probability),"incremental_information":chronological_incremental_test(matched),
            "diagnostic_table":{"rows":int(len(matched)),"logical_sha256":diagnostic_table_logical_hash(matched)},
            "guardrails":{"m0_changed_tuned_or_retrained_from_market":False,"roi_bet_threshold_or_profitable_bucket_optimization":False,"market_used_only_as_diagnostic_benchmark":True}}
    result["verdict"]=classify_verdict(result); output_dir.mkdir(parents=True,exist_ok=True)
    matched.to_parquet(output_dir/"m0_market_diagnostic_table_v0.parquet",index=False)
    (output_dir/"diagnostic_result_v0.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (output_dir/"matching_report.json").write_text(json.dumps(matching,indent=2,sort_keys=True,allow_nan=False)+"\n")
    return result
