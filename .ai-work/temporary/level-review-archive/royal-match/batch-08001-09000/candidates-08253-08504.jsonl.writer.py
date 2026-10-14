import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path.cwd()
BASE = ROOT / ".ai-work/temporary/level-review-archive/royal-match/batch-08001-09000"
OUTPUT = BASE / "candidates-08253-08504.jsonl"
INDEX = json.loads((BASE / "sheets/index.json").read_text())
TAGS = {
    "c": "compact_full_field", "s": "split_regions", "b": "layered_bands",
    "e": "edge_channels", "m": "central_mass", "o": "open_center",
    "t": "stair_step", "a": "asymmetric",
}
existing = {}
if OUTPUT.exists():
    for line in OUTPUT.read_text().splitlines():
        row = json.loads(line)
        existing[row["level"]] = row
for chunk in sys.stdin.read().strip().split("\n\n"):
    entries = {}
    for line in chunk.splitlines():
        parts = line.split("|")
        level = int(parts[0])
        assert 8253 <= level <= 8504
        entries[level] = parts
    sheets = [s for s in INDEX["sheets"] if any(r["level"] in entries for r in s["records"])]
    assert len(sheets) == 1
    sheet = sheets[0]
    assigned = [r for r in sheet["records"] if 8253 <= r["level"] <= 8504]
    assert set(entries) == {r["level"] for r in assigned}
    for source in assigned:
        level = source["level"]
        parts = entries[level]
        missing = source.get("image") is None
        if not missing:
            assert hashlib.sha256((ROOT / source["image"]).read_bytes()).hexdigest() == source["sha256"]
        partial = len(parts) > 4 and parts[4] == "partial"
        row = {
            "schema_version": 2, "game": "royal-match", "level": level,
            "review_status": "needs_review",
            "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
            "image_path": source.get("image"), "image_sha256": source.get("sha256"),
            "sheet_path": str((BASE / "sheets" / sheet["sheet"]).relative_to(ROOT)),
            "cell": source["cell"],
            "geometry_tags": [] if missing else [TAGS[t] for t in parts[1]],
            "observation": parts[2],
            "occlusion": "unknown" if missing else "partial" if partial else "none",
            "confidence": "unknown" if missing else "low" if partial else "medium",
            "verified_difficulty": "unknown", "verified_strategy": "unknown",
            "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
            "review_note": parts[3] if len(parts) > 3 else "Candidate vocabulary only; no directly cited local difficulty or strategy evidence.",
        }
        if level not in existing:
            existing[level] = row
    OUTPUT.write_text("".join(json.dumps(existing[n], ensure_ascii=False) + "\n" for n in sorted(existing)))
    checkpoint = {
        "sheet_path": str((BASE / "sheets" / sheet["sheet"]).relative_to(ROOT)),
        "visually_rendered": True, "saved_levels": sorted(entries),
        "saved_total": len(existing),
        "counts": {s: sum(r["inspection_status"] == s for r in existing.values()) for s in ("reviewed", "partial", "missing")},
    }
    (BASE / (OUTPUT.name + ".checkpoint-" + sheet["sheet"] + ".json")).write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(json.dumps(checkpoint))
