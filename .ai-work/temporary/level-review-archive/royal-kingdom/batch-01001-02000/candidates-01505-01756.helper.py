import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
OUTPUT = BASE / "candidates-01505-01756.jsonl"
CONTRACT = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
INDEX = json.loads((BASE / "sheets/index.json").read_text())
LOOKUP = {r["level"]: (s["sheet"], r) for s in INDEX["sheets"] for r in s["records"]}


def save(start, entries):
    existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
    assert start == 1505 + len(existing), (start, len(existing))
    rows = []
    for level, entry in enumerate(entries, start):
        observation, tags, partial = entry
        sheet, record = LOOKUP[level]
        row = dict(schema_version=2, game="royal-kingdom", level=level,
                   review_status="needs_review", inspection_status="partial" if partial else "reviewed",
                   image_path=record["image"], image_sha256=record["sha256"],
                   sheet_path=str(BASE / "sheets" / sheet), cell=record["cell"],
                   geometry_tags=tags, observation=observation,
                   occlusion="partial" if partial else "none", confidence="low" if partial else "medium",
                   verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
                   difficulty_hypothesis=None, strategy_hypothesis=None,
                   review_note="Reward badge/effects obscure some cells; inspect original resolution before labeling concealed geometry." if partial else "Contact-sheet visual evidence only; blocker identities and hidden states are unverified.")
        assert set(row) == set(CONTRACT["record_fields"])
        assert set(tags) <= set(CONTRACT["geometry_tags"])
        assert pathlib.Path(record["image"]).exists()
        rows.append(row)
    with OUTPUT.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    checkpoint = dict(last_saved_level=rows[-1]["level"], saved_rows=len(existing) + len(rows),
                      inspected_sheets=sorted({r["sheet_path"] for r in existing + rows}),
                      status="complete" if rows[-1]["level"] == 1756 else "in_progress")
    (BASE / "candidates-01505-01756.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(f"Saved {start}-{rows[-1]['level']}; total {checkpoint['saved_rows']}")


if __name__ == "__main__":
    for group in json.load(sys.stdin):
        save(group["start"], group["entries"])
