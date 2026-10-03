#!/usr/bin/env python3
"""Offline source-semantics comparison only. No networking, model access or ingestion."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'inputs'

def read(name):
    with (INPUT / name).open(newline='') as handle:
        return list(csv.DictReader(handle))

def write_csv(name, rows):
    assert rows
    with (ROOT / name).open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)

def main():
    selection = json.loads((ROOT / 'SAMPLE_SELECTION.json').read_text())
    manifest = json.loads((INPUT / 'EVIDENCE_MANIFEST.json').read_text())
    manifest_digest = hashlib.sha256((INPUT / 'EVIDENCE_MANIFEST.json').read_bytes()).hexdigest()
    assert manifest_digest == '6fe5387b3d4b184fc61e2c1c1ca1fe0844daa8b6b6e056ac83e62c86d5dd447b'
    checked = {}
    for source in manifest['sources']:
        name = Path(source['path']).name
        if name in ['fights.csv', 'events.csv', 'fighter_round_stats.csv', 'fighter_round_position.csv', 'source_identity_links.csv']:
            actual = hashlib.sha256((INPUT / name).read_bytes()).hexdigest()
            assert actual == source['sha256'], name
            checked[name] = actual
    assert hashlib.sha256((INPUT / 'fighters.csv').read_bytes()).hexdigest() == '7b1dc1c531c1c086e01f358750991e5eae092c9271a8b99257f1eb2ed4ce73e6'
    fighters = {r['fighter_id']: r['canonical_name'] for r in read('fighters.csv')}
    events = {r['event_id']: r for r in read('events.csv')}
    fights = [r for r in read('fights.csv') if r['promotion'] == 'UFC' and events[r['event_id']]['event_date'] <= '2026-08-15']
    links = read('source_identity_links.csv')
    stats = {(r['fight_id'], r['fighter_id'], int(r['round'])): r for r in read('fighter_round_stats.csv')}
    positions = {(r['fight_id'], r['fighter_id'], int(r['round'])): r for r in read('fighter_round_position.csv')}
    chosen, panel = [], []
    for a, b, year in selection['named_bouts']:
        matches = [r for r in fights if {fighters[r['fighter_a_id']], fighters[r['fighter_b_id']]} == {a, b} and events[r['event_id']]['event_date'].startswith(str(year))]
        assert matches, (a, b, year)
        matches.sort(key=lambda r: (events[r['event_id']]['event_date'], r['fight_id']))
        chosen.append((matches[0], len(matches)))
    sentinel = min((r for r in fights if events[r['event_id']]['event_date'].startswith('2026')), key=lambda r: (events[r['event_id']]['event_date'], r['fight_id']))
    chosen.append((sentinel, 1))
    assert len(chosen) == 28 and len({f['fight_id'] for f, _ in chosen}) == 28
    rows = []
    for number, (fight, match_count) in enumerate(chosen, 1):
        fid = fight['fight_id']
        event = events[fight['event_id']]
        source_ids = [{k:r[k] for k in ['source_name','source_id','source_url','review_status']} for r in links if r['entity_type']=='fight' and r['canonical_id']==fid]
        panel.append({'sample_id':number,'event_date':event['event_date'],'event':event['event_name'],'fighter_a':fighters[fight['fighter_a_id']],'fighter_b':fighters[fight['fighter_b_id']],'division':fight['weight_class'],'fight_id':fid,'identity_matches_in_selected_year':match_count,'selection_note':'earliest-match rule' if match_count>1 else ('2026 earliest-date sentinel' if number==28 else 'named measurement-era panel'),'source_ids_json':json.dumps(source_ids,sort_keys=True),'record_book_status':'NO_BOUT_GROUND_DURATION_ON_INSPECTED_LEADERBOARD_SURFACES','ufcalendar_status':'NOT_ACQUIRED_AUTH_REQUIRED','sportradar_status':'NOT_ACQUIRED_COMMERCIAL_ENTITLEMENT_REQUIRED'})
        for fighter in [fight['fighter_a_id'],fight['fighter_b_id']]:
            for rnd in range(1,int(fight['finish_round'])+1):
                st=stats.get((fid,fighter,rnd),{})
                pos=positions.get((fid,fighter,rnd),{})
                elapsed=300 if rnd<int(fight['finish_round']) else int(fight['finish_time_sec'])
                rows.append({'sample_id':number,'event_date':event['event_date'],'fight_id':fid,'fighter_id':fighter,'fighter':fighters[fighter],'round':rnd,'elapsed_sec':elapsed,'existing_control_sec':st.get('control_sec',''),'existing_sub_attempts':st.get('submission_attempts',''),'existing_ground_sig_landed':st.get('sig_ground_landed',''),'existing_ground_sig_attempted':st.get('sig_ground_attempted',''),'existing_reversals':st.get('reversals',''),'legacy_ground_bucket_min':pos.get('ground_bucket_min',''),'legacy_ground_lower_sec':pos.get('ground_lower_sec',''),'legacy_ground_upper_sec':pos.get('ground_upper_sec',''),'legacy_ground_control_bucket_min':pos.get('ground_control_bucket_min',''),'legacy_standups':pos.get('standups',''),'candidate_ground_sec':'','candidate_top_sec':'','candidate_bottom_sec':'','candidate_control_sec':'','candidate_id':'','candidate_resolution':'UNVERIFIED','missing_reason':'Record Book inspected fight/round surfaces have no ground duration; UFCalendar auth required; Sportradar entitlement required','provenance':'Pinned UFC EDGE core/position; blank candidate values are unobserved, never zero'})
    write_csv('SAMPLE_PANEL.csv', panel)
    write_csv('SAMPLE_ROUND_COMPARISON.csv', rows)
    sample=json.loads((ROOT/'SPORTRADAR_DOCUMENTATION_SAMPLE.json').read_text())
    matches=[r for r in fights if {fighters[r['fighter_a_id']],fighters[r['fighter_b_id']]}=={'Ian Machado Garry','Carlos Prates'} and events[r['event_id']]['event_date']=='2025-04-26']
    assert len(matches)==1
    fight=matches[0]
    supplemental=[]
    for corner, measurements in sample['round_fighter'].items():
        actor=sample['fighters'][corner]
        # The canonical source uses 'Ian Machado Garry'; reject ambiguous identities.
        fighter=next(i for i in [fight['fighter_a_id'],fight['fighter_b_id']] if fighters[i]==actor['name'])
        for m, common in zip(measurements,sample['round_common']):
            assert m['round']==common['round']
            st=stats[(fight['fight_id'],fighter,m['round'])]
            pos=positions.get((fight['fight_id'],fighter,m['round']),{})
            supplemental.append({'event_date':sample['event_date'],'fight_id':fight['fight_id'],'provider_fight_id':sample['fightId'],'fighter':actor['name'],'provider_fighter_id':actor['fighterId'],'provider_ufc_fighter_id':actor['ufcFighterId'],'round':m['round'],'ground_sec':common['ground_sec'],'ground_control_sec':m['ground_control_sec'],'top_sec':'','bottom_sec':'','control_sec':m['control_sec'],'canonical_control_sec':st['control_sec'],'control_equal':int(st['control_sec'])==m['control_sec'],'sub_attempts':m['sub_attempts'],'canonical_sub_attempts':st['submission_attempts'],'ground_sig_landed':m['ground_sig_landed'],'canonical_ground_sig_landed':st['sig_ground_landed'],'ground_sig_attempted':m['ground_sig_attempted'],'canonical_ground_sig_attempted':st['sig_ground_attempted'],'ground_total_landed':m['ground_total_landed'],'ground_total_attempted':m['ground_total_attempted'],'legacy_ground_bucket_min':pos.get('ground_bucket_min',''),'distance_plus_clinch_plus_ground':common['distance_sec']+common['clinch_sec']+common['ground_sec'],'elapsed_sec':common['elapsed_sec'],'measurement_resolution':'one-second display; accuracy unverified','source_evidence_type':sample['evidence_type'],'source_url':sample['source_url']})
    write_csv('SUPPLEMENTAL_DOCUMENTATION_COMPARISON.csv',supplemental)
    validation={'starting_commit':'b8194cd37831348bd856900cba134d05ff21e430','pr158_manifest_digest':manifest_digest,'verified_input_sha256':checked,'fighters_csv_sha256':hashlib.sha256((INPUT/'fighters.csv').read_bytes()).hexdigest(),'panel_fights':len(panel),'panel_fighter_rounds':len(rows),'panel_candidate_ground_observations':0,'supplemental_fights':1,'supplemental_fighter_rounds':len(supplemental),'supplemental_control_exact_matches':sum(r['control_equal'] for r in supplemental),'supplemental_sub_exact_matches':sum(int(r['canonical_sub_attempts'])==r['sub_attempts'] for r in supplemental),'supplemental_ground_sig_landed_matches':sum(int(r['canonical_ground_sig_landed'])==r['ground_sig_landed'] for r in supplemental),'supplemental_ground_sig_attempted_matches':sum(int(r['canonical_ground_sig_attempted'])==r['ground_sig_attempted'] for r in supplemental),'common_partition_sums_match_elapsed':all(r['distance_plus_clinch_plus_ground']==r['elapsed_sec'] for r in supplemental),'ground_seconds_round_sum':sum(r['ground_sec'] for r in sample['round_common']),'ground_control_sum_matches_common_per_round':all(sum(sample['round_fighter'][c][i]['ground_control_sec'] for c in ['red','blue'])==r['ground_sec'] for i,r in enumerate(sample['round_common'])),'divisions':sorted({r['division'] for r in panel}),'panel_date_min':min(r['event_date'] for r in panel),'panel_date_max':max(r['event_date'] for r in panel),'sample_verification_gate':'INCOMPLETE_ACCESS_GATED; one documentation example cannot verify historical backfill','model_fits':0,'frozen_artifacts_modified':False,'prospective_outcomes_read':False}
    assert validation['ground_seconds_round_sum']==175
    assert validation['common_partition_sums_match_elapsed']
    (ROOT/'VALIDATION.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n')
    print(json.dumps(validation,indent=2))

if __name__=='__main__':
    main()
