from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "sources" / "royal-match-level-archive"
SCANNER_SOURCE = Path(__file__).with_name("scan_targets.swift")
SCANNER_BINARY = PROJECT_ROOT / "analysis" / ".build" / "scan-targets"


def compile_scanner() -> None:
    SCANNER_BINARY.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["swiftc", str(SCANNER_SOURCE), "-o", str(SCANNER_BINARY)],
        check=True,
    )


def scan_chunk(paths: list[Path]) -> list[dict[str, object]]:
    result = subprocess.run(
        [str(SCANNER_BINARY), *(str(path) for path in paths)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines() if line]


def chunks[T](values: list[T], size: int) -> list[list[T]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "analysis" / "features.json")
    args = parser.parse_args()

    manifest = json.loads((SOURCE_ROOT / "manifest.json").read_text())
    levels = manifest["levels"][: args.limit]
    paths = [SOURCE_ROOT / entry["board"] for entry in levels]

    compile_scanner()
    scans: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(scan_chunk, batch) for batch in chunks(paths, 100)]
        for future in concurrent.futures.as_completed(futures):
            scans.extend(future.result())

    scans_by_path = {Path(str(scan["path"])): scan for scan in scans}
    features = []
    for entry, path in zip(levels, paths, strict=True):
        scan = scans_by_path[path]
        tutorial = "tutorial_overlay" in entry.get("flags", [])
        features.append(
            {
                "level": entry["level"],
                "tutorial": tutorial,
                "level_type": "tutorial" if tutorial else "standard",
                "target_count": scan.get("targetCount"),
                "target_values": scan.get("values", []),
                "target_confidence": scan.get("confidence", 0.0),
                "target_method": scan.get("method", "unresolved"),
                "difficulty": "unknown",
                "pattern_status": "not_analyzed",
            }
        )

    summary = {
        "levels": len(features),
        "tutorials": sum(feature["tutorial"] for feature in features),
        "target_count_resolved": sum(feature["target_count"] is not None for feature in features),
        "target_count_unknown": sum(feature["target_count"] is None for feature in features),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "levels": features}, indent=2) + "\n")


if __name__ == "__main__":
    main()
