# Royal Match level screenshot extractor — component contract

Goal: for every level in the 705-video playlist, produce two 720p screenshots:
1. **play** — the "Level N" pre-game dialog (Goal + Select Boosters + green Play button)
2. **board** — the game board in its settled state, on the last frame **before the player's first move**

Scope: 704 parsed videos, ~13,088 distinct levels, 358h of 592x1280 @ ~59.94fps video.

## Layout

```
rm-shots/
  .venv/                  python env (cv2, numpy, pytesseract)
  playlist.json           {videos:[{index,id,duration,title,level_start,level_end,level_count}], unparsed:[]}
  src/fetch.py            download one video to work/  (Component B)
  src/detect.py           detect levels in one video   (Component A)
  src/pipeline.py         orchestrate fetch->detect->extract->delete (Component B)
  src/build_index.py      manifest.json for the UI      (Component C)
  ui/index.html           browser UI                    (Component C)
  work/                   transient video files, deleted after processing
  out/detect/<vid>.json   per-video detection result
  out/levels/<NNNNN>/play.jpg, board.jpg
  out/manifest.json
  logs/
```

Python is always `/Users/tauseen.syed/Projects/rm-shots/.venv/bin/python`.
Binaries: `/opt/homebrew/bin/{ffmpeg,ffprobe,yt-dlp,tesseract}`.

## Video structure (verified on pilot footage)

Each level is one cycle:
`map/castle screen -> "Level N" play dialog -> board slides in & cascades settle -> first move -> ... -> win ("Continue") or fail -> map`

Key visual facts, normalized to frame height (592x1280 source):
- **Play dialog**: blue rounded panel centered horizontally, large saturated **green Play button**
  (~x 0.23-0.79, ~y 0.67-0.78), red circular X at the panel's top-right. Panel height VARIES with
  the number of goal items, so the "Level N" title's y position shifts — do NOT hardcode the title box;
  anchor off the detected panel/button.
- **Board screen**: header strip across the top ~0.0-0.19 with `Target` (left), king avatar (center),
  `Moves` (right). Board occupies roughly y 0.22-0.80.
- **Moves counter** decrements on each move. The target `board` frame is the **last frame where Moves
  still reads its initial value** and the board is static.
- Other screens to reject: castle/map, "Continue" win dialog, "Castle" task dialog, "ROYAL MATCH!" splash.
- Early levels overlay **tutorial tooltips** on the board. These are legitimately part of the
  pre-first-move state — keep the frame, but set flag `tutorial_overlay` if detected.
- The player **can fail and retry** a level, producing multiple play dialogs for the same level.
  Dedupe to one entry per level (prefer the first fully-successful attempt); mark extras `retry_attempt`.

## Level numbering

Two independent sources, cross-checked:
- **OCR** the "Level N" title in the play dialog (primary). Font is a bold stylized outline face;
  tesseract needs preprocessing (upscale, threshold on the white glyph core, digit whitelist).
- **Sequence** — levels appear in ascending order and `playlist.json` gives `level_start`/`level_end`.
  If K deduped dialogs are found and K == level_count, positional assignment is authoritative.

Disagreement between the two => still emit the level, but add flag `ocr_sequence_mismatch` and lower
confidence. Never silently drop a level.

## Component A — `src/detect.py` (the hard part)

CLI: `detect.py --video work/pilot_<id>.mp4 --meta '<json blob from playlist.json>' --out out/detect/<id>.json [--debug-dir DIR]`

Writes:
```json
{ "video_id":"A9xLB2MsDNg", "title":"...", "level_start":2, "level_end":30,
  "fps":59.94, "width":592, "height":1280, "duration":2521.4,
  "segments":[
    { "level":2, "level_source":"ocr|sequence|both",
      "ocr_text":"Level 2", "ocr_conf":0.91,
      "play_t":12.53,          // timestamp, seconds — dialog fully shown & static
      "board_t":18.22,         // timestamp — last static frame before first move
      "moves_start":27,        // OCR of Moves counter, or null
      "attempt":1,
      "confidence":0.0..1.0,
      "flags":[] }
  ],
  "stats":{"expected_levels":29,"found_levels":29,"flagged":0,"elapsed_s":123.4} }
```

Flag vocabulary (use exactly these): `ocr_failed`, `ocr_sequence_mismatch`, `no_static_board`,
`short_board_window`, `retry_attempt`, `count_mismatch`, `tutorial_overlay`, `low_static_confidence`.

Algorithm guidance (you own the details, but this is the validated shape):
1. **Cheap pass** — decode the whole video at ~4fps scaled small (e.g. 148x320) via a single ffmpeg
   pipe to rawvideo on stdout. Do NOT write per-frame PNGs; 358h of video makes that ruinous.
   Classify every sampled frame: `PLAY_DIALOG | BOARD | OTHER` using colour-mask ratios in
   normalized regions (green-button mask, header `Target`/`Moves` strip, red X).
2. **Refine pass** — for each detected play->board transition, re-decode just that window
   (`ffmpeg -ss ... -t ...`) at full fps and full resolution.
   - `play_t`: last frame where the dialog is present and static (just before the Play tap).
   - `board_t`: after the dialog vanishes, find the first run of >=0.4s where the frame-diff
     restricted to the **board region only** (exclude the header — the king avatar idles, and
     the Moves digits change) stays under threshold. Take the **last** frame of that run.
     Fall back to a fixed offset + `no_static_board` flag if no run qualifies.
3. Cross-check OCR vs sequence; set `confidence` and `flags`.

Performance target: must sustain well under realtime across 358h. Budget roughly <= 90s of wall
clock per 30min video on this machine (10 cores). The cheap pass dominates — keep it in one
ffmpeg process, one numpy buffer, no disk churn.

## Component B — `src/fetch.py` + `src/pipeline.py`

- `fetch.py`: download a single video, video-stream only (no audio), 720p:
  `-f "298/bv*[height<=720][protocol^=https]/bv*[height<=720]"`. Retries with backoff, resumable,
  `--no-part`. Treat the 705-video run as rate-limit-sensitive: modest concurrency (2-3),
  a short randomized sleep between videos, and graceful handling of unavailable/private videos.
- `pipeline.py`: for each video in playlist.json — fetch -> detect -> extract the two frames at the
  detected timestamps with `ffmpeg -ss <t> -i <vid> -frames:v 1 -q:v 2 out/levels/<NNNNN>/{play,board}.jpg`
  -> **delete the video file** -> checkpoint. Must be **resumable**: skip videos whose
  `out/detect/<id>.json` already exists. Peak disk stays small; never let downloaded video accumulate.
  Level dir name is the level number zero-padded to 5 (`out/levels/00002/`).
  On overlapping level claims between videos, first writer wins unless the new one has higher confidence.

## Component C — `src/build_index.py` + `ui/index.html`

- `build_index.py`: walk `out/detect/*.json` + `out/levels/`, emit `out/manifest.json`:
  `{generated, count, levels:[{level, video_id, video_title, youtube_url, play, board, confidence, flags, moves_start}]}`
  `youtube_url` should deep-link the timestamp: `https://youtu.be/<id>?t=<int(play_t)>`.
- `ui/index.html`: single self-contained file, no build step, no CDN dependency. Opened via a
  tiny local static server (`python -m http.server` from `out/`, with ui copied/symlinked in).
  Requirements: grid of levels; click to view play + board side by side; jump-to-level input;
  prev/next keyboard nav (arrow keys); filter to show only flagged/low-confidence levels;
  show the flags and a link back to the source video at the right timestamp.
  Must stay responsive with ~13,000 levels x 2 images — virtualize the grid and lazy-load images.

---

# SPEC v2 — post-pilot revisions

The 8-video pilot passed (194/194 levels, 8/8 exact sequence match). Two changes follow from
the user's review of the real output.

## v2.1 — `board_t` must be AFTER the reward/booster animation completes

**The defect.** On many levels a reward/booster object flies onto the board at level start and
distributes items before the player moves. The current detector picks the first sufficiently-still
run, which can land in the MIDDLE of that animation.

Worked example, level 13461 (`pilot_FJ6PY-6zAf8.mp4`), measured frame by frame:

| t (s) | state |
|---|---|
| 14.30-14.85 | board settled and still, Moves 25 — but reward has NOT yet entered |
| 14.90 | magenta reward object flies in from the left with a flame trail |
| **16.083** | **current `board_t` — mid-animation, object visibly crossing the board (WRONG)** |
| 15.0-17.4 | object bounces around distributing items; Moves still 25 throughout |
| ~17.50 | Moves 25 -> 24: the first move |

**Required behaviour.** `board_t` must be the last still frame with the board fully settled AFTER
the reward has finished distributing, and still strictly BEFORE the first move. Note there are
often TWO still windows (before the reward enters, and after it finishes); the correct one is the
LATER one. The user explicitly wants the post-reward state, because that is the board they would
actually be playing.

**Investigate first, then implement.** The user's hypothesis is that this animation has a fixed
duration, or a small number of variants each with a fixed duration. Test that empirically across
levels and eras before choosing an approach. Characterise: how often it occurs, whether it is a
pre-selected booster vs a reward, how many visual variants exist, and their durations. Prefer a
detected end-of-animation over a hardcoded constant, but if durations really are fixed per variant,
a variant classifier plus known duration is acceptable and more robust than a stillness heuristic.

**Hard constraint.** `board_t < first_move_t` always. Never return a frame at or after the first
move. If no still post-reward window exists before the first move (the animation may run right up
to it), pick the latest pre-first-move frame where the board is maximally settled and flag it
`no_post_reward_still`. Correctness of ordering beats stillness.

Levels with no reward animation keep the current behaviour.

## v2.2 — new required segment fields

Add to every segment in `out/detect/<vid>.json`:

```json
"board_appear_t": 14.30,        // board first fully rendered (post dialog/slide-in)
"first_move_t": 17.50,          // first move detected; null if never found
"reward_anim": {                 // null when no reward animation occurs
   "present": true,
   "start_t": 14.90,
   "end_t": 17.42,
   "variant": "flying_object",   // your classification label
   "duration": 2.52,
   "duration_source": "measured|variant_table"
}
```

`board_t` semantics change as described in v2.1. Existing fields keep their meaning.
New flags: `no_post_reward_still`, `reward_anim_uncertain`.

## v2.3 — per-level verification clip (`window.mp4`)

So the user can confirm the chosen frame is right, every level gets a clip spanning the whole
decision window.

- Path: `out/levels/<NNNNN>/window.mp4`
- Range: from `board_appear_t` to `first_move_t + 1.5s` (so the first move is visible INSIDE the
  clip, proving `board_t` precedes it). If `first_move_t` is null, use `board_t + 4s`.
- Encode: `-vf fps=10 -c:v libx264 -crf 30 -preset veryfast -pix_fmt yuv420p -movflags +faststart`
  at FULL source resolution. Measured: ~242KB and ~0.17s to encode per level; ~3.0GB over 13,088
  levels. Exactly 10fps is REQUIRED so the UI can step frames as `currentTime += 0.1`.
- Manifest gains per level:
  `"window": {"file":"levels/13461/window.mp4","fps":10,"start_t":14.30,"duration":4.70,
              "board_offset_s":3.05,"first_move_offset_s":3.20}`
  Offsets are relative to the clip start, so the UI can mark the chosen frame and the first move
  without re-deriving timings.

## v2.4 — UI: double-click a level to scrub the window

Double-clicking any level opens a frame-by-frame viewer over that level's `window.mp4`:
- Step forward/back one frame (0.1s) with buttons and left/right arrow keys; play/pause.
- A timeline marking **the chosen `board_t` frame** and **the first move**, so it is immediately
  obvious whether the capture landed correctly.
- Jump-to-chosen-frame control, and a visible indication when the current frame IS the chosen one.
- Must work for flagged and unflagged levels alike; this is the user's primary tool for judging
  extraction quality, so clarity matters more than polish.

## v2.5 — tutorials: keep exactly as-is, no special treatment

Clarification from the user: "don't leave tutorials out. Just don't give them any special
treatment. They work as things are right now."

So, precisely:
- Tutorial levels are **still captured and still appear in the output** like any other level.
- The existing `tutorial_overlay` flag stays and keeps firing as it does today.
- The v2.1 reward-animation logic applies to tutorial levels **uniformly**, the same as every
  other level — no tutorial-specific branch, no exemption, no extra tuning.
- Do NOT add tutorial-specific handling, and do NOT remove or weaken what already exists.
- The slightly-dimmed tutorial board frames are acceptable as they are. Don't spend effort
  "improving" them, and don't skip, exclude, or downrank those levels.

In short: leave tutorial behaviour untouched and let the general logic cover them.

---

# SPEC v2.6 — `board_appear_t` / `first_move_t` can land AFTER the real first move

User report: "Level 9011 suggests that the video is starting a bit too late. I think in this case
the video is after the first move was already made. Fix that at scale."

Confirmed. This is worse than a late clip start — on affected levels the detector **misses the real
first move entirely and locks onto the SECOND move**, so `board_t` is a post-first-move frame.
That is a direct violation of the product's core promise.

## Worked example — `guiinjQLYvg` level 9011, measured frame by frame

| t (s) | ground truth (from pixels) | detector emitted |
|---|---|---|
| 759.25-759.75 | "Level 9011" play dialog visible | `play_t` 759.833 — OK |
| **760.25** | **board appears, Moves = 21** | — |
| 762.25-764.00 | crimson royal_hat animation | `reward_anim: null` — MISSED |
| 764.00-766.50 | board settled, Moves still 21 | — |
| **~766.60** | **FIRST MOVE — Moves 21 -> 20** | — missed entirely |
| 767.00 | already post-first-move | `board_appear_t` 767.0 — WRONG |
| 768.75 | post-first-move | `board_t` 768.75 — WRONG |
| ~774.17 | Moves 20 -> 19 (the SECOND move) | `first_move_t` 774.167 — WRONG |

## Scale of the problem

`play_t -> board_appear_t` gap across the 194-level pilot: p50 0.75s, p75 1.33s, p95 1.75s, but
p99 18.00s and p100 21.58s. It is a clean outlier signature, not a gradual drift.

7/194 levels (3.6%) exceed 4.0s — extrapolating to ~470 levels across the full 13,088:

```
RmoqWHCPQx0 L3520   21.58s     guiinjQLYvg L9003    7.42s
guiinjQLYvg L9001   18.00s     guiinjQLYvg L9011    7.17s
guiinjQLYvg L9030   13.83s     guiinjQLYvg L9010    6.83s
0QfejcKagvk L11501   8.08s
```

## Root cause

`board_appear_t` is derived by walking backwards from `ready`, which is defined by saturation /
brightness / Laplacian-texture thresholds on the board band. On levels that open with a busy
sequence (reward animation plus a large cascade), those thresholds are only satisfied LATE — after
the player has already moved. Two things then follow:
1. The **Moves reference bitmap is sampled after the first move**, so the detector's notion of the
   initial Moves value is already decremented (21 read as 20).
2. `first_move_t` is therefore the first change *from the wrong reference* — i.e. the second move.

The backward walk is also bounded (<=3s), so it cannot recover a 7s error.

## Required fix

**Anchor on the header, not on board texture.** The `Target` / king-avatar / `Moves` header strip
renders the instant the board screen appears and is present and stable regardless of how busy the
board is. It is a far more reliable "the level has started" signal than board texture.

1. `board_appear_t` := the first frame after `play_t` where the board-screen HEADER is present
   (and stays present). Do not derive it from board stillness/texture.
2. Sample the **Moves reference bitmap at that first header frame**, not later. This is the single
   most important change — a reference taken after the first move poisons everything downstream.
3. `first_move_t` := the first confirmed, irreversible change from that reference (keep the existing
   `_move_confirmed()` guard).
4. `board_t` keeps its v2.1 definition (last settled frame before `first_move_t`, after the reward
   animation) — it becomes correct automatically once the anchor and reference are right.

**Sanity guard, required:** if `board_appear_t - play_t` exceeds ~3s (p95 is 1.75s, so this is a
genuine anomaly), treat it as a detection failure: re-derive from the header signal, and if it still
exceeds the bound, emit the level with flag `late_board_anchor` and reduced confidence. A silently
wrong timestamp is far worse than a flagged one.

New flag: `late_board_anchor`.

## Also worth fixing while here

`moves_verified` is false on 100/194 levels — for those there is no independent confirmation that
`board_t` precedes the first move. A correctly-sampled reference bitmap should raise this materially.
Report the before/after number; it is the best single proxy for whether the core promise holds.

## Acceptance criteria

- L9011 specifically: `board_appear_t` ~= 760.25, `reward_anim.present` = true spanning ~762.25-764.00,
  `first_move_t` ~= 766.60, `board_t` in 764.00-766.60 with Moves reading 21.
- All 7 listed outlier levels re-checked individually **by viewing frames**.
- Across the pilot, no level has `board_appear_t - play_t` > 3s without the `late_board_anchor` flag.
- Still 194/194 levels, 8/8 exact sequence match, 0 `board_t >= first_move_t` violations.
- No throughput regression beyond ~10%.

---

# SPEC v2.7 — inline frame timeline in the detail view

User request: "when I press on a level screenshot, I see the two page as it currently is, but the
timeline is shown at the bottom too and I can just navigate frames from there instead of having to
navigate to a third page to view the frame by frame."

Today a single click opens the play+board detail view, and frame stepping lives in a SEPARATE
full-screen scrubber reached by double-click. That is one navigation step too many. Frame stepping
should be available directly in the detail view.

## Required

**Single click on a level** opens the detail view as it is today — the **play screenshot and the
board screenshot side by side** — PLUS a frame timeline and transport controls docked at the
**bottom of that same view**. No extra navigation.

- The **play screenshot pane stays as-is** (a static image; the play dialog is not part of the
  decision window).
- The **board pane becomes scrubbable in place**: stepping frames updates the board pane to show
  that frame of `window.mp4`. It must remain visually obvious which frame is currently displayed
  and how it relates to the saved `board.jpg`.
- When the view first opens, the board pane must show **the chosen frame** (`board_offset_s`),
  i.e. exactly what `board.jpg` captured — so the default state is unchanged from today.
- Docked timeline carries the same markers as the existing scrubber: **chosen frame** and
  **first move**, visually distinct, plus the frame counter (`frame 31 / 47 · 3.10s / 4.70s`).
- Transport: step back / step forward one frame, play/pause, and a "back to chosen frame" control.
  Clicking anywhere on the timeline seeks.
- An unmistakable indicator when the displayed frame IS the chosen frame, and a clear "modified"
  state when it is not, so the user never confuses a scrubbed frame for the saved screenshot.

## Keyboard — resolve the existing conflict explicitly

`Left`/`Right` currently move to the previous/next LEVEL in the detail view. Frame stepping is now
the more frequent action, so:
- `Left` / `Right`  -> step one frame back / forward
- `Shift+Left` / `Shift+Right`  -> previous / next level
- `Space` -> play/pause,  `Escape` -> close
Show these hints in the detail view so the change is discoverable rather than surprising.

## Keep working

- Levels with no `window` (no clip) must still show the normal two-image detail view, with the
  timeline area either hidden or clearly disabled — never broken.
- The existing full-screen scrubber may stay (it is useful for a larger view), but it is no longer
  the only way to step frames. Double-click keeping its current behaviour is fine.
- Virtualized grid performance must not regress. The clip is still lazy-loaded: set `<video src>`
  only when a detail view is actually open, and clear it on close.
- `#L<level>` deep-linking, the flagged-only filter, density control and board/play thumbnail
  toggle all keep working exactly as now.

## Note on the server

`window.mp4` seeking REQUIRES HTTP Range support. `serve.sh` now uses `src/serve_range.py` for this;
plain `python -m http.server` returns 200 instead of 206 and makes every clip non-seekable, which
silently breaks frame stepping. Do not reintroduce `python -m http.server`, and verify against the
real `serve.sh`.

---

# SPEC v2.8 — the "chosen frame" marker is off by one

User report: "I think the chosen call out is offset by 1. It shows chosen on one frame after the
frame that is actually chosen."

Confirmed and measured. I compared `board.jpg` pixel-wise against every nearby clip frame for all
194 pilot levels, and found which clip frame ACTUALLY matches the saved screenshot:

```
UI currently uses Math.round(board_offset_s / 0.1):
   +0 (correct) :  59 levels (30.4%)
   +1 (late)    : 127 levels (65.5%)   <-- the user's complaint
   +2 / +3      :   8 levels ( 4.1%)

Using Math.floor instead:
   -1 :   2 (1.0%)    +0 : 141 (72.7%)    +1 : 47 (24.2%)    +2/+3 : 4 (2.0%)
```

So `floor` is much better than `round` but **still wrong on ~24%**. No timestamp formula can be
exact, because:
- `board.jpg` is extracted from the SOURCE at `board_t`, at the source's native ~59fps precision.
- `window.mp4` is resampled to exactly 10fps, so its frame grid lands on 0.1s boundaries that do
  not generally contain `board_t`.
- Which clip frame "contains" `board_t` depends on the fps filter's phase, which varies per video.

Additional finding: **0 of 194 clip frames are a near-exact pixel match** for their `board.jpg`
(best-match mean abs diff is typically 3-5). The closest clip frame can be up to 50ms away from
`board_t`, which is 2-3 source frames.

## Required fix — store the index, don't derive it

Compute the chosen frame index EMPIRICALLY at clip-cut time and put it in the manifest. The UI then
uses a stored integer instead of re-deriving it from a float.

1. **`src/pipeline.py`** — after cutting `window.mp4` and extracting `board.jpg` for a level,
   determine which clip frame actually corresponds to `board.jpg`:
   decode the clip frames in a small window around `floor(board_offset_s/0.1)` (e.g. +/-4), compare
   each to `board.jpg` (mean absolute difference, resizing if dimensions differ), and take the
   argmin. Cost is ~7 small-frame decodes per level (tens of ms); acceptable at 13,088 levels, but
   keep it inside the existing per-level lock and batched flow.
2. Emit that integer as **`board_frame_idx`**, plus **`first_move_frame_idx`** :=
   `ceil((first_move_t - start_t)/0.1)` — the first clip frame at or after the move (semantically
   "the move has happened by this frame"). Null `first_move_t` => null.
3. **`src/build_index.py`** — include both in the manifest `window` object:
   `{file, fps, start_t, duration, board_offset_s, first_move_offset_s, board_frame_idx, first_move_frame_idx}`
4. **`ui/index.html`** — use `window.board_frame_idx` / `window.first_move_frame_idx` directly when
   present for BOTH the timeline markers and the "is this the chosen frame" badge. Fall back to
   `Math.floor(offset/0.1)` only when the fields are absent (older manifests). Keep comparing frame
   identity by integer index, never by time distance.

## Acceptance

- Re-run the pixel-comparison audit across the pilot: `board_frame_idx` must equal the
  best-matching clip frame for **>=99%** of levels (ideally 100%).
- Opening a level's detail view lands on that frame, and the badge reads "chosen frame" there and
  nowhere else.
- The first-move marker sits at or after the real move, never before it.

---

# SPEC v2.9 — levels silently dropped when OCR fails

Found during the full 704-video run. Every level the pipeline captures is correct, but ~0.3% of
levels are **silently absent** — the exact failure mode the design forbids ("never silently drop a
level").

## Evidence (353 unseen videos processed at time of writing)

331/353 videos match their title's level range exactly. The 22 that don't:

```
3LNsGnhANQ4  claims 1046-1060  got 1046-1050, 1052-1060   missing 1051  dropped_out_of_range=1
sj88NkM1cbk  claims 1091-1105  got 1091-1100, 1102-1105   missing 1101  dropped_out_of_range=1
JRx5LCZtQxM  claims  421-435   missing 421 (the FIRST level)
nDyxbLc7mOo  claims 3966-3980  missing 3980 (the LAST level)
```

Full list with per-video stats is in `AFFECTED_VIDEOS.json`.

**Mechanism.** A play dialog IS detected at the right moment, but its OCR'd number reads outside the
video's expected range, so the segment is discarded (`dropped_out_of_range`) — or it is rejected as
not-a-level (`dropped_not_level`). Because the dialog count then disagrees with the title,
`positional_assignment` is disabled, leaving pure OCR with no fallback. One bad OCR = one vanished
level. Projected impact: **~41 levels across the full archive (~0.3%)**.

## Required fix

**A detected dialog must never be discarded merely because its OCR is unusable.** Recover the level
number from chronological position instead.

1. **Positional interpolation.** Dialogs occur in strictly ascending level order. If a dialog sits
   between a confidently-identified level `N` and `N+2`, it is `N+1`. Generalise: solve the
   assignment from the ordered dialog sequence plus whatever OCR readings are trustworthy. A dropped
   dialog flanked by known neighbours is unambiguous.
2. **Truncated first/last levels.** A video may open mid-level (dialog cut off) or end mid-level.
   Emit these from sequence, flagged, rather than dropping them.
3. Levels recovered this way get flag `level_from_position` and reduced confidence. Existing flags
   `ocr_failed` / `ocr_sequence_mismatch` keep their meaning.

## Do NOT force agreement with a wrong title

`N_ApgMCPdDk` is titled "Level 1551-1751" — 201 levels in a 32.4-minute video (9.7s/level, against a
playlist median of 98.2s). OCR read **1551-1571, perfectly sequential**, at 92.7s/level. **The title
is a typo; the detector is right.** It is the only such title in all 704.

So: when OCR is strongly self-consistent and sequential but the title implies an implausible level
density, **trust the detection**, flag `count_mismatch`, and do not fabricate levels to fill the
title's range. Sanity bound: a level takes ~98s on average; anything under ~25s/level means the
title is wrong, not the video.

## Hard constraint — the live run

`src/detect.py` is **in active use by a running pipeline** processing the remaining videos. Editing
it mid-run would feed partially-written code to hundreds of videos.

**Develop the fix in `src/detect_v3.py` (a copy). Do NOT modify `src/detect.py`.** It will be
swapped in by the operator after the run completes, and the ~22 affected videos reprocessed by
deleting their `out/detect/<id>.json` checkpoints and re-running the pipeline.

## Acceptance

- All 22 videos in `AFFECTED_VIDEOS.json` yield their full expected level set — except
  `N_ApgMCPdDk`, which must yield 1551-1571 and NOT 201 levels.
- **No regression**: the 8 pilot videos still give 194/194 with 8/8 exact sequence match,
  0 `board_t >= first_move_t` violations, and `board_frame_idx` unaffected.
- Re-checking a sample of already-correct videos must not change their output.
- Throughput regression under ~10%.

---

# SPEC v3.0 — whole UI era yields ZERO levels (event banner occludes the title)

Found during the full run. **18 consecutive videos covering levels 6926-7270 produced ZERO
levels — 291 levels lost and growing.** The band is contiguous and the pipeline was still
inside it. This is the single largest defect in the project.

## Signature

```
-eNyjlfSF2o 6926-6945  dialogs=24  dropped_not_level=20
AELrl4ZeLlI 6946-6970  dialogs=28  dropped_not_level=25
...
7vqy9kevgdk 7264-7270  dialogs=7   dropped_not_level=7
```

Full list in `ZERO_SEGMENT_VIDEOS.json`. The detector **finds** every dialog, then rejects
every one of them via the fuzzy "does the title read *Level*" gate.

## Root cause (diagnosed visually)

A diagnostic frame from `R6JUq6g0xXg` at t=150.2 (level 7212) shows the dialog is perfectly
normal and the title "Level 7212" is large and legible — BUT a **"Super Duke!" event banner
is rendered directly above the dialog, overlapping its top edge**, and a "Lightning Rush"
leaderboard panel covers the bottom.

If the title crop is anchored off the detected panel's top edge, the banner displaces that
anchor and the OCR crop lands on **"Super Duke!"** instead of **"Level 7212"** — which fails
the "Level" gate, so the dialog is discarded as not-a-level.

Note the pilot's level 13461 dialog also had "Butler's Gift", "Select Boosters" and a
"Lightning Rush" bar and worked fine. **The new element in this era is the event banner
ABOVE the dialog.**

## Required fix

1. **Locate the title robustly.** Do not assume a fixed offset from the panel's top edge.
   Search a wider vertical band for the "Level" glyph pattern, or locate the title relative
   to a stable landmark (the red X, the green Play button, the panel's side rails) rather
   than the top edge, which a banner can occlude or displace.
2. **A dialog must never be discarded solely because the title crop failed to read "Level".**
   If the panel is structurally a play dialog (green Play button + "Select Boosters"), keep
   it as a recovery candidate and let v2.9's positional alignment assign the number.
3. Confirm the fix on the event-banner era AND verify no regression where the banner is absent.

## Constraints

- **Build on `src/detect_v3.py`** (which already contains the v2.9 dropped-level fix).
  Do NOT touch `src/detect.py` — it is in active use by the running pipeline.
- Diagnostic videos are on disk: `work/diag/R6JUq6g0xXg.mp4` (levels 7211-7230) and
  `work/diag/hofw5Ydebkg.mp4` (levels 7006-7020). **Do NOT download anything** — concurrent
  downloads triggered a multi-hour YouTube IP block once already (README gotcha #9).
  If you need more footage, say so and the operator will fetch it during a pipeline pause.
- A previous attempt at an `ocr_blind` positional workaround was **reverted** because it
  attached the wrong dialogs to 2 of 15 levels. Silent mis-attribution is worse than a
  visible gap. Any recovery path must be verified dialog-by-dialog, not just by count.

## Acceptance

- `R6JUq6g0xXg` yields levels 7211-7230 and `hofw5Ydebkg` yields 7006-7020, with the level
  numbers confirmed by VIEWING the extracted play frames — not merely by count.
- Pilot regression: 194/194, 8/8 exact sequence, 0 `board_t >= first_move_t` violations.
- The v2.9 fixes in detect_v3.py keep working.
- Throughput regression under ~10%.

---

# SPEC v3.1 — surgical repair of 15 bad board screenshots (section downloads only)

User report: "On some levels, like 217, the player opens the pre-level screen, closes it, sees a
feature, and then opens it again. The screenshot you saved is of the feature, not the game board.
Also level 3302, 5750 has a screenshot of the game board too early. No big re-runs for this please."

Both confirmed. Two distinct defects, 15 levels total (0.13% of the archive).

## How the bad levels were found (no reprocessing needed)

`moves_plate()` geometry on every saved `board.jpg`. On a genuine board the plate is extremely
stable: `x/w` 0.705-0.707, `y/h` 0.084-0.099, `w/w` 0.247-0.251, `h/h` 0.093-0.094 (p1..p99 over
11,993 screenshots). Anything deviating >25% on x/w, w/w or h/h — or with no plate at all — is not
a board. That yielded exactly 15 outliers, verified by eye.

## Defect A — `board_t` is not a board at all (13 levels)

The player opens the pre-level dialog, CLOSES it, browses a feature, then reopens and plays. The
detector anchors on the FIRST dialog and captures whatever follows — a feature screen.

Worked example, level 217 (`x13Ri-lxJXw`), read frame by frame:
```
~178.2  "Level 217" dialog opens          <- detector used this as play_t
~179.9  dialog closed; King's Cup panel   <- SAVED AS board.jpg (wrong)
~183.5  "Level 217" dialog opens AGAIN    <- the real attempt
~186    board actually appears, Moves 28
~189    first move (Moves 28 -> 27)
```

Affected: **217** (King's Cup), **769**, **2089**, **4831**, **9280** (map screen),
**2623** (the play dialog itself), **4475**, **5518** (Dragon Nest), **9575** (King's Cup),
**4857** (the iOS home screen — the player left the game entirely),
**5465**, **6086**, **12855** ("Royal Hammer" overlay obscuring the board).

NOT affected, do not touch: **4** and **20** are tutorial levels whose boards are legitimately
dimmed; they are correct.

## Defect B — board captured too early (2 levels)

`first_move_t` lands 0.017-0.034s after `board_appear_t` — physically impossible. The Moves
reference bitmap was sampled while the header was still rendering, so the very next frame read as
a move and `board_t` collapsed onto the board's slide-in.

```
L3302  4UXi0Xw8vvc  board_appear 712.167  first_move 712.201  gap 0.034s
L5750  Oazj8sAZbD4  board_appear 386.000  first_move 386.017  gap 0.017s
```

A scan of all 11,970 levels for `first_move_t - board_appear_t < 0.5s` found **exactly these two**.

## Required approach — section downloads, NOT full videos

Source videos are deleted. Do NOT re-download whole videos: we know the timestamps, so fetch only
the needed window.

```
yt-dlp -f "298/bv*[height<=720][protocol^=https]/bv*[height<=720]" \
       --download-sections "*<start>-<end>" --no-part -o work/sections/<id>.%(ext)s <url>
```

Measured: an 80s window is **16.9 MB and ~41s**, vs ~500 MB for the full video — **30x less data**.
The section's timeline starts at 0, so **section_t = source_t - start**. Record the offset and
convert back before writing any timestamp into the archive.

Window guidance: `[first_play_t - 30, first_play_t + 90]` comfortably covers an open/close/reopen
sequence (verified on 217). Widen only if the sequence runs longer.

## Required fixes

1. **Validate `board_t` is actually a board** before saving: `moves_plate()` present AND within the
   geometry bounds above. If it fails, keep searching forward for a frame that passes.
2. **Prefer the LAST play dialog** before the board when a level has several (dialog opened, closed,
   reopened). Existing `attempts_seen` already counts these.
3. **Reject implausible first-move gaps**: if `first_move_t - board_appear_t < 0.5s`, the Moves
   reference is bad — re-derive it from a later, settled frame.
4. Apply the same three checks in `src/detect.py` so future runs cannot reproduce this.

## Deliverables

- A repair tool that, per level: downloads the section, re-derives `play_t`/`board_appear_t`/
  `first_move_t`/`board_t` within it, converts back to source time, and rewrites `board.jpg`,
  `play.jpg`, `window.mp4`, `window.json`, plus the segment in `out/detect/<id>.json`.
- The same guards in `src/detect.py`.

## Acceptance

- All 13 Defect-A levels yield a board.jpg that passes the `moves_plate()` geometry test, confirmed
  by VIEWING each one.
- 3302 and 5750 show a settled board with the Moves counter at its starting value.
- Levels 4 and 20 untouched.
- Re-running the geometry scan over the whole archive yields **0** outliers besides 4 and 20.
- Pilot regression on `work/pilot_*.mp4`: still 194/194, 8/8 exact sequence, 0 ordering violations.
