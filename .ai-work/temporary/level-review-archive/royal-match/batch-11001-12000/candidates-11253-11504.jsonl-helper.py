import json
import sys
from pathlib import Path

ROOT = Path(".ai-work/temporary/level-review-archive/royal-match/batch-11001-12000")
OUTPUT = ROOT / "candidates-11253-11504.jsonl"
TAGS = {"C": "compact_full_field", "L": "layered_bands", "M": "central_mass",
        "S": "split_regions", "E": "edge_channels", "D": "stair_step", "A": "asymmetric",
        "O": "open_center"}
index = json.loads((ROOT / "sheets/index.json").read_text())
start = int(sys.argv[1])
notes = json.loads(sys.argv[2])
sheet = next(s for s in index["sheets"] if s["records"][0]["level"] == start)
assert len(notes) == len(sheet["records"]) == 12
existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
known = {r["level"] for r in existing}
for source, note in zip(sheet["records"], notes):
    if source["level"] in known:
        continue
    tags, observation, *extra = note
    partial = bool(extra)
    missing = not source.get("image")
    existing.append({
        "schema_version": 2, "game": "royal-match", "level": source["level"],
        "review_status": "needs_review",
        "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
        "image_path": source.get("image"), "image_sha256": source.get("sha256"),
        "sheet_path": str(ROOT / "sheets" / sheet["sheet"]), "cell": source["cell"],
        "geometry_tags": [] if missing else [TAGS[t] for t in tags],
        "observation": observation, "occlusion": "unknown" if missing else "partial" if partial else "none",
        "confidence": "unknown" if missing else "low" if partial else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown", "verified_evidence": [],
        "difficulty_hypothesis": None, "strategy_hypothesis": None,
        "review_note": extra[0] if partial else
            "Sheet-level visual evidence only; blocker identities and cell connectivity not resolved beyond visible boundaries. Tags are provisional Match vocabulary, not accepted classifications."
    })
existing.sort(key=lambda r: r["level"])
assert len({r["level"] for r in existing}) == len(existing)
OUTPUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in existing))
checkpoint = ROOT / "candidates-11253-11504.jsonl-checkpoint.json"
checkpoint.write_text(json.dumps({
    "assigned_range": [11253, 11504], "saved_levels": [r["level"] for r in existing],
    "last_checkpoint_sheet": str(ROOT / "sheets" / sheet["sheet"]),
    "saved_count": len(existing), "status": "complete" if len(existing) == 252 else "in_progress"
}, indent=2) + "\n")
print(f"Saved {start}-{start + 11}; total {len(existing)}")
