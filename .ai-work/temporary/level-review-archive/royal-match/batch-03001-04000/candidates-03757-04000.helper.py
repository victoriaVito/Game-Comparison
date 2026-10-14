import collections
import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-03757-04000.jsonl"
checkpoint = base / "candidates-03757-04000.checkpoint.json"
manifest = json.loads((base / "sheets/index.json").read_text())
sheet_name = sys.argv[1]
sheet = next(s for s in manifest["sheets"] if s["sheet"] == sheet_name)
notes = sys.stdin.read().strip().splitlines()
assert len(notes) == len(sheet["records"])
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert not set(r["level"] for r in existing) & set(r["level"] for r in sheet["records"])
for source, note in zip(sheet["records"], notes):
    observation, _, tags = note.partition("|")
    missing = source["status"] == "missing" or not source.get("image")
    partial = observation.startswith("OVERLAY: ")
    row = dict(
        schema_version=2, game="royal-match", level=source["level"],
        review_status="needs_review",
        inspection_status="missing" if missing else "partial" if partial else "reviewed",
        image_path=None if missing else source["image"],
        image_sha256=None if missing else source["sha256"],
        sheet_path=(base / "sheets" / sheet_name).as_posix().split("verbose-memory/")[-1],
        cell=source["cell"], geometry_tags=[] if missing else tags.split(",") if tags else [],
        observation="Missing source; sheet cell displays MISSING SOURCE." if missing else observation.removeprefix("OVERLAY: "),
        occlusion="unknown" if missing else "partial" if partial else "none",
        confidence="unknown" if missing else "low" if partial else "medium",
        verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
        difficulty_hypothesis=None, strategy_hypothesis=None,
        review_note="No source image available." if missing else
        "Visual sheet review only; blocker identities and fine cell details require original-resolution confirmation. No local difficulty or strategy support cited."
    )
    existing.append(row)
existing.sort(key=lambda row: row["level"])
output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in existing))
state = json.loads(checkpoint.read_text()) if checkpoint.exists() else {"inspected_sheets": []}
state["inspected_sheets"].append(sheet_name)
state["rows_saved"] = len(existing)
state["inspection_counts"] = dict(collections.Counter(row["inspection_status"] for row in existing))
checkpoint.write_text(json.dumps(state, indent=2) + "\n")
print(sheet_name, state["rows_saved"], state["inspection_counts"])
