import json
import pathlib
import sys

BASE = pathlib.Path(__file__).parent
OUTPUT = BASE / "candidates-07001-07252.jsonl"
CHECKPOINT = BASE / "candidates-07001-07252-checkpoint.json"
manifest = json.loads((BASE / "sheets/index.json").read_text())
existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
sheet_name = sys.argv[1]
sheet = next(item for item in manifest["sheets"] if item["sheet"] == sheet_name)
notes = json.load(sys.stdin)
assert len(notes) == len(sheet["records"])
assert not any(row["level"] in {r["level"] for r in sheet["records"]} for row in existing)
for source, note in zip(sheet["records"], notes):
    missing = "image" not in source
    observation, tags, partial = note if note is not None else ("Source missing; sheet cell contains a MISSING SOURCE placeholder.", [], False)
    assert missing == (note is None)
    row = dict(
        schema_version=2, game="royal-match", level=source["level"],
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=source.get("image"), image_sha256=source.get("sha256"),
        sheet_path=(BASE / "sheets" / sheet_name).resolve().relative_to(pathlib.Path.cwd()).as_posix(), cell=source["cell"],
        geometry_tags=tags, observation=observation,
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="No source image available." if missing else
        "Occlusion described in observation prevents full cell interpretation; underlying geometry needs original-resolution follow-up." if partial else
        "Contact-sheet visual evidence only; blocker identities and fine cell details remain unverified. No locally cited difficulty or strategy evidence."
    )
    if not missing and not tags:
        row["review_note"] += " Geometry tags withheld because the visible outline or connectivity does not clearly support a taxonomy label."
    existing.append(row)
existing.sort(key=lambda row: row["level"])
OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in existing))
prior = json.loads(CHECKPOINT.read_text()) if CHECKPOINT.exists() else {"inspected_sheets": []}
prior["inspected_sheets"].append(sheet_name)
prior["row_count"] = len(existing)
prior["counts"] = {status: sum(row["inspection_status"] == status for row in existing) for status in ["reviewed", "partial", "missing"]}
prior["last_saved_level"] = max(row["level"] for row in existing)
CHECKPOINT.write_text(json.dumps(prior, indent=2) + "\n")
print(json.dumps(prior))
