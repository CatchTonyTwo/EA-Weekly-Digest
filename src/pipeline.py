"""Dedupe, date-window filtering, and sorting."""

from datetime import datetime, timedelta, timezone


def dedupe_events(events):
    seen, out = set(), []
    for ev in sorted(events, key=lambda e: (not e["ours"], e["source"])):
        key = ev["url"] or (ev["title"].lower().strip(),
                            ev["start"].date() if ev["start"] else None)
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
    return out


def split_windows(events, now, this_week_days, coming_up_days):
    week_end = now + timedelta(days=this_week_days)
    coming_end = now + timedelta(days=coming_up_days)
    this_week = [e for e in events if e["start"] and now <= e["start"] < week_end]
    coming_up = [e for e in events if e["start"] and week_end <= e["start"] < coming_end]
    this_week.sort(key=lambda e: e["start"])
    coming_up.sort(key=lambda e: e["start"])
    return this_week, coming_up


def filter_opportunities(items, now, max_age_days):
    cutoff = now - timedelta(days=max_age_days)
    seen, out = set(), []
    for it in sorted(items, key=lambda i: i["posted"], reverse=True):
        if it["posted"] < cutoff or it["url"] in seen:
            continue
        seen.add(it["url"])
        out.append(it)
    return out


def prepare_jobs(jobs, tier_order):
    """Dedupe by URL and group by tier, preserving configured tier order."""
    seen, grouped = set(), {}
    for j in jobs:
        key = j["url"] or (j["title"].lower(), j["org"].lower())
        if key in seen:
            continue
        seen.add(key)
        grouped.setdefault(j["tier"], []).append(j)
    for tier_jobs in grouped.values():
        tier_jobs.sort(key=lambda j: (j["closes"] is None,
                                      j["closes"] or j["posted"]
                                      or datetime.max.replace(tzinfo=timezone.utc)))
    ordered = [t for t in tier_order if t in grouped]
    ordered += [t for t in grouped if t not in ordered]
    return [(t, grouped[t]) for t in ordered]


def run_pipeline(events, opportunities, jobs, cfg, now=None):
    now = now or datetime.now(timezone.utc)
    w = cfg.get("window", {})
    events = dedupe_events(events)
    this_week, coming_up = split_windows(
        events, now,
        int(w.get("this_week_days", 7)),
        int(w.get("coming_up_days", 28)))
    opps = filter_opportunities(
        opportunities, now, int(w.get("opportunities_max_age_days", 10)))
    tier_order = []
    for src in cfg.get("sources", {}).get("jobs", []):
        for tier in src.get("geo_tiers", []):
            if tier["label"] not in tier_order:
                tier_order.append(tier["label"])
    jobs_grouped = prepare_jobs(jobs, tier_order)
    return this_week, coming_up, opps, jobs_grouped
