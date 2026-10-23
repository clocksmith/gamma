# mip-audit-v1: exact optima on dev-fit sub-instances vs the frozen local search

## Question

This is gamma-team board item 8's follow-up, item 9 (claude), goals 2a/2b. The owner's correction
of 2026-10-23 says a search that reaches a local optimum does not show that better dictionaries
or search methods cannot help. Every literal search in this program uses the same exact local
search (matched80-v3 refill plus swaps and pairs, with the minify-control span proposer).
[lagrange-select-v2](../lagrange-select-v2/README.md) left an uncertified gap of up to 18% at
256 entries.

This audit measures that search's gap directly, on instances small enough to solve exactly. It
answers whether conventional search has real headroom. That is also the owner's precondition
before any learned scorer is considered; scorer training itself stays owner-gated.

## Instances

**Programs.** For each frozen size n ∈ {20, 30, 40}, six seeds each give the dev-fit subset
`random.Random(seed).sample(dev_fit, n)`:
- n = 20: seeds 101–106;
- n = 30: seeds 201–206;
- n = 40: seeds 301–306.

The subsets come from [cost-decomposition-v1](../cost-decomposition-v1/contract.json)'s allowlist.
**Validation, the final held-out 100 and the protected 66 are never opened.**

**Pre-freeze exposure.** Four dev-fit probes used seeds 1–4, and those seeds are excluded:

| Programs | Slots | Exact optimum | Local search |
| --- | --- | --- | --- |
| 20 | 32 | 2,239, proven in 9 s | 2,342 |
| 40 | 32 | 4,860, proven in 158 s | 5,069 |
| 80 | 32 | not solved in 900 s | |
| 40 | 160 | not solved in 900 s | |

That is why the frozen sizes stop at 40, and why only the 32-slot budget is used.

## Arms (per instance)

- **Exact (MILP).** Minimize total selections over the subset with the 96 fallback characters
  plus at most B = 32 learned entries (the 128-entry codebook). Candidates are the subset's pool:
  substrings of 2–32 characters shared by at least two subset programs, never a complete source or
  solve body. Each program is a path flow, and each pool arc is linked to its entry's binary
  choice. Once the choice is fixed the paths form an integral network flow, so only the entry
  choices are integral. The solver is HiGHS through `scipy.optimize.milp` (scipy 1.18.1, in
  `.venv_rocm`), with a 900 s limit. The status, objective, dual bound and gap are reported, and
  the chosen dictionary is re-scored by exact canonical segmentation.
- **Local search.** The frozen pipeline's procedure on the same subset at 128 entries:
  - start from the fallback alphabet;
  - greedy refill, shortlist 24;
  - matched80-v3 exact local search with the minify-control neighborhood and chosen-span proposer;
  - 60,000 trials and a 1,800 s safety limit.

  Its proposals may be longer than 32 characters, up to 160 bytes, so its dictionary space is not a
  subset of the MILP pool. The local search can therefore beat a pool optimum.

## Measurement

Per instance:
- pool size and arcs;
- MILP status, objective, dual bound, gap and time;
- the exact re-score;
- local-search fit selections, trials, stop reason and time;
- the relative search gap (local search − optimum) / optimum, for proven optima;
- subset IDs and dictionary hashes.

Per size: the median and range of the gap, and the number solved. Dictionaries stay private.

## Predictions

- **M-a:** at least 15 of the 18 instances solve to proven optimality within 900 s.
- **M-b:** in every solved instance, local search is at or above the pool optimum.
- **M-c:** the median relative gap is at least 3% at every size.
- **M-d:** the median gap at n = 40 is at least the median at n = 20.

## Interpretation rule (frozen)

The outcome follows from the median gap at every size:
- **At least 3%:** conventional-search headroom is shown for this representation on these
  sub-instances. The next proposal is an exact large-neighbourhood search on the full problem, and
  the scorer precondition is met in principle. Training still needs owner approval.
- **Below 1%:** the local search is near-optimal at this scale.
- **Between 1% and 3%:** inconclusive.

Sub-instance capacity ratios (32 slots for 20–40 programs) differ from the full problem's (32 or
160 for 300), and that is stated with any conclusion. Nothing here touches M1, BITS or
validation.

## Run

Six worker processes with two threads each, PYTHONHASHSEED=0. No source execution.
