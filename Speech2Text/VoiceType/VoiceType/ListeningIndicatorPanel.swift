import AppKit
import SwiftUI

class ListeningIndicatorPanel: NSPanel {

    private var hostingView: NSHostingView<AnyView>?
    private var visualEffect: NSVisualEffectView!

    // Observable state bridged from AppController
    private var state: ListeningState = .hidden
    private var amplitude: Float = 0
    private var animateWaveform: Bool = true

    init() {
        let width: CGFloat = 220
        let height: CGFloat = 52
        super.init(
            contentRect: NSRect(x: 0, y: 0, width: width, height: height),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )

        level = .floating
        isOpaque = false
        backgroundColor = .clear
        ignoresMouseEvents = true
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        animationBehavior = .none

        // Blur background
        visualEffect = NSVisualEffectView(frame: NSRect(x: 0, y: 0, width: width, height: height))
        visualEffect.material = .hudWindow
        visualEffect.blendingMode = .behindWindow
        visualEffect.state = .active
        visualEffect.wantsLayer = true
        visualEffect.layer?.cornerRadius = 26
        visualEffect.layer?.masksToBounds = true
        contentView = visualEffect

        updateView()
    }

    private func updateView() {
        let view = ListeningIndicatorView(
            state: state,
            amplitude: amplitude,
            animateWaveform: animateWaveform
        )
        if let existing = hostingView {
            existing.rootView = AnyView(view)
        } else {
            let hv = NSHostingView(rootView: AnyView(view))
            hv.frame = visualEffect.bounds
            hv.autoresizingMask = [.width, .height]
            visualEffect.addSubview(hv)
            hostingView = hv
        }
    }

    func show(animate: Bool = true) {
        guard let screen = NSScreen.main else { return }
        let x = (screen.frame.width - frame.width) / 2
        let y = screen.frame.minY + 32
        setFrameOrigin(NSPoint(x: x, y: y))

        if animate {
            alphaValue = 0
            orderFront(nil)
            NSAnimationContext.runAnimationGroup { ctx in
                ctx.duration = 0.28
                ctx.timingFunction = CAMediaTimingFunction(name: .easeOut)
                animator().alphaValue = 1
            }
        } else {
            alphaValue = 1
            orderFront(nil)
        }
    }

    func hide() {
        NSAnimationContext.runAnimationGroup { ctx in
            ctx.duration = 0.22
            ctx.timingFunction = CAMediaTimingFunction(name: .easeIn)
            animator().alphaValue = 0
        } completionHandler: {
            self.orderOut(nil)
        }
    }

    func update(state: ListeningState, amplitude: Float = 0, animateWaveform: Bool = true) {
        self.state = state
        self.amplitude = amplitude
        self.animateWaveform = animateWaveform
        updateView()
    }
}
