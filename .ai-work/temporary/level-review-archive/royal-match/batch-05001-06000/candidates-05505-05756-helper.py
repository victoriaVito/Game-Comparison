import json
import sys
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-match/batch-05001-06000")
OUTPUT = BASE / "candidates-05505-05756.jsonl"
CHECKPOINT = BASE / "candidates-05505-05756-checkpoint.json"
manifest = json.loads((BASE / "sheets/index.json").read_text())
start = int(sys.argv[1])
sheet = f"levels-{start}-{start + 11}.jpg"
entries = next(s["records"] for s in manifest["sheets"] if s["sheet"] == sheet)
notes = json.loads(sys.stdin.read())
assert len(notes) == 12
rows = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
assert not rows or rows[-1]["level"] == start - 1
for offset, note in enumerate(notes):
    level = start + offset
    entry = next((r for r in entries if r["level"] == level), None)
    missing = entry is None or not entry.get("image") or not entry.get("sha256")
    observation, tags, partial = note
    row = dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=None if missing else entry["image"],
        image_sha256=None if missing else entry["sha256"],
        sheet_path=str(BASE / "sheets" / sheet), cell=offset + 1 if entry is None else entry.get("cell"),
        geometry_tags=[] if missing else tags,
        observation="No source image is available; the inspected sheet shows a missing placeholder." if missing else observation,
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Source missing in sheet manifest." if missing else
        "Visible covering obscures underlying cells; original-resolution follow-up required. No local difficulty or strategy evidence." if partial else
        "Contact-sheet inspection only; blocker cells are not empty gaps. No local difficulty or strategy evidence.",
    )
    if not missing and not tags:
        row["review_note"] += " Geometry tags withheld: visible coverings or connecting cells do not clearly establish a taxonomy label."
    rows.append(row)
with OUTPUT.open("a") as handle:
    for row in rows[-12:]:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
progress = dict(
    game="royal-match", assigned_range=[5505, 5756],
    last_checkpointed_level=start + 11,
    inspected_sheets=[f"levels-{n}-{n + 11}.jpg" for n in range(5505, start + 1, 12)],
    rows_saved=len(rows),
    inspection_counts={status: sum(r["inspection_status"] == status for r in rows)
                       for status in ["reviewed", "partial", "missing", "not_reviewed"]},
)
CHECKPOINT.write_text(json.dumps(progress, indent=2) + "\n")
print(json.dumps(progress))
