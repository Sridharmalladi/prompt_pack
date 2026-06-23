import SwiftUI

// MARK: - App-wide state observable by Dashboard

class AppController: ObservableObject {
    @Published var recordingState: RecordingState = .idle

    enum RecordingState { case idle, listening, processing }

    static let shared = AppController()
    private init() {}
}

// MARK: - Dashboard View

struct DashboardView: View {
    @ObservedObject private var settings = AppSettings.shared
    @ObservedObject private var permissions = PermissionsManager.shared
    @ObservedObject private var appState = AppController.shared

    var onClose: () -> Void

    // Mic pulse animation
    @State private var micPulse: CGFloat = 1.0

    var body: some View {
        VStack(spacing: 0) {
            topBar
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 16) {
                    statusCard
                    controlsSection
                    modelSection
                    permissionsSection
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 24)
            }
        }
        .frame(width: 480, height: 560)
        .background(Color.clear)
        .onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in
            permissions.checkAll()
        }
    }

    // MARK: Top Bar

    private var topBar: some View {
        ZStack {
            // Close button
            HStack {
                Button(action: onClose) {
                    Image(systemName: "xmark.circle.fill")
                        .symbolRenderingMode(.hierarchical)
                        .font(.system(size: 22))
                        .foregroundStyle(.secondary)
                }
                .buttonStyle(SpringButtonStyle())
                .padding(.leading, 16)
                Spacer()
            }

            // Center title
            Text("VoiceType")
                .font(.system(size: 17, weight: .medium))

            // Version
            HStack {
                Spacer()
                Text("v1.0")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
                    .padding(.trailing, 16)
            }
        }
        .frame(height: 52)
    }

    // MARK: Status Card

    private var statusCard: some View {
        VStack(spacing: 10) {
            ZStack {
                // Accent ring
                Circle()
                    .stroke(Color.accentColor.opacity(appState.recordingState == .listening ? 0.35 : 0.0), lineWidth: 3)
                    .frame(width: 64, height: 64)
                    .animation(.spring(response: 0.4, dampingFraction: 0.6), value: appState.recordingState == .listening)

                Image(systemName: "waveform.circle.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(micColor)
                    .scaleEffect(micPulse)
                    .animation(.spring(response: 0.6, dampingFraction: 0.4).repeatForever(autoreverses: true),
                               value: micPulse)
            }
            .onAppear { updateMicPulse() }
            .onChange(of: appState.recordingState) { _ in updateMicPulse() }

            Text(statusText)
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(statusColor)
                .contentTransition(.opacity)
                .animation(.spring(response: 0.3, dampingFraction: 0.7), value: appState.recordingState)
        }
        .padding(.vertical, 24)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 14)
                .fill(Color(NSColor.windowBackgroundColor).opacity(0.6))
        )
    }

    private var statusText: String {
        switch appState.recordingState {
        case .idle: return "Idle"
        case .listening: return "Listening..."
        case .processing: return "Processing..."
        }
    }

    private var statusColor: Color {
        switch appState.recordingState {
        case .idle: return .secondary
        case .listening: return .accentColor
        case .processing: return .orange
        }
    }

    private var micColor: Color {
        switch appState.recordingState {
        case .idle: return .secondary
        case .listening: return .accentColor
        case .processing: return .orange
        }
    }

    private func updateMicPulse() {
        micPulse = appState.recordingState == .listening ? 1.2 : 1.0
    }

    // MARK: Controls Section

    private var controlsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("Controls")

            VStack(spacing: 0) {
                ToggleRow(
                    title: "Enable Voice Typing",
                    subtitle: "Activates the global hotkey",
                    isOn: $settings.isEnabled
                )
                divider
                ToggleRow(
                    title: "Show Listening Indicator",
                    subtitle: "Overlay animation at bottom of screen",
                    isOn: $settings.showOverlay
                )
                divider
                ToggleRow(
                    title: "Animate Waveform Bars",
                    subtitle: "Live amplitude visualization",
                    isOn: $settings.animateWaveform
                )
                divider
                ToggleRow(
                    title: "Play Sound on Activation",
                    subtitle: "Subtle system sound on hotkey press",
                    isOn: $settings.playSoundOnActivate
                )
                divider
                ToggleRow(
                    title: "Launch at Login",
                    subtitle: "Start automatically on system boot",
                    isOn: Binding(
                        get: { settings.launchAtLogin },
                        set: { val in
                            settings.launchAtLogin = val
                            LaunchAtLogin.setEnabled(val)
                        }
                    )
                )
            }
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(NSColor.windowBackgroundColor).opacity(0.6))
            )
        }
    }

    // MARK: Model Section

    private var modelSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("Whisper Model")

            VStack(spacing: 0) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Model")
                            .font(.system(size: 14))
                        Text("small · offline")
                            .font(.system(size: 12))
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    modelBadge
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 12)

                Divider().padding(.horizontal, 14)

                HStack {
                    Button {
                        if let url = URL(string: "https://huggingface.co/guillaumekln/faster-whisper-small/resolve/main/model.bin") {
                            NSWorkspace.shared.open(url)
                        }
                    } label: {
                        Label("Download model", systemImage: "arrow.down.circle")
                            .font(.system(size: 12))
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.accentColor)
                    Spacer()
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
            }
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(NSColor.windowBackgroundColor).opacity(0.6))
            )
        }
    }

    private var modelBadge: some View {
        let ready = WhisperTranscriber.shared.isModelReady
        return Text(ready ? "Ready" : "Not found")
            .font(.system(size: 12, weight: .medium))
            .foregroundColor(ready ? Color(hex: "#30D158") : .orange)
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(
                Capsule().fill((ready ? Color(hex: "#30D158") : Color.orange).opacity(0.15))
            )
            .transition(.opacity.combined(with: .scale(scale: 0.9)))
            .animation(.spring(response: 0.3, dampingFraction: 0.7), value: ready)
    }

    // MARK: Permissions Section

    private var permissionsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("Permissions")

            VStack(spacing: 0) {
                PermissionRow(title: "Microphone", icon: "mic.fill", granted: permissions.microphoneGranted)
                divider
                PermissionRow(title: "Accessibility", icon: "accessibility", granted: permissions.accessibilityGranted)

                if !permissions.allGranted {
                    Divider().padding(.horizontal, 14)
                    Button("Open System Settings") {
                        permissions.openSystemSettings()
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.accentColor)
                    .font(.system(size: 13))
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(NSColor.windowBackgroundColor).opacity(0.6))
            )
        }
    }

    // MARK: Helpers

    private var divider: some View {
        Rectangle()
            .fill(Color(NSColor.separatorColor))
            .frame(height: 0.5)
            .padding(.horizontal, 14)
    }

    private func sectionHeader(_ title: String) -> some View {
        Text(title.uppercased())
            .font(.system(size: 12, weight: .medium))
            .foregroundStyle(.secondary)
            .padding(.leading, 4)
    }
}

// MARK: - Toggle Row

struct ToggleRow: View {
    let title: String
    let subtitle: String
    @Binding var isOn: Bool

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.system(size: 14))
                Text(subtitle).font(.system(size: 12)).foregroundStyle(.secondary)
            }
            Spacer()
            Toggle("", isOn: $isOn)
                .toggleStyle(.switch)
                .labelsHidden()
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 11)
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                isOn.toggle()
            }
        }
    }
}

// MARK: - Permission Row

struct PermissionRow: View {
    let title: String
    let icon: String
    let granted: Bool

    var body: some View {
        HStack {
            Label(title, systemImage: icon)
                .font(.system(size: 14))
            Spacer()
            Text(granted ? "Granted" : "Required")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(granted ? Color(hex: "#30D158") : .red)
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(
                    Capsule().fill((granted ? Color(hex: "#30D158") : Color.red).opacity(0.15))
                )
                .transition(.opacity.combined(with: .scale(scale: 0.9)))
                .animation(.spring(response: 0.3, dampingFraction: 0.7), value: granted)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 11)
    }
}

// MARK: - Spring Button Style

struct SpringButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.88 : 1.0)
            .animation(.spring(response: 0.25, dampingFraction: 0.6), value: configuration.isPressed)
    }
}

// MARK: - Color hex init

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r = Double((int >> 16) & 0xFF) / 255
        let g = Double((int >> 8) & 0xFF) / 255
        let b = Double(int & 0xFF) / 255
        self.init(red: r, green: g, blue: b)
    }
}

// MARK: - Launch at login stub (ServiceManagement)

enum LaunchAtLogin {
    static func setEnabled(_ enabled: Bool) {
        // Requires SMAppService (macOS 13+) or SMLoginItemSetEnabled (older)
        // Wired in AppDelegate at runtime
        NotificationCenter.default.post(name: .launchAtLoginChanged, object: enabled)
    }
}

extension Notification.Name {
    static let launchAtLoginChanged = Notification.Name("launchAtLoginChanged")
}
