import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-01757-02000.jsonl"
contract = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
index = json.loads((base / "sheets/index.json").read_text())
manifest = {
    r["level"]: (s["sheet"], r)
    for s in index["sheets"]
    for r in s["records"]
}
rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
for line in sys.stdin.read().strip().splitlines():
    level, tags, observation, *flags = line.split("|")
    level = int(level)
    assert level == 1757 + len(rows)
    sheet, source = manifest[level]
    partial = bool(flags and flags[0] == "partial")
    row = dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review",
        inspection_status="partial" if partial else "reviewed",
        image_path=source["image"], image_sha256=source["sha256"],
        sheet_path=(base / "sheets" / sheet).as_posix(), cell=source["cell"],
        geometry_tags=tags.split(",") if tags else [],
        observation=observation, occlusion="partial" if partial else "none",
        confidence="low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown",
        verified_evidence=[], difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="Overlay prevents full covered-cell interpretation; original-resolution follow-up needed." if partial else "Contact-sheet visual evidence only; blocker identities and fine cell details remain unverified."
    )
    assert set(row) == set(contract["record_fields"])
    assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
    assert pathlib.Path(source["image"]).is_file()
    rows.append(row)
    with output.open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    if source["cell"] == 12 or level == 2000:
        checkpoint = dict(last_saved_level=level, saved_rows=len(rows),
                          inspected_sheets=list(dict.fromkeys(r["sheet_path"] for r in rows)),
                          reviewed=sum(r["inspection_status"] == "reviewed" for r in rows),
                          partial=sum(r["inspection_status"] == "partial" for r in rows))
        (base / "candidates-01757-02000-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(f"Saved {len(rows)} rows through {rows[-1]['level']}")
