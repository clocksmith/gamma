# mip-audit-v2: exact optima on dev-fit sub-instances vs the frozen local search

This is gamma-team board item 9 (claude), goals 2a/2b. It succeeds
[v1](../mip-audit-v1/FREEZE.md) (`8187b9837`), which was superseded before it ran
([note](../mip-audit-v1/NOTE-2026-10-23.md)). Codex's review (gamma-team LOG 18:37Z) asked for
five corrections, all applied here.

## Question

The owner's correction of 2026-10-23 says a local optimum does not show that better dictionaries or
search methods cannot help. Every literal search here uses the same exact local search: matched80-v3
refill, swaps and pairs, with the minify-control chosen-span proposer. This audit measures that
search's gap on instances small enough for HiGHS to solve. The question bears on the owner's
precondition for any learned scorer; scorer training itself stays owner-gated.

## Instances (unchanged from v1)

**Programs.** For each n ∈ {20, 30, 40}, six frozen seeds each give the subset
`random.Random(seed).sample(dev_fit, n)`:
- n = 20: seeds 101–106;
- n = 30: seeds 201–206;
- n = 40: seeds 301–306.

The subsets come from cost-decomposition-v1's allowlist only. **Validation, the final held-out 100
and the protected 66 are never opened.**

**Pre-freeze exposure, dev-fit only.** Seeds 1–4 are excluded from the frozen sample. They gave:

| Programs | Slots | Exact optimum | Local search | Gap |
| --- | --- | --- | --- | --- |
| 20 | 32 | 2,239 | 2,342 | 4.6% |
| 40 | 32 | 4,860 | 5,069 | 4.3% |

At 80 programs (32 slots) and at 40 programs with 160 slots, the solver did not finish in 900 s.

**Budget.** B = 32 learned entries plus the 96 characters, i.e. the 128-entry codebook.

## Arms (per instance)

- **milp:** pool = substrings of 2–32 characters shared by at least two subset programs, never a
  complete source or solve body. Each program is a path flow, and each pool arc is linked to its
  entry's binary choice, under a budget of B. Once the choices are fixed, the path flows are an
  integral network flow, so only the choices are integral.

  The solver is HiGHS through `scipy.optimize.milp`, with `mip_rel_gap=0` and a 900 s limit.
  **Status 0 is reported as "solver-reported optimal within HiGHS tolerances", not as an
  independent proof.** The chosen dictionary is then checked:
  - it has at most B entries, all from the pool, and none forbidden;
  - every subset program encodes and decodes through the canonical codec;
  - its exact canonical score never exceeds the objective, and equals it whenever the status is
    optimal. If either check fails, the run fails.
- **local:** the frozen local search on the subset at 128 entries:
  - start from the fallback alphabet;
  - greedy refill, shortlist 24;
  - matched80-v3 local search with the minify-control neighborhood and proposer;
  - 60,000 trials and a 1,800 s safety limit.

  Its proposals may be longer than 32 characters or fall outside the pool.
- **local_pool:** the same procedure, with proposals restricted to members of the MILP pool. Its
  dictionary space is the MILP's.

Each finished dictionary is checked the same way. The dictionaries and a per-instance receipt are
written privately as each instance finishes.

## Measurement

Per instance:
- pool size and arcs;
- MILP status, message, objective, dual bound, gap, time and exact score;
- for local and local_pool: exact fit selections, trials, stop reason, time, and the witness gap
  (arm − MILP exact score) / MILP exact score;
- subset IDs and dictionary hashes.

The witness gap uses the exact score of the dictionary the MILP returned, whether or not it was
certified optimal. A positive gap is an exact witness that a better dictionary exists.

## Predictions

- **M-a:** at least 15 of the 18 instances reach solver-reported optimality within 900 s.
- **M-b:** in every solver-optimal instance, local_pool is at or above the MILP score.
- **M-c:** at every size with enough solved instances (see below), the median witness gap of
  `local` is at least 3%.
- **M-d:** the median `local` witness gap at n = 40 is at least the median at n = 20.

## Interpretation rule (frozen; per size, mixed outcomes are reported per size)

All 18 instances are reported. A size is **interpretable** only if at least 4 of its 6
instances reach solver-reported optimality. Otherwise that size is reported as
incomplete/inconclusive, and its solved instances are listed but not summarized by a median.

- **Headroom shown at size n** if the median witness gap of `local` is at least 3% (an exact
  witness count, not just a median of easy cases). It is scoped to this representation, these
  sub-instances and this capacity.
- **local_pool:** a median gap below 1% is reported only as "no ≥1% witness within the restricted
  pool". It does **not** bound headroom outside the pool, because unrestricted proposals can use
  longer or single-owner strings.
- **Anything else** is inconclusive.

Sub-instance capacity ratios (32 slots for 20–40 programs) differ from the full problem's (32 or
160 for 300), and every conclusion states that.

## Run

[audit.py](audit.py) launches 6 shard processes. Each is pinned with `sched_setaffinity` to 2 of
the cores listed in [contract.json](contract.json) (20–31), because scipy exposes no HiGHS thread
option. Settings: PYTHONHASHSEED=0, the Python in `.venv_rocm` (scipy 1.18.1).

Checks before launch:
- `--help` and imports;
- [test_audit.py](test_audit.py): MILP against brute force on more than 30 tiny instances;
- a 10-program dev-fit smoke instance with a non-frozen seed (999), discarded.

No source execution, M1 claim, BITS change or training.
