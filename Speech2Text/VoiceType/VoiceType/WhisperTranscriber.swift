import Foundation

class WhisperTranscriber {
    static let shared = WhisperTranscriber()
    private init() {}

    // Path to the faster-whisper Python runner script
    private var scriptPath: String {
        Bundle.main.path(forResource: "transcribe", ofType: "py") ?? ""
    }

    // Detect Python 3 binary (prefer venv / common brew paths)
    private var pythonPath: String {
        let candidates = [
            "/usr/local/bin/python3",
            "/opt/homebrew/bin/python3",
            "/usr/bin/python3",
            ProcessInfo.processInfo.environment["VOICETYPE_PYTHON"] ?? ""
        ]
        return candidates.first { FileManager.default.isExecutableFile(atPath: $0) } ?? "python3"
    }

    func transcribe(audioURL: URL, completion: @escaping (String?) -> Void) {
        guard !scriptPath.isEmpty else {
            print("WhisperTranscriber: transcribe.py not found in bundle")
            completion(nil)
            return
        }

        let process = Process()
        process.executableURL = URL(fileURLWithPath: pythonPath)
        process.arguments = [scriptPath, audioURL.path]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = Pipe() // suppress Python warnings

        process.terminationHandler = { _ in
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            let text = String(data: data, encoding: .utf8)?
                .trimmingCharacters(in: .whitespacesAndNewlines)
            DispatchQueue.main.async { completion(text.flatMap { $0.isEmpty ? nil : $0 }) }
        }

        do {
            try process.run()
        } catch {
            print("WhisperTranscriber: process launch failed: \(error)")
            completion(nil)
        }
    }

    var isModelReady: Bool {
        let modelPath = NSHomeDirectory() + "/Library/Application Support/VoiceType/models/small/model.bin"
        return FileManager.default.fileExists(atPath: modelPath)
    }
}
