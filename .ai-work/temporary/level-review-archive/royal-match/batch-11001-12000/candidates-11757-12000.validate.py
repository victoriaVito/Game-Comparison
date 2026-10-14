import hashlib
import json
from collections import Counter
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-11001-12000")
output = base / "candidates-11757-12000.jsonl"
contract = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((base / "sheets/index.json").read_text())
rows = list(map(json.loads, output.read_text().splitlines()))
followups = {
    11780: "Original-resolution follow-up: a full vertical background gap separates the right purple-block rectangle from the left region; the top and bottom blue-pot protrusions do not touch it.",
    11804: "Original-resolution follow-up: the diagonal horizontal-barrel chain is separated from the upper tile staircase by visible background throughout; the cyan round device at lower-right is also isolated.",
    11901: "Original-resolution follow-up: the upper container U and the lower stepped tile arms have visible background separation; the lower arms are also divided by a narrow vertical background gap.",
    11993: "Original-resolution follow-up: the three stacked teal devices at lower-left are separated from the top tile band by a horizontal background gap and from the barrel bank by a vertical background gap.",
}
for row in rows:
    level = row["level"]
    if level in followups and followups[level] not in row["review_note"]:
        row["review_note"] += " " + followups[level]
        row["observation"] += " " + followups[level].split(": ", 1)[1]
        if "split_regions" not in row["geometry_tags"]:
            row["geometry_tags"].append("split_regions")

assert [r["level"] for r in rows] == list(range(11757, 12001))
lookup = {
    record["level"]: (sheet, record)
    for sheet in index["sheets"]
    for record in sheet["records"]
}
for row in rows:
    sheet, source = lookup[row["level"]]
    assert set(row) == set(contract["record_fields"])
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["review_status"] == "needs_review"
    assert row["inspection_status"] in ("reviewed", "partial")
    assert row["image_path"] == source["image"] and not Path(row["image_path"]).is_absolute()
    assert row["image_sha256"] == source["sha256"]
    assert hashlib.sha256(Path(row["image_path"]).read_bytes()).hexdigest() == source["sha256"]
    assert row["sheet_path"] == str(base / "sheets" / sheet["sheet"])
    assert Path(row["sheet_path"]).is_file() and row["cell"] == source["cell"]
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    assert len(row["geometry_tags"]) == len(set(row["geometry_tags"]))
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is row["strategy_hypothesis"] is None
    assert row["observation"] and row["review_note"]
    assert row["confidence"] == "medium"
    assert row["occlusion"] == ("partial" if row["inspection_status"] == "partial" else "none")

output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
summary = {
    "coverage": [11757, 12000],
    "rows": len(rows),
    "inspection_counts": dict(Counter(row["inspection_status"] for row in rows)),
    "partial_levels": [row["level"] for row in rows if row["inspection_status"] == "partial"],
    "needs_review": len(rows),
    "accepted": 0,
    "missing": 0,
    "uninspected": 0,
    "inspected_sheets": sorted({row["sheet_path"] for row in rows}),
    "original_resolution_followups": [
        f"sources/royal-match-level-archive/levels/{level}/board.jpg"
        for level in followups
    ],
    "source_hashes_verified": len(rows),
    "contract_fields_verified": True,
    "all_verified_claims_unknown": True,
    "all_hypotheses_null": True,
    "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
}
assert len(summary["inspected_sheets"]) == 21
(base / "candidates-11757-12000.validation.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({k: v for k, v in summary.items() if k not in (
    "inspected_sheets", "original_resolution_followups"
)}, indent=2))
