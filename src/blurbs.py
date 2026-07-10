"""Optional LLM blurb layer.

When the ANTHROPIC_API_KEY env var is set, drafts a 1–2 sentence blurb
for each event that has a usable description, following the style rules
in prompts/blurb-style.md. One cheap Haiku call per run (~€0.01–0.05).
Without the key, the digest simply shows no blurbs — still fully usable.

Design principle: the LLM only REWRITES descriptions that exist. It is
instructed to write nothing rather than invent details, and the code
only ever attaches blurbs to items it sent — hallucinated IDs are dropped.
"""

import json
import os
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5"


def add_blurbs(events, cfg):
    """Attach ev['blurb'] in place. Returns (status, note)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return "skipped", "ANTHROPIC_API_KEY not set (optional)"

    candidates = [e for e in events if len(e.get("description", "")) > 40]
    if not candidates:
        return "empty", "no events had descriptions worth rewriting"

    style = (Path(__file__).parent.parent / "prompts" / "blurb-style.md")
    style_text = style.read_text(encoding="utf-8") if style.exists() else ""
    lang = cfg.get("community", {}).get("language", "en")

    payload = [{"id": i, "title": e["title"],
                "organizer": e.get("organizer") or "us",
                "description": e.get("description", "")}
               for i, e in enumerate(candidates)]
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 1500,
        "system": style_text + f"\nCommunity language: {lang}",
        "messages": [{"role": "user", "content":
                      "Write blurbs for these events. Reply with ONLY a JSON "
                      "object mapping id (as string) to blurb; omit ids where "
                      "no good blurb is possible.\n\n" + json.dumps(payload,
                                                                    ensure_ascii=False)}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.load(r)
    text = "".join(b.get("text", "") for b in resp.get("content", []))
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return "error", "model reply was not JSON"
    blurbs = json.loads(text[start:end + 1])

    n = 0
    for i, ev in enumerate(candidates):
        b = (blurbs.get(str(i)) or "").strip()
        if b:
            ev["blurb"] = b
            n += 1
    return "ok", f"{n}/{len(candidates)} events got blurbs"
