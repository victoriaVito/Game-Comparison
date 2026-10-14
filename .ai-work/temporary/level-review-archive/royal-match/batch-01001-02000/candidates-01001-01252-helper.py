import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-01001-01252.jsonl"
checkpoint = base / "candidates-01001-01252-checkpoint.json"
index = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
sheet = next(s for s in index["sheets"] if s["records"][0]["level"] == start)
notes = [line.split("|", 2) for line in sys.stdin.read().splitlines() if line]
assert len(notes) == len(sheet["records"]) == 12
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not existing or existing[-1]["level"] == start - 1
rows = []
for source, (status, tags, observation) in zip(sheet["records"], notes):
    assert status in ("reviewed", "partial")
    rows.append(dict(
        schema_version=2, game="royal-match", level=source["level"],
        review_status="needs_review", inspection_status=status,
        image_path=source["image"], image_sha256=source["sha256"],
        sheet_path=(base / "sheets" / sheet["sheet"]).as_posix(),
        cell=source["cell"], geometry_tags=tags.split(",") if tags else [],
        observation=observation, occlusion="severe" if status == "partial" else "none",
        confidence="low" if status == "partial" else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Visible overlay hides board cells; boundary and hidden contents remain unresolved."
        if status == "partial" else
        "Contact-sheet inspection only; fine blocker details require original-resolution review. Tags describe visible boundary or placement, not mechanics."
    ))
with output.open("a") as handle:
    for row in rows:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
all_rows = existing + rows
checkpoint.write_text(json.dumps(dict(
    inspected_sheets=[r["sheet_path"] for r in all_rows[::12]],
    inspected_levels=len(all_rows), last_level=all_rows[-1]["level"],
    reviewed=sum(r["inspection_status"] == "reviewed" for r in all_rows),
    partial=sum(r["inspection_status"] == "partial" for r in all_rows),
    complete=all_rows[-1]["level"] == 1252
), indent=2) + "\n")
print(f"Saved {start}-{rows[-1]['level']}; total {len(all_rows)}")
