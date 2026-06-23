import Foundation
import SwiftUI

class AppSettings: ObservableObject {
    @AppStorage("isEnabled") var isEnabled: Bool = true
    @AppStorage("showOverlay") var showOverlay: Bool = true
    @AppStorage("animateWaveform") var animateWaveform: Bool = true
    @AppStorage("playSoundOnActivate") var playSoundOnActivate: Bool = true
    @AppStorage("launchAtLogin") var launchAtLogin: Bool = false

    static let shared = AppSettings()
    private init() {}
}
