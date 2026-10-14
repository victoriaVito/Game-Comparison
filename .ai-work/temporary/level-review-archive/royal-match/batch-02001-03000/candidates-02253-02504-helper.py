import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-02253-02504.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
manifest = {r["level"]: (s["sheet"], r) for s in index["sheets"] for r in s["records"]}
rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
start = int(sys.argv[1])
notes = sys.stdin.read().strip().splitlines()
assert len(notes) == 12
assert not any(start <= row["level"] < start + 12 for row in rows)
for level, note in enumerate(notes, start):
    tags, observation = note.split("|", 1)
    sheet, source = manifest[level]
    partial = observation.startswith("PARTIAL ")
    observation = observation.removeprefix("PARTIAL ")
    rows.append({
        "schema_version": 2, "game": "royal-match", "level": level,
        "review_status": "needs_review", "inspection_status": "partial" if partial else "reviewed",
        "image_path": source["image"], "image_sha256": source["sha256"],
        "sheet_path": (base / "sheets" / sheet).as_posix(), "cell": source["cell"],
        "geometry_tags": tags.split(",") if tags else [], "observation": observation,
        "occlusion": "partial" if partial else "none", "confidence": "low" if partial else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown", "verified_evidence": [],
        "difficulty_hypothesis": None, "strategy_hypothesis": None,
        "review_note": "Sheet-scale visual review; fine blocker identities and covered-cell connectivity require original-resolution follow-up. No local difficulty or strategy evidence."
    })
rows.sort(key=lambda row: row["level"])
root = pathlib.Path.cwd()
for row in rows:
    row["sheet_path"] = pathlib.Path(row["sheet_path"]).relative_to(root).as_posix() if pathlib.Path(row["sheet_path"]).is_absolute() else row["sheet_path"]
output.write_text("".join(json.dumps(row) + "\n" for row in rows))
checkpoint = {
    "inspected_sheets": sorted({row["sheet_path"] for row in rows}),
    "saved_rows": len(rows), "last_saved_level": rows[-1]["level"],
    "reviewed": sum(row["inspection_status"] == "reviewed" for row in rows),
    "partial": sum(row["inspection_status"] == "partial" for row in rows)
}
(base / "candidates-02253-02504-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps(checkpoint))
