// Daily Progress Tracker — Scriptable Widget
// ─────────────────────────────────────────────
// 1. Install Scriptable from the Mac App Store
// 2. Open Scriptable → New Script → paste this file
// 3. Name it "Daily Tracker"
// 4. Add to desktop: right-click desktop → Edit Widgets → find Scriptable
// ─────────────────────────────────────────────
// Data is written by the menu bar app (menubar_widget.py) every 60s.
// File: ~/Library/Mobile Documents/iCloud~dk~simonbs~Scriptable/Documents/tracker_data.json

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  bg:         new Color("#0a0c12"),
  bgCell:     new Color("#1a1f2e"),       // empty cell
  bgFuture:   new Color("#0d1017"),       // future cell (slightly darker)
  text:       new Color("#e5e7eb"),
  textDim:    new Color("#6b7280"),
  textMuted:  new Color("#374151"),

  // PhD — blue shades (light → dark)
  phd: [
    new Color("#1e3a5f"),
    new Color("#1d4ed8"),
    new Color("#2563eb"),
    new Color("#60a5fa"),
  ],
  // NL Jobs — orange shades
  nl_jobs: [
    new Color("#5c2e0a"),
    new Color("#c2410c"),
    new Color("#ea580c"),
    new Color("#fb923c"),
  ],
  // China — red shades
  china_jobs: [
    new Color("#4c0519"),
    new Color("#b91c1c"),
    new Color("#dc2626"),
    new Color("#f87171"),
  ],
}

const GOAL_KEYS   = ["phd", "nl_jobs", "china_jobs"]
const GOAL_LABELS = { phd: "PhD", nl_jobs: "NL Jobs", china_jobs: "China" }

// ── Load data from file ───────────────────────────────────────────────────────
async function loadData() {
  try {
    const fm   = FileManager.iCloud()
    const path = fm.joinPath(fm.documentsDirectory(), "tracker_data.json")
    if (!fm.fileExists(path)) return null
    await fm.downloadFileFromiCloud(path)
    return JSON.parse(fm.readString(path))
  } catch (e) {
    return null
  }
}

// ── Draw the heatmap grid ─────────────────────────────────────────────────────
function drawHeatmap(weeks) {
  const CELL = 11
  const GAP  = 2
  const STEP = CELL + GAP
  const COLS = weeks.length   // 10 weeks
  const ROWS = 7              // Mon–Sun

  const ctx = new DrawContext()
  ctx.size = new Size(COLS * STEP - GAP, ROWS * STEP - GAP)
  ctx.opaque = false
  ctx.respectScreenScale = true

  for (let col = 0; col < COLS; col++) {
    for (let row = 0; row < ROWS; row++) {
      const cell  = weeks[col][row]
      const total = (cell.phd || 0) + (cell.nl_jobs || 0) + (cell.china_jobs || 0)

      let color
      if (cell.future) {
        color = C.bgFuture
      } else if (total === 0) {
        color = C.bgCell
      } else {
        // Pick the dominant goal and shade by intensity
        const counts  = { phd: cell.phd || 0, nl_jobs: cell.nl_jobs || 0, china_jobs: cell.china_jobs || 0 }
        const dominant = Object.entries(counts).sort(([, a], [, b]) => b - a)[0][0]
        const level    = total <= 1 ? 0 : total <= 3 ? 1 : total <= 5 ? 2 : 3
        color = C[dominant][level]
      }

      ctx.setFillColor(color)
      ctx.fillRect(new Rect(col * STEP, row * STEP, CELL, CELL))
    }
  }

  return ctx.getImage()
}

// ── Build widget ──────────────────────────────────────────────────────────────
async function buildWidget(data) {
  const w = new ListWidget()
  w.backgroundColor = C.bg
  w.setPadding(14, 16, 12, 16)
  w.url = "http://localhost:8090"

  // ── Offline state
  if (!data) {
    const t = w.addText("Tracker offline ⚠️")
    t.textColor = Color.orange()
    t.font = Font.mediumSystemFont(13)
    return w
  }

  const { today, streak, week_totals, heatmap_weeks } = data

  // ── Header: date + streak
  const hdr = w.addStack()
  hdr.layoutHorizontally()
  hdr.centerAlignContent()

  const now     = new Date()
  const dateStr = now.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })
  const dateLbl = hdr.addText(dateStr)
  dateLbl.font      = Font.mediumSystemFont(13)
  dateLbl.textColor = C.text

  hdr.addSpacer()

  const streakDays = streak?.current_days ?? 0
  if (streakDays > 0) {
    const sl = hdr.addText(`🔥 ${streakDays}d`)
    sl.font = Font.mediumSystemFont(12)
  }

  w.addSpacer(10)

  // ── Heatmap grid
  if (heatmap_weeks?.length) {
    const STEP = 13  // CELL(11) + GAP(2)
    const imgW = heatmap_weeks.length * STEP - 2
    const imgH = 7 * STEP - 2

    const heatImg = w.addImage(drawHeatmap(heatmap_weeks))
    heatImg.imageSize  = new Size(imgW, imgH)
    heatImg.cornerRadius = 2
    heatImg.leftAlignImage()
  }

  w.addSpacer(10)

  // ── Goal rows: dot · name · today count · week count
  const totalWk = GOAL_KEYS.reduce((s, k) => s + (week_totals[k] || 0), 0)

  for (const key of GOAL_KEYS) {
    const row = w.addStack()
    row.layoutHorizontally()
    row.centerAlignContent()

    // Coloured dot
    const dot = row.addText("●")
    dot.font      = Font.systemFont(9)
    dot.textColor = C[key][3]

    row.addSpacer(6)

    // Goal name
    const lbl = row.addText(GOAL_LABELS[key])
    lbl.font      = Font.systemFont(12)
    lbl.textColor = C.text

    row.addSpacer()

    // Today
    const todayN   = today?.goals?.[key]?.tasks ?? 0
    const todayTxt = row.addText(todayN > 0 ? String(todayN) : "–")
    todayTxt.font      = Font.mediumSystemFont(12)
    todayTxt.textColor = todayN > 0 ? C.text : C.textMuted

    row.addSpacer(10)

    // This week
    const wkN   = week_totals[key] || 0
    const wkTxt = row.addText(`${wkN} wk`)
    wkTxt.font      = Font.systemFont(11)
    wkTxt.textColor = C.textDim

    w.addSpacer(5)
  }

  w.addSpacer()

  // ── Legend row (PhD · NL Jobs · China)
  const legend = w.addStack()
  legend.layoutHorizontally()
  legend.centerAlignContent()

  for (const key of GOAL_KEYS) {
    const dot = legend.addText("■ ")
    dot.font      = Font.systemFont(9)
    dot.textColor = C[key][3]
    const lbl = legend.addText(GOAL_LABELS[key] + "  ")
    lbl.font      = Font.systemFont(9)
    lbl.textColor = C.textDim
  }
  legend.addSpacer()

  const totalToday = today?.total_tasks ?? 0
  const footerLbl  = legend.addText(totalToday > 0 ? `${totalToday} today` : "–")
  footerLbl.font      = Font.systemFont(10)
  footerLbl.textColor = C.textDim

  return w
}

// ── Run ───────────────────────────────────────────────────────────────────────
const data   = await loadData()
const widget = await buildWidget(data)

if (config.runsInWidget) {
  Script.setWidget(widget)
} else {
  await widget.presentMedium()
}
Script.complete()
