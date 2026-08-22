#!/usr/bin/env python3
"""Fail-closed identity audit for official UFC scorecard image candidates.

DATA PHASE ONLY. No OCR and no canonical judge-round scores are produced.

Identity text must come from the bout-local suffix after the final scorecard(s) token in the
image URL, alt text, or title. That text is split into LEFT/RIGHT fighter phrases before any
fighter matching. Each whole side phrase must match a trailing phrase of exactly one canonical
fighter name; free-floating surname-token matching is forbidden. Rematches are disambiguated
only through article-level canonical-event consensus.
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

SCORECARD_RE = re.compile(r"score\s*cards?", re.I)
REL_SPLIT_RE = re.compile(r"\b(?:vs\.?|versus|def\.?|defeats|defeated)\b", re.I)
NAME_SUFFIXES = {"jr", "sr", "ii", "iii", "iv"}
TRAILING_NOISE = {
    "official", "result", "results", "score", "scores", "scorecard", "scorecards",
    "decision", "unanimous", "split", "majority", "draw", "ufc",
}

OUT_FIELDS = [
    "article_candidate_index", "article_url", "article_title", "article_published_time",
    "image_url", "image_alt", "image_title", "identity_text_source", "identity_text",
    "fighter_left_phrase", "fighter_right_phrase", "left_candidate_count", "right_candidate_count",
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


def strip_name_suffixes(words: list[str]) -> list[str]:
    words = list(words)
    while words and words[-1] in NAME_SUFFIXES:
        words.pop()
    return words


def scorecard_suffix(value: str) -> str:
    decoded = urllib.parse.unquote(value or "")
    matches = list(SCORECARD_RE.finditer(decoded))
    if not matches:
        return ""
    suffix = ascii_words(decoded[matches[-1].end():])
    return suffix if REL_SPLIT_RE.search(suffix) else ""


def url_scorecard_suffix(url: str) -> str:
    decoded = urllib.parse.unquote(url or "")
    basename = urllib.parse.urlparse(decoded).path.rsplit("/", 1)[-1]
    basename = re.sub(r"\.(?:png|jpe?g|webp)$", "", basename, flags=re.I)
    return scorecard_suffix(basename)


def choose_identity_text(row: dict[str, str]) -> tuple[str, str]:
    suffix = url_scorecard_suffix(row.get("image_url") or "")
    if suffix:
        return "image_url_scorecard_suffix", suffix
    for source, value in (
        ("image_alt_scorecard_suffix", row.get("image_alt") or ""),
        ("image_title_scorecard_suffix", row.get("image_title") or ""),
    ):
        suffix = scorecard_suffix(value)
        if suffix:
            return source, suffix
    return "none", ""


def clean_side(value: str) -> str:
    words = ascii_words(value).split()
    while words and (words[-1] in TRAILING_NOISE or words[-1].isdigit()):
        words.pop()
    return " ".join(words)


def split_bout(text: str) -> tuple[str, str] | None:
    parts = REL_SPLIT_RE.split(text, maxsplit=1)
    if len(parts) != 2:
        return None
    left, right = clean_side(parts[0]), clean_side(parts[1])
    if not left or not right:
        return None
    return left, right


def build_trailing_phrase_index(fighters: list[dict[str, str]]) -> tuple[dict[str, set[str]], dict[str, str]]:
    index: dict[str, set[str]] = defaultdict(set)
    names: dict[str, str] = {}
    for row in fighters:
        fid = (row.get("fighter_id") or "").strip()
        name = (row.get("canonical_name") or "").strip()
        words = ascii_words(name).split()
        if not fid or len(words) < 2:
            continue
        names[fid] = name
        # Keep a suffix-bearing full phrase too, but build ordinary trailing phrases after
        # stripping Jr/Sr/roman suffixes so "Rosas" can map to "Raul Rosas Jr" correctly.
        raw_phrase = " ".join(words)
        index[raw_phrase].add(fid)
        base_words = strip_name_suffixes(words)
        for width in range(1, min(4, len(base_words)) + 1):
            phrase_words = base_words[-width:]
            if width == 1 and len(phrase_words[0]) < 4:
                continue
            index[" ".join(phrase_words)].add(fid)
    return index, names


def main() -> int:
    images = read_csv(IMAGES)
    fighters = read_csv(FIGHTERS)
    events = read_csv(EVENTS)
    fights = read_csv(FIGHTS)
    phrase_index, fighter_name = build_trailing_phrase_index(fighters)

    event_by_id = {(r.get("event_id") or "").strip(): r for r in events if (r.get("event_id") or "").strip()}
    pair_fights: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    fights_by_event_pair: dict[tuple[str, tuple[str, str]], list[dict[str, str]]] = defaultdict(list)
    for fight in fights:
        event_id = (fight.get("event_id") or "").strip()
        a = (fight.get("fighter_a_id") or "").strip()
        b = (fight.get("fighter_b_id") or "").strip()
        if event_id and a and b and a != b:
            pair = tuple(sorted((a, b)))
            pair_fights[pair].append(fight)
            fights_by_event_pair[(event_id, pair)].append(fight)

    counts = Counter(); source_counts = Counter(); side_candidate_dist = Counter()
    article_pair_event_sets: dict[tuple[str, str], list[set[str]]] = defaultdict(list)
    enriched: list[dict[str, Any]] = []

    for row in images:
        source, text = choose_identity_text(row)
        source_counts[source] += 1
        split = split_bout(text) if text else None
        left = right = ""; left_ids: set[str] = set(); right_ids: set[str] = set()
        if split:
            left, right = split
            left_ids = set(phrase_index.get(left, set()))
            right_ids = set(phrase_index.get(right, set()))
        side_candidate_dist[f"{len(left_ids)}x{len(right_ids)}"] += 1

        pair = None
        if len(left_ids) == 1 and len(right_ids) == 1:
            a = next(iter(left_ids)); b = next(iter(right_ids))
            if a != b:
                pair = tuple(sorted((a, b)))
        pair_matches = pair_fights.get(pair, []) if pair else []
        article_key = ((row.get("article_candidate_index") or "").strip(), (row.get("article_url") or "").strip())
        event_ids = {(f.get("event_id") or "").strip() for f in pair_matches if (f.get("event_id") or "").strip()}
        if pair and event_ids:
            counts["images_with_unique_side_pair_and_canonical_fight"] += 1
            article_pair_event_sets[article_key].append(event_ids)
        elif pair:
            counts["images_with_unique_side_pair_no_canonical_fight"] += 1
        else:
            counts["images_without_unique_side_pair"] += 1
        enriched.append({
            "row": row, "source": source, "text": text, "left": left, "right": right,
            "left_ids": left_ids, "right_ids": right_ids, "pair": pair,
            "pair_matches": pair_matches, "article_key": article_key,
        })

    article_event: dict[tuple[str, str], str] = {}; article_status: dict[tuple[str, str], str] = {}
    intersection_dist = Counter()
    for key in {e["article_key"] for e in enriched}:
        sets = article_pair_event_sets.get(key, [])
        intersection = set.intersection(*sets) if sets else set()
        intersection_dist[len(intersection)] += 1
        if len(intersection) == 1:
            article_event[key] = next(iter(intersection)); article_status[key] = "singleton_event_intersection_unpromoted"
            counts["articles_singleton_event_intersection"] += 1
        elif not sets:
            article_status[key] = "no_resolvable_image_pair"; counts["articles_no_resolvable_image_pair"] += 1
        elif len(intersection) > 1:
            article_status[key] = "multi_event_intersection"; counts["articles_multi_event_intersection"] += 1
        else:
            article_status[key] = "conflicting_image_pair_events"; counts["articles_conflicting_image_pair_events"] += 1

    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    out_rows: list[dict[str, Any]] = []; mapped_fights: set[str] = set(); mapped_articles: set[tuple[str, str]] = set()
    for item in enriched:
        row = item["row"]; pair = item["pair"]; pair_matches = item["pair_matches"]; key = item["article_key"]
        consensus_event = article_event.get(key, ""); fight_id = ""; candidate_event_id = ""
        if not pair:
            status = "side_phrase_not_uniquely_resolved"
        elif not pair_matches:
            status = "no_canonical_fight_for_pair"
        elif not consensus_event:
            status = "article_event_unresolved"
        else:
            eligible = fights_by_event_pair.get((consensus_event, pair), [])
            if len(eligible) == 1:
                fight_id = (eligible[0].get("fight_id") or "").strip(); candidate_event_id = consensus_event
                status = "high_confidence_fight_candidate"; counts["images_high_confidence_fight_candidate"] += 1
                mapped_fights.add(fight_id); mapped_articles.add(key)
            elif not eligible:
                status = "pair_not_in_article_event"; counts["images_pair_not_in_article_event"] += 1
            else:
                status = "multiple_same_event_pair_fights"; counts["images_multiple_same_event_pair_fights"] += 1
        event = event_by_id.get(candidate_event_id, {}) if candidate_event_id else {}
        matched_ids = sorted(set(item["left_ids"]) | set(item["right_ids"])) if pair else []
        out_rows.append({
            "article_candidate_index": row.get("article_candidate_index") or "", "article_url": row.get("article_url") or "",
            "article_title": row.get("article_title") or "", "article_published_time": row.get("article_published_time") or "",
            "image_url": row.get("image_url") or "", "image_alt": row.get("image_alt") or "", "image_title": row.get("image_title") or "",
            "identity_text_source": item["source"], "identity_text": item["text"],
            "fighter_left_phrase": item["left"], "fighter_right_phrase": item["right"],
            "left_candidate_count": len(item["left_ids"]), "right_candidate_count": len(item["right_ids"]),
            "matched_fighter_ids": "|".join(matched_ids), "matched_fighter_names": "|".join(fighter_name.get(fid, "") for fid in matched_ids),
            "pair_candidate": "true" if pair else "false", "canonical_pair_fight_count": len(pair_matches),
            "article_candidate_event_id": consensus_event, "article_consensus_status": article_status.get(key, ""),
            "candidate_fight_id": fight_id, "candidate_event_id": candidate_event_id,
            "candidate_event_name": event.get("event_name") or "", "candidate_event_date": event.get("event_date") or "",
            "identity_status": status, "review_status": "candidate",
        })
        if status != "high_confidence_fight_candidate" and len(examples[status]) < 30:
            examples[status].append({
                "article_url": row.get("article_url") or "", "image_url": row.get("image_url") or "",
                "identity_text": item["text"], "left": item["left"], "right": item["right"],
                "left_candidates": [fighter_name.get(fid, "") for fid in sorted(item["left_ids"])],
                "right_candidates": [fighter_name.get(fid, "") for fid in sorted(item["right_ids"])],
                "canonical_pair_fights": len(pair_matches), "article_status": article_status.get(key, ""),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, extrasaction="raise"); writer.writeheader(); writer.writerows(out_rows)

    payload = {
        "schema_version": 5,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_images": len(images), "counts": dict(counts), "identity_text_source_counts": dict(source_counts),
        "side_candidate_count_distribution": dict(side_candidate_dist),
        "article_event_intersection_count_distribution": {str(k): v for k, v in sorted(intersection_dist.items())},
        "mapped_articles": len(mapped_articles), "mapped_fights": len(mapped_fights), "examples": dict(examples),
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False, "ocr_performed": False,
            "display_name_only_identity_trusted": False, "scorecard_token_required_for_identity_text": True,
            "generic_hero_alt_identity_forbidden": True, "free_floating_surname_match_forbidden": True,
            "whole_side_trailing_name_phrase_required": True, "rematch_disambiguation_requires_article_event_consensus": True,
            "high_confidence_image_fight_identity_is_candidate_only": True,
            "required_next": "Review v5 residual ambiguity/error examples. Only after the identity transport is clean should the selected official image bytes be archived with hashes before OCR."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True); AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_images": len(images), "high_confidence_images": counts["images_high_confidence_fight_candidate"],
        "mapped_articles": len(mapped_articles), "mapped_fights": len(mapped_fights),
        "articles_singleton_event_intersection": counts["articles_singleton_event_intersection"],
        "articles_conflicting_image_pair_events": counts["articles_conflicting_image_pair_events"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
