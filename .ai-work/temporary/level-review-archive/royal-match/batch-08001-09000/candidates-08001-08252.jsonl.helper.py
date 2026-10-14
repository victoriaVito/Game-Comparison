import hashlib
import json
import sys
from pathlib import Path

base = Path(".ai-work/temporary/level-review-archive/royal-match/batch-08001-09000")
output = base / "candidates-08001-08252.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
existing = {}
if output.exists():
    existing = {row["level"]: row for row in map(json.loads, output.read_text().splitlines())}
payload = json.load(sys.stdin)
for sheet_name, notes in payload.items():
    sheet = next(s for s in index["sheets"] if s["sheet"] == sheet_name)
    assert len(notes) == len(sheet["records"])
    for source, note in zip(sheet["records"], notes):
        level = source["level"]
        assert 8001 <= level <= 8252
        if level in existing:
            continue
        missing = source["status"].startswith("missing")
        tags, observation = note[:2]
        partial = len(note) > 2 and note[2]
        if not missing:
            assert hashlib.sha256(Path(source["image"]).read_bytes()).hexdigest() == source["sha256"]
            assert observation and note
        row = dict(
            schema_version=2, game="royal-match", level=level,
            review_status="needs_review",
            inspection_status="missing" if missing else "partial" if partial else "reviewed",
            image_path=None if missing else source["image"],
            image_sha256=None if missing else source["sha256"],
            sheet_path=str(base / "sheets" / sheet_name),
            cell=source["cell"], geometry_tags=[] if missing else tags,
            observation="Source image is missing; the numbered sheet cell contains no board evidence." if missing else observation,
            occlusion="unknown" if missing else "partial" if partial else "none",
            confidence="unknown" if missing else "low" if partial else "medium",
            verified_difficulty="unknown", verified_strategy="unknown",
            verified_evidence=[], difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note="Source unavailable." if missing else (
                "Opaque coverings conceal cells; hidden geometry and mechanics are withheld. "
                if partial else "Visible geometry only; blocker identities and unseen mechanics are not verified. "
            ) + "Royal Kingdom tags are candidate vocabulary, not accepted Royal Match classification."
        )
        existing[level] = row
    output.write_text("".join(json.dumps(existing[n], ensure_ascii=False) + "\n" for n in sorted(existing)))
    checkpoint = dict(
        saved_levels=sorted(existing), last_inspected_sheet=str(base / "sheets" / sheet_name),
        counts={status: sum(r["inspection_status"] == status for r in existing.values())
                for status in ("reviewed", "partial", "missing")},
        status="needs_review", assigned_range=[8001, 8252]
    )
    Path(str(output) + ".checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(sheet_name, "checkpoint saved:", len(existing), "rows")
