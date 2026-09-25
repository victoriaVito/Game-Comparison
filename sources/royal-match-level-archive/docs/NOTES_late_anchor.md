# SPEC v2.6 — `board_appear_t` / `first_move_t` land after the real first move

Working notes. Updated as measurements are made.

## 0. Baseline (current `out/detect/*.json`, 8 pilot videos, 194 levels)

```
levels 194
play_t -> board_appear_t gap  p50 0.75  p75 1.33  p95 1.70  p99 14.12  max 21.58
gap > 3s : 7
   RmoqWHCPQx0 L3520  21.58
   guiinjQLYvg L9001  18.00
   guiinjQLYvg L9030  13.83
   0QfejcKagvk L11501  8.08
   guiinjQLYvg L9003   7.42
   guiinjQLYvg L9011   7.17
   guiinjQLYvg L9010   6.83
moves_verified   94/194
reward present   152
board_t null     0
board_t >= first_move_t   0
flags  reward_anim_uncertain 14, short_board_window 16, no_post_reward_still 5,
       tutorial_overlay 2, retry_attempt 3, no_static_board 1
mean confidence 0.977
```

## 1. L9011 ground truth, measured from pixels

`work/pilot_guiinjQLYvg.mp4`, 592x1280 @ 59.249 fps.

Header strip crop (`crop=592:250:0:0`, 20 fps from 759.6):
```
759.60-759.85  castle/map top bar
759.90-760.15  room sliding in, NO header
760.25         header present: Target | king | Moves 21     <-- board_appear_t
```
Moves plate crop (`crop=180:120:405:125`, 20 fps from 765.5):
```
765.50 .. 766.30   Moves 21
766.35             Moves 20        <-- first_move_t (user hand-measured ~766.60)
```
Full contact strip 758-778 @4fps confirms:
```
762.00-764.00  crimson royal_hat flies in, hops, detonates
764.25-766.30  board settled, Moves 21
766.35         Moves 21 -> 20
~774.0         Moves 20 -> 19  (the SECOND move; old first_move_t 774.167)
```
Detector emitted: board_appear_t 767.0, board_t 768.75, first_move_t 774.167,
reward_anim null, flags [no_static_board], moves_verified false.

**Confirmed: the detector locked onto the second move.**

## 2. Root cause, confirmed by measurement

Probe of `refine_window`'s internals on L9011 (`scratchpad/v26/probe.py`, 12 fps):

```
  i        t   kind    pl    pr    sat   lit     tex   mvink  diff
 14  760.167 other  0.000 0.000 0.478 0.963   294.0 1.0000   0.00
 15  760.250 board  0.477 0.604 0.478 0.963   294.0 0.2985   0.00   <- header up
 22  760.833 board  0.536 0.743 0.542 0.857   669.6 0.1786  11.04
 ...          board                    ~0.55  ~0.86  700-1000       <- pre-move board
 96  767.000 board  0.536 0.730 0.518 0.877  1489.6                 <- post-move cascade
129  769.750 board  0.534 0.728 0.550 0.861  1877.2
```

`drawn` required `tex >= max(350, 0.70 * p80(tex over the WHOLE window))`.  The post-move
explosions push p80(tex) to ~1800, so the bar is ~1260 and the pre-move board (700-1000)
never clears it.  `ready` therefore fired at 766.9, `board_appear_t` walked back only its
3 s bound to 767.0, the Moves reference was sampled post-move (reading 20 not 21), and the
first change from THAT reference was the second move at 774.17.  Exactly SPEC v2.6's
diagnosis.

The same mechanism, different cause of low texture, on the other outliers:

| level | why the board band has no texture before the first move |
|---|---|
| RmoqWHCPQx0 L3520 | board fully covered by solid orange blocker panels |
| 0QfejcKagvk L11501 | board fully covered by solid orange/green panels |
| guiinjQLYvg L9010 | board fully covered by one large red/orange panel |
| guiinjQLYvg L9011 | narrow board on a bare crimson wall |
| guiinjQLYvg L9030 | board is a single tile until the first move |
| guiinjQLYvg L9003 | "Propeller Trio / Loading" interstitial, then a small board |
| guiinjQLYvg L9001 | tutorial blacks the screen out for 3 s right after the board appears |

## 3. Second, independent defect found while implementing

The header **slides down into place over ~0.5 s**.  A Moves reference bitmap taken at the
first header frame is a translated copy of the settled one, so it matches *nothing* later.
Measured on L9001 (`scratchpad/v26/mvprobe.py`): reference at 5.000 s gives

```
  4.917-5.250   xor 0.000-0.002   (the mid-slide frames)
  5.333 onward  xor 0.253         <- every settled frame looks like a "move"
```

So `board_appear_t` is the first header frame, but the reference must be the first bitmap
the counter actually HOLDS (>= 0.40 s of header frames unchanged).  Without this the fix
would have replaced a late anchor with an instant false first move.

## 4. Third defect, found by the regression check: the tutorial dim

`A9xLB2MsDNg` L4 and L20 got WORSE with the first cut of the fix, and the reason matters.

L4, measured at native frame rate (`scratchpad/v26/sA4b.png`):
```
120.967-121.467   header up, Moves 30, plate cream coverage pr 0.724-0.725 (settled)
121.550-124.383   tutorial DIMS the whole screen; plates fall below the cream threshold,
                  so classify() says "other" - there is no header for 2.9 s
124.467           dim lifts: Moves already reads 29, Target has ticked, a match is
                  resolving.  The swipe registered DURING the dim.
```
So the first move happens inside the header gap.  A reference taken from "the first
bitmap that holds for 0.40 s of header frames" skips the pre-dim frames (they only hold
0.33 s before the header vanishes) and lands on the post-dim reading of 29 - one move
late, the very bug this task is about, in a new place.

Fix: a reading that was never *contradicted* while the header was up is also trusted,
provided it held >= 0.25 s and the header then disappeared for >= 0.25 s, and provided the
Moves plate was already at >= 90 % of its settled cream coverage (which is what rules out
a mid-slide bitmap - mid-slide pr is ~0.585 vs 0.735 settled on guiinjQLYvg L9001).
With that, L4/L20 return to their pre-change values (which were correct) and L9001/L9011
keep their fixed values.

## 5. What changed in `src/detect.py`

Only `src/detect.py` was touched.

New tunables:
```python
HDR_RUN_S = 0.25            # header must stay present this long to count as "up"
HDR_LOOSE_SPAN_S = 1.0      # re-derivation window ...
HDR_LOOSE_FRAC = 0.55       # ... header only has to be present this fraction of it
MOVES_REF_HOLD_S = 0.40     # the Moves reference must be held this long
MOVES_REF_RUN_HOLD_S = 0.25 # ... or this long, if the header then goes away
MOVES_REF_GAP_S = 0.25      # how long the header must be gone for that to apply
MOVES_REF_PLATE = 0.90      # plate must be >= this much of its settled cream coverage
MOVES_INK_LO, MOVES_INK_HI = 0.35, 2.60
LATE_ANCHOR_S = 3.0
```

New helpers `_header_anchor()` / `_header_anchor_loose()`.

In `refine_window()`:
1. `plate[]` (the Moves plate's cream coverage) is now kept - `classify()` already
   computed it, so this is free.
2. **`board_appear_t` = first frame >= `play_i` where the header is present for 0.25 s.**
   The old backward walk from `ready` is gone.
3. Sanity guard: if `board_appear_t` is more than 3 s after the last frame on which the
   play dialog was still up, re-derive with a flicker-tolerant header test; if it still
   exceeds 3 s, flag `late_board_anchor` and multiply confidence by 0.55.
4. `diffs` now starts at `appear` rather than `ready`.
5. **Moves reference** is chosen by the hold rule of sections 3 and 4 above, starting at
   `appear` (was: starting at `ready`, i.e. potentially post-move).
6. The gate on the move search and on `_move_confirmed()` changed from
   `hdr[i] and drawn[i]` (a property of the BOARD) to `legible[i]` = header present and
   the Moves box's ink coverage within 0.35-2.6x the reference's (a property of the
   PLATE).  This is what lets the search see a move on a board that is fully covered.
7. `drawn`'s percentile thresholds are now computed over `[appear, move_i)` - this level's
   own pre-move board - instead of the whole window, which the post-move explosions
   inflated.  `ready` is derived from that and is only used for picking `board_t`.
8. `assign_levels()` penalises `late_board_anchor`; `detect()` counts it in `stats`.

Unchanged: `precise_move()`, the reward detection, `consolidate_rewards()`, all OCR, all
tutorial handling (no tutorial-specific branch exists, per SPEC v2.5).

## 6. Fourth defect, found by an independent OCR audit: a one-frame seek misalignment

`scratchpad/v26/audit2.py` OCRs the Moves counter shortly after the (new) header anchor to
get the level's starting value, then OCRs the frame that `-ss board_t` actually returns.
That found 4 levels in `agxDN7ffBII` (164, 168, 175, 185) where the extracted frame read
one LESS than the level start - in both the old and the new output, so not caused by v2.6.

Cause (`scratchpad/v26/align.py`, agxDN7ffBII L164, 60.000 fps):
```
internal index 94, nominal t = 200.700 + 94/60 = 202.26667   counter still 26
emitted as round(...,3) = 202.267
ffmpeg -ss 202.267 returns the first frame at or AFTER 202.267, i.e. the NEXT one -> 25
```
A sub-millisecond rounding step is enough to cross a frame boundary.  `precise_move()` now
names a point `PRECISE_BIAS = 0.35` frames earlier, which is still inside the same frame
interval and immune to the rounding.  Verified: `-ss` at the new board_t now reads
26 / 28 / 31 / 28 on those four levels instead of 25 / 27 / 30 / 27.

## 7. Validation — 8-video pilot, 194 levels

Run: `scratchpad/v26/runall.sh` (3 concurrent, as in production).
Compared against `out/detect/*.json` by `scratchpad/v26/compare.py`.

|  | before | after |
|---|---|---|
| levels found | 194/194 | 194/194 (identical level set) |
| exact sequence match | 8/8 | 8/8 |
| `play_t -> board_appear_t` p50 / p95 / p99 / max | 0.75 / 1.70 / 14.12 / 21.58 | 0.50 / 1.33 / 1.51 / **1.67** |
| gap > 3 s | **7** | **0** |
| `board_t >= first_move_t` | 0 | 0 |
| null `board_t` / null `first_move_t` | 0 / 0 | 0 / 0 |
| `moves_verified` | 94/194 | **99/194** |
| reward levels | 152 | 154 |
| flags | no_static_board 1, short_board_window 16, no_post_reward_still 5, reward_anim_uncertain 14, tutorial_overlay 2, retry_attempt 3 | no_static_board **0**, short_board_window 14, no_post_reward_still 5, reward_anim_uncertain 14, tutorial_overlay 2, retry_attempt 3 |
| `late_board_anchor` | - | 0 |
| mean confidence | 0.977 | 0.980 |
| min `first_move_t - board_appear_t` | 1.08 s | 1.33 s |

Only 7 levels moved by more than 0.2 s - exactly the 7 SPEC v2.6 outliers.  Everything else
moved by the 0.35-frame `PRECISE_BIAS` (~6 ms) and nothing else.

### Independent audit (`scratchpad/v26/audit2.py`)

OCRs the counter just after the header anchor to get the level's starting value, then OCRs
the frame that `ffmpeg -ss board_t` actually returns.  This uses none of the detector's own
bitmap logic.

```
old   agree 112   DISAGREE 16   unreadable 66
new   agree 123   DISAGREE  4   unreadable 67
```
All 4 remaining "disagreements" are audit-side OCR failures, not detector errors - the
audit's `moves_plate()` merges two cream plates on the dark-red-banner UI era and reads
"271".  Checked frame by frame: `guiinjQLYvg` 9005 / 9018 / 9023 and `lo4xXqDlZGM` 6013 all
have board_t showing the correct starting value.  So on every level the audit could read,
the new output is correct: **127/127**.

### Per-level evidence for the 7 outliers

Frame-exact, from `scratchpad/v26/v<level>.png` (columns: anchor | reward | board_t |
first_move | the old board_t).

```
level                 board_appear_t     board_t (Moves)   first_move_t (Moves)   old board_t (Moves)
RmoqWHCPQx0 L3520     1488.750 (20)      1490.417 (20)     1490.500 (19)          1511.073 (18)  2 moves late
guiinjQLYvg L9001        4.833 (24)        12.981 (24)       13.003 (23)            27.353 (21)  3 moves late
0QfejcKagvk L11501      45.667 (22)        47.542 (22)       47.564 (21)            61.898 (21)  1 move  late
guiinjQLYvg L9030     2642.667 (23)      2644.547 (23)     2644.570 (22)          2658.136 (21)  2 moves late
guiinjQLYvg L9010      647.583 (25)       650.331 (25)      650.354 (24)           662.869 (24)  1 move  late
guiinjQLYvg L9003      113.917 (28)       117.864 (28)      117.886 (27)           124.119 (26)  2 moves late
guiinjQLYvg L9011      760.250 (21)       766.331 (21)      766.354 (20)           768.750 (20)  1 move  late
```

SPEC v2.6's acceptance criteria for L9011: `board_appear_t` 760.250 (asked ~760.25),
`reward_anim.present` true spanning 761.92-764.58 (asked ~762.25-764.00; `end_t` carries
through the trailing cascade by design), `first_move_t` 766.354 (asked ~766.60; my own
frame-by-frame reading of the Moves plate puts it at 766.35), `board_t` 766.331 which is
in 764.00-766.35 and reads **21**.

### Throughput

Standalone, single process:
```
lo4xXqDlZGM  41.3 s for 1910 s of video   46.3x realtime   (notes baseline 48.7x)
FJ6PY-6zAf8  88.0 s for 4012 s of video   45.6x realtime   (notes baseline 48.0x)
```
About 5 % slower, and the box had unrelated load (load average 13-16) during the
measurement, so this is an upper bound.  Well inside the 10 % budget.  Nothing was added to
the per-frame hot path except one `dict.get` - the added work is O(frames) array means and
a bounded XOR search, both negligible against decoding.

## 8. Known limitations / not fixed

- `first_move_t` (and `board_t`) are computed as `ss + i/fps` inside a single decode, and
  ffmpeg's `-ss` lands on the first frame at or after `ss`, so the named timestamp can be
  up to one frame (~17 ms) EARLIER than the frame it describes.  For `board_t` this is
  harmless (earlier is safe) and `PRECISE_BIAS` removes the dangerous direction; for
  `first_move_t` it means `ffmpeg -ss first_move_t` occasionally returns the last pre-move
  frame instead of the first post-move one (example: `guiinjQLYvg` L9015, reported
  1257.200, true 1257.208).  Only affects a UI marker, so it was left alone.
- The Moves reference needs ~0.4 s of a settled counter after the header appears.  Across
  the pilot the smallest `first_move_t - board_appear_t` is 1.33 s, so there is ~0.9 s of
  margin after the ~0.5 s header slide - but a player who moves within ~0.9 s of the board
  appearing could still poison the reference.  None exists in the pilot.
- The audit could not read the counter on 67/194 levels (`ocr_moves` is tuned for precision
  and returns None rather than guess), so those levels are verified only by the detector's
  own bitmap logic plus the visual sheets in `scratchpad/v26/verify/`.
- `out/detect/*.json` was NOT regenerated - the new output lives in
  `scratchpad/v26/out/`.  The pipeline needs a re-run to propagate `board_t` into
  `out/levels/*/board.jpg`, `window.mp4` and the manifest.
