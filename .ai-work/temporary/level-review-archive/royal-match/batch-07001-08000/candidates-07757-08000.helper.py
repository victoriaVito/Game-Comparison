import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
OUTPUT = BASE / "candidates-07757-08000.jsonl"
CHECKPOINT = BASE / "candidates-07757-08000.checkpoint.json"
INDEX = json.loads((BASE / "sheets/index.json").read_text())
FIELDS = set(json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["record_fields"])
manifest = {record["level"]: (sheet["sheet"], record) for sheet in INDEX["sheets"] for record in sheet["records"]}
rows = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
existing = {row["level"] for row in rows}
for sheet_observations in json.load(sys.stdin):
    sheet_names = set()
    for level, observation, tags, *partial in sheet_observations:
        assert 7757 <= level <= 8000 and level not in existing
        sheet, record = manifest[level]
        sheet_names.add(sheet)
        available = "image" in record and pathlib.Path(record["image"]).is_file()
        row = dict(
            schema_version=2, game="royal-match", level=level,
            review_status="needs_review",
            inspection_status=("partial" if partial else "reviewed") if available else "missing",
            image_path=record.get("image") if available else None,
            image_sha256=record.get("sha256") if available else None,
            sheet_path=(BASE / "sheets" / sheet).as_posix(), cell=record["cell"],
            geometry_tags=tags if available else [], observation=observation,
            occlusion=("partial" if partial else "none") if available else "unknown",
            confidence=("low" if partial else "medium") if available else "unknown",
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note=("Overlay hides cells; underlying geometry remains uncertain. " if partial else "")
            + "Visual sheet evidence only; blocker identities and small details may require original-resolution review. No local difficulty or strategy evidence."
        )
        assert set(row) == FIELDS
        rows.append(row)
        existing.add(level)
    assert len(sheet_names) == 1
    rows.sort(key=lambda row: row["level"])
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    checkpoint = dict(range=[7757, 8000], saved_rows=len(rows), last_sheet=next(iter(sheet_names)),
                      inspected_levels=[row["level"] for row in rows if row["inspection_status"] in ("reviewed", "partial")],
                      missing_levels=[row["level"] for row in rows if row["inspection_status"] == "missing"],
                      completed_sheets=sorted({pathlib.Path(row["sheet_path"]).name for row in rows}))
    CHECKPOINT.write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(f"Checkpoint: {checkpoint['last_sheet']}; {len(rows)} rows saved")
