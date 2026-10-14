import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.relative_to(pathlib.Path.cwd())
OUTPUT = BASE / "candidates-04505-04756.jsonl"
CONTRACT = json.loads(pathlib.Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())
INDEX = json.loads((BASE / "sheets/index.json").read_text())
TAGS = {"c": "compact_full_field", "s": "split_regions", "b": "layered_bands",
        "e": "edge_channels", "m": "central_mass", "o": "open_center",
        "t": "stair_step", "a": "asymmetric"}


def save(start, observations):
    sheet = next(s for s in INDEX["sheets"] if s["records"][0]["level"] == start)
    existing = [json.loads(line) for line in OUTPUT.read_text().splitlines()] if OUTPUT.exists() else []
    assert len(observations) == len(sheet["records"]) == 12
    assert not any(start <= row["level"] <= start + 11 for row in existing)
    rows = []
    for record, (tags, observation, *partial) in zip(sheet["records"], observations):
        missing = not pathlib.Path(record["image"]).is_file()
        obstructed = bool(partial)
        row = dict(schema_version=2, game="royal-kingdom", level=record["level"],
                   review_status="needs_review",
                   inspection_status="missing" if missing else "partial" if obstructed else "reviewed",
                   image_path=None if missing else record["image"],
                   image_sha256=None if missing else record["sha256"],
                   sheet_path=str(BASE / "sheets" / sheet["sheet"]), cell=record["cell"],
                   geometry_tags=[] if missing else [TAGS[tag] for tag in tags],
                   observation="Source image missing." if missing else observation,
                   occlusion="unknown" if missing else "partial" if obstructed else "none",
                   confidence="unknown" if missing else "low" if obstructed else "medium",
                   verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
                   difficulty_hypothesis=None, strategy_hypothesis=None,
                   review_note=partial[0] if obstructed else
                   "Sheet-scale visual evidence only; blocker identities and fine cell boundaries need original-resolution confirmation. No local difficulty or strategy citation.")
        assert set(row) == set(CONTRACT["record_fields"])
        rows.append(row)
    with OUTPUT.open("a") as stream:
        for row in rows:
            stream.write(json.dumps(row) + "\n")
    all_rows = existing + rows
    checkpoint = dict(inspected_sheets=sorted({r["sheet_path"] for r in all_rows}),
                      inspected_levels=len(all_rows),
                      reviewed=sum(r["inspection_status"] == "reviewed" for r in all_rows),
                      partial=sum(r["inspection_status"] == "partial" for r in all_rows),
                      last_saved_level=max(r["level"] for r in all_rows))
    (BASE / "candidates-04505-04756.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(f"Saved {start}-{start + 11}; total {len(all_rows)}.")


if __name__ == "__main__":
    save(int(sys.argv[1]), json.load(sys.stdin))
