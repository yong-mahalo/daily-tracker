// ─────────────────────────────────────────────────────────────────────────────
//  Daily Progress Tracker — iOS Home Screen Widget
//  Built for Scriptable (https://scriptable.app)
//
//  HOW TO INSTALL:
//  1. Download Scriptable (free) from the App Store
//  2. Create a new script, name it "Daily Tracker", paste this entire file
//  3. Long-press home screen → + → Scriptable → Medium widget
//  4. Long-press widget → Edit Widget → Script: Daily Tracker
//
//  LOCAL (same WiFi): use http://YOUR_MAC_IP:8090  (Mac must be on)
//  CLOUD (Railway):   use https://your-app.up.railway.app
//
//  Goals (label + color) are read from the /api/widget response, so this file
//  does not need editing when you add or rename goals via /settings.
// ─────────────────────────────────────────────────────────────────────────────

// Replace YOUR_MAC_IP with your Mac's local IP (System Settings → Wi-Fi → Details)
// when running on the same WiFi, or use your Railway URL after deploying.
const BASE_URL  = "http://YOUR_MAC_IP:8090";
// const BASE_URL = "https://your-app.up.railway.app";
const WEB_URL   = BASE_URL;

// ── Static colours (everything except per-goal colours) ──────────────────────
const C = {
  bg:     new Color("#0d0f14"),
  card:   new Color("#161921"),
  border: new Color("#FFFFFF", 0.07),
  text:   new Color("#FFFFFF", 0.88),
  sub:    new Color("#FFFFFF", 0.55),
  muted:  new Color("#FFFFFF", 0.32),
  streak: new Color("#FBBF24"),
  empty:  new Color("#FFFFFF", 0.07),
};

// ── Fetch data ────────────────────────────────────────────────────────────────
async function fetchWidget() {
  const req = new Request(`${BASE_URL}/api/widget`);
  req.timeoutInterval = 10;
  try {
    return await req.loadJSON();
  } catch (e) {
    return null;
  }
}

// ── Build widget ──────────────────────────────────────────────────────────────
async function buildWidget(data) {
  const w = new ListWidget();
  w.url = WEB_URL;
  w.backgroundColor = C.bg;
  w.setPadding(14, 16, 14, 16);

  if (!data) {
    const err = w.addText("⚠ Tracker offline");
    err.textColor = C.muted;
    err.font = Font.mediumSystemFont(13);
    return w;
  }

  const today   = data.today;
  const streak  = data.streak;
  const goalDefs = data.goals || [];
  const byGoal  = today.by_goal || {};

  // ── Header row ───────────────────────────────────────────────────────────
  const header = w.addStack();
  header.layoutHorizontally();
  header.centerAlignContent();

  const titleTxt = header.addText("Daily Tracker");
  titleTxt.textColor = C.text;
  titleTxt.font = Font.boldSystemFont(12);
  titleTxt.lineLimit = 1;

  header.addSpacer();

  if (streak.current_days > 0) {
    const streakStack = header.addStack();
    streakStack.layoutHorizontally();
    streakStack.centerAlignContent();
    streakStack.spacing = 2;
    streakStack.backgroundColor = new Color("#FBBF24", 0.12);
    streakStack.cornerRadius = 8;
    streakStack.setPadding(3, 7, 3, 7);
    const fire = streakStack.addText("🔥");
    fire.font = Font.systemFont(9);
    const streakNum = streakStack.addText(`${streak.current_days}d`);
    streakNum.textColor = C.streak;
    streakNum.font = Font.boldSystemFont(10);
  }

  w.addSpacer(8);

  // ── Date subheader ─────────────────────────────────────────────────────────
  const dateTxt = w.addText(formatDate(today.date));
  dateTxt.textColor = C.muted;
  dateTxt.font = Font.systemFont(10);

  w.addSpacer(10);

  // ── Goal rows (dynamic; one per goal returned by the API) ───────────────
  if (goalDefs.length === 0) {
    const none = w.addText("No goals configured. Open Settings.");
    none.textColor = C.muted;
    none.font = Font.systemFont(11);
  } else {
    const maxCount = Math.max(...goalDefs.map(g => (byGoal[g.key]?.tasks ?? 0)), 1);

    goalDefs.forEach((goal, idx) => {
      const g     = byGoal[goal.key] || { tasks: 0, summary: null };
      const color = new Color(goal.color);
      const count = g.tasks;

      const row = w.addStack();
      row.layoutHorizontally();
      row.centerAlignContent();
      row.spacing = 8;

      const dot = row.addStack();
      dot.layoutHorizontally();
      dot.centerAlignContent();
      dot.backgroundColor = color;
      dot.cornerRadius = 3;
      dot.size = new Size(3, 26);

      const labelCol = row.addStack();
      labelCol.layoutVertically();
      labelCol.spacing = 1;

      const labelTxt = labelCol.addText(goal.label);
      labelTxt.textColor = count > 0 ? C.text : C.muted;
      labelTxt.font = Font.semiboldSystemFont(11);
      labelTxt.lineLimit = 1;

      if (g.summary && count > 0) {
        const sumTxt = labelCol.addText(g.summary);
        sumTxt.textColor = C.sub;
        sumTxt.font = Font.systemFont(9);
        sumTxt.lineLimit = 2;
      } else if (count === 0) {
        const nothingTxt = labelCol.addText("No activity");
        nothingTxt.textColor = C.muted;
        nothingTxt.font = Font.systemFont(9);
      }

      row.addSpacer();

      const rightCol = row.addStack();
      rightCol.layoutVertically();
      rightCol.centerAlignContent();
      rightCol.spacing = 3;

      const countTxt = rightCol.addText(count > 0 ? `${count}` : "–");
      countTxt.textColor = count > 0 ? color : C.muted;
      countTxt.font = Font.boldSystemFont(14);
      countTxt.rightAlignText();

      const barOuter = rightCol.addStack();
      barOuter.backgroundColor = C.empty;
      barOuter.cornerRadius = 2;
      barOuter.size = new Size(36, 3);
      barOuter.layoutHorizontally();

      if (count > 0) {
        const fillW = Math.round((count / maxCount) * 36);
        const barFill = barOuter.addStack();
        barFill.backgroundColor = color;
        barFill.cornerRadius = 2;
        barFill.size = new Size(fillW, 3);
      }

      if (idx !== goalDefs.length - 1) w.addSpacer(7);
    });
  }

  w.addSpacer();

  // ── Footer ─────────────────────────────────────────────────────────────────
  const footer = w.addStack();
  footer.layoutHorizontally();
  footer.centerAlignContent();

  const totalToday = today.total_tasks ?? 0;
  const footerTxt  = footer.addText(
    totalToday > 0 ? `${totalToday} tasks today` : "Nothing logged yet"
  );
  footerTxt.textColor = C.muted;
  footerTxt.font = Font.systemFont(9);

  footer.addSpacer();

  const updated = new Date(data.updated_at);
  const timeTxt = footer.addText(formatTime(updated));
  timeTxt.textColor = C.muted;
  timeTxt.font = Font.systemFont(9);

  return w;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatDate(isoDate) {
  const d = new Date(isoDate + "T00:00:00");
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

function formatTime(date) {
  return date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", hour12: true });
}

// ── Run ───────────────────────────────────────────────────────────────────────
const data   = await fetchWidget();
const widget = await buildWidget(data);

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  widget.presentMedium();
}
Script.complete();
