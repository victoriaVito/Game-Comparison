import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-13001-13500")
output = base / "candidates-13001-13252.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
sheet_number = int(sys.argv[1])
sheet = index["sheets"][sheet_number - 1]
notes = json.load(sys.stdin)
assert len(notes) == len(sheet["records"]) == 12
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not existing or existing[-1]["level"] == sheet["records"][0]["level"] - 1
rows = []
for source, note in zip(sheet["records"], notes):
    assert 13001 <= source["level"] <= 13252
    tags, observation = note[:2]
    occlusion_note = note[2] if len(note) > 2 else None
    rows.append({
        "schema_version": 2, "game": "royal-match", "level": source["level"],
        "review_status": "needs_review",
        "inspection_status": "partial" if occlusion_note else "reviewed",
        "image_path": source["image"], "image_sha256": source["sha256"],
        "sheet_path": str(base / "sheets" / sheet["sheet"]), "cell": source["cell"],
        "geometry_tags": tags.split() if tags else [], "observation": observation,
        "occlusion": "partial" if occlusion_note else "none",
        "confidence": "low" if occlusion_note else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
        "review_note": occlusion_note or "Visual geometry candidate only; blocker identities and mechanics are unverified. Difficulty and strategy have no directly cited local evidence."
    })
with output.open("a") as handle:
    for row in rows:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
coverage = existing + rows
checkpoint = {
    "schema_version": 2, "game": "royal-match", "assigned_range": [13001, 13252],
    "saved_range": [coverage[0]["level"], coverage[-1]["level"]],
    "saved_rows": len(coverage), "last_inspected_sheet": sheet["sheet"],
    "inspected_sheets": sheet_number,
    "counts": {status: sum(row["inspection_status"] == status for row in coverage)
               for status in ["reviewed", "partial", "missing", "not_reviewed"]},
    "review_status": "needs_review", "complete": len(coverage) == 252
}
(base / "candidates-13001-13252.jsonl.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps(checkpoint))
