You are a senior macOS engineer. Build a minimal, production-quality background app that lets users dictate text into any focused input field using a global push-to-talk hotkey and local Whisper transcription.

Goal
A lightweight background macOS app that:

Runs silently in the background (menu bar only — no Dock icon)
Activates on a reliable global hotkey
Records speech while the hotkey is held
Transcribes locally using faster-whisper (no internet, no API)
Injects the transcribed text at the cursor's current position


Hotkey
Use Control + Shift as the global push-to-talk trigger.

Why not Fn + Shift: macOS does not reliably expose the Fn key to third-party apps. Control + Shift is the most reliable and least intrusive fallback.

Behavior:

Key down → start recording
Key up → stop recording, begin transcription, inject result


Functional Requirements
1. Menu Bar App

No Dock presence (LSUIElement = YES in Info.plist)
Menu bar icon with a simple dropdown containing:

"Open Dashboard" — opens the main control panel window
Status label: Idle / Listening... / Processing...
Quit option




2. Dashboard Window
The dashboard is the app's primary control panel. It opens as a native NSWindow with a modern, minimal SwiftUI layout. It should feel like a first-party macOS settings panel.
Window spec:

Size: 480 × 560pt, non-resizable
Title bar: hidden (titlebarAppearsTransparent = true, titleVisibility = .hidden)
Background: system material (NSVisualEffectView, .sidebar or .menu blending mode)
Corner radius: system default (NSWindow rounded)
Centered on screen on first open, remembers position on reopen

Top bar (inside window, custom):

Left side: back/close button — a circular × button (22pt diameter, SF Symbols: xmark.circle.fill, secondary label color) that closes the window. Animate it with a subtle scale-down spring on press (scaleEffect(0.88) with .spring(response: 0.25, dampingFraction: 0.6)).
Center: app name label — "VoiceType" in 17pt medium weight
Right side: app version string — "v1.0" in 12pt secondary color

Dashboard sections (top to bottom):

Section 1 — Status Card
A rounded card (cornerRadius: 14, background: Color(.windowBackgroundColor).opacity(0.6)) showing:

Large animated mic icon (SF Symbols: waveform.circle.fill, 48pt) — pulses gently at 1.2× scale on a 1.4s repeating spring when Listening, static when Idle
Status text below: "Idle" / "Listening..." / "Processing..." — animates with .contentTransition(.numericText()) or a custom crossfade
Subtle accent ring around the icon that fills like a progress indicator while recording (indeterminate spinner style, accent color)


Section 2 — Controls
A labeled section titled "Controls" in 12pt uppercase secondary text.
Grouped rounded list style (List with .insetGrouped equivalent via custom VStack in a rounded container), containing these toggle rows:
LabelSublabelToggle keyEnable Voice TypingActivates the global hotkeyisEnabledShow Listening IndicatorOverlay animation at bottom of screenshowOverlayAnimate Waveform BarsLive amplitude visualizationanimateWaveformPlay Sound on ActivationSubtle system sound on hotkey pressplaySoundOnActivateLaunch at LoginStart automatically on system bootlaunchAtLogin
Each row:

Left: label stack (title 14pt primary + sublabel 12pt secondary)
Right: Toggle using .toggleStyle(.switch)
Separator between rows: 0.5pt, Color(.separatorColor)
Tap the row anywhere to flip the toggle (make the whole row tappable)
Animate toggle state change with a 0.2s spring


Section 3 — Model
A labeled section titled "Whisper Model".
Single info row showing:

Left: "Model" label + "small · offline" sublabel
Right: green "Ready" badge (pill shape, #30D158 background at 15% opacity, #30D158 text) if model file exists, or orange "Not found" badge if missing
Below the row: a small "Download model" link button (12pt, accent color, SF Symbols: arrow.down.circle inline icon) — tapping it opens the direct model download URL in the default browser:

Model download URL:
https://huggingface.co/guillaumekln/faster-whisper-small/resolve/main/model.bin

Setup note for the developer: After downloading, place model.bin in:
~/Library/Application Support/VoiceType/models/small/
The app checks this path at launch and on each dashboard open to set the badge state.


Section 4 — Permissions
A labeled section titled "Permissions".
Two rows:
PermissionIconBadge logicMicrophonemic.fillGreen "Granted" / Red "Required"AccessibilityaccessibilityGreen "Granted" / Red "Required"

If either shows "Required": a button appears below — "Open System Settings" — that deep-links to x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility
Re-check permissions every time the dashboard window becomes active (onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)))


3. Push-to-Talk Flow
Hold hotkey → [Recording] → Release hotkey → [Transcribing] → [Text injected at cursor]

While recording: listening indicator appears (if showOverlay is on)
If isEnabled toggle is off: hotkey does nothing


4. On-Screen Listening Indicator
A small, non-intrusive overlay at the bottom center of the screen. Governed by the showOverlay dashboard toggle.
Window behavior:

NSPanel subclass, NSWindowLevel set to .floating
ignoresMouseEvents = true, canBecomeKey = false — never steals focus
Appears on key down, transitions to Processing... on key up, dismisses on inject

Visual spec:

Pill-shaped: 220 × 52pt, cornerRadius: 26pt
32pt from the bottom edge of the main screen, horizontally centered
Background: NSVisualEffectView with .dark material and slight blur
Left: animated waveform (4–5 vertical bars, governed by animateWaveform toggle)
Right: state label — "Listening..." in accent color / "Processing..." in secondary color

Animations (modern, spring-based throughout):
All animations must use SwiftUI's .animation(.spring(response:dampingFraction:)) or Core Animation with CASpringAnimation. No linear or easeInOut curves anywhere in the UI — every interactive element should feel physical and alive.

Appear: opacity 0→1 + scaleEffect 0.82→1.0, spring response: 0.3, dampingFraction: 0.65, duration ≈ 0.28s
Dismiss: opacity 1→0 + scaleEffect 1.0→0.9, spring response: 0.25, dampingFraction: 0.75
Waveform bars: Each bar independently animated with CABasicAnimation on transform.scale.y, driven by mic amplitude from AVAudioEngine tap. When animateWaveform is off, bars are static at mid-height. Bar colors: vivid accent (#FF3B30 or #30D158), bars have cornerRadius on their capsule shape.
State label transition: .contentTransition(.identity) with a crossfade when switching between Listening and Processing

State machine:
Key down  →  spring in  →  [Listening... + dancing bars]
Key up    →  bars freeze →  [Processing... + subtle spinner]  →  spring out after inject

5. Global Animation Quality Standard
Every animated element in the app must follow this standard:

No linear or easeInOut timing — use spring animations exclusively for all UI state changes
Toggle switches: state change animates with withAnimation(.spring(response: 0.3, dampingFraction: 0.7))
Badge state changes: crossfade with .transition(.opacity.combined(with: .scale(0.9))) on a spring
Status card mic icon: scaleEffect pulsing on a repeating .spring(response: 0.6, dampingFraction: 0.4) while listening
Dashboard open/close: window appears with a 0.25s spring scale from 0.95→1.0 (use NSWindow animationBehavior = .documentWindow)
Close button: scale spring on press as described above
Rows in controls list: when a toggle flips, the sublabel text updates with a crossfade spring
All durations should feel snappy — aim for 0.2–0.35s for most transitions, nothing longer than 0.5s


6. Speech-to-Text

Engine: faster-whisper
Model: small
Language: auto-detect
Fully offline
Apple Silicon optimized: compute_type="int8", device="cpu"

7. Text Injection

Primary: macOS Accessibility API (AXUIElement) — set kAXValueAttribute directly
Fallback: CGEvent keyboard simulation
No clipboard use


Permissions

Check Microphone and Accessibility on every launch and on every dashboard activation
If missing: disable isEnabled toggle automatically, show red badge, surface the "Open System Settings" button


Architecture
ModuleResponsibilityHotkeyListenerGlobal CGEvent tap for Control + ShiftAudioRecorderAVAudioEngine mic capture, amplitude publisher for waveformWhisperTranscriberPython subprocess → faster-whisper → stdout transcriptionTextInjectorAXUIElement injection with CGEvent fallbackPermissionsManagerMic + Accessibility check, publishes stateMenuBarControllerMenu bar icon, dropdown, "Open Dashboard" actionDashboardWindowSwiftUI dashboard window controllerDashboardViewFull SwiftUI view — status card, all sections, all togglesListeningIndicatorFloating NSPanel overlay with waveform animationAppSettings@AppStorage-backed settings model for all toggles

Technical Stack

Swift + SwiftUI (all UI)
AVAudioEngine for mic capture and amplitude metering
CGEvent tap for hotkey
NSPanel for overlay, NSWindow for dashboard
Python subprocess for faster-whisper bridge
AXUIElement + CGEvent for text injection
ServiceManagement framework for launch-at-login
@AppStorage for all toggle persistence


Deliverables

Full working source code — all modules above, complete and buildable
faster-whisper setup guide — pip install faster-whisper, Python path configuration for subprocess
Model download — direct URL and exact path to place the file
Permissions guide — step-by-step for Microphone and Accessibility in System Settings
Build & run instructions — Xcode project setup, entitlements, scheme config
Packaging guide — export as .app, code signing notes, launch-at-login behavior


Hard Constraints

No OpenAI API, no cloud, no telemetry
No clipboard injection
No Dock icon ever
Overlay never steals focus or blocks clicks
Idle CPU usage must be near zero
No linear animation curves anywhere — springs only
Dashboard must not break or freeze if model file is missing
App must launch and be usable even if Whisper is not yet configured (graceful degraded state with clear instructions shown in dashboard)


Design Philosophy

Invisible when idle. Instant when triggered. Feels like it shipped with macOS.

Every detail — the spring on the close button, the waveform reacting to your voice, the pill fading in at the bottom of the screen — should feel intentional and native. Prioritize reliability first, then animation quality, then visual polish. If something can fail, it fails gracefully with a clear signal in the dashboard. The foreground app is never frozen, interrupted, or affected under any circumstance.