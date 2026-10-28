# J/K results, 2026-10-28

Both runs were executed on the Linux executor from detached worktrees: J/K at `b30597477`, rejection at `3a7042294`. Each was then replayed on the host without execution. Raw streams, reports and replays stay in the executor's `gamma-continuation-20261028` run directory; they are not committed. Problem statements and generated cases were never copied off the executor.

## J/K qualification baseline

| Binding | SHA-256 |
|---|---|
| Freeze `jk-freeze.json` | `5e05dd6a3ccd88b1fb0c8766623d4d95f71a86bfd7e30e1ff88409041a92918b` |
| Refetched definition pins `jk-statements/pins.json` | `13810900b8ba6bff552b1ffa96d86b5d238101ac104ee691b0a76e41a925c0f5` |
| Mandatory source reviews `jk-review.json` | `7ba564d48573e6e77084cdbc7937272dea1d2056027e16ef1d5e62ca2594989a` |
| Execution report `jk-run/report.json` | `90aa4721881b260bc2242a18bbd811e4f9d535f41bd63add33a57b57dc0162de` |
| Host replay `jk-run/replay.json` | `7300d6707b6ac42c387add2faa4d4184933389157449aff24f09d2ac42cf55ef` |

- **Gate and runtime:** the existing six-anchor gate (`dfeb3df2…`), the shared passing preflight, unchanged limits, and a runtime inventory recorded in the freeze.
- **Execution:** all 40 programs passed every admitted case. That is 8,618 distinct cases with none blocked, 17,802 calls and 596 sandbox batches. The replay reproduced every verdict.
- **Qualification:** 30 of the 40 programs qualified on this finite suite. The other 10 passed execution but are not qualified, because their mandatory review set `independent_references_and_boundaries` to false.

The reviewers read every source and executed none. They found no correctness, safety, interface, numeric, complexity or effects defect in any of the 40 programs. The ten false flags record case-set gaps, not candidate defects:

| Problem | Gap that would let a plausible wrong program pass |
|---|---|
| 3820 | The only maximum-size tree is a star, so every distance is at most 2. No deep or path-shaped tree near the maximum size, so deep traversal and large squared distances go untested. |
| 3821 | Every case has n ≤ 100. No large n with a mid-range k, so 32-bit or floating-point truncation of n or the binomial table would pass. |
| 3825 | No case where bit 29 alone reaches the answer, so a scan of bits 0..28 would pass. Neither maximum case exercises real work. |
| 3835 | All 30 random cases have k above the largest possible cost and expect every subarray. Window shrinking is tested only on arrays of length 4 or less. |
| 3850 | At the maximum length, every value is 1. Large k never appears with real values, so floating-point fractions or products beyond 2^53 go untested. |

The reviewers also recorded weaker points that did not change any flag:
- **Uniform or trivial maximum cases:** 3819, 3834, 3836, 3839, 3844, 3845, 3849 and 3854.
- **Small random-size caps:** the K random cases are capped at size 7.
- **Freeze hash not reproducible:** K's cited pre-source freeze hash `f6864cdc…` does not match any committed file.
- **Unlisted cache:** K has a `__pycache__` folder that the manifest does not list.
- **Field-name typo:** every K semantics file spells a key `pre_sourck_reference_freeze_sha256`.

## Judge rejection of seeded wrong variants

| Binding | SHA-256 |
|---|---|
| `variants.py` | `8ff9ef9fa7bedc810d94153c608f752509244c1ef08a74ce636adcf7ad7c5ae0` |
| `rejection.py` | `8ac4753cc01984f56929e85d1a69a92b6b50a8a1718600b67949c66b46555f6c` |
| Plan | `12ac43f44c3fd91c8e7abb12a1753484919c3d4ff3f8195e68ed72a6e1cc8685` |
| Report | `2b49904afbf66db6e51eb91cbfd7a05a651137d76903c9ad3c87df47152339be` |
| Host replay | `af88a346307f887bc1b1589097783ee7ab37876247ef98346b58ba639114550f` |

All 40 originals were eligible, giving 520 operator entries. The run used 920 sandbox batches, and the replay reproduced every verdict.

- **Seeded variants:** every one of the 324 variants with a triggering case was rejected with its intended verdict on a triggering case. There were no false acceptances and no rejections for other reasons.
- **Controls:** all 40 behavior-preserving controls passed every batch, so no compliant variant was rejected.

| Operator | Triggered and rejected as intended | Not triggered by any frozen case |
|---|---:|---|
| `control-copy` | 40/40 accepted | n/a |
| `wrong-always` | 40/40 | none |
| `wrong-type` | 40/40 | none |
| `wrong-on-repeat-call` | 40/40 | none |
| `wrong-on-degenerate` | 30/30 | 3820, 3821, 3830, 3844, 3848 |
| `wrong-on-large` | 30/30 | 3821, 3836, 3848, 3850, 3853 |
| `slow-on-large` | 30/30 | as `wrong-on-large` |
| `memory-on-large` | 30/30 | as `wrong-on-large` |
| `input-mutation` | 30/30 | 3821, 3844, 3848, 3849, 3853 |
| `wrong-on-duplicates` | 28/28 | 3820, 3821, 3844, 3848, 3849, 3853 |
| `wrong-on-zero` | 14/14 | 13 problems |
| `wrong-on-negative` | 6/6 | 17 problems |
| `alias-equal-input` | 6/6 | 17 problems |

Counts cover both languages. The untriggered problems are listed once and apply to both languages.

"Not triggered" means no frozen case exercises the trigger. Some of these triggers are impossible in the problem's domain, such as negative values when inputs are non-negative, or lists when the arguments are scalars. Others are coverage gaps. This run does not separate the two.

## What this shows and does not show

These operators are detectable by construction whenever they trigger. A perfect score therefore shows that the observers, the type and effect checks, the aliasing check, the hidden-state repeat policy and the resource limits work on these sources. It does not show that the case sets catch problem-specific algorithmic errors. The review table above names five such errors that would currently pass.

## Next

Both steps below were completed the same day; see the [boundary repair and targeted-variant results](../continuation-jk-semantic-rejection-20261028-v1/RESULTS.md).

1. Add problem-specific semantic variants for 3820, 3821, 3825, 3835 and 3850, matching the review gaps: a deep-tree traversal bug, 32-bit `n`, bits 0..28 only, a window that never shrinks, and floating-point fractions. Each is expected to be a false acceptance on the current cases, which measures the gap.
2. Repair those five case sets in a new frozen lane, with independent references and boundary cases at the domain maximum. Then rerun this measurement, so the same semantic variants show the rejection.
