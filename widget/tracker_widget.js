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
// ─────────────────────────────────────────────────────────────────────────────

const BASE_URL  = "http://192.168.0.112:8090";  // ← local Mac (same WiFi)
// const BASE_URL = "https://your-app.up.railway.app";  // ← uncomment after Railway deploy
const WEB_URL   = BASE_URL;

// ── Colours ──────────────────────────────────────────────────────────────────
const C = {
  phd:    new Color("#60A5FA"),   // soft blue
  nl:     new Color("#FB923C"),   // soft orange
  cn:     new Color("#F87171"),   // soft red
  bg:     new Color("#0d0f14"),   // near-black
  card:   new Color("#161921"),   // card surface
  border: new Color("#FFFFFF", 0.07),
  text:   new Color("#FFFFFF", 0.88),
  sub:    new Color("#FFFFFF", 0.55),
  muted:  new Color("#FFFFFF", 0.32),
  streak: new Color("#FBBF24"),   // amber for streak fire
  empty:  new Color("#FFFFFF", 0.07),
};

const GOAL_KEYS    = ["phd", "nl_jobs", "china_jobs"];
const GOAL_LABELS  = { phd: "PhD", nl_jobs: "NL Jobs", china_jobs: "China" };
const GOAL_COLORS  = { phd: C.phd, nl_jobs: C.nl, china_jobs: C.cn };

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
    // ── Offline / error state ──
    const err = w.addText("⚠ Tracker offline");
    err.textColor = C.muted;
    err.font = Font.mediumSystemFont(13);
    return w;
  }

  const today   = data.today;
  const streak  = data.streak;
  const goals   = today.goals;

  // ── Header row ───────────────────────────────────────────────────────────
  const header = w.addStack();
  header.layoutHorizontally();
  header.centerAlignContent();

  const titleTxt = header.addText("Daily Tracker");
  titleTxt.textColor = C.text;
  titleTxt.font = Font.boldSystemFont(12);
  titleTxt.lineLimit = 1;

  header.addSpacer();

  // Streak chip
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
  const dateStr = formatDate(today.date);
  const dateTxt = w.addText(dateStr);
  dateTxt.textColor = C.muted;
  dateTxt.font = Font.systemFont(10);

  w.addSpacer(10);

  // ── Goal rows ──────────────────────────────────────────────────────────────
  for (const key of GOAL_KEYS) {
    const g     = goals[key];
    const color = GOAL_COLORS[key];
    const count = g.tasks;
    const max   = Math.max(...GOAL_KEYS.map(k => goals[k].tasks), 1);

    const row = w.addStack();
    row.layoutHorizontally();
    row.centerAlignContent();
    row.spacing = 8;

    // Colour dot
    const dot = row.addStack();
    dot.layoutHorizontally();
    dot.centerAlignContent();
    dot.backgroundColor = color;
    dot.cornerRadius = 3;
    dot.size = new Size(3, 26);

    // Label + summary
    const labelCol = row.addStack();
    labelCol.layoutVertically();
    labelCol.spacing = 1;

    const labelTxt = labelCol.addText(GOAL_LABELS[key]);
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

    // Task count + mini bar
    const rightCol = row.addStack();
    rightCol.layoutVertically();
    rightCol.centerAlignContent();
    rightCol.spacing = 3;

    const countTxt = rightCol.addText(count > 0 ? `${count}` : "–");
    countTxt.textColor = count > 0 ? color : C.muted;
    countTxt.font = Font.boldSystemFont(14);
    countTxt.rightAlignText();

    // Mini progress bar (proportional to max tasks today)
    const barOuter = rightCol.addStack();
    barOuter.backgroundColor = C.empty;
    barOuter.cornerRadius = 2;
    barOuter.size = new Size(36, 3);
    barOuter.layoutHorizontally();

    if (count > 0) {
      const fillW = Math.round((count / max) * 36);
      const barFill = barOuter.addStack();
      barFill.backgroundColor = color;
      barFill.cornerRadius = 2;
      barFill.size = new Size(fillW, 3);
    }

    if (key !== GOAL_KEYS[GOAL_KEYS.length - 1]) {
      w.addSpacer(7);
    }
  }

  w.addSpacer();

  // ── Footer ─────────────────────────────────────────────────────────────────
  const footer = w.addStack();
  footer.layoutHorizontally();
  footer.centerAlignContent();

  const totalToday = GOAL_KEYS.reduce((s, k) => s + goals[k].tasks, 0);
  const footerTxt  = footer.addText(
    totalToday > 0
      ? `${totalToday} tasks today`
      : "Nothing logged yet"
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
  // Preview in app
  widget.presentMedium();
}
Script.complete();
