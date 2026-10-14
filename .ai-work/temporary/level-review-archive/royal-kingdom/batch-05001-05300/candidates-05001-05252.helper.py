import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-05001-05252.jsonl"
checkpoint = base / "candidates-05001-05252.checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
for batch in json.load(sys.stdin):
    start = batch["start"]
    sheet = next(s for s in manifest["sheets"] if s["records"][0]["level"] == start)
    assert len(batch["observations"]) == len(sheet["records"]) == 12
    assert not any(start <= r["level"] < start + 12 for r in rows)
    for source, item in zip(sheet["records"], batch["observations"]):
        observation, tags = item[:2]
        partial = len(item) > 2 and item[2]
        rows.append({
            "schema_version": 2,
            "game": "royal-kingdom",
            "level": source["level"],
            "review_status": "needs_review",
            "inspection_status": "partial" if partial else "reviewed",
            "image_path": source["image"],
            "image_sha256": source["sha256"],
            "sheet_path": str(base.relative_to(pathlib.Path.cwd()) / "sheets" / sheet["sheet"]),
            "cell": source["cell"],
            "geometry_tags": tags,
            "observation": observation,
            "occlusion": "partial" if partial else "none",
            "confidence": "low" if partial else "medium",
            "verified_difficulty": "unknown",
            "verified_strategy": "unknown",
            "verified_evidence": [],
            "difficulty_hypothesis": None,
            "strategy_hypothesis": None,
            "review_note": (
                "Overlay conceals board cells; original-resolution follow-up is needed."
                if partial else
                "Sheet-scale visual evidence only; blocker identities and covered-cell connectivity are not verified. No local difficulty or strategy evidence consulted."
            ),
        })
    rows.sort(key=lambda r: r["level"])
    output.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    checkpoint.write_text(json.dumps({
        "last_saved_level": start + 11,
        "saved_rows": len(rows),
        "inspected_sheets": sorted(set(r["sheet_path"] for r in rows)),
        "reviewed": sum(r["inspection_status"] == "reviewed" for r in rows),
        "partial": sum(r["inspection_status"] == "partial" for r in rows),
        "status": "complete" if len(rows) == 252 else "in_progress",
    }, indent=2) + "\n")
    print(f"Checkpoint: {start}-{start + 11}, {len(rows)} rows saved")
