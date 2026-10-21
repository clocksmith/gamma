# Candidate energy harness v1

This is a small private mechanism experiment for Gamma v2:2b/4c. It adds an interface around the existing exact literal parser, not a new semantic-equivalence engine or a trained reasoning model. Canonical Gamma files, qualification ledgers, protected evaluations and publication state are unchanged.

## Implemented

- `harness.py` distinguishes exact candidate pieces, partial assemblies and complete vocabulary/source-choice states. Partial assemblies cannot be scored as solved programs.
- A frozen source/contract/qualification envelope must pass at every cost or energy scoring entry point. Alternatives for one problem/language must share its exact contract; comparisons and rewrite moves cannot cross languages. Canonical problem IDs and aliases share one exclusion/split namespace. Real-data envelopes require matching pinned proof files, independent review and all output, domain, mutation, alias, numeric and complexity gates. The coordinator remains responsible for approving the envelope; this code is not an independent semantic judge.
- Exact segmentation and independent forward-DP comparison reuse the pinned `../joint-v1/reachable_core.py`. Actual LTD1 dictionary and LTV1 packet construction and reconstruction reuse `../readable-v1/literal_codec.py`. All source bytes, imports, helpers, UTF-8, dictionary storage, framing and padding are counted. Flat literals accept no operand/control side channel or hidden expansion.
- The proposal pool contains exact lines and recurring 2/4/8-character strings plus an explicit single-character coverage control. Recurrence counts distinct problems. Human seed additions are a separate baseline. Add/delete/swap/source-alternative moves use a deterministic bounded round-robin order.
- `compare` provides exact package-cost ranking and an optional learned-energy scorer interface with declared model identity/storage, training-source hashes, split identity, scorer calls and runtime. It rejects non-finite energy and test-derived candidate leakage. Its offline comparison evaluates every eligible proposal exactly, so it cannot establish search acceleration.
- `dataset.schema.json` and `states.schema.json` document the external format; standard-library validators implement the required gates without adding dependencies.

The exact ranking objective is dictionary plus padded packet bits, then input bits and stable identity. Decoder storage and model storage are reported separately. This is not the same objective as minimizing selections alone, and a winner here is not automatically a human-usability winner.

## Deliberate seeds

`fixtures.py` reads the pinned `human-seed-fixture.json`. It contains only general Map/dict creation, zero-prefix seeding, increment, prefix-count lookup and a complete 155-byte JavaScript read/increment helper, with snippet and historical witness hashes. The original private run verified these exact strings against the #560/#781 successor proposals. This portable adapter verifies the fixture and snippet hashes without accessing those full private sources. These nine entries remain **receipt-needed proposals**; the fixture is not independent semantic qualification. See [PORTABILITY.md](PORTABILITY.md) for the adaptation boundary.

The parent additionally reports useful source witnesses: a dense 26-slot lowercase counter in #2068/#1684/#2716; head-index queue pieces in #2316/#2492; and fresh adjacency rows with different directedness/weight contracts. Those reported seeds have not been read or qualified by this harness and are not injected into its smoke corpus. #994 layer boundaries, #773 string-state visits, #785 color state, and the distinct #3193/#3077/#2140 dynamic programs must retain their separate contracts. A Map is not automatically a better replacement for bounded dense counters.

## Bounded verification

Execution is coordinated with the root task. When an exclusive short CPU window is available:

```bash
cd projects/algorithm_solver/literals/energy-search-v1
PYTHONDONTWRITEBYTECODE=1 taskset -c 13 python3 run_checks.py --output smoke-001
```

The command refuses an existing result directory, pins CPU13, caps address space at 512 MiB and CPU time at 20 seconds, and limits new files per invocation to 4 MiB. Earlier run files are preserved and counted separately from new output. It freezes source/split/seeds/proposals/code identities before observing costs, runs 30 mechanism tests, then compares 6/7/8-bit widths separately for compression/readable and designed-only/mined-only/human-plus-mined arms. Each arm uses its declared initial-state policy and up to eight bounded neighborhood proposals. Designed-only adds no free alphabet: an unrepresentable arm retains the two-problem denominator, zero coverage, null best/cost and every rejection. Model training and candidate program execution are both zero. Synthetic source fixtures are explicitly exposed mechanism data, not qualified LeetCode solutions or untouched heldouts.

`tiny_reference.py` adds a small support matrix for at most three concrete human seeds: exact per-variant occurrences, distinct-problem coverage, single-add savings, overlap and pair complementarity. It exhausts at most 32 dictionary/source-choice states and compares a fixed-source greedy addition policy with the finite fixed-source and joint optima. The records retain successful and failed states. These are encoding dependencies only; no semantic dependency or equivalence is inferred, and no optimality claim extends beyond that explicitly enumerated pool.

Each local result directory contains immutable predeclaration, synthetic data, human seeds, test log, per-arm receipts and a summary. Full state choices, exact sequences, source/packet/dictionary identities, eligibility failures, input and storage costs are retained locally. The staged aggregate receipts omit private sources and original tests. No neural model is included; tests exercise the scorer interface using constant spies without learning. The bounded runner uses Linux CPU affinity and resource limits; the Python modules and data use checkout-relative paths, without a task-directory fallback.

## Next gate

The mechanism checks passed; [RESULTS.md](RESULTS.md) records the synthetic results and exact receipts. Independently qualified #560/#781 successor receipts can next be wrapped by the coordinator into a real exposed-development dataset, with original/dense controls preserved. Freeze source alternatives, complete alias/family exclusions and same-budget candidate proposals before ranking. [PROTOCOL.md](PROTOCOL.md) now specifies a proposed pairwise-logistic trainable baseline, but no training has occurred. A later trained model comparison needs its own approved data/compute plan and a genuine independent evaluation population. No trained-model, 1,000-problem, generalization or M1 claim follows from this interface.
