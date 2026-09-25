from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = Path(__file__).with_name("batch_sources_0016_0100.json")
BUILDER = Path(__file__).with_name("build_video_batch.py")
YT_DLP = Path.home() / ".local" / "bin" / "yt-dlp"


def manifest_complete(path: Path, level_start: int, level_end: int) -> bool:
    if not path.exists():
        return False
    manifest = json.loads(path.read_text())
    expected = list(range(level_start, level_end + 1))
    return [entry["level"] for entry in manifest.get("levels", [])] == expected


def download_video(video_id: str, videos_dir: Path) -> Path:
    videos_dir.mkdir(parents=True, exist_ok=True)
    output = videos_dir / f"{video_id}.mp4"
    if output.exists():
        return output
    subprocess.run(
        [
            str(YT_DLP),
            "-f",
            "bestvideo[height<=720][ext=mp4]",
            "--no-progress",
            "--no-part",
            "-o",
            str(videos_dir / "%(id)s.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}",
        ],
        check=True,
    )
    return output


def process_video(source: dict[str, object], cache_root: Path, staging_root: Path) -> dict[str, object]:
    video_id = str(source["id"])
    level_start = int(source["level_start"])
    level_end = int(source["level_end"])
    output = staging_root / f"{level_start:04d}-{level_end:04d}"
    manifest_path = output / "manifest.json"
    if manifest_complete(manifest_path, level_start, level_end):
        return {"video_id": video_id, "range": [level_start, level_end], "status": "cached"}

    video = download_video(video_id, cache_root / "videos")
    subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--video",
            str(video),
            "--source-url",
            f"https://www.youtube.com/watch?v={video_id}",
            "--level-start",
            str(level_start),
            "--level-end",
            str(level_end),
            "--cache",
            str(cache_root / video_id),
            "--output",
            str(output),
        ],
        check=True,
    )
    if not manifest_complete(manifest_path, level_start, level_end):
        raise RuntimeError(f"Incomplete manifest for {level_start}-{level_end}")
    return {"video_id": video_id, "range": [level_start, level_end], "status": "processed"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=Path.home() / ".cache" / "codex" / "royal-kingdom" / "batch-0016-0100",
    )
    parser.add_argument("--staging-root", type=Path, default=PROJECT_ROOT / "staging")
    args = parser.parse_args()

    source_data = json.loads(args.sources.read_text())
    results = [
        process_video(source, args.cache_root, args.staging_root)
        for source in source_data["videos"]
    ]
    print(json.dumps({"batch": source_data["batch"], "results": results}, indent=2))


if __name__ == "__main__":
    main()
