import json
import sys
from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / ".ai-work/temporary/level-review-archive/royal-match/batch-10001-11000"
OUT = BASE / "candidates-10253-10504.jsonl"
CHECKPOINT = BASE / "candidates-10253-10504.jsonl.checkpoint.json"
TAGS = dict(
    c="compact_full_field", s="split_regions", l="layered_bands",
    e="edge_channels", m="central_mass", o="open_center",
    t="stair_step", a="asymmetric",
)
index = json.loads((BASE / "sheets/index.json").read_text())
sources = {
    r["level"]: (s["sheet"], r)
    for s in index["sheets"] for r in s["records"]
}
rows = {}
if OUT.exists():
    for line in OUT.read_text().splitlines():
        row = json.loads(line)
        rows[row["level"]] = row

start = int(sys.argv[1])
entries = json.load(sys.stdin)
assert len(entries) == 12
for level, entry in enumerate(entries, start):
    assert 10253 <= level <= 10504
    if level in rows and rows[level]["inspection_status"] in ("reviewed", "partial"):
        continue
    sheet, source = sources[level]
    tags, observation, *extras = entry
    note = extras[0] if extras else "Candidate vocabulary only; difficulty and strategy are not established by this image."
    partial = len(extras) > 1 and extras[1] == "partial"
    rows[level] = {
        "schema_version": 2,
        "game": "royal-match",
        "level": level,
        "review_status": "needs_review",
        "inspection_status": "partial" if partial else "reviewed",
        "image_path": source["image"],
        "image_sha256": source["sha256"],
        "sheet_path": str((BASE / "sheets" / sheet).relative_to(ROOT)),
        "cell": source["cell"],
        "geometry_tags": [TAGS[t] for t in tags],
        "observation": observation,
        "occlusion": "partial" if partial else "none",
        "confidence": "low" if partial else "medium",
        "verified_difficulty": "unknown",
        "verified_strategy": "unknown",
        "verified_evidence": [],
        "difficulty_hypothesis": None,
        "strategy_hypothesis": None,
        "review_note": note,
    }
OUT.write_text("".join(json.dumps(rows[n], ensure_ascii=False) + "\n" for n in sorted(rows)))
coverage = sorted(rows)
CHECKPOINT.write_text(json.dumps({
    "schema_version": 2,
    "game": "royal-match",
    "assigned_range": [10253, 10504],
    "saved_levels": coverage,
    "saved_count": len(coverage),
    "last_saved_sheet": sources[start][0],
    "inspection_counts": {
        status: sum(r["inspection_status"] == status for r in rows.values())
        for status in ("reviewed", "partial", "missing", "not_reviewed")
    },
    "complete": coverage == list(range(10253, 10505)),
    "status": "complete" if coverage == list(range(10253, 10505)) else "in_progress",
}, indent=2) + "\n")
print(f"Saved sheet {sources[start][0]}; {len(rows)} rows persisted.")
