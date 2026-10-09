# Opportunity-consistent ground pathway POC V2

Frozen PR165 execution from main 222c7a76bc75bd66e0517930863ebeab41baf99f. Read run_v1/POC_V2_PREFLIGHT_FEASIBILITY.md first. The full preflight is blocked; no outcome scoring occurred. Every unavailable row remains explicit, and no correction or fallback was selected.

Install requirements.txt on Python3.12. Run publish_evidence.py to verify all hashes, losslessly restore saved records, and regenerate every valid/unavailable construction. The large records are deterministic archive parts; RECORDS_MANIFEST.json specifies every part and member hash. Run preflight.py --output /tmp/poc-v2-replay for complete strict-prior ability/reference reconstruction plus all outer construction attempts. It does not recover evaluation outcomes. report.py regenerates the blocked reports and packaging after saved-record replay. No merge or promotion.
