from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path


CHANNEL_URL = "https://www.youtube.com/channel/UCph27JIfhqHnu5hcJiLzW4g/videos"
GAP_SOURCE = {
    "id": "Cq-Y_rnbYis",
    "title": "Royal Kingdom Levels 3541-3560",
    "level_start": 3541,
    "level_end": 3560,
    "url": "https://www.youtube.com/watch?v=Cq-Y_rnbYis",
    "source": "RasyaPlaysRK corrected-title video",
}
RANGE_PATTERN = re.compile(r"\bLevels?\s+(\d+)\s*[-–]\s*(\d+)\b", re.IGNORECASE)
RANGE_CORRECTIONS = {
    "E7BQfdokZX8": (3041, 3060),
    "Cq-Y_rnbYis": (3541, 3560),
}


def fetch_channel_entries(yt_dlp: Path) -> list[dict[str, object]]:
    result = subprocess.run(
        [
            str(yt_dlp),
            "--flat-playlist",
            "--print",
            "%(playlist_index)s\t%(id)s\t%(title)s\t%(duration)s",
            CHANNEL_URL,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    entries: list[dict[str, object]] = []
    for line in result.stdout.splitlines():
        index, video_id, title, duration = line.split("\t", 3)
        match = RANGE_PATTERN.search(title)
        if not match:
            continue
        start, end = (int(value) for value in match.groups())
        if video_id in RANGE_CORRECTIONS:
            start, end = RANGE_CORRECTIONS[video_id]
        entries.append(
            {
                "id": video_id,
                "title": title,
                "level_start": start,
                "level_end": end,
                "duration_seconds": int(float(duration)) if duration != "NA" else None,
                "channel_position": int(index),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "source": "RasyaPlaysRK channel",
            }
        )
    return entries


def select_sources(
    candidates: list[dict[str, object]], start: int, end: int
) -> list[dict[str, object]]:
    by_start: dict[int, list[dict[str, object]]] = {}
    for candidate in candidates:
        level_start = int(candidate["level_start"])
        level_end = int(candidate["level_end"])
        if level_end < level_start:
            continue
        by_start.setdefault(level_start, []).append(candidate)
    selected: list[dict[str, object]] = []
    current = start
    while current <= end:
        options = [
            candidate
            for candidate in by_start.get(current, [])
            if current <= int(candidate["level_end"]) <= end
        ]
        if not options and current == GAP_SOURCE["level_start"]:
            selected.append(GAP_SOURCE)
            current = int(GAP_SOURCE["level_end"]) + 1
            continue
        if not options:
            raise RuntimeError(f"No source begins at level {current}")
        exact_block = [
            candidate
            for candidate in options
            if int(candidate["level_end"]) == current + 19
        ]
        pool = exact_block or options
        chosen = min(
            pool,
            key=lambda candidate: (
                int(candidate["level_end"]) - int(candidate["level_start"]),
                int(candidate["channel_position"]),
            ),
        )
        selected.append(chosen)
        current = int(chosen["level_end"]) + 1
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=101)
    parser.add_argument("--end", type=int, default=5300)
    parser.add_argument(
        "--yt-dlp", type=Path, default=Path.home() / ".local" / "bin" / "yt-dlp"
    )
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).with_name("range_source_catalog.json")
    )
    args = parser.parse_args()

    candidates = fetch_channel_entries(args.yt_dlp)
    selected = select_sources(candidates, args.start, args.end)
    covered = sum(
        int(source["level_end"]) - int(source["level_start"]) + 1
        for source in selected
    )
    catalog = {
        "generated_at": datetime.now(UTC).isoformat(),
        "range": [args.start, args.end],
        "channel_url": CHANNEL_URL,
        "candidate_count": len(candidates),
        "selected_source_count": len(selected),
        "covered_levels": covered,
        "selection_policy": "Prefer exact 20-level blocks, then the smallest contiguous source",
        "sources": selected,
        "candidates": candidates,
    }
    args.output.write_text(json.dumps(catalog, indent=2) + "\n")
    print(
        json.dumps(
            {
                "sources": len(selected),
                "covered_levels": covered,
                "first": selected[0]["level_start"],
                "last": selected[-1]["level_end"],
            }
        )
    )


if __name__ == "__main__":
    main()
