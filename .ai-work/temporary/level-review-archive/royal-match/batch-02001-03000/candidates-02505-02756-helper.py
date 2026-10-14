import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-02505-02756.jsonl"
checkpoint = base / "candidates-02505-02756-checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
lookup = {
    record["level"]: (sheet["sheet"], record)
    for sheet in manifest["sheets"]
    for record in sheet["records"]
}
rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
seen = {row["level"] for row in rows}
start = int(sys.argv[1])
observations = sys.stdin.read().strip().splitlines()
assert len(observations) == 12
for level, line in enumerate(observations, start):
    assert 2505 <= level <= 2756 and level not in seen
    tags, occlusion, observation = line.split("|", 2)
    sheet, source = lookup[level]
    exists = pathlib.Path(source["image"]).is_file()
    row = dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review",
        inspection_status=("partial" if occlusion != "none" else "reviewed") if exists else "missing",
        image_path=source["image"] if exists else None,
        image_sha256=source["sha256"] if exists else None,
        sheet_path=str(base / "sheets" / sheet) if exists else None,
        cell=source["cell"] if exists else None,
        geometry_tags=tags.split(",") if tags and exists else [],
        observation=observation if exists else "Original image missing.",
        occlusion=occlusion if exists else "unknown",
        confidence=("low" if occlusion != "none" else "medium") if exists else "unknown",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note=("Overlay or glare obscures cells; hidden continuity and blocker identity remain unresolved."
                     if occlusion != "none" else
                     "Contact-sheet visual evidence only; covered cells are not empty gaps. Fine blocker identities and unshown mechanics remain unverified.")
        if exists else "Manifest source is not available.",
    )
    rows.append(row)
rows.sort(key=lambda row: row["level"])
assert len({row["level"] for row in rows}) == len(rows)
output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
checkpoint.write_text(json.dumps({
    "range": [2505, 2756],
    "saved_rows": len(rows),
    "inspected_sheets": sorted({row["sheet_path"] for row in rows if row["sheet_path"]}),
    "last_saved_level": rows[-1]["level"],
    "inspection_counts": {status: sum(row["inspection_status"] == status for row in rows)
                          for status in ["reviewed", "partial", "missing"]},
}, indent=2) + "\n")
print(f"Checkpoint: {start}-{start + 11}; saved {len(rows)} rows")
