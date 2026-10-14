import hashlib
import json
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-13001-13500")
output = base / "candidates-13001-13252.jsonl"
rows = [json.loads(line) for line in output.read_text().splitlines()]
by_level = {row["level"]: row for row in rows}

by_level[13005].update(
    geometry_tags=["split_regions", "asymmetric"],
    observation="Upper-left tile rectangle touches the broad lower yellow covered region. Upper-right yellow panel and its four purple pots are separated from both by visible background strips. Five diagonal arrow cells cross the lower panel, with four upward arrows at its lower right.",
    review_note="Original-resolution image rendered: a vertical gap beside the upper-right panel and a horizontal gap beneath its pots isolate that region. The diagonal arrows do not describe a stepped playable boundary."
)
by_level[13021].update(
    observation="Upper tile rectangle extends over two tall cyan side strips around a central blue-object square and six brown cylinders beneath. Two small numbered objects project from the left with empty background between them; the bottom-left blue structure touches the left cyan strip.",
    review_note="Original-resolution image rendered: the bottom-left blue structure adjoins the cyan strip and is not an isolated region. The upper and lower left numbered objects also touch the field."
)
by_level[13035]["review_note"] = (
    "Original-resolution image rendered: offset pink side blocks and intervening background "
    "slots are visible. Their diagonal/edge attachment is not used to assert split_regions."
)
by_level[13090]["occlusion"] = "severe"
by_level[13100].update(
    geometry_tags=["split_regions"],
    observation="Two tall tile strips stand at the left and right. Middle coin cells alternate with empty square background gaps in a checker arrangement; side coins touch the tile strips, but no uninterrupted edge-connected cell route crosses the center. Large background recesses lie above and below the coin pattern.",
    review_note="Original-resolution image rendered: the checker holes are empty background, not blockers. Split_regions refers to visible edge-disconnected regions; diagonal visual contact does not establish an edge-connected match grid."
)
by_level[13102].update(
    geometry_tags=["split_regions", "stair_step", "asymmetric"],
    observation="Upper-left tile wedge ends along stepped brown panels and red-green round pieces. A broad diagonal exposed-background corridor separates it from the lower-right wedge of brown panels and dark stones; both wedges have stepped outer boundaries.",
    review_note="Original-resolution image rendered: the diagonal corridor is exposed gold-toned scenery without cells, confirming separate regions. Sparkles still obscure several lower-right stones, so inspection remains partial."
)
by_level[13191].update(
    observation="Two tall beige side strips join the lower tile rectangle and its side arrows around a wide upper background opening. A separate framed brown scene sits above the tiles across that opening; the scene is not used as match-grid geometry. A pink bar runs beneath the tiles.",
    review_note="Original-resolution image rendered: clear background separates the upper framed scene from the match tiles. Arena/scene contents are recorded separately from match-grid geometry."
)
by_level[13200].update(
    observation="A wide middle tile crossbar surrounds a vertical coin spine. Four three-by-three coin blocks occupy the upper and lower corners, separated from the center spine by visible background slots; their corners meet the ends of the crossbar diagonally.",
    review_note="Original-resolution image rendered: the corner blocks have diagonal-only contact with the central field. Split_regions is withheld because interpreting diagonal attachment as connectivity needs review; the visible slots are described directly."
)

for level, tag, explanation in [
    (13054, "central_mass", "Wrapped cells frame the upper tiles and a narrow stem; a dominant central blocker mass is not established."),
    (13135, "central_mass", "Flower squares are predominantly side borders; they do not establish a central blocker mass."),
    (13159, "central_mass", "The middle remains tiles, while flowers and clocks flank it; central_mass is withheld."),
    (13166, "stair_step", "Stepped chevron/blocker heights inside the field do not prove a stepped playable outer boundary."),
    (13215, "central_mass", "The small blue cross and flanking flowers do not establish a dominant central blocker mass.")
]:
    by_level[level]["geometry_tags"].remove(tag)
    by_level[level]["review_note"] += " " + explanation

index = json.loads((base / "sheets/index.json").read_text())
sources = {
    source["level"]: (sheet["sheet"], source)
    for sheet in index["sheets"][:21] for source in sheet["records"]
}
allowed_tags = set(json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["geometry_tags"])
assert len(rows) == 252
assert [row["level"] for row in rows] == list(range(13001, 13253))
fields = set(json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["record_fields"])
for row in rows:
    sheet_name, source = sources[row["level"]]
    assert set(row) == fields
    assert type(row["schema_version"]) is int and row["schema_version"] == 2
    assert row["game"] == "royal-match"
    assert row["review_status"] == "needs_review"
    assert row["inspection_status"] in {"reviewed", "partial"}
    assert row["image_path"] == source["image"] and not Path(row["image_path"]).is_absolute()
    assert row["image_sha256"] == source["sha256"]
    assert hashlib.sha256(Path(row["image_path"]).read_bytes()).hexdigest() == source["sha256"]
    assert row["sheet_path"] == str(base / "sheets" / sheet_name)
    assert row["cell"] == source["cell"] and Path(row["sheet_path"]).is_file()
    assert set(row["geometry_tags"]) <= allowed_tags
    assert row["observation"] and row["review_note"]
    assert row["occlusion"] in {"none", "partial", "severe", "unknown"}
    assert row["confidence"] in {"high", "medium", "low", "unknown"}
    assert row["inspection_status"] != "partial" or row["occlusion"] != "none"
    assert row["verified_difficulty"] == row["verified_strategy"] == "unknown"
    assert row["verified_evidence"] == []
    assert row["difficulty_hypothesis"] is row["strategy_hypothesis"] is None
output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
checkpoint_path = base / "candidates-13001-13252.jsonl.checkpoint.json"
checkpoint = json.loads(checkpoint_path.read_text())
checkpoint.update({
    "rendered_numbered_sheets": [str(base / "sheets" / sheet["sheet"]) for sheet in index["sheets"][:21]],
    "original_resolution_followups": [13005, 13007, 13021, 13035, 13100, 13102, 13191, 13200],
    "validation": "Passed: 252 ordered contract rows; index paths, cells and source SHA-256 match; candidate-only status; no verified difficulty or strategy.",
    "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest()
})
checkpoint_path.write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps({key: checkpoint[key] for key in ["saved_range", "saved_rows", "inspected_sheets", "counts", "complete", "validation", "output_sha256"]}, indent=2))
