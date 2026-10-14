import hashlib
import json
import sys
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-kingdom/batch-02001-03000")
OUTPUT = BASE / "candidates-02001-02252.jsonl"
CHECKPOINT = BASE / "candidates-02001-02252-checkpoint.json"
CONTRACT = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
INDEX = json.loads((BASE / "sheets/index.json").read_text())
MANIFEST = {
    record["level"]: (sheet["sheet"], record)
    for sheet in INDEX["sheets"] for record in sheet["records"]
}


def validate(rows):
    assert [r["level"] for r in rows] == list(range(2001, 2001 + len(rows)))
    for row in rows:
        assert set(row) == set(CONTRACT["record_fields"])
        assert type(row["schema_version"]) is int and row["schema_version"] == 2
        assert row["review_status"] == "needs_review"
        assert set(row["geometry_tags"]) <= set(CONTRACT["geometry_tags"])
        assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
        assert row["verified_evidence"] == []
        assert row["difficulty_hypothesis"] is row["strategy_hypothesis"] is None
        sheet, source = MANIFEST[row["level"]]
        assert row["image_path"] == source["image"]
        assert row["image_sha256"] == source["sha256"]
        assert hashlib.sha256(Path(source["image"]).read_bytes()).hexdigest() == source["sha256"]
        assert row["sheet_path"] == str(BASE / "sheets" / sheet)
        assert row["cell"] == source["cell"]


rows = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
if len(sys.argv) > 1 and sys.argv[1] == "validate":
    validate(rows)
    assert len(rows) == 252
    print(json.dumps({"rows": len(rows), "reviewed": sum(r["inspection_status"] == "reviewed" for r in rows),
                      "partial": sum(r["inspection_status"] == "partial" for r in rows),
                      "sheets": len({r["sheet_path"] for r in rows})}))
else:
    for batch in json.load(sys.stdin):
        new_rows = []
        for item in batch:
            level = 2001 + len(rows) + len(new_rows)
            sheet, source = MANIFEST[level]
            observation, tags, *extra = item
            partial = bool(extra and extra[0])
            new_rows.append({
                "schema_version": 2, "game": "royal-kingdom", "level": level,
                "review_status": "needs_review", "inspection_status": "partial" if partial else "reviewed",
                "image_path": source["image"], "image_sha256": source["sha256"],
                "sheet_path": str(BASE / "sheets" / sheet), "cell": source["cell"],
                "geometry_tags": tags, "observation": observation,
                "occlusion": "partial" if partial else "none", "confidence": "low" if partial else "medium",
                "verified_difficulty": "unknown", "verified_strategy": "unknown", "verified_evidence": [],
                "difficulty_hypothesis": None, "strategy_hypothesis": None,
                "review_note": "Animation or foreground overlay obscures some cells; revisit the original image. Geometry describes only the visible boundary."
                if partial else "Contact-sheet visual evidence only; blocker identities and small cell details may require original-resolution review. Covered cells are not treated as empty gaps."
            })
        assert len(new_rows) == 12
        assert len({r["sheet_path"] for r in new_rows}) == 1
        validate(rows + new_rows)
        with OUTPUT.open("a") as stream:
            for row in new_rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
        rows.extend(new_rows)
        CHECKPOINT.write_text(json.dumps({
            "range": [2001, 2252], "saved_rows": len(rows), "last_saved_level": rows[-1]["level"],
            "inspected_sheets": list(dict.fromkeys(r["sheet_path"] for r in rows)),
            "reviewed": sum(r["inspection_status"] == "reviewed" for r in rows),
            "partial": sum(r["inspection_status"] == "partial" for r in rows),
            "status": "complete" if len(rows) == 252 else "in_progress"
        }, indent=2) + "\n")
        print(f"Checkpointed {sheet}: {len(rows)} rows")
