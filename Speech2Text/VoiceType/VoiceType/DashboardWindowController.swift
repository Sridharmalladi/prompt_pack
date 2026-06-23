import AppKit
import SwiftUI

class DashboardWindowController: NSWindowController {

    convenience init() {
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 480, height: 560),
            styleMask: [.titled, .closable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        window.titlebarAppearsTransparent = true
        window.titleVisibility = .hidden
        window.isMovableByWindowBackground = true
        window.animationBehavior = .documentWindow
        window.isReleasedWhenClosed = false

        // Frosted glass background
        let visualEffect = NSVisualEffectView()
        visualEffect.material = .sidebar
        visualEffect.blendingMode = .behindWindow
        visualEffect.state = .active
        window.contentView = visualEffect

        self.init(window: window)

        let dashView = DashboardView(onClose: { [weak self] in self?.close() })
        let hosting = NSHostingView(rootView: dashView)
        hosting.frame = visualEffect.bounds
        hosting.autoresizingMask = [.width, .height]
        visualEffect.addSubview(hosting)

        window.setContentSize(NSSize(width: 480, height: 560))
        window.minSize = NSSize(width: 480, height: 560)
        window.maxSize = NSSize(width: 480, height: 560)

        // Restore saved position or center
        if let savedOrigin = UserDefaults.standard.string(forKey: "dashboardOrigin"),
           let data = savedOrigin.data(using: .utf8),
           let dict = try? JSONDecoder().decode([String: CGFloat].self, from: data) {
            window.setFrameOrigin(NSPoint(x: dict["x"] ?? 0, y: dict["y"] ?? 0))
        } else {
            window.center()
        }

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(windowWillClose(_:)),
            name: NSWindow.willCloseNotification,
            object: window
        )
    }

    func show() {
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    @objc private func windowWillClose(_ notification: Notification) {
        guard let origin = window?.frame.origin,
              let data = try? JSONEncoder().encode(["x": origin.x, "y": origin.y]),
              let str = String(data: data, encoding: .utf8) else { return }
        UserDefaults.standard.set(str, forKey: "dashboardOrigin")
    }
}
