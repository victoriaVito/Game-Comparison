import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-08001-09000")
output = base / "candidates-08757-09000.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
sources = {r["level"]: (s["sheet"], r) for s in index["sheets"] for r in s["records"]}
rows = {}
if output.exists():
    rows = {r["level"]: r for r in map(json.loads, output.read_text().splitlines())}
for item in json.load(sys.stdin):
    level, observation, tags = item[:3]
    if level in rows:
        continue
    sheet, source = sources[level]
    missing = source.get("image") is None
    partial = len(item) > 3
    rows[level] = {
        "schema_version": 2, "game": "royal-match", "level": level,
        "review_status": "needs_review",
        "inspection_status": "missing" if missing else ("partial" if partial else "reviewed"),
        "image_path": source.get("image"), "image_sha256": source.get("sha256"),
        "sheet_path": str(base / "sheets" / sheet), "cell": source["cell"],
        "geometry_tags": [] if missing else tags, "observation": observation,
        "occlusion": "unknown" if missing else ("partial" if partial else "none"),
        "confidence": "unknown" if missing else ("low" if partial else "medium"),
        "verified_difficulty": "unknown", "verified_strategy": "unknown",
        "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
        "review_note": "Source unavailable; no board inference." if missing else (
            item[3] if partial else "Candidate Match vocabulary only; small-scale blocker identities are not verified.")
    }
output.write_text("".join(json.dumps(rows[n], ensure_ascii=False) + "\n" for n in sorted(rows)))
complete_sheets = sorted({sources[n][0] for n in rows if all(
    r["level"] in rows for r in next(s for s in index["sheets"] if s["sheet"] == sources[n][0])["records"]
)})
checkpoint = {"range": [8757, 9000], "saved_levels": sorted(rows),
              "complete_inspected_sheets": complete_sheets,
              "counts": {status: sum(r["inspection_status"] == status for r in rows.values())
                         for status in ["reviewed", "partial", "missing"]}}
(base / "candidates-08757-09000.jsonl.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps(checkpoint["counts"]), "saved", len(rows))
