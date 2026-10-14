import json
from pathlib import Path
import sys

BASE = Path(".ai-work/temporary/level-review-archive/royal-match/batch-05001-06000")
OUT = BASE / "candidates-05253-05504.jsonl"
CHECKPOINT = BASE / "candidates-05253-05504-checkpoint.json"
INDEX = json.loads((BASE / "sheets/index.json").read_text())
FIELDS = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["record_fields"]
records = {r["level"]: (s["sheet"], r) for s in INDEX["sheets"] for r in s["records"]}
existing = [json.loads(line) for line in OUT.read_text().splitlines()] if OUT.exists() else []
seen = {r["level"] for r in existing}
for group in json.load(sys.stdin):
    start, observations = group
    assert len(observations) == 12
    rows = []
    for offset, item in enumerate(observations):
        level = start + offset
        assert 5253 <= level <= 5504 and level not in seen
        sheet, source = records.get(level, (None, {}))
        image = source.get("image")
        missing = not image or not Path(image).is_file()
        observation, tags, *extra = item
        partial = bool(extra and extra[0])
        row = dict(
            schema_version=2, game="royal-match", level=level, review_status="needs_review",
            inspection_status="missing" if missing else ("partial" if partial else "reviewed"),
            image_path=None if missing else image, image_sha256=None if missing else source["sha256"],
            sheet_path=None if missing else str(BASE / "sheets" / sheet),
            cell=None if missing else source["cell"], geometry_tags=[] if missing else tags,
            observation="No source image is available in the manifest for this level." if missing else observation,
            occlusion="unknown" if missing else ("partial" if partial else "none"),
            confidence="unknown" if missing else ("low" if partial else "medium"),
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note="Missing source; no visual claim." if missing else (
                "Animation or overlay obscures cells; original-resolution follow-up needed." if partial else
                "Contact-sheet visual evidence only; blocker identities and covered-cell connectivity are not verified."
            ),
        )
        assert set(row) == set(FIELDS)
        rows.append(row)
        seen.add(level)
    assert not existing or rows[0]["level"] == existing[-1]["level"] + 1
    with OUT.open("a") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    existing.extend(rows)
    state = {
        "shard": str(OUT), "last_saved_level": existing[-1]["level"],
        "saved_rows": len(existing),
        "inspected_sheets": [f"levels-{n}-{n+11}.jpg" for n in range(5253, start + 1, 12)],
        "reviewed": sum(r["inspection_status"] == "reviewed" for r in existing),
        "partial": sum(r["inspection_status"] == "partial" for r in existing),
        "missing": sum(r["inspection_status"] == "missing" for r in existing),
    }
    CHECKPOINT.write_text(json.dumps(state, indent=2) + "\n")
    print(json.dumps(state))
