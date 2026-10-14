import hashlib
import json
from collections import Counter
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-10001-11000")
name = "candidates-10757-11000.jsonl"
contract = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((base / "sheets/index.json").read_text())
rows = [json.loads(line) for line in (base / name).read_text().splitlines()]
assert [r["level"] for r in rows] == list(range(10757, 11001))
metadata = {
    r["level"]: (str(base / "sheets" / s["sheet"]), r)
    for s in index["sheets"] for r in s["records"]
}
for row in rows:
    assert set(row) == set(contract["record_fields"])
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["game"] == "royal-match" and row["review_status"] == "needs_review"
    sheet, source = metadata[row["level"]]
    assert row["sheet_path"] == sheet and row["cell"] == source["cell"]
    assert row["image_path"] == source["image"]
    assert row["image_sha256"] == source["sha256"]
    assert hashlib.sha256(Path(row["image_path"]).read_bytes()).hexdigest() == row["image_sha256"]
    assert not Path(row["image_path"]).is_absolute() and not Path(row["sheet_path"]).is_absolute()
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    assert row["inspection_status"] in ("reviewed", "partial")
    assert row["occlusion"] == ("partial" if row["inspection_status"] == "partial" else "none")
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is None and row["strategy_hypothesis"] is None
    assert row["observation"] and row["review_note"]
checkpoint = json.loads((base / (name + ".checkpoint.json")).read_text())
assert checkpoint["saved_levels"] == list(range(10757, 11001))
assert len(checkpoint["completed_sheets"]) == 21
assert set(checkpoint["completed_sheets"]) == {Path(r["sheet_path"]).name for r in rows}
counts = Counter(r["inspection_status"] for r in rows)
assert checkpoint["reviewed"] == counts["reviewed"]
assert checkpoint["partial"] == counts["partial"]
result = {
    "status": "passed", "coverage": [10757, 11000], "rows": len(rows),
    "reviewed": counts["reviewed"], "partial": counts["partial"],
    "missing": 0, "not_reviewed": 0, "needs_review": len(rows), "accepted": 0,
    "rendered_numbered_sheets": 21,
    "original_followup_levels": [10775, 10944, 11000],
    "checks": [
        "Exact numeric order and complete contract fields",
        "Repository-relative image and sheet paths, indexed cell and source SHA-256",
        "All 244 original source hashes recomputed locally",
        "Allowed candidate vocabulary, no accepted rows",
        "Unknown verified difficulty and strategy; null hypotheses",
        "All 21 sheet checkpoints present and coverage counts consistent"
    ],
    "output_sha256": hashlib.sha256((base / name).read_bytes()).hexdigest()
}
(base / (name + ".validation.json")).write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
