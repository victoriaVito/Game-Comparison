import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-05001-06000")
output = base / "candidates-05001-05252.jsonl"
manifest = json.loads((base / "sheets/index.json").read_text())
entries = {r["level"]: (s["sheet"], r) for s in manifest["sheets"] for r in s["records"]}
start = int(sys.argv[1])
notes = json.loads(sys.stdin.read())
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not existing or existing[-1]["level"] == start - 1
for offset, note in enumerate(notes):
    level = start + offset
    sheet, entry = entries[level]
    observation, tags, *partial = note
    missing = not entry.get("image") or not Path(entry["image"]).is_file()
    row = dict(schema_version=2, game="royal-match", level=level,
               review_status="needs_review",
               inspection_status="missing" if missing else "partial" if partial else "reviewed",
               image_path=None if missing else entry["image"],
               image_sha256=None if missing else entry["sha256"],
               sheet_path=str(base / "sheets" / sheet), cell=entry["cell"],
               geometry_tags=[] if missing else tags,
               observation=observation, occlusion="unknown" if missing else "partial" if partial else "none",
               confidence="unknown" if missing else "low" if partial else "medium",
               verified_difficulty="unknown", verified_strategy="unknown",
               verified_evidence=[], difficulty_hypothesis=None, strategy_hypothesis=None,
               review_note="No local difficulty or strategy evidence; fine blocker identities require original-resolution follow-up." +
               (" Overlay obscures cells; hidden connectivity is not inferred." if partial else ""))
    existing.append(row)
with output.open("w") as stream:
    for row in existing:
        stream.write(json.dumps(row) + "\n")
checkpoint = dict(last_level=existing[-1]["level"], saved_rows=len(existing),
                  inspected_sheets=sorted({r["sheet_path"] for r in existing if r["inspection_status"] in ("reviewed", "partial")}))
(base / "candidates-05001-05252.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(f"Saved through {existing[-1]['level']}: {len(existing)} rows")
