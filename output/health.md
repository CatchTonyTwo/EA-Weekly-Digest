# Source health report
Run: 2026-07-10 10:39 UTC

| Source | Status | Items | Note |
|---|---|---|---|
| EA Barcelona (Luma) | ✅ ok | 74 | 74 events in feed |
| EA UPF (Luma) | ✅ ok | 6 | 6 events in feed |
| All Tech is Human BCN (Luma) | ✅ ok | 8 | 8 events in feed |
| AI Safety Barcelona (Luma user page) | ⚠️ empty | 0 | no Luma calendar found on this page (user profiles without a calendar have no feed — ask the organizer for their calendar link, or check the page manually: https://luma.com/user/aisafetybcn |
| EA Madrid (Meetup) | ⚠️ empty | 0 | 0 events in feed |
| ESALogika (Meetup) | ✅ ok | 1 | 1 events in feed |
| Social Impact Meetups (Meetup) | ⚠️ empty | 0 | 0 events in feed |
| Norrsken events (Firecrawl) | ➖ skipped | 0 | skipped — set FIRECRAWL_API_KEY to enable (free tier at firecrawl.dev). Check manually: https://www.norrsken.org/events |
| EA Forum events | ⚠️ empty | 0 | 17 events on forum, 0 matched location filter |
| EA Forum — Opportunities to take action | ✅ ok | 13 | 15 posts on tag, 13 above min_score |
| 80,000 Hours job board | ✅ ok | 7 | Barcelona: 0 (≤60d); Spain: 1 (≤45d); Remote — Europe: 0 (≤10d); Remote — Global: 6 (≤10d) |
| LLM blurbs | ➖ skipped |  | ANTHROPIC_API_KEY not set (optional) |
| Google Sheet log | ➖ skipped |  | SHEET_WEBHOOK_URL not set (optional) |

⚠️ empty = source responded but returned no items. Normal for quiet
sources; investigate if a normally-active source stays empty for weeks.
❌ error = source failed. The digest was still generated without it —
check the source manually and fix or remove it in config.yaml.
