# Daily Progress Tracker

A frictionless daily logging app that turns free-form brain dumps into structured, color-coded progress across any goals **you** define.

**Features:**
- 🎯 **User-defined goals** — add, rename, recolor, or remove tracks from `/settings`
- 🧠 **LLM parsing** — paste anything; Claude categorizes it into your goal buckets
- 🗓️ **GitHub-style heatmap** — multi-goal days show proportional color gradients
- 📱 **iOS home screen widget** — via the free Scriptable app
- 🔄 **Notion sync** — one-way push to per-goal Notion databases
- 🚂 **Railway deployment** — accessible from anywhere with HTTPS

The repo ships with three placeholder goals (Goal A / B / C). Edit them in `/settings` to match your life.

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

Open **http://localhost:8090** in your browser, then visit **http://localhost:8090/settings** to define your goals.

---

## Defining Your Goals

Goals are managed in the app at **`/settings`**. Each goal has:

| Field | Notes |
|---|---|
| **Key** | Lowercase identifier (`phd`, `side_project`). Stable — used in the DB; don't change after data is logged. |
| **Label** | Display name shown in the UI and the LLM prompt. |
| **Color** | Hex color for the heatmap and goal cards. |
| **Description** | Optional context passed to the LLM so it can route brain dumps more accurately. |
| **Sort order** | Smaller numbers appear first. |
| **Notion DB ID** | Optional. 32-char Notion database ID for per-goal sync. |

The LLM sees your goals' labels + descriptions and classifies each item in a brain dump into one of them. Items unrelated to any goal land in `general_notes`.

---

## Configuration (`config.json`)

Non-secret app-level settings live here. Goals live in the DB now, not in this file.

```jsonc
{
  "llm_model": "claude-sonnet-4-6",       // Claude model to use
  "notion_sync_enabled": false             // Set true once Notion DB IDs are set per goal
}
```

---

## iPhone Widget (Scriptable)

The widget reads goal labels and colors from `/api/widget`, so it automatically reflects whatever you've configured in `/settings` — no code edits needed when you add or rename a goal.

1. Install **Scriptable** (free) from the App Store
2. Open Scriptable → tap **+** → paste the entire contents of `widget/tracker_widget.js`
3. Name the script **"Daily Tracker"**
4. Edit the `BASE_URL` at the top of the script:
   - **Same WiFi as your Mac:** `http://YOUR_MAC_IP:8090`
   - **After Railway deploy:** `https://your-app.up.railway.app`
5. Long-press your home screen → **+** → Scriptable → **Medium** widget
6. Long-press the widget → **Edit Widget** → Script: **Daily Tracker**

The widget auto-refreshes every 15 minutes.

> The other files in `widget/` are experimental prototypes (a menubar app, JSX/CoffeeScript variants) and aren't required.

---

## Railway Deployment

### 1. Create project & connect repo

```bash
npm install -g @railway/cli
railway login
railway init
railway link
```

Or use the Railway dashboard at [railway.app](https://railway.app).

### 2. Add a persistent volume

In the Railway dashboard:
- Go to your service → **Volumes** → **Add Volume**
- Mount path: `/data`

### 3. Set environment variables

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `NOTION_TOKEN` | `secret_...` (optional) |
| `DATABASE_PATH` | `/data/tracker.db` |
| `TRACKER_PASSWORD` | a strong password |

### 4. Deploy

```bash
git push origin main
```

### 5. Update widget URL

After deploy, copy the Railway public URL and update `BASE_URL` in `widget/tracker_widget.js`.

---

## Notion Sync Setup

1. For each goal you want to sync, create a Notion database with these properties:
   - **Name** (Title)
   - **Status** (Select: `logged`, `in_progress`, `done`)
   - **Category** (Select: `application`, `outreach`, `research`, `networking`, `profile`, `learning`, `admin`, `general`)
   - **Log Date** (Date)
   - **Effort (min)** (Number)
2. Share each database with your Notion integration token
3. In `/settings`, paste the Notion DB ID into the goal that should sync there
4. Set `"notion_sync_enabled": true` in `config.json`

**Check sync status:** `GET /api/sync/status`
**Retry failed syncs:** `POST /api/sync/retry`

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET`   | `/`                              | Main page (heatmap + log form) |
| `GET`   | `/settings`                      | Manage goals |
| `GET`   | `/day/{date}`                    | HTMX partial: day detail panel |
| `GET`   | `/calendar?year=&month=`         | HTMX partial: heatmap grid |
| `POST`  | `/api/log`                       | Submit brain dump → LLM parse → store (HTML response) |
| `POST`  | `/api/log/json`                  | Same as above but JSON response |
| `GET`   | `/api/goals`                     | List goals |
| `POST`  | `/api/goals`                     | Create goal (JSON body) |
| `PATCH` | `/api/goals/{key}`               | Update goal |
| `DELETE`| `/api/goals/{key}`               | Delete goal (fails if tasks reference it) |
| `GET`   | `/api/widget`                    | iOS widget JSON payload (includes goal metadata) |
| `GET`   | `/api/stats`                     | Streak + totals JSON |
| `GET`   | `/api/heatmap?year=&month=`      | Month cell data JSON |
| `GET`   | `/api/sync/status`               | Notion sync queue status |
| `POST`  | `/api/sync/retry`                | Retry all failed Notion syncs |
| `GET`   | `/api/export`                    | Download `tracker.db` backup |

### POST /api/log

**Form fields** (or JSON body):

```
raw_text    string   Your brain dump text
entry_date  string   ISO date, e.g. "2026-03-03" (optional, defaults to today)
```

**Example:**

```bash
curl -X POST http://localhost:8090/api/log \
  -F "raw_text=Emailed advisor about thesis topic. Applied to UX role at Acme. Read two papers." \
  -F "entry_date=2026-03-03"
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
│   │   ├── pages.py         # HTML pages (/, /day/{date}, /calendar, /settings)
│   │   ├── api_log.py       # POST /api/log
│   │   ├── api_goals.py     # /api/goals CRUD
│   │   ├── api_heatmap.py   # GET /api/heatmap, /api/stats
│   │   ├── api_widget.py    # GET /api/widget
│   │   └── api_sync.py      # /api/sync/*, /api/export
│   ├── services/
│   │   ├── goals.py         # Goal repository
│   │   ├── llm.py           # Claude API — prompt built from configured goals
│   │   ├── heatmap.py       # Gradient CSS, month cell aggregation
│   │   └── notion_sync.py   # One-way Notion sync
│   └── templates/
│       ├── base.html        # Design system + CSS
│       ├── index.html       # Main page
│       ├── settings.html    # Goal management
│       └── partials/        # HTMX fragments
├── migrations/
│   ├── 001_initial.sql      # SQLite schema
│   └── 002_goals.sql        # Goals table + relax goal CHECK constraints
├── widget/
│   └── tracker_widget.js    # iOS Scriptable widget
├── config.json              # App-level non-secrets
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
