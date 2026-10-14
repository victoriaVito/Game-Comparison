import json
import pathlib
import sys

BASE = pathlib.Path(__file__).parent
OUTPUT = BASE / "candidates-03001-03252.jsonl"
ROOT = pathlib.Path.cwd()
INDEX = json.loads((BASE / "sheets/index.json").read_text())
TAGS = {
    "c": "compact_full_field", "s": "split_regions", "l": "layered_bands",
    "e": "edge_channels", "m": "central_mass", "o": "open_center",
    "t": "stair_step", "a": "asymmetric",
}


def save(start, lines):
    sheet = next(s for s in INDEX["sheets"] if s["records"][0]["level"] == start)
    entries = lines.strip().splitlines()
    assert len(entries) == len(sheet["records"]) == 12
    existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
    assert not existing or existing[-1]["level"] == start - 1
    rows = []
    for source, line in zip(sheet["records"], entries):
        flags, observation = line.split("|", 1)
        partial = "p" in flags
        missing = not source.get("image") or not (ROOT / source["image"]).exists()
        rows.append({
            "schema_version": 2, "game": "royal-kingdom", "level": source["level"],
            "review_status": "needs_review",
            "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
            "image_path": None if missing else source["image"],
            "image_sha256": None if missing else source["sha256"],
            "sheet_path": str((BASE / "sheets" / sheet["sheet"]).relative_to(ROOT)),
            "cell": source["cell"],
            "geometry_tags": [] if missing else [TAGS[f] for f in flags if f in TAGS],
            "observation": "Source image is missing; no image-level conclusion." if missing else observation.strip(),
            "occlusion": "unknown" if missing else "partial" if partial else "none",
            "confidence": "unknown" if missing else "low" if partial else "medium",
            "verified_difficulty": "unknown", "verified_strategy": "unknown",
            "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
            "review_note": "Animation or foreground overlay hides cells; original-resolution follow-up required." if partial else
            "Sheet-scale visual evidence only; blocker identity and exact cell counts require original-resolution follow-up. Covered cells are not empty gaps.",
        })
    with OUTPUT.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    all_rows = existing + rows
    checkpoint = {
        "range": [3001, 3252], "saved_rows": len(all_rows),
        "last_saved_level": all_rows[-1]["level"],
        "inspected_sheets": [s["sheet"] for s in INDEX["sheets"] if s["records"][0]["level"] <= start],
        "counts": {status: sum(r["inspection_status"] == status for r in all_rows)
                   for status in ("reviewed", "partial", "missing")},
    }
    (BASE / "candidates-03001-03252-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(json.dumps(checkpoint))


if __name__ == "__main__":
    save(int(sys.argv[1]), sys.stdin.read())
