import Foundation

// MARK: - Top-level widget response

struct WidgetData: Decodable {
    let today: TodayData?
    let streak: StreakData?
    let week_totals: WeekTotals?
    let heatmap_weeks: [[HeatmapCell]]?
}

struct TodayData: Decodable {
    let date: String?
    let total_tasks: Int?
    let goals: GoalStats?
}

struct GoalStats: Decodable {
    let phd: GoalDetail?
    let nl_jobs: GoalDetail?
    let china_jobs: GoalDetail?

    func count(for key: GoalKey) -> Int {
        switch key {
        case .phd:       return phd?.tasks ?? 0
        case .nl_jobs:   return nl_jobs?.tasks ?? 0
        case .china_jobs: return china_jobs?.tasks ?? 0
        }
    }

    func summary(for key: GoalKey) -> String? {
        switch key {
        case .phd:       return phd?.summary
        case .nl_jobs:   return nl_jobs?.summary
        case .china_jobs: return china_jobs?.summary
        }
    }
}

struct GoalDetail: Decodable {
    let tasks: Int?
    let summary: String?
}

struct StreakData: Decodable {
    let current_days: Int?
    let longest_days: Int?
}

struct WeekTotals: Decodable {
    let phd: Int?
    let nl_jobs: Int?
    let china_jobs: Int?

    func count(for key: GoalKey) -> Int {
        switch key {
        case .phd:       return phd ?? 0
        case .nl_jobs:   return nl_jobs ?? 0
        case .china_jobs: return china_jobs ?? 0
        }
    }
}

struct HeatmapCell: Decodable {
    let phd: Int?
    let nl_jobs: Int?
    let china_jobs: Int?
    let future: Bool?

    var phdCount: Int    { phd ?? 0 }
    var nlCount: Int     { nl_jobs ?? 0 }
    var chinaCount: Int  { china_jobs ?? 0 }
    var total: Int       { phdCount + nlCount + chinaCount }
    var isFuture: Bool   { future ?? false }
}

// MARK: - Goal metadata

enum GoalKey: String, CaseIterable {
    case phd, nl_jobs, china_jobs

    var label: String {
        switch self {
        case .phd:       return "PhD"
        case .nl_jobs:   return "NL Jobs"
        case .china_jobs: return "China"
        }
    }
}
