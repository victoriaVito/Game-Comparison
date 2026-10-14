import hashlib
import json
import sys
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-match/batch-12001-13000")
OUTPUT = BASE / "candidates-12505-12756.jsonl"
CHECKPOINT = BASE / "candidates-12505-12756.jsonl.checkpoint.json"
INDEX = json.loads((BASE / "sheets/index.json").read_text())
FIELDS = set(json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["record_fields"])
TAGS = set(json.loads(Path("royal-kingdom/analysis/pattern_taxonomy_v1.json").read_text())["traits"])


def save(start, evidence):
    sheet = next(s for s in INDEX["sheets"] if s["records"][0]["level"] == start)
    assert len(evidence) == len(sheet["records"]) == 12
    existing = {}
    if OUTPUT.exists():
        existing = {r["level"]: r for r in map(json.loads, OUTPUT.read_text().splitlines())}
    for source, entry in zip(sheet["records"], evidence):
        level = source["level"]
        assert 12505 <= level <= 12756
        if level in existing and existing[level]["inspection_status"] in ("reviewed", "partial", "missing"):
            continue
        tags, observation = entry[:2]
        assert set(tags) <= TAGS and observation
        detail = entry[2] if len(entry) > 2 else None
        partial = bool(detail) if not isinstance(detail, dict) else detail.get("partial", False)
        image = Path(source["image"]) if source.get("image") else None
        missing = image is None or not image.is_file()
        if not missing:
            assert hashlib.sha256(image.read_bytes()).hexdigest() == source["sha256"]
        row = {
            "schema_version": 2,
            "game": "royal-match",
            "level": level,
            "review_status": "needs_review",
            "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
            "image_path": None if missing else source["image"],
            "image_sha256": None if missing else source["sha256"],
            "sheet_path": str(BASE / "sheets" / sheet["sheet"]),
            "cell": source["cell"],
            "geometry_tags": [] if missing else tags,
            "observation": "Source image is missing; no board evidence available." if missing else observation,
            "occlusion": "unknown" if missing else "partial" if partial else "none",
            "confidence": "unknown" if missing else "low" if partial else "medium",
            "verified_difficulty": "unknown",
            "verified_strategy": "unknown",
            "verified_evidence": [],
            "difficulty_hypothesis": None,
            "strategy_hypothesis": None,
            "review_note": detail["review_note"] if isinstance(detail, dict) else detail if partial else "Visual candidate only. Small blocker identities remain uncertain; tags describe visible geometry, not validated Match taxonomy. No cited difficulty or strategy evidence.",
        }
        assert set(row) == FIELDS
        existing[level] = row
    ordered = [existing[k] for k in sorted(existing)]
    OUTPUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in ordered))
    checkpoint = {
        "assigned_range": [12505, 12756],
        "saved_levels": [r["level"] for r in ordered],
        "saved_count": len(ordered),
        "rendered_sheets": sorted(set(r["sheet_path"] for r in ordered)),
        "inspection_counts": {status: sum(r["inspection_status"] == status for r in ordered) for status in ("reviewed", "partial", "missing")},
        "last_saved_sheet": sheet["sheet"],
        "remaining_levels": [n for n in range(12505, 12757) if n not in existing],
        "status": "complete" if len(ordered) == 252 else "in_progress",
    }
    CHECKPOINT.write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(json.dumps({"sheet": sheet["sheet"], "saved_count": len(ordered), "counts": checkpoint["inspection_counts"]}))


if __name__ == "__main__":
    save(int(sys.argv[1]), json.loads(sys.stdin.read()))
