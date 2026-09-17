# Model Validation Bucket Contract V1

Validation terrain is model-independent and pre-registered. Stage A accepts only
allowlisted pre-fight F02 columns and rejects outcome or prediction column families.
Its assignment is immutable within V1; future models join the frozen artifact rather
than regenerating it. Threshold/source changes require V2. Missing rich statistics are
`UNASSIGNABLE_BY_CONTRACT`, never LOW. Performance metrics are N-gated: normal at
N≥100, moderate at 50–99, thin at 25–49, and insufficient below 25. Outcome- and
market-driven threshold selection are prohibited, and prediction files cannot affect
bucket assignment.
