# Pre-registration: Unseen Corpus Predictions for Phase 3 Diagnostic

Committed **before** running `diagnostic.py` on any corpus in `unseen-instances.json`.

## Frozen unseen inputs (8 corpora, 15 queries)

1. **`unseen_real_py_tests_12`** (real, never-read): 12 smallest `.py` files (`828..1066` B) under `tests/` at pinned `clocksmith/gamma@59ff0441`.
   - `W2 @ K=64`: predict `IMPOSSIBLE` (real Python test syntax exceeds 64 slots under `W2`; changes encoding choice away from plain 6-bit).
   - `W2 @ K=96`: predict `FEASIBLE` (printable ASCII + newline fits within 96 singletons; falsified if non-ASCII bytes appear).
2. **`unseen_real_yaml_pair`** (real, never-read): the two `1128` B YAML files under `configs/latent_handoff/` at pinned `59ff0441`.
   - `W2 @ K=64`: predict `FEASIBLE` (YAML config alphabet fits in `<= 64` singletons; genuinely falsifiable).
   - `W2 @ K=32`: predict `IMPOSSIBLE` (`LB > 32`).
3. **`decision_66char_pairable`** (encoding-decision pair A, `|\Sigma| = 66 > 64`): 62 unique chars + 2 non-adjacent paired tokens occurring consistently across 2 programs.
   - `W2 @ K=64`: predict `FEASIBLE` (`LB = 64`, byte-verified 64-slot dictionary) — **changes the encoding choice**: naive `|\Sigma| = 66 > 64` rejects 6-bit, while the checker proves 6-bit is feasible with zero escapes.
   - `W2 @ K=63`: predict `IMPOSSIBLE` (`LB = 64`).
4. **`decision_66char_doomed`** (encoding-decision pair B, identical `|\Sigma| = 66` and same two shared tokens, plus shifted repeats breaking both pairs):
   - `W2 @ K=64`: predict `IMPOSSIBLE` (`LB = 66`, `monotoneSaturation >= W2`) — confirms plain 6-bit is doomed for all $k \ge 2$, forcing escape or 7-bit.
   - `W2 @ K=66`: predict `FEASIBLE` (66 singletons).
5. **`unseen_3comp_mixed`** (3 fresh disjoint components, `|\Sigma| = 12`): `["cde","cdf","gdf"]` (`5`) + `["hjkl","klhj","hlkj","kjhl"]` (`4`) + `["wxy","wxwx"]` (`2`).
   - `W2 @ K=10`: predict `IMPOSSIBLE` (`Comp = 3`, `LB = 11`).
   - `W2 @ K=11`: predict `FEASIBLE` (11-entry verified dictionary).
6. **`unseen_forced_block_split`** (fresh 6-program single program-connected corpus, `|\Sigma| = 8`): `["ijk","ljk","ijmnop","opmn","mpon","onmp"]`.
   - `W2 @ K=7`: predict `IMPOSSIBLE` (`Comp = 1`, `LB = 8` via `forced-block-components`, `monotoneSaturation >= W2`).
   - `W2 @ K=8`: predict `FEASIBLE` (8 singletons).
7. **`unseen_u_span_obstruction`** (fresh 4-program `U` corpus, `|\Sigma| = 4`, `rank = 3`): `["uvwz","wzuv","uzwv","wvuz"]`.
   - `U @ K=3`: predict `IMPOSSIBLE` (`LB = 4` via `span-parse-obstruction`).
   - `U @ K=4`: predict `FEASIBLE` (4 singletons).
8. **`unseen_unresolved_interval`** (natural `UNRESOLVED` case without `--no-search`): `["abcd","abce","fbcd"]` padded with a 20-char shared-context tail so forced block `"abcd"` is ineligible (`doc_freq = 1`) and `|tokens| > 24`, at `K = 25` (`LB = 25`, `UB = 26`):
   - `W2 @ K=25`: predict `UNRESOLVED` (`interval = [25, 26]`, no rank bound reported as a construction).

## Falsification & reporting rules

- Commit `PREREGISTRATION-UNSEEN.md`, `freeze_unseen.py`, `unseen-instances.json`, `unseen-predictions.json`, and `SHA256SUMS-UNSEEN` **before** running `evaluate_unseen.py`.
- Report every miss alongside every match; never edit predictions or instances after running `evaluate_unseen.py`.
- Keep the connected-component counterexample search (`connected_search.py`) strictly separate from this diagnostic evaluation.
