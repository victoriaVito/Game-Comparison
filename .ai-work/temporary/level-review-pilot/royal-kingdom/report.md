# Royal Kingdom classification pilot: levels 1–1,000

**Status:** Incomplete candidate-only pilot; not a canonical or accepted dataset. Taxonomy: `royal-kingdom/analysis/pattern_taxonomy_v1.json` (v1, unchanged).

- Requested: 1,000 numeric levels.
- Reviewed from actual image renders: 6 (levels 1, 250, 500, 501, 750, and 1,000).
- Unreviewable within the available visual-review interactions: 994; no visual tags were inferred for these rows.
- Missing source images at the exact expected paths: 0.
- Expected path pattern confirmed: `royal-kingdom/levels/level-<4-digit zero-padded number>.jpg`; all paths 0001–1000 exist.
- Source-video directory `royal-kingdom/videos/` is absent. `verified_difficulty` and `verified_strategy` are `unknown` in every row; no video evidence is claimed. No speculative hypotheses were added.

Two read-only child reviewers handled disjoint halves (1–500 and 501–1,000). Each could render only three images before reporting a visual-inspection capacity blocker. Their rendered-level findings are preserved as candidate-only observations above; no overlapping review was available for adjudicating independent disagreement. Ambiguity reported by the reviewers is retained on levels 1, 250, and 500. The principal coverage gap is 994 uninspected images.

`candidate_tags.jsonl` contains exactly one row for every requested numeric level, with the relative source path and explicit `reviewed`, `unreviewable`, or `missing` status. This run stopped at the requested two-half reconciliation; no later batch was started.
