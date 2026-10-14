import json
import pathlib
import sys

base = pathlib.Path(".ai-work/temporary/level-review-archive/royal-kingdom/batch-04001-05000")
output = base / "candidates-04757-05000.jsonl"
checkpoint = base / "candidates-04757-05000-checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
lookup = {r["level"]: (s["sheet"], r) for s in manifest["sheets"] for r in s["records"]}
rows = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
data = json.load(sys.stdin)
for start, entries in data:
    for offset, entry in enumerate(entries):
        level = start + offset
        assert 4757 <= level <= 5000
        assert not any(row["level"] == level for row in rows)
        sheet, source = lookup[level]
        observation, tags, partial = entry
        rows.append(dict(
            schema_version=2, game="royal-kingdom", level=level,
            review_status="needs_review", inspection_status="partial" if partial else "reviewed",
            image_path=source["image"], image_sha256=source["sha256"],
            sheet_path=str(base / "sheets" / sheet), cell=source["cell"],
            geometry_tags=tags, observation=observation,
            occlusion="partial" if partial else "none", confidence="low" if partial else "medium",
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note=("Animated effects or a foreground vessel obscure cells; inspect the original image before assigning finer geometry."
                         if partial else "Contact-sheet visual evidence only; blocker identities and finer cell boundaries require original-resolution confirmation.")
        ))
    rows.sort(key=lambda row: row["level"])
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    checkpoint.write_text(json.dumps(dict(
        range=[4757, 5000], saved_rows=len(rows),
        inspected_sheets=sorted(set(row["sheet_path"] for row in rows)),
        last_saved_level=rows[-1]["level"], status="complete" if len(rows) == 244 else "in_progress"
    ), indent=2) + "\n")
print(f"Saved {len(rows)} rows; last level {rows[-1]['level']}")
