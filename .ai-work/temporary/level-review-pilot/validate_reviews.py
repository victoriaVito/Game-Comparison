"""Validate candidate pilot shards without promoting observations to accepted labels."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


PILOT = Path(__file__).resolve().parent
ROOT = PILOT.parents[2]
CONTRACT = json.loads((PILOT / "review_contract.json").read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_records(path):
    rows = []
    for line, text in enumerate(path.read_text().splitlines(), 1):
        require(bool(text.strip()), f"{path}:{line}: empty row")
        row = json.loads(text)
        require(isinstance(row, dict), f"{path}:{line}: row must be an object")
        rows.append(row)
    return rows


def validate_records(game, rows, index_path, verify_hashes):
    require(index_path.resolve().is_relative_to(ROOT.resolve()), "Index outside worktree")
    index = json.loads(index_path.read_text())
    require(index["game"] == game, "Index game mismatch")
    start, stop = index["range"]
    require(
        [row.get("level") for row in rows] == list(range(start, stop + 1)),
        f"{game}: expected exact ordered sequence {start}..{stop}",
    )
    sources = {}
    for sheet in index["sheets"]:
        for record in sheet["records"]:
            sources[record["level"]] = (
                record,
                str((index_path.parent / sheet["sheet"]).relative_to(ROOT)),
            )
    for row in rows:
        prefix = f"{game} level {row['level']}"
        require(set(CONTRACT["record_fields"]) <= row.keys(), f"{prefix}: missing fields")
        require(type(row["schema_version"]) is int and row["schema_version"] == 2 and row["game"] == game, f"{prefix}: identity")
        require(type(row["level"]) is int, f"{prefix}: numeric level must be integer")
        require(row["review_status"] in ("candidate", "needs_review"), f"{prefix}: status")
        state = row["inspection_status"]
        require(state in ("reviewed", "partial", "not_reviewed", "missing"), f"{prefix}: inspection")
        require(row["occlusion"] in ("none", "partial", "severe", "unknown"), f"{prefix}: occlusion")
        require(row["confidence"] in ("high", "medium", "low", "unknown"), f"{prefix}: confidence")
        require(isinstance(row["observation"], str), f"{prefix}: observation")
        require(isinstance(row["review_note"], str), f"{prefix}: review note")
        tags = row["geometry_tags"]
        require(isinstance(tags, list), f"{prefix}: tags must be a list")
        require(all(isinstance(tag, str) for tag in tags), f"{prefix}: non-string tag")
        require(len(set(tags)) == len(tags), f"{prefix}: duplicate tags")
        require(set(tags) <= set(CONTRACT["geometry_tags"]), f"{prefix}: unsupported tags")
        source, sheet_path = sources[row["level"]]
        missing = source["status"] == "missing"
        # The prepared index may use an explicit missing-source status.
        missing = missing or source.get("image") is None
        if missing:
            require(state == "missing", f"{prefix}: missing image mislabeled")
            require(row["image_path"] is None and row["image_sha256"] is None, f"{prefix}: missing source")
        else:
            require(state != "missing", f"{prefix}: existing image mislabeled")
            require(row["image_path"] == source["image"], f"{prefix}: image path drift")
            require(row["image_sha256"] == source["sha256"], f"{prefix}: image hash drift")
            image = ROOT / row["image_path"]
            require(image.resolve().is_relative_to(ROOT.resolve()), f"{prefix}: path escape")
            require(image.is_file(), f"{prefix}: original image absent")
            if verify_hashes:
                require(hashlib.sha256(image.read_bytes()).hexdigest() == source["sha256"], f"{prefix}: source changed")
        if state in ("reviewed", "partial"):
            require(row["sheet_path"] == sheet_path, f"{prefix}: inspected sheet mismatch")
            require(row["cell"] == source["cell"], f"{prefix}: cell mismatch")
            require(bool(row["observation"].strip()), f"{prefix}: inspected without evidence")
            require(row["confidence"] != "unknown", f"{prefix}: inspected without confidence")
        else:
            require(not tags, f"{prefix}: uninspected image has visual labels")
            require(row["difficulty_hypothesis"] is None and row["strategy_hypothesis"] is None, f"{prefix}: uninspected hypothesis")
        if state == "partial":
            require(row["review_status"] == "needs_review", f"{prefix}: partial must need review")
        require(isinstance(row["verified_evidence"], list), f"{prefix}: verified evidence")
        for field in ("verified_difficulty", "verified_strategy"):
            require(isinstance(row[field], str), f"{prefix}: {field}")
            if row[field] != "unknown":
                require(bool(row["verified_evidence"]), f"{prefix}: unsupported {field}")
                for evidence in row["verified_evidence"]:
                    require(isinstance(evidence, dict) and evidence.get("source_path"), f"{prefix}: source reference")
                    source_path = ROOT / evidence["source_path"]
                    require(source_path.resolve().is_relative_to(ROOT.resolve()) and source_path.is_file(), f"{prefix}: evidence source")
                    require(bool(evidence.get("location")), f"{prefix}: evidence location")
        for field in ("difficulty_hypothesis", "strategy_hypothesis"):
            hypothesis = row[field]
            if hypothesis is not None:
                require(isinstance(hypothesis, dict), f"{prefix}: hypothesis object")
                require(hypothesis.get("inference") is True, f"{prefix}: hypothesis not marked inference")
                require(hypothesis.get("confidence") in ("high", "medium", "low"), f"{prefix}: hypothesis confidence")
                require(all(isinstance(hypothesis.get(key), str) and hypothesis[key].strip() for key in ("statement", "rationale")), f"{prefix}: hypothesis evidence")
    counts = dict(Counter(row["inspection_status"] for row in rows))
    return {
        "game": game,
        "records": len(rows),
        "inspection_counts": counts,
        "available_images_have_recorded_inspection": counts.get("not_reviewed", 0) == 0,
        "accepted_labels": 0,
        "limitation": "Structural and hash validation does not independently prove visual fidelity.",
    }


def validate_game(game, verify_hashes):
    directory = PILOT / game
    rows = []
    for start, stop in ((1, 504), (505, 1000)):
        path = directory / f"review-v2-{start:04d}-{stop:04d}.jsonl"
        shard = read_records(path)
        require(
            [row.get("level") for row in shard] == list(range(start, stop + 1)),
            f"{path}: expected exact ordered sequence {start}..{stop}",
        )
        rows.extend(shard)
    return validate_records(
        game, rows, directory / "sheets-20261009" / "index.json", verify_hashes
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=CONTRACT["games"], action="append")
    parser.add_argument("--verify-hashes", action="store_true")
    args = parser.parse_args()
    summaries = [validate_game(game, args.verify_hashes) for game in args.game or CONTRACT["games"]]
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
