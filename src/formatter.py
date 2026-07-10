"""WhatsApp-formatted digest + health report.

Formatting follows EA Barcelona's announcement conventions:
- emoji + *bold title* per item
- indented `> ` lines for date / location / link
- "(Organised by X)" attribution for events not organised by us
- "Tomorrow" replaces the date line for next-day events
- all times converted to the community timezone (never UTC)
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

EVENT_EMOJI = "🗓️"


def _short_venue(venue):
    """'Sopa Barcelona, Carrer de Roc Boronat, 114, ...' -> 'Sopa Barcelona (Carrer de Roc Boronat, 114)'."""
    parts = [p.strip() for p in venue.split(",") if p.strip()]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} ({parts[1]})"


def _fmt_time(dt):
    s = dt.strftime("%H:%M")
    return s


def _date_line(ev, tz, now_local):
    start = ev["start"].astimezone(tz)
    end = ev["end"].astimezone(tz) if ev.get("end") else None
    day = start.strftime("%A")
    date = f"{start.strftime('%b')} {start.day}"
    if ev.get("all_day"):
        when = f"{day}, {date}"
    elif end and end.date() == start.date():
        when = f"{day}, {date} | {_fmt_time(start)} – {_fmt_time(end)}"
    else:
        when = f"{day}, {date} | {_fmt_time(start)}"
    if start.date() == (now_local + timedelta(days=1)).date():
        # "Tomorrow" rule
        when = f"*Tomorrow* ({when})"
    return f"> 🗓️ {when}"


def format_event(ev, tz, now_local):
    title = f"{EVENT_EMOJI} *{ev['title']}*"
    if not ev["ours"]:
        if ev.get("relevant_note"):
            title += f" _({ev['relevant_note']})_"
        elif ev.get("organizer"):
            title += f" _(Organised by {ev['organizer']})_"
    lines = [title]
    if ev.get("blurb"):
        lines.append(ev["blurb"])
    lines.append(_date_line(ev, tz, now_local))
    venue = _short_venue(ev.get("venue", ""))
    if venue:
        lines.append(f"> 📍 {venue}")
    if ev.get("url"):
        lines.append(f"> 👉 {ev['url']}")
    return "\n".join(lines)


def format_opportunity(it):
    posted = it["posted"].strftime("%b %d")
    return (f"🚀 *{it['title']}*\n"
            f"> 👉 {it['url']}\n"
            f"> _Posted {posted} on the EA Forum_")


def format_job(j, tz):
    head = f"💼 *{j['title']}*" + (f" — {j['org']}" if j["org"] else "")
    lines = [head]
    if j.get("location"):
        lines.append(f"> 🌍 {j['location']}")
    if j.get("closes"):
        lines.append(f"> ⏰ Deadline: {j['closes'].astimezone(tz).strftime('%b %d')}")
    if j.get("url"):
        lines.append(f"> 👉 {j['url']}")
    return "\n".join(lines)


def build_digest(this_week, coming_up, opps, jobs_grouped, cfg, now=None):
    now = now or datetime.now(timezone.utc)
    tz = ZoneInfo(cfg["community"].get("timezone", "UTC"))
    now_local = now.astimezone(tz)
    blocks = []

    blocks.append("👇 *THIS WEEK*")
    if this_week:
        blocks.extend(format_event(e, tz, now_local) for e in this_week)
    else:
        blocks.append("_(no events found for this week)_")

    if coming_up:
        blocks.append("🗓️ *COMING UP SOON*")
        blocks.extend(format_event(e, tz, now_local) for e in coming_up)

    if jobs_grouped or opps:
        blocks.append("🚀 *OPPORTUNITIES & JOBS*")
    for tier, jobs in jobs_grouped:
        blocks.append(f"📍 *{tier}*")
        blocks.extend(format_job(j, tz) for j in jobs)
    if opps:
        if jobs_grouped:
            blocks.append("📰 *From the EA Forum*")
        blocks.extend(format_opportunity(o) for o in opps)

    fb = cfg.get("fallback", {})
    if len(this_week) + len(coming_up) < int(fb.get("min_items", 0)):
        blocks.append("💡 " + fb.get("intro", ""))
        blocks.extend(fb.get("resources", []))

    header = (f"*EA Weekly Digest — {cfg['community']['name']}*\n"
              f"_Draft generated {now_local.strftime('%A, %b %d %H:%M')} "
              f"({cfg['community'].get('timezone')})_. "
              f"_Review, edit, personalise — then send._")
    return header + "\n\n" + "\n\n".join(blocks) + "\n"


def build_health(report, now=None):
    now = now or datetime.now(timezone.utc)
    icons = {"ok": "✅", "empty": "⚠️", "error": "❌", "skipped": "➖"}
    lines = [
        "# Source health report",
        f"Run: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "| Source | Status | Items | Note |",
        "|---|---|---|---|",
    ]
    for r in report:
        lines.append(f"| {r['name']} | {icons.get(r['status'], '?')} {r['status']} "
                     f"| {r['count']} | {r['note']} |")
    lines += [
        "",
        "⚠️ empty = source responded but returned no items. Normal for quiet",
        "sources; investigate if a normally-active source stays empty for weeks.",
        "❌ error = source failed. The digest was still generated without it —",
        "check the source manually and fix or remove it in config.yaml.",
    ]
    return "\n".join(lines) + "\n"
