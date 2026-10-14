import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path.cwd()
DIRECTORY = ROOT / ".ai-work/temporary/level-review-archive/royal-match/batch-10001-11000"
OUTPUT = DIRECTORY / "candidates-10001-10252.jsonl"
CHECKPOINT = DIRECTORY / "candidates-10001-10252.jsonl.checkpoint.json"
INDEX = json.loads((DIRECTORY / "sheets/index.json").read_text())
CONTRACT = json.loads((ROOT / ".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
assert len({row["level"] for row in existing}) == len(existing)
rows = {row["level"]: row for row in existing}
sheet = next(item for item in INDEX["sheets"] if item["sheet"] == sys.argv[1])
notes = {}
for line in sys.stdin.read().strip().splitlines():
    fields = line.split("|")
    level, tags, observation = fields[:3]
    notes[int(level)] = (tags.split(",") if tags else [], observation, fields[3] if len(fields) > 3 else "")
assert set(notes) == {item["level"] for item in sheet["records"]}
for item in sheet["records"]:
    level = item["level"]
    assert 10001 <= level <= 10252
    if level in rows:
        assert rows[level]["inspection_status"] in ("reviewed", "partial", "missing")
        continue
    tags, observation, ambiguity = notes[level]
    assert set(tags) <= set(CONTRACT["geometry_tags"])
    assert observation
    image = ROOT / item["image"]
    assert image.is_file()
    assert hashlib.sha256(image.read_bytes()).hexdigest() == item["sha256"]
    rows[level] = {
        "schema_version": 2, "game": "royal-match", "level": level,
        "review_status": "needs_review", "inspection_status": "partial" if ambiguity.startswith("Occlusion:") else "reviewed",
        "image_path": item["image"], "image_sha256": item["sha256"],
        "sheet_path": (DIRECTORY / "sheets" / sheet["sheet"]).relative_to(ROOT).as_posix(),
        "cell": item["cell"], "geometry_tags": tags, "observation": observation,
        "occlusion": "severe" if ambiguity.startswith("Occlusion: severe;") else "partial" if ambiguity.startswith("Occlusion:") else "none",
        "confidence": "low" if ambiguity.startswith("Occlusion:") else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None,
        "strategy_hypothesis": None,
        "review_note": ambiguity or "Blocker identities are descriptive, not mechanic claims. Match taxonomy remains candidate vocabulary; no verified difficulty or strategy evidence."
    }
ordered = [rows[level] for level in sorted(rows)]
assert all(set(row) == set(CONTRACT["record_fields"]) for row in ordered)
OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in ordered))
checkpoint = {
    "schema_version": 2, "game": "royal-match", "assigned_range": [10001, 10252],
    "saved_levels": sorted(rows), "saved_count": len(rows),
    "inspection_counts": dict(collections.Counter(row["inspection_status"] for row in ordered)),
    "last_checkpointed_sheet": sheet["sheet"],
    "completed_sheets": [entry["sheet"] for entry in INDEX["sheets"]
                         if all(item["level"] in rows for item in entry["records"])],
    "status": "complete" if len(rows) == 252 else "in_progress",
    "method": "Numbered contact sheets rendered with image view tools; image-specific observations manually supplied. Original SHA-256 verified locally.",
    "blocker": None
}
CHECKPOINT.write_text(json.dumps(checkpoint, indent=2) + "\n")
print(f"Checkpointed {sheet['sheet']}: {len(rows)} saved rows")
