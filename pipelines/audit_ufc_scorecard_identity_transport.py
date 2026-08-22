#!/usr/bin/env python3
"""Audit conservative identity transport for official UFC scorecard image candidates.

DATA PHASE ONLY. No OCR and no canonical judge-round scores are produced.

Scorecard media metadata often contains two different bout references: an EVENT HEADLINER
prefix and the ACTUAL IMAGE BOUT after a "scorecard(s)" token. This audit isolates only
bout-local metadata before fighter matching. Alt/title are preferred, but they are subjected
to the same suffix isolation as URLs. Name suffixes (Jr/Sr/II/III/IV) are excluded when
building surname aliases so a fighter such as Raul Rosas Jr. does not make "Rosas" appear
uniquely owned by somebody else.
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
SUFFIX_TOKENS = {"jr", "sr", "ii", "iii", "iv"}
REL_RE = re.compile(r"\b(?:vs|versus|def|defeats|defeated|draw|contest|between|and)\b", re.I)
SCORECARD_RE = re.compile(r"score\s*cards?", re.I)

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


def contains_phrase(hay: str, phrase: str) -> bool:
    return f" {phrase} " in f" {hay} "


def bout_local_text(value: str, require_scorecard_if_present: bool = True) -> str:
    """Return a relation-bearing bout-local fragment with event/headliner prefix removed."""
    decoded = urllib.parse.unquote(value or "")
    matches = list(SCORECARD_RE.finditer(decoded))
    if matches:
        fragment = decoded[matches[-1].end():]
        normalized = ascii_words(fragment)
        return normalized if REL_RE.search(normalized) else ""
    normalized = ascii_words(decoded)
    return normalized if REL_RE.search(normalized) else ""


def url_bout_text(url: str) -> str:
    decoded = urllib.parse.unquote(url or "")
    basename = urllib.parse.urlparse(decoded).path.rsplit("/", 1)[-1]
    basename = re.sub(r"\.(?:png|jpe?g|webp)$", "", basename, flags=re.I)
    # URL fallback is stricter: without a scorecard token we cannot reliably distinguish
    # event/headliner filename material from the image bout, so fail closed.
    matches = list(SCORECARD_RE.finditer(basename))
    if not matches:
        return ""
    fragment = ascii_words(basename[matches[-1].end():])
    return fragment if REL_RE.search(fragment) else ""


def choose_identity_text(row: dict[str, str]) -> tuple[str, str]:
    for source, value in (("image_alt", row.get("image_alt") or ""), ("image_title", row.get("image_title") or "")):
        fragment = bout_local_text(value)
        if fragment:
            return source, fragment
    fragment = url_bout_text(row.get("image_url") or "")
    if fragment:
        return "image_url_scorecard_suffix", fragment
    return "none", ""


def canonical_name_words(value: str) -> list[str]:
    words = ascii_words(value).split()
    while words and words[-1] in SUFFIX_TOKENS:
        words.pop()
    return words


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
        raw_full = ascii_words(name)
        words = canonical_name_words(name)
        if not fid or len(words) < 2:
            continue
        fighter_name[fid] = name
        # Preserve suffix-bearing full display names as full aliases while using suffix-stripped
        # words only for surname ownership.
        full_alias[raw_full].add(fid)
        surname = words[-1]
        if len(surname) >= 4:
            surname_owners[surname].add(fid)
    unique_surname = {s: next(iter(ids)) for s, ids in surname_owners.items() if len(ids) == 1}

    event_by_id = {(r.get("event_id") or "").strip(): r for r in events if (r.get("event_id") or "").strip()}
    pair_fights: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    fights_by_event_pair: dict[tuple[str, tuple[str, str]], list[dict[str, str]]] = defaultdict(list)
    for fight in fights:
        a = (fight.get("fighter_a_id") or "").strip(); b = (fight.get("fighter_b_id") or "").strip()
        event_id = (fight.get("event_id") or "").strip()
        if a and b and a != b and event_id:
            pair = tuple(sorted((a, b)))
            pair_fights[pair].append(fight)
            fights_by_event_pair[(event_id, pair)].append(fight)

    enriched: list[dict[str, Any]] = []
    grouped_pair_events: dict[tuple[str, str], list[set[str]]] = defaultdict(list)
    counts = Counter(); match_count_dist = Counter(); source_counts = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in images:
        source, hay = choose_identity_text(row)
        source_counts[source] += 1
        matched: set[str] = set()
        if hay:
            for alias, ids in full_alias.items():
                if contains_phrase(hay, alias):
                    matched.update(ids)
            for surname, fid in unique_surname.items():
                if contains_phrase(hay, surname):
                    matched.add(fid)
        match_count_dist[len(matched)] += 1
        pair = tuple(sorted(matched)) if len(matched) == 2 else None
        pair_matches = pair_fights.get(pair, []) if pair else []
        article_key = ((row.get("article_candidate_index") or "").strip(), (row.get("article_url") or "").strip())
        event_ids = {(f.get("event_id") or "").strip() for f in pair_matches if (f.get("event_id") or "").strip()}
        if pair and event_ids:
            grouped_pair_events[article_key].append(event_ids)
            counts["images_with_two_fighter_pair_and_canonical_fight"] += 1
        elif len(matched) == 2:
            counts["images_with_two_fighters_no_canonical_pair"] += 1
        else:
            counts["images_without_exact_two_fighter_transport"] += 1
        enriched.append({"row": row, "source": source, "hay": hay, "matched": matched, "pair": pair, "pair_matches": pair_matches, "article_key": article_key})

    article_event: dict[tuple[str, str], str] = {}
    article_status: dict[tuple[str, str], str] = {}
    intersection_dist = Counter()
    for key in {e["article_key"] for e in enriched}:
        sets = grouped_pair_events.get(key, [])
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

    out_rows: list[dict[str, Any]] = []
    mapped_fights: set[str] = set(); mapped_articles: set[tuple[str, str]] = set()
    for item in enriched:
        row = item["row"]; matched = item["matched"]; pair = item["pair"]; pair_matches = item["pair_matches"]
        key = item["article_key"]; event_id = article_event.get(key, "")
        fight_id = ""; candidate_event_id = ""
        if len(matched) != 2:
            status = "not_exact_two_fighter_transport"
        elif not pair_matches:
            status = "no_canonical_fight_for_pair"
        elif not event_id:
            status = "article_event_unresolved"
        else:
            eligible = fights_by_event_pair.get((event_id, pair), []) if pair else []
            if len(eligible) == 1:
                fight_id = (eligible[0].get("fight_id") or "").strip(); candidate_event_id = event_id
                status = "high_confidence_fight_candidate"; counts["images_high_confidence_fight_candidate"] += 1
                mapped_fights.add(fight_id); mapped_articles.add(key)
            elif not eligible:
                status = "pair_not_in_article_event"; counts["images_pair_not_in_article_event"] += 1
            else:
                status = "multiple_same_event_pair_fights"; counts["images_multiple_same_event_pair_fights"] += 1
        event = event_by_id.get(candidate_event_id, {}) if candidate_event_id else {}
        out_rows.append({
            "article_candidate_index": row.get("article_candidate_index") or "", "article_url": row.get("article_url") or "",
            "article_title": row.get("article_title") or "", "article_published_time": row.get("article_published_time") or "",
            "image_url": row.get("image_url") or "", "image_alt": row.get("image_alt") or "", "image_title": row.get("image_title") or "",
            "identity_text_source": item["source"], "identity_text": item["hay"],
            "matched_fighter_ids": "|".join(sorted(matched)), "matched_fighter_names": "|".join(fighter_name.get(fid, "") for fid in sorted(matched)),
            "pair_candidate": "true" if pair else "false", "canonical_pair_fight_count": len(pair_matches),
            "article_candidate_event_id": event_id, "article_consensus_status": article_status.get(key, ""),
            "candidate_fight_id": fight_id, "candidate_event_id": candidate_event_id,
            "candidate_event_name": event.get("event_name") or "", "candidate_event_date": event.get("event_date") or "",
            "identity_status": status, "review_status": "candidate",
        })
        if status in {"article_event_unresolved", "pair_not_in_article_event", "no_canonical_fight_for_pair"} and len(examples[status]) < 30:
            examples[status].append({
                "article_url": row.get("article_url") or "", "image_url": row.get("image_url") or "", "image_alt": row.get("image_alt") or "",
                "identity_text_source": item["source"], "identity_text": item["hay"],
                "matched_names": [fighter_name.get(fid, "") for fid in sorted(matched)], "canonical_pair_fights": len(pair_matches),
                "article_status": article_status.get(key, ""),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_FIELDS, extrasaction="raise"); writer.writeheader(); writer.writerows(out_rows)

    payload = {
        "schema_version": 3,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate_images": len(images), "counts": dict(counts), "identity_text_source_counts": dict(source_counts),
        "image_matched_fighter_count_distribution": {str(k): v for k, v in sorted(match_count_dist.items())},
        "article_event_intersection_count_distribution": {str(k): v for k, v in sorted(intersection_dist.items())},
        "mapped_articles": len(mapped_articles), "mapped_fights": len(mapped_fights), "examples": dict(examples),
        "output": str(OUT.relative_to(ROOT)),
        "decision": {
            "canonical_judge_round_scores_written": False, "ocr_performed": False,
            "display_name_only_identity_trusted": False, "whole_image_url_identity_forbidden": True,
            "event_headliner_prefix_excluded_from_alt_title_and_url": True,
            "name_suffix_aware_surname_uniqueness": True,
            "high_confidence_image_fight_identity_is_candidate_only": True,
            "required_next": "Identity-filter official scorecard images before binary archival. Archive source image bytes plus hashes for the promoted subset before any OCR-derived layer; OCR output remains non-canonical until judge/round/fighter score semantics are independently verified."
        },
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True); AUDIT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_images": len(images), "high_confidence_images": counts["images_high_confidence_fight_candidate"], "mapped_articles": len(mapped_articles), "mapped_fights": len(mapped_fights), "articles_singleton_event_intersection": counts["articles_singleton_event_intersection"], "identity_text_source_counts": dict(source_counts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
