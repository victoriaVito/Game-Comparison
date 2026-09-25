# Status — COMPLETE

**Finished: 2026-09-15 14:45**

The archive is built. For how the system works see `README.md`; for the design contract and
revision history see `SPEC.md`.

---

## Final result

| | |
|---|---|
| **Levels captured** | **13,087** |
| **Coverage of levels the playlist actually contains** | **13,087 / 13,087 — 100%** |
| Videos processed | 704 / 704 (0 failures) |
| Archive size | 9.1 GB |
| **`board_t` before first move** | **13,089 / 13,089 — 0 violations** |
| Every `board.jpg` is a real board | 13,087 pass, 0 failures |
| Levels with a verification clip | 13,072 |
| Disk / manifest consistency | exact, 0 drift |

### Why 13,087 and not 13,499

The nominal span 2 → 13,500 is 13,499 levels. The difference is entirely footage that does not exist:

- **411 levels are never covered by any video.** 30 separate blocks; the largest are
  12451-12500 (50), 5411-5445 (35), 7286-7310, 7486-7510, 8751-8775 (25 each).
- **1 level (11565) is claimed by a title but never played** — `dbgQU_Y3XG0` ends on the map screen
  showing the "Level 11565" button without opening it. Verified frame by frame.
- **~182 phantom levels** from one mistyped title: `N_ApgMCPdDk` reads "Level 1551-1751" but is
  really 1551-1571 (201 levels in 32.4 min would be 9.7s/level against a 98.2s median).

Every level that was ever recorded and published is in the archive.

---

## Flags (13,089 segments)

| Flag | Count | % | Meaning |
|---|---|---|---|
| `reward_anim_uncertain` | 1,840 | 14.1% | Booster animation found, end slightly fuzzy — frames fine |
| `short_board_window` | 1,503 | 11.5% | Brief settled run, usually animated board props |
| `no_post_reward_still` | 397 | 3.0% | Reward ran into the first move; latest valid frame used |
| `count_mismatch` | 161 | 1.2% | Level count differs from the title's claim |
| `retry_attempt` | 56 | 0.4% | Level failed and replayed; best attempt kept |
| `ocr_sequence_mismatch` | 43 | 0.3% | OCR disagreed with sequence; sequence won |
| `level_from_position` | 41 | 0.3% | Number recovered positionally after OCR failure |
| `no_static_board` | 15 | 0.1% | No settled run; quietest pre-move frame used |
| `tutorial_overlay` | 11 | 0.1% | Tutorial tooltip present; board dimmed |
| `ocr_failed` | 10 | 0.1% | Title unreadable; sequence used |
| `board_rewound`, `low_static_confidence`, `late_board_anchor`, `first_move_regated` | 12 | 0.1% | Guard fallbacks |

Flags mark levels worth spot-checking; **no level is ever excluded because of one.** Use the
**Flagged / low-confidence only** filter in the UI.

---

## Defects found and fixed during the build

| # | Defect | Impact | Fix |
|---|---|---|---|
| 1 | `board_t` landed mid reward-animation | most levels | Anchor on first move, walk back at native fps |
| 2 | `board_appear_t` could land AFTER the first move | ~3.6% (~470 levels) | Anchor on the header, not board texture |
| 3 | Chosen-frame marker off by one | 65% of UI markers | Measure `board_frame_idx` by pixel-match, don't derive it |
| 4 | Sub-ms rounding shifted the extracted frame | 4 levels | Name a point 0.35 frames earlier |
| 5 | Levels silently dropped on OCR failure | ~0.3% | Positional alignment; out-of-range reading = *no* reading |
| 6 | **Whole UI era yielded ZERO levels** | **291 levels** | Event banner displaced the title anchor — locate title robustly |
| 7 | Saved screenshot was a feature screen, not a board | 15 levels | Validate board geometry; prefer the LAST dialog |
| 8 | Board captured too early | 2 levels | Reject implausible first-move gaps, re-derive reference |

Defects 6 and 7 were found only because the user inspected real output. Neither showed up in
per-video audits — #6 looked like "0 levels, no error", #7 looked like a perfectly valid capture.

---

## Operational notes

Three YouTube IP blocks were hit during the run ("Sign in to confirm you're not a bot"), costing
several hours. Causes and mitigations are in README gotchas #9-#11. Short version: **never download
manually while the pipeline is running**, wait a block out rather than retrying, and make sure
transient failures don't write permanent checkpoints.

Final pacing that worked: `--download-concurrency 1 --sleep-min 60 --sleep-max 120`.

---

## Background processes — stop when finished browsing

```bash
touch .stop_auto_index          # stops the manifest auto-rebuilder
pkill -f serve_range            # stops the UI server
```

## Optional housekeeping

```bash
rm -rf out_demo                 # 801 MB synthetic UI test data
rm -f work/pilot_*.mp4          # pilot videos kept for regression testing
```

Keep `work/pilot_*.mp4` if you may want to re-validate detector changes later — they are the
194-level regression set.
