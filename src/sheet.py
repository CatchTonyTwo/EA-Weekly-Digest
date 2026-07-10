"""Optional Google Sheet logging via an Apps Script webhook.

Why a webhook instead of the Sheets API: no Google Cloud project, no
service account, no JSON key file. Each community creates a Sheet, adds
a ~10-line Apps Script (see docs/google-sheet-setup.md), deploys it as a
web app, and pastes the URL into a GitHub secret. Total setup: ~5 min.

Enabled when the SHEET_WEBHOOK_URL environment variable is set
(locally or as a GitHub Actions secret). Silently skipped otherwise.
"""

import json
import os
import urllib.request

from .fetchers import UA


def post_to_sheet(this_week, coming_up, opps, jobs_grouped, now):
    url = os.environ.get("SHEET_WEBHOOK_URL", "").strip()
    if not url:
        return "skipped", "SHEET_WEBHOOK_URL not set (optional)"

    run_date = now.strftime("%Y-%m-%d")
    rows = []
    for section, events in (("this_week", this_week), ("coming_up", coming_up)):
        for e in events:
            rows.append([run_date, "event", section, e["title"],
                         e["start"].isoformat() if e["start"] else "",
                         e.get("organizer") or ("us" if e["ours"] else ""),
                         e.get("venue", ""), e.get("url", ""), e["source"]])
    for tier, jobs in jobs_grouped:
        for j in jobs:
            rows.append([run_date, "job", tier, j["title"],
                         j["closes"].isoformat() if j.get("closes") else "",
                         j.get("org", ""), j.get("location", ""),
                         j.get("url", ""), j["source"]])
    for o in opps:
        rows.append([run_date, "opportunity", "forum", o["title"],
                     o["posted"].isoformat(), "", "", o["url"], o["source"]])

    req = urllib.request.Request(
        url, data=json.dumps({"rows": rows}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()
    return "ok", f"{len(rows)} rows appended"
