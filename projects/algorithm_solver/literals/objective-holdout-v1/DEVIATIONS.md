# Deviations from the preregistered order of work

Each entry is written before any result it could affect is read.

## 1. `frozen/train.log` was missing from the freeze commit (2026-11-26, recorded in commit `b82e3a89b` at 14:05:38 UTC)

- **What happened.** `SHA256SUMS-FROZEN` lists `frozen/train.log`, the console log of `train_arms.py`. The
  repository ignores `*.log`, so the file was not in freeze commit `9d7d54b9e`. The scorer exported that commit,
  ran `sha256sum -c SHA256SUMS-FROZEN`, got 33 of 34 lines OK and one missing file, and stopped as the rules
  require. No test file had been fetched and nothing had been scored.
- **What the file is.** A log. No script reads it. Every header, the zstd dictionary, both set manifests,
  `train-summary.json` and every script verified OK.
- **Fix.** The file is added to git by force in a follow-up commit, with the bytes whose hash the freeze
  already lists (`3506ba96…`). `SHA256SUMS-FROZEN` is not edited. The scorer exports that one file from the
  follow-up commit and reruns the full check before continuing.
- **Effect on results.** None possible: no frozen input to scoring changed.
