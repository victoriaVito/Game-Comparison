import collections
import hashlib
import json
import pathlib

base = pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-12001-13000")
output = base / "candidates-12001-12252.jsonl"
rows = list(map(json.loads, output.read_text().splitlines()))
by_level = {r["level"]: r for r in rows}

# Resolve conservatively the covered areas noted during contact-sheet inspection.
covered = {
    12001: "Bright activation effects overlap the lower-right wooden cells.",
    12010: "Two broad red compartments conceal cells surrounding the horizontal cylinders.",
    12011: "Tall red curtain strips conceal their underlying cells.",
    12016: "The green lower cover conceals its underlying cells.",
    12024: "The numbered green compartments conceal their underlying cells.",
    12030: "The left and right green covers conceal their underlying cells.",
    12038: "The middle-right red curtain conceals its underlying cells.",
    12040: "The numbered green side covers conceal their cells; purple glow also limits route detail.",
    12046: "Activation glow overlaps the bottom-right bottles and brown covered cells.",
    12061: "The green lower compartments conceal their underlying cells.",
}
for level, evidence in covered.items():
    row = by_level[level]
    row["inspection_status"] = "partial"
    row["occlusion"] = "partial"
    row["confidence"] = "low"
    if evidence not in row["observation"]:
        row["observation"] += " " + evidence
    row["review_note"] = "Full cell interpretation is withheld because of the visible cover or activation effect described in the observation. Candidate geometry only."

by_level[12130]["geometry_tags"] = ["split_regions", "layered_bands"]
by_level[12130]["observation"] = "A central tile rectangle narrows downward between two red squares into a cyan and small-red-item stem above blue numbered squares. Two isolated blue diamond rails ending in purple sockets stand at the sides; original resolution shows floor gaps between each rail and both the central grid and bottom base."
by_level[12130]["review_note"] = "Original-resolution follow-up confirms both side rails are disconnected from the central field by visible floor gaps. Candidate geometry only."
by_level[12177]["geometry_tags"] = ["split_regions", "asymmetric"]
by_level[12177]["observation"] = "The match grid consists of a broad right tile rectangle adjoining four blue horizontal boxes on its left, with a small empty notch between the middle boxes. An isolated tall green cylinder stands farther left across a visible floor gap confirmed at original resolution. The brick wall and numbered boss beneath are a separate arena."
by_level[12177]["review_note"] = "Original-resolution follow-up confirms the cylinder's floor gap. The boss arena is excluded from match-grid connectivity."
by_level[12182]["review_note"] = "Original-resolution follow-up shows blank outlined cells between the far-left staggered brown blocks. Their playable status is not established; split_regions is withheld. Brown strips are not treated as evidence of disconnection."
by_level[12034]["observation"] = "The upper-left tile pocket widens rightward in two lower rows, then widens again into a broad rocky lower rectangle. A blue diamond column borders the lower left; three blue numbered squares and two red squares descend diagonally beside a cyan jar at lower right. The stepped upper-right outer boundary is distinct from the diagonal blocker arrangement inside the lower rectangle."
by_level[12034]["review_note"] = "Original-resolution follow-up confirms successive widening steps in the upper-right outer boundary. stair_step refers to that boundary, not the diagonal numbered blockers."
followup = " Original-resolution follow-up confirms the left dispenser islands and the tall right curtain; hidden connections remain unverified."
if followup not in by_level[12079]["review_note"]:
    by_level[12079]["review_note"] += followup
for level in [12121, 12147, 12180]:
    followup = " Original-resolution image was also rendered to verify the visible floor gaps."
    if followup not in by_level[level]["review_note"]:
        by_level[level]["review_note"] += followup

output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
contract = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((base / "sheets/index.json").read_text())
sources = {
    source["level"]: (sheet["sheet"], source)
    for sheet in index["sheets"] for source in sheet["records"]
}
assert len(rows) == 252
assert [row["level"] for row in rows] == list(range(12001, 12253))
assert len(by_level) == len(rows)
for row in rows:
    assert set(row) == set(contract["record_fields"])
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["game"] == "royal-match" and row["review_status"] == "needs_review"
    assert row["inspection_status"] in {"reviewed", "partial"}
    assert row["geometry_tags"] and set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is row["strategy_hypothesis"] is None
    sheet_name, source = sources[row["level"]]
    assert row["image_path"] == source["image"]
    assert row["image_sha256"] == source["sha256"]
    assert row["cell"] == source["cell"]
    assert row["sheet_path"] == str(base / "sheets" / sheet_name)
    assert not pathlib.Path(row["image_path"]).is_absolute()
    assert not pathlib.Path(row["sheet_path"]).is_absolute()
    assert hashlib.sha256(pathlib.Path(row["image_path"]).read_bytes()).hexdigest() == row["image_sha256"]
    if row["inspection_status"] == "partial":
        assert row["occlusion"] == "partial" and row["confidence"] == "low"
    else:
        assert row["occlusion"] == "none"
counts = dict(collections.Counter(row["inspection_status"] for row in rows))
sheets = list(dict.fromkeys(row["sheet_path"] for row in rows))
assert len(sheets) == 21
report = dict(
    assigned_range=[12001, 12252], saved_range=[12001, 12252],
    saved_count=len(rows), saved_levels=[r["level"] for r in rows],
    inspection_counts=counts, needs_review_count=len(rows), accepted_count=0,
    missing_count=0, not_reviewed_count=0, inspected_sheets=sheets,
    original_resolution_followups=[12034, 12079, 12121, 12130, 12147, 12177, 12180, 12182],
    output_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
    validation="passed: contract fields, numeric order, metadata, hashes, statuses and evidence constraints",
    blocker=None,
)
(base / "candidates-12001-12252.jsonl.checkpoint.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k not in {"saved_levels", "inspected_sheets"}}, indent=2))
