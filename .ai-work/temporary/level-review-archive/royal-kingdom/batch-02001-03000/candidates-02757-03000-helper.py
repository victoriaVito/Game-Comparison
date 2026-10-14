import json
import sys
from pathlib import Path

base = Path(__file__).resolve().parent.relative_to(Path.cwd())
output = base / "candidates-02757-03000.jsonl"
checkpoint = base / "candidates-02757-03000-checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
contract = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
for batch in json.load(sys.stdin):
    start, observations = batch
    sheet = next(s for s in manifest["sheets"] if s["records"][0]["level"] == start)
    assert len(observations) == len(sheet["records"])
    rows = []
    for source, detail in zip(sheet["records"], observations):
        level = source["level"]
        assert 2757 <= level <= 3000
        assert not any(r["level"] == level for r in existing)
        observation, tags, partial = detail
        missing = not source.get("image") or not Path(source["image"]).exists()
        row = dict(
            schema_version=2, game="royal-kingdom", level=level,
            review_status="needs_review",
            inspection_status="missing" if missing else "partial" if partial else "reviewed",
            image_path=None if missing else source["image"],
            image_sha256=None if missing else source["sha256"],
            sheet_path=str(base / "sheets" / sheet["sheet"]), cell=source["cell"],
            geometry_tags=[] if missing else tags,
            observation="Source image unavailable." if missing else observation,
            occlusion="unknown" if missing else "partial" if partial else "none",
            confidence="unknown" if missing else "low" if partial else "medium",
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note="Animation obscures some cells; original-resolution follow-up required." if partial else "Sheet-scale visual evidence only; blocker identities and mechanics are unverified."
        )
        assert set(row) == set(contract["record_fields"])
        assert set(tags) <= set(contract["geometry_tags"])
        rows.append(row)
    existing.extend(rows)
    assert [r["level"] for r in existing] == list(range(2757, existing[-1]["level"] + 1))
    with output.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    checkpoint.write_text(json.dumps({
        "last_saved_level": existing[-1]["level"],
        "inspected_sheets": list(dict.fromkeys(r["sheet_path"] for r in existing)),
        "saved_rows": len(existing),
        "reviewed": sum(r["inspection_status"] == "reviewed" for r in existing),
        "partial": sum(r["inspection_status"] == "partial" for r in existing),
        "missing": sum(r["inspection_status"] == "missing" for r in existing)
    }, indent=2) + "\n")
    print(f"Checkpoint saved: {sheet['sheet']}; {len(existing)} rows")
