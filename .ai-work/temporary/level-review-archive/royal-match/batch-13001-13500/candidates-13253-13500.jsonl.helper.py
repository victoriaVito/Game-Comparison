import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-13001-13500")
output = base / "candidates-13253-13500.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
lookup = {
    r["level"]: (s["sheet"], r)
    for s in index["sheets"]
    for r in s["records"]
}
rows = {}
if output.exists():
    rows = {r["level"]: r for r in map(json.loads, output.read_text().splitlines())}
for line in sys.stdin.read().splitlines():
    if not line.strip():
        continue
    level, tags, observation, *extra = line.split("|")
    level = int(level)
    assert 13253 <= level <= 13500
    sheet, source = lookup[level]
    partial = bool(extra)
    row = dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review",
        inspection_status="partial" if partial else "reviewed",
        image_path=source["image"], image_sha256=source["sha256"],
        sheet_path=str(base / "sheets" / sheet), cell=source["cell"],
        geometry_tags=tags.split(",") if tags else [],
        observation=observation, occlusion="partial" if partial else "none",
        confidence="medium", verified_difficulty="unknown",
        verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note=extra[0] if partial else
        "Candidate Match vocabulary only; blocker identities and unseen mechanics are not verified.",
    )
    if level not in rows:
        rows[level] = row
    assigned = [
        r["level"] for s in index["sheets"] if s["sheet"] == sheet
        for r in s["records"] if 13253 <= r["level"] <= 13500
    ]
    if all(n in rows for n in assigned):
        output.write_text("".join(json.dumps(rows[n]) + "\n" for n in sorted(rows)))
        checkpoint = dict(
            last_sheet=sheet, saved_levels=sorted(rows),
            count=len(rows), status="needs_review",
            visual_evidence="Numbered sheets rendered with image view tools.",
        )
        (base / "candidates-13253-13500.jsonl.checkpoint.json").write_text(
            json.dumps(checkpoint, indent=2) + "\n"
        )
        print(f"Checkpoint {sheet}: {len(rows)} rows")
