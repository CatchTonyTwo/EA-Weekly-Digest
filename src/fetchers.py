"""Source fetchers. Each returns (items, note) and NEVER raises:
a failing source is isolated and reported in health.md, the run continues.

Free, structured endpoints only (no scraping of JS pages):
  - Luma ICS:   https://api.lu.ma/ics/get?entity=calendar&id=cal-XXXX
  - Meetup ICS: https://www.meetup.com/<group>/events/ical/
  - EA Forum GraphQL (events view / tag posts)
"""

import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone

UA = "ea-weekly-digest/0.1 (open-source community newsletter tool)"
EAFORUM_GQL = "https://forum.effectivealtruism.org/graphql"


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def gql(query):
    req = urllib.request.Request(
        EAFORUM_GQL,
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# ---------------------------------------------------------------- ICS parsing

def _unfold(text):
    """RFC 5545: continuation lines start with a space or tab."""
    lines = []
    for raw in text.splitlines():
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _unescape(v):
    return (v.replace("\\n", "\n").replace("\\N", "\n")
             .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\"))


def _parse_dt(value):
    """Parse ICS date/datetime. Returns aware UTC datetime, or None."""
    value = value.strip()
    try:
        if value.endswith("Z"):
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        if "T" in value:  # floating local time — treat as UTC (rare in our sources)
            return datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        # all-day event
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_ics(text):
    """Minimal, dependency-free VEVENT parser (fields we need only)."""
    events, cur = [], None
    for line in _unfold(text):
        if line.startswith("BEGIN:VEVENT"):
            cur = {}
        elif line.startswith("END:VEVENT"):
            if cur is not None:
                events.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            key, _, value = line.partition(":")
            name = key.split(";")[0].upper()
            if name == "DTSTART":
                cur["start"] = _parse_dt(value)
                cur["all_day"] = "VALUE=DATE" in key.upper() and "T" not in value
            elif name == "DTEND":
                cur["end"] = _parse_dt(value)
            elif name == "SUMMARY":
                cur["title"] = _unescape(value).strip()
            elif name == "DESCRIPTION":
                cur["description"] = _unescape(value)
            elif name == "LOCATION":
                cur["venue"] = _unescape(value).strip()
            elif name == "URL":
                cur["url"] = value.strip()
    return events


_LUMA_URL_RE = re.compile(r"https://(?:lu\.ma|luma\.com)/[A-Za-z0-9._-]+")


def _finish_event(ev, source_name, organizer, ours, relevant_note):
    # Luma puts the event link inside DESCRIPTION; Meetup uses URL property
    if not ev.get("url"):
        m = _LUMA_URL_RE.search(ev.get("description", "") or "")
        if m:
            ev["url"] = m.group(0)
    venue = ev.get("venue", "") or ""
    if venue.startswith("http"):  # Luma sometimes puts the event URL as location
        venue = ""
    # clean description for the optional blurb layer: drop Luma's
    # "Get up-to-date information at:" line and the Address block
    desc = ev.get("description", "") or ""
    desc = re.sub(r"Get up-to-date information at:\s*\S+", "", desc)
    desc = re.split(r"\n\s*Address:", desc)[0]
    desc = re.sub(r"\s+", " ", desc).strip()[:500]
    return {
        "description": desc,
        "title": ev.get("title", "(untitled)"),
        "start": ev.get("start"),
        "end": ev.get("end"),
        "venue": venue,
        "url": ev.get("url", ""),
        "source": source_name,
        "organizer": organizer,
        "ours": ours,
        "relevant_note": relevant_note,
        "all_day": ev.get("all_day", False),
    }


def _from_ics_url(url, src):
    text = http_get(url)
    n_total = text.count("BEGIN:VEVENT")
    events = []
    for ev in parse_ics(text):
        if ev.get("start") is None:
            continue
        events.append(_finish_event(
            ev, src["name"], src.get("organizer", ""),
            src.get("ours", False), src.get("relevant_note", "")))
    return events, f"{n_total} events in feed"


# ---------------------------------------------------------------- fetchers

def fetch_luma_ics(src):
    url = f"https://api.lu.ma/ics/get?entity=calendar&id={src['calendar_id']}"
    return _from_ics_url(url, src)


def fetch_luma_page(src):
    """Discover cal-XXXX id(s) on a Luma page, then fetch their ICS."""
    html = http_get(src["url"])
    cal_ids = sorted(set(re.findall(r"cal-[A-Za-z0-9]{10,}", html)))
    if not cal_ids:
        return [], ("no Luma calendar found on this page (user profiles without a "
                    "calendar have no feed — ask the organizer for their calendar "
                    "link, or check the page manually: " + src["url"])
    events, notes = [], []
    for cid in cal_ids[:3]:
        evs, note = _from_ics_url(
            f"https://api.lu.ma/ics/get?entity=calendar&id={cid}", src)
        events.extend(evs)
        notes.append(f"{cid}: {note}")
    return events, "; ".join(notes)


def fetch_meetup_ics(src):
    url = f"https://www.meetup.com/{src['group']}/events/ical/"
    return _from_ics_url(url, src)


def fetch_eaforum_events(src):
    limit = int(src.get("limit", 30))
    q = ('{ posts(input: {terms: {view: "events", limit: %d}}) '
         '{ results { title pageUrl startTime endTime location onlineEvent } } }' % limit)
    results = gql(q)["data"]["posts"]["results"]
    keywords = [k.lower() for k in src.get("location_keywords", [])]
    include_online = bool(src.get("include_online", False))
    events, kept = [], 0
    for p in results:
        loc = (p.get("location") or "").lower()
        is_online = bool(p.get("onlineEvent"))
        if keywords and not any(k in loc for k in keywords):
            if not (is_online and include_online):
                continue
        start = p.get("startTime")
        if not start:
            continue
        kept += 1
        events.append({
            "title": p["title"],
            "start": datetime.fromisoformat(start.replace("Z", "+00:00")),
            "end": (datetime.fromisoformat(p["endTime"].replace("Z", "+00:00"))
                    if p.get("endTime") else None),
            "venue": p.get("location") or ("Online" if is_online else ""),
            "url": p["pageUrl"],
            "source": src["name"],
            "organizer": "",
            "ours": False,
            "relevant_note": "",
            "all_day": False,
        })
    return events, f"{len(results)} events on forum, {kept} matched location filter"


def fetch_eaforum_tag(src):
    slug = src["tag_slug"]
    tag_q = ('{ tags(input: {terms: {view: "tagBySlug", slug: "%s"}}) '
             '{ results { _id name } } }' % slug)
    tags = gql(tag_q)["data"]["tags"]["results"]
    if not tags:
        return [], f"tag '{slug}' not found"
    tag_id = tags[0]["_id"]
    limit = int(src.get("limit", 15))
    q = ('{ posts(input: {terms: {view: "tagById", tagId: "%s", limit: %d}}) '
         '{ results { title pageUrl postedAt baseScore } } }' % (tag_id, limit))
    results = gql(q)["data"]["posts"]["results"]
    min_score = int(src.get("min_score", 0))
    items = []
    for p in results:
        if (p.get("baseScore") or 0) < min_score:
            continue
        items.append({
            "title": p["title"],
            "url": p["pageUrl"],
            "posted": datetime.fromisoformat(p["postedAt"].replace("Z", "+00:00")),
            "score": p.get("baseScore", 0),
            "source": src["name"],
        })
    return items, f"{len(results)} posts on tag, {len(items)} above min_score"


# ---------------------------------------------------------- Firecrawl tier

def fetch_firecrawl_events(src):
    """Optional paid tier for JS-heavy sites with no feed (Norrsken,
    Eventbrite discovery pages...). Requires FIRECRAWL_API_KEY env var
    (free tier: 500 credits ≈ 100 page scrapes). Skipped gracefully
    when the key is not set."""
    import os
    api_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        return [], ("skipped — set FIRECRAWL_API_KEY to enable "
                    "(free tier at firecrawl.dev). Check manually: " + src["url"])

    schema = {
        "type": "object",
        "properties": {"events": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "date_iso": {"type": "string"},
                "time": {"type": "string"},
                "location": {"type": "string"},
                "url": {"type": "string"},
            }, "required": ["title"]}}},
        "required": ["events"],
    }
    body = json.dumps({
        "url": src["url"],
        "waitFor": 5000,
        "formats": [{
            "type": "json",
            "prompt": ("Extract all upcoming events listed on this page. For "
                       "each: title, ISO date (YYYY-MM-DD), time if shown, "
                       "city/location, absolute event URL."),
            "schema": schema,
        }],
    }).encode()
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v2/scrape", data=body,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.load(r)
    raw = (data.get("data", {}).get("json", {}) or {}).get("events", [])

    keywords = [k.lower() for k in src.get("filter_keywords", [])]
    now = datetime.now(timezone.utc)
    events, kept = [], 0
    for ev in raw:
        hay = f"{ev.get('title','')} {ev.get('location','')}".lower()
        if keywords and not any(k in hay for k in keywords):
            continue
        start, all_day = None, True
        d = (ev.get("date_iso") or "").strip()[:10]
        try:
            start = datetime.strptime(d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        t = (ev.get("time") or "").strip()
        m = re.match(r"(\d{1,2})[:.]?(\d{2})?\s*(am|pm)?", t, re.I)
        if m and m.group(1):
            h = int(m.group(1))
            ampm = (m.group(3) or "").lower()
            if ampm:  # 12-hour clock: "9 AM" -> 9, "12 AM" -> 0, "3 PM" -> 15
                h = h % 12 + (12 if ampm == "pm" else 0)
            if 0 <= h <= 23:
                start = start.replace(hour=h, minute=int(m.group(2) or 0))
                all_day = False
        if start < now - timedelta(days=1):
            continue
        kept += 1
        events.append({
            "title": ev["title"], "start": start, "end": None,
            "venue": ev.get("location", ""), "url": ev.get("url", ""),
            "source": src["name"], "organizer": src.get("organizer", ""),
            "ours": False, "relevant_note": src.get("relevant_note", ""),
            "all_day": all_day, "description": "",
        })
    return events, f"{len(raw)} events on page, {kept} kept after filters"


# ------------------------------------------------------------- Algolia jobs

def _algolia_query(app_id, api_key, index, params):
    url = f"https://{app_id}-dsn.algolia.net/1/indexes/*/queries"
    body = json.dumps({"requests": [{"indexName": index, "params": params}]}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "X-Algolia-Application-Id": app_id,
        "X-Algolia-API-Key": api_key,
        "Content-Type": "application/json",
        "User-Agent": UA,
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["results"][0]


def fetch_algolia_jobs(src):
    """Job boards backed by Algolia (80,000 Hours; Probably Good once keys
    are configured). Queries one facet filter per geographic tier, in
    priority order; a job appears only in its highest-priority tier."""
    from urllib.parse import quote
    app_id, api_key = src["app_id"], src["api_key"]
    index = src["index"]
    facet_field = src.get("facet_field", "tags_location_80k")
    default_age = int(src.get("max_age_days", 10))
    per_tier = int(src.get("limit_per_tier", 6))
    now_utc = datetime.now(timezone.utc)

    jobs, seen, tier_notes = [], set(), []
    for tier in src.get("geo_tiers", []):
        label = tier["label"]
        # rare local jobs deserve a longer lookback than global remote ones
        max_age_days = int(tier.get("max_age_days", default_age))
        cutoff = now_utc - timedelta(days=max_age_days)
        got = 0
        for facet in tier.get("facets", []):
            ff = quote(json.dumps([[f"{facet_field}:{facet}"]]))
            res = _algolia_query(app_id, api_key, index,
                                 f"facetFilters={ff}&hitsPerPage=50")
            for h in res.get("hits", []):
                oid = str(h.get("objectID"))
                if oid in seen:
                    continue
                posted = h.get("posted_at")
                posted_dt = (datetime.fromtimestamp(posted, tz=timezone.utc)
                             if isinstance(posted, (int, float)) else None)
                if posted_dt and posted_dt < cutoff:
                    continue
                loc_tags = h.get(facet_field) or []
                kw = tier.get("require_keyword")
                if kw and not any(kw.lower() in str(t).lower() for t in loc_tags):
                    continue
                closes = h.get("closes_at")
                closes_dt = (datetime.fromtimestamp(closes, tz=timezone.utc)
                             if isinstance(closes, (int, float)) else None)
                seen.add(oid)
                got += 1
                jobs.append({
                    "title": h.get("title") or h.get("title_80k") or "(untitled)",
                    "org": h.get("company_name") or "",
                    "url": (h.get("url_external")
                            or h.get("company_career_page_url") or ""),
                    "posted": posted_dt,
                    "closes": closes_dt,
                    "tier": label,
                    "location": ", ".join(map(str, (h.get("card_locations")
                                                    or loc_tags)[:2])),
                    "source": src["name"],
                })
                if got >= per_tier:
                    break
            if got >= per_tier:
                break
        tier_notes.append(f"{label}: {got} (≤{max_age_days}d)")
    return jobs, "; ".join(tier_notes)


FETCHERS = {
    "luma_ics": fetch_luma_ics,
    "luma_page": fetch_luma_page,
    "meetup_ics": fetch_meetup_ics,
    "eaforum_events": fetch_eaforum_events,
    "eaforum_tag": fetch_eaforum_tag,
    "algolia_jobs": fetch_algolia_jobs,
    "firecrawl_events": fetch_firecrawl_events,
}


def fetch_source(src):
    """Run one source with full isolation. Returns (items, status, note)."""
    ftype = src.get("type")
    fn = FETCHERS.get(ftype)
    if fn is None:
        return [], "error", f"unknown source type '{ftype}'"
    try:
        items, note = fn(src)
        if not items and note.startswith("skipped"):
            status = "skipped"
        else:
            status = "ok" if items else "empty"
        return items, status, note
    except Exception as e:  # noqa: BLE001 — isolation is the point
        return [], "error", f"{type(e).__name__}: {e}"
