import hashlib
import json
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-12001-13000")
output = base / "candidates-12505-12756.jsonl"
contract = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((base / "sheets/index.json").read_text())
rows = list(map(json.loads, output.read_text().splitlines()))
history_path = base / "candidates-12505-12756.jsonl.refinements.json"
history = json.loads(history_path.read_text()) if history_path.exists() else []

refinements = {
    12511: {
        "geometry_tags": ["layered_bands"],
        "observation": "Two broad panels each have left tiles and four right grass-covered squares beside purple pipes. A horizontal empty recess lies between their left portions, but two short purple tube cells on the right visibly bridge the upper and lower panels; separate regions are therefore not established.",
        "review_note": "Original rendered: sources/royal-match-level-archive/levels/12511/board.jpg. The right-hand purple tube bridge resolves the sheet-scale connectivity ambiguity. Bright lower-right grass glare limits small-content identification, but the panel boundary remains visible. No difficulty or strategy evidence.",
    },
    12586: {
        "observation": "A detached top tile strip sits above a second tile strip ending in a green circular device. That device touches the right end of a pink-round-blocker strip immediately below. Three further pink-round strips alternate positions down the screen with clear empty horizontal gaps separating them.",
        "review_note": "Original rendered: sources/royal-match-level-archive/levels/12586/board.jpg. The second and third strips touch at the green device; split_regions refers only to the visibly detached top and lower strips, not to every horizontal band. No difficulty or strategy evidence.",
    },
}
for level in (12542, 12610, 12614, 12633, 12666, 12738, 12741):
    row = next(r for r in rows if r["level"] == level)
    suffix = " open_center withheld: visible exterior/side recesses or small holes do not establish a predominantly empty central area."
    refinements[level] = {
        "geometry_tags": [t for t in row["geometry_tags"] if t != "open_center"],
        "review_note": row["review_note"] if row["review_note"].endswith(suffix) else row["review_note"] + suffix,
    }
for row in rows:
    change = refinements.get(row["level"])
    if change and any(row[k] != v for k, v in change.items()):
        history.append({"level": row["level"], "previous": {k: row[k] for k in change}, "refined": change})
        row.update(change)
output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
history_path.write_text(json.dumps(history, indent=2) + "\n")

assert [r["level"] for r in rows] == list(range(12505, 12757))
sources = {
    r["level"]: (r, str(base / "sheets" / s["sheet"]))
    for s in index["sheets"] for r in s["records"]
}
for row in rows:
    source, sheet_path = sources[row["level"]]
    assert set(row) == set(contract["record_fields"])
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["game"] == "royal-match" and row["review_status"] == "needs_review"
    assert row["inspection_status"] in ("reviewed", "partial", "missing")
    assert row["sheet_path"] == sheet_path and row["cell"] == source["cell"]
    assert not Path(row["sheet_path"]).is_absolute()
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is None and row["strategy_hypothesis"] is None
    if row["inspection_status"] == "missing":
        assert row["image_path"] is None and row["image_sha256"] is None
        assert row["geometry_tags"] == []
    else:
        assert row["image_path"] == source["image"]
        assert not Path(row["image_path"]).is_absolute()
        assert row["image_sha256"] == source["sha256"]
        assert hashlib.sha256(Path(row["image_path"]).read_bytes()).hexdigest() == source["sha256"]
        assert row["observation"] and row["review_note"]
    if row["inspection_status"] == "partial":
        assert row["occlusion"] == "partial" and row["confidence"] == "low"

counts = {s: sum(r["inspection_status"] == s for r in rows) for s in ("reviewed", "partial", "missing")}
sheets = sorted(set(r["sheet_path"] for r in rows))
assert len(sheets) == 21
checkpoint_path = base / "candidates-12505-12756.jsonl.checkpoint.json"
checkpoint = json.loads(checkpoint_path.read_text())
assert checkpoint["saved_levels"] == [r["level"] for r in rows]
assert checkpoint["inspection_counts"] == counts and checkpoint["remaining_levels"] == []
report = {
    "status": "validated_complete",
    "range": [12505, 12756],
    "saved_count": len(rows),
    "inspection_counts": counts,
    "review_status_counts": {"needs_review": len(rows), "accepted": 0},
    "rendered_numbered_sheets": sheets,
    "rendered_numbered_sheet_count": len(sheets),
    "original_resolution_followups": [12511, 12586, 12680, 12682, 12730],
    "source_hashes_verified": 252,
    "schema_fields_verified": True,
    "numeric_order_verified": True,
    "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    "refinement_history": str(history_path),
}
(base / "candidates-12505-12756.jsonl.validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
