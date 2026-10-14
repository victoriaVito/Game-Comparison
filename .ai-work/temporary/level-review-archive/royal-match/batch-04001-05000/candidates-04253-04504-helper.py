import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-04253-04504.jsonl"
checkpoint = base / "candidates-04253-04504-checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
notes = json.loads(sys.argv[2])
sheet = next(s for s in manifest["sheets"] if s["sheet"].startswith(f"levels-{start}-"))
records = {r["level"]: r for r in sheet["records"]}
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert len(notes) == 12
assert not any(start <= r["level"] < start + 12 for r in existing)
for offset, note in enumerate(notes):
    level = start + offset
    source = records.get(level, {})
    missing = not source.get("image")
    observation, tags = note if isinstance(note, list) else (note, [])
    partial = observation.startswith("Overlay:")
    existing.append({
        "schema_version": 2, "game": "royal-match", "level": level,
        "review_status": "needs_review",
        "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
        "image_path": None if missing else source["image"],
        "image_sha256": None if missing else source["sha256"],
        "sheet_path": str(base / "sheets" / sheet["sheet"]) if not missing else None,
        "cell": None if missing else source["cell"], "geometry_tags": [] if missing else tags,
        "observation": "No source image is available; the inspected sheet shows a missing placeholder." if missing else observation,
        "occlusion": "unknown" if missing else "partial" if partial else "none",
        "confidence": "unknown" if missing else "low" if partial else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
        "review_note": "Missing source evidence." if missing else "Contact-sheet inspection; fine blocker identities and covered-cell connectivity require original-resolution review. No locally verified difficulty or strategy."
    })
existing.sort(key=lambda r: r["level"])
output.write_text("".join(json.dumps(r) + "\n" for r in existing))
previous = json.loads(checkpoint.read_text()) if checkpoint.exists() else {"inspected_sheets": []}
previous["inspected_sheets"].append(sheet["sheet"])
previous["saved_rows"] = len(existing)
previous["last_saved_level"] = start + 11
checkpoint.write_text(json.dumps(previous, indent=2) + "\n")
print(f"Saved {start}-{start + 11}; total {len(existing)}")
