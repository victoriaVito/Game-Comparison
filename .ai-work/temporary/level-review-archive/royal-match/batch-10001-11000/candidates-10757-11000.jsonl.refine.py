import json
from pathlib import Path

path = Path(".ai-work/temporary/level-review-archive/royal-match/batch-10001-11000/candidates-10757-11000.jsonl")
rows = [json.loads(line) for line in path.read_text().splitlines()]
for row in rows:
    level = row["level"]
    if level == 10775:
        row["geometry_tags"] = ["central_mass"]
        row["observation"] = (
            "Upper-right tiles narrow against a stepped frozen internal boundary. "
            "A large frozen L-shaped area dominates the center-left; a wide lower frozen "
            "jar block adjoins small frozen squares on both sides through purple-framed "
            "junctions. Background lies outside the left shoulder, not between every frozen section."
        )
        row["review_note"] = (
            "Original also rendered: sources/royal-match-level-archive/levels/10775/board.jpg. "
            "Removed split_regions: apparent sheet gaps were not sufficient evidence of disconnected "
            "regions. Withheld stair_step because the diagonal is an internal frozen/tile boundary, "
            "not the outer playable boundary. Hidden frozen contents remain unverified."
        )
    if level == 10944:
        row["review_note"] = (
            "Original also rendered: sources/royal-match-level-archive/levels/10944/board.jpg. "
            "The gate touches the tube region only at its lower-left corner in the image; "
            "withheld split_regions because the image alone does not resolve corner connectivity. "
            "Difficulty and strategy remain unverified."
        )
    if level == 11000:
        row["review_note"] = (
            "Original also rendered: sources/royal-match-level-archive/levels/11000/board.jpg. "
            "Visible stepped background bands separate the three coin/TNT chevrons. "
            "No difficulty or strategy evidence is available."
        )
    if level in (10777, 10804):
        row["inspection_status"] = "partial"
        row["occlusion"] = "partial"
        row["confidence"] = "low"
        row["review_note"] = (
            "Lower-right animation glare obscures some blocker contents; "
            "visible overall layout is recorded, but those cells require unobscured evidence."
        )
    if level == 10989:
        row["observation"] = (
            "An upper tile head joins a staggered vertical chain of four grassy squares. "
            "Eight isolated patterned single-cell blocks sit on either side across background "
            "gaps, offset from the grassy chain."
        )
path.write_text("".join(json.dumps(row) + "\n" for row in rows))
