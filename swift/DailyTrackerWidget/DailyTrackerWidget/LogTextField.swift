import AppKit
import SwiftUI

/// NSTextField wrapper that explicitly makes its window key when editing starts.
/// Needed because .nonactivatingPanel panels don't become key on click.
struct LogTextField: NSViewRepresentable {
    @Binding var text: String
    var placeholder: String = "Log today…"
    var onSubmit: () -> Void

    func makeNSView(context: Context) -> NSTextField {
        let tf = PaddedTextField()
        tf.placeholderString = placeholder
        tf.isBezeled = false
        tf.drawsBackground = false
        tf.focusRingType = .none
        tf.font = NSFont.systemFont(ofSize: 12)
        tf.textColor = NSColor.white.withAlphaComponent(0.88)
        tf.delegate = context.coordinator
        return tf
    }

    func updateNSView(_ nsView: NSTextField, context: Context) {
        if nsView.stringValue != text {
            nsView.stringValue = text
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator(parent: self) }

    // MARK: - Coordinator

    class Coordinator: NSObject, NSTextFieldDelegate {
        var parent: LogTextField

        init(parent: LogTextField) { self.parent = parent }

        func controlTextDidBeginEditing(_ obj: Notification) {
            guard let tf = obj.object as? NSTextField,
                  let window = tf.window else { return }
            // Make the non-activating panel key so keyboard events work
            NSApp.activate(ignoringOtherApps: true)
            window.makeKeyAndOrderFront(nil)
        }

        func controlTextDidChange(_ obj: Notification) {
            if let tf = obj.object as? NSTextField {
                parent.text = tf.stringValue
            }
        }

        func control(_ control: NSControl, textView: NSTextView,
                     doCommandBy selector: Selector) -> Bool {
            if selector == #selector(NSResponder.insertNewline(_:)) {
                parent.onSubmit()
                return true
            }
            return false
        }
    }
}

private class PaddedTextField: NSTextField {
    /// Accept the first click even when the window is not key.
    /// Without this, the first click on a .nonactivatingPanel just warms up
    /// the window; a second click would be needed to focus the field.
    override func acceptsFirstMouse(for event: NSEvent?) -> Bool { true }

    override func mouseDown(with event: NSEvent) {
        // Make the panel key so keyboard events reach this field
        NSApp.activate(ignoringOtherApps: true)
        window?.makeKeyAndOrderFront(nil)
        super.mouseDown(with: event)
    }

    override func becomeFirstResponder() -> Bool {
        let result = super.becomeFirstResponder()
        if result, let window = self.window {
            NSApp.activate(ignoringOtherApps: true)
            window.makeKeyAndOrderFront(nil)
        }
        return result
    }
}
