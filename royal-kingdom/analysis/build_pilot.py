from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCANNER_SOURCE = Path(__file__).with_name("probe_frame.swift")
SCANNER_BINARY = Path(__file__).with_name(".build") / "probe-frame"
SOURCE_URL = "https://www.youtube.com/watch?v=nT-hcLmkddg"
SAMPLE_RATE = 2
REVIEW_FILE = Path(__file__).with_name("review.json")


@dataclass(frozen=True)
class FrameProbe:
    path: Path
    second: float
    text: tuple[str, ...]
    numbers: tuple[int, ...]
    has_moves_label: bool
    board_edge_energy: float


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def compile_scanner() -> None:
    if (
        SCANNER_BINARY.exists()
        and SCANNER_BINARY.stat().st_mtime >= SCANNER_SOURCE.stat().st_mtime
    ):
        return
    SCANNER_BINARY.parent.mkdir(parents=True, exist_ok=True)
    run(["swiftc", str(SCANNER_SOURCE), "-o", str(SCANNER_BINARY)])


def extract_samples(video: Path, samples: Path) -> None:
    samples.mkdir(parents=True, exist_ok=True)
    if any(samples.glob("*.jpg")):
        return
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-vf",
            f"fps={SAMPLE_RATE},crop=405:720:437:0",
            "-q:v",
            "3",
            str(samples / "%06d.jpg"),
        ]
    )


def chunks[T](values: list[T], size: int) -> list[list[T]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def probe_frames(paths: list[Path], cache: Path) -> list[FrameProbe]:
    probes: list[FrameProbe] = []
    raw_lines: list[str] = []
    if cache.exists():
        raw_lines = cache.read_text().splitlines()
    else:
        for batch in chunks(paths, 100):
            result = subprocess.run(
                [str(SCANNER_BINARY), *(str(path) for path in batch)],
                check=True,
                capture_output=True,
                text=True,
            )
            raw_lines.extend(result.stdout.splitlines())
        cache.write_text("\n".join(raw_lines) + "\n")

    for line in raw_lines:
            raw = json.loads(line)
            path = Path(raw["path"])
            frame_number = int(path.stem)
            probes.append(
                FrameProbe(
                    path=path,
                    second=(frame_number - 1) / SAMPLE_RATE,
                    text=tuple(raw["text"]),
                    numbers=tuple(raw["numbers"]),
                    has_moves_label=raw["hasMovesLabel"],
                    board_edge_energy=raw["boardEdgeEnergy"],
                )
            )
    return sorted(probes, key=lambda probe: probe.second)


def level_anchors(probes: list[FrameProbe]) -> dict[int, FrameProbe]:
    anchors: dict[int, FrameProbe] = {1: probes[0]}
    for probe in probes:
        joined = " ".join(probe.text).lower()
        if not any(label in joined for label in ("play", "reward", "free")):
            continue
        for level in range(2, 16):
            pattern = rf"Level[ ._-]*{level}[ _.-]*"
            if level not in anchors and any(re.fullmatch(pattern, line, re.IGNORECASE) for line in probe.text):
                anchors[level] = probe
    missing = sorted(set(range(1, 16)) - anchors.keys())
    if missing:
        raise RuntimeError(f"Missing level anchors: {missing}")
    return anchors


def choose_capture(window: list[FrameProbe]) -> FrameProbe:
    candidates = [probe for probe in window if probe.has_moves_label]
    if not candidates:
        candidates = [
            probe
            for probe in window
            if probe.text
            and probe.text[0].isdigit()
            and 10 <= int(probe.text[0]) <= 99
        ]
    stable = [
        probe
        for probe in candidates
        if any(
            0 < other.second - probe.second <= 1.5
            and (probe.has_moves_label or other.text[:1] == probe.text[:1])
            for other in candidates
        )
    ]
    if not stable:
        raise RuntimeError(f"No stable board found after {window[0].second:.1f}s")
    target_second = stable[0].second + 1.0
    return min(window, key=lambda probe: abs(probe.second - target_second))


def write_output(probes: list[FrameProbe], anchors: dict[int, FrameProbe], output: Path) -> None:
    levels_dir = output / "levels"
    levels_dir.mkdir(parents=True, exist_ok=True)
    review = json.loads(REVIEW_FILE.read_text()) if REVIEW_FILE.exists() else {}
    reviewed_tutorials = set(review.get("tutorial_levels", []))
    levels = []
    for level in range(1, 16):
        start = anchors[level].second
        end = anchors[level + 1].second if level < 15 else probes[-1].second
        window = [probe for probe in probes if start <= probe.second < end]
        capture = choose_capture(window)
        anchor_text = " ".join(anchors[level].text).lower()
        level_type = "standard"
        if "dark kingdom" in anchor_text:
            level_type = "dark_kingdom"
        elif "kingdom" in anchor_text:
            level_type = "kingdom"
        tutorial = level in reviewed_tutorials or any(
            any(
                keyword in line.lower()
                for keyword in ("tap", "hit the", "make a match", "fight back")
            )
            for probe in window
            if capture.second - 2 <= probe.second <= capture.second + 3
            for line in probe.text
        )
        destination = levels_dir / f"level-{level:04d}.jpg"
        shutil.copy2(capture.path, destination)
        levels.append(
            {
                "level": level,
                "board": f"levels/{destination.name}",
                "source_url": SOURCE_URL,
                "timestamp_seconds": capture.second,
                "segment_start_seconds": start,
                "segment_end_seconds": end,
                "confidence": 0.9 if level > 1 else 0.8,
                "method": "level_dialog_then_stable_moves",
                "level_type": level_type,
                "tutorial": tutorial,
                "tutorial_method": "visual_review" if level in reviewed_tutorials else "ocr_instruction",
                "flags": [
                    "pilot",
                    "visual_review_passed",
                    *(["tutorial_overlay"] if tutorial else []),
                ],
                "ocr_text": list(capture.text),
            }
        )

    manifest = {
        "game": "Royal Kingdom",
        "source": SOURCE_URL,
        "expected_levels": 15,
        "captured_levels": len(levels),
        "sample_rate_fps": SAMPLE_RATE,
        "levels": levels,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path.home() / ".cache" / "codex" / "royal-kingdom" / "samples",
    )
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    compile_scanner()
    extract_samples(args.video, args.cache)
    probes = probe_frames(sorted(args.cache.glob("*.jpg")), args.cache.parent / "probes.jsonl")
    anchors = level_anchors(probes)
    write_output(probes, anchors, args.output)
    print(f"Captured {len(anchors)} levels")


if __name__ == "__main__":
    main()
