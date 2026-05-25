// Daily Tracker — macOS Übersicht Desktop Widget
export const command = "curl -s --max-time 5 http://localhost:8090/api/widget";
export const refreshFrequency = 60000;

// ── Constants ──────────────────────────────────────────────────────────────────

const GOALS = ["phd", "nl_jobs", "china_jobs"];
const LABELS = { phd: "PhD", nl_jobs: "NL Jobs", china_jobs: "China" };
const COLORS = { phd: "#60A5FA", nl_jobs: "#FB923C", china_jobs: "#F87171" };
const COLORS_RGB = {
  phd:        [96, 165, 250],
  nl_jobs:    [251, 146, 60],
  china_jobs: [248, 113, 113],
};

const CELL = 11;
const CGAP = 2;

// ── CSS ────────────────────────────────────────────────────────────────────────

export const css = `
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
  }

  .root {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 290px;
    pointer-events: all;
    font-family: -apple-system, "SF Pro Display", "Helvetica Neue", sans-serif;
    color: rgba(255,255,255,0.85);
    background: rgba(10,12,18,0.93);
    backdrop-filter: blur(30px) saturate(200%);
    -webkit-backdrop-filter: blur(30px) saturate(200%);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    overflow: hidden;
    user-select: none;
  }

  /* Header */
  .hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px 10px;
  }
  .hdr-date {
    font-size: 13px;
    font-weight: 500;
    color: rgba(255,255,255,0.75);
    letter-spacing: -0.01em;
  }
  .streak {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;
    color: #FBBF24;
    background: rgba(251,191,36,0.10);
    border-radius: 20px;
    padding: 3px 9px 3px 6px;
  }

  /* Heatmap */
  .hmap {
    padding: 0 16px 12px;
  }
  .hmap-grid {
    display: flex;
    gap: ${CGAP}px;
  }
  .hmap-days {
    display: flex;
    flex-direction: column;
    gap: ${CGAP}px;
    padding-top: 1px;
    margin-right: 3px;
  }
  .hmap-day {
    height: ${CELL}px;
    width: 8px;
    font-size: 7px;
    line-height: ${CELL}px;
    color: rgba(255,255,255,0.20);
    text-align: right;
  }
  .hmap-col {
    display: flex;
    flex-direction: column;
    gap: ${CGAP}px;
  }
  .hmap-cell {
    width: ${CELL}px;
    height: ${CELL}px;
    border-radius: 2px;
  }

  /* Divider */
  .div {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin: 0;
  }

  /* Goals */
  .goals {
    padding: 10px 16px 8px;
  }
  .goal {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
  }
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .goal-name {
    font-size: 12px;
    font-weight: 500;
    flex: 1;
    color: rgba(255,255,255,0.70);
  }
  .goal-today {
    font-size: 13px;
    font-weight: 700;
    min-width: 16px;
    text-align: right;
  }
  .goal-today-zero { color: rgba(255,255,255,0.18); }
  .goal-wk {
    font-size: 10px;
    color: rgba(255,255,255,0.28);
    min-width: 36px;
    text-align: right;
  }

  /* Proportion bar */
  .pbar-wrap {
    padding: 8px 16px 12px;
  }
  .pbar {
    display: flex;
    height: 3px;
    border-radius: 2px;
    overflow: hidden;
    gap: 1px;
    margin-bottom: 7px;
  }
  .pbar-empty {
    height: 3px;
    background: rgba(255,255,255,0.07);
    border-radius: 2px;
    margin-bottom: 7px;
  }
  .pseg { height: 100%; }
  .plegend {
    display: flex;
    gap: 10px;
  }
  .pleg-item {
    font-size: 10px;
    font-weight: 500;
    color: rgba(255,255,255,0.35);
  }
  .pleg-pct {
    font-weight: 700;
  }

  /* Footer */
  .footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 16px 10px;
    border-top: 1px solid rgba(255,255,255,0.05);
  }
  .footer-txt {
    font-size: 10px;
    color: rgba(255,255,255,0.22);
  }

  /* Offline */
  .offline {
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: rgba(255,255,255,0.35);
    font-size: 12px;
  }
`;

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", {
    weekday: "short", day: "numeric", month: "short",
  });
}

function fmtTime(isoUtc) {
  return new Date(isoUtc).toLocaleTimeString("en-GB", {
    hour: "numeric", minute: "2-digit",
  });
}

// ── Heatmap ────────────────────────────────────────────────────────────────────

function cellColor(cell) {
  if (cell.future) return "transparent";
  const total = (cell.phd || 0) + (cell.nl_jobs || 0) + (cell.china_jobs || 0);
  if (total === 0) return "rgba(255,255,255,0.07)";
  const max = Math.max(cell.phd || 0, cell.nl_jobs || 0, cell.china_jobs || 0);
  let key = "phd";
  if ((cell.nl_jobs || 0) === max) key = "nl_jobs";
  if ((cell.china_jobs || 0) === max) key = "china_jobs";
  const [r, g, b] = COLORS_RGB[key];
  const alpha = total >= 5 ? 0.95 : total >= 3 ? 0.72 : 0.48;
  return `rgba(${r},${g},${b},${alpha})`;
}

const DAY_LABELS = ["M", "", "W", "", "F", "", ""];

function Heatmap({ weeks }) {
  if (!weeks || !weeks.length) return null;
  return (
    <div className="hmap">
      <div className="hmap-grid">
        <div className="hmap-days">
          {DAY_LABELS.map((l, i) => <div key={i} className="hmap-day">{l}</div>)}
        </div>
        {weeks.map((week, wi) => (
          <div key={wi} className="hmap-col">
            {week.map((cell, di) => (
              <div key={di} className="hmap-cell" style={{ background: cellColor(cell) }} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Proportion bar ─────────────────────────────────────────────────────────────

function PBar({ weekTotals }) {
  const total = GOALS.reduce((s, k) => s + (weekTotals[k] || 0), 0);
  if (total === 0) return <div className="pbar-empty" />;
  return (
    <div className="pbar">
      {GOALS.map(k => {
        const c = weekTotals[k] || 0;
        if (!c) return null;
        return <div key={k} className="pseg" style={{ width: `${(c/total*100).toFixed(1)}%`, background: COLORS[k] }} />;
      })}
    </div>
  );
}

function PLegend({ weekTotals }) {
  const total = GOALS.reduce((s, k) => s + (weekTotals[k] || 0), 0);
  if (!total) return null;
  return (
    <div className="plegend">
      {GOALS.filter(k => weekTotals[k] > 0).map(k => (
        <span key={k} className="pleg-item">
          <span style={{ color: COLORS[k] }}>{LABELS[k]}</span>{" "}
          <span className="pleg-pct" style={{ color: COLORS[k] }}>
            {Math.round((weekTotals[k] || 0) / total * 100)}%
          </span>
        </span>
      ))}
    </div>
  );
}

// ── Render ─────────────────────────────────────────────────────────────────────

export function render({ output, error }) {
  if (error || !output || !output.trim()) {
    return (
      <div className="root">
        <div className="offline">⚠ Tracker offline — start the server</div>
      </div>
    );
  }

  let data;
  try { data = JSON.parse(output); }
  catch {
    return <div className="root"><div className="offline">⚠ Invalid response</div></div>;
  }

  const { today = {}, streak = {}, week_totals = {}, heatmap_weeks = [], updated_at } = data;
  const { goals = {}, total_tasks = 0 } = today;
  const weekTotal = GOALS.reduce((s, k) => s + (week_totals[k] || 0), 0);

  return (
    <div className="root">

      {/* Header */}
      <div className="hdr">
        <span className="hdr-date">{fmtDate(today.date)}</span>
        {(streak.current_days || 0) > 0 && (
          <span className="streak">🔥 {streak.current_days}d</span>
        )}
      </div>

      {/* Heatmap */}
      <Heatmap weeks={heatmap_weeks} />

      <hr className="div" />

      {/* Goal list */}
      <div className="goals">
        {GOALS.map(k => {
          const count = (goals[k] || {}).tasks || 0;
          const wk = week_totals[k] || 0;
          return (
            <div key={k} className="goal">
              <div className="dot" style={{ background: COLORS[k] }} />
              <span className="goal-name">{LABELS[k]}</span>
              <span
                className={`goal-today${count === 0 ? " goal-today-zero" : ""}`}
                style={count > 0 ? { color: COLORS[k] } : {}}
              >
                {count > 0 ? count : "–"}
              </span>
              <span className="goal-wk">{wk > 0 ? `${wk} this wk` : ""}</span>
            </div>
          );
        })}
      </div>

      <hr className="div" />

      {/* Proportion bar */}
      <div className="pbar-wrap">
        <PBar weekTotals={week_totals} />
        {weekTotal > 0 && <PLegend weekTotals={week_totals} />}
      </div>

      {/* Footer */}
      <div className="footer">
        <span className="footer-txt">
          {total_tasks > 0 ? `${total_tasks} tasks today` : "Nothing logged yet"}
        </span>
        {updated_at && <span className="footer-txt">{fmtTime(updated_at)}</span>}
      </div>

    </div>
  );
}
