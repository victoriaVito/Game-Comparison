import hashlib
import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-kingdom/batch-03001-04000")
output = base / "candidates-03505-03756.jsonl"
checkpoint = base / "candidates-03505-03756-checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
contract = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
records = {r["level"]: (s["sheet"], r) for s in manifest["sheets"] for r in s["records"]}
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
start = int(sys.argv[1])
observations = json.load(sys.stdin)
assert len(observations) == 12
assert start == (existing[-1]["level"] + 1 if existing else 3505)
assert start + 11 <= 3756
rows = []
for level, details in enumerate(observations, start):
    observation, tags, *partial = details
    sheet, source = records[level]
    image = Path(source["image"])
    missing = not image.is_file()
    if not missing:
        assert hashlib.sha256(image.read_bytes()).hexdigest() == source["sha256"]
    obscured = bool(partial and partial[0])
    row = dict(
        schema_version=2, game="royal-kingdom", level=level,
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if obscured else "reviewed",
        image_path=None if missing else source["image"],
        image_sha256=None if missing else source["sha256"],
        sheet_path=str(base / "sheets" / sheet), cell=source["cell"],
        geometry_tags=[] if missing else tags,
        observation="Source image is missing." if missing else observation,
        occlusion="unknown" if missing else "partial" if obscured else "none",
        confidence="unknown" if missing else "low" if obscured else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Animation or overlay hides cells; original-resolution follow-up needed." if obscured else
        "Sheet-scale visual evidence only; blocker identities and fine cell boundaries remain unverified. No local difficulty or strategy evidence cited."
    )
    assert set(row) == set(contract["record_fields"])
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    rows.append(row)
with output.open("a") as handle:
    for row in rows:
        handle.write(json.dumps(row) + "\n")
all_rows = existing + rows
checkpoint.write_text(json.dumps({
    "last_completed_level": start + 11,
    "inspected_sheets": len(all_rows) // 12,
    "inspected_images": sum(r["inspection_status"] in ("reviewed", "partial") for r in all_rows),
    "reviewed": sum(r["inspection_status"] == "reviewed" for r in all_rows),
    "partial": sum(r["inspection_status"] == "partial" for r in all_rows),
    "missing": sum(r["inspection_status"] == "missing" for r in all_rows)
}, indent=2) + "\n")
print(f"Saved and checkpointed {start}-{start + 11}")
