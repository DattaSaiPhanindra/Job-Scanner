#!/usr/bin/env python3
"""
quick_scan.py — Fast ATS job board scanner

Polls target companies on Greenhouse, Lever, and Ashby every few minutes
via their public JSON APIs. Detects new postings, sends email alerts,
and writes recent_jobs.json for the live dashboard.

Usage:
    python scripts/quick_scan.py              # normal scan
    python scripts/quick_scan.py --dry-run    # scan without sending email
    python scripts/quick_scan.py --seed       # record all existing jobs as baseline
                                              # (no email, no dashboard, first run does this auto)

Environment variables (set as GitHub Actions secrets):
    SMTP_EMAIL      — Gmail address to send from
    SMTP_PASSWORD   — Gmail App Password (not your real password)
    NOTIFY_EMAIL    — Where to send alerts (defaults to SMTP_EMAIL)
"""

import json
import os
import sys
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

# ─── Paths ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
CONFIG_PATH = ROOT_DIR / "config.json"
DATA_DIR = ROOT_DIR / "data"
SEEN_JOBS_PATH = DATA_DIR / "seen_jobs.json"
RECENT_JOBS_PATH = ROOT_DIR / "recent_jobs.json"

TIMEOUT = 15
MAX_WORKERS = 10

DRY_RUN = "--dry-run" in sys.argv
SEED_MODE = "--seed" in sys.argv


# ═══════════════════════════════════════════════════════════════════════════════
#  ATS FETCHERS — one function per platform
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_greenhouse(slug):
    """Greenhouse public board API → list of normalized job dicts."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/json"})
        if r.status_code != 200:
            return []
        data = r.json()
        jobs = []
        for j in data.get("jobs", []):
            jobs.append({
                "id": f"gh_{j['id']}",
                "title": j.get("title", ""),
                "company_slug": slug,
                "company": slug.replace("-", " ").title(),
                "location": j.get("location", {}).get("name", ""),
                "url": j.get("absolute_url", ""),
                "ats": "Greenhouse",
                "posted_at": j.get("updated_at", ""),
            })
        return jobs
    except Exception as e:
        print(f"    [!] Greenhouse/{slug}: {e}")
        return []


def fetch_lever(slug):
    """Lever public postings API → list of normalized job dicts."""
    url = f"https://api.lever.co/v0/postings/{slug}"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/json"})
        if r.status_code != 200:
            return []
        data = r.json()
        jobs = []
        for j in data:
            created_ms = j.get("createdAt", 0)
            created_iso = ""
            if created_ms:
                created_iso = datetime.fromtimestamp(
                    created_ms / 1000, tz=timezone.utc
                ).isoformat()

            jobs.append({
                "id": f"lv_{j['id']}",
                "title": j.get("text", ""),
                "company_slug": slug,
                "company": slug.replace("-", " ").title(),
                "location": j.get("categories", {}).get("location", ""),
                "url": j.get("hostedUrl", ""),
                "ats": "Lever",
                "posted_at": created_iso,
            })
        return jobs
    except Exception as e:
        print(f"    [!] Lever/{slug}: {e}")
        return []


def fetch_ashby(slug):
    """Ashby public posting API → list of normalized job dicts."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/json"})
        if r.status_code != 200:
            return []
        data = r.json()
        org_name = data.get("organizationName", slug.replace("-", " ").title())
        jobs = []
        for j in data.get("jobs", []):
            jobs.append({
                "id": f"ab_{j.get('id', '')}",
                "title": j.get("title", ""),
                "company_slug": slug,
                "company": org_name,
                "location": j.get("location", ""),
                "url": j.get("jobUrl", f"https://jobs.ashbyhq.com/{slug}"),
                "ats": "Ashby",
                "posted_at": j.get("publishedAt", ""),
            })
        return jobs
    except Exception as e:
        print(f"    [!] Ashby/{slug}: {e}")
        return []


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
}


# ═══════════════════════════════════════════════════════════════════════════════
#  MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

def matches_filters(job, keywords, locations):
    """Return True if job title matches any keyword AND location matches any location."""
    title_lower = job.get("title", "").lower()
    loc_lower = job.get("location", "").lower()

    keyword_ok = not keywords  # empty list = match all
    for kw in keywords:
        if kw.lower() in title_lower:
            keyword_ok = True
            break

    location_ok = not locations  # empty list = match all
    for loc in locations:
        if loc.lower() in loc_lower:
            location_ok = True
            break

    return keyword_ok and location_ok


# ═══════════════════════════════════════════════════════════════════════════════
#  EMAIL NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def send_email(new_jobs, config):
    """Send an HTML email listing newly detected jobs."""
    email_cfg = config.get("email", {})
    if not email_cfg.get("enabled", False):
        return

    smtp_user = os.environ.get("SMTP_EMAIL", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    to_email = os.environ.get("NOTIFY_EMAIL", smtp_user)

    if not smtp_user or not smtp_pass:
        print("    [!] SMTP_EMAIL / SMTP_PASSWORD not set — skipping email")
        return

    if DRY_RUN:
        print(f"    [dry-run] Would email {len(new_jobs)} jobs to {to_email}")
        return

    now_str = datetime.now(timezone.utc).strftime("%b %d, %H:%M UTC")
    subject = f"\U0001f680 {len(new_jobs)} New Job{'s' if len(new_jobs) != 1 else ''} — {now_str}"

    rows = []
    for i, job in enumerate(new_jobs[:50]):
        bg = "#f0f4f8" if i % 2 == 0 else "#ffffff"
        rows.append(
            f'<tr style="background:{bg};">'
            f'<td style="padding:10px 12px;"><a href="{job["url"]}" '
            f'style="color:#2563eb;text-decoration:none;font-weight:600;">{job["title"]}</a></td>'
            f'<td style="padding:10px 12px;">{job["company"]}</td>'
            f'<td style="padding:10px 12px;">{job["location"]}</td>'
            f'<td style="padding:10px 12px;"><code style="background:#e2e8f0;'
            f'padding:2px 6px;border-radius:4px;font-size:12px;">{job["ats"]}</code></td>'
            f'</tr>'
        )

    overflow = ""
    if len(new_jobs) > 50:
        overflow = f'<p style="color:#64748b;">…and {len(new_jobs) - 50} more. Check the live dashboard.</p>'

    html = f"""
    <div style="font-family:-apple-system,system-ui,sans-serif;max-width:700px;margin:0 auto;">
      <h2 style="color:#0f172a;">{len(new_jobs)} new job{'s' if len(new_jobs)!=1 else ''} detected</h2>
      <p style="color:#64748b;margin-bottom:20px;">Scanned at {now_str}. These will appear on your
      live dashboard for {config.get('job_display_hours', 1)} hour.</p>
      <table style="border-collapse:collapse;width:100%;font-size:14px;">
        <thead>
          <tr style="background:#0f172a;color:#fff;">
            <th style="padding:10px 12px;text-align:left;">Title</th>
            <th style="padding:10px 12px;text-align:left;">Company</th>
            <th style="padding:10px 12px;text-align:left;">Location</th>
            <th style="padding:10px 12px;text-align:left;">ATS</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
      {overflow}
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(
            email_cfg.get("smtp_server", "smtp.gmail.com"),
            email_cfg.get("smtp_port", 587),
        ) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
        print(f"    \u2709  Email sent to {to_email}")
    except Exception as e:
        print(f"    [!] Email failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    now = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"  QUICK SCAN — {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}\n")

    # ── Load config ──
    if not CONFIG_PATH.exists():
        print("[!] config.json not found. Run from the repo root.")
        sys.exit(1)

    config = json.loads(CONFIG_PATH.read_text())
    keywords = config.get("keywords", [])
    locations = config.get("locations", [])
    companies = config.get("companies", {})
    display_hours = config.get("job_display_hours", 1)

    # ── Load state ──
    DATA_DIR.mkdir(exist_ok=True)

    seen_ids = set()
    if SEEN_JOBS_PATH.exists():
        try:
            seen_ids = set(json.loads(SEEN_JOBS_PATH.read_text()))
        except json.JSONDecodeError:
            seen_ids = set()

    existing_recent = []
    if RECENT_JOBS_PATH.exists():
        try:
            existing_recent = json.loads(RECENT_JOBS_PATH.read_text())
        except json.JSONDecodeError:
            existing_recent = []

    # ── Build task list ──
    tasks = []
    for ats_name, slugs in companies.items():
        fetcher = FETCHERS.get(ats_name)
        if not fetcher:
            print(f"  [!] Unknown ATS platform: {ats_name}")
            continue
        for slug in slugs:
            tasks.append((ats_name, slug, fetcher))

    print(f"  Scanning {len(tasks)} company boards across {len(companies)} platforms…\n")

    # ── Parallel fetch ──
    all_jobs = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(fn, slug): (ats, slug)
            for ats, slug, fn in tasks
        }
        for future in as_completed(futures):
            ats, slug = futures[future]
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
                if jobs:
                    print(f"    \u2713 {ats}/{slug}: {len(jobs)} jobs")
                else:
                    print(f"    \u2013 {ats}/{slug}: 0 jobs")
            except Exception as e:
                print(f"    \u2717 {ats}/{slug}: {e}")

    print(f"\n  Total fetched:   {len(all_jobs)} jobs")

    # ── Filter by user keywords/locations ──
    matched = [j for j in all_jobs if matches_filters(j, keywords, locations)]
    print(f"  After filtering: {len(matched)} jobs")

    # ── Detect if this is the first run (no previously seen jobs) ──
    is_first_run = len(seen_ids) == 0

    if is_first_run or SEED_MODE:
        # FIRST RUN / SEED MODE:
        # Record all current job IDs so we know what already exists,
        # but do NOT treat them as "new" — they've been posted for
        # days/weeks, we just haven't seen them yet.
        for job in matched:
            seen_ids.add(job["id"])

        label = "SEED MODE" if SEED_MODE else "FIRST RUN"
        print(f"\n  \u{1f331} {label}: Recorded {len(seen_ids)} existing job IDs as baseline.")
        print(f"     No notifications sent. Only genuinely new jobs will")
        print(f"     be detected starting from the NEXT scan.\n")

        # Clear the dashboard — don't show old jobs as new
        RECENT_JOBS_PATH.write_text(json.dumps([]))
        SEEN_JOBS_PATH.write_text(json.dumps(list(seen_ids)))
        print(f"  \U0001f5c2  Tracked IDs:  {len(seen_ids)}")
        print(f"\n  \u2705 Seed complete. Future scans will only detect new postings.\n")
        return

    # ── Normal mode: detect genuinely NEW jobs ──
    now_iso = now.isoformat()
    new_jobs = []
    for job in matched:
        if job["id"] not in seen_ids:
            job["detected_at"] = now_iso
            new_jobs.append(job)
            seen_ids.add(job["id"])

    print(f"  \U0001f195 New this scan:  {len(new_jobs)} jobs")

    # ── Email alert (only for genuinely new postings) ──
    if new_jobs:
        send_email(new_jobs, config)

    # ── Update recent_jobs.json (keep only the display window + buffer) ──
    cutoff = now - timedelta(hours=display_hours + 1)

    recent_by_id = {j["id"]: j for j in existing_recent}
    for job in new_jobs:
        recent_by_id[job["id"]] = job

    fresh = []
    for job in recent_by_id.values():
        detected = job.get("detected_at", "")
        if not detected:
            continue
        try:
            dt = datetime.fromisoformat(detected.replace("Z", "+00:00"))
            if dt > cutoff:
                fresh.append(job)
        except ValueError:
            pass

    fresh.sort(key=lambda j: j.get("detected_at", ""), reverse=True)

    RECENT_JOBS_PATH.write_text(json.dumps(fresh, indent=2))
    print(f"  \U0001f4ca Dashboard:     {len(fresh)} jobs in the live window")

    # ── Prune seen_ids older than 7 days (keep file from growing forever) ──
    # We keep all IDs for 7 days to avoid re-alerting on the same job
    # if it's still listed days later. Simple approach: just cap the set size.
    MAX_SEEN = 500_000
    if len(seen_ids) > MAX_SEEN:
        seen_ids = set(list(seen_ids)[-MAX_SEEN:])

    SEEN_JOBS_PATH.write_text(json.dumps(list(seen_ids)))
    print(f"  \U0001f5c2  Tracked IDs:  {len(seen_ids)}")

    print(f"\n  \u2705 Scan complete.\n")


if __name__ == "__main__":
    main()
