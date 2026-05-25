import AppKit
import SwiftUI
import Carbon.HIToolbox
import Combine

class WidgetHostingView: NSHostingView<TrackerView> {
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var panel: NSPanel?
    var fetcher = DataFetcher()
    private var hotKeyRef: EventHotKeyRef?
    private var cancellables = Set<AnyCancellable>()
    private var statusItem: NSStatusItem?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)

        let hosting = WidgetHostingView(rootView: TrackerView(fetcher: fetcher))

        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 310, height: 340),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.isFloatingPanel = true
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .stationary, .fullScreenAuxiliary]
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.hasShadow = true
        panel.contentView = hosting

        if let screen = NSScreen.main {
            let sf = screen.visibleFrame
            let w: CGFloat = 310, h: CGFloat = 340
            panel.setFrameOrigin(NSPoint(x: sf.maxX - w - 20, y: sf.maxY - h - 20))
        }

        panel.orderFrontRegardless()
        self.panel = panel

        fetcher.start()
        registerHotKey()
        setupStatusItem()

        // Observe shouldHide from TrackerView button tap
        fetcher.$shouldHide
            .filter { $0 }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] _ in
                self?.panel?.orderOut(nil)
                self?.fetcher.shouldHide = false
            }
            .store(in: &cancellables)
    }

    // Re-show when user relaunches the app
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows: Bool) -> Bool {
        if !hasVisibleWindows { panel?.orderFrontRegardless() }
        return true
    }

    // MARK: - Menubar icon

    private func setupStatusItem() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let btn = statusItem?.button {
            btn.image = NSImage(systemSymbolName: "chart.bar.fill", accessibilityDescription: "Tracker")
            btn.image?.size = NSSize(width: 16, height: 16)
            btn.action = #selector(togglePanel)
            btn.target = self
        }
    }

    // MARK: - Global hotkey ⌥⌘T

    private func registerHotKey() {
        var spec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard),
                                 eventKind: UInt32(kEventHotKeyPressed))
        InstallEventHandler(
            GetApplicationEventTarget(),
            { (_, _, userData) -> OSStatus in
                guard let ptr = userData else { return noErr }
                let d = Unmanaged<AppDelegate>.fromOpaque(ptr).takeUnretainedValue()
                DispatchQueue.main.async { d.togglePanel() }
                return noErr
            },
            1, &spec,
            Unmanaged.passUnretained(self).toOpaque(),
            nil
        )
        var hotKeyID = EventHotKeyID()
        hotKeyID.signature = fourCC("DTRK")
        hotKeyID.id = 1
        RegisterEventHotKey(UInt32(kVK_ANSI_T), UInt32(optionKey | cmdKey),
                            hotKeyID, GetApplicationEventTarget(), 0, &hotKeyRef)
    }

    @objc func togglePanel() {
        guard let panel else { return }
        if panel.isVisible { panel.orderOut(nil) } else { panel.orderFrontRegardless() }
    }

    @objc func refreshNow() { fetcher.fetch() }
}

extension Notification.Name {
    static let hideTrackerWidget = Notification.Name("hideTrackerWidget")
}

private func fourCC(_ s: String) -> FourCharCode {
    s.utf8.prefix(4).reduce(0) { ($0 << 8) | FourCharCode($1) }
}
