from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REVIEWS_ROOT = PROJECT_ROOT / "reviews"
BLOCK_SIZE = 100
SAMPLE_SIZE = 40
REVIEW_NAME_PATTERN = re.compile(r"review-(\d{4})-(\d{4})\.json$")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Finalize one visually inspected stratified review block."
    )
    parser.add_argument("--block-start", type=int, required=True)
    parser.add_argument("--review-cache", type=Path, required=True)
    parser.add_argument("--exception-level", type=int, action="append", default=[])
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    start = args.block_start
    end = start + BLOCK_SIZE - 1
    if start < 1 or (start - 1) % BLOCK_SIZE:
        parser.error("block-start must be 1, 101, 201, ...")
    exceptions = sorted(set(args.exception_level))
    if any(level < start or level > end for level in exceptions):
        parser.error(f"exception levels must be inside {start}-{end}")

    contact_sheet = args.review_cache / f"review-{start:04d}-{end:04d}.jpg"
    metadata_path = args.review_cache / "sample-metadata.json"
    if not contact_sheet.is_file() or contact_sheet.read_bytes()[:3] != b"\xff\xd8\xff":
        raise RuntimeError(f"Missing or invalid contact sheet: {contact_sheet}")
    metadata = load_json(metadata_path)
    blocks = metadata.get("blocks", [])
    block = next(
        (item for item in blocks if int(item["block_start"]) == start),
        None,
    )
    if block is None or len(block["samples"]) != SAMPLE_SIZE:
        raise RuntimeError(f"Expected {SAMPLE_SIZE} selected levels for {start}-{end}")
    sample_levels = [int(sample["level"]) for sample in block["samples"]]
    if sample_levels != sorted(set(sample_levels)):
        raise RuntimeError(f"Invalid sample sequence for {start}-{end}")

    subreviews: list[tuple[Path, dict[str, object]]] = []
    covered_levels: list[int] = []
    for path in sorted(REVIEWS_ROOT.glob("review-*.json")):
        match = REVIEW_NAME_PATTERN.fullmatch(path.name)
        if match is None:
            continue
        sub_start, sub_end = (int(value) for value in match.groups())
        if sub_start < start or sub_end > end:
            continue
        review = load_json(path)
        if review.get("reviewed_levels") != list(range(sub_start, sub_end + 1)):
            raise RuntimeError(f"Invalid reviewed level sequence: {path}")
        subreviews.append((path, review))
        covered_levels.extend(review["reviewed_levels"])
    if sorted(covered_levels) != list(range(start, end + 1)):
        raise RuntimeError(f"Review files do not partition {start}-{end} exactly")

    if args.dry_run:
        print(json.dumps({"validated": [start, end], "sample_size": len(sample_levels)}))
        return

    for path, review in subreviews:
        review["visual_review"] = "stratified_sample_passed"
        path.write_text(json.dumps(review, indent=2) + "\n")

    result = "passed_after_recapture" if exceptions else "passed"
    summary = {
        "reviewed_at": datetime.now(UTC).date().isoformat(),
        "review_scope": f"Royal Kingdom stratified sample for levels {start}-{end}",
        "result": result,
        "sample_size": SAMPLE_SIZE,
        "accepted_count": SAMPLE_SIZE,
        "detected_exception_levels": exceptions,
        "resolved_exception_levels": exceptions,
        "ambiguous_levels": [],
        "failed_count": 0,
        "missing_count": 0,
        "selection_policy": "Every multiple of 5 plus offsets 3, 7, 11, and 19 in each 20-level sub-block",
        "resolution": args.resolution,
        "contact_sheet": str(contact_sheet.resolve()),
        "sample_metadata": str(metadata_path.resolve()),
    }
    output = REVIEWS_ROOT / f"review-sample-{start:04d}-{end:04d}.json"
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"finalized": [start, end], "result": result, "output": str(output)}))


if __name__ == "__main__":
    main()
