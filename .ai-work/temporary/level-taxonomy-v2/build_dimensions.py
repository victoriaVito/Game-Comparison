"""Build a per-level multi-dimension table from data that already exists locally.

Candidate-only: nothing here accepts a label. Each dimension records its source so it
can be audited. Geometry uses the archive candidate tags, overridden by the newest
direct/multi-reviewer adjudication when one exists.
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
INTRO_REPORT = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "/Users/victoria.serrano/Shared with me/codex_taussen/docs/research/gameplay-introductions-report.md"
)
ADJ = ROOT / ".ai-work/temporary/level-review-archive/adjudication"


def parse_intro_tables(text):
    tables, current = {}, None
    for line in text.splitlines():
        if line.startswith("## Royal Kingdom element introductions"):
            current = "royal-kingdom"
        elif line.startswith("## Royal Match mapped element introductions"):
            current = "royal-match"
        elif line.startswith("## "):
            current = None
        elif current:
            m = re.match(r"^\|\s*([\d,]+)\s*\|\s*([^|]+?)\s*\|", line)
            if m:
                tables.setdefault(current, []).append(
                    {"level": int(m.group(1).replace(",", "")), "element": m.group(2)}
                )
    return tables


def rk_moves(ocr):
    tokens = [str(t).strip() for t in ocr or []]
    for i, tok in enumerate(tokens):
        if re.fullmatch(r"moves?", tok, re.I) and i + 1 < len(tokens) and tokens[i + 1].isdigit():
            return int(tokens[i + 1])
    return None


def band(level, size=500):
    lo = (level - 1) // size * size + 1
    return f"{lo:05d}-{lo + size - 1:05d}"


def main():
    intros = parse_intro_tables(INTRO_REPORT.read_text())
    (OUT / "element-introductions.json").write_text(
        json.dumps(
            {
                "source": str(INTRO_REPORT),
                "evidence_status": "community-reported; semantic names not independently verified",
                "introductions": intros,
            },
            indent=2,
        )
        + "\n"
    )

    geometry = {}
    for row in json.loads((ROOT / ".ai-work/temporary/figjam-upload/manifest.json").read_text()):
        geometry[(row["game"], row["level"])] = {
            "tags": row["tags"],
            "inspection": row.get("inspection"),
            "confidence": row.get("confidence"),
            "source": "archive_candidate",
        }
    for f in sorted(ADJ.glob("direct-visual-check-*.jsonl")):
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            tags = r.get("proposed_geometry_tags")
            if tags is None:
                continue
            geometry[(r["game"], r["level"])] = {
                "tags": sorted(tags),
                "inspection": r.get("inspection_status", "partial"),
                "confidence": r.get("confidence"),
                "source": f"adjudication:{f.name}",
            }

    shared_features = INTRO_REPORT.parents[2] / "analysis/features.json"
    features_path = shared_features if shared_features.exists() else ROOT / "analysis/features.json"
    rm_features = {r["level"]: r for r in json.loads(features_path.read_text())["levels"]}
    rm_manifest = json.loads((ROOT / "sources/royal-match-level-archive/manifest.json").read_text())["levels"]
    rk_manifest = json.loads((ROOT / "royal-kingdom/manifest.json").read_text())["levels"]

    rows = []
    for game, entries in (("royal-match", rm_manifest), ("royal-kingdom", rk_manifest)):
        intro = sorted(intros.get(game, []), key=lambda x: x["level"])
        intro_at = collections.defaultdict(list)
        for x in intro:
            intro_at[x["level"]].append(x["element"])
        for e in entries:
            lvl = e["level"]
            prior = [x for x in intro if x["level"] <= lvl]
            if game == "royal-match":
                feat = rm_features.get(lvl, {})
                mode = feat.get("game_mode") or feat.get("level_type", "unknown")
                tutorial = feat.get("tutorial")
                target_count = feat.get("target_count")
                moves = e.get("moves_start")
            else:
                mode = e.get("level_type", "unknown")
                tutorial = e.get("tutorial")
                target_count = None
                moves = rk_moves(e.get("ocr_text"))
            geo = geometry.get((game, lvl), {"tags": [], "inspection": "missing", "confidence": None, "source": None})
            rows.append(
                {
                    "game": game,
                    "level": lvl,
                    "level_band": band(lvl),
                    "mode": mode,
                    "tutorial": tutorial,
                    "target_count": target_count,
                    "moves_start": moves,
                    "element_era": prior[-1]["element"] if prior else None,
                    "elements_available_count": len(prior),
                    "element_introduced_here": intro_at.get(lvl, []),
                    "geometry_tags": geo["tags"],
                    "geometry_tag_count": len(geo["tags"]),
                    "geometry_source": geo["source"],
                    "geometry_inspection": geo["inspection"],
                    "geometry_confidence": geo["confidence"],
                    "capture_flags": e.get("flags", []),
                    "status": "candidate",
                }
            )

    with open(OUT / "level-dimensions.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    summary = {"levels": len(rows), "sources": {"royal_match_features": str(features_path), "element_introductions": str(INTRO_REPORT)}, "by_game": {}}
    for game in ("royal-match", "royal-kingdom"):
        g = [r for r in rows if r["game"] == game]
        summary["by_game"][game] = {
            "levels": len(g),
            "mode": dict(collections.Counter(r["mode"] for r in g)),
            "tutorial": sum(1 for r in g if r["tutorial"]),
            "target_count": dict(collections.Counter(str(r["target_count"]) for r in g)),
            "moves_known": sum(1 for r in g if r["moves_start"] is not None),
            "element_intro_levels": sum(1 for r in g if r["element_introduced_here"]),
            "geometry_tag_count": dict(collections.Counter(r["geometry_tag_count"] for r in g)),
            "geometry_adjudicated": sum(1 for r in g if (r["geometry_source"] or "").startswith("adjudication")),
        }
    summary["limitations"] = [
        "Element introductions are community-reported; absence from the initial frame is not proof of absence.",
        "Royal Kingdom target_count is not extracted; moves_start for Royal Kingdom comes from noisy OCR.",
        "Geometry tags are candidates; none are accepted.",
    ]
    (OUT / "level-dimensions-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
