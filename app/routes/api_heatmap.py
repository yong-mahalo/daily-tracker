import datetime

from fastapi import APIRouter

from app import database as db
from app.services import heatmap as heatmap_svc

router = APIRouter()


@router.get("/heatmap")
def get_heatmap(year: int | None = None, month: int | None = None):
    today = datetime.date.today()
    year = year or today.year
    month = month or today.month
    cells = heatmap_svc.get_month_cells(year, month)
    return {"year": year, "month": month, "cells": cells}


@router.get("/stats")
def get_stats():
    # Current streak: consecutive days with at least one entry, ending today or yesterday
    today = datetime.date.today()
    rows = db.fetchall(
        "SELECT DISTINCT entry_date FROM log_entries ORDER BY entry_date DESC"
    )
    dates = [datetime.date.fromisoformat(r["entry_date"]) for r in rows]

    current_streak = 0
    check = today
    for d in dates:
        if d == check:
            current_streak += 1
            check -= datetime.timedelta(days=1)
        elif d == today - datetime.timedelta(days=1) and current_streak == 0:
            # Allow streak to start from yesterday
            current_streak += 1
            check = d - datetime.timedelta(days=1)
        else:
            break

    # Longest streak
    longest = 0
    run = 0
    prev = None
    for d in reversed(dates):
        if prev is None or (d - prev).days == 1:
            run += 1
        else:
            longest = max(longest, run)
            run = 1
        prev = d
    longest = max(longest, run)

    # Totals per goal
    totals = db.fetchall(
        "SELECT goal, COUNT(*) as count FROM tasks GROUP BY goal"
    )
    totals_by_goal = {r["goal"]: r["count"] for r in totals}

    return {
        "current_streak": current_streak,
        "longest_streak": longest,
        "total_tasks": totals_by_goal,
        "total_days_logged": len(dates),
    }
