import json
import sys
from pathlib import Path

base = Path(__file__).resolve().parent.relative_to(Path.cwd())
output = base / "candidates-06001-06252.jsonl"
checkpoint = base / "candidates-06001-06252.checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
saved = {row["level"] for row in existing}
start = int(sys.argv[1])
entries = json.loads(sys.stdin.read())
sheet = next(s for s in manifest["sheets"] if s["sheet"] == f"levels-{start}-{start + 11}.jpg")
assert len(entries) == len(sheet["records"]) == 12
rows = []
for source, entry in zip(sheet["records"], entries):
    level = source["level"]
    assert 6001 <= level <= 6252 and level not in saved
    missing = not source.get("image")
    observation, tags, *partial = entry
    row = dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=source.get("image"), image_sha256=source.get("sha256"),
        sheet_path=(base / "sheets" / sheet["sheet"]).as_posix(), cell=source.get("cell"),
        geometry_tags=[] if missing else tags, observation=observation,
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Missing source image in manifest." if missing else
        "Overlay obscures cells; inspect original resolution before assigning further geometry." if partial else
        "Sheet-scale visual evidence only; blocker identities and hidden cells are not verified.",
    )
    rows.append(row)
assert not existing or existing[-1]["level"] + 1 == start
with output.open("a") as handle:
    for row in rows:
        handle.write(json.dumps(row) + "\n")
existing.extend(rows)
checkpoint.write_text(json.dumps(dict(
    last_saved_level=existing[-1]["level"],
    inspected_sheets=[f"levels-{n}-{n+11}.jpg" for n in range(6001, start+1, 12)],
    rows=len(existing),
    counts={status: sum(r["inspection_status"] == status for r in existing)
            for status in ("reviewed", "partial", "missing")},
), indent=2) + "\n")
print(f"Checkpoint: {start}-{start+11}; {len(existing)} saved rows")
