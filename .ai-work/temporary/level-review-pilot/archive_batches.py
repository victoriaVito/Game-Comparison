"""Prepare and validate bounded local archive reviews; TASKS.md remains the tracker."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

PILOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PILOT))
from build_contact_sheets import build
from validate_reviews import read_records, require, validate_records


ROOT = PILOT.parents[2]
OUTPUT = ROOT / ".ai-work/temporary/level-review-archive"
ENDS = {"royal-match": 13500, "royal-kingdom": 5300}
PROGRESS_PREFIX = "Full archive workflow progress: "


def directory(game, start, end):
    require(game in ENDS, "Unsupported game")
    require(start >= 1001 and (start - 1) % 1000 == 0, "Expected post-pilot batch boundary")
    require(end == min(start + 999, ENDS[game]), "Unexpected batch end")
    return OUTPUT / game / f"batch-{start:05d}-{end:05d}"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")
    require(json.loads(path.read_text()) == value, f"Readback failed: {path}")


def prepare(game, start, end):
    target = directory(game, start, end)
    target.mkdir(parents=True, exist_ok=True)
    index_path = target / "sheets/index.json"
    if not index_path.exists():
        require(not (target / "sheets").exists(), "Incomplete sheet preparation: preserve and investigate")
        build(game, start, end, target / "sheets")
    index = json.loads(index_path.read_text())
    require(index["game"] == game and index["range"] == [start, end], "Existing index mismatch")
    chunks = []
    # Each reviewer gets at most 21 twelve-image sheets, not a whole 1,000-image context.
    for offset in range(0, len(index["sheets"]), 21):
        sheets = index["sheets"][offset:offset + 21]
        low = sheets[0]["records"][0]["level"]
        high = sheets[-1]["records"][-1]["level"]
        chunks.append({
            "start": low,
            "end": high,
            "sheets": [str((index_path.parent / s["sheet"]).relative_to(ROOT)) for s in sheets],
            "output": str((target / f"candidates-{low:05d}-{high:05d}.jsonl").relative_to(ROOT)),
        })
    return {
        "game": game, "start": start, "end": end,
        "directory": str(target.relative_to(ROOT)),
        "index": str(index_path.relative_to(ROOT)),
        "chunks": chunks,
        "available": index["available"],
        "missing": index["missing"],
    }


def validate_batch(game, start, end):
    target = directory(game, start, end)
    spec = prepare(game, start, end)
    rows = []
    for chunk in spec["chunks"]:
        shard = read_records(ROOT / chunk["output"])
        require(
            [row.get("level") for row in shard] == list(range(chunk["start"], chunk["end"] + 1)),
            f"Shard incomplete: {chunk['output']}",
        )
        rows.extend(shard)
    summary = validate_records(game, rows, ROOT / spec["index"], True)
    require(summary["available_images_have_recorded_inspection"], "Uninspected images remain")
    evidence_counts = Counter(r["observation"] for r in rows if r["inspection_status"] in ("reviewed", "partial"))
    summary.update({
        "range": [start, end],
        "review_status": "needs_review",
        "repeated_observations": [
            {"observation": text, "count": count}
            for text, count in evidence_counts.items() if count > 1
        ],
        "classification_complete": False,
    })
    write_json(target / "validation.json", summary)
    return summary


def normalize_sheet_paths(game, start, end):
    spec = prepare(game, start, end)
    index = json.loads((ROOT / spec["index"]).read_text())
    expected = {
        record["level"]: str((ROOT / spec["index"]).parent / sheet["sheet"])
        for sheet in index["sheets"] for record in sheet["records"]
    }
    staged, changes, all_rows = [], [], []
    for chunk in spec["chunks"]:
        path = ROOT / chunk["output"]
        rows = read_records(path)
        for row in rows:
            if row["inspection_status"] == "missing":
                continue
            canonical = str(Path(expected[row["level"]]).relative_to(ROOT))
            current = row["sheet_path"]
            if current != canonical:
                require(Path(current).is_absolute(), "Unexpected noncanonical relative sheet path")
                require(Path(current) == Path(expected[row["level"]]), "Sheet path targets different source")
                changes.append({"file": chunk["output"], "level": row["level"],
                                "old_sheet_path": current, "new_sheet_path": canonical})
                row["sheet_path"] = canonical
        staged.append((path, rows))
        all_rows.extend(rows)
    validate_records(game, all_rows, ROOT / spec["index"], True)
    if changes:
        audit = directory(game, start, end) / "sheet-path-repair.json"
        require(not audit.exists(), "Existing repair audit must be preserved")
        write_json(audit, {"changes": changes, "semantic_fields_changed": False})
        for path, rows in staged:
            text = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
            path.write_text(text)
            require(read_records(path) == rows, f"Repair readback failed: {path}")
    return {"game": game, "range": [start, end], "normalized_sheet_paths": len(changes)}


def quality_result(game, start, end):
    target = directory(game, start, end)
    summary = json.loads((target / "validation.json").read_text())
    quality = json.loads((target / "quality-review.json").read_text())
    require(quality.get("status") == "needs_review", "Quality review cannot accept labels")
    sample = quality.get("sample", [])
    require(isinstance(sample, list) and len(sample) >= min(12, end - start + 1), "Quality sample incomplete")
    require(len({r.get("level") for r in sample}) == len(sample), "Duplicate sampled levels")
    index = json.loads((target / "sheets/index.json").read_text())
    sources = {record["level"]: record for sheet in index["sheets"] for record in sheet["records"]}
    for item in sample:
        require(type(item.get("level")) is int and start <= item["level"] <= end, "Quality sample range")
        require(item.get("result") in ("supported", "conflict", "uncertain"), "Quality sample result")
        require(isinstance(item.get("evidence"), str) and item["evidence"].strip(), "Quality evidence missing")
        image_path = ROOT / item.get("image_path", "")
        require(image_path.resolve().is_relative_to(ROOT.resolve()) and image_path.is_file(), "Quality image reference")
        require(item["image_path"] == sources[item["level"]].get("image"), "Quality level/image mismatch")
    summary["quality_review"] = {
        "sample_size": len(sample),
        "results": dict(Counter(r["result"] for r in sample)),
        "limitation": "Sampled review is not full independent geometry validation.",
    }
    write_json(target / "validation.json", summary)
    return summary


def update_tracker():
    tracker = ROOT / "TASKS.md"
    summaries = []
    if OUTPUT.exists():
        for path in sorted(OUTPUT.glob("*/batch-*/validation.json")):
            value = json.loads(path.read_text())
            summaries.append(f"{value['game']} {value['range'][0]}-{value['range'][1]}")
    timestamp = datetime.now(timezone.utc).isoformat()
    line = (
        PROGRESS_PREFIX + f"{timestamp}; {len(summaries)} post-pilot batches structurally validated"
        + (f" ({'; '.join(summaries)})." if summaries else ".")
        + " Labels remain unaccepted; quality conflicts are retained in per-batch reports."
        + " Source of truth: TSK-002. No linked remote task ID is configured; no remote sync is claimed."
    )
    text = tracker.read_text()
    require(text.count(PROGRESS_PREFIX) == 1, "Expected one existing workflow milestone line")
    lines = text.splitlines(keepends=True)
    updated = "".join(line + "\n" if item.startswith(PROGRESS_PREFIX) else item for item in lines)
    tracker.write_text(updated)
    require(line in tracker.read_text(), "Tracker readback failed")
    return {"task": "TSK-002", "status": "in_progress", "validated_post_pilot_batches": len(summaries)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "normalize", "validate", "quality", "track"))
    parser.add_argument("--game", choices=ENDS)
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()
    if args.action == "track":
        result = update_tracker()
    else:
        require(args.game is not None and args.start is not None and args.end is not None, "Batch arguments required")
        result = {"prepare": prepare, "normalize": normalize_sheet_paths,
                  "validate": validate_batch, "quality": quality_result}[args.action](
            args.game, args.start, args.end
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
