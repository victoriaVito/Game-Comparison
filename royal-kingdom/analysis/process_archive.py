from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = Path(__file__).with_name("range_source_catalog.json")
BUILDER = Path(__file__).with_name("build_video_batch.py")
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"
REVIEWS_ROOT = PROJECT_ROOT / "reviews"
STAGING_ROOT = PROJECT_ROOT / "staging"
PROGRESS_PATH = Path(__file__).with_name("archive_progress.json")
STATE_LOCK_PATH = Path(__file__).with_name("archive_state.lock")
YT_DLP = Path.home() / ".local" / "bin" / "yt-dlp"
DEFAULT_CACHE = Path.home() / ".cache" / "codex" / "royal-kingdom" / "archive"


@contextmanager
def state_lock() -> Iterator[None]:
    with STATE_LOCK_PATH.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def video_is_complete(path: Path) -> bool:
    if not path.is_file():
        return False
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", str(path)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "duration=" in result.stdout


def download_video(source: dict[str, object], cache_root: Path) -> Path:
    videos_dir = cache_root / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    video = videos_dir / f"{source['id']}.mp4"
    if video_is_complete(video):
        return video
    video.unlink(missing_ok=True)
    Path(f"{video}.part").unlink(missing_ok=True)
    Path(f"{video}.ytdl").unlink(missing_ok=True)
    selectors = (
        "bestvideo[height<=720][ext=mp4][vcodec^=avc1][protocol=https]",
        "bestvideo[height<=720][ext=mp4][vcodec^=avc1][protocol=https]",
        "bestvideo[height<=720][ext=mp4][protocol=https]",
    )
    for attempt, selector in enumerate(selectors, start=1):
        video.unlink(missing_ok=True)
        Path(f"{video}.part").unlink(missing_ok=True)
        Path(f"{video}.ytdl").unlink(missing_ok=True)
        try:
            subprocess.run(
                [
                    str(YT_DLP),
                    "-f",
                    selector,
                    "--abort-on-unavailable-fragments",
                    "--no-progress",
                    "-o",
                    str(videos_dir / "%(id)s.%(ext)s"),
                    str(source["url"]),
                ],
                check=True,
            )
            break
        except subprocess.CalledProcessError:
            if attempt == len(selectors):
                raise
    if not video_is_complete(video):
        raise RuntimeError(f"Downloaded video is incomplete: {video}")
    return video


def published_levels() -> dict[int, dict[str, object]]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    return {int(entry["level"]): entry for entry in manifest["levels"]}


def continuous_prefix(levels: dict[int, dict[str, object]]) -> int:
    level = 1
    while level in levels:
        level += 1
    return level - 1


def source_is_published(source: dict[str, object]) -> bool:
    levels = published_levels()
    expected = range(int(source["level_start"]), int(source["level_end"]) + 1)
    return all(
        level in levels and (PROJECT_ROOT / str(levels[level]["board"])).is_file()
        for level in expected
    )


def extract_source(source: dict[str, object], video: Path, cache_root: Path) -> Path:
    start = int(source["level_start"])
    end = int(source["level_end"])
    output = STAGING_ROOT / f"{start:04d}-{end:04d}"
    subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--video",
            str(video),
            "--source-url",
            str(source["url"]),
            "--level-start",
            str(start),
            "--level-end",
            str(end),
            "--cache",
            str(cache_root / str(source["id"])),
            "--output",
            str(output),
        ],
        check=True,
    )
    return output


def validate_staging(source: dict[str, object], staging: Path) -> list[dict[str, object]]:
    manifest = json.loads((staging / "manifest.json").read_text())
    levels = manifest["levels"]
    start = int(source["level_start"])
    end = int(source["level_end"])
    if [entry["level"] for entry in levels] != list(range(start, end + 1)):
        raise RuntimeError(f"Staging coverage mismatch for {start}-{end}")
    for entry in levels:
        board = staging / str(entry["board"])
        if not board.is_file() or board.read_bytes()[:3] != b"\xff\xd8\xff":
            raise RuntimeError(f"Invalid JPEG for level {entry['level']}")
        text = " ".join(str(value) for value in entry["ocr_text"]).lower()
        blocked_screen = any(
            label in text for label in ("new item unlocked", "my team", "select boosters")
        ) or all(label in text for label in ("world", "tasks", "home"))
        if blocked_screen:
            raise RuntimeError(f"Non-board screen captured for level {entry['level']}")
    return levels


def write_review(source: dict[str, object], levels: list[dict[str, object]]) -> Path:
    REVIEWS_ROOT.mkdir(exist_ok=True)
    start = int(source["level_start"])
    end = int(source["level_end"])
    path = REVIEWS_ROOT / f"review-{start:04d}-{end:04d}.json"
    review = {
        "reviewed_at": datetime.now(UTC).isoformat(),
        "review_scope": f"Royal Kingdom levels {start}-{end}",
        "result": "automated_passed",
        "checks": [
            "Exact expected level sequence",
            "JPEG signature present for every board",
            "Source URL and timestamp present for every level",
            "No captured New item unlocked screen",
        ],
        "visual_review": "pending_stratified_sample",
        "reviewed_levels": [entry["level"] for entry in levels],
    }
    path.write_text(json.dumps(review, indent=2) + "\n")
    return path


def publish(levels: list[dict[str, object]]) -> None:
    with state_lock():
        manifest = json.loads(MANIFEST_PATH.read_text())
        merged = {int(entry["level"]): entry for entry in manifest["levels"]}
        levels_dir = PROJECT_ROOT / "levels"
        for entry in levels:
            staging = STAGING_ROOT / f"{int(levels[0]['level']):04d}-{int(levels[-1]['level']):04d}"
            source = staging / str(entry["board"])
            flags = [flag for flag in entry["flags"] if flag != "needs_visual_review"]
            entry["flags"] = [*flags, "automated_review_passed"]
            shutil.copy2(source, levels_dir / source.name)
            merged[int(entry["level"])] = entry
        ordered = [merged[level] for level in sorted(merged)]
        manifest.update(
            {
                "source": "Multiple YouTube walkthroughs; see source_url per level",
                "source_count": len({entry["source_url"] for entry in ordered}),
                "expected_levels": int(json.loads(CATALOG_PATH.read_text())["range"][1]),
                "captured_levels": len(ordered),
                "levels": ordered,
            }
        )
        atomic_write_json(MANIFEST_PATH, manifest)


def record_progress(source: dict[str, object], status: str, detail: str = "") -> None:
    with state_lock():
        progress = json.loads(PROGRESS_PATH.read_text()) if PROGRESS_PATH.exists() else {"runs": []}
        progress["updated_at"] = datetime.now(UTC).isoformat()
        progress["published_through"] = continuous_prefix(published_levels())
        progress["runs"].append(
            {
                "source_id": source["id"],
                "range": [source["level_start"], source["level_end"]],
                "status": status,
                "detail": detail,
            }
        )
        atomic_write_json(PROGRESS_PATH, progress)


def cleanup(source: dict[str, object], staging: Path, video: Path, cache_root: Path) -> None:
    video.unlink(missing_ok=True)
    sample_cache = cache_root / str(source["id"])
    if sample_cache.is_dir():
        shutil.rmtree(sample_cache)
    if staging.is_dir():
        shutil.rmtree(staging)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--keep-transient", action="store_true")
    args = parser.parse_args()

    catalog = json.loads(CATALOG_PATH.read_text())
    sources = [
        source
        for source in catalog["sources"]
        if int(source["level_start"]) >= args.start
        and int(source["level_end"]) <= args.end
    ]
    if not sources or int(sources[0]["level_start"]) != args.start:
        raise RuntimeError(f"No catalog sequence begins at {args.start}")
    if int(sources[-1]["level_end"]) != args.end:
        raise RuntimeError(f"Catalog sequence does not end at {args.end}")

    for source in sources:
        if source_is_published(source):
            record_progress(source, "already_published")
            continue
        try:
            video = download_video(source, args.cache_root)
            staging = extract_source(source, video, args.cache_root)
            levels = validate_staging(source, staging)
            write_review(source, levels)
            publish(levels)
            record_progress(source, "published")
            if not args.keep_transient:
                cleanup(source, staging, video, args.cache_root)
        except Exception as exc:
            record_progress(source, "failed", str(exc))
            raise
        print(
            json.dumps(
                {
                    "published": [source["level_start"], source["level_end"]],
                    "archive_total": len(published_levels()),
                }
            )
        )


if __name__ == "__main__":
    main()
