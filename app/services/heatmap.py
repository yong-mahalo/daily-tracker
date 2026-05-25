import calendar
import datetime

from app import database as db
from app.config import CONFIG

GOALS = ["phd", "nl_jobs", "china_jobs"]


def get_month_cells(year: int, month: int) -> list[dict]:
    """Return a list of cell dicts for every day in the given month."""
    # Fetch all task counts for this month
    month_str = f"{year}-{month:02d}"
    rows = db.fetchall(
        "SELECT l.entry_date, t.goal, COUNT(*) as count "
        "FROM tasks t JOIN log_entries l ON t.log_entry_id = l.id "
        "WHERE l.entry_date LIKE ? "
        "GROUP BY l.entry_date, t.goal",
        (f"{month_str}-%",),
    )

    # Build a nested dict: date -> goal -> count
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        d = row["entry_date"]
        if d not in counts:
            counts[d] = {g: 0 for g in GOALS}
        counts[d][row["goal"]] = row["count"]

    # Generate one cell per calendar day
    _, days_in_month = calendar.monthrange(year, month)
    cells = []
    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        task_counts = counts.get(date_str, {g: 0 for g in GOALS})
        total = sum(task_counts.values())
        cells.append(
            {
                "date": date_str,
                "weekday": datetime.date(year, month, day).weekday(),  # 0=Mon
                "has_entry": total > 0,
                "task_counts": task_counts,
                "total_tasks": total,
                "gradient_css": compute_gradient_css(task_counts) if total > 0 else "",
            }
        )
    return cells


def compute_gradient_css(task_counts: dict[str, int]) -> str:
    """
    Returns a CSS linear-gradient string proportional to task counts per goal.
    Colors come from config. Opacity encodes intensity within each band.
    """
    colors = CONFIG.get("goal_colors", {})
    color_map = {
        "phd": colors.get("phd", "#3B82F6"),
        "nl_jobs": colors.get("nl_jobs", "#F97316"),
        "china_jobs": colors.get("china_jobs", "#EF4444"),
    }

    active = [(g, task_counts[g]) for g in GOALS if task_counts.get(g, 0) > 0]
    if not active:
        return ""

    total = sum(c for _, c in active)

    # If only one goal, return a solid color with intensity-based opacity
    if len(active) == 1:
        goal, count = active[0]
        opacity = _opacity(count)
        return f"background-color: {_hex_with_opacity(color_map[goal], opacity)}"

    # Multi-goal: proportional gradient
    stops = []
    cumulative = 0.0
    for goal, count in active:
        pct_start = cumulative / total * 100
        cumulative += count
        pct_end = cumulative / total * 100
        opacity = _opacity(count)
        color = _hex_with_opacity(color_map[goal], opacity)
        stops.append(f"{color} {pct_start:.1f}% {pct_end:.1f}%")

    return f"background: linear-gradient(to right, {', '.join(stops)})"


def _opacity(count: int) -> float:
    if count <= 2:
        return 0.45
    if count <= 5:
        return 0.70
    return 1.0


def _hex_with_opacity(hex_color: str, opacity: float) -> str:
    """Convert #RRGGBB + opacity float to rgba(r, g, b, opacity)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{opacity:.2f})"
