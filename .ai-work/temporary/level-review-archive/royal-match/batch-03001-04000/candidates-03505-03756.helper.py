import json
import pathlib
import sys

base = pathlib.Path(__file__).parent
output = base / "candidates-03505-03756.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
records = {
    record["level"]: (sheet["sheet"], record)
    for sheet in index["sheets"]
    for record in sheet["records"]
}
start = int(sys.argv[1])
if len(sys.argv) > 2:
    observations = json.loads(sys.argv[2])
else:
    observations = []
    for line in sys.stdin.read().strip().splitlines():
        observation, tags = line.split("|")
        partial = tags.endswith("!")
        tags = tags.rstrip("!")
        observations.append([observation, tags.split(",") if tags else []] + ([True] if partial else []))
previous = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
assert start == (previous[-1]["level"] + 1 if previous else 3505)
assert len(observations) == 12
with output.open("a") as stream:
    for offset, entry in enumerate(observations):
        level = start + offset
        sheet, record = records[level]
        observation, tags, *partial = entry
        missing = not record.get("image") or not pathlib.Path(record["image"]).exists()
        row = dict(
            schema_version=2, game="royal-match", level=level,
            review_status="needs_review",
            inspection_status="missing" if missing else "partial" if partial else "reviewed",
            image_path=None if missing else record["image"],
            image_sha256=None if missing else record["sha256"],
            sheet_path=str((base / "sheets" / sheet).resolve().relative_to(pathlib.Path.cwd())), cell=record["cell"],
            geometry_tags=[] if missing else tags,
            observation="Source image missing." if missing else observation,
            occlusion="unknown" if missing else "severe" if partial else "none",
            confidence="unknown" if missing else "low" if partial else "medium",
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note="Overlay hides underlying cells; boundary interpretation withheld." if partial else
            "Visual sheet evidence only; blocker identities and fine cell boundaries may need original-resolution review."
        )
        stream.write(json.dumps(row) + "\n")
    stream.flush()
rows = [json.loads(line) for line in output.read_text().splitlines()]
checkpoint = {
    "last_inspected_level": rows[-1]["level"],
    "saved_rows": len(rows),
    "inspected_sheets": sorted(set(row["sheet_path"] for row in rows)),
    "counts": {status: sum(row["inspection_status"] == status for row in rows)
               for status in ["reviewed", "partial", "missing"]},
}
(base / "candidates-03505-03756.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps(checkpoint["counts"]), "saved", len(rows), "through", rows[-1]["level"])
