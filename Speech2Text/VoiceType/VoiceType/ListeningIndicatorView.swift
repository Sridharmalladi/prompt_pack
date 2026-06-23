import SwiftUI

enum ListeningState {
    case hidden, listening, processing
}

struct WaveformBars: View {
    let amplitude: Float
    let animate: Bool

    @State private var heights: [CGFloat] = [0.4, 0.6, 0.8, 0.5, 0.3]

    private let barCount = 5
    private let barWidth: CGFloat = 4
    private let maxHeight: CGFloat = 24
    private let color = Color(red: 1, green: 0.231, blue: 0.188) // #FF3B30

    var body: some View {
        HStack(spacing: 3) {
            ForEach(0..<barCount, id: \.self) { i in
                Capsule()
                    .fill(color)
                    .frame(width: barWidth, height: heights[i] * maxHeight)
                    .animation(
                        .spring(response: 0.3 + Double(i) * 0.05, dampingFraction: 0.5),
                        value: heights[i]
                    )
            }
        }
        .onChange(of: amplitude) { newAmp in
            guard animate else { return }
            for i in 0..<barCount {
                let jitter = CGFloat.random(in: 0.6...1.0)
                heights[i] = CGFloat(newAmp) * jitter + 0.15
            }
        }
        .onChange(of: animate) { on in
            if !on {
                withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
                    heights = [0.4, 0.6, 0.5, 0.7, 0.4]
                }
            }
        }
    }
}

struct ListeningIndicatorView: View {
    let state: ListeningState
    let amplitude: Float
    let animateWaveform: Bool

    var body: some View {
        HStack(spacing: 12) {
            WaveformBars(amplitude: amplitude, animate: state == .listening && animateWaveform)

            Text(state == .processing ? "Processing..." : "Listening...")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(state == .processing ? .secondary : Color.accentColor)
                .contentTransition(.identity)
                .animation(.spring(response: 0.25, dampingFraction: 0.75), value: state == .processing)
        }
        .padding(.horizontal, 20)
        .frame(width: 220, height: 52)
        .background(
            ZStack {
                // NSVisualEffectView blur is set in the NSPanel wrapper
                Color.black.opacity(0.01)
            }
        )
    }
}
