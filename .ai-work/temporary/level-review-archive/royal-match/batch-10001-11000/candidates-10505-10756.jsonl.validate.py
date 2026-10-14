import collections
import hashlib
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[5]
OUTPUT = DIRECTORY / "candidates-10505-10756.jsonl"
rows = [json.loads(line) for line in OUTPUT.read_text().splitlines()]
contract = json.loads((ROOT / ".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((DIRECTORY / "sheets/index.json").read_text())
sources = {
    source["level"]: (sheet, source)
    for sheet in index["sheets"]
    for source in sheet["records"]
    if 10505 <= source["level"] <= 10756
}
assert [row["level"] for row in rows] == list(range(10505, 10757))
for row in rows:
    sheet, source = sources[row["level"]]
    assert set(row) == set(contract["record_fields"])
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["game"] == "royal-match"
    assert row["review_status"] == "needs_review"
    assert row["inspection_status"] in {"reviewed", "partial", "missing"}
    assert row["cell"] == source["cell"]
    assert row["sheet_path"] == (DIRECTORY / "sheets" / sheet["sheet"]).relative_to(ROOT).as_posix()
    assert (ROOT / row["sheet_path"]).is_file()
    assert set(row["geometry_tags"]).issubset(contract["geometry_tags"])
    assert row["observation"] and row["review_note"]
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is None and row["strategy_hypothesis"] is None
    if source.get("image") is None:
        assert row["inspection_status"] == "missing"
        assert row["image_path"] is None and row["image_sha256"] is None
        assert row["geometry_tags"] == []
    else:
        assert row["image_path"] == source["image"]
        assert row["image_sha256"] == source["sha256"]
        assert hashlib.sha256((ROOT / row["image_path"]).read_bytes()).hexdigest() == row["image_sha256"]
        assert not Path(row["image_path"]).is_absolute()
        assert row["confidence"] in {"medium", "low", "high"}
        assert row["occlusion"] == ("partial" if row["inspection_status"] == "partial" else "none")
checkpoint = json.loads((DIRECTORY / (OUTPUT.name + ".checkpoint.json")).read_text())
assert len(checkpoint["completed_sheets"]) == 21
assert len(set(checkpoint["completed_sheets"])) == 21
assert checkpoint["saved_range"] == [10505, 10756]
assert checkpoint["saved_rows"] == len(rows) == 252
assert checkpoint["counts"] == {
    status: sum(row["inspection_status"] == status for row in rows)
    for status in ["reviewed", "partial", "missing", "not_reviewed"]
}
print(json.dumps({
    "result": "passed",
    "saved_range": [10505, 10756],
    "rows": len(rows),
    "counts": dict(collections.Counter(row["inspection_status"] for row in rows)),
    "needs_review": 252,
    "accepted": 0,
    "rendered_numbered_sheets": 21,
    "missing_levels": [row["level"] for row in rows if row["inspection_status"] == "missing"],
    "jsonl_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
}, indent=2))
