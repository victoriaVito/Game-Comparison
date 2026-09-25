# Royal Match Level Archive — Research Learnings

Status: consolidated repository learning  
Last reviewed: 2026-09-23  
Repository: https://github.int.midasplayer.com/tauseen-syed/royal-match-level-archive  
Reviewed revision: `4837acf`

## Local Source and Refresh Policy

The repository is available locally at `sources/royal-match-level-archive` as a partial clone with a persistent sparse working tree. The working tree includes `README.md`, `docs/`, `index.html`, `manifest.json`, and the complete `levels/` image directory. Each board remains at its canonical path, such as `levels/00018/board.jpg`, so the local UI and manifest work without path rewriting.

An automated daily check compares the local revision with upstream `main`. When a new commit is detected, it may fast-forward a clean working tree, materialize new or changed files under `levels/`, review material documentation and interface changes, and update this note. It must verify that the number of local `board.jpg` files matches `manifest.count`, remain silent when upstream is unchanged, and stop rather than overwrite local edits or use destructive Git operations.

## Objective

Capture the verified structure, purpose, quality model, and open questions of the internal Royal Match level archive so later analysis can start from an auditable baseline.

## What the Archive Is

The project is a browsable internal reference archive of Royal Match level boards. Each captured image represents the board immediately before the player's first move. The published repository is a reduced distribution intended for browsing; the full production archive also retains additional verification material.

The dataset was derived from a public YouTube gameplay playlist containing 704 videos and approximately 358 hours of footage. Video titles encode level ranges, and levels appear in ascending order. The extraction pipeline uses those properties as independent ground truth rather than trusting OCR alone.

## Observed Published UI

The published GitHub Pages interface was observed loading successfully without an additional login prompt. It presented:

- 13,087 captured levels out of a displayed denominator of 13,270 (98.6%).
- 3,022 flagged entries.
- 150 low-confidence entries.
- 412 missing levels.
- 30 coverage gaps.
- Compact, Normal, and Large density controls.
- A filter for flagged or low-confidence levels.
- Direct navigation to a level number.
- A virtualized grid of numbered level cards.

The level cards initially appeared black or empty in the observed capture. This may reflect lazy image loading, render timing, or an asset-loading issue; it was not diagnosed from the screenshot alone.

## Repository Findings

The repository is readable through the authenticated local Git environment. The integrated web reader could not access the internal domain, but `git ls-remote` and a partial shallow clone succeeded.

The reduced repository contains:

- `index.html`: the self-contained archive interface.
- `docs/playlist.json`: source playlist metadata.
- `docs/SPEC.md`: extraction and UI contracts plus revision history.
- `docs/STATUS.md`: completion metrics and validation results.
- `docs/NOTES_*.md`: focused defect investigations.
- `levels/<level>/board.jpg`: one board image per published level.

The repository reports Python as the primary implementation language and HTML as the secondary language. The reduced published copy is primarily a static browsing artifact; the full extraction pipeline described in the specification is not included in this reduced repository snapshot.

## Dataset and Coverage

The repository documentation reports:

- 13,087 published board screenshots.
- 100% coverage of the levels that the source playlist actually contains.
- A nominal level span from 2 through 13,500.
- 411 levels not covered by any source video.
- Level 11,565 named by a source video but never played in the footage.
- 704 source videos processed with no reported processing failures.
- Published board resolution of 414 × 896 pixels.

The full archive is documented as approximately 8.89–9.1 GB with 65,390 files. The reduced GitHub Pages copy omits play-dialog screenshots and per-level verification clips to remain within the hosting size limit.

## Extraction Method

The core pipeline is described as:

1. Parse playlist metadata and expected level ranges.
2. Download one video at a time.
3. Detect play dialogs, board appearance, reward animations, and the first move.
4. Select the last settled board frame strictly before the first move.
5. Extract and validate the frame.
6. Delete the source video to keep peak disk use small.
7. Write a resumable checkpoint and continue.

The important design decision is to anchor frame selection on the first move and walk backward to a valid settled frame. This prevents the archive from capturing the board too early, during booster or reward animation, or after gameplay has begun.

OCR is cross-checked against the expected chronological sequence. A failed or contradictory OCR result should be flagged and recovered positionally rather than silently dropping the level.

## Detector Architecture and Why It Works

The detector follows a coarse-to-precise architecture designed around the economics of 358 hours of video:

1. A cheap low-resolution pass samples the full video and classifies candidate play-dialog, board, and other-screen runs without writing frame images to disk.
2. A bounded refine pass re-decodes only candidate transition windows at higher temporal and spatial resolution.
3. A native-frame-rate precision pass establishes the first irreversible Moves-counter change and walks backward to the last settled pre-move frame.
4. Independent level-number evidence combines OCR, title-derived ranges, chronological order, and plausibility checks.
5. A geometry check distinguishes a real game-board header from visually similar feature, map, dialog, and operating-system screens.

This is a general pattern for long-video extraction: use cheap signals to reduce the search space, then spend precision only around decision boundaries. The most reliable anchor is not “the board looks still”; it is a state transition with gameplay semantics. The Moves counter changes when the swipe registers, approximately 0.17 seconds before visible piece motion in the measured example, making it a safer first-move boundary than board animation.

The settled pre-move window may be only one or two native source frames. A coarse 12 fps grid can miss it entirely, so exact correctness depends on a native-rate pass. The final timestamp is deliberately biased toward the earlier safe side when source seeking and frame timestamps disagree by a fraction of a frame.

## Reward and Booster Animation Findings

The investigated start-of-level animation is a pre-selected booster, not a level reward: a crimson royal hat enters the board, hops and converts pieces into power-ups without decrementing Moves.

In the eight-video, 194-level pilot:

- It appeared in 152 of 194 levels (78%).
- It appeared in 0 of 29 levels from the oldest 2021 recording and about 92% of the later-session levels.
- One visual variant was observed across the sample.
- Duration was quantized but recording-dependent, clustering around 2.25, 2.60, and 3.40 seconds.
- A single global duration constant would therefore be wrong for a substantial part of the corpus.

The robust solution does not require perfect booster recognition. It anchors on the first move and searches backward, which selects the later settled window after the booster by construction. Booster detection remains useful for reporting and fallback behavior, but it is not the primary correctness mechanism.

This yields a transferable design principle: when an intermediate animation is diverse or difficult to classify, anchor the decision on a later invariant state transition and derive the desired frame relative to it.

## Quality and Verification Model

The archive distinguishes inclusion from confidence. Flagged levels remain visible and reviewable instead of being excluded.

Documented flag categories include:

- Reward-animation uncertainty.
- Short settled-board windows.
- No post-reward still frame.
- Source-title count mismatch.
- Retry attempts.
- OCR and sequence disagreement.
- Level numbers recovered from position.
- Tutorial overlays.
- Late board anchors and other guarded fallbacks.

The final status document reports zero known cases where the selected board timestamp is at or after the first move, and zero saved images failing the real-board validation. These are repository claims backed by the project's recorded audits; they were not independently recomputed during this review.

### Confidence Is Evidence, Not Decoration

Confidence and flags express why an entry deserves review; they do not determine whether it exists. The project consistently favors a visible, lower-confidence result over silent data loss. Examples include positional level recovery, uncertain animation boundaries, short settled windows, tutorial overlays, retry attempts, and title-count disagreement.

The same principle applies to source conflicts. If OCR is strongly sequential but a video title implies an implausible density, the system trusts the coherent observed sequence and flags the title mismatch rather than fabricating missing levels. One title claimed 201 levels in 32.4 minutes, while the footage consistently showed levels 1,551–1,571; plausibility and internal consistency outweighed the nominal title range.

### Validation Layers

The repository demonstrates four complementary validation layers:

- **Structural invariants:** timestamps remain ordered, level identities remain unique, and source-to-output mappings remain consistent.
- **Deterministic visual checks:** board-header geometry, Moves-counter changes, pixel comparison, and disk/manifest consistency.
- **Regression corpora:** an eight-video, 194-level pilot spanning different UI eras and edge cases.
- **Human visual review:** contact sheets and frame-by-frame inspection of representative and anomalous cases.

No single layer was sufficient. Automated audits missed a whole UI era producing zero levels and accepted valid-looking feature screens as boards; both classes were discovered through inspection of real outputs. Conversely, human inspection alone would not scale to 13,087 levels or prove archive-wide invariants.

## Important Defects Previously Found

The project history records several defects that materially shaped the current design:

- Frames selected during reward or booster animations.
- Board appearance detected after the first move.
- Chosen-frame timeline markers offset from the actual saved frame.
- Sub-millisecond timestamp rounding selecting the wrong source frame.
- Levels silently dropped after OCR failure.
- An entire UI era rejected because an event banner displaced the title anchor.
- Feature or map screens saved instead of boards after a dialog was closed and reopened.
- Board frames captured too early because the Moves reference was sampled while the header was still rendering.

Two defects were found only through human inspection of real output, demonstrating that aggregate counts and automated validation are necessary but insufficient evidence of visual correctness.

## Root-Cause Lessons from the Defects

### 1. Detect semantic transitions, not visual proxies

Board texture, motion, and header presence were useful signals but unreliable primary anchors. Animated props, tutorial dimming, partial boards, UI slide-ins, and non-game screens could satisfy those visual heuristics. The Moves transition supplied the semantic boundary that the image-level proxies lacked.

### 2. Never let one recognition system erase evidence

OCR failures originally caused detected dialogs to disappear. Chronological position, neighboring OCR results, expected ranges, and density plausibility provide independent evidence. Recovery remains flagged and lower-confidence, but the observation is retained.

### 3. Structural fallbacks need refusal conditions

A blind positional workaround once assigned the wrong dialogs to levels. The safer fallback promotes structurally valid play dialogs only when counts and surrounding evidence agree; otherwise it declines to guess. Lower recall is preferable to silent mis-attribution.

### 4. UI landmarks drift across eras

An event banner above the play dialog displaced the assumed title crop and caused 18 consecutive videos to yield zero levels. Stable landmarks such as the Play button, close button, side rails, and “Select Boosters” caption are stronger anchors than a panel's top edge.

### 5. “Looks like a board” is not equivalent to “is the playable board”

Feature panels, the castle map, a Royal Hammer overlay, a play dialog, and even the iOS home screen matched an overly broad board classifier. Moves-plate geometry and temporal context were needed to distinguish genuine boards, while tutorial-dimmed boards required explicit known-good handling.

### 6. Store measured identity instead of re-deriving it

The UI originally derived a chosen video-frame index from a floating-point timestamp. Resampling the source video to a 10 fps verification clip changed the frame grid, making rounding wrong for most pilot levels. The corrected design pixel-matches `board.jpg` against nearby clip frames and stores the resulting integer `board_frame_idx`.

### 7. Rare-case guards should not perturb the healthy path

A first implementation of the early-move guard changed healthy pilot levels. The final design runs the established path first and activates the guard only when the result violates a physical invariant. This is a strong general rule for mature pipelines: exceptional-case fixes should be conditional fallbacks with byte-level regression checks.

### 8. Repair locally when the defect is local

For a small set of bad boards, the project downloaded bounded video sections rather than entire source videos. Fifteen repaired levels required roughly 500 MB instead of an estimated 7.5 GB, while preserving source-time offsets and re-verifying each derived artifact. Surgical remediation reduces bandwidth, runtime, and the chance of disturbing already-correct output.

## Operational Learnings

- The pipeline is resumable and checkpointed per source video; transient download failures must never be persisted as successful checkpoints.
- Video files are deleted after extraction to bound peak disk use.
- Concurrent or manual YouTube downloads can trigger IP bot protection. The successful final pacing was one download at a time with long randomized delays.
- Repeated retries during a block make recovery worse. The recorded response was to stop, cool down, and probe sparingly rather than attempt cookie or client workarounds.
- Process-detection and error-signature guards themselves need tests: a `pgrep` pattern matched its own shell, and a bare `429` detector falsely matched an ffmpeg bitrate string.
- Temporary section downloads retain explicit offset sidecars because section time starts at zero and must be converted back to source time before any canonical timestamp is written.
- Repairs back up original screenshots, clips, sidecars, and detection JSON before replacement, enabling audit and rollback without destructive Git operations.

## Published Interface Learnings

The UI is a single self-contained HTML document with no build step or CDN dependency. It demonstrates several useful patterns for large visual archives:

- Virtualize the grid instead of creating more than 13,000 live image cards.
- Lazy-load screenshots and attach verification-video sources only while a detail view is open.
- Clear video sources on close to release resources.
- Preserve deep links through `#L<level>` URLs.
- Treat missing levels as explicit navigable states with source-video context instead of silently skipping them.
- Persist lightweight display preferences locally.
- Keep frame identity integer-based and display whether the current scrubbed frame is the saved chosen frame.
- Provide graceful degradation when verification clips are absent in the reduced hosted copy.

The product-design lesson is that uncertainty is part of the browsing experience: filters, confidence, flags, missing ranges, provenance, and verification controls make the corpus inspectable rather than presenting every image as equally authoritative.

## Level-Design Learnings Available from the Corpus

The archive can support a visual taxonomy of Royal Match level construction, including:

- Board silhouette, usable-space distribution, symmetry, compartments, corridors, and disconnected regions.
- Initial color distribution and the visible placement of blockers, targets, generators, and special elements.
- Tutorial overlays and the evolution of onboarding presentation across level eras.
- Recurring structural motifs and how frequently they reappear across level bands.
- Changes in board presentation and UI eras across the level sequence.
- The relationship between pre-selected boosters and the actual initial playable state.
- Candidate outliers for qualitative review, especially levels with unusual geometry or extraction flags.

These observations can generate hypotheses about pacing, complexity, novelty, and content reuse, but screenshots alone cannot validate difficulty, intended solution, move economy, random generation, spawn probabilities, win rate, fail reasons, or player experience. Those require gameplay telemetry, configuration data, or full video analysis.

## Derived Analysis App

A local derived app is served separately from the synchronized source repository. It preserves the original archive behavior and adds filters backed by `analysis/features.json`:

- Tutorial versus non-tutorial, using the repository's `tutorial_overlay` evidence.
- One, two, three, four, or unresolved visible target counts.
- Difficulty with an explicit `unknown` state; Normal, Hard, and Super Hard remain disabled until play-dialog evidence is available.

Target counts are extracted from the stable Target panel using macOS Vision OCR. A conservative visual-layout fallback resolves four-target panels when OCR reads only one overlaid quantity. Every result stores its method and confidence, and unresolved captures remain visible instead of being forced into a class.

The first 30-level pilot produced 29 correct target counts under visual review and one justified unresolved result: level 20 shows a Reward screen rather than a readable Target panel. The full pass currently resolves 11,696 of 13,087 levels and leaves 1,391 unresolved. This is a useful browsing index, not yet a ground-truth label set; stratified validation across UI eras is still required before using aggregate distributions as design evidence.

## Evidence Chronology

The source documents have different authority and timestamps:

- `NOTES_*.md` preserve investigations as they happened, including partial validation, blocked downloads, intermediate failures, and superseded implementation states.
- `SPEC.md` records evolving requirements and acceptance criteria.
- `STATUS.md` and `README.md` present the final repository claim: 13,087 captured boards, complete coverage of available footage, zero ordering violations, and zero invalid published board images.

Historical notes must therefore be read as provenance, not automatically as current state. For example, `NOTES_bad_boards.md` records a point where 15 of 17 identified boards were repaired and two remained blocked; the later final status reports the completed archive-wide validation. The note remains valuable because it explains the defect class, remediation, regression caught during implementation, and verification method.

## Current Interpretation

The archive is best treated as a high-coverage visual reference corpus, not as raw game configuration data. It provides screenshots, provenance, confidence signals, and source timestamps, but it does not expose the underlying level-design parameters or authoritative runtime representation.

Its strongest analytical uses are:

- Visual comparison of board layouts across level ranges.
- Identification of recurring board structures and UI eras.
- Manual review of flagged or low-confidence captures.
- Sampling boards for qualitative level-design research.
- Linking a board back to the corresponding gameplay source.

The most reusable engineering conclusion is that this archive is not merely a screenshot collection. It is an evidence system: every useful artifact is tied to a source, a temporal boundary, a confidence state, a validation method, and a path for human review.

## Open Questions

1. Why does the live UI use 13,270 as its denominator while the repository documentation describes a nominal span of 13,499 levels from 2 through 13,500?
2. Why does the UI show 412 missing levels while the documentation separates 411 uncovered levels and one claimed-but-unplayed level?
3. Are the 3,022 flagged entries unique levels, or flag occurrences across 13,089 detected segments?
4. What specifically caused the observed black level cards: lazy loading, browser timing, missing assets, or a rendering defect?
5. Is the full-resolution archive accessible to this project, or only the reduced GitHub Pages distribution?

## Evidence Boundaries

- Verified directly: repository access; local and upstream `main` both at revision `4837acf`; repository file tree; playlist metadata; interface implementation; and the contents of `README.md`, `docs/STATUS.md`, `docs/SPEC.md`, and all five `docs/NOTES_*.md` investigation records.
- Reported from the observed live UI: displayed capture rate, flagged count, low-confidence count, missing count, gaps, controls, and initially black cards.
- Mechanically confirmed from `docs/playlist.json`: 704 parsed video entries plus one unparsed entry, spanning the published source sequence from levels 2–30 through 13,461–13,500.
- Not independently verified: replaying the extraction pipeline, recomputing image audits, inspecting all 13,087 images, validating source videos, accessing the separately retained full archive, or resolving historical intermediate claims against artifacts omitted from the reduced repository.
