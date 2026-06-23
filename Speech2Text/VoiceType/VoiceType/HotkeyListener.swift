import Foundation
import CoreGraphics
import Carbon

class HotkeyListener {
    static let shared = HotkeyListener()

    var onKeyDown: (() -> Void)?
    var onKeyUp: (() -> Void)?

    private var eventTap: CFMachPort?
    private var runLoopSource: CFRunLoopSource?
    private var isRecording = false

    private init() {}

    func start() {
        let mask: CGEventMask = (1 << CGEventType.flagsChanged.rawValue)
        eventTap = CGEvent.tapCreate(
            tap: .cgSessionEventTap,
            place: .headInsertEventTap,
            options: .defaultTap,
            eventsOfInterest: mask,
            callback: { proxy, type, event, refcon -> Unmanaged<CGEvent>? in
                let listener = Unmanaged<HotkeyListener>.fromOpaque(refcon!).takeUnretainedValue()
                listener.handle(event: event)
                return Unmanaged.passRetained(event)
            },
            userInfo: Unmanaged.passUnretained(self).toOpaque()
        )

        guard let tap = eventTap else {
            print("HotkeyListener: failed to create event tap — check Accessibility permission")
            return
        }

        runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetMain(), runLoopSource, .commonModes)
        CGEvent.tapEnable(tap: tap, enable: true)
    }

    func stop() {
        if let tap = eventTap { CGEvent.tapEnable(tap: tap, enable: false) }
        if let src = runLoopSource { CFRunLoopRemoveSource(CFRunLoopGetMain(), src, .commonModes) }
        eventTap = nil
        runLoopSource = nil
    }

    private func handle(event: CGEvent) {
        let flags = event.flags
        let ctrl  = flags.contains(.maskControl)
        let shift = flags.contains(.maskShift)
        let hotkeyHeld = ctrl && shift

        // Ignore Command/Option/Fn to avoid false triggers
        let extras = flags.contains(.maskCommand) || flags.contains(.maskAlternate)
        if extras { return }

        if hotkeyHeld && !isRecording {
            isRecording = true
            DispatchQueue.main.async { self.onKeyDown?() }
        } else if !hotkeyHeld && isRecording {
            isRecording = false
            DispatchQueue.main.async { self.onKeyUp?() }
        }
    }
}
