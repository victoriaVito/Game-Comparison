import json
import pathlib
import sys

BASE = pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-06001-07000")
OUTPUT = BASE / "candidates-06253-06504.jsonl"
CHECKPOINT = BASE / "candidates-06253-06504.checkpoint.json"
index = json.loads((BASE / "sheets/index.json").read_text())
start = int(sys.argv[1])
observations = [line.strip() for line in sys.stdin if line.strip()]
assert len(observations) == 12
sheet = next(s for s in index["sheets"] if s["sheet"] == f"levels-{start}-{start + 11}.jpg")
existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
assert (existing[-1]["level"] + 1 if existing else 6253) == start
for record, observation in zip(sheet["records"], observations):
    assert record["level"] == start + record["cell"] - 1
    missing = not record.get("image") or not pathlib.Path(record["image"]).exists()
    partial = observation.startswith("PARTIAL: ")
    row = dict(
        schema_version=2, game="royal-match", level=record["level"],
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=None if missing else record["image"],
        image_sha256=None if missing else record["sha256"],
        sheet_path=str(BASE / "sheets" / sheet["sheet"]), cell=record["cell"],
        geometry_tags=[], observation="Source image missing." if missing else observation.removeprefix("PARTIAL: "),
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Visual sheet review only; exact blocker identities and fine cell boundaries need original-resolution confirmation. Geometry labels withheld rather than treating covered cells as empty gaps.",
    )
    with OUTPUT.open("a") as handle:
        handle.write(json.dumps(row) + "\n")
    existing.append(row)
CHECKPOINT.write_text(json.dumps(dict(
    last_completed_sheet=sheet["sheet"], last_saved_level=existing[-1]["level"],
    inspected_sheets=len(existing) // 12,
    saved_rows=len(existing), reviewed=sum(r["inspection_status"] == "reviewed" for r in existing),
    partial=sum(r["inspection_status"] == "partial" for r in existing),
    missing=sum(r["inspection_status"] == "missing" for r in existing),
), indent=2) + "\n")
print(f"Checkpoint: {sheet['sheet']}; {len(existing)} saved rows")
