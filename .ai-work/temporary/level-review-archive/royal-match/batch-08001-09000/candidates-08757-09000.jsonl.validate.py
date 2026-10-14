import hashlib
import json
from collections import Counter
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-08001-09000")
output = base / "candidates-08757-09000.jsonl"
rows = [json.loads(line) for line in output.read_text().splitlines()]
index = json.loads((base / "sheets/index.json").read_text())
contract = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
sources = {r["level"]: (s["sheet"], r) for s in index["sheets"] for r in s["records"]}
for row in rows:
    if row["level"] == 8980:
        row["geometry_tags"] = []
        row["observation"] = (
            "Narrow central upper tiles lead into two short and three wide horizontal blue bands "
            "flanked by red containers; green numbered panels border both sides, with upper "
            "background slots but lower blue bands touching their edges."
        )
        row["review_note"] = (
            "Original-resolution follow-up corrects the sheet-scale separation hypothesis: "
            "upper slots do not prove disconnected regions because lower bands meet the panels. "
            "Green panels conceal their side cells."
        )
    if row["level"] in (8900, 9000):
        row["review_note"] += " Original-resolution follow-up confirms the visible separating background gaps."
    if row["inspection_status"] != "missing" and not row["geometry_tags"]:
        row["review_note"] += " No geometry tag assigned: visible mixed structure does not establish a reliable candidate category."
output.write_text("".join(json.dumps(row) + "\n" for row in rows))

assert [r["level"] for r in rows] == list(range(8757, 9001))
hashes_checked = 0
for row in rows:
    sheet, source = sources[row["level"]]
    assert set(row) == set(contract["record_fields"])
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["game"] == "royal-match" and row["review_status"] == "needs_review"
    assert row["sheet_path"] == str(base / "sheets" / sheet)
    assert row["cell"] == source["cell"]
    assert row["image_path"] == source.get("image")
    assert row["image_sha256"] == source.get("sha256")
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is row["strategy_hypothesis"] is None
    assert row["observation"] and row["review_note"]
    if row["image_path"] is None:
        assert row["inspection_status"] == "missing"
        assert row["image_sha256"] is None and row["geometry_tags"] == []
    else:
        assert not Path(row["image_path"]).is_absolute()
        assert hashlib.sha256(Path(row["image_path"]).read_bytes()).hexdigest() == row["image_sha256"]
        hashes_checked += 1
        assert row["inspection_status"] in ("reviewed", "partial")
        if row["inspection_status"] == "partial":
            assert row["occlusion"] == "partial" and row["confidence"] == "low"
sheet_checkpoints = []
for sheet in index["sheets"]:
    selected = [r for r in rows if sources[r["level"]][0] == sheet["sheet"]]
    if selected:
        sheet_checkpoints.append({
            "sheet_path": str(base / "sheets" / sheet["sheet"]),
            "saved_range": [selected[0]["level"], selected[-1]["level"]],
            "rows": len(selected),
            "counts": dict(Counter(r["inspection_status"] for r in selected))
        })
assert len(sheet_checkpoints) == 21
result = {
    "status": "validated", "range": [8757, 9000], "rows": len(rows),
    "counts": dict(Counter(r["inspection_status"] for r in rows)),
    "needs_review": len(rows), "accepted": 0,
    "source_hashes_verified": hashes_checked,
    "numbered_sheets_rendered": 21,
    "original_resolution_followups": [8900, 8980, 9000],
    "sheet_checkpoints": sheet_checkpoints
}
(base / "candidates-08757-09000.jsonl.validation.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "sheet_checkpoints"}, indent=2))
