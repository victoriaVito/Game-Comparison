import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-02001-02252.jsonl"
manifest = json.loads((base / "sheets/index.json").read_text())
contract = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
start = int(sys.argv[1])
sheet = next(s for s in manifest["sheets"] if s["records"][0]["level"] == start)
observations = sys.stdin.read().strip().splitlines()
assert len(observations) == len(sheet["records"])
existing = [json.loads(s) for s in output.read_text().splitlines()] if output.exists() else []
assert not any(start <= r["level"] <= start + 11 for r in existing)
rows = []
for entry, text in zip(sheet["records"], observations):
    observation, _, tags = text.partition("|")
    missing = not entry.get("image") or not pathlib.Path(entry["image"]).is_file()
    partial = observation.startswith("PARTIAL: ")
    row = dict(schema_version=2, game="royal-match", level=entry["level"],
               review_status="needs_review", inspection_status="missing" if missing else "partial" if partial else "reviewed",
               image_path=None if missing else entry["image"], image_sha256=None if missing else entry["sha256"],
               sheet_path=str(base / "sheets" / sheet["sheet"]), cell=entry["cell"],
               geometry_tags=[] if missing else [s for s in tags.split(",") if s],
               observation="Source image missing." if missing else observation.removeprefix("PARTIAL: "),
               occlusion="unknown" if missing else "partial" if partial else "none",
               confidence="unknown" if missing else "low" if partial else "medium",
               verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
               difficulty_hypothesis=None, strategy_hypothesis=None,
               review_note="Sheet-scale visual evidence only; blocker identity and covered-cell connectivity require original-resolution confirmation. No local difficulty or strategy evidence cited.")
    assert set(row) == set(contract["record_fields"])
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    rows.append(row)
with output.open("a") as stream:
    for row in rows:
        stream.write(json.dumps(row) + "\n")
checkpoint = base / "candidates-02001-02252-checkpoint.json"
all_rows = existing + rows
checkpoint.write_text(json.dumps(dict(inspected_sheets=[s["sheet"] for s in manifest["sheets"] if any(r["sheet_path"].endswith(s["sheet"]) for r in all_rows)], saved_rows=len(all_rows), last_saved_level=rows[-1]["level"], inspection_counts={state: sum(r["inspection_status"] == state for r in all_rows) for state in ["reviewed", "partial", "missing"]}), indent=2) + "\n")
print(f"Checkpoint: {start}-{rows[-1]['level']}; {len(all_rows)} rows saved")
