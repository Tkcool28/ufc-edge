from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ufc_edge.handicap.builders import (
    build_fighter_dossier,
    build_matchup_packet,
    packet_output_guard,
)
from ufc_edge.handicap.output import resolve_output_root
from ufc_edge.handicap.store import CanonicalStore

STAT_FIELDS = [
    "fight_id","fighter_id","round","knockdowns","sig_strikes_landed","sig_strikes_attempted",
    "total_strikes_landed","total_strikes_attempted","takedowns_landed","takedowns_attempted",
    "submission_attempts","reversals","control_sec","sig_head_landed","sig_head_attempted",
    "sig_body_landed","sig_body_attempted","sig_leg_landed","sig_leg_attempted",
    "sig_distance_landed","sig_distance_attempted","sig_clinch_landed","sig_clinch_attempted",
    "sig_ground_landed","sig_ground_attempted",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


@pytest.fixture()
def mini_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    canonical = root / "data/canonical/v0"
    schemas = root / "schemas"
    provenance = root / "provenance"
    canonical.mkdir(parents=True)
    schemas.mkdir()
    provenance.mkdir()

    contract = {
        "contract_version": "0.4.0-draft",
        "tables": {
            "fighters": {"fields": {"fighter_id":{"type":"string"},"canonical_name":{"type":"string"},
                "dob":{"type":"date"},"height_cm":{"type":"number"},"reach_cm":{"type":"number"},
                "stance":{"type":"string"},"nickname":{"type":"string"}}},
            "events": {"fields": {"event_id":{"type":"string"},"event_name":{"type":"string"},
                "event_date":{"type":"date"},"event_start_utc":{"type":"timestamp"},
                "location":{"type":"string"},"promotion":{"type":"string"}}},
            "fights": {"fields": {"fight_id":{"type":"string"},"event_id":{"type":"string"},
                "fighter_a_id":{"type":"string"},"fighter_b_id":{"type":"string"},"winner_id":{"type":"string"},
                "result":{"type":"string"},"method":{"type":"string"},"finish_round":{"type":"integer"},
                "finish_time_sec":{"type":"integer"},"weight_class":{"type":"string"},"scheduled_rounds":{"type":"integer"}}},
            "fighter_round_stats": {"fields": {**{f:{"type":"integer"} for f in STAT_FIELDS if f not in {"fight_id","fighter_id"}},
                "fight_id":{"type":"string"},"fighter_id":{"type":"string"}}},
            "fighter_round_position": {"fields": {"fight_id":{"type":"string"},"fighter_id":{"type":"string"},
                "round":{"type":"integer"},"back_control_bucket_min":{"type":"integer"},
                "back_control_lower_sec":{"type":"integer"},"back_control_upper_sec":{"type":"integer"}}},
            "rankings": {"fields": {"fighter_id":{"type":"string"},"ranking_date":{"type":"date"},
                "weight_class":{"type":"string"},"rank":{"type":"integer"},"ranking_body":{"type":"string"}}},
            "fighter_profile_snapshots": {"fields": {"fighter_id":{"type":"string"},
                "observed_at_utc":{"type":"timestamp"},"listed_weight_lbs":{"type":"number"},
                "listed_weight_class":{"type":"string"},"status_text":{"type":"string"}}},
            "source_identity_links": {"fields": {"entity_type":{"type":"string"},"canonical_id":{"type":"string"},
                "source_name":{"type":"string"},"source_id":{"type":"string"},"review_status":{"type":"string"},
                "source_display_name":{"type":"string"}}},
            "weigh_ins": {"fields": {"weigh_in_observation_id":{"type":"string"},"fight_id":{"type":"string"},
                "fighter_id":{"type":"string"},"weigh_in_date":{"type":"date"},"scale_weight_lbs":{"type":"number"}}},
        },
    }
    (schemas/"canonical_data_contract_v0.json").write_text(json.dumps(contract))
    (schemas/"source_field_map_v0.json").write_text('{"test":true}')
    (schemas/"source_precedence_v0.json").write_text('{"test":true}')

    fighters = [
        {"fighter_id":"fa","canonical_name":"Alpha One","dob":"1990-01-01","height_cm":"180","reach_cm":"182","stance":"Orthodox","nickname":"A"},
        {"fighter_id":"fb","canonical_name":"Bravo Two","dob":"1992-02-02","height_cm":"175","reach_cm":"178","stance":"Southpaw","nickname":"B"},
        {"fighter_id":"fc","canonical_name":"Álpha-One","dob":"1993-03-03","height_cm":"170","reach_cm":"170","stance":"","nickname":""},
    ]
    events = [
        {"event_id":"e1","event_name":"Past UFC","event_date":"2020-01-01","event_start_utc":"2020-01-01T20:00:00Z","location":"X","promotion":"UFC"},
        {"event_id":"e2","event_name":"Future UFC","event_date":"2025-01-01","event_start_utc":"2025-01-01T20:00:00Z","location":"Y","promotion":"UFC"},
    ]
    fights = [
        {"fight_id":"f1","event_id":"e1","fighter_a_id":"fa","fighter_b_id":"fb","winner_id":"fa","result":"W/L","method":"KO/TKO","finish_round":"2","finish_time_sec":"30","weight_class":"Lightweight","scheduled_rounds":"3"},
        {"fight_id":"f2","event_id":"e2","fighter_a_id":"fa","fighter_b_id":"fb","winner_id":"fb","result":"L/W","method":"Decision - Unanimous","finish_round":"3","finish_time_sec":"300","weight_class":"Lightweight","scheduled_rounds":"3"},
    ]

    def stat(fid, fighter, rnd, kd, ctrl):
        row = {f:"" for f in STAT_FIELDS}
        row.update({"fight_id":fid,"fighter_id":fighter,"round":str(rnd),"knockdowns":str(kd),
            "sig_strikes_landed":"10","sig_strikes_attempted":"20","total_strikes_landed":"12",
            "total_strikes_attempted":"22","takedowns_landed":"1","takedowns_attempted":"2",
            "submission_attempts":"0","reversals":"0","control_sec":ctrl,
            "sig_head_landed":"5","sig_head_attempted":"10","sig_body_landed":"3","sig_body_attempted":"5",
            "sig_leg_landed":"2","sig_leg_attempted":"5","sig_distance_landed":"7","sig_distance_attempted":"14",
            "sig_clinch_landed":"2","sig_clinch_attempted":"4","sig_ground_landed":"1","sig_ground_attempted":"2"})
        return row

    stats = [
        stat("f1","fa",0,9,"999"),
        stat("f1","fa",1,1,"60"), stat("f1","fb",1,0,""),
        stat("f1","fa",2,0,"30"), stat("f1","fb",2,0,"10"),
        stat("f2","fa",1,0,"0"), stat("f2","fb",1,0,"0"),
    ]
    positions = [
        {"fight_id":"f1","fighter_id":"fa","round":"1","back_control_bucket_min":"1","back_control_lower_sec":"60","back_control_upper_sec":"119"},
    ]
    rankings = [
        {"fighter_id":"fa","ranking_date":"2019-12-01","weight_class":"LW","rank":"5","ranking_body":"LW"},
        {"fighter_id":"fa","ranking_date":"2024-12-01","weight_class":"LW","rank":"2","ranking_body":"LW"},
    ]
    profiles = [
        {"fighter_id":"fa","observed_at_utc":"2019-12-15T00:00:00Z","listed_weight_lbs":"155","listed_weight_class":"LW","status_text":"Active"},
        {"fighter_id":"fa","observed_at_utc":"2024-12-15T00:00:00Z","listed_weight_lbs":"155","listed_weight_class":"LW","status_text":"Active"},
    ]
    links = [
        {"entity_type":"fighter","canonical_id":"fa","source_name":"greco1899_ufcstats","source_id":"http://ufcstats.com/fighter/fa","review_status":"trusted","source_display_name":"Alpha 1"},
        {"entity_type":"fighter","canonical_id":"fb","source_name":"greco1899_ufcstats","source_id":"http://ufcstats.com/fighter/fb","review_status":"trusted","source_display_name":""},
        {"entity_type":"fighter","canonical_id":"fc","source_name":"other","source_id":"fc","review_status":"candidate","source_display_name":"Alpha One"},
    ]
    weighins = [
        {"weigh_in_observation_id":"w1","fight_id":"f1","fighter_id":"fa","weigh_in_date":"2019-12-31","scale_weight_lbs":"155"},
        {"weigh_in_observation_id":"w2","fight_id":"f2","fighter_id":"fa","weigh_in_date":"2024-12-31","scale_weight_lbs":"155"},
    ]

    _write_csv(canonical/"fighters.csv", list(fighters[0]), fighters)
    _write_csv(canonical/"events.csv", list(events[0]), events)
    _write_csv(canonical/"fights.csv", list(fights[0]), fights)
    _write_csv(canonical/"fighter_round_stats.csv", STAT_FIELDS, stats)
    _write_csv(canonical/"fighter_round_position.csv", ["fight_id","fighter_id","round","back_control_bucket_min","back_control_lower_sec","back_control_upper_sec"], positions)
    _write_csv(canonical/"rankings.csv", list(rankings[0]), rankings)
    _write_csv(canonical/"fighter_profile_snapshots.csv", list(profiles[0]), profiles)
    _write_csv(canonical/"source_identity_links.csv", list(links[0]), links)
    _write_csv(canonical/"weigh_ins.csv", list(weighins[0]), weighins)

    manifest = {
        "canonical_contract_version":"0.4.0-draft",
        "files":[
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(canonical.glob("*.csv"))
        ],
    }
    (canonical/"manifest.json").write_text(json.dumps(manifest))
    frozen_paths = [
        "schemas/canonical_data_contract_v0.json",
        "schemas/source_field_map_v0.json",
        "schemas/source_precedence_v0.json",
        "data/canonical/v0/manifest.json",
    ]
    freeze = {
        "canonical_contract_version":"0.4.0-draft",
        "frozen_files":[{"path":rel,"sha256":_sha(root/rel),"bytes":(root/rel).stat().st_size} for rel in frozen_paths],
    }
    (provenance/"data_phase_freeze_v0.json").write_text(json.dumps(freeze))
    return root


def test_identity_is_fail_closed(mini_repo: Path):
    store = CanonicalStore(mini_repo)
    assert store.resolve_fighter("fa") == "fa"
    assert store.resolve_fighter("Alpha One") == "fa"
    assert store.resolve_fighter("Alpha 1") == "fa"
    assert store.resolve_fighter("alpha 1") == "fa"
    with pytest.raises(KeyError):
        store.resolve_fighter("Alph One")


def test_normalized_ambiguity_fails_closed(mini_repo: Path):
    store = CanonicalStore(mini_repo)
    with pytest.raises(ValueError):
        store.resolve_fighter("alpha one")


def test_cutoff_excludes_future_fight_ranking_profile_and_weighin(mini_repo: Path):
    store = CanonicalStore(mini_repo)
    packet = build_fighter_dossier(store, "fa", "2021-01-01", generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test")
    assert [x["canonical_fight"]["fight_id"] for x in packet["fight_history"]] == ["f1"]
    assert [x["ranking_date"] for x in packet["ranking_history"]] == ["2019-12-01"]
    assert [x["observed_at_utc"] for x in packet["profile_snapshots"]] == ["2019-12-15T00:00:00Z"]
    assert [x["weigh_in_observation_id"] for x in packet["weigh_in_history"]] == ["w1"]


def test_round_zero_missingness_and_control_semantics(mini_repo: Path):
    store = CanonicalStore(mini_repo)
    packet = build_fighter_dossier(store, "fa", "2021-01-01", generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test")
    fight = packet["fight_history"][0]
    assert [r["round"] for r in fight["fighter_round_stats"]] == [1, 2]
    opponent_r1 = fight["opponent_round_stats"][0]
    assert opponent_r1["control_sec"] is None
    pos = fight["fighter_round_position"][0]
    assert pos["back_control_bucket_min"] == 1
    assert pos["back_control_lower_sec"] == 60
    assert fight["fighter_round_stats"][0]["control_sec"] == 60


def test_matchup_contains_both_complete_histories_and_prior_meeting(mini_repo: Path):
    store = CanonicalStore(mini_repo)
    packet = build_matchup_packet(store, "fa", "fb", "2021-01-01", generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test")
    assert packet["fighter_a"]["metadata"]["canonical_fighter_id"] == "fa"
    assert packet["fighter_b"]["metadata"]["canonical_fighter_id"] == "fb"
    assert len(packet["fighter_a"]["fight_history"]) == 1
    assert len(packet["fighter_b"]["fight_history"]) == 1
    assert [x["canonical_fight"]["fight_id"] for x in packet["direct_prior_meetings"]] == ["f1"]
    assert packet["fighter_a"]["fight_history"][0]["fighter_round_stats"][0]["sig_head_landed"] == 5


def test_substantive_determinism_ignores_generation_timestamp(mini_repo: Path):
    store = CanonicalStore(mini_repo)
    p1 = build_matchup_packet(store, "fa", "fb", "2021-01-01", generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test")
    p2 = build_matchup_packet(store, "fa", "fb", "2021-01-01", generated_at=datetime(2026,2,1,tzinfo=timezone.utc), generator_commit_sha="test")
    assert p1["substantive_sha256"] == p2["substantive_sha256"]


def test_output_guard_rejects_non_handicap_path(mini_repo: Path):
    good = mini_repo / "handicap/v0/fighters/fa.json"
    assert packet_output_guard(mini_repo, good) == good.resolve()
    with pytest.raises(ValueError):
        packet_output_guard(mini_repo, mini_repo / "data/canonical/v0/nope.json")


def test_explicit_repo_local_output_cannot_target_protected_paths(mini_repo: Path, tmp_path: Path):
    good = mini_repo / "handicap" / "custom"
    assert resolve_output_root(mini_repo, good) == good.resolve()

    for protected in (
        mini_repo / "data",
        mini_repo / "data/canonical/v0",
        mini_repo / "schemas",
        mini_repo / "provenance",
        mini_repo,
    ):
        with pytest.raises(ValueError, match="repo-local output"):
            resolve_output_root(mini_repo, protected)

    external = tmp_path / "isolated-output"
    assert resolve_output_root(mini_repo, external) == external.resolve()


def test_canonical_csv_corruption_is_rejected(mini_repo: Path):
    corrupted = mini_repo / "data/canonical/v0/fighter_round_stats.csv"
    corrupted.write_text(corrupted.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="canonical table hash mismatch.*fighter_round_stats.csv"):
        CanonicalStore(mini_repo)


def test_delete_and_regenerate_in_memory(mini_repo: Path):
    store = CanonicalStore(mini_repo)
    p1 = build_fighter_dossier(store, "fa", "2021-01-01", generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test")
    out = mini_repo / "handicap/v0/fighters/fa.json"
    out.parent.mkdir(parents=True)
    out.write_text(json.dumps(p1))
    out.unlink()
    p2 = build_fighter_dossier(CanonicalStore(mini_repo), "fa", "2021-01-01", generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test")
    assert p1["substantive_sha256"] == p2["substantive_sha256"]


def test_missing_position_stays_absent_not_zero(mini_repo: Path):
    store = CanonicalStore(mini_repo)
    packet = build_fighter_dossier(store, "fb", "2021-01-01", generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test")
    assert packet["fight_history"][0]["fighter_round_position"] == []


def test_read_only_build_does_not_modify_frozen_inputs(mini_repo: Path):
    protected = [
        mini_repo/"data/canonical/v0/fighters.csv",
        mini_repo/"data/canonical/v0/fights.csv",
        mini_repo/"schemas/canonical_data_contract_v0.json",
        mini_repo/"provenance/data_phase_freeze_v0.json",
    ]
    before = {str(path): _sha(path) for path in protected}
    store = CanonicalStore(mini_repo)
    build_matchup_packet(store, "fa", "fb", "2021-01-01", generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test")
    after = {str(path): _sha(path) for path in protected}
    assert before == after


def test_card_builder_and_unknown_event(mini_repo: Path):
    from ufc_edge.handicap.cards import build_card_packets
    store = CanonicalStore(mini_repo)
    out = mini_repo/"handicap"
    manifest = build_card_packets(
        store, "e1", "2021-01-01", out,
        generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test"
    )
    assert len(manifest["fights"]) == 1
    card_dir = out/"v0/cards/e1"
    assert (card_dir/"manifest.json").exists()
    assert len(list(card_dir.glob("fight_01_*.json"))) == 1
    assert len(list(card_dir.glob("fight_01_*.md"))) == 1
    with pytest.raises(KeyError):
        build_card_packets(
            store, "missing", "2021-01-01", out,
            generated_at=datetime(2026,1,1,tzinfo=timezone.utc), generator_commit_sha="test"
        )
