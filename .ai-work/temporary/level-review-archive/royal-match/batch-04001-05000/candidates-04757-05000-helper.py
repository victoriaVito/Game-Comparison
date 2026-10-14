import json
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-match/batch-04001-05000")
OUTPUT = BASE / "candidates-04757-05000.jsonl"
INDEX = json.loads((BASE / "sheets/index.json").read_text())


def save(start, observations, partial=()):
    sheet = next(s for s in INDEX["sheets"] if s["sheet"].startswith(f"levels-{start}-"))
    records = sheet["records"]
    assert len(records) == len(observations)
    existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
    assert not existing or existing[-1]["level"] == start - 1
    rows = []
    for source, detail in zip(records, observations):
        level = source["level"]
        missing = not source.get("image")
        observation, tags = detail
        covered = level in partial
        rows.append(dict(
            schema_version=2, game="royal-match", level=level,
            review_status="needs_review",
            inspection_status="missing" if missing else "partial" if covered else "reviewed",
            image_path=None if missing else source["image"],
            image_sha256=None if missing else source["sha256"],
            sheet_path=str(BASE / "sheets" / sheet["sheet"]), cell=source.get("cell"),
            geometry_tags=[] if missing else tags,
            observation="No source image available; the sheet cell is a missing placeholder." if missing else observation,
            occlusion="unknown" if missing else "partial" if covered else "none",
            confidence="unknown" if missing else "low" if covered else "medium",
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note="Missing source evidence." if missing else
                "Animation or light effects obscure some cells; inspect the original before labeling." if covered else
                "Contact-sheet evidence only; blocker identities and hidden cells are not verified."
        ))
    with OUTPUT.open("a") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")
    progress = existing + rows
    checkpoint = dict(last_level=progress[-1]["level"], saved_rows=len(progress),
                      inspected_images=sum(r["inspection_status"] in ("reviewed", "partial") for r in progress),
                      partial_images=sum(r["inspection_status"] == "partial" for r in progress),
                      missing_images=sum(r["inspection_status"] == "missing" for r in progress),
                      inspected_sheets=list(dict.fromkeys(r["sheet_path"] for r in progress)))
    (BASE / "candidates-04757-05000-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
