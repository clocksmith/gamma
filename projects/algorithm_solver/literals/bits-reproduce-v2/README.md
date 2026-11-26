# BITS reproduction, fail-closed (`bits-reproduce-v2`)

This supersedes `../bits-reproduce-v1`. That folder stays frozen at the paper's evidence pin, and
its `MANIFEST.md` still describes what each step covers.

```sh
python3 -B reproduce.py           # quick: exits 2, INCOMPLETE, and lists what it did not verify
python3 -B reproduce.py --full    # exits 0 only if every claimed result was verified
```

Exit codes: `0` VERIFIED, `1` a check failed, `2` INCOMPLETE (a check was not run or verified
only a hash).

## Why v2

An audit found that v1 printed "N passed" after quick mode, although quick mode:

- skips the slow checks;
- compares only the SHA-256 of the 4,141-node PY-3 defect tree and scores PY-3 at its rank;
- leaves the 33rd exact coverage point (76 slots, `check_addendum.py --deep`) and seed 2 of the
  ladder audit to separate commands, even in `--full`.

v2 reads v1's step list from v1's frozen `reproduce.py`, after checking that file's SHA-256.
It marks every skipped check and the hash-only tree as NOT VERIFIED and exits non-zero while any
row is not verified. A missing script counts as FAILED. `--full` adds the two separate
commands. Every run, quick or full, also runs:

- `bits-envelope-v1`: the byte envelope of the four frozen matched80 packages, plus its
  uncounted-index and slot-swap tests;
- `sixbit-v1/independent-verifier/check.py`: the solver-free matched80 checker;
- `witness-newline-sensitivity-v1`: the matched80 rank with and without trailing newlines
  (compact 79 to 78, canonical unchanged), which is the scope of the unrestricted minimum.

The checksums of v1, v2 and the two new folders are verified first.

`--full` also runs the escape-arm slot-swap test of `06562147d`. No step imports `model.py`.
