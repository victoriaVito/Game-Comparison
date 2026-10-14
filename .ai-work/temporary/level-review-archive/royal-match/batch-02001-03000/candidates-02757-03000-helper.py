import json
import sys
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-match/batch-02001-03000")
OUT = BASE / "candidates-02757-03000.jsonl"
CHECKPOINT = BASE / "candidates-02757-03000-checkpoint.json"
manifest = json.loads((BASE / "sheets/index.json").read_text())
sheet_name = sys.argv[1]
sheet = next(s for s in manifest["sheets"] if s["sheet"] == sheet_name)
observations = json.load(sys.stdin)
assert len(observations) == len(sheet["records"])
existing = [json.loads(line) for line in OUT.read_text().splitlines()] if OUT.exists() else []
assert not any(r["sheet_path"] == str(BASE / "sheets" / sheet_name) for r in existing)
rows = []
for source, evidence in zip(sheet["records"], observations):
    level = source["level"]
    assert 2757 <= level <= 3000
    tags, observation = evidence[:2]
    partial = len(evidence) > 2 and evidence[2] == "partial"
    missing = not source.get("image") or not Path(source["image"]).is_file()
    rows.append({
        "schema_version": 2,
        "game": "royal-match",
        "level": level,
        "review_status": "needs_review",
        "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
        "image_path": None if missing else source["image"],
        "image_sha256": None if missing else source["sha256"],
        "sheet_path": str(BASE / "sheets" / sheet_name),
        "cell": source["cell"],
        "geometry_tags": [] if missing else tags,
        "observation": "Source image missing." if missing else observation,
        "occlusion": "unknown" if missing else "partial" if partial else "none",
        "confidence": "unknown" if missing else "low" if partial else "medium",
        "verified_difficulty": "unknown",
        "verified_strategy": "unknown",
        "verified_evidence": [],
        "difficulty_hypothesis": None,
        "strategy_hypothesis": None,
        "review_note": "Visual sheet evidence only; small blocker identities and covered-cell contents require original-resolution confirmation."
            if not partial else "Overlay obscures cells; geometry is limited to visible portions. Original-resolution follow-up required.",
    })
assert not existing or rows[0]["level"] == existing[-1]["level"] + 1
with OUT.open("a") as handle:
    for row in rows:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
all_rows = existing + rows
CHECKPOINT.write_text(json.dumps({
    "range": [2757, 3000],
    "last_saved_level": all_rows[-1]["level"],
    "inspected_sheets": list(dict.fromkeys(r["sheet_path"] for r in all_rows)),
    "saved_rows": len(all_rows),
    "inspection_counts": {status: sum(r["inspection_status"] == status for r in all_rows)
        for status in ["reviewed", "partial", "missing"]},
}, indent=2) + "\n")
print(f"Saved {sheet_name}: {len(rows)} rows; cumulative {len(all_rows)}")
