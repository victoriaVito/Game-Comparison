import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-03253-03504.jsonl"
if sys.argv[1] == "--normalize-sheet-paths":
    records = [json.loads(line) for line in output.read_text().splitlines()]
    for record in records:
        path = pathlib.Path(record["sheet_path"])
        if path.is_absolute():
            record["sheet_path"] = str(path.relative_to(pathlib.Path.cwd()))
    output.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))
    print(f"Normalized only sheet_path values in {len(records)} saved rows.")
    sys.exit(0)
contract = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
manifest = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
sheet = next(s for s in manifest["sheets"] if s["records"][0]["level"] == start)
lines = sys.stdin.read().strip().splitlines()
assert len(lines) == len(sheet["records"]) == 12
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not any(start <= r["level"] < start + 12 for r in existing)
assert start == 3253 + len(existing)
rows = []
for source, line in zip(sheet["records"], lines):
    tags, observation = line.split("|", 1)
    partial = tags.startswith("!")
    tags = tags.lstrip("!")
    missing = not source.get("image") or not pathlib.Path(source["image"]).exists()
    row = dict(
        schema_version=2, game="royal-kingdom", level=source["level"],
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=None if missing else source["image"],
        image_sha256=None if missing else source["sha256"],
        sheet_path=str(base / "sheets" / sheet["sheet"]), cell=source["cell"],
        geometry_tags=[] if missing else tags.split(",") if tags else [],
        observation="Source image missing." if missing else observation.strip(),
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="No local difficulty or strategy evidence. " + (
            "Overlay obscures cells; inspect original resolution before interpreting hidden geometry."
            if partial else "Geometry reflects visible board boundaries, not inferred connectivity through blockers; fine mechanic identities remain unverified."
        ),
    )
    assert set(row) == set(contract["record_fields"])
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    rows.append(row)
with output.open("a") as stream:
    for row in rows:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
checkpoint = base / "candidates-03253-03504-checkpoint.json"
checkpoint.write_text(json.dumps({
    "range": [3253, 3504], "last_saved_level": start + 11,
    "inspected_sheets": [s["sheet"] for s in manifest["sheets"] if 3253 <= s["records"][0]["level"] <= start],
    "saved_rows": len(existing) + len(rows),
    "reviewed": sum(r["inspection_status"] == "reviewed" for r in existing + rows),
    "partial": sum(r["inspection_status"] == "partial" for r in existing + rows),
    "missing": sum(r["inspection_status"] == "missing" for r in existing + rows),
}, indent=2) + "\n")
print(f"Saved and checkpointed {start}-{start + 11}; total rows {len(existing) + 12}")
