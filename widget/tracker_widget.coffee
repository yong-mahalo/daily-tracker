command: "curl -s --max-time 5 'http://localhost:8090/api/widget'"
refreshFrequency: 60000

style: """
  body
    position: fixed
    top: 20px
    right: 20px
    width: 310px
    font-family: -apple-system, "SF Pro Display", sans-serif
    background: rgba(10,12,18,0.94)
    -webkit-backdrop-filter: blur(30px) saturate(180%)
    border: 1px solid rgba(255,255,255,0.08)
    border-radius: 14px
    overflow: hidden
    color: rgba(255,255,255,0.85)
    -webkit-font-smoothing: antialiased
    pointer-events: none

  .root
    padding: 14px 16px 12px

  .hdr
    display: flex
    align-items: center
    justify-content: space-between
    margin-bottom: 12px

  .hdr-date
    font-size: 13px
    font-weight: 500
    color: rgba(255,255,255,0.7)

  .streak
    font-size: 12px
    font-weight: 600
    color: #FB923C

  .heatmap
    display: flex
    gap: 2px
    margin-bottom: 12px

  .week
    display: flex
    flex-direction: column
    gap: 2px

  .cell
    width: 11px
    height: 11px
    border-radius: 2px
    flex-shrink: 0

  .legend
    display: flex
    gap: 6px
    align-items: center
    margin-bottom: 10px

  .leg-dot
    width: 8px
    height: 8px
    border-radius: 2px
    flex-shrink: 0

  .leg-label
    font-size: 10px
    color: rgba(255,255,255,0.35)
    margin-right: 4px

  .goals
    display: flex
    flex-direction: column
    gap: 6px
    margin-bottom: 10px

  .goal-row
    display: flex
    align-items: center
    gap: 8px
    font-size: 12px

  .dot
    width: 8px
    height: 8px
    border-radius: 50%
    flex-shrink: 0

  .goal-name
    flex: 1
    color: rgba(255,255,255,0.8)

  .goal-today
    font-size: 12px
    font-weight: 600
    color: rgba(255,255,255,0.9)
    min-width: 14px
    text-align: right

  .goal-week
    font-size: 11px
    color: rgba(255,255,255,0.3)
    min-width: 52px
    text-align: right

  .divider
    height: 1px
    background: rgba(255,255,255,0.06)
    margin-bottom: 8px

  .footer
    font-size: 11px
    color: rgba(255,255,255,0.3)
    text-align: center
"""

COLORS =
  phd:        ['#1e3a5f', '#1d4ed8', '#2563eb', '#60a5fa']
  nl_jobs:    ['#5c2e0a', '#c2410c', '#ea580c', '#fb923c']
  china_jobs: ['#4c0519', '#b91c1c', '#dc2626', '#f87171']

GOAL_KEYS   = ['phd', 'nl_jobs', 'china_jobs']
GOAL_LABELS = {phd: 'PhD', nl_jobs: 'NL Jobs', china_jobs: 'China'}
GOAL_DOTS   = {phd: '#60a5fa', nl_jobs: '#fb923c', china_jobs: '#f87171'}

cellColor = (cell) ->
  total = (cell.phd or 0) + (cell.nl_jobs or 0) + (cell.china_jobs or 0)
  return '#0d1017' if cell.future
  return '#1a1f2e' if total is 0
  counts  = {phd: cell.phd or 0, nl_jobs: cell.nl_jobs or 0, china_jobs: cell.china_jobs or 0}
  dominant = Object.keys(counts).reduce (a, b) -> if counts[a] >= counts[b] then a else b
  level    = if total <= 1 then 0 else if total <= 3 then 1 else if total <= 5 then 2 else 3
  COLORS[dominant][level]

render: (output) ->
  try
    data = JSON.parse output
  catch
    return "<div class='root' style='color:rgba(255,255,255,0.3);font-size:12px'>Loading…</div>"

  today  = data.today  or {}
  streak = data.streak or {}
  week   = data.week_totals or {}
  weeks  = data.heatmap_weeks or []
  goals  = today.goals or {}

  # ── Header
  now    = new Date()
  DAYS   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']
  MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  dateStr  = "#{DAYS[now.getDay()]} #{now.getDate()} #{MONTHS[now.getMonth()]}"
  streakHtml = if (streak.current_days or 0) > 0
    "<span class='streak'>🔥 #{streak.current_days}d</span>"
  else ''

  # ── Heatmap grid
  hmHtml = weeks.map((wk) ->
    cells = wk.map((cell) ->
      "<div class='cell' style='background:#{cellColor(cell)}'></div>"
    ).join('')
    "<div class='week'>#{cells}</div>"
  ).join('')

  # ── Legend
  legHtml = GOAL_KEYS.map((key) ->
    """<div class='leg-dot' style='background:#{GOAL_DOTS[key]}'></div>
       <span class='leg-label'>#{GOAL_LABELS[key]}</span>"""
  ).join('')

  # ── Goal rows
  goalsHtml = GOAL_KEYS.map((key) ->
    todayN  = goals[key]?.tasks or 0
    wkN     = week[key] or 0
    todayTxt = if todayN > 0 then "#{todayN}" else '–'
    wkTxt    = if wkN > 0 then "#{wkN} this wk" else ''
    """<div class='goal-row'>
         <div class='dot' style='background:#{GOAL_DOTS[key]}'></div>
         <span class='goal-name'>#{GOAL_LABELS[key]}</span>
         <span class='goal-today'>#{todayTxt}</span>
         <span class='goal-week'>#{wkTxt}</span>
       </div>"""
  ).join('')

  total   = today.total_tasks or 0
  footer  = if total > 0 then "#{total} tasks today" else "Nothing logged yet"

  """
  <div class='root'>
    <div class='hdr'>
      <span class='hdr-date'>#{dateStr}</span>
      #{streakHtml}
    </div>
    <div class='heatmap'>#{hmHtml}</div>
    <div class='legend'>#{legHtml}</div>
    <div class='divider'></div>
    <div class='goals'>#{goalsHtml}</div>
    <div class='footer'>#{footer}</div>
  </div>
  """
