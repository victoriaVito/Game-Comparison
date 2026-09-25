from __future__ import annotations

import json
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STAGING_ROOT = PROJECT_ROOT / "staging"
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"
REVIEW_PATH = Path(__file__).with_name("review_0016_0100.json")


def load_batch() -> list[tuple[dict[str, object], Path]]:
    entries: list[tuple[dict[str, object], Path]] = []
    for manifest_path in sorted(STAGING_ROOT.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        entries.extend(
            (entry, manifest_path.parent / str(entry["board"]))
            for entry in manifest["levels"]
        )
    return entries


def main() -> None:
    review = json.loads(REVIEW_PATH.read_text())
    reviewed_levels = review.get("reviewed_levels", [])
    expected_batch = list(range(16, 101))
    if review.get("result") != "passed" or reviewed_levels != expected_batch:
        raise RuntimeError("Calibration batch does not have a complete passed review")

    manifest = json.loads(MANIFEST_PATH.read_text())
    existing = {int(entry["level"]): entry for entry in manifest["levels"]}
    batch = load_batch()
    batch_levels = [int(entry["level"]) for entry, _ in batch]
    if batch_levels != expected_batch:
        raise RuntimeError("Staging does not contain the exact 16-100 sequence")

    levels_dir = PROJECT_ROOT / "levels"
    levels_dir.mkdir(exist_ok=True)
    for entry, source in batch:
        if not source.is_file() or source.read_bytes()[:3] != b"\xff\xd8\xff":
            raise RuntimeError(f"Invalid board image: {source}")
        flags = [flag for flag in entry["flags"] if flag != "needs_visual_review"]
        entry["flags"] = [*flags, "visual_review_passed"]
        existing[int(entry["level"])] = entry
        shutil.copy2(source, levels_dir / source.name)

    levels = [existing[level] for level in sorted(existing)]
    if [entry["level"] for entry in levels] != list(range(1, 101)):
        raise RuntimeError("Merged manifest does not contain the exact 1-100 sequence")
    manifest.update(
        {
            "source": "Multiple YouTube walkthroughs; see source_url per level",
            "source_count": len({entry["source_url"] for entry in levels}),
            "expected_levels": 100,
            "captured_levels": 100,
            "levels": levels,
        }
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
