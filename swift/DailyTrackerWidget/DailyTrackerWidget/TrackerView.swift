import SwiftUI
import AppKit

struct TrackerView: View {
    @ObservedObject var fetcher: DataFetcher
    var onHide: (() -> Void)? = nil

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 14)
                .fill(Color(red: 0.055, green: 0.063, blue: 0.09).opacity(0.96))
                .overlay(
                    RoundedRectangle(cornerRadius: 14)
                        .stroke(Color.white.opacity(0.09), lineWidth: 1)
                )

            if fetcher.isOffline || fetcher.widgetData == nil {
                offlineView
            } else {
                mainView(fetcher.widgetData!)
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 14))
        .frame(width: 310)
    }

    // MARK: - Offline

    private var offlineView: some View {
        VStack(spacing: 6) {
            Text("⚠️ Tracker offline")
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.orange)
            Button("Refresh") { fetcher.fetch() }
                .buttonStyle(PlainButtonStyle())
                .font(.system(size: 11))
                .foregroundColor(.white.opacity(0.45))
        }
        .padding(16)
    }

    // MARK: - Main

    private func mainView(_ data: WidgetData) -> some View {
        VStack(alignment: .leading, spacing: 8) {

            // ── Header ──────────────────────────────────────────
            HStack(spacing: 0) {
                Text(dateString())
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white.opacity(0.85))
                Spacer()
                if let days = data.streak?.current_days, days > 0 {
                    Text("🔥 \(days)d")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundColor(Color(hex: "#fb923c"))
                }
                // Hide button — ⌥⌘T to show again
                Text("Hide")
                    .font(.system(size: 10, weight: .medium))
                    .foregroundColor(.white.opacity(0.6))
                    .padding(.horizontal, 7)
                    .padding(.vertical, 3)
                    .background(Color.white.opacity(0.12))
                    .cornerRadius(4)
                    .onTapGesture { fetcher.shouldHide = true }
                    .padding(.leading, 8)
            }

            // ── Heatmap ─────────────────────────────────────────
            if let weeks = data.heatmap_weeks, !weeks.isEmpty {
                HeatmapView(weeks: weeks)
                LegendDots()
            }

            thinDivider

            // ── Goal rows ───────────────────────────────────────
            VStack(spacing: 4) {
                goalRow(.phd,       data)
                goalRow(.nl_jobs,   data)
                goalRow(.china_jobs, data)
            }

            thinDivider

            // ── Log input ────────────────────────────────────────
            logInputView
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
    }

    // MARK: - Divider

    private var thinDivider: some View {
        Rectangle()
            .fill(Color.white.opacity(0.07))
            .frame(height: 1)
    }

    // MARK: - Goal rows

    private let dotHex: [GoalKey: String] = [
        .phd:        "#60a5fa",
        .nl_jobs:    "#fb923c",
        .china_jobs: "#f87171",
    ]

    private func goalRow(_ key: GoalKey, _ data: WidgetData) -> some View {
        let today   = data.today?.goals?.count(for: key) ?? 0
        let week    = data.week_totals?.count(for: key) ?? 0
        let summary = today > 0 ? data.today?.goals?.summary(for: key) : nil

        return VStack(alignment: .leading, spacing: 2) {
            HStack(spacing: 6) {
                Circle()
                    .fill(Color(hex: dotHex[key]!))
                    .frame(width: 7, height: 7)
                Text(key.label)
                    .font(.system(size: 12))
                    .foregroundColor(.white.opacity(0.78))
                Spacer()
                if today > 0 {
                    Text("+\(today) today")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(Color(hex: dotHex[key]!).opacity(0.9))
                } else {
                    Text("–")
                        .font(.system(size: 11))
                        .foregroundColor(.white.opacity(0.25))
                }
                Text(week > 0 ? "\(week) wk" : "")
                    .font(.system(size: 11))
                    .foregroundColor(.white.opacity(0.3))
                    .frame(minWidth: 36, alignment: .trailing)
            }
            if let summary, !summary.isEmpty {
                Text(summary)
                    .font(.system(size: 10))
                    .foregroundColor(.white.opacity(0.42))
                    .lineLimit(1)
                    .padding(.leading, 13)
            }
        }
    }

    // MARK: - Log input

    private var logInputView: some View {
        Group {
            if fetcher.logStatus.isEmpty {
                Button(action: showLogDialog) {
                    HStack(spacing: 6) {
                        Image(systemName: "square.and.pencil")
                            .font(.system(size: 11))
                        Text("Log today…")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(.white.opacity(0.45))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 6)
                    .background(Color.white.opacity(0.05))
                    .cornerRadius(6)
                    .overlay(RoundedRectangle(cornerRadius: 6)
                        .stroke(Color.white.opacity(0.1), lineWidth: 1))
                }
                .buttonStyle(PlainButtonStyle())
            } else {
                let isOk = fetcher.logStatus.hasPrefix("✓")
                VStack(spacing: 2) {
                    Text(fetcher.logStatus)
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(isOk ? .green : .red)
                    if !isOk {
                        Text("Check ANTHROPIC_API_KEY in .env")
                            .font(.system(size: 9))
                            .foregroundColor(.white.opacity(0.35))
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 6)
                .background(Color.white.opacity(0.05))
                .cornerRadius(6)
            }
        }
    }

    // MARK: - Helpers

    /// Shows a native NSAlert with an embedded text field.
    /// NSAlert always gets proper keyboard focus, bypassing the non-activating panel issue.
    private func showLogDialog() {
        let alert = NSAlert()
        alert.messageText = "Log Today"
        alert.informativeText = "What did you work on? e.g. \"phd - read papers, nl - applied to 3 jobs\""
        alert.alertStyle = .informational
        alert.addButton(withTitle: "Log")
        alert.addButton(withTitle: "Cancel")

        let tf = NSTextField(frame: NSRect(x: 0, y: 0, width: 320, height: 24))
        tf.placeholderString = "phd - …,  nl - …,  china - …"
        alert.accessoryView = tf
        alert.window.initialFirstResponder = tf

        NSApp.activate(ignoringOtherApps: true)
        if alert.runModal() == .alertFirstButtonReturn {
            let text = tf.stringValue.trimmingCharacters(in: .whitespaces)
            if !text.isEmpty {
                fetcher.submitLog(text) { _ in }
            }
        }
    }

    private func dateString() -> String {
        let f = DateFormatter()
        f.dateFormat = "EEE d MMM"
        return f.string(from: Date())
    }
}
