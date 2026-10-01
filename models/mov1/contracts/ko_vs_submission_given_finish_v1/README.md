# MOV1 conditional finish-method contract V1

Read [MOV1_KO_VS_SUBMISSION_GIVEN_FINISH_V1_CONTRACT.md](MOV1_KO_VS_SUBMISSION_GIVEN_FINISH_V1_CONTRACT.md), then its referenced JSON/CSV specifications. This directory freezes decisions for a later run and contains no trained model, predictions or performance results.

Validate without fitting: `python tools/contracts/validate_mov1_contract_v1.py --f02-table /path/to/winner_modeling_table.parquet`. `VALIDATION_EVIDENCE.json` records the frozen source check; `CONTRACT_MANIFEST.json` inventories SHA256. Missing immutable inputs or mismatched hashes fail closed. Do not modify V1 to accommodate a later outcome.
