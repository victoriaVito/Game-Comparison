import json
import pathlib
import sys

BASE = pathlib.Path(__file__).parent
OUTPUT = BASE / "candidates-01757-02000.jsonl"
CHECKPOINT = BASE / "candidates-01757-02000-checkpoint.json"
INDEX = json.loads((BASE / "sheets/index.json").read_text())
ROOT = pathlib.Path.cwd()
RECORDS = {
    r["level"]: (s["sheet"], r)
    for s in INDEX["sheets"]
    for r in s["records"]
    if 1757 <= r["level"] <= 2000
}
existing = {
    row["level"]: row
    for row in (
        [json.loads(line) for line in OUTPUT.read_text().splitlines()]
        if OUTPUT.exists()
        else []
    )
}
sheet = sys.argv[1]
lines = [line for line in sys.stdin.read().splitlines() if line.strip()]
expected = {level for level, (name, _) in RECORDS.items() if name == sheet}
assert {int(line.split("|", 1)[0]) for line in lines} == expected
for line in lines:
    level_text, tags_text, observation = line.split("|", 2)
    level = int(level_text)
    assert level not in existing, f"Already saved: {level}"
    name, source = RECORDS[level]
    missing = not (ROOT / source["image"]).is_file()
    partial = observation.startswith("PARTIAL: ")
    observation = observation.removeprefix("PARTIAL: ")
    existing[level] = {
        "schema_version": 2,
        "game": "royal-kingdom",
        "level": level,
        "review_status": "needs_review",
        "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
        "image_path": None if missing else source["image"],
        "image_sha256": None if missing else source["sha256"],
        "sheet_path": str((BASE / "sheets" / name).relative_to(ROOT)),
        "cell": source["cell"],
        "geometry_tags": [] if missing else tags_text.split(",") if tags_text else [],
        "observation": "Source image is missing." if missing else observation,
        "occlusion": "unknown" if missing else "partial" if partial else "none",
        "confidence": "unknown" if missing else "low" if partial else "medium",
        "verified_difficulty": "unknown",
        "verified_strategy": "unknown",
        "verified_evidence": [],
        "difficulty_hypothesis": None,
        "strategy_hypothesis": None,
        "review_note": "Contact-sheet visual evidence only; blocker identities and covered-cell connectivity require original-resolution follow-up. No local difficulty or strategy evidence cited.",
    }
OUTPUT.write_text("".join(json.dumps(existing[n]) + "\n" for n in sorted(existing)))
counts = {
    status: sum(row["inspection_status"] == status for row in existing.values())
    for status in ("reviewed", "partial", "missing")
}
CHECKPOINT.write_text(json.dumps({
    "range": [1757, 2000],
    "last_saved_sheet": sheet,
    "saved_levels": sorted(existing),
    "inspected_sheets": sorted({row["sheet_path"] for row in existing.values()}),
    "counts": counts,
    "complete": len(existing) == 244,
}, indent=2) + "\n")
print(sheet, len(existing), counts)
