import AVFoundation
import Combine

class AudioRecorder: ObservableObject {
    @Published var amplitude: Float = 0.0

    private var engine = AVAudioEngine()
    private var file: AVAudioFile?
    private(set) var recordingURL: URL?

    static let shared = AudioRecorder()
    private init() {}

    func start() {
        let input = engine.inputNode
        let format = input.outputFormat(forBus: 0)

        let url = FileManager.default.temporaryDirectory.appendingPathComponent("voicetype_recording.wav")
        recordingURL = url

        do {
            file = try AVAudioFile(forWriting: url, settings: format.settings)
        } catch {
            print("AudioRecorder: failed to create file: \(error)")
            return
        }

        input.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
            guard let self = self else { return }
            try? self.file?.write(from: buffer)

            // Compute RMS amplitude for waveform
            guard let channelData = buffer.floatChannelData?[0] else { return }
            let frameCount = Int(buffer.frameLength)
            let rms = sqrt(channelData.prefix(frameCount).map { $0 * $0 }.reduce(0, +) / Float(frameCount))
            DispatchQueue.main.async { self.amplitude = min(rms * 10, 1.0) }
        }

        do {
            try engine.start()
        } catch {
            print("AudioRecorder: engine start failed: \(error)")
        }
    }

    func stop() -> URL? {
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        engine.reset()
        DispatchQueue.main.async { self.amplitude = 0 }
        let url = recordingURL
        file = nil
        recordingURL = nil
        return url
    }
}
