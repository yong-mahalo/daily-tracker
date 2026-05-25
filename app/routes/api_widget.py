import datetime

from fastapi import APIRouter

from app import database as db
from app.services import goals as goal_repo

router = APIRouter()


@router.get("/widget")
def get_widget():
    today = str(datetime.date.today())
    today_date = datetime.date.today()

    goals = goal_repo.list_goals()
    goal_keys = [g["key"] for g in goals]

    summaries = db.fetchall(
        "SELECT goal, summary_text, task_count FROM daily_summaries WHERE summary_date = ?",
        (today,),
    )
    by_goal = {s["goal"]: s for s in summaries}

    today_by_goal = {}
    for key in goal_keys:
        s = by_goal.get(key)
        today_by_goal[key] = {
            "tasks": s["task_count"] if s else 0,
            "summary": s["summary_text"] if s else None,
        }
    total_tasks = sum(g["tasks"] for g in today_by_goal.values())

    # Streak
    rows = db.fetchall("SELECT DISTINCT entry_date FROM log_entries ORDER BY entry_date DESC")
    dates = [datetime.date.fromisoformat(r["entry_date"]) for r in rows]
    current_streak = 0
    check = today_date
    for d in dates:
        if d == check:
            current_streak += 1
            check -= datetime.timedelta(days=1)
        elif d == today_date - datetime.timedelta(days=1) and current_streak == 0:
            current_streak += 1
            check = d - datetime.timedelta(days=1)
        else:
            break

    longest, run, prev = 0, 0, None
    for d in reversed(dates):
        if prev is None or (d - prev).days == 1:
            run += 1
        else:
            longest = max(longest, run)
            run = 1
        prev = d
    longest = max(longest, run)

    # Per-day counts (last 7 days + 10-week heatmap) — build dynamically per goal
    week_ago = str(today_date - datetime.timedelta(days=6))
    grid_start = today_date - datetime.timedelta(days=today_date.weekday() + 7 * 9)

    week_rows = db.fetchall(
        "SELECT t.goal, COUNT(*) as count FROM tasks t "
        "JOIN log_entries l ON t.log_entry_id = l.id "
        "WHERE l.entry_date >= ? GROUP BY t.goal",
        (week_ago,),
    )
    week_totals = {key: 0 for key in goal_keys}
    for r in week_rows:
        if r["goal"] in week_totals:
            week_totals[r["goal"]] = r["count"]

    # Per-day-per-goal counts since grid_start (covers both sparkline and 10w heatmap)
    counts_rows = db.fetchall(
        "SELECT l.entry_date, t.goal, COUNT(*) AS count "
        "FROM log_entries l LEFT JOIN tasks t ON t.log_entry_id = l.id "
        "WHERE l.entry_date >= ? "
        "GROUP BY l.entry_date, t.goal",
        (str(grid_start),),
    )
    counts_by_date: dict[str, dict[str, int]] = {}
    for r in counts_rows:
        d = r["entry_date"]
        if d not in counts_by_date:
            counts_by_date[d] = {key: 0 for key in goal_keys}
        if r["goal"] and r["goal"] in counts_by_date[d]:
            counts_by_date[d][r["goal"]] = r["count"]

    def day_counts(day: datetime.date) -> dict:
        return counts_by_date.get(str(day), {key: 0 for key in goal_keys})

    last_7_days = []
    for offset in range(6, -1, -1):
        day = today_date - datetime.timedelta(days=offset)
        last_7_days.append({"date": str(day), "counts": day_counts(day)})

    heatmap_weeks = []
    for week in range(10):
        week_data = []
        for day_idx in range(7):
            day = grid_start + datetime.timedelta(days=week * 7 + day_idx)
            week_data.append({
                "date": str(day),
                "counts": day_counts(day),
                "future": day > today_date,
            })
        heatmap_weeks.append(week_data)

    return {
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "goals": [
            {"key": g["key"], "label": g["label"], "color": g["color"]}
            for g in goals
        ],
        "today": {
            "date": today,
            "has_entry": bool(summaries),
            "total_tasks": total_tasks,
            "by_goal": today_by_goal,
        },
        "streak": {
            "current_days": current_streak,
            "longest_days": longest,
        },
        "week_totals": week_totals,
        "last_7_days": last_7_days,
        "heatmap_weeks": heatmap_weeks,
    }
