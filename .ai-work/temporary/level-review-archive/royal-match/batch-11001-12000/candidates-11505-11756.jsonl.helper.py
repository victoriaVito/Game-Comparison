import hashlib
import json
import pathlib
import sys

BASE = pathlib.Path(".ai-work/temporary/level-review-archive/royal-match/batch-11001-12000")
OUTPUT = BASE / "candidates-11505-11756.jsonl"
CHECKPOINT = BASE / "candidates-11505-11756.jsonl.checkpoint.json"
INDEX = json.loads((BASE / "sheets/index.json").read_text())
TAGS = dict(c="compact_full_field", s="split_regions", l="layered_bands",
            e="edge_channels", m="central_mass", o="open_center",
            t="stair_step", a="asymmetric")

def save(start, entries):
    sheet = next(s for s in INDEX["sheets"] if s["records"][0]["level"] == start)
    records = sheet["records"]
    assert len(entries) == len(records)
    existing = {}
    if OUTPUT.exists():
        existing = {r["level"]: r for r in map(json.loads, OUTPUT.read_text().splitlines())}
    for source, entry in zip(records, entries):
        level = source["level"]
        assert 11505 <= level <= 11756
        if level in existing:
            continue
        codes, observation = entry.split("|", 1)
        missing = source.get("image") is None
        if not missing:
            assert hashlib.sha256(pathlib.Path(source["image"]).read_bytes()).hexdigest() == source["sha256"]
        partial = codes.startswith("?")
        codes = codes.lstrip("?")
        existing[level] = {
            "schema_version": 2, "game": "royal-match", "level": level,
            "review_status": "needs_review",
            "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
            "image_path": None if missing else source["image"],
            "image_sha256": None if missing else source["sha256"],
            "sheet_path": str(BASE / "sheets" / sheet["sheet"]),
            "cell": source["cell"],
            "geometry_tags": [] if missing else [TAGS[x] for x in codes],
            "observation": observation,
            "occlusion": "unknown" if missing else "partial" if partial else "none",
            "confidence": "unknown" if missing else "low" if partial else "medium",
            "verified_difficulty": "unknown", "verified_strategy": "unknown",
            "verified_evidence": [], "difficulty_hypothesis": None,
            "strategy_hypothesis": None,
            "review_note": "Source absent in local index." if missing else
                "Sheet visually inspected; blocker identities and connectivity through covered cells remain uncertain. Tags are candidate vocabulary, not accepted labels; no difficulty or strategy evidence."
        }
    OUTPUT.write_text("".join(json.dumps(existing[k], ensure_ascii=False) + "\n" for k in sorted(existing)))
    checkpoints = json.loads(CHECKPOINT.read_text()) if CHECKPOINT.exists() else {"completed_sheets": []}
    if sheet["sheet"] not in checkpoints["completed_sheets"]:
        checkpoints["completed_sheets"].append(sheet["sheet"])
    checkpoints.update(saved_levels=sorted(existing), saved_count=len(existing),
                       status="complete" if len(existing) == 252 else "partial",
                       inspected_sheet_count=len(checkpoints["completed_sheets"]))
    CHECKPOINT.write_text(json.dumps(checkpoints, indent=2) + "\n")
    print(start, len(existing), "saved")

if __name__ == "__main__":
    save(int(sys.argv[1]), sys.stdin.read().strip().splitlines())
