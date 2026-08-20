#!/usr/bin/env python3
"""Bounded coverage/robots probe for MMA Decisions as a judge-score source.

This does not crawl decision detail pages. It checks robots.txt, then (only if allowed)
fetches the public annual event indexes 1995-current at a slow rate and inventories UFC
event links. The goal is to establish coverage before deciding whether a larger raw
snapshot is appropriate.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE = "https://mmadecisions.com"
UA = "ufc-edge-data/0.2 (private modeling research; bounded coverage probe)"
OUT = Path("provenance/mmadecisions_ufc_coverage_probe.json")
MIN_INTERVAL = 2.0


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.href: str | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = {k: (v or "") for k, v in attrs}
            if d.get("href"):
                self.href = d["href"]
                self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append({"href": self.href, "text": re.sub(r"\s+", " ", " ".join(self.text)).strip()})
            self.href = None
            self.text = []


def get(url: str) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/plain,text/html,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.read(), response.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("content-type", "")


def main() -> int:
    robots_url = BASE + "/robots.txt"
    status, robots_body, robots_ct = get(robots_url)
    robots_text = robots_body.decode("utf-8", errors="replace")
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    if status == 200:
        rp.parse(robots_text.splitlines())
        allowed = rp.can_fetch(UA, BASE + "/decisions-by-event/2026/")
    else:
        # Fail closed: if robots cannot be read, don't fan out.
        allowed = False

    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "robots": {
            "url": robots_url,
            "status": status,
            "content_type": robots_ct,
            "bytes": len(robots_body),
            "sha256": hashlib.sha256(robots_body).hexdigest(),
            "text": robots_text[:10000],
            "annual_event_index_allowed": allowed,
        },
        "years": [],
        "summary": {},
        "decision": {
            "detail_crawl_started": False,
            "rule": "No detail-page acquisition is authorized by this probe. First require readable robots policy and acceptable annual-index coverage.",
        },
    }

    if allowed:
        current_year = datetime.now(timezone.utc).year
        all_ufc_events = []
        for year in range(1995, current_year + 1):
            url = f"{BASE}/decisions-by-event/{year}/"
            status_y, body, ct = get(url)
            parser = AnchorParser()
            if status_y == 200:
                parser.feed(body.decode("utf-8", errors="replace"))
            events = []
            seen = set()
            for link in parser.links:
                absolute = urljoin(url, link["href"])
                p = urlparse(absolute)
                if p.netloc != "mmadecisions.com":
                    continue
                if "/event/" not in p.path or "decisions-by-event" not in p.path:
                    continue
                if not re.search(r"\bUFC\b", link["text"], flags=re.I):
                    continue
                if absolute in seen:
                    continue
                seen.add(absolute)
                events.append({"url": absolute, "title": link["text"]})
            all_ufc_events.extend(events)
            report["years"].append({
                "year": year,
                "url": url,
                "status": status_y,
                "content_type": ct,
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "ufc_event_count": len(events),
                "ufc_events": events,
            })
            if year != current_year:
                time.sleep(MIN_INTERVAL)
        report["summary"] = {
            "years_probed": len(report["years"]),
            "years_with_ufc_events": sum(1 for y in report["years"] if y["ufc_event_count"]),
            "ufc_event_links_total": len(all_ufc_events),
            "first_year_with_ufc": next((y["year"] for y in report["years"] if y["ufc_event_count"]), None),
            "last_year_with_ufc": next((y["year"] for y in reversed(report["years"]) if y["ufc_event_count"]), None),
            "request_interval_seconds": MIN_INTERVAL,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"robots_status={status} allowed={allowed} ufc_events={report.get('summary', {}).get('ufc_event_links_total')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
