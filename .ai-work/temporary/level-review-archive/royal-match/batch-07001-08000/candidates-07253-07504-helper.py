import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-07253-07504.jsonl"
checkpoint = base / "candidates-07253-07504-checkpoint.json"
index = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
notes = json.loads(sys.stdin.read())
sheet = next(s for s in index["sheets"] if s["records"][0]["level"] == start)
rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not any(start <= row["level"] <= start + 11 for row in rows)
assert len(notes) == 12
for record, note in zip(sheet["records"], notes):
    missing = "image" not in record
    text, tags, partial = note if isinstance(note, list) else (note, [], False)
    rows.append(dict(
        schema_version=2, game="royal-match", level=record["level"],
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=record.get("image"), image_sha256=record.get("sha256"),
        sheet_path=(base / "sheets" / sheet["sheet"]).as_posix(), cell=record["cell"],
        geometry_tags=[] if missing else tags,
        observation="The inspected sheet cell is marked missing; no source board is available." if missing else text,
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Missing manifest entry." if missing else
        "Overlay obscures cells; full boundary and blocker identities need original-resolution review." if partial else
        "Sheet-scale visual evidence only; blocker identities and unsupported geometry labels are withheld."
    ))
rows.sort(key=lambda row: row["level"])
output.write_text("".join(json.dumps(row) + "\n" for row in rows))
done = json.loads(checkpoint.read_text()) if checkpoint.exists() else {"inspected_sheets": []}
done["inspected_sheets"].append(sheet["sheet"])
done["rows_saved"] = len(rows)
done["counts"] = {status: sum(r["inspection_status"] == status for r in rows) for status in ("reviewed", "partial", "missing")}
checkpoint.write_text(json.dumps(done, indent=2) + "\n")
print(sheet["sheet"], done["counts"])
