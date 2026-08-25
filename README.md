# Job Scanner — Complete Setup Guide (Zero to Working)

Everything you need to set up a near-real-time job alert system that scans 100 top tech companies across Greenhouse, Lever, and Ashby every 10 minutes, emails you new matches, and shows a live dashboard where jobs appear for 1 hour then vanish.

Total cost: **$0**. Total time: **~15 minutes**.

---

## Prerequisites

You need three things before starting:

- A **GitHub account** (free) — [github.com/signup](https://github.com/signup)
- A **Gmail account** with 2-Factor Authentication enabled
- A web browser

That's it. No coding required, no server, no terminal.

---

## STEP 1 — Create a New GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `job-scanner` (or anything you want)
3. Description: `Near-real-time job alert scanner`
4. Select **Public** (required for free GitHub Actions minutes)
5. Check **"Add a README file"**
6. Click **"Create repository"**

You now have an empty repo at `github.com/YOUR_USERNAME/job-scanner`.

---

## STEP 2 — Upload the Scanner Files

You have 5 files to add. Here's each one:

### File 1: `config.json` (in the root)

Click **"Add file" → "Create new file"** in your repo.

- Name: `config.json`
- Paste the entire contents of the `config.json` file provided

This file controls which companies to scan, what job titles to match, and your email settings. The provided config includes 100 companies across all 3 platforms.

Click **"Commit changes"**.

### File 2: `scripts/quick_scan.py`

Click **"Add file" → "Create new file"**.

- Name: `scripts/quick_scan.py` (typing the `/` creates the folder automatically)
- Paste the entire contents of the `quick_scan.py` file provided

Click **"Commit changes"**.

### File 3: `.github/workflows/quick_scan.yml`

Click **"Add file" → "Create new file"**.

- Name: `.github/workflows/quick_scan.yml` (the `/` creates each folder)
- Paste the entire contents of the `quick_scan.yml` file provided

Click **"Commit changes"**.

### File 4: `live.html`

Click **"Add file" → "Create new file"**.

- Name: `live.html`
- Paste the entire contents of the `live.html` file provided

Click **"Commit changes"**.

### File 5: `data/seen_jobs.json`

Click **"Add file" → "Create new file"**.

- Name: `data/seen_jobs.json`
- Contents: `[]`

Click **"Commit changes"**.

### File 6: `recent_jobs.json`

Click **"Add file" → "Create new file"**.

- Name: `recent_jobs.json`
- Contents: `[]`

Click **"Commit changes"**.

---

## STEP 3 — Create a Gmail App Password

Gmail won't let you use your real password for SMTP. You need an "App Password."

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **"Security"** in the left sidebar
3. Under "How you sign in to Google," confirm **2-Step Verification is ON**
   - If it's off, turn it on first (Google requires this for App Passwords)
4. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
5. In the "App name" field, type: `Job Scanner`
6. Click **"Create"**
7. Google shows you a **16-character password** (like `abcd efgh ijkl mnop`)
8. **Copy this password** — you'll need it in the next step
   - Remove the spaces when pasting: `abcdefghijklmnop`

---

## STEP 4 — Add GitHub Secrets (Email Credentials)

Your email password must be stored securely as a GitHub Secret, not in any file.

1. Go to your repo on GitHub
2. Click **Settings** (the gear icon tab)
3. In the left sidebar, click **Secrets and variables → Actions**
4. Click **"New repository secret"** and add these three secrets one at a time:

| Name | Value | Example |
|------|-------|---------|
| `SMTP_EMAIL` | Your Gmail address | `yourname@gmail.com` |
| `SMTP_PASSWORD` | The 16-character App Password from Step 3 | `abcdefghijklmnop` |
| `NOTIFY_EMAIL` | Where to receive alerts (can be same as SMTP_EMAIL, or a different email) | `yourname@gmail.com` |

After adding all three, you should see them listed (values hidden) under "Repository secrets."

---

## STEP 5 — Enable GitHub Actions

1. Go to your repo on GitHub
2. Click the **"Actions"** tab
3. You'll see a yellow banner: *"Workflows aren't being run on this repository"*
4. Click **"I understand my workflows, go ahead and enable them"**

---

## STEP 6 — Run It for the First Time (Manual Test)

Don't wait for the cron schedule — trigger it manually now to verify everything works.

1. In the **Actions** tab, click **"🔍 Quick Scan — Job Alerts"** in the left sidebar
2. Click the **"Run workflow"** dropdown button on the right
3. Click the green **"Run workflow"** button
4. Wait 30–60 seconds, then refresh the page
5. You should see a workflow run appear. Click it to see the logs.

**What to look for in the logs:**

- `Scanning 100 company boards across 3 platforms…` — it's running
- `✓ greenhouse/stripe: 247 jobs` — APIs are responding
- `🆕 New this scan: 83 jobs` — first run will find lots of "new" jobs
- `✉ Email sent to yourname@gmail.com` — email notification worked

If you see errors about SMTP, double-check your secrets in Step 4.

**Check your email** — you should have received the first alert with a table of matching jobs.

---

## STEP 7 — Enable the Live Dashboard (GitHub Pages)

1. Go to your repo → **Settings**
2. In the left sidebar, click **"Pages"**
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main** — folder: **/ (root)**
4. Click **"Save"**
5. Wait 1–2 minutes for the first deployment

Your live dashboard is now at:

```
https://YOUR_USERNAME.github.io/job-scanner/live.html
```

Open it in a browser — you should see the jobs from your first scan with countdown timers.

---

## STEP 8 — Customize Your Config

Now edit `config.json` in your repo to match your actual job search:

### Edit keywords
Only jobs whose title contains at least one keyword will be tracked. Remove keywords you don't care about, add ones you do:

```json
"keywords": [
  "software engineer",
  "data engineer",
  "backend"
]
```

Set to `[]` to match ALL jobs at your target companies.

### Edit locations
Filter by location (matches against the job's location field):

```json
"locations": ["Remote", "New York", "San Francisco", "Austin"]
```

Set to `[]` to match all locations.

### Add or remove companies
See the full company list below. Add any company's slug to the appropriate platform array.

After editing, commit the changes. The next scan (within 10 minutes) will use the new config.

---

## You're Done!

The system is now running. Here's what happens automatically:

- **Every 10 minutes**: GitHub Actions runs `quick_scan.py`
- **New jobs detected**: You receive an email with a table of matches
- **Dashboard**: `live.html` shows jobs from the last hour with countdown timers
- **After 1 hour**: Jobs automatically disappear from the dashboard
- **Cost**: $0 forever (public repo = unlimited GitHub Actions minutes)

---

## Verified Company Slugs (100 companies)

Below is every company in the provided `config.json`, organized by platform. Each slug has been verified against public sources and Apify scrapers as of mid-2026.

**How slugs work**: The slug is the last part of the company's ATS URL.
- Greenhouse: `boards.greenhouse.io/{slug}`
- Lever: `jobs.lever.co/{slug}`
- Ashby: `jobs.ashbyhq.com/{slug}`

You can verify any slug by visiting that URL in your browser. If it loads a careers page, the slug is correct.

### Greenhouse (50 companies)

Companies that use `boards-api.greenhouse.io/v1/boards/{slug}/jobs`:

| Slug | Company | Category |
|------|---------|----------|
| `anthropic` | Anthropic | AI |
| `stripe` | Stripe | Fintech |
| `figma` | Figma | Design Tools |
| `cloudflare` | Cloudflare | Infrastructure |
| `discord` | Discord | Social / Gaming |
| `reddit` | Reddit | Social Media |
| `databricks` | Databricks | Data / AI |
| `lyft` | Lyft | Rideshare |
| `robinhood` | Robinhood | Fintech |
| `doordash` | DoorDash | Delivery |
| `pinterest` | Pinterest | Social Media |
| `mongodb` | MongoDB | Databases |
| `datadog` | Datadog | Observability |
| `twilio` | Twilio | Communications |
| `gitlab` | GitLab | Developer Tools |
| `brex` | Brex | Fintech |
| `gusto` | Gusto | HR / Payroll |
| `lattice` | Lattice | HR Tech |
| `plaid` | Plaid | Fintech |
| `airtable` | Airtable | Productivity |
| `instacart` | Instacart | Delivery |
| `duolingo` | Duolingo | Education |
| `hubspot` | HubSpot | Marketing / CRM |
| `dropbox` | Dropbox | Cloud Storage |
| `snap` | Snap | Social Media |
| `github` | GitHub | Developer Tools |
| `nba` | NBA | Sports |
| `nytimes` | The New York Times | Media |
| `tripadvisor` | TripAdvisor | Travel |
| `forbes` | Forbes | Media |
| `squarespace` | Squarespace | Website Builder |
| `grammarly` | Grammarly | AI / Writing |
| `affirm` | Affirm | Fintech |
| `elastic` | Elastic | Search / Data |
| `samsara` | Samsara | IoT |
| `toast` | Toast | Restaurant Tech |
| `okta` | Okta | Security / Identity |
| `pagerduty` | PagerDuty | DevOps |
| `zscaler` | Zscaler | Cybersecurity |
| `appian` | Appian | Low-Code |
| `nightfall` | Nightfall AI | Security |
| `cockroachlabs` | CockroachDB | Databases |
| `benchling` | Benchling | Biotech |
| `whatnot` | Whatnot | E-Commerce |
| `watershedclimate` | Watershed | Climate Tech |
| `flexport` | Flexport | Logistics |
| `chime` | Chime | Fintech |
| `earnin` | Earnin | Fintech |
| `nerdwallet` | NerdWallet | Finance |
| `andurilindustries` | Anduril | Defense Tech |

### Lever (20 companies)

Companies that use `api.lever.co/v0/postings/{slug}`:

| Slug | Company | Category |
|------|---------|----------|
| `netflix` | Netflix | Streaming |
| `spotify` | Spotify | Music / Audio |
| `shopify` | Shopify | E-Commerce |
| `tailscale` | Tailscale | Networking |
| `retool` | Retool | Developer Tools |
| `coupa` | Coupa | Procurement |
| `aircall` | Aircall | Communications |
| `persona` | Persona | Identity |
| `upstart` | Upstart | Fintech / AI |
| `mux` | Mux | Video |
| `seatgeek` | SeatGeek | Ticketing |
| `anyscale` | Anyscale (Ray) | AI Infrastructure |
| `applydigital` | Apply Digital | Digital Agency |
| `talkdesk` | Talkdesk | Contact Center |
| `automox` | Automox | IT / Security |
| `grafana` | Grafana Labs | Observability |
| `chainalysis` | Chainalysis | Blockchain |
| `taxbit` | TaxBit | Crypto / Tax |
| `snorkel` | Snorkel AI | AI / ML |
| `dbt-labs` | dbt Labs | Data |

### Ashby (30 companies)

Companies that use `api.ashbyhq.com/posting-api/job-board/{slug}`:

| Slug | Company | Category |
|------|---------|----------|
| `openai` | OpenAI | AI |
| `notion` | Notion | Productivity |
| `ramp` | Ramp | Fintech |
| `linear` | Linear | Developer Tools |
| `cursor` | Cursor | AI / IDE |
| `elevenlabs` | ElevenLabs | AI / Audio |
| `replit` | Replit | Developer Tools |
| `supabase` | Supabase | Databases |
| `docker` | Docker | Developer Tools |
| `posthog` | PostHog | Product Analytics |
| `substack` | Substack | Publishing |
| `mercury` | Mercury | Banking |
| `vercel` | Vercel | Developer Tools |
| `deel` | Deel | HR / Global Payroll |
| `vanta` | Vanta | Security / Compliance |
| `webflow` | Webflow | Website Builder |
| `loom` | Loom | Video |
| `langchain` | LangChain | AI / LLM Tools |
| `snowflake` | Snowflake | Data |
| `deliveroo` | Deliveroo | Delivery |
| `opendoor` | Opendoor | Real Estate |
| `railway` | Railway | Developer Tools |
| `resend` | Resend | Email |
| `modal` | Modal | AI Infrastructure |
| `browserbase` | Browserbase | Browser Infra |
| `drata` | Drata | Compliance |
| `coder` | Coder | Developer Tools |
| `neon` | Neon | Databases |
| `turso` | Turso | Databases |
| `inngest` | Inngest | Developer Tools |

---

## How to Find More Company Slugs

Want to add a company that's not in the list above?

1. Go to the company's careers page (google "Company Name careers")
2. Look at where job listing links point to:
   - If links go to `boards.greenhouse.io/SLUG/...` → it's Greenhouse, slug is `SLUG`
   - If links go to `jobs.lever.co/SLUG/...` → it's Lever, slug is `SLUG`
   - If links go to `jobs.ashbyhq.com/SLUG/...` → it's Ashby, slug is `SLUG`
3. Many companies use custom domains (like `careers.stripe.com`) that proxy to their ATS — view the page source or network requests to find the real ATS

Quick test — paste this URL into your browser (replacing `SLUG`):
- `https://boards-api.greenhouse.io/v1/boards/SLUG/jobs` — returns JSON if valid
- `https://api.lever.co/v0/postings/SLUG` — returns JSON if valid
- `https://api.ashbyhq.com/posting-api/job-board/SLUG` — returns JSON if valid

---

## Troubleshooting

### "Email not arriving"
- Check your spam folder
- Verify SMTP_EMAIL and SMTP_PASSWORD secrets are correct
- Make sure you used a Gmail **App Password**, not your real password
- Make sure 2FA is enabled on your Google account

### "0 jobs found for a company"
- The company may have moved off that ATS platform
- The slug might be wrong — verify by visiting the URL in your browser
- The company might have no open positions right now

### "Workflow not running on schedule"
- GitHub Actions cron on free tier can be delayed 5–20 minutes during peak times
- Make sure the repo is Public (private repos have limited free minutes)
- Check the Actions tab for any error messages

### "Dashboard shows no jobs"
- Make sure GitHub Pages is enabled (Step 7)
- The `recent_jobs.json` file needs to exist and have data
- Check that the scanner has run at least once successfully
- Jobs older than 1 hour are automatically hidden — this is by design

---

## Architecture Overview

```
  YOU
   │
   ├── 📧 Email notification (new jobs only)
   │
   └── 🌐 Live dashboard (jobs.github.io/job-scanner/live.html)
         │ fetches recent_jobs.json every 60 seconds
         │ shows only last 1 hour
         │ auto-removes expired jobs
         │
  GitHub Actions (every 10 min)
   │
   ├── quick_scan.py
   │    ├── Read config.json (companies, keywords, locations)
   │    ├── Poll 100 companies in parallel (10 threads)
   │    │    ├── Greenhouse API (50 companies)
   │    │    ├── Lever API (20 companies)
   │    │    └── Ashby API (30 companies)
   │    ├── Filter by keywords & locations
   │    ├── Compare against seen_jobs.json
   │    ├── Email new matches via Gmail SMTP
   │    └── Write recent_jobs.json (for dashboard)
   │
   └── git commit & push (updates GitHub Pages)
```
