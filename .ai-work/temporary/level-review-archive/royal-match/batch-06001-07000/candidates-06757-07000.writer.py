import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-06757-07000.jsonl"
checkpoint = base / "candidates-06757-07000.checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
fields = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["record_fields"]
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
progress = json.loads(checkpoint.read_text()) if checkpoint.exists() else {"inspected_sheets": []}
for sheet_name, observations in json.load(sys.stdin):
    sheet = next(s for s in manifest["sheets"] if s["sheet"] == sheet_name)
    assert sheet_name not in progress["inspected_sheets"]
    rows = []
    for record in sheet["records"]:
        level = record["level"]
        assert 6757 <= level <= 7000
        missing = not record.get("image")
        details = observations.get(str(level))
        assert missing or details, level
        text, tags, partial = details if details else ("The inspected sheet cell states MISSING SOURCE; no board image is visible.", [], False)
        row = dict(schema_version=2, game="royal-match", level=level,
                   review_status="needs_review",
                   inspection_status="missing" if missing else "partial" if partial else "reviewed",
                   image_path=record.get("image"), image_sha256=record.get("sha256"),
                   sheet_path=str(base / "sheets" / sheet_name), cell=record["cell"],
                   geometry_tags=tags, observation=text,
                   occlusion="unknown" if missing else "partial" if partial else "none",
                   confidence="unknown" if missing else "low" if partial else "medium",
                   verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
                   difficulty_hypothesis=None, strategy_hypothesis=None,
                   review_note="Source unavailable; no geometry inferred." if missing else
                   "Overlay obscures some cells; inspect original resolution before classification." if partial else
                   "Sheet-scale visual evidence only; blocker identities and finer boundary details need original-resolution confirmation. No difficulty or strategy source cited.")
        row["sheet_path"] = str(pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-06001-07000/sheets") / sheet_name)
        assert set(row) == set(fields)
        assert not existing or level > existing[-1]["level"]
        rows.append(row)
    with output.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    existing.extend(rows)
    progress["inspected_sheets"].append(sheet_name)
    progress["saved_rows"] = len(existing)
    progress["last_level"] = existing[-1]["level"]
    progress["inspection_counts"] = {status: sum(r["inspection_status"] == status for r in existing) for status in ["reviewed", "partial", "missing"]}
    checkpoint.write_text(json.dumps(progress, indent=2) + "\n")
    print(sheet_name, progress["saved_rows"], progress["inspection_counts"])
