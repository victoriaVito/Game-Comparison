import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-01001-01252.jsonl"
contract = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((base / "sheets/index.json").read_text())
manifest = {r["level"]: (s["sheet"], r) for s in index["sheets"] for r in s["records"]}
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
start = int(sys.argv[1])
entries = json.load(sys.stdin)
assert start == 1001 + len(existing)
assert len(entries) == 12
for level, entry in enumerate(entries, start):
    observation, tags = entry[:2]
    sheet, source = manifest[level]
    present = pathlib.Path(source["image"]).is_file()
    partial = len(entry) > 2 and entry[2] == "partial"
    row = {
        "schema_version": 2, "game": "royal-kingdom", "level": level,
        "review_status": "needs_review",
        "inspection_status": ("partial" if partial else "reviewed") if present else "missing",
        "image_path": source["image"] if present else None,
        "image_sha256": source["sha256"] if present else None,
        "sheet_path": str(base / "sheets" / sheet), "cell": source["cell"],
        "geometry_tags": tags if present else [],
        "observation": observation if present else "Original image is missing.",
        "occlusion": ("partial" if partial else "none") if present else "unknown",
        "confidence": ("low" if partial else "medium") if present else "unknown",
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
        "review_note": "Contact-sheet visual evidence only; covered cells count as grid, not empty gaps. Fine blocker identities and hidden mechanics are unverified."
    }
    if not tags and present:
        row["review_note"] += " Geometry labels withheld where the visible silhouette is ambiguous."
    assert set(row) == set(contract["record_fields"])
    assert all(t in contract["geometry_tags"] for t in tags)
    existing.append(row)
with output.open("a") as f:
    for row in existing[-12:]:
        f.write(json.dumps(row) + "\n")
checkpoint = {"last_saved_level": existing[-1]["level"], "saved_rows": len(existing),
              "inspected_sheets": [s["sheet"] for s in index["sheets"] if all(r["level"] in {x["level"] for x in existing} for r in s["records"])],
              "status": "complete" if existing[-1]["level"] == 1252 else "in_progress"}
(base / "candidates-01001-01252-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps(checkpoint))
