# Daily Progress Tracker

A frictionless daily logging app that turns free-form brain dumps into structured, color-coded progress — across three parallel goals: PhD positions, Netherlands jobs, and China jobs.

**Features:**
- 🧠 **LLM parsing** — paste anything; Claude categorizes it into goal buckets
- 🗓️ **GitHub-style heatmap** — multi-goal days show proportional color gradients
- 📱 **iOS home screen widget** — via the free Scriptable app
- 🔄 **Notion sync** — one-way push to your Notion workspace
- 🚂 **Railway deployment** — accessible from anywhere with HTTPS

---

## Quick Start (Local)

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd daily-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
cp .env.example .env
```

Open `.env` and fill in:

```dotenv
ANTHROPIC_API_KEY=sk-ant-...       # Required for LLM parsing
NOTION_TOKEN=secret_...            # Optional — only needed for Notion sync
DATABASE_PATH=./tracker.db         # Default: local file
TRACKER_PASSWORD=                  # Optional — leave empty for local dev (no auth)
```

### 3. Run the server

```bash
.venv/bin/uvicorn app.main:app --reload --port 8090
```

Open **http://localhost:8090** in your browser.

---

## Configuration (`config.json`)

Non-secret tunable values live in `config.json`. Edit as needed:

```jsonc
{
  "llm_model": "claude-sonnet-4-6",       // Claude model to use
  "notion_sync_enabled": false,            // Set true once DB IDs are filled in
  "notion_phd_db_id": "",                  // Notion database ID for PhD tasks
  "notion_nl_db_id": "",                   // Notion database ID for NL Jobs tasks
  "notion_china_db_id": ""                 // Notion database ID for China Jobs tasks
}
```

### Finding Notion database IDs

1. Open the Notion database in your browser
2. The URL looks like: `https://www.notion.so/workspace/My-DB-**abc123def456...**?v=...`
3. The bold part (32 hex chars, with or without dashes) is the database ID

---

## iPhone Widget (Scriptable)

1. Install **Scriptable** (free) from the App Store
2. Open Scriptable → tap **+** → paste the entire contents of `widget/tracker_widget.js`
3. Name the script **"Daily Tracker"**
4. Edit the `BASE_URL` at the top of the script:
   - **Same WiFi as your Mac:** `http://YOUR_MAC_IP:8090`
     (find your Mac's IP: System Settings → Wi-Fi → Details)
   - **After Railway deploy:** `https://your-app.up.railway.app`
5. Long-press your home screen → **+** → Scriptable → **Medium** widget
6. Long-press the widget → **Edit Widget** → Script: **Daily Tracker**

The widget auto-refreshes every 15 minutes and shows today's task counts, goal summaries, and your current streak.

---

## Railway Deployment

### 1. Create project & connect repo

```bash
npm install -g @railway/cli
railway login
railway init              # creates new project
railway link              # link to existing project
```

Or use the Railway dashboard at [railway.app](https://railway.app) to connect your GitHub repo.

### 2. Add a persistent volume

In the Railway dashboard:
- Go to your service → **Volumes** → **Add Volume**
- Mount path: `/data`

### 3. Set environment variables

In the Railway dashboard → **Variables**:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `NOTION_TOKEN` | `secret_...` (optional) |
| `DATABASE_PATH` | `/data/tracker.db` |
| `TRACKER_PASSWORD` | a strong password |

### 4. Deploy

```bash
git push origin main   # Railway auto-deploys on push
```

### 5. Update widget URL

After deploy, copy the Railway public URL (e.g. `https://daily-tracker-production.up.railway.app`) and update `BASE_URL` in `widget/tracker_widget.js`.

---

## Notion Sync Setup

Once you have Notion DB IDs in `config.json`:

1. Create three Notion databases (or reuse existing ones) with these properties:
   - **Name** (Title)
   - **Status** (Select: `logged`, `in_progress`, `done`)
   - **Category** (Select: `application`, `outreach`, `research`, `networking`, `profile`, `general`)
   - **Log Date** (Date)
   - **Effort (min)** (Number)

2. Share each database with your Notion integration token

3. Set `"notion_sync_enabled": true` in `config.json`

4. New log entries will automatically sync tasks to Notion in the background

**Check sync status:** `GET /api/sync/status`
**Retry failed syncs:** `POST /api/sync/retry`

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Main page (heatmap + log form) |
| `GET` | `/day/{date}` | HTMX partial: day detail panel |
| `GET` | `/calendar?year=&month=` | HTMX partial: heatmap grid |
| `POST` | `/api/log` | Submit brain dump → LLM parse → store |
| `GET` | `/api/widget` | iOS widget JSON payload |
| `GET` | `/api/stats` | Streak + totals JSON |
| `GET` | `/api/heatmap?year=&month=` | Month cell data JSON |
| `GET` | `/api/sync/status` | Notion sync queue status |
| `POST` | `/api/sync/retry` | Retry all failed Notion syncs |
| `GET` | `/api/export` | Download `tracker.db` backup |

### POST /api/log

**Form fields** (or JSON body):

```
raw_text    string   Your brain dump text
entry_date  string   ISO date, e.g. "2026-03-03" (optional, defaults to today)
```

**Example:**

```bash
curl -X POST http://localhost:8090/api/log \
  -F "raw_text=Emailed Prof. van den Heuvel at TU Delft. Applied to ASML UX role. Reviewed Alibaba posting." \
  -F "entry_date=2026-03-03"
```

---

## Integrating with phd-tracker

After a phd-tracker scrape run, auto-create a log entry:

```python
import requests

requests.post("http://localhost:8090/api/log", data={
    "raw_text": f"PhD scraper run: found {n} new positions. Applied to {applied}.",
    "entry_date": today,
})
```

---

## Project Structure

```
daily-tracker/
├── app/
│   ├── main.py              # FastAPI app, Basic Auth middleware
│   ├── config.py            # Env secrets + config.json loader
│   ├── database.py          # SQLite connection, migrations, helpers
│   ├── routes/
│   │   ├── pages.py         # HTML pages (GET /, /day/{date}, /calendar)
│   │   ├── api_log.py       # POST /api/log
│   │   ├── api_heatmap.py   # GET /api/heatmap, /api/stats
│   │   ├── api_widget.py    # GET /api/widget
│   │   └── api_sync.py      # /api/sync/*, /api/export
│   ├── services/
│   │   ├── llm.py           # Claude API: parse_brain_dump()
│   │   ├── heatmap.py       # Gradient CSS, month cell aggregation
│   │   └── notion_sync.py   # One-way Notion sync
│   └── templates/
│       ├── base.html        # Design system + CSS
│       ├── index.html       # Main page
│       └── partials/        # HTMX fragments
├── migrations/
│   └── 001_initial.sql      # SQLite schema
├── widget/
│   └── tracker_widget.js    # iOS Scriptable widget
├── config.json              # Tunable values (not secrets)
├── .env.example             # Secret template
├── requirements.txt
└── railway.toml             # Railway deployment config
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | — | Anthropic API key for Claude |
| `NOTION_TOKEN` | No | — | Notion integration token |
| `DATABASE_PATH` | No | `./tracker.db` | Path to SQLite database file |
| `TRACKER_PASSWORD` | No | — | HTTP Basic Auth password (no username required) |
