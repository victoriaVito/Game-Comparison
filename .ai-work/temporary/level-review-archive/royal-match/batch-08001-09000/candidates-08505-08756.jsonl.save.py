import hashlib
import json
import pathlib
import sys

BASE = pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-08001-09000")
OUT = BASE / "candidates-08505-08756.jsonl"
INDEX = json.loads((BASE / "sheets/index.json").read_text())
TAGS = set(json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["geometry_tags"])
rows = {r["level"]: r for r in map(json.loads, OUT.read_text().splitlines())} if OUT.exists() else {}
sheet = sys.argv[1]
entries = next(s["records"] for s in INDEX["sheets"] if s["sheet"] == sheet)
observations = {}
for line in sys.stdin.read().splitlines():
    if not line.strip():
        continue
    level, tags, observation, *extra = line.split("|")
    observations[int(level)] = (tags.split(",") if tags else [], observation, extra)
for entry in entries:
    level = entry["level"]
    assert 8505 <= level <= 8756
    if level in rows:
        continue
    missing = entry["status"].startswith("missing")
    if not missing:
        assert level in observations, level
        tags, observation, extra = observations[level]
        assert set(tags) <= TAGS
        image = entry["image"]
        digest = hashlib.sha256(pathlib.Path(image).read_bytes()).hexdigest()
        assert digest == entry["sha256"]
    else:
        tags, observation, extra, image, digest = [], "No source image is available in the local sheet index.", [], None, None
    partial = bool(extra)
    rows[level] = {
        "schema_version": 2, "game": "royal-match", "level": level,
        "review_status": "needs_review",
        "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
        "image_path": image, "image_sha256": digest,
        "sheet_path": str(BASE / "sheets" / sheet), "cell": entry["cell"],
        "geometry_tags": tags, "observation": observation,
        "occlusion": "unknown" if missing else "partial" if partial else "none",
        "confidence": "unknown" if missing else "low" if partial else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
        "review_note": "Source missing; no board interpretation is possible." if missing else extra[0] if partial else
        "Visual sheet evidence only. Blocker identities and connectivity hidden by occupied cells remain uncertain; unsupported tags are withheld. Candidate vocabulary is not an accepted Match taxonomy."
    }
OUT.write_text("".join(json.dumps(rows[k], ensure_ascii=False) + "\n" for k in sorted(rows)))
checkpoint = OUT.with_name(OUT.name + ".checkpoint.json")
previous = json.loads(checkpoint.read_text()) if checkpoint.exists() else {"rendered_sheets": []}
if sheet not in previous["rendered_sheets"]:
    previous["rendered_sheets"].append(sheet)
previous.update({"saved_levels": sorted(rows), "saved_count": len(rows), "review_status": "needs_review"})
checkpoint.write_text(json.dumps(previous, indent=2) + "\n")
print(sheet, len(entries), "saved; total", len(rows))
