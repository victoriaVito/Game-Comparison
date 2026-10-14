import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path.cwd()
BASE = ROOT / ".ai-work/temporary/level-review-archive/royal-match/batch-12001-13000"
OUT = BASE / "candidates-12757-13000.jsonl"
CHECKPOINT = BASE / "candidates-12757-13000.jsonl.checkpoint.json"
INDEX = json.loads((BASE / "sheets/index.json").read_text())
CONTRACT = json.loads((ROOT / ".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
FIELDS = set(CONTRACT["record_fields"])
SOURCES = {
    r["level"]: (s["sheet"], r)
    for s in INDEX["sheets"]
    for r in s["records"]
}
rows = {}
if OUT.exists():
    for line in OUT.read_text().splitlines():
        row = json.loads(line)
        assert row["level"] not in rows
        rows[row["level"]] = row
if len(sys.argv) > 1:
    start = int(sys.argv[1])
    entries = json.load(sys.stdin)
    for offset, entry in enumerate(entries):
        level = start + offset
        assert 12757 <= level <= 13000
        if level in rows:
            continue
        sheet, source = SOURCES[level]
        observation, tags, *detail = entry
        partial = bool(detail and detail[0])
        image = source["image"]
        assert hashlib.sha256((ROOT / image).read_bytes()).hexdigest() == source["sha256"]
        rows[level] = {
            "schema_version": 2,
            "game": "royal-match",
            "level": level,
            "review_status": "needs_review",
            "inspection_status": "partial" if partial else "reviewed",
            "image_path": image,
            "image_sha256": source["sha256"],
            "sheet_path": str((BASE / "sheets" / sheet).relative_to(ROOT)),
            "cell": source["cell"],
            "geometry_tags": tags,
            "observation": observation,
            "occlusion": "partial" if partial else "none",
            "confidence": "low" if partial else "medium",
            "verified_difficulty": "unknown",
            "verified_strategy": "unknown",
            "verified_evidence": [],
            "difficulty_hypothesis": None,
            "strategy_hypothesis": None,
            "review_note": detail[0] if partial else (
                "Visual candidate only. Blocker identities and underlying covered cells are not verified; "
                "no difficulty or strategy claim is supported. Tags are withheld where visible geometry is insufficient."
            ),
        }
for level, row in rows.items():
    assert set(row) == FIELDS
    assert row["schema_version"] == 2 and type(row["schema_version"]) is int
    assert row["review_status"] == "needs_review"
    assert set(row["geometry_tags"]) <= set(CONTRACT["geometry_tags"])
    sheet, source = SOURCES[level]
    assert row["cell"] == source["cell"]
    assert row["image_path"] == source["image"]
    assert row["image_sha256"] == source["sha256"]
    assert row["sheet_path"] == str((BASE / "sheets" / sheet).relative_to(ROOT))
OUT.write_text("".join(json.dumps(rows[n], ensure_ascii=False) + "\n" for n in sorted(rows)))
summary = {
    "assigned_range": [12757, 13000],
    "saved_count": len(rows),
    "saved_levels": sorted(rows),
    "inspection_counts": dict(collections.Counter(r["inspection_status"] for r in rows.values())),
    "review_status_counts": dict(collections.Counter(r["review_status"] for r in rows.values())),
    "completed_sheets": sorted(set(r["sheet_path"] for r in rows.values())),
    "remaining_levels": [n for n in range(12757, 13001) if n not in rows],
    "method": "Direct rendering of each numbered contact sheet; original images used for unclear boundaries.",
}
CHECKPOINT.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: summary[k] for k in ["saved_count", "inspection_counts", "review_status_counts"]}))
