import datetime

from fastapi import APIRouter

from app import database as db

router = APIRouter()


@router.get("/widget")
def get_widget():
    today = str(datetime.date.today())

    # Today's summaries
    summaries = db.fetchall(
        "SELECT goal, summary_text, task_count FROM daily_summaries WHERE summary_date = ?",
        (today,),
    )
    by_goal = {s["goal"]: s for s in summaries}

    goals_out = {}
    for goal in ("phd", "nl_jobs", "china_jobs"):
        s = by_goal.get(goal)
        goals_out[goal] = {
            "tasks": s["task_count"] if s else 0,
            "summary": s["summary_text"] if s else None,
        }

    total_tasks = sum(g["tasks"] for g in goals_out.values())

    # Streak (reuse same logic as stats endpoint)
    rows = db.fetchall(
        "SELECT DISTINCT entry_date FROM log_entries ORDER BY entry_date DESC"
    )
    dates = [datetime.date.fromisoformat(r["entry_date"]) for r in rows]
    # Current streak: consecutive days ending today or (if today not yet logged) yesterday
    today_date = datetime.date.today()
    current_streak = 0
    check = today_date
    for d in dates:
        if d == check:
            current_streak += 1
            check -= datetime.timedelta(days=1)
        elif d == today_date - datetime.timedelta(days=1) and current_streak == 0:
            # Today not yet logged — still honour yesterday's streak
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

    # Week totals (last 7 days, aggregate per goal)
    week_ago = str(today_date - datetime.timedelta(days=6))
    week_rows = db.fetchall(
        "SELECT t.goal, COUNT(*) as count FROM tasks t "
        "JOIN log_entries l ON t.log_entry_id = l.id "
        "WHERE l.entry_date >= ? GROUP BY t.goal",
        (week_ago,),
    )
    week_totals = {r["goal"]: r["count"] for r in week_rows}

    # last_7_days sparkline: per-day counts per goal (LEFT JOIN keeps days with entries but 0 tasks)
    sparkline_rows = db.fetchall(
        "SELECT l.entry_date, "
        "  SUM(CASE WHEN t.goal = 'phd'        THEN 1 ELSE 0 END) AS phd, "
        "  SUM(CASE WHEN t.goal = 'nl_jobs'    THEN 1 ELSE 0 END) AS nl_jobs, "
        "  SUM(CASE WHEN t.goal = 'china_jobs' THEN 1 ELSE 0 END) AS china_jobs "
        "FROM log_entries l "
        "LEFT JOIN tasks t ON t.log_entry_id = l.id "
        "WHERE l.entry_date >= ? "
        "GROUP BY l.entry_date "
        "ORDER BY l.entry_date ASC",
        (week_ago,),
    )
    sparkline_by_date = {r["entry_date"]: r for r in sparkline_rows}

    # Zero-fill: always return exactly 7 entries, oldest → newest
    last_7_days = []
    for offset in range(6, -1, -1):
        day = today_date - datetime.timedelta(days=offset)
        day_str = str(day)
        row = sparkline_by_date.get(day_str)
        last_7_days.append({
            "date":       day_str,
            "phd":        row["phd"]        if row else 0,
            "nl_jobs":    row["nl_jobs"]    if row else 0,
            "china_jobs": row["china_jobs"] if row else 0,
        })

    # 10-week heatmap grid aligned to Monday
    grid_start = today_date - datetime.timedelta(days=today_date.weekday() + 7 * 9)
    heatmap_rows = db.fetchall(
        "SELECT l.entry_date, "
        "  SUM(CASE WHEN t.goal = 'phd'        THEN 1 ELSE 0 END) AS phd, "
        "  SUM(CASE WHEN t.goal = 'nl_jobs'    THEN 1 ELSE 0 END) AS nl_jobs, "
        "  SUM(CASE WHEN t.goal = 'china_jobs' THEN 1 ELSE 0 END) AS china_jobs "
        "FROM log_entries l "
        "LEFT JOIN tasks t ON t.log_entry_id = l.id "
        "WHERE l.entry_date >= ? "
        "GROUP BY l.entry_date",
        (str(grid_start),),
    )
    heatmap_by_date = {r["entry_date"]: r for r in heatmap_rows}
    heatmap_weeks = []
    for week in range(10):
        week_data = []
        for day_idx in range(7):
            day = grid_start + datetime.timedelta(days=week * 7 + day_idx)
            day_str = str(day)
            row = heatmap_by_date.get(day_str)
            week_data.append({
                "date":       day_str,
                "phd":        row["phd"]        if row else 0,
                "nl_jobs":    row["nl_jobs"]    if row else 0,
                "china_jobs": row["china_jobs"] if row else 0,
                "future":     day > today_date,
            })
        heatmap_weeks.append(week_data)

    return {
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "today": {
            "date": today,
            "has_entry": bool(summaries),
            "total_tasks": total_tasks,
            "goals": goals_out,
        },
        "streak": {
            "current_days": current_streak,
            "longest_days": longest,
        },
        "week_totals": week_totals,
        "last_7_days": last_7_days,
        "heatmap_weeks": heatmap_weeks,
    }
