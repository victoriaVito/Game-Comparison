import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-04253-04504.jsonl"
manifest = json.loads((base / "sheets/index.json").read_text())
lookup = {r["level"]: (s["sheet"], r) for s in manifest["sheets"] for r in s["records"]}
start = int(sys.argv[1])
notes = json.load(sys.stdin)
assert len(notes) == 12
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not existing or existing[-1]["level"] == start - 1
for offset, note in enumerate(notes):
    level = start + offset
    sheet, source = lookup[level]
    partial = len(note) > 2 and note[2]
    row = dict(schema_version=2, game="royal-kingdom", level=level,
               review_status="needs_review", inspection_status="partial" if partial else "reviewed",
               image_path=source["image"], image_sha256=source["sha256"],
               sheet_path=(base / "sheets" / sheet).as_posix(), cell=source["cell"],
               geometry_tags=note[0], observation=note[1],
               occlusion="partial" if partial else "none", confidence="low" if partial else "medium",
               verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
               difficulty_hypothesis=None, strategy_hypothesis=None,
               review_note="Overlay hides some cells; revisit original resolution." if partial else
               "Visible boundary and blocker placement only; mechanic identities and unseen cells remain unverified.")
    row["sheet_path"] = str(pathlib.Path(row["sheet_path"]).relative_to(pathlib.Path.cwd()))
    existing.append(row)
with output.open("w") as stream:
    for row in existing:
        stream.write(json.dumps(row) + "\n")
(base / "candidates-04253-04504-checkpoint.json").write_text(json.dumps({
    "last_saved_level": start + 11, "inspected_sheets": len(existing) // 12,
    "saved_rows": len(existing), "status": "complete" if start + 11 == 4504 else "in_progress"
}, indent=2) + "\n")
print(f"Saved {start}-{start+11}; total {len(existing)} rows")
