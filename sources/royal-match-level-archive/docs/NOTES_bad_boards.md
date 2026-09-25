# NOTES — SPEC v3.1: the 15 bad board screenshots

Working notes for the surgical repair. Written as the work happened, so the order is
chronological rather than tidy.

## The acceptance test, as code

`src/board_geom.py` — Moves-plate geometry, `PLATE_REF` +/-25% on `x/w`, `w/w`, `h/h`.
`y/h` is deliberately NOT bounded: the header slides in vertically and its resting y
drifts a little between UI eras, while the three bounded ratios separate "board" from
"not a board" by a factor of 2+.

`src/audit_boards.py` — scans every `out/levels/*/board.jpg` and prints the outliers.

    .venv/bin/python src/audit_boards.py --jobs 6

## Baseline scan (2026-09-15, 12,751 boards on disk — the archive has grown since the
## spec was written against 11,993)

    scanned 12751  pass 12733  outliers 18

| level | reading | class |
|---|---|---|
| 4, 20 | no plate | **tutorial dim — correct, do not touch** (per spec) |
| 1701 | no plate | **tutorial dim — correct, same class as 4/20.** Viewed: a real settled board with a "Activate power-up to spread JELLY" tooltip and the header dimmed. NOT in the spec's list because it was not yet in the archive when the spec was written. |
| 217 769 2089 2623 4475 4831 4857 5465 5518 6086 9280 9575 12855 | dev 0.44-0.61 / no plate | **Defect A — the 13 levels in the spec** |
| 11232, 12113 | no plate | **Defect A, same "Royal Hammer!" banner variant as 12855**, produced by the pipeline *after* the spec's scan. Left untouched (the brief says touch only the 15) — see "Unresolved" below. |

3302 and 5750 (Defect B) **pass** the geometry test — their board.jpg is a real board
header, it is just the bare backdrop with no pieces drawn yet. Geometry cannot see that
defect; the `first_move_t - board_appear_t < 0.5s` scan is what finds it.

## What each bad board.jpg actually shows (viewed, not inferred)

217 King's Cup leaderboard · 769 castle map · 2089 castle map · 2623 the "Level 2623"
play dialog itself · 4475 Dragon Nest event · 4831 castle map · 4857 the iOS home screen
· 5465 "Royal Hammer!" banner over the board · 5518 Dragon Nest · 6086 Royal Hammer ·
9280 castle map · 9575 King's Cup · 12855 Royal Hammer.
3302 and 5750: correct header (Moves 20 / 27) over an **empty** board — the pieces had
not been drawn yet.

## Root causes

**A.** `classify()` calls any screen with a big cream plate on the right of the header a
BOARD. The King's Cup panel, Dragon Nest, the castle map, the Royal Hammer intro banner
and the iOS home screen all qualify. So when the player opens the dialog, closes it,
browses a feature and reopens it, `_header_anchor` locks onto the feature screen and
every timestamp downstream describes it.

Where the reopen is far enough apart that a "board" run separates the two dialog runs,
`_merge_instances` does *not* merge them; they survive as two instances with the same
OCR level and `assign_levels` collapses them as a retry, keeping `grp[0]` — the first,
i.e. the wrong one. That is why 9 of the 13 carry `retry_attempt` and `attempts_seen=2`.

**B.** `precise_move()` opens its window `PRECISE_BACK_S` (1.6 s) before the coarse move.
On a level whose board appears barely more than that before the move, the window reaches
back into the header's **slide-in**, where the Moves bitmap is a translated copy of the
settled one and so differs from `ref_bits` everywhere. The first frame of the window is
then declared the move, and `board_t` collapses onto the slide-in.

## The three guards (src/detect_v31.py, to be copied over src/detect.py)

1. **Geometry-validated anchor.** `refine_window` now computes `geo[i]` (Moves-plate
   geometry) for every frame `classify` called BOARD. If the anchor's first second
   contains no geometrically-genuine board *while the window contains one later*, the
   anchor moves to the first genuine one and the segment is flagged `board_reanchored`.
   Conditional on purpose — a healthy level is bit-for-bit unchanged and a tutorial level
   (whose dim removes the plate entirely) keeps anchoring on the header as before.
   Cost: `moves_plate` is 0.08 ms on a 296x640 refine frame.
2. **Prefer the last attempt that reached a real board.** `Dialog.board_ok` is measured in
   `work()` on the full-res frame that is already in hand. `assign_levels` keeps `grp[0]`
   unless its board is not a board, in which case it falls through to the last attempt
   whose board is. Conditional, again, so genuine retries are unaffected.
   `_merge_instances`' within-instance picker gained `board_ok` as a tie-break too.
3. **Move floor.** A move is not believed within `MIN_MOVE_GAP_S = 0.5 s` of
   `board_appear_t`, in both the 12 fps coarse search and (via `move_floor_t`) inside
   `precise_move`, whose window is what actually reached back into the slide-in.

New flag `board_unverified` (board_t's frame fails the geometry test; expected on tutorial
levels, alarming anywhere else) with a 0.90 confidence multiplier. The flag/confidence
table moved out of `assign_levels` into `score_segment()` so `repair_boards.py` re-scores a
repaired segment through exactly the same code.

## The repair tool

`src/repair_boards.py`. Per level: find the owning video from `_source.json`, download
`[play_t-30, play_t+90]`, **verify** the section offset (the originally-detected dialog
must be found within 1.5 s of where `source_t - start` predicts — refuse to write
otherwise), re-detect inside the section, pick the LAST dialog followed by a
geometry-verified board, convert back to source time, check the invariants, then write.

Backups: `out/levels/<NNNNN>/_backup_v31/` and `out/detect/<id>.json.v31bak`, written once
before the first overwrite.

`window.mp4` is re-cut with pipeline.py's exact `WINDOW_ENCODE_ARGS` (fps=10, libx264,
crf 30, veryfast) and `board_frame_idx` is re-measured by pixel-matching the new board.jpg
against the new clip — SPEC v2.8's rule, because no timestamp formula lands on the right
10 fps frame.

## Verified: the section timeline

`work/sections/x13Ri-lxJXw.mp4` covers source 120-200. Checked by eye:
section 58.25 = "Level 217" dialog (= source 178.25, the original `play_t`), 59.9 =
King's Cup, 63.5 = "Level 217" again. **`source_t = section_t + start`, exactly.**
The tool re-checks this per level rather than trusting it.

## L217 re-derived (dry run, detect_v31)

    before: play=178.250 appear=178.833 board=179.917 first_move=184.667
    after:  play=183.500 appear=184.667 board=192.861 first_move=192.883

Both dialog runs in the section now resolve to the same board (`board_t` 72.861 section),
and the later one wins. Confirmed against a 2 fps tile of section 63-75 s: dialog at 63.0,
"TNT" loading screen 63.5-64.0, board slides in 64.5, Moves **28** and settled from 65.0,
the reward hat finishes ~68.5, Moves goes 28 -> 27 between 72.5 and 73.0. So
`board_appear_t` 64.667 and `first_move_t` 72.883 are both right.

> The spec's worked example ("~186 board appears, ~189 first move") was approximate; the
> real numbers are ~184.7 and ~192.9. `board_t` is the last settled frame before the move,
> so a `board_t`/`first_move_t` gap of ~0.02 s is normal and expected — Defect B is about
> the `board_appear_t` -> `first_move_t` gap, not this one.

## Scope: 17 levels, not 15

The coordinator confirmed **11232 and 12113 are in scope** — identical Defect-A "Royal
Hammer!" signature to 12855, they simply post-date the spec's scan. **1701 is out of
scope** (tutorial dim, same class as 4 and 20, legitimately correct).

`src/audit_boards.py` now reports `KNOWN_GOOD = {4, 20, 1701}` as *known-good exclusions*
rather than failures, so a clean archive prints `FAILURES 0`.

### 11232 / 12113 had to wait for the pipeline

Both are owned by videos in the running remediation's `--only` list — `ElqR3dVyXPo` and
`7cWyFzWKRNk` — whose `out/detect/*.json` had been **deleted for reprocessing**, which is
why `find_level()` could not resolve them. Repairing them mid-run would have been
overwritten. Hence the final ordering:

1. pipeline exits
2. swap `detect_v31.py` -> `detect.py`
3. **full** pilot regression (all 8 videos, both versions, uncontended)
4. re-run the geometry audit — this is the *authoritative* defect list, because the
   remediation has been rewriting `out/levels/` for 18 videos covering levels 6926-7270
5. fetch sections one at a time, 30 s apart, abort on any bot-block signature
6. repair + view every level
7. final audit: expect `FAILURES 0`

## Result

**15 of 17 levels repaired and confirmed by eye.** Final archive audit:

    scanned 13044  pass 13039  known-good exclusions 3  FAILURES 2
      [known-good, tutorial dim] L4, L20, L1701
      [FAIL] L11232, L12113          <- blocked, see below

Archive-wide invariants over all 12,432 segments: **0** `board_t >= first_move_t`
violations, **0** levels with `first_move_t - board_appear_t < 0.5 s` (the scan that
originally found 3302 and 5750 now returns nothing). Levels 4, 20 and 1701 were never
written to — no `_backup_v31/` exists for them and 4/20 still carry their 14 Sep mtime.

| level | was | now |
|---|---|---|
| 217 | King's Cup leaderboard | board, Moves 28 |
| 769 | castle map | board, Moves 29 |
| 2089 | castle map | board, Moves 32 |
| 2623 | the play dialog itself | board, Moves 23 |
| 3302 | empty board, pieces not drawn | board with pieces, Moves 20 |
| 4475 | Dragon Nest event | board, Moves 28 |
| 4831 | castle map | board, Moves 25 |
| 4857 | iOS home screen | board, Moves 20 |
| 5465 | "Royal Hammer!" banner | board, Moves 24 |
| 5518 | Dragon Nest event | board, Moves 21 |
| 5750 | empty board, pieces not drawn | board with pieces, Moves 27 |
| 6086 | "Royal Hammer!" banner | board, Moves 23 |
| 9280 | castle map | board, Moves 22 |
| 9575 | King's Cup leaderboard | board, Moves 27 |
| 12855 | "Royal Hammer!" banner | board, Moves 22 |

Every repaired `board.jpg` measures `plate_dev` 0.003-0.006 (a genuine board is 0.003-0.004).
All 15 `window.mp4` re-cut at exactly 10 fps with a re-measured `board_frame_idx`.

### BLOCKED: 11232 and 12113

Their owning videos — `ElqR3dVyXPo` and `7cWyFzWKRNk` — have **no `out/detect/<id>.json`**.
Both are in `AFFECTED_VIDEOS.json` and their checkpoints were deleted for a remediation
batch that has not run yet (they were processed at 06:08 and 09:32, before the 6926-7270
run that finished at 12:49, and were not in its scope). `repair_boards.py` needs that
segment to read `play_t` from and to write back to, so it refuses.

**These two need no section download at all.** The fixed `detect.py` now has all four
guards, so simply letting the pipeline reprocess those two videos should repair them for
free — and any repair done before that run would be overwritten by it anyway:

```bash
.venv/bin/python src/pipeline.py --only ElqR3dVyXPo,7cWyFzWKRNk
.venv/bin/python src/audit_boards.py --jobs 6      # expect FAILURES 0
```

## Pilot regression (final, uncontended, all 8 videos)

Baseline = the pre-swap detector, preserved as `src/detect_v3_backup.py`.

| | |
|---|---|
| Levels | **194 -> 194** |
| Exact sequence match | **8/8 videos** |
| `board_t >= first_move_t` violations | **0** |
| Segment diffs vs baseline | **0** — every field byte-identical, including `board_t` (so `board_frame_idx` is untouched) |
| Throughput | 35.8x -> 33.9x realtime, **5.5% regression** (budget 10%) |

## The regression I introduced, and caught

First cut of guard 3 skipped early indices in `precise_move`'s search (`range(lo_i, ...)`)
instead of clamping the window. That silently defeated the pre-existing
`if move_i == 0: return None` rule, whose job is to reject a window that opened *after* the
move had already happened. Result on the pilot: **board_t jumped ~1.5 s earlier on 4 of 29
levels of `A9xLB2MsDNg`** (L4, L20, L21 and small shifts on L12/L28) — `PRECISE_BACK_S`
exactly, the signature of "move found at index 1".

Fixed by clamping `ss` forward instead, never past `t_move_coarse - MIN_PRECISE_BACK_S`
(0.30 s) so the walk back to the last settled frame still has frames to walk over. The
`move_i == 0 -> None` rule is untouched.

Second finding from the same run: `board_unverified` was firing on tutorial levels and
costing them 10% confidence. It is now suppressed when `tutorial_overlay` is present —
those levels are correct and must stay byte-identical.

Third: even the corrected clamp still perturbed six pilot levels by 1-70 ms, because it
fired on *every* level whose move came within ~2.1 s of the board. The final shape is
**"run it exactly as before, then check the answer, and only re-run clamped if the answer
is impossible"** — so a healthy level never takes the new path at all and stays bit-for-bit
identical. That is the general lesson: a guard for a 2-in-13,000 defect should be a
*fallback*, not a change to the main path.

## Files / how to undo

| path | what |
|---|---|
| `src/detect.py` | **now carries all four guards** (was swapped in after the pipeline exited) |
| `src/detect_v3_backup.py` | the exact pre-swap detector — the regression baseline; `cp` it back to undo |
| `src/detect_v31.py` | identical copy of the new `detect.py`, kept as the version record |
| `src/board_geom.py`, `src/audit_boards.py`, `src/repair_boards.py` | new |
| `out/levels/<NNNNN>/_backup_v31/` | 15 dirs — the original jpgs/clip/sidecars |
| `out/detect/<id>.json.v31bak` | 15 files — the original per-video detect json |
| `work/sections/` | 488 MB, 15 sections + `.section.json` offset sidecars. Kept so any level can be re-verified without another download; delete when happy. |

`manifest.json` was deliberately **not** rebuilt — the operator does that
(`.venv/bin/python src/build_index.py`). It reads `board_frame_idx` from each level's
`window.json`, which the repair rewrote, so a rebuild will pick the new frames up.

## Two more false alarms worth recording

Both were in my own safety code, and both would have looked like real failures:

* `pgrep -f 'src/pipeline.py'` **matches the shell running it**, so the "don't download
  while the pipeline runs" guard fired permanently. Fixed with `'[s]rc/pipeline.py'`.
* The bot-block detector matched a bare `"429"` — and yt-dlp pipes ffmpeg's progress
  through, where `bitrate=2429.9kbits/s` contains it. It aborted a completely healthy
  download run. Now it matches only the real signatures (`sign in to confirm`,
  `not a bot`, `too many requests`, `http error 429`), with a unit check.

**No genuine bot-block occurred.** All 15 sections fetched one at a time with 30 s gaps,
11-36 MB each, ~500 MB total against ~7.5 GB for the full videos.
