# NOTES — SPEC v3.0, whole UI era yields ZERO levels

Working file: `src/detect_v3.py` (only file touched). Scratch: `/tmp/v4work`, `/tmp/v4out`.
`src/detect.py` untouched. No downloads performed.

## Hypothesis — CONFIRMED, exactly as stated in SPEC v3.0

`ocr_level()` (detect_v3.py:1105) anchors the title crop on `panel_top()` (:988), which returns
**the first row in 0.10h..0.55h where a 6-row window is >60% bright** (V>100 over x 0.05..0.95w).

On `R6JUq6g0xXg` t=150.2 (level 7212), measured directly:

```
panel_top(im) -> 128   (= exactly 0.10*h, the scan's first row — the "Super Duke!" banner)
ocr_level(im) -> (None, 0.0, '7 55 a', False)     # is_level_dialog = False
```

Row brightness profile of that frame:

```
y=128..184  0.83-0.91   <- Super Duke! event banner (full width, bright)
y=188..216  0.07-0.15   <- dark gap between banner and dialog
y=220..     0.36 -> 0.90 <- the real dialog panel top (~y=228)
```

True panel top is ~228; the title "Level 7212" occupies y≈250-320. The legacy crop is
`pt+0.004h .. pt+0.090h` = rows 133..243 — entirely inside the banner. So the crop OCRs the
banner, `_looks_like_level_word()` fails, and `assign_levels()` drops the instance as
`not_level`. Every dialog in the video hits this, `groups` ends up empty, and the v2.9
alignment is never even reached (it is gated on `groups` being non-empty), so zero segments.

The banner is present on *every* dialog in both diagnostic videos — it is a permanent event
strip for that era, not an occasional popup.

## Dialog inventory (full-res frame per detected cheap-pass run)

`R6JUq6g0xXg` 22 runs: run0 = Leaderboard/Continue popup (false positive), runs 1-20 =
Level 7211..7230 (incl. "Hard Level" 7215/7225 red panel and "Super Hard" 7219/7229 purple
panel), run21 = Team chat screen. `hofw5Ydebkg` 16 runs: 7006, a "Sky Race" popup, 7007..7020.
Bottom bars are "Lightning Rush" / "Sky Race" leaderboards.

## What changed in `src/detect_v3.py` (only file modified)

### 1. Title anchoring — the actual fix

* `panel_top()` -> `panel_tops(im, limit)`: returns **every** bright-band start in
  0.10h..0.55h, not just the first. `panel_top()` kept as `panel_tops(...,1)[0]`.
* New `close_button_top(im)`: bbox-top of the red circular close button, searched over
  y 0.06h..0.60h, x 0.70w..w. Accepts a component that is 0.07w-0.22w wide *and* tall,
  near-square (|w-h| <= 0.30 max), fill >= 0.38 (the white X is cut out of the disc, so
  the measured fill is ~0.48 — the first cut of this used 0.55 and found nothing).
  The button sits **on** the panel, level with the title, so nothing drawn *above* the
  dialog can displace it.
* `ocr_level()` split into `_read_title(im, pt)` (the old body) plus a driver that tries
  anchors in order and returns the first that reads "Level" **and** yields a number:
  1. `panel_tops()[0]` — the legacy anchor. If it says "Level", return immediately, so
     behaviour is unchanged wherever it already worked (no extra tesseract calls either).
  2. `close_button_top() - 3`
  3. the bright band nearest the close button
  4. remaining bright bands, top-down (max 4 fallback attempts total)
  A fallback must produce "Level" *and* digits before it is accepted; otherwise the
  legacy answer stands. That is far too specific for a mis-aimed crop to fake, so the
  fallback cannot invent a level out of an event popup.

Order matters, measured both ways: anchoring on the *band nearest the button* first
mis-read `R6JUq6g0xXg` L7228/L7230 as 1228/1230 (the whole-title `image_to_string` vote
flips 7->1 with a 5-px crop shift), while anchoring on the *button* first missed
`hofw5Ydebkg` L7014/L7018 (button anchor gives the digits but an empty word). Button
first, nearest band second, gets all four right.

### 2. Structural play-dialog test — SPEC v3.0 item 2

* New `has_select_boosters(im)`: find the green Play button (`find_button`, already used
  by the cheap pass), OCR the band `btn.y0-0.195h .. btn.y0-0.100h` with **psm 11**
  (sparse text — psm 7 reads the band as one smear and returns nothing), fuzzy-match any
  output line against "selectboosters" (>= 11 of 14 characters).
  Verified True on all 16 pilot play frames spanning five UI eras (levels 2, 16, 161,
  173, 1511, 1521, 3506, 3513, 5996, 6006, 9001, 9016, 11501, 11508, 13461, 13481) and on
  the banner era; False on the Leaderboard popup, the Team screen, the Sky Race popup and
  both "Continue?" popups.
* `Dialog.structural`, computed **only when the title did not read "Level"**, so a healthy
  video pays nothing.
* `_promotable()` now also accepts a reject with structural evidence (previously a
  legible non-"Level" title made a dialog permanently unpromotable — a real risk in this
  era, where a mis-anchored crop reads a legible "SuperDuke").
* New last-resort branch in `assign_levels()`: when **every** instance was rejected
  (`groups` empty — the zero-segment signature), take the structurally-confirmed rejects
  and, **only if their count equals the title's level count exactly**, map candidate i to
  level lo+i. Exact count makes the monotone mapping forced, so there is no choice left to
  get wrong. Reported as `stats.ocr_blind`.

### 3. Throughput

The first cut cost +1.36 s on every dialog whose title did not read "Level" (4 fallback
anchors x 4 tesseract calls). `_read_title` is now split into `_title_word` (mask + word
OCR) and `_title_number` (the three digit psm passes); a fallback anchor runs the word
pass only and is abandoned unless it says "Level". `MAX_TITLE_ANCHORS = 3`.
Per-frame micro-benchmark, old `detect.ocr_level` vs new, same 18 frames:

```
16 healthy play frames   old 0.30-0.34 s   new 0.29-0.33 s   (delta within noise)
2 "Continue?" popups     old 0.28 s        new 0.50 s        (was 1.65 s before the split)
has_select_boosters                        0.10 s per popup
```

## Results

### Acceptance: the two diagnostic videos

| video | claims | before | after |
|---|---|---|---|
| `R6JUq6g0xXg` | 7211-7230 | **0**/20, dialogs=21, dropped_not_level=20 | **20/20**, all `level_source: both` |
| `hofw5Ydebkg` | 7006-7020 | **0**/15, dialogs=16, dropped_not_level=15 | **15/15**, all `level_source: both` |

`both` means the OCR and the title-derived sequence agree *independently* - the strongest
result available. 0 drops, 0 positional recoveries needed, 0 `board_t >= first_move_t`.

**Visually confirmed**, not just counted: the play frame was extracted at every emitted
`play_t` and read by eye. All 20 read "Level 7211".."Level 7230" in order; all 15 read
"Level 7006".."Level 7020" in order; both include the Hard Level (red) and Super Hard
(purple) panel variants. Contact sheets: `/tmp/v4work/ver2_R6.png`, `/tmp/v4work/ver2_ho.png`.

### Pilot regression — PASS

```
194/194 levels, 8/8 exact sequence match, 0 board_t >= first_move_t violations
```

Field-by-field vs the shipped `out/detect/*.json` (`/tmp/v4work/cmp.py`): the **only**
differences anywhere are 11 `ocr_text` values that improved from `None`/noise to a clean
"Level NNNN" (e.g. `L1520 None -> 'Level1520'`, `L9009 'a Level9009' -> 'Level9009'`).
Every `level`, `level_source`, `ocr_level`, `ocr_conf`, `play_t`, `board_t`,
`board_appear_t`, `first_move_t`, `moves_*`, `confidence` and `flags` is unchanged, and
all per-video stats are unchanged. `board_frame_idx` is derived from `board_t` in
pipeline.py, so it is unaffected.

### Mis-attribution check on the structural fallback (the thing that got reverted)

`ocr_level` monkey-patched to fail on every frame, run over all 8 pilots in both modes
(`empty` = illegible title, `garbage` = legible non-"Level" title), then each recovered
`play_t` compared against the known-correct detection (`/tmp/v4work/blind.py`):

```
0QfejcKagvk  15/15   0 wrong dialogs     (the video the reverted ocr_blind got wrong: it
0mwjjHHcmGI  20/20   0 wrong dialogs      filed 11514 and 11515 under the wrong dialogs;
guiinjQLYvg  30/30   0 wrong dialogs      the two "Continue?" popups are now excluded
A9xLB2MsDNg   declined (0/29)             structurally, so the count comes out exact)
FJ6PY-6zAf8   declined (0/40)
RmoqWHCPQx0   declined (0/15)
agxDN7ffBII   declined (0/25)
lo4xXqDlZGM   declined (0/20)
```

**0 mis-attributions in 16 runs.** The 5 declines are the gate working as intended:
`A9xLB2MsDNg` has 2 retry_attempt levels, and without OCR a retry cannot be collapsed, so
the structural count is 31 against a title of 29; `lo4xXqDlZGM` gets 19 structural of 20
(one dialog's play_t frame fails the caption OCR). Counts disagree -> do nothing, which
leaves exactly today's behaviour (zero) rather than a guess. Recall of this net is
therefore ~3/8; it is a safety net for a future wholesale OCR failure, not a primary path.

### Throughput

Wall clock is not measurable right now - the live pipeline is running with
`--process-concurrency 2` and both binaries scatter over 32-58 s on the same video. CPU
time is the honest metric; 4 interleaved pairs on `work/pilot_0QfejcKagvk.mp4`:

```
detect     user 193.00  198.00  186.45  197.76   mean 193.80
detect_v3  user 200.93  194.33  199.09  188.82   mean 195.79
```

**+1.0% CPU**, far under the 10% bound. Consistent with the micro-benchmark: the only
added work is ~0.33 s per dialog whose title does not read "Level", of which a typical
video has one or two.

## Unresolved / not measured

* Only 2 of the 18 zero-segment videos are on disk, so the other 16 (levels 6926-7205,
  7231-7270) are **untested**. They share the signature and, from the contact sheets, the
  same event-banner UI, but that is inference. The operator should re-run the whole list
  in `ZERO_SEGMENT_VIDEOS.json` after swapping detect_v3 in.
* `nDyxbLc7mOo`'s "Wild Card" popup - the case `_promotable()` exists to block - could not
  be re-tested (video deleted, downloads forbidden). `has_select_boosters` only *widens*
  promotability, so the risk is that a Wild Card popup passes the caption test. Five
  negative controls that do have a green button all return False (Leaderboard, Team chat,
  Sky Race, and both "Continue?" popups), and the match needs 11 of 14 characters of
  "selectboosters" on the row above the button, which that popup does not have.
* `R6JUq6g0xXg` run21 (a Team chat screen at t=1804) and `hofw5Ydebkg` run01 (a Sky Race
  popup) are still detected as dialogs by the cheap pass and still correctly rejected.
  Unchanged behaviour, noted only so it is not mistaken for a new problem.

## Files

Modified: `src/detect_v3.py` **only**. `src/detect.py` untouched (md5 still
`c8c76b9bdf351e0e40957e8c160208f0`). Nothing written to `out/`; all output in
`/tmp/v4out` and `/tmp/v4work`.
