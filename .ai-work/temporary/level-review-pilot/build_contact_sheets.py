import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    "royal-match": ROOT / "sources/royal-match-level-archive",
    "royal-kingdom": ROOT / "royal-kingdom",
}
CELL_WIDTH = 300
CELL_HEIGHT = 650
LABEL_HEIGHT = 28
PER_SHEET = 12


def build(game, start, end, output):
    source = SOURCES[game]
    manifest = json.loads((source / "manifest.json").read_text())
    entries = {entry["level"]: entry for entry in manifest["levels"]}
    records = []
    for level in range(start, end + 1):
        entry = entries.get(level)
        if entry is None:
            records.append({"level": level, "status": "missing_manifest_entry"})
            continue
        path = source / entry["board"]
        if not path.resolve().is_relative_to(source.resolve()):
            raise ValueError(f"Board path escapes source directory: {path}")
        with Image.open(path) as image:
            image.load()
            if image.format != "JPEG":
                raise ValueError(f"Not a JPEG: {path}")
            dimensions = list(image.size)
        records.append({
            "level": level,
            "status": "available_not_reviewed",
            "image": str(path.relative_to(ROOT)),
            "dimensions": dimensions,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })

    output.mkdir(parents=True, exist_ok=False)
    sheets = []
    for offset in range(0, len(records), PER_SHEET):
        batch = records[offset:offset + PER_SHEET]
        sheet = Image.new("RGB", (CELL_WIDTH * 4, (CELL_HEIGHT + LABEL_HEIGHT) * 3), "white")
        draw = ImageDraw.Draw(sheet)
        for index, record in enumerate(batch):
            x = index % 4 * CELL_WIDTH
            y = index // 4 * (CELL_HEIGHT + LABEL_HEIGHT)
            draw.text((x + 8, y + 6), f"{game} | Level {record['level']}", fill="black")
            if "image" in record:
                with Image.open(ROOT / record["image"]) as image:
                    thumbnail = ImageOps.contain(
                        image.convert("RGB"), (CELL_WIDTH, CELL_HEIGHT), Image.Resampling.LANCZOS
                    )
                sheet.paste(thumbnail, (x + (CELL_WIDTH - thumbnail.width) // 2, y + LABEL_HEIGHT))
            else:
                draw.text((x + 8, y + LABEL_HEIGHT + 20), "MISSING SOURCE", fill="red")
            record["cell"] = index + 1
        filename = f"levels-{batch[0]['level']:04d}-{batch[-1]['level']:04d}.jpg"
        sheet.save(output / filename, quality=95)
        with Image.open(output / filename) as saved:
            saved.load()
            if saved.size != sheet.size:
                raise ValueError(f"Invalid sheet dimensions: {filename}")
        sheets.append({"sheet": filename, "records": batch})
    index = {
        "game": game,
        "range": [start, end],
        "status": "prepared_not_visually_reviewed",
        "requested": len(records),
        "available": sum("image" in record for record in records),
        "missing": [record["level"] for record in records if "image" not in record],
        "sheets": sheets,
    }
    (output / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(json.dumps({key: value for key, value in index.items() if key != "sheets"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare traceable 12-level visual review sheets.")
    parser.add_argument("--game", choices=SOURCES, required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.start < 1 or args.end < args.start:
        parser.error("Require 1 <= start <= end")
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / ".ai-work/temporary").resolve()):
        parser.error("Output must be inside the project .ai-work/temporary directory")
    build(args.game, args.start, args.end, output)
