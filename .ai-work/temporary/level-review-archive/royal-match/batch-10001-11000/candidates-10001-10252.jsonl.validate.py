import collections
import hashlib
import json
import pathlib

root = pathlib.Path.cwd()
directory = root / ".ai-work/temporary/level-review-archive/royal-match/batch-10001-11000"
output = directory / "candidates-10001-10252.jsonl"
rows = [json.loads(line) for line in output.read_text().splitlines()]
index = json.loads((directory / "sheets/index.json").read_text())
contract = json.loads((root / ".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
sources = {record["level"]: (sheet["sheet"], record)
           for sheet in index["sheets"] for record in sheet["records"]}
assert [row["level"] for row in rows] == list(range(10001, 10253))
for row in rows:
    sheet, source = sources[row["level"]]
    assert set(row) == set(contract["record_fields"])
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["review_status"] == "needs_review"
    assert row["game"] == "royal-match"
    assert row["image_path"] == source["image"]
    assert row["image_sha256"] == source["sha256"]
    assert hashlib.sha256((root / row["image_path"]).read_bytes()).hexdigest() == source["sha256"]
    assert row["cell"] == source["cell"]
    assert row["sheet_path"] == (directory / "sheets" / sheet).relative_to(root).as_posix()
    assert (root / row["sheet_path"]).is_file()
    assert row["inspection_status"] in ("reviewed", "partial")
    assert row["observation"]
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    assert len(row["geometry_tags"]) == len(set(row["geometry_tags"]))
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is None and row["strategy_hypothesis"] is None
    if row["inspection_status"] == "partial":
        assert row["occlusion"] in ("partial", "severe")
        assert row["confidence"] == "low" and row["review_note"].startswith("Occlusion:")
    else:
        assert row["occlusion"] == "none"
counts = dict(collections.Counter(row["inspection_status"] for row in rows))
checkpoint = json.loads((directory / "candidates-10001-10252.jsonl.checkpoint.json").read_text())
assert checkpoint["status"] == "complete"
assert checkpoint["saved_levels"] == list(range(10001, 10253))
assert checkpoint["inspection_counts"] == counts
assert len(checkpoint["completed_sheets"]) == 21
report = {
    "coverage": [10001, 10252], "count": len(rows), "inspection_counts": counts,
    "needs_review": len(rows), "accepted": 0, "missing": 0,
    "rendered_numbered_sheets": checkpoint["completed_sheets"],
    "verification": "Exact ordered coverage, contract fields, integer schema, relative source and sheet paths, index cells, source SHA-256, candidate tags, unknown verified claims and null hypotheses checked.",
    "sha256": hashlib.sha256(output.read_bytes()).hexdigest()
}
(directory / "candidates-10001-10252.jsonl.validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
