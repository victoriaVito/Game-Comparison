import hashlib
import json
from collections import Counter
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-04001-05000")
output = base / "candidates-04001-04252.jsonl"
checkpoint = base / "candidates-04001-04252.checkpoint.json"
contract = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((base / "sheets/index.json").read_text())
manifest = {r["level"]: (s["sheet"], r) for s in index["sheets"] for r in s["records"]}
rows = [json.loads(line) for line in output.read_text().splitlines()]
assert [r["level"] for r in rows] == list(range(4001, 4253))

withheld = {
    4024: ("split_regions", "Orange covered panels and local recesses do not establish disconnected regions; split_regions withheld."),
    4032: ("split_regions", "Small side-block junctions are ambiguous at sheet resolution; split_regions withheld."),
    4059: ("open_center", "Only a narrow upper internal slot is empty; open_center withheld because the main center contains tiles."),
    4100: ("open_center", "Central coin cells remain occupied; open_center withheld despite visible lateral cavities."),
    4160: ("open_center", "The inner central region is occupied; only the surrounding moat is empty, so open_center is withheld."),
}
for row in rows:
    if row["level"] in withheld:
        tag, note = withheld[row["level"]]
        row["geometry_tags"] = [t for t in row["geometry_tags"] if t != tag]
        if note not in row["review_note"]:
            row["review_note"] += " " + note
    if row["level"] == 4032:
        row["observation"] = (
            "A tall tile rectangle at right has paw pots and pink squares along its left edge. "
            "Three left-side blocks contain an upper paw-pot square, a middle hanging-red-object panel, "
            "and a lower tan-covered square. Visible gutters surround parts of the upper and lower blocks; "
            "the middle panel's junction with the pink edge needs higher-resolution confirmation."
        )
    if row["inspection_status"] == "partial":
        row["review_note"] = (
            "Overlay or animation obscures board cells as described in the observation; "
            "hidden cells and the complete layout cannot be established."
        )
    assert set(row) == set(contract["record_fields"])
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["game"] == "royal-match" and row["review_status"] == "needs_review"
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is None and row["strategy_hypothesis"] is None
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    sheet, source = manifest[row["level"]]
    assert row["sheet_path"] == str(base / "sheets" / sheet)
    assert row["cell"] == source["cell"]
    assert Path(row["sheet_path"]).is_file()
    if source.get("image"):
        assert row["inspection_status"] in ("reviewed", "partial")
        assert row["image_path"] == source["image"]
        assert row["image_sha256"] == source["sha256"]
        assert not Path(row["image_path"]).is_absolute()
        assert hashlib.sha256(Path(row["image_path"]).read_bytes()).hexdigest() == source["sha256"]
        assert row["occlusion"] == ("partial" if row["inspection_status"] == "partial" else "none")
    else:
        assert row["inspection_status"] == "missing"
        assert row["image_path"] is None and row["image_sha256"] is None
        assert row["geometry_tags"] == []
    assert len(row["observation"]) > 50

output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
counts = Counter(row["inspection_status"] for row in rows)
state = json.loads(checkpoint.read_text())
assert state["saved_rows"] == 252 and state["last_saved_level"] == 4252
assert len(state["inspected_sheets"]) == 21
state["validation"] = {
    "status": "passed",
    "exact_fields": True,
    "numeric_order": True,
    "manifest_paths_cells_hashes": True,
    "original_image_sha256_verified": sum(row["image_path"] is not None for row in rows),
    "all_needs_review": True,
    "unknown_verified_claims": True,
    "withheld_ambiguous_tags_levels": list(withheld),
}
checkpoint.write_text(json.dumps(state, indent=2) + "\n")
print(json.dumps({
    "path": str(output), "rows": len(rows), "inspected_sheets": len(state["inspected_sheets"]),
    "reviewed": counts["reviewed"], "partial": counts["partial"], "missing": counts["missing"],
    "validation": "passed",
}, indent=2))
