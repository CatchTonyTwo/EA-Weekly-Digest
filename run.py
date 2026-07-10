#!/usr/bin/env python3
"""EA Weekly Digest — entry point.

Usage:
    python run.py [--config config.yaml]

Fetches all configured sources (each isolated — one broken source never
kills the run), then writes to the output dir:
    digest.md   WhatsApp-formatted draft for a volunteer to review & send
    health.md   per-source status report
    items.json  raw structured data (for the Google Sheet step, v0.2)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from src.fetchers import fetch_source
from src.pipeline import run_pipeline
from src.formatter import build_digest, build_health
from src.sheet import post_to_sheet
from src.blurbs import add_blurbs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)

    events, opportunities, jobs, report = [], [], [], []
    for kind, bucket in (("events", events), ("opportunities", opportunities),
                         ("jobs", jobs)):
        for src in cfg.get("sources", {}).get(kind, []):
            items, status, note = fetch_source(src)
            bucket.extend(items)
            report.append({"name": src.get("name", "?"), "status": status,
                           "count": len(items), "note": note})
            print(f"[{status:^5}] {src.get('name'):45s} {len(items):3d} items  {note}")

    this_week, coming_up, opps, jobs_grouped = run_pipeline(
        events, opportunities, jobs, cfg, now)

    try:
        blurb_status, blurb_note = add_blurbs(this_week + coming_up, cfg)
    except Exception as e:  # blurbs are cosmetic — never kill the digest
        blurb_status, blurb_note = "error", f"{type(e).__name__}: {e}"
    report.append({"name": "LLM blurbs", "status": blurb_status,
                   "count": "", "note": blurb_note})

    try:
        sheet_status, sheet_note = post_to_sheet(
            this_week, coming_up, opps, jobs_grouped, now)
    except Exception as e:  # sheet failure must not kill the digest
        sheet_status, sheet_note = "error", f"{type(e).__name__}: {e}"
    report.append({"name": "Google Sheet log", "status": sheet_status,
                   "count": "", "note": sheet_note})

    out = Path(cfg.get("output", {}).get("dir", "output"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "digest.md").write_text(
        build_digest(this_week, coming_up, opps, jobs_grouped, cfg, now),
        encoding="utf-8")
    (out / "health.md").write_text(build_health(report, now), encoding="utf-8")

    def ser(o):
        return o.isoformat() if isinstance(o, datetime) else str(o)
    (out / "items.json").write_text(json.dumps(
        {"generated": now.isoformat(),
         "this_week": this_week, "coming_up": coming_up,
         "opportunities": opps,
         "jobs": {tier: js for tier, js in jobs_grouped}},
        default=ser, indent=2, ensure_ascii=False), encoding="utf-8")

    n_jobs = sum(len(js) for _, js in jobs_grouped)
    print(f"\nDigest: {len(this_week)} this week, {len(coming_up)} coming up, "
          f"{n_jobs} jobs, {len(opps)} opportunities -> {out / 'digest.md'}")
    errors = [r for r in report if r["status"] == "error"]
    if errors:
        print(f"⚠️  {len(errors)} source(s) failed — see {out / 'health.md'}")


if __name__ == "__main__":
    main()
