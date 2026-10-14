import json
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-kingdom/batch-01001-02000")
OUT = BASE / "candidates-01253-01504.jsonl"
CONTRACT = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
INDEX = json.loads((BASE / "sheets/index.json").read_text())


def save(start, observations):
    assert len(observations) == 12
    sheet = next(s for s in INDEX["sheets"] if s["records"][0]["level"] == start)
    existing = [json.loads(line) for line in OUT.read_text().splitlines()] if OUT.exists() else []
    assert not any(start <= row["level"] < start + 12 for row in existing)
    for source, details in zip(sheet["records"], observations):
        text, tags, partial = details
        available = bool(source.get("image")) and Path(source["image"]).is_file()
        row = dict(
            schema_version=2, game="royal-kingdom", level=source["level"],
            review_status="needs_review",
            inspection_status=("partial" if partial else "reviewed") if available else "missing",
            image_path=source["image"] if available else None,
            image_sha256=source["sha256"] if available else None,
            sheet_path=str(BASE / "sheets" / sheet["sheet"]), cell=source["cell"],
            geometry_tags=tags if available else [], observation=text if available else "Source image is missing.",
            occlusion="partial" if partial and available else ("none" if available else "unknown"),
            confidence="low" if partial else ("medium" if available else "unknown"),
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note=("Animation or foreground overlay obscures cells; inspect original resolution before accepting geometry."
                         if partial else "Visual sheet evidence only; blocker identities and covered-cell contents are not verified.")
                         if available else "No source image is available."
        )
        assert set(row) == set(CONTRACT["record_fields"])
        existing.append(row)
    existing.sort(key=lambda row: row["level"])
    OUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in existing))
    checkpoint = {
        "range": [1253, 1504], "last_inspected_sheet": sheet["sheet"],
        "saved_rows": len(existing),
        "inspected_sheets": sorted({row["sheet_path"] for row in existing if row["inspection_status"] in ("reviewed", "partial")}),
        "reviewed": sum(row["inspection_status"] == "reviewed" for row in existing),
        "partial": sum(row["inspection_status"] == "partial" for row in existing),
        "missing": sum(row["inspection_status"] == "missing" for row in existing),
        "status": "complete" if len(existing) == 252 else "in_progress",
    }
    (BASE / "candidates-01253-01504-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(sheet["sheet"], len(existing), "saved")
