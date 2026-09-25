from __future__ import annotations

import fcntl
import json
import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"
STAGING_ROOT = PROJECT_ROOT / "staging" / "no-booster"
SOURCES_PATH = Path(__file__).with_name("no_booster_recaptures_m3.json")
STATE_LOCK_PATH = Path(__file__).with_name("archive_state.lock")


@contextmanager
def state_lock() -> Iterator[None]:
    with STATE_LOCK_PATH.open("a") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def main() -> None:
    sources = json.loads(SOURCES_PATH.read_text())["sources"]
    levels = tuple(int(source["level"]) for source in sources)

    with state_lock():
        manifest = json.loads(MANIFEST_PATH.read_text())
        entries = {int(entry["level"]): entry for entry in manifest["levels"]}
        replacements: list[tuple[int, Path, dict[str, object]]] = []
        for level in levels:
            staging = STAGING_ROOT / f"level-{level:04d}"
            staged_manifest = json.loads((staging / "manifest.json").read_text())
            staged_entry = staged_manifest["levels"][0]
            if int(staged_entry["level"]) != level:
                raise RuntimeError(f"Staged manifest mismatch for level {level}")

            source_board = staging / staged_entry["board"]
            if source_board.read_bytes()[:3] != b"\xff\xd8\xff":
                raise RuntimeError(f"Invalid JPEG for level {level}")

            replacements.append((level, source_board, staged_entry))

        for level, source_board, staged_entry in replacements:
            target_board = PROJECT_ROOT / entries[level]["board"]
            shutil.copy2(source_board, target_board)
            staged_entry["board"] = entries[level]["board"]
            staged_entry["flags"] = [
                flag
                for flag in staged_entry.get("flags", [])
                if flag != "needs_visual_review"
            ] + ["visual_review_passed", "no_booster_recapture"]
            entries[level] = staged_entry

        manifest["levels"] = [entries[int(entry["level"])] for entry in manifest["levels"]]
        atomic_write_json(MANIFEST_PATH, manifest)
    print(json.dumps({"published": list(levels), "captured_levels": manifest["captured_levels"]}))


if __name__ == "__main__":
    main()
