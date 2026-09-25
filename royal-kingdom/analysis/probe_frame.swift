import AppKit
import Foundation
import Vision

struct ProbeResult: Codable {
    let path: String
    let text: [String]
    let numbers: [Int]
    let hasMovesLabel: Bool
    let boardEdgeEnergy: Double
}

func boardEdgeEnergy(_ image: CGImage) -> Double {
    let bitmap = NSBitmapImageRep(cgImage: image)
    let xRange = 20..<385
    let yRange = 45..<360
    var total = 0.0
    var samples = 0
    for y in stride(from: yRange.lowerBound, to: yRange.upperBound, by: 4) {
        for x in stride(from: xRange.lowerBound, to: xRange.upperBound, by: 4) {
            guard let current = bitmap.colorAt(x: x, y: y)?.usingColorSpace(.deviceRGB),
                  let neighbor = bitmap.colorAt(x: x + 4, y: y)?.usingColorSpace(.deviceRGB) else { continue }
            total += abs(current.redComponent - neighbor.redComponent)
            total += abs(current.greenComponent - neighbor.greenComponent)
            total += abs(current.blueComponent - neighbor.blueComponent)
            samples += 3
        }
    }
    return samples == 0 ? 0 : total / Double(samples)
}

func probe(_ path: String) throws -> ProbeResult {
    guard let image = NSImage(contentsOfFile: path),
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        throw NSError(domain: "RoyalKingdomProbe", code: 1)
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    request.recognitionLanguages = ["en-US"]
    try VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])

    let text = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
    let numberPattern = try NSRegularExpression(pattern: "[0-9]+")
    let numbers = text.flatMap { line -> [Int] in
        let range = NSRange(line.startIndex..<line.endIndex, in: line)
        return numberPattern.matches(in: line, range: range).compactMap { match in
            Range(match.range, in: line).flatMap { Int(line[$0]) }
        }
    }

    return ProbeResult(
        path: path,
        text: text,
        numbers: numbers,
        hasMovesLabel: text.contains { $0.lowercased().contains("mov") },
        boardEdgeEnergy: boardEdgeEnergy(cgImage)
    )
}

let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys]

for path in CommandLine.arguments.dropFirst() {
    do {
        FileHandle.standardOutput.write(try encoder.encode(probe(path)))
        FileHandle.standardOutput.write(Data("\n".utf8))
    } catch {
        FileHandle.standardError.write(Data("\(path): \(error.localizedDescription)\n".utf8))
    }
}
