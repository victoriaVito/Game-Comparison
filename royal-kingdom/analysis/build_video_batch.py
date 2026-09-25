from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_pilot import FrameProbe, compile_scanner, probe_frames


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def video_dimensions(video: Path) -> tuple[int, int]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(result.stdout)["streams"][0]
    return int(stream["width"]), int(stream["height"])


def extract_samples(video: Path, samples: Path) -> None:
    samples.mkdir(parents=True, exist_ok=True)
    if any(samples.glob("*.jpg")):
        return
    width, height = video_dimensions(video)
    transform = "scale=405:720" if height > width else "crop=405:720:(iw-405)/2:0"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-vf",
            f"fps=2,{transform}",
            "-q:v",
            "3",
            str(samples / "%06d.jpg"),
        ],
        check=True,
    )


def find_anchors(
    probes: list[FrameProbe], level_start: int, level_end: int
) -> dict[int, FrameProbe]:
    anchors: dict[int, FrameProbe] = {}
    previous_second = -1.0
    for level in range(level_start, level_end + 1):
        for probe in probes:
            if probe.second <= previous_second:
                continue
            joined = " ".join(probe.text).lower()
            if not any(label in joined for label in ("play", "reward", "free")):
                continue
            pattern = rf"(?:\S+\s*)?Level[ ._-]*{level}[ _.-]*"
            if any(re.fullmatch(pattern, line, re.IGNORECASE) for line in probe.text):
                anchors[level] = probe
                previous_second = probe.second
                break
    if level_start not in anchors:
        anchors[level_start] = probes[0]
    missing = sorted(set(range(level_start, level_end + 1)) - anchors.keys())
    if missing:
        raise RuntimeError(f"Missing level anchors: {missing}")
    return anchors


def choose_capture(window: list[FrameProbe]) -> FrameProbe:
    unlock_end = max(
        (
            probe.second
            for probe in window
            if "new item unlocked" in " ".join(probe.text).lower()
        ),
        default=window[0].second,
    )
    candidates = [
        probe
        for probe in window
        if probe.has_moves_label and probe.second > unlock_end
    ]
    for current, following in zip(candidates, candidates[1:], strict=False):
        if following.second - current.second > 0.6:
            continue
        moves_index = next(
            (
                index
                for index, line in enumerate(following.text[:-1])
                if line.lower().startswith("mov")
            ),
            None,
        )
        if moves_index is None or not following.text[moves_index + 1].isdigit():
            return following
        initial_moves = int(following.text[moves_index + 1])
        capture = following
        for candidate in candidates[candidates.index(following) + 1 :]:
            candidate_index = next(
                (
                    index
                    for index, line in enumerate(candidate.text[:-1])
                    if line.lower().startswith("mov")
                ),
                None,
            )
            if candidate_index is None or not candidate.text[candidate_index + 1].isdigit():
                continue
            if int(candidate.text[candidate_index + 1]) != initial_moves:
                break
            capture = candidate
        return capture
    raise RuntimeError(f"No stable board found after {window[0].second:.1f}s")


def classify_level(anchor: FrameProbe, window: list[FrameProbe], capture: FrameProbe) -> tuple[str, bool]:
    anchor_text = " ".join(anchor.text).lower()
    level_type = "standard"
    if "dark kingdom" in anchor_text:
        level_type = "dark_kingdom"
    elif "kingdom" in anchor_text:
        level_type = "kingdom"
    tutorial = any(
        any(keyword in line.lower() for keyword in ("tap", "hit the", "make a match", "fight back"))
        for probe in window
        if capture.second - 2 <= probe.second <= capture.second + 3
        for line in probe.text
    )
    return level_type, tutorial


def build_manifest(
    probes: list[FrameProbe],
    anchors: dict[int, FrameProbe],
    level_start: int,
    level_end: int,
    source_url: str,
    output: Path,
) -> dict[str, object]:
    levels_dir = output / "levels"
    levels_dir.mkdir(parents=True, exist_ok=True)
    levels: list[dict[str, object]] = []
    for level in range(level_start, level_end + 1):
        start = anchors[level].second
        end = anchors[level + 1].second if level < level_end else probes[-1].second
        window = [probe for probe in probes if start <= probe.second < end]
        capture = choose_capture(window)
        level_type, tutorial = classify_level(anchors[level], window, capture)
        destination = levels_dir / f"level-{level:04d}.jpg"
        shutil.copy2(capture.path, destination)
        levels.append(
            {
                "level": level,
                "board": f"levels/{destination.name}",
                "source_url": source_url,
                "timestamp_seconds": capture.second,
                "segment_start_seconds": start,
                "segment_end_seconds": end,
                "confidence": 0.9,
                "method": "level_dialog_then_stable_moves",
                "level_type": level_type,
                "tutorial": tutorial,
                "tutorial_method": "ocr_instruction",
                "flags": ["calibration_batch", "needs_visual_review"],
                "ocr_text": list(capture.text),
            }
        )
    manifest = {
        "game": "Royal Kingdom",
        "source": source_url,
        "expected_range": [level_start, level_end],
        "expected_levels": level_end - level_start + 1,
        "captured_levels": len(levels),
        "levels": levels,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--level-start", type=int, required=True)
    parser.add_argument("--level-end", type=int, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    compile_scanner()
    extract_samples(args.video, args.cache / "samples")
    probes = probe_frames(
        sorted((args.cache / "samples").glob("*.jpg")), args.cache / "probes.jsonl"
    )
    anchors = find_anchors(probes, args.level_start, args.level_end)
    manifest = build_manifest(
        probes,
        anchors,
        args.level_start,
        args.level_end,
        args.source_url,
        args.output,
    )
    print(json.dumps({"captured": manifest["captured_levels"], "range": manifest["expected_range"]}))


if __name__ == "__main__":
    main()
