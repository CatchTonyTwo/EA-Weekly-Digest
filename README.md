# EA Weekly Digest

Automatically collects events and opportunities from your community's
sources every week and drafts a WhatsApp-ready announcement for a
volunteer to review and send. Built by EA Barcelona; designed to be
adopted by any community by editing **one config file**.

**A volunteer's weekly job becomes:** open `output/digest.md`, delete
what's not relevant, personalise the opening, paste into WhatsApp.
~20–30 minutes instead of hours of tab-hopping.

## How it works

- Runs **every Monday morning** on GitHub Actions (free — no server, no
  laptop needed), or on demand via the "Run workflow" button.
- Pulls from free structured feeds — no fragile HTML scraping:
  - **Luma** calendars (ICS)
  - **Meetup** groups (ICS)
  - **EA Forum** events + the *Opportunities to take action* tag (GraphQL)
- Every source is isolated: one broken source never kills the run.
  `output/health.md` tells you exactly what worked and what didn't.
- The digest follows WhatsApp announcement conventions: bold titles,
  `>` detail lines, organiser attribution, "Tomorrow" for next-day
  events, all times in your community's timezone.

## Set up for your community (~30 min, no coding)

1. **Fork this repo** (button top-right on GitHub). Public forks run
   Actions for free.
2. **Edit `config.yaml`** (pencil icon on GitHub — no local setup needed):
   community name, timezone, and your sources. Each source is 3–5 lines;
   the comments in the file explain every type.
   - *Luma calendar id:* open your Luma calendar page, view page source,
     search for `cal-`. (Or open an issue and someone will help.)
   - *Meetup group:* the slug from the URL, e.g. `effective-altruism-madrid`.
3. **Enable workflows**: Actions tab → "I understand… enable".
4. **Test it**: Actions → Weekly digest → Run workflow. After ~1 minute,
   `output/digest.md` and `output/health.md` appear in your repo.

Every Monday, the fresh draft is committed to `output/digest.md`.

## Run locally (optional)

```bash
pip install -r requirements.txt
python run.py
```

## Weekly volunteer checklist

1. Open `output/digest.md`, check `output/health.md` for ❌/⚠️.
2. Curate: delete irrelevant items, reorder, add context or community
   news the tool can't know about. **You are the editor — the tool is
   only a researcher.**
3. Spot-check links and deadlines for the items you keep.
4. Personalise the opening line, paste into WhatsApp, send.

## Maintenance

- A source stopped returning items? Check `health.md`, then its URL in a
  browser. Fix or delete its block in `config.yaml`. You never need to
  touch Python.
- GitHub pauses schedules after 60 days without activity; the weekly
  output commit prevents this. If Actions were disabled (e.g. long
  outage), re-enable in the Actions tab.

## Job boards (v0.2)

Jobs from Algolia-backed boards (80,000 Hours works out of the box)
are grouped by **geographic priority** — e.g. Barcelona > Spain >
Remote Europe > Remote Global — with each job shown only in its
highest-priority tier. Edit the `geo_tiers` in `config.yaml` to match
your community's location. Only jobs posted in the last `max_age_days`
appear, so the digest stays fresh.

To add Probably Good, grab its public search keys from your browser
(instructions in the commented block in `config.yaml`).

## Google Sheet logging (v0.2, optional)

Set a `SHEET_WEBHOOK_URL` secret and every run appends all found items
to a Google Sheet — a searchable archive of everything ever announced.
5-minute setup, no Google Cloud account: see `docs/google-sheet-setup.md`.

## Optional upgrades (v0.3)

Three GitHub secrets unlock extras — each is optional and the digest
runs fine without them (see `docs/SETUP.md`):

- `FIRECRAWL_API_KEY` — enables `firecrawl_events` sources: JS-heavy
  sites with no feeds (e.g. Norrsken). Free tier covers typical weekly
  use for a year+.
- `ANTHROPIC_API_KEY` — an LLM drafts a 1–2 sentence blurb under each
  event from its source description (style rules in
  `prompts/blurb-style.md`; it never invents details). Cents per week.
- `SHEET_WEBHOOK_URL` — logs everything to a Google Sheet archive.

## Roadmap

- v1.0 — adoption guide tested with a second community, EA Forum
  write-up

## License

MIT — use it, fork it, adapt it for your community.
