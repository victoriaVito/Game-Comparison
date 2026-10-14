import json
from pathlib import Path

BASE = Path(".ai-work/temporary/level-review-archive/royal-kingdom/batch-05001-05300")
OUT = BASE / "candidates-05253-05300.jsonl"
CHECKPOINT = BASE / "candidates-05253-05300.checkpoint.json"
MANIFEST = json.loads((BASE / "sheets/index.json").read_text())
FIELDS = set(json.loads(Path(".ai-work/temporary/level-review-pilot/review_contract.json").read_text())["record_fields"])


def save_sheet(start, observations):
    sheet = next(s for s in MANIFEST["sheets"] if s["sheet"] == f"levels-{start}-{start + 11}.jpg")
    previous = [json.loads(line) for line in OUT.read_text().splitlines()] if OUT.exists() else []
    existing = {r["level"]: r for r in previous}
    assert len(observations) == 12
    for record, details in zip(sheet["records"], observations):
        level = record["level"]
        assert start <= level <= start + 11
        if level in existing:
            continue
        tags, observation, partial, note = details
        missing = not record.get("image") or not Path(record["image"]).is_file()
        row = dict(
            schema_version=2, game="royal-kingdom", level=level,
            review_status="needs_review",
            inspection_status="missing" if missing else "partial" if partial else "reviewed",
            image_path=None if missing else record["image"],
            image_sha256=None if missing else record["sha256"],
            sheet_path=str(BASE / "sheets" / sheet["sheet"]), cell=record["cell"],
            geometry_tags=[] if missing else tags,
            observation="Source image is missing." if missing else observation,
            occlusion="unknown" if missing else "partial" if partial else "none",
            confidence="unknown" if missing else "low" if partial else "medium",
            verified_difficulty="unknown", verified_strategy="unknown", verified_evidence=[],
            difficulty_hypothesis=None, strategy_hypothesis=None,
            review_note=note or "Visual layout only; mechanic identities and hidden layers are not verified."
        )
        assert set(row) == FIELDS
        existing[level] = row
    rows = [existing[k] for k in sorted(existing)]
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    CHECKPOINT.write_text(json.dumps({
        "range": [5253, 5300], "saved_rows": len(rows),
        "inspected_sheets": sorted(set(r["sheet_path"] for r in rows)),
        "reviewed": sum(r["inspection_status"] == "reviewed" for r in rows),
        "partial": sum(r["inspection_status"] == "partial" for r in rows),
        "missing": sum(r["inspection_status"] == "missing" for r in rows),
        "last_saved_sheet": sheet["sheet"],
        "status": "completed" if len(rows) == 48 else "in_progress"
    }, indent=2) + "\n")
    print(f"Saved {sheet['sheet']}: {len(rows)} cumulative rows")


if __name__ == "__main__":
    save_sheet(5253, [
        (["asymmetric"], "Two stacked tile pockets occupy the left, with a small downward tile extension. Purple-framed square blockers project to their right; two separate stacks of blue trays sit across a broad background gap on the far right.", False, "Far-right trays are described separately; their status as match cells is unclear, so split_regions is withheld."),
        (["asymmetric"], "Two cyan L-shaped channels run down the left and turn right along the lower board, separated by red covered cells. A tile patch sits in the upper-right beside tall white columns; bright bursts overlap that patch.", True, "Upper-right effects obscure individual cells. Channels and covered cells do not establish disconnected play regions."),
        (["compact_full_field", "layered_bands"], "The lower rectangular match grid has brown stacked discs around its border and across a middle horizontal row, leaving tile-filled strips above and below. Chains, clouds and a fire bar belong to the arena above the grid.", False, ""),
        (["central_mass"], "A stepped tile cap spans the top. A broad green covered block fills the middle, narrowing near the bottom between red blocks and striped purple posts; square emblem boxes fill the lower corners and flank a central post.", False, "The green area is covered grid, not an empty gap."),
        (["asymmetric"], "Tall purple columns fill the upper-left while tiles fill the upper-right. Green sprout rows and a row of round white objects extend below; the bottom boundary has alternating projecting feet and recessed gaps, with a framed background opening near the middle.", False, "The mixed lower objects remain visually connected; no split label is inferred from blocker types."),
        (["compact_full_field"], "A square tile field is bordered by single brown blocks on all four sides and tall purple cylinders along both outer vertical edges. A detached narrow strip of face-like objects sits above across a visible background gap.", False, "The detached upper strip may be a tray rather than match cells; split_regions is withheld."),
        (["asymmetric"], "Tiles fill the upper-left, and stacked orange-framed boxes fill the upper-right. Two tall flower-filled columns descend through the field; pale-blue panels occupy the lower rows, with small background openings between panels and an inset empty window above.", False, "Pale-blue panels are occupied cells, not empty regions; connectivity around the central openings is ambiguous."),
        (["compact_full_field"], "The lower tile grid is broad and rectangular with alternating single-cell projections on its top and bottom edges. Five glowing devices linked by pink beams occupy the separate boss arena above.", False, "Arena beam geometry is excluded from match-board tags."),
        (["split_regions", "layered_bands"], "An isolated wide top strip alternates purple plus-marked blocks and crown tiles. A clear horizontal background gap separates it from the lower field, where green covered cells sit above purple blocks between beige panels at both sides.", False, ""),
        (["asymmetric"], "An uninterrupted tile column group runs down the left with a purple tray beneath. The right consists of alternating red and blue large blocks and keyhole boxes, including a central box; background gaps appear between the large right-side blocks.", False, "Large framed objects make exact right-side match-cell connectivity unclear; split_regions is withheld."),
        (["layered_bands"], "Tall red side columns flank a tile pocket at the upper center. Yellow round objects span beneath the tiles, followed by an orange diamond-block row and gray circular sockets; the lower sockets form side legs and a narrow central stem around background recesses.", False, ""),
        (["compact_full_field"], "Two broad tile halves flank a narrow full-height beige blocker column. Red target blocks line the stepped outer edges, with several targets intruding near the lower-right; the central divider is occupied rather than an empty gap.", False, ""),
    ])
    save_sheet(5265, [
        (["compact_full_field"], "The lower rectangular match field has tiles interspersed with green gem-marked covered cells in several vertical runs. Circular targets, doll-like objects and yellow platforms occupy the separate arena above.", False, ""),
        (["central_mass"], "Tiles occupy a wide upper cap while stacked brown discs fill nearly all the central and lower field. Purple cylinders and blue trays line both sides; the bottom center is recessed upward, leaving two blocker-filled feet.", False, ""),
        (["asymmetric"], "A tall purple-striped block column occupies the left; flowers cross the upper-middle and tiles occupy the upper-right. Purple striped blocks form a bottom band, but a large pot and bright sparkles cover much of the center-right grid.", True, "The pot and effects prevent a complete boundary/connectivity interpretation."),
        (["central_mass", "layered_bands"], "Tiles flank a dense central block of purple containers in the upper rectangle. Paired horizontal brown bars sit below on left and right, and more purple containers form lower side pockets around two large orange curved objects at bottom center.", False, "Large framed lower objects are occupied, not empty separation."),
        (["split_regions", "layered_bands"], "Two separated orange-box strips sit at the top. Across a clear horizontal gap, the middle tile rectangle is flanked by white columns and purple pebble strips; another background gap separates two pairs of blue square objects at the bottom.", False, ""),
        (["compact_full_field"], "The lower tile field has shallow corner notches and a narrower center extension along the bottom. Cyan ghost-like objects surround a central orange stack in the separate upper boss arena.", False, ""),
        (["asymmetric"], "Tiles form the upper-right part of a broad field. Beige square blockers with blue domes trace a diagonal through the center; large blue devices occupy the lower-left triangle. The overall outer boundary is mostly rectangular despite the stepped internal blockers.", False, "The diagonal blocker line is not a stepped play boundary; stair_step is withheld."),
        (["compact_full_field", "central_mass"], "A three-by-three cluster of brown squares occupies the center of the tile field. The outer edge has a top-center notch and shallow left/right recesses at mid-height, but tile rows connect across above and below the cluster.", False, ""),
        (["asymmetric"], "A narrow tile cap sits above two cyan channels that descend and join along the bottom around a large background opening. Blue devices fill lower side pockets; purple-framed structures border the channels, and flashes cover several upper tiles.", True, "Upper flashes obscure cells. The large interior opening is below the tile cap; open_center is withheld because the channels' cell role is uncertain."),
        (["asymmetric"], "Pale-blue panels cap a dense left block of blue diamond tiles. Green covering fills upper-right and lower-right lobes around a middle-right tile pocket; a central background window separates two red blocks vertically.", False, "Covered lobes are grid occupancy. The off-center window alone does not justify open_center."),
        (["compact_full_field"], "A rectangular lower match grid contains mixed tiles, with a bright activation flash at the lower-left corner. Platforms, a small hat-like object and a cloaked figure occupy the separate boss arena above.", True, "The lower-left flash hides some initial cell contents."),
        (["asymmetric"], "Tiles occupy the upper-left and continue into a lower-left pocket of purple plus-marked blocks separated by vertical flower strips. A solid red covered rectangle fills the upper-right, above a large beige panel at lower-right; a narrow background recess lies beside that panel.", False, "The covered red area is part of the occupied field, not a gap."),
    ])
    save_sheet(5277, [
        (["asymmetric"], "A broad tile rectangle occupies the right, bordered on its left by two vertical runs of red targets. Keyhole boxes, red-fruit trays and a purple chest stack on the left, with small framed background windows between them.", False, "Left-side framed objects are described without treating their intervening windows as proof of disconnected match regions."),
        (["stair_step", "asymmetric"], "A rectangular left field has tiles above rows of purple containers and green gem-covered cells. To the right, tall purple columns rise progressively toward the upper-right inside a stepped red border; the outer lower/right boundary climbs diagonally.", False, "The stair_step tag refers to the visible outer boundary, not just the column heights."),
        (["asymmetric"], "Three purple-container islands sit down the left with broad gaps between them. A tall beige panel occupies the middle-right, next to alternating brown discs and cyan circles; a narrow tile strip runs down the far-right.", False, "The detached left islands are visible, but the beige panel and container islands' match-cell role is uncertain; split_regions is withheld."),
        (["asymmetric"], "The lower match field consists of two tile rectangles offset vertically, the right extending lower than the left. Orange diamond blocks line their outer sides and a shared central divider. Green strips, blue figures and targets sit in the arena above.", False, "The occupied center divider is not an empty split."),
        (["asymmetric"], "Four pale-blue panels stack at the far-left beside brown blocks and two large blue panels. A purple tray column rises centrally and turns across the bottom-right; tiles occupy a vertical pocket on the right, with a striped small chest inset among them.", False, ""),
        (["central_mass"], "Upper tile pockets flank a tall beige blocker mound that widens through the middle. Red blocks sit at the sides of the mound above blue tray stacks in both lower corners; a large cyan square fills the lower center beneath a narrow framed purple opening.", False, "The beige mound is occupied grid; its stepped internal boundary is not stair_step."),
        (["asymmetric"], "Orange boxes and horizontal white columns fill the upper-left while a tile patch occupies the upper-right. Blue diamond blocks fill two lower diagonal banks around a staircase-shaped background opening; brown discs and vertical white columns border the right bank. Bright bursts cover upper-right cells.", True, "The internal stepped opening is not the outer play boundary. Effects obscure the upper-right patch; connectivity around the diagonal opening remains uncertain."),
        (["layered_bands"], "Tiles form a broad top strip between purple striped side columns. Two sprout-filled square pockets sit beneath it around blue vertical panels; the bottom is a wide band of orange patterned blocks, with purple columns extending down both sides.", False, "Blue panels and patterned blocks occupy cells; their different appearance does not create separate regions."),
        (["compact_full_field"], "The lower rectangular tile field is divided by a single central column of red target blocks. Purple pots, a green figure and a small fire patch belong to the boss arena above, not the grid.", False, ""),
        (["asymmetric", "layered_bands"], "Orange diamond blocks form upper and lower horizontal banks, with purple cylinders stepping along the left edge. A large circular orange object and red-cylinder panel interrupt the middle-left; a continuous tile strip runs the full height on the right.", False, ""),
        (["central_mass"], "Green covering fills a wide middle block and both top corners around a small top-center tile pocket. Two purple square boxes interrupt the covered area's sides; blue round devices occupy two lower feet flanking a cyan center panel and a bottom-center background notch.", False, "Green covering is not empty space, and the lower notch is peripheral rather than an open center."),
        (["asymmetric"], "Tiles occupy the upper-left above a purple drawer. Tall red striped columns form the center and lower-left banks; four large blue panels stack in pairs at the right beside a vertical purple block strip. Small purple-framed background gaps interrupt the center.", False, "Large framed structures leave precise match-cell connectivity uncertain; tags beyond asymmetry are withheld."),
    ])
    save_sheet(5289, [
        (["asymmetric", "layered_bands"], "The upper rectangle alternates brown discs and cyan circular objects, with small white figures in one row. Horizontal brown bars fill the lower-left beside a purple-framed background opening, while tiles fill the lower-right; sparkles overlap those lower-right tiles.", True, "Lower-right activation effects obscure some tile contents."),
        (["compact_full_field"], "The lower rectangle contains tiles around a diagonal band of purple containers climbing from bottom-left to top-right. The boundary remains rectangular; clouds, a robot and a cyan beam occupy the separate upper arena.", False, "The diagonal occupied band is not a stepped boundary."),
        (["asymmetric", "central_mass"], "Blue round devices run across the top and down the far-left in an L-shaped rim. Tiles occupy a narrow upper-middle pocket between clock panels; red covered cells fill both sides and the lower center, with two more clocks in the bottom corners.", False, "The visible opening below the top rim is near the upper-left, not an empty central area."),
        (["central_mass"], "A narrow central tile pocket is surrounded by dense yellow round blockers and gray sockets. Purple striped columns and two red blocks border the outer sides, whose upper-left and lower-right projections make the outline offset.", False, ""),
        (["compact_full_field", "layered_bands"], "Brown stacked discs form vertical bands through a rectangular tile field. Red target columns run down both outer edges and in two shorter central runs; orange boxes form a dense bottom band above a row of purple trays.", False, "The occupied bands do not divide the grid with an empty gap."),
        (["asymmetric"], "A short isolated tile strip sits at the upper-left. Below and to its right is a purple-framed blue panel, then a large orange timer panel bordered along the bottom and right by blue oval sockets; broad background fills most of the intervening space.", False, "Only the top strip is clearly matchable tiles. Other framed panels' roles are uncertain, so split_regions is withheld."),
        (["stair_step"], "In the lower match field, green covered side lobes taper inward in steps from both top corners. A horizontal crown-tile line crosses their narrow middle, and background recesses widen above and below it. Orange stacks and purple round devices occupy the separate upper arena.", False, "The narrow center crown cell appears to bridge the lobes; a split_regions tag is not supported."),
        (["asymmetric"], "Tiles occupy a narrow upper-middle strip. Cyan channels loop through the left and right wings and join in a wide horizontal middle band; the bottom channel branches around an open bottom-center notch, flanked by purple cylinders and orange curved panels.", False, "The cyan channels and large side objects have uncertain cell roles; the bottom notch is not labeled open_center."),
        (["asymmetric", "central_mass"], "A continuous tile strip runs down the far-left. Purple pebble covering fills most of the remaining rectangle around two sets of vertical white columns; blue devices sit to their right, while orange round blocks and blue domes form vertical and horizontal internal lines.", False, ""),
        (["stair_step", "asymmetric", "central_mass"], "Purple containers dominate a broad field with a small tile patch at the upper-right. Purple plus blocks form an internal stepped line, orange circular objects fill lower-left bands beside a beige corner panel, and the outer lower-right edge retreats in visible steps.", False, "stair_step describes the lower-right outer edge, not the internal plus-marked line."),
        (["central_mass"], "Green covering surrounds a small upper-center tile pocket and two striped chests in the top corners. A narrow covered stem runs down the middle between horizontal background slots; two large red-framed banks of brown bars fill the lower-left and lower-right.", False, "The center is occupied by a green stem, not an empty notch; lower banks' precise cell roles are uncertain."),
        (["compact_full_field"], "The lower match board is an unobstructed wide rectangle of mixed colored tiles without obvious internal gaps or blocker bands. A robot flanked by two blue figures and a curved row of yellow rings occupy the separate upper boss arena.", False, "Arena rings and robot placements are excluded from match-board geometry."),
    ])
