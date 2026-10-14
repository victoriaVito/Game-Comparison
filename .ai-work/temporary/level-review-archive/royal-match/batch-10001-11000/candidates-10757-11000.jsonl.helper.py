import hashlib
import json
import pathlib
import sys

base = pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-10001-11000")
output = base / "candidates-10757-11000.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
sources = {}
for sheet in index["sheets"]:
    for record in sheet["records"]:
        sources[record["level"]] = (sheet["sheet"], record)
existing = {}
if output.exists():
    existing = {r["level"]: r for r in map(json.loads, output.read_text().splitlines())}
for line in sys.stdin.read().splitlines():
    if not line.strip():
        continue
    level, tags, observation = line.split("|", 2)
    level = int(level)
    assert 10757 <= level <= 11000
    if level in existing:
        assert existing[level]["observation"] == observation
        continue
    sheet, source = sources[level]
    path = source.get("image")
    assert path and pathlib.Path(path).exists()
    assert hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest() == source["sha256"]
    partial = observation.startswith("PARTIAL: ")
    existing[level] = {
        "schema_version": 2, "game": "royal-match", "level": level,
        "review_status": "needs_review",
        "inspection_status": "partial" if partial else "reviewed",
        "image_path": path, "image_sha256": source["sha256"],
        "sheet_path": str(base / "sheets" / sheet), "cell": source["cell"],
        "geometry_tags": tags.split(",") if tags else [],
        "observation": observation.removeprefix("PARTIAL: "),
        "occlusion": "partial" if partial else "none",
        "confidence": "low" if partial else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None,
        "strategy_hypothesis": None,
        "review_note": (
            "Animation obscures some cells; hidden contents and exact boundaries remain uncertain."
            if partial else
            "Visual sheet evidence only. Blocker identities and hidden mechanics are unverified; tags are candidate vocabulary, not accepted labels."
        )
    }
output.write_text("".join(json.dumps(existing[n], ensure_ascii=False) + "\n" for n in sorted(existing)))
checkpoint = {
    "saved_levels": sorted(existing), "count": len(existing),
    "reviewed": sum(r["inspection_status"] == "reviewed" for r in existing.values()),
    "partial": sum(r["inspection_status"] == "partial" for r in existing.values()),
    "completed_sheets": [
        s["sheet"] for s in index["sheets"]
        if any(10757 <= r["level"] <= 11000 for r in s["records"])
        and all(r["level"] in existing for r in s["records"] if 10757 <= r["level"] <= 11000)
    ]
}
(base / "candidates-10757-11000.jsonl.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps({k: v for k, v in checkpoint.items() if k != "saved_levels"}))
