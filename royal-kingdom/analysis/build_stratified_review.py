from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BLOCK_SIZE = 100
SUB_BLOCK_SIZE = 20
SUB_BLOCK_OFFSETS = (3, 7, 11, 19)
SHEET_COLUMNS = 5
SHEET_ROWS = 8
THUMBNAIL_SIZE = (202, 360)


@dataclass(frozen=True)
class ImageRecord:
    level: int
    path: Path
    width: int
    height: int
    sha256: str


def sample_levels(block_start: int) -> list[int]:
    block_end = block_start + BLOCK_SIZE - 1
    multiples_of_five = range(block_start + 4, block_end + 1, 5)
    offsets = (
        sub_block_start + offset - 1
        for sub_block_start in range(block_start, block_end + 1, SUB_BLOCK_SIZE)
        for offset in SUB_BLOCK_OFFSETS
    )
    return sorted((*multiples_of_five, *offsets))


def discover_complete_blocks(levels_dir: Path) -> list[int]:
    level_ids: set[int] = set()
    for path in levels_dir.glob("level-*.jpg"):
        try:
            level_ids.add(int(path.stem.removeprefix("level-")))
        except ValueError:
            continue
    if not level_ids:
        raise ValueError(f"No level JPEGs found in {levels_dir}")
    highest_complete_boundary = max(level_ids) // BLOCK_SIZE * BLOCK_SIZE
    return [
        block_start
        for block_start in range(1, highest_complete_boundary + 1, BLOCK_SIZE)
        if all(level in level_ids for level in range(block_start, block_start + BLOCK_SIZE))
    ]


def validate_image(path: Path, level: int, ffprobe: str) -> ImageRecord:
    if not path.is_file():
        raise ValueError(f"Missing level image: {path}")
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or "ffprobe could not decode the image"
        raise ValueError(f"Invalid image for level {level}: {detail}")
    try:
        stream = json.loads(result.stdout)["streams"][0]
        codec_name = stream["codec_name"]
        width = int(stream["width"])
        height = int(stream["height"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Missing JPEG stream metadata for level {level}: {path}") from exc
    if codec_name != "mjpeg" or width <= 0 or height <= 0:
        raise ValueError(f"Level {level} is not a valid JPEG: {path}")
    return ImageRecord(
        level=level,
        path=path,
        width=width,
        height=height,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def validate_block(
    levels_dir: Path, block_start: int, ffprobe: str
) -> tuple[list[ImageRecord], list[ImageRecord]]:
    all_records = [
        validate_image(levels_dir / f"level-{level:04d}.jpg", level, ffprobe)
        for level in range(block_start, block_start + BLOCK_SIZE)
    ]
    records_by_level = {record.level: record for record in all_records}
    selected_levels = sample_levels(block_start)
    if len(selected_levels) != 40 or len(set(selected_levels)) != 40:
        raise RuntimeError(f"Invalid sample policy for block starting at {block_start}")
    return all_records, [records_by_level[level] for level in selected_levels]


def build_contact_sheet(records: list[ImageRecord], output_path: Path, ffmpeg: str) -> None:
    if len(records) != SHEET_COLUMNS * SHEET_ROWS:
        raise ValueError(f"Contact sheet requires exactly {SHEET_COLUMNS * SHEET_ROWS} images")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cell_width, cell_height = THUMBNAIL_SIZE
    inputs = [argument for record in records for argument in ("-i", str(record.path))]
    normalized_inputs = [
        (
            f"[{index}:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,"
            f"pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:white,setsar=1[v{index}]"
        )
        for index in range(len(records))
    ]
    layout = "|".join(
        f"{(index % SHEET_COLUMNS) * cell_width}_{(index // SHEET_COLUMNS) * cell_height}"
        for index in range(len(records))
    )
    stack = "".join(f"[v{index}]" for index in range(len(records)))
    filter_complex = ";".join(
        [*normalized_inputs, f"{stack}xstack=inputs={len(records)}:layout={layout}:fill=black[out]"]
    )
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[out]",
            "-frames:v",
            "1",
            "-map_metadata",
            "-1",
            "-threads",
            "1",
            "-c:v",
            "mjpeg",
            "-q:v",
            "2",
            str(output_path),
        ],
        check=True,
    )


def validate_contact_sheet(output_path: Path, ffprobe: str, ffmpeg: str) -> None:
    cell_width, cell_height = THUMBNAIL_SIZE
    expected_width = SHEET_COLUMNS * cell_width
    expected_height = SHEET_ROWS * cell_height
    probe = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height",
            "-of",
            "json",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    if (
        stream.get("codec_name") != "mjpeg"
        or stream.get("width") != expected_width
        or stream.get("height") != expected_height
    ):
        raise RuntimeError(f"Unexpected contact sheet stream: {stream}")
    decoded = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(output_path),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "-",
        ],
        check=True,
        capture_output=True,
    ).stdout
    if len(decoded) != expected_width * expected_height:
        raise RuntimeError("Contact sheet did not decode to the expected pixel count")
    empty_cells: list[int] = []
    for cell_index in range(SHEET_COLUMNS * SHEET_ROWS):
        column = cell_index % SHEET_COLUMNS
        row = cell_index // SHEET_COLUMNS
        cell_sum = 0
        for y in range(row * cell_height, (row + 1) * cell_height):
            start = y * expected_width + column * cell_width
            cell_sum += sum(decoded[start : start + cell_width])
        mean_luma = cell_sum / (cell_width * cell_height)
        if mean_luma < 5:
            empty_cells.append(cell_index + 1)
    if empty_cells:
        raise RuntimeError(f"Contact sheet contains black or empty cells: {empty_cells}")


def build_metadata(
    levels_dir: Path,
    output_dir: Path,
    block_results: list[tuple[int, list[ImageRecord], list[ImageRecord]]],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "selection_policy": {
            "block_size": BLOCK_SIZE,
            "samples_per_block": 40,
            "multiples_of": 5,
            "sub_block_size": SUB_BLOCK_SIZE,
            "sub_block_offsets": list(SUB_BLOCK_OFFSETS),
        },
        "levels_directory": str(levels_dir.resolve()),
        "output_directory": str(output_dir.resolve()),
        "blocks": [
            {
                "block_start": block_start,
                "block_end": block_start + BLOCK_SIZE - 1,
                "validated_image_count": len(all_records),
                "sample_count": len(selected_records),
                "contact_sheet": f"review-{block_start:04d}-{block_start + BLOCK_SIZE - 1:04d}.jpg",
                "samples": [
                    {
                        "level": record.level,
                        "source_image": str(record.path.resolve()),
                        "width": record.width,
                        "height": record.height,
                        "sha256": record.sha256,
                    }
                    for record in selected_records
                ],
            }
            for block_start, all_records, selected_records in block_results
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build deterministic stratified Royal Kingdom review contact sheets."
    )
    parser.add_argument("--levels-dir", type=Path, default=PROJECT_ROOT / "levels")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--block-start",
        type=int,
        action="append",
        help="One-based start of a 100-level block. Repeat to select multiple blocks.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate complete blocks and JPEGs without writing output.",
    )
    args = parser.parse_args()

    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if ffprobe is None or ffmpeg is None:
        parser.error("ffprobe and ffmpeg must be available on PATH")

    discovered_blocks = discover_complete_blocks(args.levels_dir)
    block_starts = args.block_start or discovered_blocks
    invalid_starts = [start for start in block_starts if start < 1 or (start - 1) % BLOCK_SIZE]
    if invalid_starts:
        parser.error(f"Block starts must be 1, 101, 201, ...: {invalid_starts}")
    incomplete_blocks = [start for start in block_starts if start not in discovered_blocks]
    if incomplete_blocks:
        parser.error(f"Blocks are incomplete or unavailable: {incomplete_blocks}")

    block_results = [
        (block_start, *validate_block(args.levels_dir, block_start, ffprobe))
        for block_start in block_starts
    ]
    metadata = build_metadata(args.levels_dir, args.output_dir, block_results)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "passed",
                    "dry_run": True,
                    "blocks": block_starts,
                    "validated_images": sum(len(result[1]) for result in block_results),
                    "selected_images": sum(len(result[2]) for result in block_results),
                },
                indent=2,
            )
        )
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for block_start, _, selected_records in block_results:
        build_contact_sheet(
            selected_records,
            args.output_dir / f"review-{block_start:04d}-{block_start + BLOCK_SIZE - 1:04d}.jpg",
            ffmpeg,
        )
        validate_contact_sheet(
            args.output_dir / f"review-{block_start:04d}-{block_start + BLOCK_SIZE - 1:04d}.jpg",
            ffprobe,
            ffmpeg,
        )
    metadata_path = args.output_dir / "sample-metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"status": "passed", "metadata": str(metadata_path), "blocks": block_starts}, indent=2))


if __name__ == "__main__":
    main()
