# Reward / booster animation — investigation notes (SPEC v2.1/v2.2)

Handoff document. Everything below was measured on the 8 pilot videos in `work/`
(194 levels total). Written so it can be picked up cold.

---

## 1. What the animation actually is

At the start of a level, a **deep-crimson dome-shaped hat with a gold band and a green
gem on top** flies onto the board from off-screen (usually from the left or bottom),
bounces/hops around the board 2-4 times, and on each landing detonates, converting board
pieces into power-ups. Then it vanishes in a final burst and the resulting cascade runs
out. The Moves counter does NOT change during any of this.

It is a **pre-selected booster**, not a level reward — the player buys/selects it in the
"Select Boosters" row of the Level N dialog. That is why it is absent from the oldest
recording (the player had none) and near-universal in the newer ones.

Visually unmistakable: nothing else on the board is that colour and that size. In HSV
(OpenCV ranges) the dome is **hue 162-179, sat >= 190, val 50-215** — a magenta-leaning
crimson well away from the red game pieces (hue 0-8). At 296x640 the dome's bounding box
is roughly 85-95 px wide and 65-90 px tall, i.e. ~0.30 x ~0.18 of the board band.

### Variants

**There is only ONE visual variant across all 8 videos and all UI eras.** I surveyed the
peak frame of the longest motion burst for all 194 levels
(`scratchpad/inv/survey.py`, sheets `survey_00.png` … `survey_09.png`) and every level
that has an animation shows the same crimson hat. No second object was found.

What *does* vary is how long it stays on screen — see §3. That is the only thing that
looks variant-like, and it varies **per recording**, not per level.

Label used in the JSON: `"variant": "royal_hat"`.

---

## 2. Frequency

Levels with the animation, by video (detector output, `stats.reward_levels`):

| video_id | levels | with reward | note |
|---|---|---|---|
| A9xLB2MsDNg | 2-30 (29) | **0/29** | 2021 UI era, no boosters at all |
| agxDN7ffBII | 161-185 (25) | 22/25 | |
| 0mwjjHHcmGI | 1511-1530 (20) | 19/20 | |
| RmoqWHCPQx0 | 3506-3520 (15) | 14/15 | |
| lo4xXqDlZGM | 5996-6015 (20) | 19/20 | |
| guiinjQLYvg | 9001-9030 (30) | 25/30 | |
| 0QfejcKagvk | 11501-11515 (15) | 14/15 | |
| FJ6PY-6zAf8 | 13461-13500 (40) | 39/40 | |
| **total** | **194** | **152 (78 %)** | **92 % of non-2021 levels** |

Era dependence is stark and binary: **zero** in the levels 2-30 recording, ~92 % in every
other recording. It is not a function of level number but of which recording session it is
(i.e. which boosters that player had).

An independent offline measurement (`scratchpad/inv/hatnovel.py`, a different code path
using a per-level reference frame instead of a temporal majority) found 155/194. The two
agree on 191/194: the detector misses 3 (`0QfejcKagvk/11501`, `FJ6PY-6zAf8/13462`,
`guiinjQLYvg/9001`) and finds 1 that the offline method missed (`lo4xXqDlZGM/6001`, which
I confirmed visually does have the hat). So recall is ~98 % relative to the reference.

**Known failure mode:** levels whose *backdrop* is the same crimson as the hat. Example
`FJ6PY-6zAf8` level 13462: the board band is ~16 % crimson all the time, the hat adds only
~3 %, and the background-subtraction step cancels it. Accepted — see §5, this does not
affect `board_t`.

---

## 3. Duration — does the fixed-duration hypothesis hold?

**It holds, strongly, but the constant is per-recording, not global.**

Measurement = time the crimson object is continuously on screen (bridging <=3 absent
frames), sampled at 20 fps, over all 154 levels where it was detectable
(`scratchpad/inv/hatnovel.json` + the aggregation in §8).

Distribution of on-screen duration over all levels:

```
2.2 s : 51 levels     2.3 s : 20      2.4 s : 1      2.5 s : 2
2.6 s : 49            2.9 s : 1       3.4 s : 21     3.8 s : 1
0.8-1.0 s : 7  (partial detections, not real durations)
```

Grouped by video — the striking result:

| video_id | level range | measured on-screen durations |
|---|---|---|
| 0mwjjHHcmGI | 1511-1530 | **2.6 s x 19** (100 %) |
| RmoqWHCPQx0 | 3506-3520 | **2.6 s x 14** (100 %) |
| lo4xXqDlZGM | 5996-6015 | 2.6 x 16, 2.5 x 2 |
| agxDN7ffBII | 161-185 | **3.4 s x 21**, 2.9 x 1 |
| FJ6PY-6zAf8 | 13461-13500 | 2.2 x 27, 2.3 x 9, (0.8/0.9/3.8 x 1 each) |
| guiinjQLYvg | 9001-9030 | 2.2 x 19, 2.3 x 4, 2.4 x 1, (0.8/1.0) |
| 0QfejcKagvk | 11501-11515 | 2.3 x 7, 2.2 x 5, 2.1 x 1, (0.8/1.0) |

So there are **three duration classes: ~2.25 s, ~2.60 s, ~3.40 s**, and within one
recording the duration is constant to within one 20 fps frame (spread p90-p10 = 0.08-0.30 s
for most videos). The 2.2 vs 2.3 split is pure sampling quantisation of the same value.

Verdict: the user's hypothesis **holds**. But because the constant differs between
recordings (presumably game version or booster tier — probably the number of hops), a
hardcoded global table would be wrong for 1/3 of the playlist. The detector therefore
*measures* per level and uses the **video's own median** as the table, snapped to the
nearest of `(2.25, 2.60, 3.40)` when within 0.25 s. Reported in
`stats.reward_object_s_median` / `stats.reward_object_s_spread`.

### Concrete per-level evidence (cite these, they were measured frame by frame)

Object on-screen span, then the full `reward_anim` the detector now emits
(`start_t` = object first seen, `end_t` = the trailing cascade has run out):

```
FJ6PY-6zAf8  L13461  object 14.85-17.10   reward_anim 14.917 -> 17.417  dur 2.500
                     board_appear 14.333, first_move 17.504   (user's hand measurement:
                     enters 14.90, ends 17.42, first move ~17.50 — exact match)
FJ6PY-6zAf8  L13463  reward_anim 181.750 -> 184.417  dur 2.667   first_move 185.004
FJ6PY-6zAf8  L13464  reward_anim 235.583 -> 238.250  dur 2.667   first_move 238.354
FJ6PY-6zAf8  L13465  reward_anim 284.833 -> 287.083  dur 2.250   first_move 287.171
FJ6PY-6zAf8  L13466  reward_anim 327.000 -> 329.667  dur 2.667   first_move 329.887
FJ6PY-6zAf8  L13468  reward_anim 499.167 -> 501.667  dur 2.500   first_move 501.754
FJ6PY-6zAf8  L13480  reward_anim 1712.833 -> 1715.083 dur 2.250  first_move 1715.137
FJ6PY-6zAf8  L13500  reward_anim 3657.667 -> 3660.170 dur 2.500  first_move 3660.203
RmoqWHCPQx0  L3506   object ~11.33-13.90 (2.6)  board_appear 10.73, first_move 15.383
lo4xXqDlZGM  L5996   object ~24.12-26.87 (2.6)  board_appear 23.52, first_move 27.417
guiinjQLYvg  L9002   object ~73.20-75.80 (2.2)  board_appear 73.15, first_move 78.400
0QfejcKagvk  L11504  object ~2.3   busy run 292.217-293.567, single still frame 293.617,
                     first_move 293.677  (measured at native 59.45 fps)
A9xLB2MsDNg  L2      NO animation. board_appear 5.92, settles 6.23, first_move 8.083
A9xLB2MsDNg  L7,9,11,17,21 …  NO animation anywhere in levels 2-30
```

Other timings worth keeping:
- The object enters **0.4-1.8 s after `board_appear_t`** (p5/p50/p95 = 0.40 / 1.17 / 1.80).
- Gap from the object vanishing to the first move: p0/p25/p50/p75/p100 =
  0.20 / 0.80 / 1.42 / 2.40 / 9.80 s. Only 6/154 levels have < 0.4 s.

---

## 4. The single most load-bearing measurement: when does the Moves counter change?

Measured at native frame rate on `0QfejcKagvk` L11504 (59.45 fps), see §8 for the command:

```
293.542  d1=1.45   board still finishing the cascade
293.592  d1=0.51   board settled (d1 0.24-0.89 from here on)
293.660  d1=0.38   <-- last frame before the counter changes
293.677  Moves bitmap changes (25 -> 24)
293.845  d1=7.35   the pieces finally start to swap
```

Two facts fall out, and they drive the whole design:

1. **The Moves counter decrements the instant the swipe registers — roughly 0.17 s BEFORE
   the board visibly moves.** So "last still frame before the counter change" is always
   also before the move's own animation. `board_t < first_move_t` is safe.
2. Across 187 levels with a still run, the gap between the end of the last still run and
   the counter change is **0.05 s for 176 of them** (p50 = p75 = p90 = 0.05 s). Only 11
   levels have a gap > 0.3 s. Players of these walkthrough videos buffer their swipe
   during the animation, so the move lands within a frame or two of the board settling.

Consequence: the settled window is often only **one or two source frames wide**. A 12 fps
refine grid literally cannot see it — hence the precision pass (§5).

---

## 5. Chosen approach for `board_t`, and what was rejected

### Chosen: anchor on the first move, walk backwards at native frame rate.

1. 12 fps refine pass as before -> `play_t`, `ready`, `board_appear_t`, the Moves
   reference bitmap, and a *coarse* first-move index.
2. **Precision pass**: re-decode `[coarse_move - 1.60 s, coarse_move + 0.45 s]` at the
   file's native fps, half resolution. Find the exact frame where the Moves bitmap first
   differs from the reference and stays different. Walk back up to 0.40 s for the last
   settled frame. That frame is `board_t`.
3. If no settled frame exists in those 0.40 s -> take the quietest frame of that window
   and flag `no_post_reward_still`.

Why this works without reasoning about the animation at all: the animation always ends
before the player can move, so "last settled frame before the move" is *by construction*
in the later of the two still windows. Verified: on all **152** levels with a detected
animation, `board_t > reward_anim.end_t`, gap p5/p50/p95 = 0.05 / 0.98 / 4.67 s.

Stillness test at native fps (thresholds measured, see §4):
`d(i, 1) < 1.00` **and** `d(i, ~50 ms) < 2.20`, on the mean |delta| of the board band.
Two scales are needed because the last of the sparkle decays slowly: a single 83 ms step
still reads ~1.8 on a board that is frame-to-frame static.

### Rejected alternatives

- **"Take the last still run before the move" on the 12 fps grid.** Fails on the 11 levels
  where the animation runs into the move: walking back on a coarse grid lands in the
  *pause between two hops* (L13461 -> 16.15 s, which is the old wrong answer 16.083).
  Also cannot see 1-frame still windows at all (§4).
- **Variant classifier + hardcoded duration table.** The duration really is quantised, but
  the constant is per-recording, so a global table is wrong for a third of the playlist.
  Kept only as a *fallback* for levels where the end is unobservable, using the video's own
  median. `duration_source` is `"measured"` or `"variant_table"` accordingly.
- **Detecting the object and skipping past it as the primary mechanism.** Fragile on
  crimson-backdrop levels (L13462) and unnecessary — the move anchor already dominates it.
  The detector still runs it, but only for reporting and for the no-move fallback.
- **Keeping `ACTION_DIFF`/`action_i` as a bound on `board_t`.** That bound is exactly what
  caused the v2.1 defect: the reward animation looks like "the player did something", so it
  clipped `board_t` to the *pre*-reward window. It is now only consulted after the reward
  animation has ended, and only on the no-first-move fallback path.

---

## 6. Levels with NO clean post-reward, pre-first-move frame

`no_post_reward_still`, 5 of 194. All get the quietest pre-move frame; ordering is never
violated.

```
FJ6PY-6zAf8  13461  board_t 17.470   first_move 17.504
FJ6PY-6zAf8  13465  board_t 287.154  first_move 287.171
FJ6PY-6zAf8  13480  board_t 1715.103 first_move 1715.137
FJ6PY-6zAf8  13500  board_t 3660.170 first_move 3660.203
0QfejcKagvk  11514  board_t 1248.381 first_move 1248.448
```

(The pre-fix offline scan found 11 candidates at 20 fps — `0QfejcKagvk` 11511/11513/11514,
`0mwjjHHcmGI` 1528, `FJ6PY-6zAf8` 13461/13465/13468/13477/13478/13480/13500. Six of those
turned out to have a 1-2 source-frame still window that only the native-rate pass can see.)

---

## 7. Implementation status in `src/detect.py`

**Done.**

- `_raw_stream(..., fps=None)` — native frame rate mode, no fps filter.
- `reward_mask()` / `reward_presence()` / `_longest_run()` — object detection. Background
  suppression is a **per-pixel temporal majority** over the scanned window (the hat is on
  screen for a minority of the window at any given pixel), dilated 7x7 and subtracted;
  this is what removes crimson backdrops without needing a reference frame.
- `precise_move()` — the native-rate precision pass (§5).
- `refine_window()` — now also returns `board_appear_t`, `first_move_t`, `reward`.
  - `board_appear_t`: bounded backward walk from `ready` (which is up to 0.6 s late
    because its texture threshold is a percentile of the whole window and later
    explosions inflate it). Reference = median sat/lit/tex over the 0.5 s from `ready`;
    accept while `sat >= 0.95x`, `lit >= 0.90x`, `tex >= 0.80x`; never walks back more
    than 3 s, never past `play_i`. On L13461 this gives 14.333 vs the user's 14.30.
  - **`_move_confirmed()`** — new guard. A candidate counter change is only believed if
    the following 2.5 s of drawn board frames keep reading something other than the
    reference (a real move is irreversible). This fixed 3 levels in `A9xLB2MsDNg`
    (8, 17, 21) where a tutorial dim flickers the header and faked a move; they had
    `no_static_board` before and are now clean.
- `consolidate_rewards()` — per-video median duration, `variant_table` fallback,
  `reward_anim_uncertain`, and normalisation to the exact v2.2 schema.
- `assign_levels()` — emits `board_appear_t`, `first_move_t`, `reward_anim`; confidence
  penalties for the two new flags.
- `detect()` — hard clamp `board_t < first_move_t` as a safety net; new stats keys
  `reward_levels`, `reward_object_s_median`, `reward_object_s_spread`,
  `no_post_reward_still`.
- `short_board_window` is now **adaptive**: it fires only when the settled run is shorter
  than `min(0.40 s, 0.60 x available)` where available = first_move - (reward end, or
  board_appear). Count over the pilot fell 43 -> 16, which is the point: on most levels
  the window genuinely is one frame wide and that is not a defect.

**Deliberately untouched** (per SPEC v2.5): everything tutorial-related. No
tutorial-specific branch exists; `tutorial_overlay` still fires on `A9xLB2MsDNg` levels
4 and 20 exactly as before, and those levels go through the identical v2.1 code path.

**Not mine / not started**: v2.3 `window.mp4` generation (pipeline.py), v2.4 UI scrubber,
manifest `window` block (build_index.py).

---

## 8. Commands

Python is always `/Users/tauseen.syed/Projects/rm-shots/.venv/bin/python`.

Run one video:
```
.venv/bin/python src/detect.py --video work/pilot_FJ6PY-6zAf8.mp4 \
  --meta '<blob from playlist.json>' --out /tmp/FJ6PY-6zAf8.json -v
```

Run the whole 8-video pilot, 3 concurrent (writes to `scratchpad/new/out/`):
```
/private/tmp/.../scratchpad/new/runall.sh
```

Visual verification sheets — one row per level, columns
`board_appear | reward start | reward end | board_t-0.35 | board_t | first_move | +0.3`:
```
.venv/bin/python /private/tmp/.../scratchpad/new/verify.py [video_id]
# writes verify/<vid>_NN.png, 8 levels per sheet
```

Labelled contact strip of any window:
```
.venv/bin/python /private/tmp/.../scratchpad/inv/strip.py <video> <t0> <dur> <out.png> [fps] [cols]
```

Native-frame-rate diff/Moves profile around a timestamp (this is how §4 was measured):
decode with `D._raw_stream(path, 296, 640, None, ss, dur)`, then per frame
`mean|board_i - board_{i-k}|` for k in 1,3,5 and `(moves_bits ^ ref).mean()`.

Offline investigation scripts (all in `scratchpad/inv/`, kept for re-derivation):
`features.py` (20 fps motion/moves/texture timeline per level -> `feat/*.npz`),
`analyze.py` (still/busy run structure -> `analysis.json`),
`hatfeat.py` (raw crimson blob stats -> `hat/*.npz`),
`hatnovel.py` (object presence vs a pre-move reference frame -> `hatnovel.json`),
`survey.py` (194-level contact sheet of the animation peak frame).

---

## 9. Validation result (8-video pilot, 194 levels)

- 194/194 levels found, identical level set to the pre-change run.
- **0** violations of `board_t < first_move_t`; **0** null `board_t`.
- `board_t` moved **later on 64 levels**, earlier on **0**.
- On all 152 reward levels `board_t > reward_anim.end_t`.
- `moves_start` OCR cross-check (`moves_verified`): 94/194 vs 95/194 before — unchanged.
- Flags: `short_board_window` 16 (was 43), `no_static_board` 1 (was 4),
  `no_post_reward_still` 5, `reward_anim_uncertain` 14, `tutorial_overlay` 2 (unchanged),
  `retry_attempt` 3.
- Speed: 48.0x realtime standalone on `FJ6PY-6zAf8` (4012 s video in 83.5 s), 48.7x on
  `lo4xXqDlZGM`; 18.7-29.2x per worker with 3 running concurrently. No regression.
  (A later run showed 8-9x per worker — that was contention from other work on the box,
  not the detector; re-measure standalone if in doubt.)

Canonical worked example, matching the user's hand measurement in SPEC v2.1 exactly:

```
FJ6PY-6zAf8 / level 13461
  play_t          13.750
  board_appear_t  14.333   (user: "board settled and still from 14.30")
  reward_anim     14.917 -> 17.417, royal_hat, 2.500 s, measured
                           (user: "enters 14.90 ... finishes ~17.42")
  board_t         17.470   (was 16.083 — mid-animation, the v2.1 defect)
  first_move_t    17.504   (user: "~17.50, Moves 25 -> 24")
  flags           no_post_reward_still, reward_anim_uncertain, short_board_window
```

Pre-change `out/detect/*.json` are backed up at
`/private/tmp/claude-502/-Users-tauseen-syed/6444f7e0-08ed-407d-b56f-2beda68869ed/scratchpad/backup_out_detect/`
(the project also has `out/detect_v1_backup/`). `out/detect/` itself is being regenerated
with the new detector by the pipeline work, so do not hand-edit it.
