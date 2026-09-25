import AppKit
import Foundation
import Vision

struct ScanResult: Codable {
    let path: String
    let values: [Int]
    let targetCount: Int?
    let confidence: Double
    let method: String
    let rawText: [String]
    let energies: [String: Double]
}

func recognize(_ cgImage: CGImage) throws -> ([String], [Int]) {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    request.recognitionLanguages = ["en-US"]
    try VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])

    let text = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
    let numberPattern = try NSRegularExpression(pattern: "[0-9]+")
    let values = text.flatMap { line -> [Int] in
        let range = NSRange(line.startIndex..<line.endIndex, in: line)
        return numberPattern.matches(in: line, range: range).compactMap { match in
            Range(match.range, in: line).flatMap { Int(line[$0]) }
        }
    }.filter { $0 > 0 && $0 < 1000 }

    return (text, values)
}

func cropAndScale(_ image: CGImage, x: Int, y: Int, width: Int, height: Int) throws -> CGImage {
    guard let cropped = image.cropping(to: CGRect(x: x, y: y, width: width, height: height)) else {
        throw NSError(domain: "TargetScanner", code: 2, userInfo: [NSLocalizedDescriptionKey: "Cannot crop target panel"])
    }
    let scale = 5
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    guard let context = CGContext(
        data: nil,
        width: width * scale,
        height: height * scale,
        bitsPerComponent: 8,
        bytesPerRow: 0,
        space: colorSpace,
        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
    ) else {
        throw NSError(domain: "TargetScanner", code: 3, userInfo: [NSLocalizedDescriptionKey: "Cannot create image context"])
    }
    context.interpolationQuality = .high
    context.draw(cropped, in: CGRect(x: 0, y: 0, width: width * scale, height: height * scale))
    guard let scaled = context.makeImage() else {
        throw NSError(domain: "TargetScanner", code: 4, userInfo: [NSLocalizedDescriptionKey: "Cannot scale target panel"])
    }
    return scaled
}

func patchEnergy(_ bitmap: NSBitmapImageRep, centerX: Int, centerY: Int, radius: Int = 12) -> Double {
    var samples: [[Double]] = [[], [], []]
    for y in (centerY - radius)..<(centerY + radius) {
        for x in (centerX - radius)..<(centerX + radius) {
            guard let color = bitmap.colorAt(x: x, y: y)?.usingColorSpace(.deviceRGB) else { continue }
            samples[0].append(Double(color.redComponent))
            samples[1].append(Double(color.greenComponent))
            samples[2].append(Double(color.blueComponent))
        }
    }
    return samples.map { channel in
        let mean = channel.reduce(0, +) / Double(channel.count)
        return channel.map { value in
            let delta = value - mean
            return delta * delta
        }.reduce(0, +) / Double(channel.count)
    }.reduce(0, +).squareRoot()
}

func scanTargetPanel(at path: String) throws -> ScanResult {
    guard let image = NSImage(contentsOfFile: path),
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        throw NSError(domain: "TargetScanner", code: 1, userInfo: [NSLocalizedDescriptionKey: "Cannot decode image: \(path)"])
    }

    let wholePanel = try cropAndScale(cgImage, x: 0, y: 35, width: 145, height: 125)
    let whole = try recognize(wholePanel)
    let bitmap = NSBitmapImageRep(cgImage: cgImage)
    let energies = [
        "topLeft": patchEnergy(bitmap, centerX: 52, centerY: 92),
        "topRight": patchEnergy(bitmap, centerX: 100, centerY: 92),
        "bottomLeft": patchEnergy(bitmap, centerX: 52, centerY: 132),
        "bottomRight": patchEnergy(bitmap, centerX: 100, centerY: 132),
        "center": patchEnergy(bitmap, centerX: 73, centerY: 112),
    ]
    let gridValues = ["topLeft", "topRight", "bottomLeft", "bottomRight"].compactMap { energies[$0] }
    let targetCount: Int?
    let confidence: Double
    let method: String
    if (2...4).contains(whole.1.count) {
        targetCount = whole.1.count
        confidence = 0.95
        method = "ocr_values"
    } else if whole.1.count == 1 && gridValues.count == 4 && gridValues.allSatisfy({ $0 > 0.22 }) {
        targetCount = 4
        confidence = 0.75
        method = "visual_grid"
    } else if whole.1.count == 1 {
        targetCount = 1
        confidence = 0.80
        method = "ocr_values"
    } else {
        targetCount = nil
        confidence = 0.0
        method = "unresolved"
    }

    return ScanResult(path: path, values: whole.1, targetCount: targetCount, confidence: confidence, method: method, rawText: whole.0, energies: energies)
}

let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys]

for path in CommandLine.arguments.dropFirst() {
    do {
        let result = try scanTargetPanel(at: path)
        FileHandle.standardOutput.write(try encoder.encode(result))
        FileHandle.standardOutput.write(Data("\n".utf8))
    } catch {
        FileHandle.standardError.write(Data("\(error.localizedDescription)\n".utf8))
    }
}
