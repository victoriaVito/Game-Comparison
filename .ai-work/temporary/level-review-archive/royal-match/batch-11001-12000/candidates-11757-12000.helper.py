import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-11001-12000")
output = base / "candidates-11757-12000.jsonl"
checkpoint = base / "candidates-11757-12000.checkpoint.json"
index = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
sheet = next(s for s in index["sheets"] if s["records"][0]["level"] == start)
evidence = json.load(sys.stdin)
assert len(evidence) == len(sheet["records"])
rows = {}
if output.exists():
    rows = {r["level"]: r for r in map(json.loads, output.read_text().splitlines())}
for source, item in zip(sheet["records"], evidence):
    level = source["level"]
    assert 11757 <= level <= 12000
    if level in rows:
        continue
    tags, observation = item[:2]
    note = item[2] if len(item) > 2 else "Candidate vocabulary only; mechanics and hidden cells are not verified."
    partial = len(item) > 3 and item[3]
    rows[level] = dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review", inspection_status="partial" if partial else "reviewed",
        image_path=source["image"], image_sha256=source["sha256"],
        sheet_path=str(base / "sheets" / sheet["sheet"]), cell=source["cell"],
        geometry_tags=tags, observation=observation,
        occlusion="partial" if partial else "none", confidence="medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None, review_note=note,
    )
output.write_text("".join(json.dumps(rows[n], ensure_ascii=False) + "\n" for n in sorted(rows)))
checkpoint.write_text(json.dumps({
    "saved_levels": sorted(rows), "count": len(rows),
    "last_inspected_sheet": str(base / "sheets" / sheet["sheet"]),
    "review_status": "needs_review", "complete": len(rows) == 244,
}, indent=2) + "\n")
print(f"Saved {start}-{sheet['records'][-1]['level']}; total {len(rows)}")
