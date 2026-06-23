import Foundation
import ApplicationServices
import CoreGraphics

class TextInjector {
    static let shared = TextInjector()
    private init() {}

    func inject(_ text: String) {
        guard !text.isEmpty else { return }
        if !injectViaAccessibility(text) {
            injectViaKeyboard(text)
        }
    }

    // MARK: - Primary: AXUIElement

    private func injectViaAccessibility(_ text: String) -> Bool {
        let systemElement = AXUIElementCreateSystemWide()
        var focusedElement: CFTypeRef?
        let result = AXUIElementCopyAttributeValue(systemElement, kAXFocusedUIElementAttribute as CFString, &focusedElement)
        guard result == .success, let element = focusedElement else { return false }

        let axElement = element as! AXUIElement

        // Try appending to existing value
        var currentValue: CFTypeRef?
        AXUIElementCopyAttributeValue(axElement, kAXValueAttribute as CFString, &currentValue)
        let current = (currentValue as? String) ?? ""

        // Try selected text range to insert at cursor
        var selectedRangeValue: CFTypeRef?
        if AXUIElementCopyAttributeValue(axElement, kAXSelectedTextRangeAttribute as CFString, &selectedRangeValue) == .success,
           let rangeValue = selectedRangeValue {
            var cfRange = CFRange()
            if AXValueGetValue(rangeValue as! AXValue, .cfRange, &cfRange) {
                var insertionRange = CFRange(location: cfRange.location, length: 0)
                if let axRange = AXValueCreate(.cfRange, &insertionRange) {
                    // Set selected text (replaces selection or inserts at cursor)
                    let setResult = AXUIElementSetAttributeValue(axElement, kAXSelectedTextAttribute as CFString, text as CFString)
                    if setResult == .success { return true }
                }
            }
        }

        // Fallback: set full value
        let newValue = current + text
        let setResult = AXUIElementSetAttributeValue(axElement, kAXValueAttribute as CFString, newValue as CFString)
        return setResult == .success
    }

    // MARK: - Fallback: CGEvent keyboard simulation

    private func injectViaKeyboard(_ text: String) {
        let source = CGEventSource(stateID: .hidSystemState)
        for scalar in text.unicodeScalars {
            let char = UniChar(scalar.value & 0xFFFF)
            var mutableChar = char
            if let down = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: true) {
                down.keyboardSetUnicodeString(stringLength: 1, unicodeString: &mutableChar)
                down.post(tap: .cghidEventTap)
            }
            if let up = CGEvent(keyboardEventSource: source, virtualKey: 0, keyDown: false) {
                up.keyboardSetUnicodeString(stringLength: 1, unicodeString: &mutableChar)
                up.post(tap: .cghidEventTap)
            }
        }
    }
}
