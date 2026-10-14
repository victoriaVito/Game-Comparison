import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-kingdom/batch-04001-05000")
output = base / "candidates-04001-04252.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
notes = json.loads(sys.argv[2])
sheet = next(s for s in index["sheets"] if s["records"][0]["level"] == start)
assert len(notes) == len(sheet["records"]) == 12
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not existing or existing[-1]["level"] == start - 1
rows = []
for source, note in zip(sheet["records"], notes):
    observation, tags, *partial = note
    occluded = bool(partial and partial[0])
    rows.append(dict(
        schema_version=2, game="royal-kingdom", level=source["level"],
        review_status="needs_review", inspection_status="partial" if occluded else "reviewed",
        image_path=source["image"], image_sha256=source["sha256"],
        sheet_path=str(base / "sheets" / sheet["sheet"]), cell=source["cell"],
        geometry_tags=tags, observation=observation,
        occlusion="partial" if occluded else "none", confidence="low" if occluded else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Overlay hides part of the grid; boundary interpretation is provisional." if occluded else
        "Contact-sheet visual evidence only; small blocker identities remain uncertain. No local difficulty or strategy evidence cited."
    ))
with output.open("a") as stream:
    for row in rows:
        stream.write(json.dumps(row) + "\n")
(base / "candidates-04001-04252.checkpoint.json").write_text(json.dumps({
    "last_level": rows[-1]["level"], "inspected_sheets": len(existing + rows) // 12,
    "inspected_images": len(existing + rows), "status": "in_progress" if start < 4241 else "complete"
}, indent=2) + "\n")
