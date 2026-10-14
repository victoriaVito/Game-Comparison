import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.relative_to(Path.cwd())
OUTPUT = BASE / "candidates-03757-04000.jsonl"
CONTRACT = json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
INDEX = json.loads((BASE / "sheets/index.json").read_text())


def save(start, entries):
    existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
    seen = {row["level"] for row in existing}
    for level, entry in enumerate(entries, start):
        if level in seen:
            continue
        matches = [(sheet, record) for sheet in INDEX["sheets"] for record in sheet["records"] if record["level"] == level]
        observation, tags, partial = entry
        sheet, record = matches[0] if matches else (None, None)
        available = record is not None and Path(record["image"]).exists()
        row = dict(
            schema_version=2, game="royal-kingdom", level=level,
            review_status="needs_review",
            inspection_status=("partial" if partial else "reviewed") if available else "missing",
            image_path=record["image"] if available else None,
            image_sha256=record["sha256"] if available else None,
            sheet_path=str(BASE / "sheets" / sheet["sheet"]) if available else None,
            cell=record["cell"] if available else None,
            geometry_tags=tags if available else [],
            observation=observation if available else "Source image or manifest entry is missing.",
            occlusion="partial" if partial else ("none" if available else "unknown"),
            confidence="low" if partial else ("medium" if available else "unknown"),
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note=("Foreground animation obscures cells at the positions described in observation; full-resolution follow-up needed." if partial else "Sheet-scale visual evidence only; covered cells are not empty gaps. No local difficulty or strategy citation."),
        )
        assert set(row) == set(CONTRACT["record_fields"])
        existing.append(row)
    for row in existing:
        if row["sheet_path"] and Path(row["sheet_path"]).is_absolute():
            row["sheet_path"] = str(Path(row["sheet_path"]).relative_to(Path.cwd()))
        if row["level"] == 3759:
            row["geometry_tags"] = []
        if row["inspection_status"] == "partial":
            row["review_note"] = "Foreground animation obscures cells at the positions described in observation; full-resolution follow-up needed."
        if not row["geometry_tags"] and "Geometry labels withheld" not in row["review_note"]:
            row["review_note"] += " Geometry labels withheld: the visible mix of occupied structures and openings does not establish a confident taxonomy match."
    existing.sort(key=lambda row: row["level"])
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in existing))
    checkpoint = dict(range=[3757, 4000], saved_rows=len(existing), last_level=max(row["level"] for row in existing),
                      inspected_sheets=sorted({row["sheet_path"] for row in existing if row["sheet_path"]}),
                      reviewed=sum(row["inspection_status"] == "reviewed" for row in existing),
                      partial=sum(row["inspection_status"] == "partial" for row in existing))
    (BASE / "candidates-03757-04000-checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(json.dumps({key: value for key, value in checkpoint.items() if key != "inspected_sheets"}))


if __name__ == "__main__":
    save(int(sys.argv[1]), json.load(sys.stdin))
