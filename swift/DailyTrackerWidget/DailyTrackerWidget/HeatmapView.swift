import SwiftUI

// MARK: - Color palettes

private let palettes: [GoalKey: [String]] = [
    .phd:        ["#1a3560", "#1d4ed8", "#3b82f6", "#93c5fd"],
    .nl_jobs:    ["#6b2d0a", "#c2410c", "#f97316", "#fdba74"],
    .china_jobs: ["#5c0a1a", "#b91c1c", "#ef4444", "#fca5a5"],
]

private let emptyCell  = Color(hex: "#2a3450")
private let futureCell = Color(hex: "#111520")

extension Color {
    init(hex: String) {
        let h = hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
        var rgb: UInt64 = 0
        Scanner(string: h).scanHexInt64(&rgb)
        self.init(
            red:   Double((rgb >> 16) & 0xFF) / 255,
            green: Double((rgb >> 8)  & 0xFF) / 255,
            blue:  Double(rgb         & 0xFF) / 255
        )
    }
}

private func stripeColor(key: GoalKey, count: Int, isFuture: Bool) -> Color {
    if isFuture { return futureCell }
    if count == 0 { return emptyCell }
    let level = count <= 1 ? 0 : count <= 3 ? 1 : count <= 6 ? 2 : 3
    return Color(hex: palettes[key]![level])
}

// MARK: - Single day: 3 vertical stripes [PhD|NL|China]

struct DayCellView: View {
    let cell: HeatmapCell
    var isToday: Bool = false

    private let sw: CGFloat = 4
    private let ch: CGFloat = 11

    var body: some View {
        HStack(spacing: 0) {
            stripe(.phd,        cell.phdCount)
            stripe(.nl_jobs,    cell.nlCount)
            stripe(.china_jobs, cell.chinaCount)
        }
        .frame(width: sw * 3, height: ch)
        .clipShape(RoundedRectangle(cornerRadius: 2))
        .overlay(
            RoundedRectangle(cornerRadius: 2)
                .stroke(Color.white.opacity(isToday ? 0.85 : 0), lineWidth: 1.5)
        )
    }

    private func stripe(_ key: GoalKey, _ count: Int) -> some View {
        Rectangle()
            .fill(stripeColor(key: key, count: count, isFuture: cell.isFuture))
            .frame(width: sw, height: ch)
    }
}

// MARK: - Full heatmap: day labels + week labels + today indicator

struct HeatmapView: View {
    let weeks: [[HeatmapCell]]

    private let cellW: CGFloat  = 12   // 3 × 4px stripes
    private let cellH: CGFloat  = 11
    private let colGap: CGFloat = 3
    private let rowGap: CGFloat = 2
    private let labelW: CGFloat = 10   // day-of-week label column

    // Today: day-of-week index Mon=0 … Sun=6
    private var todayDayIdx: Int {
        let wd = Calendar.current.component(.weekday, from: Date()) // 1=Sun
        return (wd + 5) % 7
    }

    private func weekLabel(_ wi: Int) -> String {
        let ago = (weeks.count - 1) - wi
        if ago == 0 { return "●" }
        // show label every 2 weeks; hide others to reduce clutter
        if ago % 2 == 1 { return "" }
        return "\(ago)w"
    }

    private func dayLabel(_ di: Int) -> String {
        switch di { case 0: return "M"; case 2: return "W"; case 4: return "F"; default: return "" }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {

            // ── Week labels row ───────────────────────────────
            HStack(spacing: 0) {
                Spacer().frame(width: labelW + colGap)
                HStack(spacing: colGap) {
                    ForEach(0..<weeks.count, id: \.self) { wi in
                        Text(weekLabel(wi))
                            .font(.system(size: 8))
                            .foregroundColor(
                                wi == weeks.count - 1
                                    ? Color.white.opacity(0.55)
                                    : Color.white.opacity(0.22)
                            )
                            .frame(width: cellW, alignment: .center)
                    }
                }
            }

            // ── Day labels + cell grid ─────────────────────────
            HStack(alignment: .top, spacing: colGap) {

                // Day-of-week labels (M W F)
                VStack(spacing: rowGap) {
                    ForEach(0..<7, id: \.self) { di in
                        Text(dayLabel(di))
                            .font(.system(size: 8))
                            .foregroundColor(.white.opacity(0.25))
                            .frame(width: labelW, height: cellH, alignment: .trailing)
                    }
                }

                // Cell columns
                HStack(spacing: colGap) {
                    ForEach(0..<weeks.count, id: \.self) { wi in
                        let isCurrentWeek = wi == weeks.count - 1
                        VStack(spacing: rowGap) {
                            ForEach(0..<weeks[wi].count, id: \.self) { di in
                                DayCellView(
                                    cell: weeks[wi][di],
                                    isToday: isCurrentWeek && di == todayDayIdx
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Compact legend

struct LegendDots: View {
    var body: some View {
        HStack(spacing: 8) {
            ForEach([GoalKey.phd, .nl_jobs, .china_jobs], id: \.self) { key in
                HStack(spacing: 3) {
                    RoundedRectangle(cornerRadius: 1)
                        .fill(Color(hex: palettes[key]![2]))
                        .frame(width: 8, height: 8)
                    Text(key.label)
                        .font(.system(size: 10))
                        .foregroundColor(.white.opacity(0.38))
                }
            }
            Spacer()
            Text("3 stripes/day")
                .font(.system(size: 9))
                .foregroundColor(.white.opacity(0.18))
        }
    }
}
