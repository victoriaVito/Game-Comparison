import json
from pathlib import Path

BASE = Path(__file__).parent
OUTPUT = BASE / "candidates-01505-01756.jsonl"
CONTRACT = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
INDEX = json.loads((BASE / "sheets/index.json").read_text())
MANIFEST = {r["level"]: (s["sheet"], r) for s in INDEX["sheets"] for r in s["records"]}


def save(start, observations):
    rows = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
    assert len(observations) == 12
    assert not rows or rows[-1]["level"] == start - 1
    for level, item in enumerate(observations, start):
        text, tags, *extra = item
        sheet, source = MANIFEST[level]
        missing = not Path(source["image"]).is_file()
        partial = bool(extra and extra[0])
        row = dict(schema_version=2, game="royal-match", level=level,
                   review_status="needs_review", inspection_status="missing" if missing else "partial" if partial else "reviewed",
                   image_path=None if missing else source["image"], image_sha256=None if missing else source["sha256"],
                   sheet_path=str(BASE / "sheets" / sheet), cell=source["cell"],
                   geometry_tags=[] if missing else tags, observation="Source image missing." if missing else text,
                   occlusion="unknown" if missing else "partial" if partial else "none",
                   confidence="unknown" if missing else "low" if partial else "medium",
                   verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
                   difficulty_hypothesis=None, strategy_hypothesis=None,
                   review_note="Contact-sheet visual evidence only; blocker identities and covered-cell contents are unresolved. No local difficulty or strategy evidence.")
        assert set(row) == set(CONTRACT["record_fields"])
        rows.append(row)
    OUTPUT.write_text("".join(json.dumps(row) + "\n" for row in rows))
    checkpoint = dict(last_saved_level=rows[-1]["level"], saved_rows=len(rows),
                      inspected_sheets=[f"levels-{n}-{n+11}.jpg" for n in range(1505, start+1, 12)])
    (BASE / "candidates-01505-01756-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
