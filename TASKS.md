# Game Level Archive — Canonical Task Tracker

Status: active  
Owner: Victoria Serrano  
Last updated: 2026-09-25 11:03 CEST  
Source of truth: this file  
External repository: https://github.com/victoriaVito/Game-Comparison

## Status model

- `planned`: accepted scope, work not started.
- `in_progress`: implementation or verification is active.
- `blocked`: progress requires an explicit dependency or decision.
- `done`: acceptance criteria are satisfied and evidence is linked.

## Active tasks

### TSK-001 — Maintain the Royal Match source mirror

Status: `blocked`  
Owner: Victoria Serrano  
Scope: Keep a complete local copy of the internal Royal Match archive, including level images and upstream changes.

Acceptance criteria:

- The local repository matches the selected upstream branch.
- All manifest-referenced level images exist locally.
- Refresh execution reports upstream changes, image completeness, and failures.
- At least one scheduled refresh is observed end to end.

Evidence:

- [`sources/royal-match-level-archive`](sources/royal-match-level-archive)
- [`docs/research/royal-match-level-archive.md`](docs/research/royal-match-level-archive.md)

Latest verification (2026-09-24 09:00 CEST): local `HEAD` and the cached `origin/main` reference both resolve to `4837acfe9684ee4fb5b3c4b64e5ef164f78b0dbe`; 13,087 board JPEGs match `manifest.count`, and a representative file has a valid JPEG signature.  
Blocker: this automation run was not permitted to execute `git fetch`, so the current upstream revision could not be verified.  
Next action: allow the scheduled task to fetch the internal GitHub remote, then repeat the revision and inventory checks.

### TSK-002 — Classify and filter Royal Match levels

Status: `in_progress`  
Owner: Victoria Serrano  
Scope: Filter levels by tutorials, target count, level type, difficulty, and reusable board patterns.

Acceptance criteria:

- Tutorial and target-count filters are available in the local archive.
- Target-count coverage and unresolved cases are reported explicitly.
- Difficulty labels are derived from valid source evidence or remain `unknown`.
- Pattern analysis has a versioned taxonomy and reviewed validation sample.

Evidence:

- [`analysis/build_features.py`](analysis/build_features.py)
- [`analysis/features.json`](analysis/features.json)
- [`app/index.html`](app/index.html)

Current evidence: 13,087 levels processed; 11 tutorials; 11,696 target counts resolved; 1,391 unresolved.  
Artifact inventory reviewed 2026-10-08: `sources/royal-match-level-archive/manifest.json` records 13,087 captured boards, 412 missing, 3,022 flagged, and 150 low-confidence; `analysis/features.json` confirms the feature counts above. No difficulty labels or pattern analysis were added.  
Agreed pilot scope (2026-10-08): review levels 1–1,000 separately for Royal Match and Royal Kingdom before scaling to further 1,000-level batches. Keep evidence-backed visual observations distinct from visual hypotheses about difficulty or strategy; preserve `unknown` where a claim cannot be supported. The initial execution ended incomplete; visual classification remains open.
Pilot input check (2026-10-08): local board images exist for both requested ranges. The Royal Kingdom source-video directory is absent from this checkout, so video-grounded difficulty and strategy labels cannot be verified locally; keep them `unknown` unless another included source directly supports them, and store image-based hypotheses separately.
Pilot run reconciled (2026-10-08): each game's candidate JSONL contains 1,000 unique numeric levels, but neither completed the requested full visual classification. Royal Match: 997 board images available, 3 absent (levels 1, 299, 300), 0 directly image-reviewed. Royal Kingdom: 1,000 images available, 6 directly image-reviewed, 994 not visually reviewed; source videos are absent. Difficulty/strategy remain unknown; no speculative hypotheses were added. Candidate outputs and reports are under `.ai-work/temporary/level-review-pilot/{royal-match,royal-kingdom}/`; they are not accepted labels. No later batches started.
Pilot audit (2026-10-09): direct image viewing works. Prepared and decoded 84 traceable 12-level contact sheets per game, retaining manifest paths and original-image hashes. Inspected the first sheet of each game (23 available images); these are not complete classifications. Direct inspection contradicts the original Royal Kingdom level 1 `split_regions` tag; a candidate correction and schema/occlusion issues are recorded in `.ai-work/temporary/level-review-pilot/audit-20261009.md`. Original candidate outputs remain preserved and unaccepted.
Pilot resumed (2026-10-10): a shared candidate-only record contract is saved at `.ai-work/temporary/level-review-pilot/review_contract.json`. The existing 1-1,000 ranges are being partitioned at sheet boundaries into 1-504 and 505-1,000 per game, with visual-inspection checkpoints, occlusion flags, and separate difficulty/strategy hypotheses. No later 1,000-level batch is authorized by this continuation.
Pilot checkpoint (2026-10-10): both Royal Match v2 shards pass `validate_reviews.py --game royal-match --verify-hashes`: 1,000 ordered records, 995 reviewed, 2 partial, and 3 missing; zero accepted labels. This validates structure and original hashes, not independent visual fidelity. Royal Kingdom 1-504 is saved with reported 483 reviewed and 21 partial, including a traceable candidate correction of level 1 to `compact_full_field`. The Royal Kingdom 505-1,000 reviewer exited without a shard after interpreting a schema clarification as its whole task; the original visual-review assignment has been explicitly resumed.
Pilot quality checkpoint (2026-10-10): all four shards now exist and pass full structural/original-hash validation. Recorded inspection counts are Royal Match 995 reviewed, 2 partial, 3 missing; Royal Kingdom 972 reviewed, 28 partial. However, the Kingdom 505-1,000 shard has only eight distinct observation templates across its 489 reviewed rows (one repeats 141 times), unlike the other three shards' image-specific descriptions. Its evidence and generic hypotheses are insufficient for completing the classification; the same reviewer has been directed to revisit the assigned sheets and save concrete per-image evidence. Summary: `.ai-work/temporary/level-review-pilot/validation-20261010.json`. No candidates are accepted.
Pilot revision checkpoint (2026-10-10): Kingdom 505-1,000 now has 496 distinct observations, all marked `needs_review`, with hypotheses removed. All four shards still pass structural and source-hash checks. A direct parent spot check of sheets 505-516 and 997-1,000 nevertheless finds remaining geometry conflicts at 507 (`split_regions` despite a connected upper grid), 999 (blocker differences do not establish disconnection), and 1,000 (`central_mass` applied to an empty central notch). These conflicts and candidate alternatives are preserved in `validation-20261010.json`; no historical labels were overwritten or accepted.
Remaining work: validate candidate geometry against actual playable boundaries, resolve the recorded conflicts and partial cases, and obtain acceptance before scaling. The visual-review outputs are saved; trustworthy classification is not yet complete.
Full archive authorization (2026-10-10): Victoria requested continuing in 1,000-level batches through the end. Scope is the existing local manifests: Royal Match through numeric level 13,500 and Royal Kingdom through 5,300. Preserve the 1-1,000 pilot and its unresolved conflicts; review the remaining 18 batches as separate candidate outputs, with sheet-sized subranges, per-image evidence, original hashes, and sampled quality review. No downloads, source modifications, accepted-label promotion, or remote publication are authorized.
Full archive workflow progress: 2026-10-10T20:54:32.618358+00:00; 18 post-pilot batches structurally validated (royal-kingdom 1001-2000; royal-kingdom 2001-3000; royal-kingdom 3001-4000; royal-kingdom 4001-5000; royal-kingdom 5001-5300; royal-match 1001-2000; royal-match 2001-3000; royal-match 3001-4000; royal-match 4001-5000; royal-match 5001-6000; royal-match 6001-7000; royal-match 7001-8000; royal-match 8001-9000; royal-match 9001-10000; royal-match 10001-11000; royal-match 11001-12000; royal-match 12001-13000; royal-match 13001-13500). Labels remain unaccepted; quality conflicts are retained in per-batch reports. Source of truth: TSK-002. No linked remote task ID is configured; no remote sync is claimed.
Archive repair checkpoint (2026-10-10): Victoria requested fixing the unfinished work. Normalized 231 absolute sheet-path aliases in Royal Match 7,001-8,000 after verifying they target exactly the indexed sheets; semantic observations and labels were unchanged. The repair audit is saved in that batch's `sheet-path-repair.json`. Full schema/source-hash validation now passes: 800 reviewed, 110 partial, 90 missing. A second normalization makes zero changes. This batch still needs sampled quality review; Match 8,001-13,500 has not yet been reviewed.
Archive continuation outcome (2026-10-10): run `c4d016de-2893-4b9b-9502-003dcca6a126` saved all 18 post-pilot batches with structural/source-hash validation and sampled quality reports; no execution blockers remain. Royal Match 1,001-13,500: 10,882 reviewed, 1,208 partial, 410 missing. Royal Kingdom 1,001-5,300: 3,907 reviewed, 393 partial, no missing. The 217 sampled cases include 68 conflicts and 27 uncertain results, preserved without label promotion. The pilot remains unchanged. Persisted handoff: `.ai-work/temporary/level-review-archive/continuation-handoff.json`. These counts describe recorded inspection, not full independent visual validation. No labels are accepted and no remote synchronization is claimed.
Next action: resolve recorded geometry conflicts and partial cases against original images, then obtain candidate acceptance. Batch coverage is saved through both archive endpoints; TSK-002 remains in progress until classification acceptance criteria are satisfied.

Adjudication tasks (same canonical task; no separate tracker):
- [x] TSK-002.A1 Build a traceable review queue from all 217 sampled quality checks and the four documented pilot geometry/correction cases. Preserve reviewer claims as unverified input; include original image/hash and candidate-row references. Queue: `.ai-work/temporary/level-review-archive/adjudication/quality-sample-queue.jsonl` (221 rows; 99 high-priority conflicts/uncertain/historical disagreements).
- [ ] TSK-002.A2 Independently inspect every sampled conflict/uncertain case plus pilot conflicts against original images. Record visible evidence, candidate disposition, confidence, and unresolved ambiguity without overwriting source candidate shards. Started: 11 direct image checks for Royal Kingdom 1, 507, 999, 1,000, 1,001, 1,126, 1,252, 1,504 and Royal Match 1,127, 1,504, 1,757 are in `direct-visual-check-001.jsonl` and `direct-visual-check-002.jsonl`; all 11 original SHA-256 hashes were verified. Candidate corrections include withholding unsupported `split_regions`, `central_mass`, `open_center`, and `edge_channels` tags, correcting concrete observation wording, and retaining partial/uncertain cases. None are accepted.
- [ ] TSK-002.A3 Reconcile geometry definitions only where inspected examples support a precise clarification. Keep proposed taxonomy changes versioned and candidate; preserve disagreements and request owner acceptance before promotion.
- [ ] TSK-002.A4 Triage all recorded partial and missing levels against available evidence. Resolve only when an original image supports it; otherwise retain explicit partial/missing status and report coverage. Local search (2026-10-13) examined 18,569 repository image files and 118 manifests, excluding generated review sheets; no alternate local capture was found for the 413 missing Royal Match levels, and Royal Kingdom has zero missing levels. Following Victoria's authorization for public-source discovery using metadata only, 101 YouTube oEmbed records were checked for title-matched leads covering all 413 missing Royal Match level numbers, including level 1 outside the manifest range. This does not verify video contents, accessible frames, reuse rights, or a usable screenshot. A YouTube page for Royal Match levels 291-300 was opened in the browser; its visible chapters identify level 299 at 21:19 and level 300 at 24:45. Link saved in the source report as a research lead; the page did not show an explicit reuse license, so the video was not downloaded and no frame was extracted. A review of YouTube's published Terms of Service identified restrictions on automated access and reuse; the prior metadata method's authorization and any screenshot reuse basis have not been determined. A follow-up search for sources with explicit download/reuse terms confirmed five Wikimedia Commons files, including level screenshots 1300 and 2102 under CC BY-SA 4.0 with a VRT permission-confirmed notice; neither matches a missing level. Do not acquire video media without an explicitly permitted method and applicable rights. Catalog: `.ai-work/temporary/level-review-archive/missing-capture-public-sources.csv`; report: `.ai-work/temporary/level-review-archive/missing-capture-public-source-report.md`; local-search evidence: `.ai-work/temporary/level-review-archive/missing-capture-local-search.json`.
- [ ] TSK-002.A5 Produce a candidate-only export with provenance, open conflicts, missing/partial coverage, and unknown difficulty/strategy; have Victoria review before any acceptance or app integration.

Execution checkpoint (2026-10-13): A1 is complete and A2 is in progress. Direct image checks confirm that visible Royal Kingdom 507/999 do not show an empty separating gap, level 1,000 has an empty notch rather than a central blocker mass, and level 1,126's lower-center opening exits at the board boundary rather than forming an enclosed central hole. Royal Match 1,127's object rails do not by themselves prove playable edge channels. Other reviewed samples surfaced description corrections and an occluded partial board. The tutorial overlay at level 1 prevents full inspection; level 1,001 remains ambiguous. These are candidate adjudications, not accepted labels. No canonical tags were accepted and taxonomy/source/app files remain unchanged.
Missing-capture search checkpoint (2026-10-13): local search found no alternate Royal Match images; 412 manifest gaps plus level 1 yield 413 absent captures. Following explicit authorization for public-source discovery without downloads or frame extraction, 101 YouTube oEmbed records were checked and title-matched leads were cataloged for all 413 missing level numbers. Each record includes the returned title and author, and its claimed range endpoints match the title. A follow-up search for sources with clear download/reuse terms verified two Wikimedia Commons level screenshots under CC BY-SA 4.0 with VRT permission confirmation, but their levels (1300 and 2102) are not missing. A YouTube 291-300 lead surfaced, but no reuse license was verified. No video content was opened, no media was downloaded, and no image was obtained. See `.ai-work/temporary/level-review-archive/missing-capture-public-source-report.md` and `.ai-work/temporary/level-review-archive/missing-capture-public-sources.csv`.

### TSK-005 — Scale the Royal Kingdom archive beyond the pilot

Status: `done`  
Owner: Victoria Serrano  
Scope: Extend the verified extraction pipeline from levels 1–15 to the available Royal Kingdom playlist.

Acceptance criteria:

- Playlist inventory is captured with source provenance and duplicate detection.
- Processing is incremental and bounded by available disk space.
- Every extracted level retains source URL, timestamp, type, confidence, and review status.
- Missing, ambiguous, and failed levels remain visible in coverage reporting.
- The local browser updates from the expanded manifest without manual duplication.

Dependencies:

- TSK-003 pilot extraction.
- TSK-004 agent team and publication gate.

Current evidence:

- Best-supported main-level cap on 2026-09-24: 5,300.
- RasyaPlaysRK range videos cover all levels 1–5,300 after correcting the advertised end level of video `Cq-Y_rnbYis` from 3,460 to 3,560.
- Media-integrity validation confirmed that `Cq-Y_rnbYis` yields the complete levels 3,541–3,560 sequence; the previously selected Royal Mania fallback yielded only level 3,541 and was rejected.
- Complete title-level video coverage is available from RasyaPlaysRK, with the corrected-title exception preserved explicitly in the source inventory.
- M1 is complete: levels 1–100 are published with 100 board JPEGs, exact manifest coverage, source URL and timestamp provenance, and visual-review status.
- The levels 16–100 calibration batch reconciles to 85 accepted, 0 ambiguous, 0 failed, and 0 missing; levels 41, 51, 61, and 91 were recaptured after review rejected item-unlock screens.
- Valid image-size variants are 404×720 for the 15-level pilot and 95 individual recaptures, and 405×720 for the remaining 5,190 boards; all 5,300 JPEGs decode correctly and no additional dimensions are present.
- The production source catalog selects 256 bounded sources and covers the exact sequence 101–5,300; the 3,541–3,560 range uses the media-validated RasyaPlaysRK corrected-title source.
- Levels 101–200 are published and fully visually reviewed; the first-move selector was recalibrated to wait through pre-level booster animations while preserving the initial move count.
- M2 is reconciled through level 500: 500 published, 0 missing, 0 failed, and 0 unresolved ambiguities. The five booster-animation exceptions (211, 291, 371, 379, 380) were replaced from independently verified no-booster sources during M3.
- M3 is complete: continuous coverage and stratified visual review are reconciled through level 1,200.
- Continuous coverage and stratified visual review now extend through level 1,300; levels 1,201-1,300 passed the 40-level sample without recaptures or unresolved exceptions.
- Continuous coverage and stratified visual review now extend through level 1,400; levels 1,301-1,400 passed after Magic Pot captures at 1,350 and 1,367 were replaced from verified no-booster sources.
- Continuous coverage and stratified visual review now extend through level 1,500; levels 1,401-1,500 passed after Magic Pot captures at 1,419 and 1,440 were replaced from verified no-booster sources.
- Continuous coverage and stratified visual review now extend through level 1,600; levels 1,501-1,600 passed after ten Power Rush captures were replaced from verified Royal Kingdom no-booster sources.
- Continuous coverage and stratified visual review now extend through level 1,700; levels 1,601-1,700 passed the 40-level sample without recaptures or unresolved exceptions.
- Continuous coverage and stratified visual review now extend through level 1,800; levels 1,701-1,800 passed an independent 40-level sample without recaptures or unresolved exceptions.
- Continuous coverage and stratified visual review now extend through level 1,900; levels 1,801-1,900 passed an independent 40-level sample without recaptures or unresolved exceptions.
- Continuous coverage and stratified visual review now extend through level 2,000; levels 1,901-2,000 passed an independent 40-level sample without recaptures or unresolved exceptions.
- Continuous coverage and stratified visual review now extend through level 3,000; levels 2,001-2,100 passed an independent 40-level sample without recaptures, the bounded levels 1,061-2,100 extraction process completed successfully, and the previously reviewed levels 2,101-3,000 close M4 without gaps.
- Levels 501-600 passed a 40-level stratified visual review after six Magic Pot captures (530, 551, 571, 580, 587, 591) were replaced from independently verified no-booster sources.
- Levels 601-700 passed a 40-level stratified visual review after three Magic Pot captures (607, 615, 630) were replaced from independently verified no-booster sources.
- Levels 701-800 passed a 40-level stratified visual review after six Power Rush captures (705, 710, 720, 725, 745, 750) and one Magic Pot capture (727) were replaced from independently verified no-booster sources.
- Levels 801-900 passed a 40-level stratified visual review after two Magic Pot captures (879, 883) were replaced from independently verified no-booster sources.
- Levels 901-1,000 passed a 40-level stratified visual review after two Magic Pot captures (945, 963) were replaced with initial pre-move frames from independently verified no-booster sources.
- Levels 1,001-1,100 passed a 40-level stratified visual review without recaptures or unresolved exceptions.
- Levels 1,101-1,200 passed a 40-level stratified visual review after the Magic Pot capture at 1,143 was replaced from a verified no-booster source.
- The independently completed levels 2,101-2,200 block passed a 40-level stratified visual review after Magic Pot captures at 2,139 and 2,179 were replaced from verified no-booster sources; this does not advance the continuous-prefix milestone.
- The independently completed levels 2,201-2,300 block passed a 40-level stratified visual review after the invalid `My Team` screen at 2,283 was replaced with the initial pre-move frame from a verified no-booster source; this does not advance the continuous-prefix milestone.
- The independently completed levels 2,301-2,400 block passed a 40-level stratified visual review after nine Magic Pot or active-effect captures were replaced with initial pre-move frames from verified no-booster sources; this does not advance the continuous-prefix milestone.
- The independently completed levels 2,401-2,500 block passed a 40-level stratified visual review after Magic Pot captures at 2,460 and 2,487 were replaced from verified no-booster sources; this does not advance the continuous-prefix milestone.
- The independently completed levels 2,501-2,600 block passed a 40-level stratified visual review without recaptures or unresolved exceptions; this does not advance the continuous-prefix milestone.
- The independently completed levels 2,601-2,700 block passed a 40-level stratified visual review without recaptures or unresolved exceptions; this does not advance the continuous-prefix milestone.
- The independently completed levels 2,701-2,800 block passed a 40-level stratified visual review without recaptures or unresolved exceptions; this does not advance the continuous-prefix milestone.
- The independently completed levels 2,801-2,900 block passed an independent 40-level stratified visual review without recaptures or unresolved exceptions; this does not advance the continuous-prefix milestone.
- The independently completed levels 2,901-3,000 block passed an independent 40-level stratified visual review without recaptures or unresolved exceptions; M4 remains open until levels 1,901-2,100 complete the continuous prefix.
- The independently completed levels 3,001-3,100 block passed an independent 40-level stratified visual review without recaptures or unresolved exceptions; the bounded levels 2,501-3,040 extraction process completed successfully.
- The independently completed levels 3,101-3,200 block passed a 40-level stratified visual review without recaptures or unresolved exceptions.
- The independently completed levels 3,201-3,300 block passed a 40-level stratified visual review after the Magic Pot capture at 3,220 was replaced from a verified no-booster source.
- The independently completed levels 3,301-3,400 block passed a 40-level stratified visual review after five Magic Pot captures were replaced from verified Royal Kingdom no-booster sources.
- The independently completed levels 3,401-3,500 block passed a 40-level stratified visual review after the Magic Pot capture at 3,463 was replaced from a verified Royal Kingdom no-booster source.
- The independently completed levels 3,501-3,600 block passed a 40-level stratified visual review after the active-effect capture at 3,511 was replaced from a verified Royal Kingdom no-booster source; the reviewed block includes the corrected-title range 3,541-3,560.
- The independently completed levels 3,601-3,700 block passed an independent 40-level stratified visual review without recaptures or unresolved exceptions.
- The independently completed levels 3,701-3,800 block passed an independent 40-level stratified review after five active-effect captures (3,755, 3,759, 3,763, 3,767, and 3,779) were replaced from verified Royal Kingdom no-booster sources.
- The independently completed levels 3,801-3,900 block passed an independent 40-level stratified review after five active-effect captures (3,835, 3,863, 3,865, 3,867, and 3,879) were replaced from verified Royal Kingdom no-booster sources.
- The independently completed levels 3,901-4,000 block passed an independent 40-level stratified review after the active Power Rush capture at 3,995 was replaced from a verified Royal Kingdom no-booster source.
- Continuous coverage and stratified visual review now extend through level 4,100; levels 4,001-4,100 passed an independent 40-level stratified review after active Power Rush captures at 4,019, 4,079, and 4,091 were replaced from verified Royal Kingdom no-booster sources.
- Continuous coverage and stratified visual review now extend through level 4,200; levels 4,101-4,200 passed after the blurred capture at 4,111 was replaced and dedicated sources confirmed that the visible beams at 4,105, 4,150, 4,180, and 4,195 are persistent board mechanics.
- Continuous coverage and stratified visual review now extend through level 4,300; levels 4,201-4,300 passed after Power Rush animation captures at 4,247, 4,287, and 4,299 were replaced with stable pre-move frames from alternate Royal Kingdom sources.
- The independently completed levels 4,301-4,400 block passed a 40-level stratified visual review after Magic Pot captures at 4,307, 4,323, 4,339, and 4,343 were replaced from verified no-booster sources.
- OCR recovery for level 4,404 now accepts one noisy token before an otherwise exact level label; the corrected rule rebuilt the complete 4,401-4,420 sequence before extraction resumed.
- The independently completed levels 4,401-4,500 block passed a 40-level stratified visual review after Magic Pot captures at 4,407 and 4,463 were replaced from verified no-booster sources.
- The independently completed levels 4,501-4,600 block passed a 40-level stratified visual review after five Magic Pot captures were replaced from verified Royal Kingdom no-booster sources.
- The independently completed levels 4,601-4,700 block passed a 40-level stratified visual review without recaptures or unresolved exceptions.
- The independently completed levels 4,701-4,800 block passed a 40-level stratified visual review without recaptures; the source timeline confirmed that the large cloud at level 4,750 is the persistent Dark Kingdom objective rather than an active booster overlay.
- The independently completed levels 4,801-4,900 block passed an independent 40-level stratified visual review without recaptures; full-resolution review confirmed that the cloud counter at level 4,875 is an intentional level mechanic.
- The independently completed levels 4,901-5,000 block passed an independent 40-level stratified visual review without recaptures or unresolved exceptions.
- The independently completed levels 5,001-5,100 block passed an independent 40-level stratified visual review without recaptures; the sampled cloud-covered board was confirmed as an intentional counted level mechanic.
- The independently completed levels 5,101-5,200 block passed an independent 40-level stratified review after the destruction-animation capture at 5,147 was replaced from a verified Royal Kingdom no-booster source.
- The independently completed levels 5,201-5,300 block passed an independent 40-level stratified review without recaptures; the bounded levels 4,401-5,300 extraction process completed successfully, and full-resolution review confirmed the localized glow at 5,267 does not obscure the board or HUD.
- All four lock-protected extraction ranges for levels 1,061-5,300 completed successfully; atomic manifest publication was verified with eight concurrent writers before scaling.
- The shared Swift frame scanner is reused when current, avoiding concurrent recompilation races; no-booster publication now validates every staged replacement before copying any board image.
- Media validation corrected a source-title typo from `3041-3460` to `3041-3060`; the regenerated catalog now selects the twenty verified 20-level videos for 3061-3460 and remains exactly contiguous through 5,300.
- Pattern taxonomy v1 is calibrated on 20 reviewed level examples and restricted to observable board geometry; difficulty and strategy inference remain out of scope.
- DASH/HTTPS downloads are now preferred and unavailable fragments abort the source before OCR or publication.
- The local browser manifest updates incrementally at `http://127.0.0.1:8767/`.

Evidence:

- [`royal-kingdom/analysis/source_inventory.json`](royal-kingdom/analysis/source_inventory.json)
- [`royal-kingdom/manifest.json`](royal-kingdom/manifest.json)
- [`royal-kingdom/analysis/review_0016_0100.json`](royal-kingdom/analysis/review_0016_0100.json)
- [`royal-kingdom/analysis/batch_sources_0016_0100.json`](royal-kingdom/analysis/batch_sources_0016_0100.json)
- [`royal-kingdom/analysis/range_source_catalog.json`](royal-kingdom/analysis/range_source_catalog.json)
- [`royal-kingdom/analysis/archive_progress.json`](royal-kingdom/analysis/archive_progress.json)
- [`royal-kingdom/analysis/pattern_taxonomy_v1.json`](royal-kingdom/analysis/pattern_taxonomy_v1.json)
- [`royal-kingdom/reviews/review-m2-0001-0500.json`](royal-kingdom/reviews/review-m2-0001-0500.json)
- [`royal-kingdom/analysis/no_booster_recaptures_m3.json`](royal-kingdom/analysis/no_booster_recaptures_m3.json)
- [`royal-kingdom/reviews/review-sample-0501-0600.json`](royal-kingdom/reviews/review-sample-0501-0600.json)
- [`royal-kingdom/reviews/review-sample-0601-0700.json`](royal-kingdom/reviews/review-sample-0601-0700.json)
- [`royal-kingdom/reviews/review-sample-0701-0800.json`](royal-kingdom/reviews/review-sample-0701-0800.json)
- [`royal-kingdom/reviews/review-sample-0801-0900.json`](royal-kingdom/reviews/review-sample-0801-0900.json)
- [`royal-kingdom/reviews/review-sample-0901-1000.json`](royal-kingdom/reviews/review-sample-0901-1000.json)
- [`royal-kingdom/reviews/review-sample-1001-1100.json`](royal-kingdom/reviews/review-sample-1001-1100.json)
- [`royal-kingdom/reviews/review-sample-1101-1200.json`](royal-kingdom/reviews/review-sample-1101-1200.json)
- [`royal-kingdom/reviews/review-sample-1201-1300.json`](royal-kingdom/reviews/review-sample-1201-1300.json)
- [`royal-kingdom/reviews/review-sample-1301-1400.json`](royal-kingdom/reviews/review-sample-1301-1400.json)
- [`royal-kingdom/reviews/review-sample-1401-1500.json`](royal-kingdom/reviews/review-sample-1401-1500.json)
- [`royal-kingdom/reviews/review-sample-1501-1600.json`](royal-kingdom/reviews/review-sample-1501-1600.json)
- [`royal-kingdom/reviews/review-sample-1601-1700.json`](royal-kingdom/reviews/review-sample-1601-1700.json)
- [`royal-kingdom/reviews/review-sample-1701-1800.json`](royal-kingdom/reviews/review-sample-1701-1800.json)
- [`royal-kingdom/reviews/review-sample-1801-1900.json`](royal-kingdom/reviews/review-sample-1801-1900.json)
- [`royal-kingdom/reviews/review-sample-1901-2000.json`](royal-kingdom/reviews/review-sample-1901-2000.json)
- [`royal-kingdom/reviews/review-sample-2001-2100.json`](royal-kingdom/reviews/review-sample-2001-2100.json)
- [`royal-kingdom/reviews/review-sample-2101-2200.json`](royal-kingdom/reviews/review-sample-2101-2200.json)
- [`royal-kingdom/reviews/review-sample-2201-2300.json`](royal-kingdom/reviews/review-sample-2201-2300.json)
- [`royal-kingdom/reviews/review-sample-2301-2400.json`](royal-kingdom/reviews/review-sample-2301-2400.json)
- [`royal-kingdom/reviews/review-sample-2401-2500.json`](royal-kingdom/reviews/review-sample-2401-2500.json)
- [`royal-kingdom/reviews/review-sample-2501-2600.json`](royal-kingdom/reviews/review-sample-2501-2600.json)
- [`royal-kingdom/reviews/review-sample-2601-2700.json`](royal-kingdom/reviews/review-sample-2601-2700.json)
- [`royal-kingdom/reviews/review-sample-2701-2800.json`](royal-kingdom/reviews/review-sample-2701-2800.json)
- [`royal-kingdom/reviews/review-sample-2801-2900.json`](royal-kingdom/reviews/review-sample-2801-2900.json)
- [`royal-kingdom/reviews/review-sample-2901-3000.json`](royal-kingdom/reviews/review-sample-2901-3000.json)
- [`royal-kingdom/reviews/review-sample-3001-3100.json`](royal-kingdom/reviews/review-sample-3001-3100.json)
- [`royal-kingdom/reviews/review-sample-3101-3200.json`](royal-kingdom/reviews/review-sample-3101-3200.json)
- [`royal-kingdom/reviews/review-sample-3201-3300.json`](royal-kingdom/reviews/review-sample-3201-3300.json)
- [`royal-kingdom/reviews/review-sample-3301-3400.json`](royal-kingdom/reviews/review-sample-3301-3400.json)
- [`royal-kingdom/reviews/review-sample-3401-3500.json`](royal-kingdom/reviews/review-sample-3401-3500.json)
- [`royal-kingdom/reviews/review-sample-3501-3600.json`](royal-kingdom/reviews/review-sample-3501-3600.json)
- [`royal-kingdom/reviews/review-sample-3601-3700.json`](royal-kingdom/reviews/review-sample-3601-3700.json)
- [`royal-kingdom/reviews/review-sample-3701-3800.json`](royal-kingdom/reviews/review-sample-3701-3800.json)
- [`royal-kingdom/reviews/review-sample-3801-3900.json`](royal-kingdom/reviews/review-sample-3801-3900.json)
- [`royal-kingdom/reviews/review-sample-3901-4000.json`](royal-kingdom/reviews/review-sample-3901-4000.json)
- [`royal-kingdom/reviews/review-sample-4001-4100.json`](royal-kingdom/reviews/review-sample-4001-4100.json)
- [`royal-kingdom/reviews/review-sample-4101-4200.json`](royal-kingdom/reviews/review-sample-4101-4200.json)
- [`royal-kingdom/reviews/review-sample-4201-4300.json`](royal-kingdom/reviews/review-sample-4201-4300.json)
- [`royal-kingdom/reviews/review-sample-4301-4400.json`](royal-kingdom/reviews/review-sample-4301-4400.json)
- [`royal-kingdom/reviews/review-sample-4401-4500.json`](royal-kingdom/reviews/review-sample-4401-4500.json)
- [`royal-kingdom/reviews/review-sample-4501-4600.json`](royal-kingdom/reviews/review-sample-4501-4600.json)
- [`royal-kingdom/reviews/review-sample-4601-4700.json`](royal-kingdom/reviews/review-sample-4601-4700.json)
- [`royal-kingdom/reviews/review-sample-4701-4800.json`](royal-kingdom/reviews/review-sample-4701-4800.json)
- [`royal-kingdom/reviews/review-sample-4801-4900.json`](royal-kingdom/reviews/review-sample-4801-4900.json)
- [`royal-kingdom/reviews/review-sample-4901-5000.json`](royal-kingdom/reviews/review-sample-4901-5000.json)
- [`royal-kingdom/reviews/review-sample-5001-5100.json`](royal-kingdom/reviews/review-sample-5001-5100.json)
- [`royal-kingdom/reviews/review-sample-5101-5200.json`](royal-kingdom/reviews/review-sample-5101-5200.json)
- [`royal-kingdom/reviews/review-sample-5201-5300.json`](royal-kingdom/reviews/review-sample-5201-5300.json)

Coverage definition:

- Layer 1 — archive: one verified initial-board capture and complete provenance for every numbered level.
- Layer 2 — structured analysis: automated level type, tutorial status, objectives, move count, visible blockers, and confidence for every level.
- Layer 3 — review: human review of every exception plus a stratified sample from each 100-level batch.
- Layer 4 — editorial analysis: timed commentary for tutorials, new mechanics, Kingdom/Dark Kingdom encounters, visible monetization events, notable failures, and representative strategy patterns.

Execution plan:

1. **Freeze the source inventory.** Resolve every video ID to its advertised level range, record duration and upload date, detect overlaps, and keep the media-validated 3,541–3,560 title correction explicit.
2. **Calibrate on levels 16–100.** Process one bounded batch, manually review every capture, and update segmentation rules before scaling.
3. **Process sequential 100-level batches.** Download only the videos required for the active batch, validate media streams, extract evidence, publish accepted artifacts, then release transient source media from the bounded cache.
4. **Run deterministic gates.** Require valid timestamps, expected level coverage, decodable JPEGs, duplicate detection, schema validity, and source linkage before agent analysis.
5. **Dispatch specialized analysis.** Run gameplay, strategy, monetization, and player-experience agents only on scoped clips; route disagreements or confidence below 0.85 to review.
6. **Publish incrementally.** Merge a batch only when its accepted, missing, ambiguous, and failed counts reconcile to the expected range; keep gaps visible in the browser.
7. **Audit at milestones.** Perform full reconciliation at levels 100, 500, 1,200, 3,000, and 5,300; compare manifest entries, files, source ranges, and review records.
8. **Maintain the moving cap.** Recheck official updates and high-level sources every two weeks, add only newly published ranges, and never count Champions Arena repeats as new numbered levels.

Batch quality gates:

- 100% of expected level numbers are accepted or explicitly classified as missing, ambiguous, or failed.
- 100% of factual and monetization claims link to timestamps or frames.
- Zero unsupported claims that a player paid or had to pay.
- At least 95% of representative frames pass automatically; all remaining frames require human review.
- No batch is published with unresolved duplicate level IDs or broken image references.

Storage policy:

- Permanent: board images, manifests, source metadata, hashes, review records, agent outputs, and selected commentary clips.
- Transient: full source videos, limited to the active batch and a target cache ceiling of 2 GB.
- Current disk evidence: 33 GB free on 2026-09-24; keeping all source videos permanently is out of scope without additional storage.

Milestones:

- M1: levels 1–100 complete and fully reviewed (completed 2026-09-24).
- M2: levels 1–500 reconciled; first pattern taxonomy calibrated (completed 2026-09-24).
- M3: levels 1–1,200 reconciled against the supplementary no-booster playlist (completed 2026-09-25).
- M4: levels 1–3,000 complete with drift review for UI and mechanics (completed 2026-09-25).
- M5: levels 1–5,300 complete, gap-free, and ready for biweekly incremental maintenance (completed 2026-09-25).

Next action: maintain the moving cap biweekly and process only newly verified numbered-level ranges.

### TSK-007 — Publish the complete project to GitHub

Status: `done`  
Owner: Victoria Serrano  
Scope: Publish the complete Game Comparison workspace to `victoriaVito/Game-Comparison`, including both browsable level archives and the Royal Kingdom source video.

Acceptance criteria:

- The GitHub `main` branch contains the project code, documentation, manifests, reviews, level images, and source metadata.
- The source MP4 is published as a GitHub Release asset because the repository owner's Git LFS quota is exhausted.
- Nested source-repository Git metadata is excluded while its complete browsable working tree remains present.
- Local and remote commit IDs match after publication.
- Representative Royal Match and Royal Kingdom JPEGs are readable from the published repository.

Current evidence: the complete asset commit was verified locally and on `origin/main`; the remote tree contains exactly 5,300 Royal Kingdom JPEGs and 13,087 Royal Match JPEGs. Representative images from both archives return the JPEG signature `ffd8ff`. The source-video Release asset is uploaded at 169,649,800 bytes with SHA-256 `7fed3e38ffc4edfc87920733c3f55d00c062058dcdcb9fb5664b957bbfbf44fc`.  
Next action: use `victoriaVito/Game-Comparison` as the publication repository and keep future archive updates incremental.

## Completed tasks

### TSK-003 — Build the Royal Kingdom levels 1–15 pilot

Status: `done`  
Owner: Victoria Serrano  
Scope: Extract and publish one initial board capture for each level in the pilot video.

Acceptance criteria:

- All 15 expected levels are present.
- Every capture shows the initial board before the first move.
- Standard, Kingdom, and Dark Kingdom types are represented.
- Tutorial overlays are retained and reviewed.
- The local browser renders the complete pilot.

Verification:

- 15/15 captures present and visually reviewed.
- Level types: 12 standard, 2 Kingdom, 1 Dark Kingdom.
- Tutorial levels: 1, 5, 8, 10, and 12.

Evidence:

- [`royal-kingdom/manifest.json`](royal-kingdom/manifest.json)
- [`royal-kingdom/analysis/review.json`](royal-kingdom/analysis/review.json)
- [`royal-kingdom/app/index.html`](royal-kingdom/app/index.html)

### TSK-004 — Create the specialized analysis agent team

Status: `done`  
Owner: Victoria Serrano  
Scope: Define specialized agents and subagents for ingestion, gameplay observation, strategy, monetization, player experience, commentary, review, and publishing.

Acceptance criteria:

- Agent hierarchy and authority boundaries are persisted.
- Handoffs use structured outputs and scoped evidence.
- An independent reviewer gates publication.
- Unsupported payment claims are blocked deterministically.
- The current pilot commentary passes validation.

Verification:

- 10 agents and 10 controlled handoffs configured.
- Six timed commentary notes validated.
- Team validation completed with zero errors.

Evidence:

- [`royal-kingdom/agents/team.json`](royal-kingdom/agents/team.json)
- [`royal-kingdom/analysis/validate_agent_team.py`](royal-kingdom/analysis/validate_agent_team.py)
- [`royal-kingdom/analysis/video_notes.json`](royal-kingdom/analysis/video_notes.json)

### TSK-006 — Add evidence-aware video commentary to the pilot

Status: `done`  
Owner: Victoria Serrano  
Scope: Pause the pilot video at selected moments to explain gameplay, visible monetization evidence, and analyst impressions.

Acceptance criteria:

- The local video includes audio and plays in the archive.
- Commentary pauses are timestamped, ordered, skippable, and at least ten seconds apart.
- Gameplay observations, monetization evidence, and impressions remain distinct.
- Absence of a visible purchase is not presented as proof that payment is unnecessary.

Verification:

- Six commentary pauses cover levels 1, 5, 8, 10, 12, and 15.
- Local media contains H.264 video and AAC audio.
- HTML JavaScript and commentary validation pass.

Evidence:

- [`royal-kingdom/videos/source-nT-hcLmkddg.mp4`](royal-kingdom/videos/source-nT-hcLmkddg.mp4)
- [`royal-kingdom/analysis/video_notes.json`](royal-kingdom/analysis/video_notes.json)
- [`royal-kingdom/app/index.html`](royal-kingdom/app/index.html)

## Synchronization

Local canonical tracker: synchronized and verified.  
External tracker: not configured; no remote status was written.

Latest repository check:

- Royal Match local revision: `4837acfe9684ee4fb5b3c4b64e5ef164f78b0dbe`.
- Local inventory: 13,087/13,087 board JPEGs present.
- Representative JPEG signature: valid.
- Upstream comparison: blocked because this automation run could not execute `git fetch`.
