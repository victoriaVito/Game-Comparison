import hashlib
import json
import pathlib
import sys

base = pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-12001-13000")
output = base / "candidates-12001-12252.jsonl"
checkpoint = base / "candidates-12001-12252.jsonl.checkpoint.json"
index = json.loads((base / "sheets/index.json").read_text())
existing = {}
if output.exists():
    existing = {r["level"]: r for r in map(json.loads, output.read_text().splitlines())}
start = int(sys.argv[1])
sheet = next(s for s in index["sheets"] if s["records"][0]["level"] == start)
lines = sys.stdin.read().strip().splitlines()
assert len(lines) == len(sheet["records"]) == 12
for source, line in zip(sheet["records"], lines):
    level = source["level"]
    assert 12001 <= level <= 12252
    tags, observation = line.split("|", 1)
    partial = tags.startswith("partial;")
    if partial:
        tags = tags.removeprefix("partial;")
    image = source.get("image")
    assert image and hashlib.sha256(pathlib.Path(image).read_bytes()).hexdigest() == source["sha256"]
    row = dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review", inspection_status="partial" if partial else "reviewed",
        image_path=image, image_sha256=source["sha256"],
        sheet_path=str(base / "sheets" / sheet["sheet"]), cell=source["cell"],
        geometry_tags=tags.split(",") if tags else [], observation=observation,
        occlusion="partial" if partial else "none", confidence="low" if partial else "medium", verified_difficulty="unknown",
        verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note=("Visible covers prevent interpretation of the cells beneath them. " if partial else "") + "Visually inspected numbered contact sheet. Candidate geometry only; blocker identities and unseen mechanics are not verified.",
    )
    if level not in existing:
        existing[level] = row
output.write_text("".join(json.dumps(existing[k], ensure_ascii=False) + "\n" for k in sorted(existing)))
checkpoint.write_text(json.dumps(dict(
    assigned_range=[12001, 12252], saved_levels=sorted(existing),
    saved_count=len(existing), last_inspected_sheet=str(base / "sheets" / sheet["sheet"]),
    review_status="needs_review", accepted_count=0,
), indent=2) + "\n")
print(f"Saved sheet {start}-{start + 11}; total {len(existing)}")
