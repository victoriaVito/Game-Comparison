import json
import pathlib
import sys

base = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
output = base / "candidates-03253-03504.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
contract = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
manifest = {r["level"]: (s["sheet"], r) for s in index["sheets"] for r in s["records"]}
data = json.load(sys.stdin)
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
start = data["start"]
assert len(data["observations"]) == 12
assert start == (existing[-1]["level"] + 1 if existing else 3253)
with output.open("a") as stream:
    for offset, entry in enumerate(data["observations"]):
        level = start + offset
        sheet, source = manifest[level]
        observation, tags = entry[:2]
        partial = len(entry) > 2 and entry[2]
        present = source.get("image") and pathlib.Path(source["image"]).exists()
        row = dict(schema_version=2, game="royal-match", level=level,
                   review_status="needs_review", inspection_status=("partial" if partial else "reviewed") if present else "missing",
                   image_path=source["image"] if present else None,
                   image_sha256=source["sha256"] if present else None,
                   sheet_path=str(base / "sheets" / sheet) if present else None,
                   cell=source["cell"] if present else None,
                   geometry_tags=tags if present else [], observation=observation if present else "Source image is missing.",
                   occlusion="partial" if partial else "none", confidence="low" if partial else "medium",
                   verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
                   difficulty_hypothesis=None, strategy_hypothesis=None,
                   review_note="Sheet-scale visual review; blocker identities and concealed cells require original-resolution follow-up. No local difficulty or strategy evidence cited.")
        assert set(row) == set(contract["record_fields"])
        assert set(row["geometry_tags"]) <= set(contract["geometry_tags"])
        stream.write(json.dumps(row) + "\n")
        existing.append(row)
    stream.flush()
checkpoint = dict(last_inspected_level=start + 11, inspected_sheets=len(existing) // 12,
                  rows=len(existing), reviewed=sum(r["inspection_status"] == "reviewed" for r in existing),
                  partial=sum(r["inspection_status"] == "partial" for r in existing),
                  missing=sum(r["inspection_status"] == "missing" for r in existing))
(base / "candidates-03253-03504-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(checkpoint)
