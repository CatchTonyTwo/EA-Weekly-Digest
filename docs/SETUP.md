# Setup guide for community organizers

You need: a GitHub account (free) and ~30 minutes. No coding, no
terminal, nothing installed on your computer. Everything happens in the
browser.

## Part 1 — Get your own copy (5 min)

1. Log in to github.com (create a free account if needed).
2. Open this repo and click **Fork** (top right) → **Create fork**.
   You now have your own independent copy that you fully control.
3. In *your* fork, go to the **Actions** tab and click
   **"I understand my workflows, go ahead and enable them"**.

## Part 2 — Configure your community (15 min)

Open `config.yaml` in your fork and click the ✏️ pencil to edit. Change:

1. **`community:`** — your name, timezone
   (find yours: en.wikipedia.org/wiki/List_of_tz_database_time_zones),
   and language.
2. **`sources: events:`** — delete the Barcelona sources, add yours:
   - **Luma calendar**: open your calendar page → right-click → View
     page source → Ctrl+F for `cal-` → copy the id (like
     `cal-9tdD2nUvxmygpXa`) into a `luma_ics` block.
   - **Meetup group**: copy the slug from the URL
     (meetup.com/**your-group-name**/) into a `meetup_ics` block.
   - **EA Forum events**: just change `location_keywords` to your city,
     region, country.
3. **`sources: jobs:`** — change the `geo_tiers` labels and facet values
   to your location (e.g. `"Berlin, Germany"` / `"Germany"`). To see
   valid values, open jobs.80000hours.org and look at the Location
   filter list.
4. **`fallback:`** — your evergreen resources for quiet weeks.

Commit the change (green button). Then: **Actions → Weekly digest →
Run workflow**. After ~1 minute, refresh — `output/digest.md` is your
first draft and `output/health.md` shows what worked per source.

## Part 3 — Optional upgrades (5 min each, all free tiers)

Add these as secrets: **Settings → Secrets and variables → Actions →
New repository secret**. All are optional; the digest works without them.

| Secret name | What it unlocks | Where to get it |
|---|---|---|
| `SHEET_WEBHOOK_URL` | Every item logged to a Google Sheet archive | docs/google-sheet-setup.md (5 min, free) |
| `FIRECRAWL_API_KEY` | Sources on JS-heavy sites with no feeds (marked `firecrawl_events` in config) | firecrawl.dev → sign up → API key. Free tier ≈ 100 page-scrapes; a weekly source uses ~4–5/month |
| `ANTHROPIC_API_KEY` | Auto-drafted 1–2 sentence blurbs under each event | console.anthropic.com → API keys. Weekly cost: a few cents |

## Weekly routine (the volunteer job, ~20–30 min)

1. Monday morning: open `output/digest.md` in your repo.
2. Glance at `output/health.md` — any ❌? Check that source manually.
3. Curate: delete what's not relevant, reorder, add your own community
   news, personalise the opening. You're the editor.
4. Spot-check links and deadlines of what you kept.
5. Paste into WhatsApp. Done.

## When something breaks

- One source ❌ in health.md → open its URL in a browser. Site dead?
  Delete its block from config.yaml. Changed? Update the id/slug.
- Everything failing → check Actions tab for the error log; the most
  common cause is a typo in config.yaml (indentation matters in YAML).
- Ask for help → open an Issue on the original repo.
