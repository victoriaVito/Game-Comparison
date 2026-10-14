import collections
import hashlib
import json
import pathlib
import sys

base = pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-12001-13000")
output = base / "candidates-12253-12504.jsonl"
index = json.loads((base / "sheets/index.json").read_text())
start = int(sys.argv[1])
sheet = next(s for s in index["sheets"] if s["sheet"] == f"levels-{start}-{start + 11}.jpg")
lines = sys.stdin.read().strip().splitlines()
assert len(lines) == len(sheet["records"]) == 12
existing = [json.loads(line) for line in output.read_text().splitlines()] if output.exists() else []
by_level = {row["level"]: row for row in existing}
codes = dict(c="compact_full_field", s="split_regions", l="layered_bands",
             e="edge_channels", m="central_mass", o="open_center",
             t="stair_step", a="asymmetric")
for source, line in zip(sheet["records"], lines):
    level = source["level"]
    assert 12253 <= level <= 12504
    if level in by_level:
        continue
    parts = line.split("|")
    tags, observation = parts[:2]
    missing = source["status"].startswith("missing")
    image = source.get("image")
    digest = source.get("sha256")
    if not missing:
        assert image and pathlib.Path(image).is_file()
        assert hashlib.sha256(pathlib.Path(image).read_bytes()).hexdigest() == digest
    partial = len(parts) > 2
    row = dict(schema_version=2, game="royal-match", level=level,
               review_status="needs_review",
               inspection_status="missing" if missing else "partial" if partial else "reviewed",
               image_path=None if missing else image,
               image_sha256=None if missing else digest,
               sheet_path=str(base / "sheets" / sheet["sheet"]), cell=source["cell"],
               geometry_tags=[] if missing else [codes[tag] for tag in tags],
               observation=observation, occlusion="unknown" if missing else "partial" if partial else "none",
               confidence="unknown" if missing else "low" if partial else "medium",
               verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
               difficulty_hypothesis=None, strategy_hypothesis=None,
               review_note=parts[2] if partial else
               "Source unavailable; no board interpretation." if missing else
               "Visual candidate only; blocker identities and mechanics are unverified. Unsupported geometry tags withheld.")
    by_level[level] = row
rows = [by_level[level] for level in sorted(by_level)]
output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
checkpoint = dict(last_saved_sheet=sheet["sheet"], saved_levels=sorted(by_level),
                  counts=dict(collections.Counter(row["inspection_status"] for row in rows)),
                  status="complete" if len(rows) == 252 else "in_progress")
(base / "candidates-12253-12504.jsonl.checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n")
print(json.dumps(dict(sheet=sheet["sheet"], saved=len(rows), counts=checkpoint["counts"])))
