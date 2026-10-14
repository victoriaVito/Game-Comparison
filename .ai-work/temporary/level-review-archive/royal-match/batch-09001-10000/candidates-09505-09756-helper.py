import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
BATCH = Path(__file__).resolve().parent
INDEX = BATCH / "sheets" / "index.json"
OUTPUT = BATCH / "candidates-09505-09756.jsonl"
CHECKPOINT = BATCH / "candidates-09505-09756.checkpoint.json"
ALLOWED_TAGS = {
    "compact_full_field",
    "split_regions",
    "layered_bands",
    "edge_channels",
    "central_mass",
    "open_center",
    "stair_step",
    "asymmetric",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", required=True)
    args = parser.parse_args()
    descriptions = json.load(sys.stdin)
    index = json.loads(INDEX.read_text())
    sheet = next(item for item in index["sheets"] if item["sheet"] == args.sheet)
    source_by_level = {item["level"]: item for item in sheet["records"]}
    levels = sorted(source_by_level)
    if len(descriptions) != len(levels):
        raise ValueError(f"{args.sheet}: expected {len(levels)} descriptions")

    existing = {}
    if OUTPUT.exists():
        for line in OUTPUT.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                existing[row["level"]] = row
    added = []
    for level, detail in zip(levels, descriptions):
        if level in existing:
            continue
        source = source_by_level[level]
        missing = source.get("image") is None or source["status"].startswith("missing")
        tags = detail.get("tags", [])
        if not set(tags) <= ALLOWED_TAGS:
            raise ValueError(f"{level}: unsupported tag")
        if missing:
            row = {
                "schema_version": 2,
                "game": "royal-match",
                "level": level,
                "review_status": "needs_review",
                "inspection_status": "missing",
                "image_path": None,
                "image_sha256": None,
                "sheet_path": None,
                "cell": None,
                "geometry_tags": [],
                "observation": "",
                "occlusion": "unknown",
                "confidence": "unknown",
                "verified_difficulty": "unknown",
                "verified_strategy": "unknown",
                "verified_evidence": [],
                "difficulty_hypothesis": None,
                "strategy_hypothesis": None,
                "review_note": "No local source image is present in the prepared index.",
            }
        else:
            row = {
                "schema_version": 2,
                "game": "royal-match",
                "level": level,
                "review_status": "needs_review",
                "inspection_status": "reviewed",
                "image_path": source["image"],
                "image_sha256": source["sha256"],
                "sheet_path": str((BATCH / "sheets" / args.sheet).relative_to(ROOT)),
                "cell": source["cell"],
                "geometry_tags": tags,
                "observation": detail["observation"],
                "occlusion": "none",
                "confidence": detail.get("confidence", "medium"),
                "verified_difficulty": "unknown",
                "verified_strategy": "unknown",
                "verified_evidence": [],
                "difficulty_hypothesis": None,
                "strategy_hypothesis": None,
                "review_note": detail.get(
                    "review_note",
                    "Image-specific visual candidate; geometry vocabulary remains unaccepted.",
                ),
            }
        added.append(row)
        existing[level] = row

    expected = list(range(9505, 9757))
    ordered_levels = sorted(existing)
    if any(level not in expected for level in existing):
        raise ValueError("Existing output contains rows outside the assigned range")
    OUTPUT.write_text("".join(json.dumps(existing[n], ensure_ascii=False) + "\n" for n in ordered_levels))

    checkpoint = json.loads(CHECKPOINT.read_text()) if CHECKPOINT.exists() else {
        "assigned_range": [9505, 9756],
        "reviewed_sheets": [],
        "record_count": 0,
        "checkpoint_rule": "Updated after each inspected sheet; only reviewed source images are counted.",
    }
    if args.sheet not in checkpoint["reviewed_sheets"]:
        checkpoint["reviewed_sheets"].append(args.sheet)
    checkpoint["reviewed_sheets"].sort()
    checkpoint["record_count"] = len(existing)
    checkpoint["output_sha256"] = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    CHECKPOINT.write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(json.dumps({
        "sheet": args.sheet,
        "new_rows": len(added),
        "total_rows": len(existing),
        "checkpoint_sheets": len(checkpoint["reviewed_sheets"]),
    }))


if __name__ == "__main__":
    main()
