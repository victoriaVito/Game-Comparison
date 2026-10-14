import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-01253-01504.jsonl"
manifest = json.loads((base / "sheets/index.json").read_text())
entries = {
    r["level"]: (s["sheet"], r)
    for s in manifest["sheets"]
    for r in s["records"]
}
start = int(sys.argv[1])
observations = json.loads(sys.stdin.read())
saved = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert len(observations) == 12
assert start == 1253 + len(saved)
for level, item in enumerate(observations, start):
    sheet, source = entries[level]
    observation, tags, *partial = item
    missing = not source.get("image") or not pathlib.Path(source["image"]).exists()
    row = dict(
        schema_version=2, game="royal-match", level=level,
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=None if missing else source["image"],
        image_sha256=None if missing else source["sha256"],
        sheet_path=str(base / "sheets" / sheet).split("/victoria-serrano-abk-verbose-memory/")[-1],
        cell=source["cell"], geometry_tags=[] if missing else tags,
        observation="Source image missing." if missing else observation,
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note=partial[0] if partial else "Contact-sheet visual evidence only; blocker identities and fine cell details remain unverified. Tags withheld where the visible boundary is ambiguous.",
    )
    saved.append(row)
with output.open("a") as handle:
    for row in saved[-12:]:
        handle.write(json.dumps(row) + "\n")
checkpoint = dict(last_inspected_sheet=sheet, last_level=start + 11,
                  inspected_sheets=len(saved) // 12, saved_rows=len(saved),
                  reviewed=sum(r["inspection_status"] == "reviewed" for r in saved),
                  partial=sum(r["inspection_status"] == "partial" for r in saved),
                  missing=sum(r["inspection_status"] == "missing" for r in saved))
(base / "candidates-01253-01504-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps(checkpoint))
