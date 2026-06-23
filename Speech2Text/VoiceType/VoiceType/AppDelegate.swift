import AppKit
import SwiftUI
import ServiceManagement
import AVFoundation

@main
class AppDelegate: NSObject, NSApplicationDelegate {

    private var statusItem: NSStatusItem!
    private var dashboardController: DashboardWindowController?
    private var listeningPanel: ListeningIndicatorPanel?

    private let recorder = AudioRecorder.shared
    private let hotkey   = HotkeyListener.shared
    private let injector = TextInjector.shared
    private let permissions = PermissionsManager.shared
    private let settings = AppSettings.shared
    private let appState = AppController.shared

    func applicationDidFinishLaunching(_ notification: Notification) {
        // No dock icon
        NSApp.setActivationPolicy(.accessory)

        permissions.checkAll()
        setupMenuBar()
        setupHotkey()
        setupLaunchAtLoginObserver()

        // Create panel eagerly (off-screen)
        listeningPanel = ListeningIndicatorPanel()
    }

    // MARK: - Menu Bar

    private func setupMenuBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = statusItem.button {
            button.image = NSImage(systemSymbolName: "waveform.circle", accessibilityDescription: "VoiceType")
            button.action = #selector(statusBarButtonClicked)
            button.target = self
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }
        rebuildMenu()
    }

    private func rebuildMenu() {
        let menu = NSMenu()

        let statusTitle: String
        switch appState.recordingState {
        case .idle:        statusTitle = "Idle"
        case .listening:   statusTitle = "Listening..."
        case .processing:  statusTitle = "Processing..."
        }

        let statusItem = NSMenuItem(title: statusTitle, action: nil, keyEquivalent: "")
        statusItem.isEnabled = false
        menu.addItem(statusItem)

        menu.addItem(.separator())

        let dashboard = NSMenuItem(title: "Open Dashboard", action: #selector(openDashboard), keyEquivalent: "")
        dashboard.target = self
        menu.addItem(dashboard)

        menu.addItem(.separator())

        let quit = NSMenuItem(title: "Quit VoiceType", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        menu.addItem(quit)

        self.statusItem.menu = menu
    }

    @objc private func statusBarButtonClicked() {
        rebuildMenu()
        statusItem.button?.performClick(nil)
    }

    @objc func openDashboard() {
        if dashboardController == nil {
            dashboardController = DashboardWindowController()
        }
        dashboardController?.show()
    }

    // MARK: - Hotkey

    private func setupHotkey() {
        hotkey.onKeyDown = { [weak self] in self?.beginRecording() }
        hotkey.onKeyUp   = { [weak self] in self?.endRecording() }
        if permissions.accessibilityGranted {
            hotkey.start()
        }
        // Re-attempt if accessibility gets granted later
        NotificationCenter.default.addObserver(forName: NSApplication.didBecomeActiveNotification, object: nil, queue: .main) { [weak self] _ in
            guard let self = self else { return }
            self.permissions.checkAll()
            if self.permissions.accessibilityGranted {
                self.hotkey.start()
            }
        }
    }

    private func beginRecording() {
        guard settings.isEnabled, permissions.allGranted else { return }
        appState.recordingState = .listening
        rebuildMenu()

        if settings.playSoundOnActivate {
            NSSound(named: "Pop")?.play()
        }

        recorder.start()

        if settings.showOverlay {
            listeningPanel?.update(state: .listening, animateWaveform: settings.animateWaveform)
            listeningPanel?.show()
        }

        // Forward amplitude to panel
        startAmplitudeTimer()
    }

    private var amplitudeTimer: Timer?

    private func startAmplitudeTimer() {
        amplitudeTimer?.invalidate()
        amplitudeTimer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            self.listeningPanel?.update(
                state: .listening,
                amplitude: self.recorder.amplitude,
                animateWaveform: self.settings.animateWaveform
            )
        }
    }

    private func endRecording() {
        amplitudeTimer?.invalidate()
        amplitudeTimer = nil

        guard let audioURL = recorder.stop() else {
            resetState()
            return
        }

        appState.recordingState = .processing
        rebuildMenu()

        if settings.showOverlay {
            listeningPanel?.update(state: .processing)
        }

        WhisperTranscriber.shared.transcribe(audioURL: audioURL) { [weak self] text in
            guard let self = self else { return }
            if let text = text, !text.isEmpty {
                self.injector.inject(text)
            }
            self.resetState()
            try? FileManager.default.removeItem(at: audioURL)
        }
    }

    private func resetState() {
        appState.recordingState = .idle
        rebuildMenu()
        listeningPanel?.hide()
    }

    // MARK: - Launch at Login

    private func setupLaunchAtLoginObserver() {
        NotificationCenter.default.addObserver(forName: .launchAtLoginChanged, object: nil, queue: .main) { note in
            guard let enabled = note.object as? Bool else { return }
            if #available(macOS 13.0, *) {
                do {
                    if enabled {
                        try SMAppService.mainApp.register()
                    } else {
                        try SMAppService.mainApp.unregister()
                    }
                } catch {
                    print("LaunchAtLogin error: \(error)")
                }
            }
        }
    }
}
