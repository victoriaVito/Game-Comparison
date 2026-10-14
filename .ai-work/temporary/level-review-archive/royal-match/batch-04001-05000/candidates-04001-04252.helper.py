import json
import sys
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-match/batch-04001-05000")
OUT = BASE / "candidates-04001-04252.jsonl"
CHECKPOINT = BASE / "candidates-04001-04252.checkpoint.json"
TAGS = {
    "C": "compact_full_field", "S": "split_regions", "L": "layered_bands",
    "E": "edge_channels", "M": "central_mass", "O": "open_center",
    "T": "stair_step", "A": "asymmetric",
}
index = json.loads((BASE / "sheets/index.json").read_text())
manifest = {
    r["level"]: (s["sheet"], r)
    for s in index["sheets"] for r in s["records"]
}
start = int(sys.argv[1])
lines = [line for line in sys.stdin.read().splitlines() if line.strip()]
assert len(lines) == 12
previous = [json.loads(line) for line in OUT.read_text().splitlines()] if OUT.exists() else []
assert start == (previous[-1]["level"] + 1 if previous else 4001)
assert 4001 <= start <= 4241 and (start - 4001) % 12 == 0
rows = []
for level, line in zip(range(start, start + 12), lines):
    codes, observation = line.split("|", 1)
    partial = "P" in codes
    sheet, source = manifest[level]
    missing = not source.get("image")
    row = {
        "schema_version": 2, "game": "royal-match", "level": level,
        "review_status": "needs_review",
        "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
        "image_path": None if missing else source["image"],
        "image_sha256": None if missing else source["sha256"],
        "sheet_path": str(BASE / "sheets" / sheet), "cell": source["cell"],
        "geometry_tags": [] if missing else [TAGS[c] for c in codes if c != "P"],
        "observation": observation.strip(),
        "occlusion": "unknown" if missing else "partial" if partial else "none",
        "confidence": "unknown" if missing else "low" if partial else "medium",
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
        "review_note": (
            "Source unavailable; no visual inference."
            if missing else
            "Overlay or animation obscures board cells as described in the observation; hidden cells and the complete layout cannot be established."
            if partial else
            "Contact-sheet review only; blocker identities and small cell details may require original-resolution review. Tags describe visible boundary or placement, not connectivity through blockers. No local difficulty or strategy evidence assessed."
        ),
    }
    rows.append(row)
with OUT.open("a") as stream:
    for row in rows:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")
all_rows = previous + rows
CHECKPOINT.write_text(json.dumps({
    "schema_version": 2, "game": "royal-match", "assigned_range": [4001, 4252],
    "saved_rows": len(all_rows), "last_saved_level": all_rows[-1]["level"],
    "inspected_sheets": list(dict.fromkeys(r["sheet_path"] for r in all_rows)),
    "reviewed": sum(r["inspection_status"] == "reviewed" for r in all_rows),
    "partial": sum(r["inspection_status"] == "partial" for r in all_rows),
    "missing": sum(r["inspection_status"] == "missing" for r in all_rows),
    "status": "complete" if all_rows[-1]["level"] == 4252 else "in_progress",
}, indent=2) + "\n")
print(f"Checkpoint: {start}-{start + 11}; {len(all_rows)} rows saved")
