import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-04001-05000")
output = base / "candidates-04505-04756.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
observations = json.loads(sys.stdin.read())
sheet = next(s for s in index["sheets"] if s["sheet"] == f"levels-{start}-{start+11}.jpg")
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert len(observations) == 12
assert not any(start <= r["level"] <= start + 11 for r in existing)
rows = []
for entry, description in zip(sheet["records"], observations):
    level = entry["level"]
    assert start <= level <= start + 11
    missing = not entry.get("image")
    partial = description.startswith("PARTIAL:") if description else False
    text = description.removeprefix("PARTIAL:").strip() if description else "The sheet explicitly marks this level MISSING SOURCE; no board image is available."
    rows.append(dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=entry.get("image"), image_sha256=entry.get("sha256"),
        sheet_path=str(base / "sheets" / sheet["sheet"]), cell=entry["cell"],
        geometry_tags=[], observation=text,
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="No image evidence." if missing else "Geometry labels withheld; thumbnail evidence supports the described arrangement but not precise cell connectivity. No local difficulty or strategy citation."
    ))
with output.open("a") as stream:
    for row in rows:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
all_rows = existing + rows
(base / "candidates-04505-04756-checkpoint.json").write_text(json.dumps({
    "last_inspected_sheet": sheet["sheet"],
    "saved_rows": len(all_rows),
    "reviewed": sum(r["inspection_status"] == "reviewed" for r in all_rows),
    "partial": sum(r["inspection_status"] == "partial" for r in all_rows),
    "missing": sum(r["inspection_status"] == "missing" for r in all_rows),
    "inspected_sheets": sorted({r["sheet_path"] for r in all_rows}),
}, indent=2) + "\n")
