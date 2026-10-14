import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-05757-06000.jsonl"
checkpoint = base / "candidates-05757-06000.checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
entries = {
    r["level"]: (s["sheet"], r)
    for s in manifest["sheets"] for r in s["records"]
}
rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
seen = {r["level"] for r in rows}
payload = json.load(sys.stdin)
for start, observations in payload:
    sheet_levels = []
    for offset, description in enumerate(observations):
        level = start + offset
        assert 5757 <= level <= 6000 and level not in seen
        sheet, source = entries[level]
        tags, observation = description.split("|", 1)
        partial = observation.startswith("PARTIAL ")
        observation = observation.removeprefix("PARTIAL ")
        row = dict(
            schema_version=2, game="royal-match", level=level,
            review_status="needs_review",
            inspection_status="partial" if partial else "reviewed",
            image_path=source["image"], image_sha256=source["sha256"],
            sheet_path=str(base / "sheets" / sheet), cell=source["cell"],
            geometry_tags=tags.split(",") if tags else [], observation=observation,
            occlusion="partial" if partial else "none",
            confidence="low" if partial else "medium",
            verified_difficulty="unknown", verified_strategy="unknown",
            verified_evidence=[], difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note="Contact-sheet visual review; blocker identities and concealed cells need original-resolution confirmation. No verified difficulty or strategy evidence.",
        )
        row["sheet_path"] = str(pathlib.Path(row["sheet_path"]).relative_to(pathlib.Path.cwd()))
        rows.append(row)
        seen.add(level)
        sheet_levels.append(level)
    rows.sort(key=lambda r: r["level"])
    output.write_text("".join(json.dumps(r) + "\n" for r in rows))
    checkpoint.write_text(json.dumps({
        "saved_rows": len(rows), "last_completed_sheet": sheet,
        "last_sheet_levels": sheet_levels, "inspected_levels": sorted(seen),
        "status": "complete" if len(rows) == 244 else "in_progress"
    }, indent=2) + "\n")
    print(sheet, len(sheet_levels), "saved; total", len(rows))
