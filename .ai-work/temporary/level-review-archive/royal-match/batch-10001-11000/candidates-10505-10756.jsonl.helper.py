import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DIRECTORY = Path(__file__).resolve().parent
OUTPUT = DIRECTORY / "candidates-10505-10756.jsonl"
CHECKPOINT = DIRECTORY / "candidates-10505-10756.jsonl.checkpoint.json"
INDEX = json.loads((DIRECTORY / "sheets/index.json").read_text())
TAGS = {
    "full": "compact_full_field",
    "split": "split_regions",
    "bands": "layered_bands",
    "edge": "edge_channels",
    "mass": "central_mass",
    "open": "open_center",
    "step": "stair_step",
    "asym": "asymmetric",
}


def save_sheet(start, entries):
    sheet = next(s for s in INDEX["sheets"] if s["records"][0]["level"] == start)
    assert len(entries) == len(sheet["records"])
    existing = {}
    if OUTPUT.exists():
        existing = {r["level"]: r for r in map(json.loads, OUTPUT.read_text().splitlines())}
    for source, entry in zip(sheet["records"], entries):
        level = source["level"]
        assert 10505 <= level <= 10756
        if level in existing:
            continue
        missing = source.get("image") is None
        if not missing:
            assert hashlib.sha256((ROOT / source["image"]).read_bytes()).hexdigest() == source["sha256"]
        tags, observation = entry[:2]
        partial = len(entry) > 2 and entry[2] == "partial"
        note = entry[3] if len(entry) > 3 else "Visual sheet evidence only; blocker identities and fine cell boundaries are not independently verified. Tags remain candidate vocabulary for Royal Match; difficulty and strategy have no directly cited local evidence."
        existing[level] = {
            "schema_version": 2, "game": "royal-match", "level": level,
            "review_status": "needs_review",
            "inspection_status": "missing" if missing else "partial" if partial else "reviewed",
            "image_path": None if missing else source["image"],
            "image_sha256": None if missing else source["sha256"],
            "sheet_path": (DIRECTORY / "sheets" / sheet["sheet"]).relative_to(ROOT).as_posix(),
            "cell": source["cell"], "geometry_tags": [] if missing else [TAGS[t] for t in tags.split()],
            "observation": observation, "occlusion": "unknown" if missing else "partial" if partial else "none",
            "confidence": "unknown" if missing else entry[4] if len(entry) > 4 else "medium",
            "verified_difficulty": "unknown", "verified_strategy": "unknown",
            "verified_evidence": [], "difficulty_hypothesis": None, "strategy_hypothesis": None,
            "review_note": note,
        }
    OUTPUT.write_text("".join(json.dumps(existing[n], ensure_ascii=False) + "\n" for n in sorted(existing)))
    checkpoint = json.loads(CHECKPOINT.read_text()) if CHECKPOINT.exists() else {"schema_version": 2, "completed_sheets": []}
    if sheet["sheet"] not in checkpoint["completed_sheets"]:
        checkpoint["completed_sheets"].append(sheet["sheet"])
    checkpoint.update(saved_range=[min(existing), max(existing)], saved_rows=len(existing),
                      status="complete" if len(existing) == 252 else "partial",
                      counts={status: sum(r["inspection_status"] == status for r in existing.values())
                              for status in ["reviewed", "partial", "missing", "not_reviewed"]})
    CHECKPOINT.write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(f"Checkpoint {sheet['sheet']}: {len(existing)} saved rows")
