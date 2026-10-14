import hashlib
import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-11001-12000")
output = base / "candidates-11001-11252.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
tags = {
    "c": "compact_full_field", "s": "split_regions", "b": "layered_bands",
    "e": "edge_channels", "m": "central_mass", "o": "open_center",
    "t": "stair_step", "a": "asymmetric",
}
existing = {}
if output.exists():
    for line in output.read_text().splitlines():
        row = json.loads(line)
        existing[row["level"]] = row

for batch in json.load(sys.stdin):
    start, observations = batch
    sheet = next(s for s in index["sheets"] if s["records"][0]["level"] == start)
    assert len(observations) == len(sheet["records"])
    for source, evidence in zip(sheet["records"], observations):
        level = source["level"]
        assert 11001 <= level <= 11252
        if level in existing:
            continue
        codes, observation, *extra = evidence
        partial = bool(extra and extra[0])
        image = source.get("image")
        missing = not image or not Path(image).exists()
        if not missing:
            assert hashlib.sha256(Path(image).read_bytes()).hexdigest() == source["sha256"]
        existing[level] = {
            "schema_version": 2, "game": "royal-match", "level": level,
            "review_status": "needs_review",
            "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
            "image_path": None if missing else image,
            "image_sha256": None if missing else source["sha256"],
            "sheet_path": str(base / "sheets" / sheet["sheet"]),
            "cell": source["cell"],
            "geometry_tags": [] if missing else [tags[c] for c in codes],
            "observation": "Source image is missing." if missing else observation,
            "occlusion": "unknown" if missing else "partial" if partial else "none",
            "confidence": "unknown" if missing else "low" if partial else "medium",
            "verified_difficulty": "unknown", "verified_strategy": "unknown",
            "verified_evidence": [], "difficulty_hypothesis": None,
            "strategy_hypothesis": None,
            "review_note": extra[0] if partial else (
                "Candidate vocabulary only; fine cell connectivity and blocker identities "
                "are not asserted beyond visible evidence. No local difficulty or strategy citation."
            ),
        }
    output.write_text("".join(json.dumps(existing[k], ensure_ascii=False) + "\n" for k in sorted(existing)))
    checkpoint = {
        "schema_version": 2, "assigned_range": [11001, 11252],
        "saved_levels": sorted(existing), "last_saved_sheet": sheet["sheet"],
        "counts": {status: sum(r["inspection_status"] == status for r in existing.values())
                   for status in ("reviewed", "partial", "missing", "not_reviewed")},
    }
    (base / "candidates-11001-11252.jsonl.checkpoint.json").write_text(
        json.dumps(checkpoint, indent=2) + "\n"
    )
    print(f"Saved sheet {sheet['sheet']}: {len(existing)} persistent rows")
