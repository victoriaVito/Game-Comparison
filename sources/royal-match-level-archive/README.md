# Royal Match — level board archive

Browsable archive of **13,087 Royal Match levels**, each showing the **game board exactly as it
appears immediately before the player's first move**.

Built by extracting frames from a 704-video / 358-hour public YouTube gameplay playlist.

## 🔎 Browse it

**→ [Open the archive](../../)** (GitHub Pages)

| Action | How |
|---|---|
| Find a level | Type the number in **Jump to level #** |
| Link to a level | append `#L8451` to the URL |
| Inspect | **Click** a level |
| Next / previous level | `←` / `→` |
| Close | `Esc` |
| Spot-check quality | tick **Flagged / low-confidence only** |
| Scan density | **Compact / Normal / Large** |

## What's here

| | |
|---|---|
| Levels | **13,087** |
| Coverage of levels the playlist actually contains | **100%** |
| Source videos | 704 |
| Board captured strictly before the first move | **13,089 / 13,089 — 0 violations** |
| Every image verified to be a real game board | **13,087 / 13,087** |
| Board resolution | 414×896 |

### Level coverage

Levels span **2 → 13,500**. 411 levels in that range are **never covered by any video** in the
playlist (30 blocks; largest are 12451-12500, 5411-5445, 7286-7310, 7486-7510, 8751-8775), plus one
level (11565) whose video ends on the map screen without ever playing it. Everything that was
recorded and published is here. Uncaptured levels appear in the UI as "not captured", naming the
source video, rather than being silently skipped.

## This is a reduced copy

GitHub Pages caps a site at 1 GB; the full archive is 8.89 GB across 65,390 files. This copy carries
**board screenshots only**, at 414×896 (downscaled from 592×1280). Omitted here:

- **play-dialog screenshots** — the pre-level "Level N" panel with Goal and boosters
- **per-level verification clips** — a 10fps `window.mp4` per level spanning board-appearance →
  first move, used to audit the frame choice frame by frame

Dropping the play dialog bought **2.1× the pixels** on the board within the same budget. The
full-resolution archive, with both screens and all 13,072 clips, is retained separately.

Each level links back to its **source video at the exact timestamp** the frame was taken from.

## How it was built

```
playlist.json ──► fetch.py ──► detect.py ──► extract frames ──► delete video ──► checkpoint
                  (yt-dlp)     (OpenCV)        (ffmpeg)          (disk stays small)
```

The key insight: **video titles encode their level ranges** ("Royal Match Gameplay Level 2-30") and
levels always appear in ascending order — so every video carries independent ground truth, and OCR
of the on-screen "Level N" is verified against an expected sequence rather than trusted.

Finding the board frame is the hard part. It is derived by anchoring on the **first move** (detected
from the Moves counter changing) and walking backwards at native frame rate to the last settled
frame. Because the pre-level booster animation always finishes before the player can move, this
lands after the animation by construction.

Full method, per-flag reference, and the eight defects found and fixed during the build are in
[`docs/`](docs/) — `SPEC.md` (design + revision history), `STATUS.md` (final numbers), and the
`NOTES_*.md` investigation records.

## Flags

Levels are flagged where the extraction is worth a second look; **none are ever excluded.** Use the
**Flagged / low-confidence only** filter to review them.

| Flag | Meaning |
|---|---|
| `reward_anim_uncertain` | Booster animation found, end slightly fuzzy — frames fine |
| `short_board_window` | Brief settled run, usually animated board props |
| `no_post_reward_still` | Reward ran into the first move; latest valid pre-move frame used |
| `count_mismatch` | Level count differs from the title's claim |
| `retry_attempt` | Level failed and replayed; best attempt kept |
| `ocr_sequence_mismatch` | OCR disagreed with sequence; sequence won |
| `level_from_position` | Number recovered positionally after OCR failure |
| `tutorial_overlay` | Tutorial tooltip present; board dimmed |

## Source & attribution

Frames are extracted from a public YouTube gameplay playlist. Royal Match is a product of
Dream Games. This is a derived reference index for internal analysis.
