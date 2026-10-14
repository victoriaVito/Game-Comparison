import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-07505-07756.jsonl"
contract = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
notes = json.loads(sys.stdin.read())
sheet = next(s for s in index["sheets"] if s["records"][0]["level"] == start)
assert len(notes) == len(sheet["records"])
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not existing or existing[-1]["level"] == start - 1
for record, note in zip(sheet["records"], notes):
    missing = "image" not in record
    observation, tags, partial = note if isinstance(note, list) else (note, [], False)
    row = dict(
        schema_version=2, game="royal-match", level=record["level"],
        review_status="needs_review", inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=record.get("image"), image_sha256=record.get("sha256"),
        sheet_path=(base / "sheets" / sheet["sheet"]).as_posix(), cell=record["cell"],
        geometry_tags=[] if missing else tags,
        observation="The inspected sheet cell says MISSING SOURCE; no board image is present." if missing else observation,
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Source absent from the manifest." if missing else
        "Visual candidate only. Fine blocker identities and covered-cell connectivity require original-resolution confirmation; no unsupported geometry or strategy is assigned."
        + (" The water or bright-effect overlay described in the observation obscures some cells." if partial else ""),
    )
    assert set(row) == set(contract["record_fields"])
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    existing.append(row)
with output.open("a") as stream:
    for row in existing[-12:]:
        stream.write(json.dumps(row) + "\n")
checkpoint = base / "candidates-07505-07756.checkpoint.json"
checkpoint.write_text(json.dumps({
    "last_saved_level": existing[-1]["level"],
    "sheets_inspected": [s["sheet"] for s in index["sheets"] if start >= s["records"][0]["level"] >= 7505],
    "saved_rows": len(existing),
    "reviewed": sum(r["inspection_status"] == "reviewed" for r in existing),
    "partial": sum(r["inspection_status"] == "partial" for r in existing),
    "missing": sum(r["inspection_status"] == "missing" for r in existing),
}, indent=2) + "\n")
print(f"Saved through {existing[-1]['level']}: {len(existing)} rows")
