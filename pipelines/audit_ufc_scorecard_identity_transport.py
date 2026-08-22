#!/usr/bin/env python3
"""Audit conservative identity transport for official UFC scorecard image candidates.

DATA PHASE ONLY. No OCR and no canonical judge-round scores are produced.

Important parsing rule: scorecard image URLs frequently include EVENT HEADLINER names before
"Scorecard(s)" and the ACTUAL IMAGE BOUT after it. Identity matching therefore never scans
the whole URL. It prefers image alt/title text; URL fallback is restricted to the decoded
bout-specific filename suffix after the last scorecard token. If that suffix is not useful,
the URL contributes no fighter identity.

Names remain transport aids only. An image becomes a high-confidence fight candidate only
when its isolated bout metadata resolves exactly two fighters and article-level multi-image
event consensus plus that pair resolves exactly one existing canonical fight.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "data/derived/discovery/ufc_scorecard_image_candidates.csv"
FIGHTERS = ROOT / "data/canonical/v0/fighters.csv"
EVENTS = ROOT / "data/canonical/v0/events.csv"
FIGHTS = ROOT / "data/canonical/v0/fights.csv"
OUT = ROOT / "data/derived/identity/ufc_scorecard_identity_transport_candidate.csv"
AUDIT = ROOT / "provenance/audits/ufc_scorecard_identity_transport_latest.json"

OUT_FIELDS = [
    "article_candidate_index", "article_url", "article_title", "article_published_time",
    "image_url", "image_alt", "image_title", "identity_text_source", "identity_text",
    "matched_fighter_ids", "matched_fighter_names", "pair_candidate",
    "canonical_pair_fight_count", "article_candidate_event_id", "article_consensus_status",
    "candidate_fight_id", "candidate_event_id", "candidate_event_name", "candidate_event_date",
    "identity_status", "review_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def ascii_words(value: str) -> str:
    text = urllib.parse.unquote(value or "")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def name_words(value: str) -> list[str]:
    return ascii_words(value).split()


def contains_phrase(hay: str, phrase: str) -> bool:
    return f" {phrase} " in f" {hay} "


def url_bout_suffix(url: str) -> str:
    """Return only bout-local filename material, never the event/headliner prefix."""
    decoded = urllib.parse.unquote(url or "")
    basename = urllib.parse.urlparse(decoded).path.rsplit("/", 1)[-1]
    basename = re.sub(r"\.(?:png|jpe?g|webp)$", "", basename, flags=re.I)
    # Split on the LAST scorecard/scorecards occurrence; event/headliner text before it is
    # intentionally discarded. Many UFC filenames use separators such as '-', '_', spaces.
    matches = list(re.finditer(r"score\s*cards?", basename, re.I))
    if not matches:
        return ""
    suffix = basename[matches[-1].end():]
    normalized = ascii_words(suffix)
    # A useful fallback must look like a bout/result fragment, not an opaque image id.
    if not re.search(r"\b(?:vs|versus|def|defeats|defeated)\b", normalized):
        return ""
    return normalized


def choose_identity_text(row: dict[str, str]) -> tuple[str, str]:
    alt_title = ascii_words(" ".join((row.get("image_alt") or "", row.get("image_title") or "")))
    # Alt/title is image-local by construction and is preferred whenever it contains a bout
    # relation token. This avoids event-level names in surrounding URL structure.
    if re.search(r"\b(?:vs|versus|def|defeats|defeated|draw|contest)\b", alt_title):
        return "image_alt_title", alt_title
    suffix = url_bout_suffix(row.get("image_url") or "")
    if suffix:
        return "image_url_scorecard_suffix", suffix
    return "none", ""


def match_fighters(
    hay: str,
    full_alias: dict[str, set[str]],
    unique_surname: dict[str, str],
) -> set[str]:
    if not hay:
        return set()
    matched: set[str] = set()
    for alias, ids in full_alias.items():
        if contains_phrase(hay, alias):
            matched.update(ids)
    # Use globally unique surnames only as a fallback for abbreviated filenames. Full-name
    # hits remain in the set; a surname can only add one globally unique fighter.
    for surname, fid in unique_surname.items():
        if contains_phrase(hay, surname):
            matched.add(fid)
    return matched


def main() -> int:
    images = read_csv(IMAGES)
    fighters = read_csv(FIGHTERS)
    events = read_csv(EVENTS)
    fights = read_csv(FIGHTS)

    fighter_name: dict[str, str] = {}
    full_alias: dict[str, set[str]] = defaultdict(set)
    surname_owners: dict[str, set[str]] = defaultdict(set)
    for row in fighters:
        fid = (row.get("fighter_id") or "").strip()
        name = (row.get("canonical_name") or "").strip()
        words = name_words(name)
        if not fid or len(words) < 2:
            continue
        fighter_name[fid] = name
        full_alias[" ".join(words)].add(fid)
        surname = words[-1]
        if len(surname) >= 4:
            surname_owners[surname].add(fid)
    unique_surname = {alias: next(iter(ids)) for alias, ids in surname_owners.items() if len(ids) == 1}

    event_by_id = {
        (row.get("event_id") or "").strip(): row
        for row in events if (row.get("event_id") or "").strip()
    }
    pair_fights: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    fights_by_event_pair: dict[tuple[str, tuple[str, str]], list[dict[str, str]]] = defaultdict(list)
    for row in fights:
        a = (row.get("fighter_a_id") or "").strip()
        b = (row.get("fighter_b_id") or "").strip()
        event_id = (row.get("event_id") or "").strip()
        if a and b and a != b and event_id:
            pair = tuple(sorted((a, b)))
            pair_fights[pair].append(row)
            fights_by_event_pair[(event_id, pair)].append(row)

    enriched: list[dict[str, Any]] = []
    grouped_pair_events: dict[tuple[str, str], list[set[str]]] = defaultdict(list)
    counts = Counter()
    match_count_dist = Counter()
    identity_source_counts = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in images:
        identity_source, identity_text = choose_identity_text(row)
        identity_source_counts[identity_source] += 1
        matched = match_fighters(identity_text, full_alias, unique_surname)
        match_count_dist[len(matched)] += 1
        pair: tuple[str, str] | None = tuple(sorted(matched)) if len(matched) == 2 else None
        pair_matches = pair_fights.get(pair, []) if pair else []
        article_key = ((row.get("article_candidate_index") or "").strip(), (row.get("article_url") or "").strip())
        event_ids = {(fight.get("event_id") or "").strip() for fight in pair_matches if (fight.get("event_id") or "").strip()}
        if pair and event_ids:
            grouped_pair_events[article_key].append(event_ids)
            counts["images_with_two_fighter_pair_and_canonical_fight"] += 1
        elif len(matched) == 2:
            counts["images_with_two_fighters_no_canonical_pair"] += 1
        else:
            counts["images_without_exact_two_fighter_transport"] += 1
        enriched.append({
            "row": row, "matched": matched, "pair": pair, "pair_matches": pair_matches,
            "event_ids": event_ids, "article_key": article_key,
            "identity_source": identity_source, "identity_text": identity_text,
        })

    article_event: dict[tuple[str, str], str] = {}
    article_status: dict[tuple[str, str], str] = {}
    article_intersection_dist = Counter()
    for article_key in {item["article_key"] for item in enriched}:
        sets = grouped_pair_events.get(article_key, [])
        intersection = set.intersection(*sets) if sets else set()
        article_intersection_dist[len(intersection)] += 1
        if len(intersection) == 1:
            article_event[article_key] = next(iter(intersection))
            article_status[article_key] = "singleton_event_intersection_unpromoted"
            counts["articles_singleton_event_intersection"] += 1
        elif not sets:
            article_status[article_key] = "no_resolvable_image_pair"
            counts["articles_no_resolvable_image_pair"] += 1
        elif len(intersection) > 1:
            article_status[article_key] = "multi_event_intersection"
            counts["articles_multi_event_intersection"] += 1
        else:
            article_status[article_key] = "conflicting_image_pair_events"
            counts["articles_conflicting_image_pair_events"] += 1

    output_rows: list[dict[str, Any]] = []
    mapped_fights: set[str] = set()
    mapped_articles: set[tuple[str, str]] = set()
    for item in enriched:
        row = item["row"]
        matched: set[str] = item["matched"]
        pair = item["pair"]
        pair_matches = item["pair_matches"]
        article_key = item["article_key"]
        event_id = article_event.get(article_key, "")
        fight_id = ""
        candidate_event_id = ""
        if len(matched) != 2:
            status = "not_exact_two_fighter_transport"
        elif not pair_matches:
            status = "no_canonical_fight_for_pair"
        elif not event_id:
            status = "article_event_unresolved"
        else:
            eligible = fights_by_event_pair.get((event_id, pair), []) if pair else []
            if len(eligible) == 1:
                fight_id = (eligible[0].get("fight_id") or "").strip()
                candidate_event_id = event_id
                status = "high_confidence_fight_candidate"
                counts["images_high_confidence_fight_candidate"] += 1
                mapped_fights.add(fight_id)
                mapped_articles.add(article_key)
            elif not eligible:
                status = "pair_not_in_article_event"
                counts["images_pair_not_in_article_event"] += 1
            else:
                status = "multiple_same_event_pair_fights"
                counts["images_multiple_same_event_pair_fights"] += 1
        event = event_by_id.get(candidate_event_id, {}) if candidate_event_id else {}
        output_rows.append({
            "article_candidate_index": row.get("article_candidate_index") or "",
            "article_url": row.get("article_url") or "",
            "article_title": row.get("article_title") or "",
            "article_published_time": row.get("article_published_time") or "",
            "image_url": row.get("image_url") or "",
            "image_alt": row.get("image_alt") or "",
            "image_title": row.get("image_title") or "",
            "identity_text_source": item["identity_source"],
            "identity_text": item["identity_text"],
            "matched_fighter_ids": "|".join(sorted(matched)),
            "matched_fighter_names": "|".join(fighter_name.get(fid, "") for fid in sorted(matched)),
            "pair_candidate": "true" if pair else "false",
            "canonical_pair_fight_count": len(pair_matches),
            "article_candidate_event_id": event_id,
            "article_consensus_status": article_status.get(article_key, ""),
            "candidate_fight_id": fight_id,
            "candidate_event_id": candidate_event_id,
            "candidate_event_name": event.get("event_name") or "",
            "candidate_event_date": event.get("event_date") or "",
            "identity_status": status,
            "review_status": "candidate",
        })
        if status in {"article_event_unresolved", "pair_not_in_article_event", "no_canonical_fight_for_pair"} and len(examples[status]) < 30:
            examples[status].append({
                "article_url": row.get("article_url") or "",
                "image_url": row.get("image_url") or "",
                "image_alt": row.get("image_alt") or "",
                "identity_text_source": item["identity_source"],
                "identity_text": item["identity_text"],
                "matched_names": [fighter_name.get(fid, "") for fid in sorted(matched)],
                "canonical_pair_fights": len(pair_matches),
                "article_status": article_status.get(article_key, ""),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, extrasaction="raise")
        writer.writeheader(); writer.writerows(output_rows)

    payload = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_images": len(images),
        "counts": dict(counts),
        "identity_text_source_counts": dict(identity_source_counts),
        "image_matched_fighter_count_distribution": {str(k): v for k, v in sorted(match_count_dist.items())},
        "article_event_intersection_count_distribution": {str(k): v for k, v in sorted(article_intersection_dist.items())},
        "mapped_articles": len(mapped_articles),
        "mapped_fights": len(mapped_fights),
        "examples": dict(examples),
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False,
            "ocr_performed": False,
            "display_name_only_identity_trusted": False,
            "whole_image_url_identity_forbidden": True,
            "event_headliner_prefix_excluded": True,
            "high_confidence_image_fight_identity_is_candidate_only": True,
            "required_next": "Identity-filter official scorecard images before binary archival. Archive source image bytes plus hashes for the promoted subset before any OCR-derived layer; OCR output remains non-canonical until judge/round/fighter score semantics are independently verified."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_images": len(images),
        "high_confidence_images": counts["images_high_confidence_fight_candidate"],
        "mapped_articles": len(mapped_articles),
        "mapped_fights": len(mapped_fights),
        "articles_singleton_event_intersection": counts["articles_singleton_event_intersection"],
        "identity_text_source_counts": dict(identity_source_counts),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
