import json
import sys
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-kingdom/batch-02001-03000")
OUT = BASE / "candidates-02505-02756.jsonl"
CHECKPOINT = BASE / "candidates-02505-02756-checkpoint.json"
manifest = json.loads((BASE / "sheets/index.json").read_text())
lookup = {r["level"]: (s["sheet"], r) for s in manifest["sheets"] for r in s["records"]}
rows = [json.loads(line) for line in OUT.read_text().splitlines()] if OUT.exists() else []
start = int(sys.argv[1])
observations = json.load(sys.stdin)
assert len(observations) == 12
assert not rows or rows[-1]["level"] == start - 1
for offset, item in enumerate(observations):
    level = start + offset
    sheet, source = lookup[level]
    assert Path(source["image"]).exists()
    observation, tags = item[:2]
    partial = len(item) > 2 and item[2]
    row = {
        "schema_version": 2, "game": "royal-kingdom", "level": level,
        "review_status": "needs_review",
        "inspection_status": "partial" if partial else "reviewed",
        "image_path": source["image"], "image_sha256": source["sha256"],
        "sheet_path": str(BASE / "sheets" / sheet), "cell": source["cell"],
        "geometry_tags": tags, "observation": observation,
        "occlusion": "partial" if partial else "none",
        "confidence": "low" if partial else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None,
        "strategy_hypothesis": None,
        "review_note": "Contact-sheet visual evidence only; small cell details and mechanics remain unverified. Tags withheld where boundary or connectivity is ambiguous."
    }
    with OUT.open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    rows.append(row)
CHECKPOINT.write_text(json.dumps({
    "assigned_range": [2505, 2756], "last_saved_level": rows[-1]["level"],
    "saved_rows": len(rows),
    "inspected_sheets": list(dict.fromkeys(r["sheet_path"] for r in rows)),
    "reviewed": sum(r["inspection_status"] == "reviewed" for r in rows),
    "partial": sum(r["inspection_status"] == "partial" for r in rows),
    "status": "complete" if rows[-1]["level"] == 2756 else "in_progress"
}, indent=2) + "\n")
print(f"Checkpoint: {len(rows)} rows through {rows[-1]['level']}")
