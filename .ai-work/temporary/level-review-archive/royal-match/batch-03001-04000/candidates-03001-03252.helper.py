import json
import pathlib
import sys

base = pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-03001-04000")
output = base / "candidates-03001-03252.jsonl"
manifest = json.loads((base / "sheets/index.json").read_text())
fields = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["record_fields"]
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
for sheet_input in json.loads(sys.stdin.read()):
    start, observations = sheet_input
    sheet = next(s for s in manifest["sheets"] if s["records"][0]["level"] == start)
    assert len(observations) == len(sheet["records"]) == 12
    assert not existing or existing[-1]["level"] == start - 1
    rows = []
    for record, entry in zip(sheet["records"], observations):
        text, tags, partial = entry
        available = record.get("image") and pathlib.Path(record["image"]).is_file()
        row = dict(
            schema_version=2, game="royal-match", level=record["level"],
            review_status="needs_review",
            inspection_status=("partial" if partial else "reviewed") if available else "missing",
            image_path=record["image"] if available else None,
            image_sha256=record["sha256"] if available else None,
            sheet_path=str(base / "sheets" / sheet["sheet"]), cell=record["cell"],
            geometry_tags=tags if available else [],
            observation=text if available else "Original image unavailable in the local manifest or filesystem.",
            occlusion="partial" if partial else "none", confidence="low" if partial else "medium",
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note="Concealment or visual obstruction is described in observation; full layout requires unobstructed source-resolution follow-up." if partial else "Sheet-scale visual evidence only; blocker identities and hidden mechanics are unverified.",
        )
        assert set(row) == set(fields)
        rows.append(row)
    with output.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    existing.extend(rows)
    checkpoint = dict(last_inspected_sheet=sheet["sheet"], last_saved_level=existing[-1]["level"],
                      inspected_sheets=len(existing)//12, saved_rows=len(existing),
                      reviewed=sum(r["inspection_status"] == "reviewed" for r in existing),
                      partial=sum(r["inspection_status"] == "partial" for r in existing))
    (base / "candidates-03001-03252.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(json.dumps(checkpoint))
