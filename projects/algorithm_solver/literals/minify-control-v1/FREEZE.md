# minify-control-v1: frozen design (compaction-only control)

Owner Amendment 1 (2026-10-22, relayed from Mars): run the minify-only control first. It
compares original, minified and rewritten sources on identical problems and correctness
contracts, under a fixed dictionary and under independently refitted dictionaries with equal
optimization budgets. It reports source bytes, selections, character fallback and complete
package cost. Otherwise source shortening and dictionary adaptation stay confounded, as in
[scale500-v1](../scale500-v1/README.md), where W2's 66% cut came mostly from about 3x shorter
sources. The typed-component draft ([structural-v1](../structural-v1/DRAFT.md)) waits for this
result.

This design was committed before any minified source was generated and before any arm ran.
The implementation, the terser package hash and the minified-source qualification receipt are
pinned by SHA-256 in `contract.json` in a separate commit, also before any arm runs. A change
after this commit is a disclosed amendment.

## Problems and partitions

- **Population:** the frozen 500 ([population-500.json](../admission500-v1/evidence/population-500.json),
  sha `0d6cb3ff...`). Same 500 problems, interfaces and frozen corpus cases (48,405) for every
  pool. The protected 66 stay closed.
- **Development-validation partition** (Amendment 1), taken from the scale500 training 400:
  sha256(`minify-control-v1-devval` + id), lowest 100 go to **dev-val**, the other 300 to
  **dev-fit**. The structural experiment reuses the same partition.
- **Final held-out 100** (scale500 split): no separate measurement. These problems enter only
  as part of the all-500 M1 aggregates, and no per-split figure for them is computed or read.

## Source pools (one source per problem)

| Pool | Source |
| --- | --- |
| O | the admitted original, `population500/<id>.js` (all 500 pass their baselines) |
| Om | O passed through terser 5.46.1 (`/usr/share/nodejs/terser`, sha-pinned) as `terser <file> --comments false`. That is no `-c` and no `-m`: compaction only, with every name, statement and algorithm kept |
| R | the qualified shared-style rewrite: style150-v1 for the first 150, scale500-v1 for the other 350 (500/500 qualified) |

Om is qualified exactly like a rewrite: strict parity with O's recorded observation on every
frozen case (result, result type, arguments after the call, alias edges), using the unchanged
oracle and the original's entry name. Generation is deterministic and runs once; nobody edits
the output. A failing Om falls back to O for that problem. It is recorded, counted and kept in
the denominator.

## Dictionaries and arms (each at 128 / 7 bits and 256 / 8 bits)

**Refitted:** one dictionary per pool, fitted independently with equal budgets.
- **F500:** fitted on all 500 and reported on all 500 (the M1 metrics).
- **Fdev:** fitted on dev-fit 300 and measured unchanged on dev-val 100.

That makes 3 pools x 2 widths x 2 fits = 12 search arms.

Identical procedure for every search arm:
- Start from the 96-character fallback alphabet.
- Greedy refill (shortlist 24), then matched80-v3 exact local search with the style150-v2
  chosen-source proposer, using the scale500 neighborhood (96 additions, 500 swaps, 150 pairs,
  16 pair additions, 8 pair removals).
- **Spans only:** the STYLE.md designed forms are off for every arm. They would favor R.
- 60,000-trial cap; 6 h safety limit per arm; `PYTHONHASHSEED=0`.

Trials, seconds and stop reason are reported per arm. Equal budgets mean equal trial caps; O's
longer sources make each trial slower, and that difference is reported, not equalized.

**Fixed:** a dictionary held constant across all three pools, so the source change alone is
measured. Each fixed dictionary is applied by exact parsing to every pool at its width.
- **A:** the fallback alphabet only. Unfitted and neutral.
- **P:** style150-v2 D (existing before this experiment; fitted on the first 150's pool, so it
  is biased toward shared-style text, as disclosed).
- **X:** each pool's F500 dictionary applied to the other two pools on all 500, and each Fdev
  dictionary applied to the other two on dev-val 100. That gives full 3 x 3 matrices.

**Decomposition.** For pools X to Y:
- source effect under X's dictionary = sel(Y, D_X) − sel(X, D_X);
- adaptation effect = sel(Y, D_Y) − sel(Y, D_X).

Both orders are reported because the split depends on the path.

## Metrics (M1 thresholds unchanged)

Per arm and per evaluation, on all 500 and per admission cohort (first-150, admitted-213,
gap-137), and on dev-val 100 for Fdev:
- source bytes;
- selections, median, p95, worst;
- programs within 32 and within 96 selections;
- bytes per selection;
- character fallback: the fraction of selections that are single-character entries, and the
  fraction of source bytes emitted by them;
- dictionary bytes;
- complete package bytes (dictionary + 41 framing bytes per packet + payload);
- whole-program literal count.

Every packet of every arm and fixed evaluation is decoded independently through the canonical
codec to its qualified source hash. One failure fails the control.

## Predictions

- **K1:** Om totals at most 75% of O's source bytes, and refitted L-Om at 256 (F500) uses at
  least 25% fewer selections than refitted L-O.
- **K2:** refitted R at 256 (F500) uses at least 20% fewer selections than refitted Om. Style
  matters beyond compaction.
- **K3:** under refitted dictionaries at 256 (F500), R has more bytes per selection than Om. The
  style adds recurrence, not only shortening.
- **K4:** adaptation matters. On Om at 256, D_R costs at least 10% more selections than D_Om.
- **K5:** on dev-val 100 (Fdev), the order O > Om > R in selections holds at both widths.
- **K6:** at least 490 of 500 Om sources qualify.
- **K7:** no arm meets M1.
- **K8:** every packet decodes; zero failures.

## Order of work

1. `minify.py`: generate Om, qualify it against the frozen cases, and write the receipt (pass
   rows with hashes, and failures with their first mismatch). It runs once, before any arm.
2. `control.py`: the 12 search arms, the fixed evaluations, packet verification and
   `results.json`. Focused tests:
   - a spans-only proposer returns no designed forms;
   - a cross-applied dictionary parses exactly;
   - the decomposition arithmetic.
   A 200-trial smoke run checks the plumbing; its outputs are discarded, as in earlier freezes.
3. Pin code hashes, the terser package hash and the Om receipt in `contract.json`; commit.
4. On the owner's go-ahead: run on Jupiter, verify, then write the README and public evidence
   (aggregates, counts and hashes only; no sources, dictionaries or sequences).

## Not claimed

- No M1 qualification, unseen solving or assembly result. This is offline representation
  evidence on known sources.
- No BITS profile.
- No components, scorer or training: the structural draft follows this control, and a scorer
  waits for demonstrated search headroom and the owner's explicit approval.
