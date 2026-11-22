# BITS capacity results: reproduction manifest

One command re-checks every capacity result without a solver:

```sh
python3 -B reproduce.py            # checksums and the quick checkers, about two minutes
python3 -B reproduce.py --full     # adds the slow ones, about fifteen minutes
```

Needs Python 3.10 or later and Git, run from a clone of `clocksmith/gamma` that contains commit
`59ff04415ff2afd04ff2ed451340f4f02852bf18` (the pin of the matched80 sources).

## What is reproduced

| Result | Folder | Check |
| --- | --- | --- |
| matched80 needs exactly 92 entries under the witness rule and 79 unrestricted, compact and canonical | `witness-coverage-v1` | `check_rank.py`: ranks in two prime fields and matching dictionaries |
| Witnessed coverage at every budget; exact at 24 of 93 | `witness-coverage-v1` | `check_coverage.py` replays every stored dictionary; `check_unrestricted.py` proves the ceiling (slow) |
| Tiny controls and the counterexamples to both early conjectures | `capacity-theorems-v1` | `evaluate.py`, `evaluate.py --round2`: exhaustive search |
| The capacity question is NP-complete under the witness rule; the potential certificate and where it fails | `capacity-complexity-v1` | `evaluate.py`: exhaustive search and 758 certificates in exact fractions |
| Deciding whether one entry per character is optimal is co-NP-complete | `capacity-complexity-v1` | `check_saturation.py`: the construction on 20 instances |
| Two C corpora: minimum 61 and 65 | `capacity-complexity-v1` | `evaluate_real.py`: certificate and replayed dictionary |
| Nine unseen projects near 64 characters | `capacity-boundary-v1` | `evaluate.py` (no length cap, as first run), `capped.py` (160-byte cap) |
| The rank-tight parsing test is sound and what it settles alone | `capacity-kernel-audit-v1` | `kernel_alone_real.py`, `independent_kernel.py`; `audit_kernel.py 1` (slow) |
| Twelve public projects, three arms | `capacity-lagrangian-race-v1` | `three_arm.py` re-derives every answer from the stored measurements (slow) |
| matched80 press certificates | `sixbit-v1/reproducibility` | `verify_bits.py` (slow) |

## What is not reproduced by this command

- **Anything a solver found.** Dictionaries and certificates are stored and re-checked; the searches that
  found them (`find_certificates.py`, `find_real.py`, `run_benchmark.py`, `three_arm.py --run`) need scipy
  and are not rerun.
- **Times.** They are single measurements on one laptop.
- **The baseline's own certificates** in the three-arm race. Its "fits" answers are replayed; its "does not
  fit" answers are checked only for agreement with the other arms.
- **The encoding comparison** in `capacity-bakeoff-v1` and the first race in `capacity-race-v1`. They have
  their own checksums and scripts.
- **`capacity-impossibility-v1` and `capacity-diagnostic-v1`.** They have their own tests.

## Pins

| What | Pin |
| --- | --- |
| matched80 source bytes | Gamma `59ff04415ff2afd04ff2ed451340f4f02852bf18` |
| Kernel test as audited | Gamma `30c74bee` (`capacity-diagnostic-v1/diagnostic.py`) |
| Audit and second implementation | Gamma `7a2cfb66` |
| Three-arm race: pre-registration, results | Gamma `51a3d650`, `789b063e` |
| Nine-project benchmark: pre-registration, results | Gamma `64b1ea0d`, `59690402` |
| Hardness notes | Gamma `fe4c0c10`, `59690402`, `5cdb48ba` |
| Public corpora | upstream commits recorded in `capacity-lagrangian-race-v1/public-instances.json` |

Each folder's `SHA256SUMS` file is verified first. A mismatch stops nothing but is reported as a failure.
