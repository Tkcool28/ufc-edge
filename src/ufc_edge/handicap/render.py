from __future__ import annotations

from typing import Any

CLASSIC_METRICS = [
    ("KD", "knockdowns"),
    ("SIG", ("sig_strikes_landed", "sig_strikes_attempted")),
    ("TOTAL", ("total_strikes_landed", "total_strikes_attempted")),
    ("TD", ("takedowns_landed", "takedowns_attempted")),
    ("SUB", "submission_attempts"),
    ("REV", "reversals"),
    ("CTRL(s)", "control_sec"),
    ("HEAD", ("sig_head_landed", "sig_head_attempted")),
    ("BODY", ("sig_body_landed", "sig_body_attempted")),
    ("LEG", ("sig_leg_landed", "sig_leg_attempted")),
    ("DIST", ("sig_distance_landed", "sig_distance_attempted")),
    ("CLINCH", ("sig_clinch_landed", "sig_clinch_attempted")),
    ("GROUND", ("sig_ground_landed", "sig_ground_attempted")),
]

POSITION_PREFIXES = [
    "standing",
    "neutral",
    "distance",
    "clinch",
    "ground",
    "ground_control",
    "guard_control",
    "half_guard_control",
    "side_control",
    "mount_control",
    "back_control",
    "misc_ground_control",
]

def _cell(value: Any) -> str:
    if value is None:
        return "—"
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return text

def _pair(row: dict[str, Any] | None, metric: str | tuple[str, str]) -> str:
    if not row:
        return "—"
    if isinstance(metric, tuple):
        return f"{_cell(row.get(metric[0]))}/{_cell(row.get(metric[1]))}"
    return _cell(row.get(metric))

def _position(row: dict[str, Any] | None, prefix: str) -> str:
    if not row:
        return "—"
    bucket = row.get(f"{prefix}_bucket_min")
    lower = row.get(f"{prefix}_lower_sec")
    upper = row.get(f"{prefix}_upper_sec")
    if bucket is None and lower is None and upper is None:
        return "—"
    return f"{_cell(bucket)}m [{_cell(lower)}–{_cell(upper)}s]"

def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["_None available._", ""]
    out = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    out.extend("| " + " | ".join(_cell(v) for v in row) + " |" for row in rows)
    out.append("")
    return out

def _dynamic_table(rows: list[dict[str, Any]], preferred: list[str] | None = None) -> list[str]:
    if not rows:
        return ["_None available._", ""]
    keys: list[str] = []
    preferred = preferred or []
    for key in preferred:
        if any(key in row for row in rows) and key not in keys:
            keys.append(key)
    for row in rows:
        for key in row:
            if key not in keys and not isinstance(row.get(key), (dict, list)):
                keys.append(key)
    rendered = [[row.get(key) for key in keys] for row in rows]
    return _table(keys, rendered)

def _summary_lines(dossier: dict[str, Any]) -> list[str]:
    summary = dossier["descriptive_summary"]
    lines = [
        f"- Observed fights: **{summary['observed_total_fights']}** "
        f"(UFC {summary['observed_ufc_fights']}, external {summary['observed_external_fights']})",
        f"- Results: `{summary['results']}`",
        f"- Method results: `{summary['method_results']}`",
        f"- Observed fighter-round rows: **{summary['total_observed_round_rows']}**",
    ]
    recent = summary.get("most_recent_fight")
    if recent:
        lines.append(
            "- Most recent: "
            f"{_cell(recent.get('event_date'))} vs {_cell(recent.get('opponent_name'))} — "
            f"{_cell(recent.get('result'))} via {_cell(recent.get('method'))}"
        )
    lines.append("")
    lines.append("Raw descriptive round-stat totals include observed/missing denominators in JSON; no missing values are zero-filled.")
    lines.append("")
    return lines

def _fight_history_table(dossier: dict[str, Any]) -> list[str]:
    rows: list[list[Any]] = []
    for item in dossier["fight_history"]:
        fight = item["canonical_fight"]
        event = item.get("event") or {}
        rows.append(
            [
                event.get("event_date"),
                event.get("promotion"),
                event.get("event_name"),
                item.get("opponent_name"),
                item.get("fighter_result"),
                fight.get("method"),
                fight.get("finish_round"),
                fight.get("finish_time_sec"),
                fight.get("weight_class"),
                fight.get("fight_id"),
            ]
        )
    return _table(
        ["Date", "Promotion", "Event", "Opponent", "Result", "Method", "Finish R", "Finish sec", "Weight class", "Fight ID"],
        rows,
    )

def _classic_round_table(item: dict[str, Any]) -> list[str]:
    f_by_round = {row["round"]: row for row in item.get("fighter_round_stats", [])}
    o_by_round = {row["round"]: row for row in item.get("opponent_round_stats", [])}
    rounds = sorted(set(f_by_round).union(o_by_round))
    headers = ["R"]
    for label, _ in CLASSIC_METRICS:
        headers.extend([f"F {label}", f"O {label}"])
    rows: list[list[Any]] = []
    for round_no in rounds:
        frow, orow = f_by_round.get(round_no), o_by_round.get(round_no)
        values: list[Any] = [round_no]
        for _, metric in CLASSIC_METRICS:
            values.extend([_pair(frow, metric), _pair(orow, metric)])
        rows.append(values)
    return _table(headers, rows)

def _position_round_table(item: dict[str, Any]) -> list[str]:
    f_by_round = {row["round"]: row for row in item.get("fighter_round_position", [])}
    o_by_round = {row["round"]: row for row in item.get("opponent_round_position", [])}
    rounds = sorted(set(f_by_round).union(o_by_round))
    headers = ["R"]
    for prefix in POSITION_PREFIXES:
        label = prefix.replace("_", " ")
        headers.extend([f"F {label}", f"O {label}"])
    rows: list[list[Any]] = []
    for round_no in rounds:
        frow, orow = f_by_round.get(round_no), o_by_round.get(round_no)
        values: list[Any] = [round_no]
        for prefix in POSITION_PREFIXES:
            values.extend([_position(frow, prefix), _position(orow, prefix)])
        rows.append(values)
    return _table(headers, rows)

def _fighter_detail(label: str, dossier: dict[str, Any]) -> list[str]:
    name = dossier["metadata"]["canonical_fighter_name"]
    lines = [f"## {label}: {name}", "", "### Descriptive summary", ""]
    lines.extend(_summary_lines(dossier))
    lines.extend(["### Complete fight history", ""])
    lines.extend(_fight_history_table(dossier))

    lines.extend(["### Round-by-round classic stats", ""])
    lines.append("`F` = dossier fighter; `O` = opponent. Landed/attempted fields are shown as `L/A`.")
    lines.append("")
    for item in dossier["fight_history"]:
        fight = item["canonical_fight"]
        event = item.get("event") or {}
        lines.append(
            f"#### {_cell(event.get('event_date'))} — {name} vs {_cell(item.get('opponent_name'))} "
            f"(`{_cell(fight.get('fight_id'))}`)"
        )
        lines.append("")
        lines.extend(_classic_round_table(item))

    lines.extend(["### Positional / TIP evidence", ""])
    lines.append(
        "Values are canonical whole-minute floor buckets with explicit second bounds; "
        "they are **not exact elapsed seconds** and remain distinct from classic `control_sec`."
    )
    lines.append("")
    any_position = False
    for item in dossier["fight_history"]:
        if item.get("fighter_round_position") or item.get("opponent_round_position"):
            any_position = True
            fight = item["canonical_fight"]
            event = item.get("event") or {}
            lines.append(
                f"#### {_cell(event.get('event_date'))} — {name} vs {_cell(item.get('opponent_name'))} "
                f"(`{_cell(fight.get('fight_id'))}`)"
            )
            lines.append("")
            lines.extend(_position_round_table(item))
    if not any_position:
        lines.extend(["_No eligible positional/TIP evidence available._", ""])

    lines.extend(["### Fight-specific weigh-ins", ""])
    lines.extend(
        _dynamic_table(
            dossier.get("weigh_in_history", []),
            ["weigh_in_date", "fight_id", "fighter_id", "scale_weight_lbs", "weigh_in_observation_id"],
        )
    )
    lines.extend(["### Ranking history", ""])
    lines.extend(
        _dynamic_table(
            dossier.get("ranking_history", []),
            ["ranking_date", "weight_class", "rank", "ranking_body", "fighter_id"],
        )
    )
    lines.extend(["### Official profile snapshots", ""])
    lines.extend(
        _dynamic_table(
            dossier.get("profile_snapshots", []),
            ["observed_at_utc", "listed_weight_lbs", "listed_weight_class", "status_text", "gym_text"],
        )
    )
    return lines

def render_matchup_markdown(packet: dict[str, Any]) -> str:
    meta = packet["metadata"]
    a = packet["fighter_a"]
    b = packet["fighter_b"]
    a_name = meta["fighter_a"]["name"]
    b_name = meta["fighter_b"]["name"]
    lines: list[str] = [
        f"# {a_name} vs {b_name} — H00 Handicap Packet",
        "",
        "## Packet metadata / cutoff",
        "",
        f"- Packet schema: `{meta['packet_schema_version']}`",
        f"- DATA contract: `{meta['data_contract_version']}`",
        f"- Information cutoff: **{meta['information_cutoff']}**",
        f"- Generated at: `{meta['generated_at_utc']}`",
        f"- Generator: `{meta['generator_version']}` @ `{meta.get('generator_commit')}`",
        f"- Canonical manifest: `{meta['canonical_manifest']['path']}` "
        f"SHA-256 `{meta['canonical_manifest']['sha256']}`",
        f"- DATA freeze: `{meta['data_freeze']['path']}`",
        "",
        "## Identity / physical context",
        "",
    ]
    a_phys = a["fighter"]["identity_physical_context"]
    b_phys = b["fighter"]["identity_physical_context"]
    fields = ["canonical_name", "dob", "age_as_of_cutoff", "height_cm", "reach_cm", "stance", "nickname"]
    identity_rows = [[field, a_phys.get(field), b_phys.get(field)] for field in fields]
    lines.extend(_table(["Field", a_name, b_name], identity_rows))

    lines.extend(["## Direct prior meetings", ""])
    direct_rows: list[list[Any]] = []
    for item in packet.get("direct_prior_meetings", []):
        fight = item["canonical_fight"]
        event = item.get("event") or {}
        direct_rows.append(
            [
                event.get("event_date"),
                event.get("event_name"),
                item.get("fighter_result"),
                fight.get("method"),
                fight.get("finish_round"),
                fight.get("finish_time_sec"),
                fight.get("fight_id"),
            ]
        )
    lines.extend(_table(["Date", "Event", f"{a_name} result", "Method", "Finish R", "Finish sec", "Fight ID"], direct_rows))

    lines.extend(_fighter_detail("Fighter A", a))
    lines.extend(_fighter_detail("Fighter B", b))

    lines.extend(["## Opponent index", ""])
    opponent_rows: list[list[Any]] = []
    for opponent in packet.get("opponent_index", []):
        meetings = opponent.get("meetings", [])
        opponent_rows.append(
            [
                opponent.get("name"),
                opponent.get("canonical_opponent_id"),
                ", ".join(opponent.get("faced_by", [])),
                "; ".join(
                    f"{m.get('event_date')} {m.get('result')} {m.get('method')} ({m.get('fight_id')})"
                    for m in meetings
                ),
                opponent.get("optional_dossier_path"),
            ]
        )
    lines.extend(_table(["Opponent", "Canonical ID", "Faced by", "Meeting context", "Optional dossier"], opponent_rows))

    lines.extend(["## Missing-data / semantic warnings", ""])
    lines.extend(f"- {warning}" for warning in meta.get("warnings", []))
    lines.extend(
        [
            "",
            "## Canonical / provenance references",
            "",
            f"- `{meta['canonical_manifest']['path']}`",
            f"- `{meta['data_freeze']['path']}`",
            f"- `{meta['field_provenance']['path']}`",
            "",
            "H00 is a disposable read-only view. Canonical DATA and its frozen provenance remain authoritative.",
            "",
        ]
    )
    return "\n".join(lines)
