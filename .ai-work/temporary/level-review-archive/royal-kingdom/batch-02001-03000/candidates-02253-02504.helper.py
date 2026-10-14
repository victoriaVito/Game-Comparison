import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-02253-02504.jsonl"
manifest = json.loads((base / "sheets/index.json").read_text())
lookup = {r["level"]: (s["sheet"], r) for s in manifest["sheets"] for r in s["records"]}
saved = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
start = int(sys.argv[1])
lines = sys.stdin.read().strip().splitlines()
assert len(lines) == 12
assert start == (saved[-1]["level"] + 1 if saved else 2253)
for offset, line in enumerate(lines):
    level = start + offset
    tags, observation = line.split("|", 1)
    partial = tags.startswith("!")
    tags = tags.lstrip("!")
    sheet, source = lookup[level]
    row = dict(
        schema_version=2, game="royal-kingdom", level=level,
        review_status="needs_review", inspection_status="partial" if partial else "reviewed",
        image_path=source["image"], image_sha256=source["sha256"],
        sheet_path=(base / "sheets" / sheet).as_posix().split("abk-verbose-memory/")[-1],
        cell=source["cell"], geometry_tags=tags.split(",") if tags else [],
        observation=observation, occlusion="severe" if level == 2286 else "partial" if partial else "none",
        confidence="low" if partial else "medium", verified_difficulty="unknown",
        verified_strategy="unknown", verified_evidence=[], difficulty_hypothesis=None,
        strategy_hypothesis=None,
        review_note="Visible effects or interface obscure cells; full initial geometry requires an unobstructed local image." if partial else "Contact-sheet inspection; small blocker details remain uncertain. No local difficulty or strategy evidence cited."
    )
    saved.append(row)
with output.open("a") as handle:
    for row in saved[-12:]:
        handle.write(json.dumps(row) + "\n")
checkpoint = dict(last_inspected_level=start + 11, inspected_sheets=len(saved) // 12,
                  inspected_images=len(saved), reviewed=sum(r["inspection_status"] == "reviewed" for r in saved),
                  partial=sum(r["inspection_status"] == "partial" for r in saved))
(base / "candidates-02253-02504.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(checkpoint)
