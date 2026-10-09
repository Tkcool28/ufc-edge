"""Blocked-preflight reports only; no outcome or loss calculation."""
import argparse,json,io,tarfile,lzma,hashlib
import numpy as np
import pandas as pd
from preflight import P,CON,SRC,ROOT,sha,js,csv
from verify_records import verify
OUT=P/'run_v1'
def write(name,text): (OUT/name).write_text(text.rstrip()+'\n')
def table(rows,cols):
    return '| '+' | '.join(cols)+' |\n| '+' | '.join(['---']*len(cols))+' |\n'+'\n'.join('| '+' | '.join(str(r[c]) for c in cols)+' |' for r in rows)
def main():
    result=json.loads((OUT/'PREFLIGHT_RESULT.json').read_text());assert result['status']=='BLOCKED_OPPORTUNITY_FEASIBILITY'
    ap=argparse.ArgumentParser();ap.add_argument('--reuse-validated',action='store_true');args=ap.parse_args()
    if args.reuse_validated:
        seal=json.loads((OUT/'PREDICTION_SEAL.json').read_text())
        for name,digest in seal['hashes'].items():assert sha(OUT/name)==digest,name
        replay=json.loads((OUT/'REGENERATION.json').read_text())
    else:replay=verify()
    js(OUT/'REGENERATION.json',replay)
    records=json.loads((OUT/'opportunity_transition_reward_records.json').read_text());valid=[r for r in records if r['status']=='VALID']
    breaks=json.loads((OUT/'breakdown.json').read_text())
    header=f"Starting main: `{result['starting_main_sha']}`. Branch: `feat/ground-opportunity-consistent-poc-v2`.\n\nStatus: **BLOCKED_OPPORTUNITY_FEASIBILITY**. No target outcomes recovered for scoring; zero outcomes scored.\n"
    spec='''# POC V2 implementation specification

The immutable PR165 contract is authoritative. opportunity.py copies its numeric equations, single bounded TRF solve, bounds, initialization and tolerances unchanged; additional evidence fields retain failed-solver residual/Jacobian/returns. preflight.py reconstructs all original strict-prior abilities and Jan1 division priors and compares every field to the saved PR163 records. It recreates only the primary POC-A transition probabilities for reference verification, never rerunning its ablations.

POC-B changes only total-time TD/SUB/GnP reward to eligible-state hazard mapping and joint finite-round return inversion. Raw control proxy, legacy regularization, bilateral feasibility, standing KO, submission conversion, latent ground KO, priors and round resets are frozen. No projection, reward reduction, multistart, fallback or empirical multiplier. Every required row is attempted; invalid rows are unavailable.

Broadly supported preflight rows require both fighters to meet all four existing PR163 access/control/submission/GnP broad support flags (control: one decision and 15 decision minutes; other dimensions: three measured bouts and 15 minutes). All 4260 outer contexts are attempted and preserved regardless of support. Supported fraction is a descriptor; even 100% supported feasibility would not permit scoring with any invalid outer row.

The saved source archive is verified byte-for-byte. Only prediction-only, ability, pool and primary transition records are parsed; the archive's target-outcome member is hashed but never parsed. Current canonical history is permitted solely for strict-prior ability reconstruction and prior pooling. No evaluation outcomes, prospective confirmation outcomes, archived F or Arm C losses are loaded by this blocked execution. Their original frozen bytes remain in the verified source lock.

Reproduce: python preflight.py from repository root creates run_v1; python verify_records.py regenerates every saved valid/unavailable record exactly. Python3.12, NumPy2.3.5, SciPy1.17.0; pandas2.2.3 lossless saved-float reader. Artifact restoration is byte-exact. Original local replay was bit-identical; cross-runtime solver replay checks the same frozen occupancy/reward/flux/probability tolerances, identical inputs/status/failure codes, and exact deterministic repeated solves within each runtime. It does not require identical low-order floating-point solver/Jacobian bits across Python patch or BLAS builds. No scientific tolerance or solver setting is changed. No scoring is implemented or invoked after this blocked preflight.
'''
    write('POC_V2_IMPLEMENTATION_SPEC.md',spec+header)
    codes=['INVALID_INPUT','INVALID_CONVERSION','INVALID_PROXY_TARGET','INFEASIBLE_SIMPLEX','NO_POSITIVE_RESET_BUDGET','NUMERICAL_RESET_BUDGET','INFEASIBLE_FINITE_ROUND_CEILING','UNRESOLVED_FINITE_ROUND_TARGET','REWARD_RESIDUAL','RESET_FLUX_RESIDUAL','NUMERICAL_TRANSITION']
    counts=[dict(code=k,count=result['failure_codes'].get(k,0)) for k in codes]
    text='# Preflight feasibility\n\n'+header+f"\nSupported: {result['supported_valid_rows']}/{result['supported_rows']} = {100*result['supported_feasibility_fraction']:.6f}%. All outer: {result['valid_outer_rows']}/4260 valid; **{result['invalid_outer_rows']} unavailable**. Required: supported >=99%, outer 100%.\n\n"+table(counts,['code','count'])+'\n\n'
    for dim in ['outer_year','division','support_stratum','scheduled_rounds']:
        cells=[r for r in breaks if r['dimension']==dim];text+=f'## {dim}\n\n'+table(cells,['cell','rows','valid','invalid','certified_structural'])+'\n\n'
    text+=f"Certified necessary-flow/simplex/zero-terminal ceiling failures: {result['certified_structural_rows']}. Other unresolved/numerical rows: {result['unresolved_or_numerical_rows']}. Solver nonconvergence is not a proof of mathematical impossibility. Full code-by-cell counts are in breakdown.json.\n\nClassification **{result['classification']}**: construction is blocked by unresolved numerical inversion; no structural impossibility is certified. This concerns this fixed generic-state mapping and proxy targets, not every possible coarse ground architecture.\n"
    write('POC_V2_PREFLIGHT_FEASIBILITY.md',text)
    write('POC_V2_REWARD_CONSERVATION.md','# Reward conservation\n\n'+header+f"\nAll {len(valid)} valid states meet frozen occupation/reward/flux/probability and closed-form gates. All 18 PR165 synthetic tests and two equation-equivalence tests pass. Every 4260 saved construction record regenerates exactly.\n\n"+json.dumps(replay,indent=2)+'\n\nUnavailable states are not claimed to conserve requested occupancy or rewards. Their failed fits retain residual/Jacobian and achieved shares; certified early rejections have no solver and use null/not-applicable solution fields.\n')
    prediction_rows=[dict(fight_id=r['fight_id'],outer_year=r['outer_year'],status=r['status'],failure_code=r['failure_code'],raw_KO=r.get('raw_KO'),raw_SUB=r.get('raw_SUB'),raw_DEC=r.get('raw_DEC'),K=r.get('K')) for r in records]
    csv(OUT/'prediction_only_UNSEALED.csv',pd.DataFrame(prediction_rows))
    js(OUT/'PREDICTION_SEAL.json',dict(status='NOT_SEALED_FEASIBILITY_BLOCKED',complete_valid_prediction_population=False,outcomes_scored=0,hashes={n:sha(OUT/n) for n in ['ability_records.csv.gz','opportunity_transition_reward_records.json','feasibility_rows.csv','prediction_only_UNSEALED.csv']}))
    write('POC_V2_PREDICTION_SEAL.md','# Prediction seal\n\n'+header+'\nNo complete valid prediction seal exists. prediction_only_UNSEALED.csv retains all ordered 4260 rows, with null model probabilities for unavailable states. Construction/support/hazard/reward records are hashed in PREDICTION_SEAL.json; they are feasibility evidence, not permission to score. No F-composed output is created, no failed row is substituted, and no evaluation outcome table is read.\n')
    for name in ['POC_V2_CONDITIONAL_RESULTS.md','POC_V2_THREE_WAY_RESULTS.md','POC_V2_SUBMISSION_CALIBRATION.md','POC_V2_B3_B5_RESULTS.md','POC_V2_STRIKING_PRESERVATION.md','POC_V2_ARM_C_COMPARISON.md']:
        write(name,'# '+name.removeprefix('POC_V2_').removesuffix('.md').replace('_',' ').title()+'\n\n'+header+'\nNOT SCORED / GATE UNMET: mandatory 100% outer construction failed. No comparison, bootstrap, calibration fit or success gate is evaluated. Saved POC-A and Arm C evidence stays unchanged and source-hash verified.\n')
    for name,dim in [('POC_V2_ANNUAL_RESULTS.md','outer_year'),('POC_V2_SUPPORT_RESULTS.md','support_stratum')]:
        write(name,'# Construction coverage\n\n'+header+'\n'+table([r for r in breaks if r['dimension']==dim],['cell','rows','valid','invalid','certified_structural'])+'\n\nPerformance NOT SCORED. No unsupported performance cell is marked as passing.\n')
    multiplier=[]
    for r in valid:
        for side,m in enumerate(r['multipliers']):multiplier.append(dict(fight_id=r['fight_id'],side=side,**m))
    mf=pd.DataFrame(multiplier);csv(OUT/'implicit_multipliers_valid_only.csv.gz',mf)
    dist=mf[['A','B','C','D']].describe(percentiles=[.05,.25,.5,.75,.95]);csv(OUT/'multiplier_distribution.csv',dist.reset_index(names='statistic'))
    write('POC_V2_IMPLICIT_MULTIPLIERS.md','# Implicit opportunity multipliers\n\n'+header+'\nValid construction rows only; this is a feasibility-conditioned subset and cannot represent the full frozen population. A=SUB hazard/directional total SUB reward; B=SUB hazard/attacker shrunk SUB rate; C=directional total SUB reward/attacker shrunk SUB rate; D=1/actor share. Null for zero denominators.\n\n'+dist.to_string()+'\n\nNo Holmes adjustment comparison is performed because the frozen run could not complete. No multiplier is selected or tuned.\n')
    js(OUT/'scoring_records.json',{'status':'NOT_SCORED_FEASIBILITY_BLOCKED','records':[]})
    js(OUT/'GATE_TABLE.json',{'supported_99_percent':result['supported_feasibility_fraction']>=.99,'outer_100_percent':False,'scientific_scoring_gates':'NOT_SCORED / GATE UNMET','classification':result['classification']})
    write('NEXT_MILESTONE.md','# Next scientific milestone\n\nInvestigate the unresolved finite-round inversions using target-independent mathematics and measurements. Determine whether failed roots reflect solver limits or provable fixed-entry/occupancy contradictions; no structural certificate exists in this run. Any proof or broader numerical diagnostic must preserve the current result and must not score outcomes. Any changed architecture, measurement semantics or feasibility rule requires a separately reviewed contract. Do not tune or run outcome comparisons on the feasible subset. This blocked result does not establish whether opportunity consistency improves predictive performance, whether detailed positions are necessary, or whether every coarse architecture fails.\n')
    # Lossless deterministic records packaging, preserving underlying record hashes.
    large=['ability_records.csv.gz','opportunity_transition_reward_records.json','implicit_multipliers_valid_only.csv.gz','feasibility_rows.csv','prediction_only_UNSEALED.csv']
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w') as t:
        for name in large:
            data=(OUT/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.mode=0o644;t.addfile(info,io.BytesIO(data))
    archive=lzma.compress(buf.getvalue());parts=[]
    for i,start in enumerate(range(0,len(archive),40000)):
        name=f'RECORDS.tar.xz.part{i:03d}';(OUT/name).write_bytes(archive[start:start+40000]);parts.append(dict(name=name,sha256=sha(OUT/name)))
    js(OUT/'RECORDS_MANIFEST.json',dict(archive_sha256=hashlib.sha256(archive).hexdigest(),parts=parts,members={n:sha(OUT/n) for n in large}))
    js(OUT/'EVIDENCE_MANIFEST.json',dict(workflow_sha256=sha(ROOT/'.github/workflows/ground-opportunity-consistent-poc-v2.yml'),starting_main_sha=result['starting_main_sha'],contract_manifest_sha256=sha(CON/'EVIDENCE_MANIFEST.json'),POC_A_manifest_sha256=sha(SRC/'run_v1/EVIDENCE_MANIFEST.json'),source_lock_sha256=sha(CON/'SOURCE_LOCK.json'),artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(P.rglob('*')) if p.is_file() and '__pycache__' not in str(p) and p.name not in large+['EVIDENCE_MANIFEST.json','COMPLETION.json']},restored_records={n:sha(OUT/n) for n in large}))
    js(OUT/'COMPLETION.json',dict(status='BLOCKED_OPPORTUNITY_FEASIBILITY',classification=result['classification'],outcomes_scored=0,evidence_manifest_sha256=sha(OUT/'EVIDENCE_MANIFEST.json'),invalid_outer_rows=result['invalid_outer_rows'],merged=False))
    print('BLOCKED evidence manifest',sha(OUT/'EVIDENCE_MANIFEST.json'),flush=True)
if __name__=='__main__':main()
