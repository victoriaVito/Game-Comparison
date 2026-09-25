from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = Path(__file__).with_name("no_booster_recaptures_m3.json")
BUILDER = Path(__file__).with_name("build_video_batch.py")
YT_DLP = Path.home() / ".local" / "bin" / "yt-dlp"
DEFAULT_CACHE = Path.home() / ".cache" / "codex" / "royal-kingdom" / "no-booster"


def video_supports_canonical_crop(video: Path) -> bool:
    if not video.is_file():
        return False
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
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return False
    streams = json.loads(result.stdout).get("streams", [])
    if not streams:
        return False
    width = int(streams[0]["width"])
    height = int(streams[0]["height"])
    return (height == 720 and width >= 405) or (width == 720 and height >= 720)


def download(source: dict[str, object], cache: Path) -> Path:
    videos = cache / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    video = videos / f"{source['id']}.mp4"
    if video_supports_canonical_crop(video):
        return video
    video.unlink(missing_ok=True)
    avc_selector = "bestvideo[height=720][ext=mp4][vcodec^=avc1][protocol=https]/bestvideo[width=720][ext=mp4][vcodec^=avc1][protocol=https]"
    fallback_selector = "bestvideo[height=720][ext=mp4][protocol=https]/bestvideo[width=720][ext=mp4][protocol=https]"
    selectors = (avc_selector, avc_selector, fallback_selector)
    for attempt, format_selector in enumerate(selectors, start=1):
        try:
            subprocess.run(
                [
                    str(YT_DLP),
                    "-f",
                    format_selector,
                    "--abort-on-unavailable-fragments",
                    "--no-progress",
                    "-o",
                    str(videos / "%(id)s.%(ext)s"),
                    str(source["url"]),
                ],
                check=True,
            )
            if video_supports_canonical_crop(video):
                break
            video.unlink(missing_ok=True)
            if attempt == len(selectors):
                raise RuntimeError(f"Downloaded video cannot support a 405x720 crop: {video}")
        except subprocess.CalledProcessError:
            if attempt == len(selectors):
                raise
    return video


def stage_explicit_capture(
    source: dict[str, object], video: Path, output: Path, level: int
) -> None:
    board = output / "levels" / f"level-{level:04d}.jpg"
    board.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            str(source["timestamp_seconds"]),
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-vf",
            "crop=405:720:(iw-405)/2:0",
            "-q:v",
            "2",
            str(board),
        ],
        check=True,
    )
    duration_result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    manifest = {
        "game": "Royal Kingdom",
        "source": source["url"],
        "expected_range": [level, level],
        "expected_levels": 1,
        "captured_levels": 1,
        "levels": [
            {
                "level": level,
                "board": f"levels/level-{level:04d}.jpg",
                "source_url": source["url"],
                "timestamp_seconds": source["timestamp_seconds"],
                "segment_start_seconds": 0.0,
                "segment_end_seconds": float(duration_result.stdout.strip()),
                "confidence": 0.9,
                "method": "explicit_initial_frame",
                "level_type": "dark_kingdom" if level % 10 == 0 else "standard",
                "tutorial": False,
                "tutorial_method": "ocr_instruction",
                "flags": ["calibration_batch", "needs_visual_review"],
                "ocr_text": source["ocr_text"],
            }
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    sources = json.loads(SOURCES_PATH.read_text())["sources"]
    for source in sources:
        level = int(source["level"])
        video = download(source, DEFAULT_CACHE)
        output = PROJECT_ROOT / "staging" / "no-booster" / f"level-{level:04d}"
        if "timestamp_seconds" in source:
            stage_explicit_capture(source, video, output, level)
        else:
            subprocess.run(
                [
                    sys.executable,
                    str(BUILDER),
                    "--video",
                    str(video),
                    "--source-url",
                    str(source["url"]),
                    "--level-start",
                    str(level),
                    "--level-end",
                    str(level),
                    "--cache",
                    str(DEFAULT_CACHE / str(source["id"])),
                    "--output",
                    str(output),
                ],
                check=True,
            )
        manifest = json.loads((output / "manifest.json").read_text())
        if [entry["level"] for entry in manifest["levels"]] != [level]:
            raise RuntimeError(f"Invalid no-booster staging for level {level}")
        print(json.dumps({"prepared": level, "source_id": source["id"]}))


if __name__ == "__main__":
    main()
