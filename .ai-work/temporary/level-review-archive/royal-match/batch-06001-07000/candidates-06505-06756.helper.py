import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUTPUT = ROOT / "candidates-06505-06756.jsonl"
CHECKPOINT = ROOT / "candidates-06505-06756.checkpoint.json"
INDEX = json.loads((ROOT / "sheets/index.json").read_text())
CONTRACT = json.loads((ROOT.parents[2] / "level-review-pilot/review_contract.json").read_text())


def save_sheet(start, observations):
    sheet = next(s for s in INDEX["sheets"] if s["sheet"] == f"levels-{start}-{start + 11}.jpg")
    existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
    assert not any(start <= row["level"] <= start + 11 for row in existing)
    assert len(observations) == len(sheet["records"]) == 12
    for source, detail in zip(sheet["records"], observations):
        missing = not source.get("image")
        text, *options = detail.split("|")
        partial = "partial" in options
        tags = [option for option in options if option != "partial" and option]
        row = dict(
            schema_version=2, game="royal-match", level=source["level"],
            review_status="needs_review",
            inspection_status="missing" if missing else "partial" if partial else "reviewed",
            image_path=None if missing else source["image"],
            image_sha256=None if missing else source["sha256"],
            sheet_path=str(ROOT.relative_to(pathlib.Path.cwd()) / "sheets" / sheet["sheet"]),
            cell=source["cell"], geometry_tags=[] if missing else tags,
            observation="No source image is available in the manifest; the sheet shows a missing placeholder." if missing else text,
            occlusion="unknown" if missing else "partial" if partial else "none",
            confidence="unknown" if missing else "low" if partial else "medium",
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note="Missing source; no visual layout can be assessed." if missing else
            "Animation or overlay obscures some cells; original-resolution follow-up is needed." if partial else
            "Contact-sheet visual evidence only; blocker identities and hidden cell continuity are not verified.",
        )
        assert set(row) == set(CONTRACT["record_fields"])
        existing.append(row)
    existing.sort(key=lambda row: row["level"])
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in existing))
    inspected = sorted({row["sheet_path"] for row in existing})
    CHECKPOINT.write_text(json.dumps(dict(
        range=[6505, 6756], inspected_sheets=inspected, inspected_sheet_count=len(inspected),
        saved_rows=len(existing),
        reviewed=sum(row["inspection_status"] == "reviewed" for row in existing),
        partial=sum(row["inspection_status"] == "partial" for row in existing),
        missing=sum(row["inspection_status"] == "missing" for row in existing),
        last_saved_level=existing[-1]["level"],
    ), indent=2) + "\n")
    print(f"Saved sheet {start}-{start + 11}: {len(existing)} rows total.")


if __name__ == "__main__":
    save_sheet(int(sys.argv[1]), sys.stdin.read().strip().splitlines())
