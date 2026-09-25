from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_UNGROUNDED_CLAIMS = (
    "the player paid",
    "payment is required",
    "must pay",
    "has no monetization",
)


def validate_team(team: dict[str, object]) -> list[str]:
    errors: list[str] = []
    agents = team.get("agents", [])
    agent_ids = [agent["id"] for agent in agents]
    if len(agent_ids) != len(set(agent_ids)):
        errors.append("Agent IDs must be unique")
    for agent in agents:
        parent = agent.get("parent")
        if parent is not None and parent not in agent_ids:
            errors.append(f"Unknown parent for {agent['id']}: {parent}")
    for source, target in team.get("handoffs", []):
        if source not in agent_ids or target not in agent_ids:
            errors.append(f"Invalid handoff: {source} -> {target}")
    return errors


def validate_notes(notes: dict[str, object], duration: float) -> list[str]:
    errors: list[str] = []
    timestamps: list[float] = []
    required = ("id", "timestamp_seconds", "title", "gameplay", "monetization", "impression")
    for note in notes.get("notes", []):
        missing = [field for field in required if field not in note]
        if missing:
            errors.append(f"Missing fields in note: {missing}")
            continue
        timestamp = float(note["timestamp_seconds"])
        timestamps.append(timestamp)
        if not 0 <= timestamp <= duration:
            errors.append(f"Timestamp outside video: {note['id']}")
        monetization = str(note["monetization"]).lower()
        if any(claim in monetization for claim in FORBIDDEN_UNGROUNDED_CLAIMS):
            errors.append(f"Unsupported monetization wording: {note['id']}")
    if timestamps != sorted(timestamps):
        errors.append("Commentary timestamps must be ordered")
    if any(right - left < 10 for left, right in zip(timestamps, timestamps[1:])):
        errors.append("Commentary pauses must be at least 10 seconds apart")
    summary = notes.get("monetization_summary", {})
    if summary.get("status") not in {"observed", "not_observed", "not_determinable"}:
        errors.append("Invalid monetization summary status")
    if not summary.get("limit"):
        errors.append("Monetization summary requires an evidence limit")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", type=Path, default=PROJECT_ROOT / "agents" / "team.json")
    parser.add_argument("--notes", type=Path, default=PROJECT_ROOT / "analysis" / "video_notes.json")
    parser.add_argument("--duration", type=float, default=1394.559833)
    args = parser.parse_args()

    team = json.loads(args.team.read_text())
    notes = json.loads(args.notes.read_text())
    errors = validate_team(team) + validate_notes(notes, args.duration)
    result = {
        "status": "passed" if not errors else "failed",
        "agents": len(team["agents"]),
        "handoffs": len(team["handoffs"]),
        "commentary_notes": len(notes["notes"]),
        "errors": errors,
    }
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
