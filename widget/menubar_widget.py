#!/usr/bin/env python3
"""
Daily Tracker — macOS Menu Bar Widget
Run:    pip install rumps
        python3 widget/menubar_widget.py
"""
import json
import os
import subprocess
import threading
import urllib.request
import datetime

import rumps

API_BASE    = "http://localhost:8090"

# Scriptable iCloud Documents folder — widget reads tracker_data.json from here
SCRIPTABLE_DIR = os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~dk~simonbs~Scriptable/Documents"
)


def _save_for_scriptable(data):
    """Write fresh widget data to Scriptable's Documents folder."""
    if not os.path.isdir(SCRIPTABLE_DIR):
        return
    try:
        path = os.path.join(SCRIPTABLE_DIR, "tracker_data.json")
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass
GOAL_KEYS   = ["phd", "nl_jobs", "china_jobs"]
GOAL_ICONS  = {"phd": "🔵", "nl_jobs": "🟠", "china_jobs": "🔴"}
GOAL_LABELS = {"phd": "PhD", "nl_jobs": "NL Jobs", "china_jobs": "China"}

# Pages: order = log → pbar → heatmap → loop
PAGES       = ["log", "pbar", "heatmap"]
PAGE_LABELS = {"log": "Log Today", "pbar": "Progress Bar", "heatmap": "Heatmap"}
BAR_WIDTH   = 16


# ── Network ───────────────────────────────────────────────────────────────────

def fetch_data():
    try:
        with urllib.request.urlopen(f"{API_BASE}/api/widget", timeout=5) as r:
            data = json.loads(r.read())
        _save_for_scriptable(data)   # keep Scriptable widget in sync
        return data
    except Exception:
        return None


def post_log(raw_text):
    data = json.dumps({"raw_text": raw_text}).encode()
    req = urllib.request.Request(
        f"{API_BASE}/api/log",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


# ── macOS helpers ─────────────────────────────────────────────────────────────

def notify(message, title="Daily Tracker"):
    subprocess.run(
        ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
        capture_output=True,
    )


def ask_text(prompt, title="Daily Tracker"):
    script = f"""
tell application "System Events" to activate
set r to display dialog "{prompt}" default answer "" with title "{title}" ¬
    buttons {{"Cancel", "Log"}} default button "Log"
return text returned of r
"""
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


# ── App ───────────────────────────────────────────────────────────────────────

class DailyTrackerApp(rumps.App):
    def __init__(self):
        super().__init__("●", quit_button=None)
        self._page = 0        # index into PAGES
        self._data = None
        self._lock = threading.Lock()
        self._update()

    # ── Data refresh ──────────────────────────────────────────────────────────

    def _update(self):
        data = fetch_data()
        with self._lock:
            self._data = data
            self._rebuild(data)

    @rumps.timer(60)
    def _auto_refresh(self, _):
        threading.Thread(target=self._update, daemon=True).start()

    # ── Page header ───────────────────────────────────────────────────────────

    def _page_header(self):
        """Dot indicator:  ● ◦ ◦  Log Today"""
        dots = "  ".join("●" if i == self._page else "◦" for i in range(len(PAGES)))
        label = PAGE_LABELS[PAGES[self._page]]
        return rumps.MenuItem(f"{dots}   {label}", callback=None)

    def _next_button(self):
        """▶  Next: Progress Bar  (cycles on click)"""
        next_page  = (self._page + 1) % len(PAGES)
        next_label = PAGE_LABELS[PAGES[next_page]]
        return rumps.MenuItem(f"▶   Next: {next_label}", callback=self._go_next)

    def _go_next(self, _):
        self._page = (self._page + 1) % len(PAGES)
        with self._lock:
            self._rebuild(self._data)

    # ── Page builders ─────────────────────────────────────────────────────────

    def _page_log(self, data):
        """Page 1 — today's summary + log prompt."""
        today  = data.get("today", {})
        goals  = today.get("goals", {})
        streak = data.get("streak", {})
        week   = data.get("week_totals", {})
        total  = today.get("total_tasks", 0)

        today_str   = datetime.date.today().strftime("%a %-d %b")
        streak_days = streak.get("current_days", 0)
        streak_txt  = f"   🔥 {streak_days}d" if streak_days else ""

        items = [rumps.MenuItem(f"{today_str}{streak_txt}", callback=None), None]

        for key in GOAL_KEYS:
            count  = goals.get(key, {}).get("tasks", 0)
            wk     = week.get(key, 0)
            c_txt  = "–" if count == 0 else str(count)
            wk_txt = f"   {wk} this wk" if wk else ""
            items.append(rumps.MenuItem(
                f"{GOAL_ICONS[key]} {GOAL_LABELS[key]:<10}{c_txt}{wk_txt}",
                callback=None,
            ))

        items.append(None)
        items.append(rumps.MenuItem(
            f"{total} tasks today" if total else "Nothing logged yet",
            callback=None,
        ))
        return items

    def _page_pbar(self, data):
        """Page 2 — weekly progress bars."""
        week  = data.get("week_totals", {})
        total = sum(week.get(k, 0) for k in GOAL_KEYS)

        items = [rumps.MenuItem("── This Week ──────────────────", callback=None)]
        for key in GOAL_KEYS:
            count  = week.get(key, 0)
            pct    = count / total if total else 0
            filled = round(pct * BAR_WIDTH)
            bar    = "█" * filled + "░" * (BAR_WIDTH - filled)
            items.append(rumps.MenuItem(
                f"{GOAL_ICONS[key]} {GOAL_LABELS[key]:<10} {bar} {round(pct*100)}%",
                callback=None,
            ))
        if not total:
            items.append(rumps.MenuItem("No tasks this week", callback=None))
        return items

    def _page_heatmap(self, data):
        """Page 3 — weekly bar chart (10 weeks, oldest → newest)."""
        weeks = data.get("heatmap_weeks", [])
        if not weeks:
            return [rumps.MenuItem("No data yet", callback=None)]

        # Sum tasks per week (exclude future days)
        week_totals = [
            sum(
                cell.get("phd", 0) + cell.get("nl_jobs", 0) + cell.get("china_jobs", 0)
                for cell in week if not cell.get("future")
            )
            for week in weeks
        ]

        max_t  = max(week_totals) if any(t > 0 for t in week_totals) else 1
        BAR_W  = 12
        n      = len(weeks)

        # Calculate week start dates (grid always starts on a Monday)
        today      = datetime.date.today()
        grid_start = today - datetime.timedelta(days=today.weekday() + 7 * (n - 1))

        items = [rumps.MenuItem("── Last 10 Weeks ──────────────", callback=None)]
        for i, total in enumerate(week_totals):
            week_start = grid_start + datetime.timedelta(weeks=i)

            if i == n - 1:
                label = "This week"
            elif i == n - 2:
                label = "Last week"
            else:
                label = week_start.strftime("%-d %b")   # e.g. "5 Jan"

            filled = round(total / max_t * BAR_W) if max_t else 0
            bar    = "█" * filled + "░" * (BAR_W - filled)
            suffix = f"  {total}" if total else ""
            items.append(rumps.MenuItem(f"{label:<10}  {bar}{suffix}", callback=None))

        return items

    # ── Menu rebuild ──────────────────────────────────────────────────────────

    def _rebuild(self, data):
        # Clear existing items to prevent duplications on re-build
        for key in list(self.menu.keys()):
            del self.menu[key]

        if not data:
            self.title = "⚠️"
            self.menu = [
                rumps.MenuItem("Tracker offline", callback=None), None,
                rumps.MenuItem("🔄  Refresh", callback=self._manual_refresh),
                rumps.MenuItem("Quit", callback=rumps.quit_application),
            ]
            return

        total = data.get("today", {}).get("total_tasks", 0)
        self.title = str(total) if total else "●"

        page_name = PAGES[self._page]
        if page_name == "log":
            content = self._page_log(data)
        elif page_name == "pbar":
            content = self._page_pbar(data)
        else:
            content = self._page_heatmap(data)

        self.menu = (
            [self._page_header(), None]
            + content
            + [
                None,
                self._next_button(),
                None,
                rumps.MenuItem("📝  Log Today…",   callback=self._log_today),
                rumps.MenuItem("🌐  Open Tracker", callback=self._open_browser),
                rumps.MenuItem("🔄  Refresh",      callback=self._manual_refresh),
                None,
                rumps.MenuItem("Quit", callback=rumps.quit_application),
            ]
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _log_today(self, _):
        text = ask_text("What did you work on today?\n(free-form, any language)")
        if not text:
            return

        def _do():
            try:
                result  = post_log(text)
                by_goal = result.get("tasks_by_goal", {})
                summary = ", ".join(
                    f"{GOAL_LABELS[k]}: {v}" for k, v in by_goal.items() if v
                ) or "0 tasks"
                notify(f"Logged!  {summary}")
                self._update()
            except Exception as e:
                notify(f"Error: {e}")

        threading.Thread(target=_do, daemon=True).start()

    def _open_browser(self, _):
        subprocess.Popen(["open", API_BASE])

    def _manual_refresh(self, _):
        threading.Thread(target=self._update, daemon=True).start()


if __name__ == "__main__":
    DailyTrackerApp().run()
