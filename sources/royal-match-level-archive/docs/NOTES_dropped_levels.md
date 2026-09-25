# NOTES — SPEC v2.9, levels silently dropped when OCR fails

Working file: `src/detect_v3.py` (copy of `src/detect.py`; original untouched — live run in progress).
Scratch: `/tmp/v3` (videos), `/tmp/v3out` (detect JSON), `/tmp/v3work` (logs).

## Root-cause map (from existing `out/detect/*.json`, no re-run needed)

`assign_levels()` drops an instance outright in three places (detect.py:1412-1425):
1. no run in the instance says "Level" **and** no `ocr_level` → `dropped_not_level`
2. `ocr_level` present, conf ≥ 0.5, outside `[lo-3, hi+3]` → `dropped_out_of_range`
3. no run says "Level" and `ocr_level` outside `[lo-1, hi+1]` → `dropped_not_level`

A drop removes a real level. `k != expected` then disables `positional`, so every segment falls back
to pure OCR (`level_source="ocr"`) and gets `count_mismatch`. The level is gone.

## The 22, categorised (gaps measured from the shipped detect JSON)

| kind | videos |
|---|---|
| mid-video hole, big time gap at the hole | SdCCiUurF68(3462), jorpD61uajc(2131), z531eaVxOF4(2171), FcKbScYoPgI(1371), 8Ihsul2sfk4(1201), sj88NkM1cbk(1101), D_m64wGMeMg(5281), Rq23jyuN3Tc(5901), aaTT3Am_F2c(3101), TGoltn3WFP4(3927), 3LNsGnhANQ4(1051), 7NrAzLTkjKI(2313), -304iKnGUGU(2121), mCdxoJxD-a8(2373) |
| missing FIRST level | JRx5LCZtQxM(421) t0=135.5, P725kpl-EAw(5621) t0=143.0, 64ipC9mKDfY(391) t0=129.6, mns99cZalxg(591) t0=123.6, **Tf9KRJFfScY(6260) t0=7.5 — no room, suspect title off-by-one** |
| missing LAST level | nDyxbLc7mOo(3980) tail=263s, EUetRi0SLC8(1721) tail=123s |
| title typo | N_ApgMCPdDk "1551-1751" (201 lv / 1946 s = 9.7 s/lv); OCR 1551-1571 sequential |

Every one of the 22 except N_ApgMCPdDk has ≥1 dropped instance, so a recovery candidate should exist.

## Confirmed root cause (visual, 3 videos)

The OCR appends a spurious trailing digit to the level number:

| video | raw OCR | true level |
|---|---|---|
| 3LNsGnhANQ4 | `Level10517` conf 0.746 | 1051 |
| sj88NkM1cbk | `Level11017` conf 0.655 | 1101 |
| JRx5LCZtQxM | `Level4217`  conf 0.719 | 421  |

The title still reads "Level", so the dialog is unquestionably a play dialog — but the number
lands outside `[lo-3, hi+3]`, so the old `dropped_out_of_range` branch deleted it. Frames extracted
at the recovered `play_t` show "Level 1051" / "Level 1101" / "Level 421" exactly as predicted.

## What changed in `src/detect_v3.py`

1. `assign_levels()` no longer `continue`s on a failed filter — the instance is held as a
   **recovery candidate** with the reason recorded.
2. New `_align_candidates()`: a Needleman-Wunsch-style DP aligning the ordered candidate list
   onto `lo..hi`. Costs (module constants): `MISSING_LEVEL_COST 5.0`, `REJECT_USE_COST 2.0`,
   `NO_OCR_COST 0.6`, `OCR_MISMATCH_COST 3.5`, `KEPT_SKIP_COST 4.5`, `OCR_TRUST_CONF 0.5`.
   An **out-of-range reading is demoted to "no reading"**, not used as counter-evidence — that is
   the actual fix for the trailing-digit case.
3. `_promotable()` gate: a reject may stand in for a missing level only if its title said "Level"
   or was illegible. A legible non-Level title ("Wild Card") is positive evidence of an event
   popup. *Added after nDyxbLc7mOo fabricated level 3980 out of a Wild Card dialog.*
4. Recovered levels → `level_source: "position"`, flag `level_from_position`, conf 0.45 (before
   the usual multipliers), plus `ocr_sequence_mismatch` or `ocr_failed`.
5. `MIN_SECONDS_PER_LEVEL = 25.0`: if the title implies a denser video than that, the title is a
   typo — alignment is skipped entirely and legacy OCR numbering stands (N_ApgMCPdDk).
6. Truncation: the "dialog must be followed by ≥4 board samples" test now scales its threshold
   down when fewer than 25 s of video remain, so a last level cut short is not lost.
7. New stats: `sequence_aligned`, `recovered_from_position`, `unrecovered_levels`,
   `title_implausible`.

**No-regression guarantee by construction:** when `k == expected` the alignment is a monotone
bijection of k groups onto k levels, i.e. forced to `group i -> lo+i` — bit-identical to the old
`positional` path. Recovery can only fire when `k < expected`. If the DP wants to leave an
*accepted* dialog unmatched, the whole alignment is discarded and legacy numbering is used, so a
kept dialog is never silently dropped.

## Results so far

| video | claims | v2 result | v3 result | note |
|---|---|---|---|---|
| 3LNsGnhANQ4 | 1046-1060 | 14, missing 1051 | **15/15** | 1051 recovered, verified visually |
| sj88NkM1cbk | 1091-1105 | 14, missing 1101 | **15/15** | 1101 recovered, verified visually |
| JRx5LCZtQxM | 421-435 | 14, missing 421 | **15/15** | 421 recovered at t=5.1s, verified visually |
| SdCCiUurF68 | 3461-3480 | 19, missing 3462 | **20/20** | recovered from an *illegible-title* reject at t=193.5 |
| jorpD61uajc | 2126-2145 | 19, missing 2131 | **20/20** | `Level21317` -> 2131 |
| P725kpl-EAw | 5621-5630 | 9, missing 5621 | **10/10** | `Level56217` -> 5621 (first level) |
| nDyxbLc7mOo | 3966-3980 | 14, missing 3980 | 14/15, `unrecovered_levels:[3980]` | **title over-claims**: the recording ends on the map screen at "Level 3980" without playing it (contact strip of t=1110-1376 shows Space Mission / Collection / Wild Card / Dragon Nest browsing). Levels now numbered `both` instead of `ocr`. |
| Tf9KRJFfScY | 6260-6275 | 15, missing 6260 | 15/16, `unrecovered_levels:[6260]` | **title over-claims**: opens on the map screen with "Level 6261" as next; 6260 is never played |
| N_ApgMCPdDk | 1551-1751 | 21 (1551-1571) | **21 (1551-1571)**, `title_implausible: true` | title typo, as specified |

### Pilot regression (8 videos, 194 levels) — `/tmp/v3out/pilot` vs `out/detect`

Compared field by field (every segment key + all stats except timing/new keys) with
`/tmp/v3work/cmp.py`.

```
0QfejcKagvk IDENTICAL (15)   A9xLB2MsDNg IDENTICAL (29)   RmoqWHCPQx0 IDENTICAL (15)
0mwjjHHcmGI IDENTICAL (20)   FJ6PY-6zAf8 IDENTICAL (40)   agxDN7ffBII IDENTICAL (25)
guiinjQLYvg IDENTICAL (30)   lo4xXqDlZGM IDENTICAL (20)
videos with diffs: 0
8 videos, 194 levels, 8/8 exact sequence match, 0 board_t>=first_move_t violations
```

**PASS** — not merely equivalent, byte-identical on every segment field including
`board_t`/`board_appear_t`/`first_move_t`/`confidence`/`flags`.

Re-run in full a second time (`/tmp/v3out/pilot2`) after a late correctness fix — I had moved the
"carry the union of the instance's OCR evidence" block *ahead* of the keep/reject tests, which could
in principle change which instances are rejected. Restored to the legacy order so the keep/reject
decision is bit-faithful to `detect.py`; all 8 pilots still byte-identical.

## Synthetic unit checks (`/tmp/v3work/test_align.py`, 23 assertions, all pass)

Drives `assign_levels()` directly with fabricated `Dialog`s — no video needed. Covers: clean video
unchanged; trailing-junk-digit mid/head/tail recovery; event popup NOT promoted into a genuine gap;
event popup ignored when nothing is missing; implausible title (N_ApgMCPdDk shape); title
over-claiming one level at the head (Tf9KRJFfScY shape); retry collapse; and `k > expected` falling
back to legacy rather than discarding a kept dialog.

## Throughput (interleaved A/B, same video, same machine)

`work/pilot_0QfejcKagvk.mp4`, 1573 s, three alternating pairs:

```
detect     29.58s (47.1x)   28.44s (49.0x)   28.46s (48.9x)   median 28.46s
detect_v3  29.15s (47.8x)   28.92s (48.2x)   28.63s (48.7x)   median 28.63s
```

**+0.6% wall time**, inside run-to-run noise and far under the 10% bound. Expected: the change is
one `assign_levels()` call per video over ≤50 candidates × ≤40 levels, plus one integer comparison
per dialog run in the cheap pass.

---

## UNRELATED BUG FOUND DURING VALIDATION — whole videos yielding zero levels

While watching `logs/pipeline.log` I saw the live run emit `segments=0 levels_ok=0` for a video.
Scanning all 404 detect outputs:

```
idx  video         title                  dialogs  dropped_not_level  found
313  -eNyjlfSF2o   Level 6926-6945           24           20           0/20
312  AELrl4ZeLlI   Level 6946-6970           28           25           0/25
311  TgNrbxUoF1s   Level 6976-6990           16           15           0/15
310  hofw5Ydebkg   Level 7006-7020           16           15           0/15
309  X5L9BqMxhNQ   Level 7021-7035           16           16           0/15
308  FlHVknilam0   Level 7036-7055           22           21           0/20
307  RryOjPgKj1Y   Level 7056-7085           31           30           0/30
306  kkhVDI5fO1M   Level 7106-7125           20           20           0/20
```

A **contiguous block of playlist indices 306-313**. Index 314 (`5KByVzyrbvs`) and 316 are fine, and
so are much later levels (13461 works), so this is not a level-number effect — it is ~8 consecutive
uploads whose dialog-title OCR fails completely. Every dialog is detected (count ≈ expected + 1) and
every one is thrown away by the same `dropped_not_level` branch this spec is about. **~160 levels
lost, silently.** The run is still descending through that index range, so the block may grow.

`detect_v3` as written does **not** rescue these, and I deliberately decided it should not.

I prototyped the obvious extension (an `ocr_blind` branch: when *no* instance in the whole video
produced either a "Level" title or an in-range number, promote every reject and assign purely by
position — gated on `not groups`, so it could only ever fire where the alternative is zero levels).
Then I validated it against real footage by monkey-patching `ocr_level` to return nothing and
re-running a pilot, which reproduces exactly this failure mode on a video whose correct answer is
known (`/tmp/v3work/blind.py`).

Result on `pilot_0QfejcKagvk` (levels 11501-11515):

```
      level   blind play_t    true play_t
      11513       1126.00        1126.00
      11514       1190.83        1244.67   <<< wrong dialog
      11515       1244.67        1332.08   <<< wrong dialog
```

It produced the right level *count* and the right level *numbers*, but picked the wrong dialogs:
there were 17 instances for 15 levels, and with no OCR every candidate costs the same, so the DP
skipped the last one instead of the two event popups at 1190.8 s and 1305.4 s. Two levels would have
been filed with somebody else's screenshot. **Silent mis-attribution is worse than a visible gap**,
so I reverted it.

The candidate dump does show a usable separator — both popups had `reward_anim` absent while all 15
real levels had it, and their `moves_stable_s` sat outside the 3.1-5.2 s band the real levels
occupied — but tuning that on one simulated pilot would be over-fitting, and I could not obtain any
of the eight real videos to check it (YouTube began bot-checking this IP, see below). The proper fix
for that block is to make the title OCR work for that UI era, not to guess positions.
**Flagged for the operator as a separate defect.**

## NOT YET VALIDATED — 13 of the 22

These could not be re-downloaded (YouTube bot-block, below), so they have **not** been run through
`detect_v3`:

```
z531eaVxOF4(2171)  FcKbScYoPgI(1371)  8Ihsul2sfk4(1201)  D_m64wGMeMg(5281)  Rq23jyuN3Tc(5901)
aaTT3Am_F2c(3101)  TGoltn3WFP4(3927)  7NrAzLTkjKI(2313)  64ipC9mKDfY(391)   EUetRi0SLC8(1721)
-304iKnGUGU(2121)  mCdxoJxD-a8(2373)  mns99cZalxg(591)
```

11 of the 13 are the same mid-video-hole shape as the six already confirmed fixed, and 2 are the
head/tail shape (64ipC9mKDfY, mns99cZalxg at the head; EUetRi0SLC8 at the tail) — also confirmed
fixed in the validated set (JRx5LCZtQxM, P725kpl-EAw at the head). I expect them to pass, but I have
not measured it and am not claiming it.

To finish once downloads work again:

```bash
for v in z531eaVxOF4 FcKbScYoPgI 8Ihsul2sfk4 D_m64wGMeMg Rq23jyuN3Tc aaTT3Am_F2c TGoltn3WFP4 \
         7NrAzLTkjKI 64ipC9mKDfY EUetRi0SLC8 -304iKnGUGU mCdxoJxD-a8 mns99cZalxg; do
  yt-dlp -f "298/bv*[height<=720][protocol^=https]/bv*[height<=720]" --no-part -o "/tmp/v3/%(id)s.%(ext)s" \
    "https://www.youtube.com/watch?v=$v"
  meta=$(.venv/bin/python -c "import json;print(json.dumps([x for x in json.load(open('playlist.json'))['videos'] if x['id']=='$v'][0]))")
  .venv/bin/python src/detect_v3.py --video /tmp/v3/$v.mp4 --meta "$meta" --out /tmp/v3out/$v.json
  rm -f /tmp/v3/$v.mp4
done
```

Pass criterion: `found_levels == expected_levels`, `unrecovered_levels == []`, and each
`level_from_position` segment's `play_t` really shows that level number in the frame.

## Throttling incident

At ~22:27 YouTube began returning "Sign in to confirm you're not a bot" for downloads. My validation
downloads were running alongside the live run's; I stopped mine as soon as the live log showed the
same error. The operator restarted the pipeline at 22:30 with
`--download-concurrency 1 --sleep-min 8 --sleep-max 20 --throttle-threshold 2 --throttle-cooldown 1200`.
The block did not lift: a single test download at 23:04, half an hour after the last successful one,
still returned the bot check. I did **not** try to work around it — no `--cookies-from-browser`, no
alternate `player_client` — and I stopped and deleted my own download scripts once I found the
operator's `resume_when_clear.sh` already running, since it deliberately probes metadata only every
20 min and explicitly does not retry downloads ("hammering a blocked IP reinforces the block"). My
scripts probed every 5 min and would have started 13 downloads on top of the relaunched pipeline.

The live pipeline process itself is gone as of ~22:34 (cooldown then exit); `resume_when_clear.sh`
(pid 63632) is watching and will relaunch it with `--sleep-min 20 --sleep-max 45`.

## Status log

- [x] copied detect.py -> detect_v3.py (original untouched, md5 c8c76b9bdf351e0e40957e8c160208f0)
- [x] implement alignment-based assignment
- [x] synthetic unit checks (23/23)
- [x] pilot regression — 194/194, 8/8, 0 violations, byte-identical
- [x] throughput — +0.6%
- [~] validate 22 — **9 done** (7 pass, 2 shown to be title errors), **13 blocked** on the bot-block
- [ ] visual verification of an *illegible-title* recovery (SdCCiUurF68 L3462) — video already deleted,
      needs a re-download. The three *out-of-range* recoveries were verified visually; this is the one
      recovery class where I have numeric agreement but no picture.

## Handover

`src/detect_v3.py` is complete and ready to swap in. `src/detect.py` is untouched
(md5 `c8c76b9bdf351e0e40957e8c160208f0`, mtime 15:59, unchanged since before this work).
`README.md` gained one row in the flags table for `level_from_position`; nothing else was modified.
Scratch artefacts left in `/tmp/v3work` (`cmp.py`, `test_align.py`, `blind.py`, logs) and
`/tmp/v3out` (detect JSON for the 9 validated videos + both pilot sweeps).
