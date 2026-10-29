# WGSL Repair V12 Controlled-Lane Design

> Historical freeze: V12 has now completed. See the
> [V12 controlled-data result](wgsl-repair-v12-2026-07-13.md). Statements below
> that no V12 result exists describe the state when this design was frozen.

V12 is harness-ready and has no training result. It fixes two design defects
found while interpreting V10: the three 1,200-row data lanes shared the same
first 800 rows, and one 64-token generation ceiling was too short for a small
but real external-kernel repair stratum.

The original machine-readable design receipt recorded a seed-11-first
selection followed by replication. Before any V12 capability outcome was
opened, commit `df8da5d160a12aedd69c1a2ea541af1f3dd7910f` strengthened that
contract to require all three lanes at all three seeds. The checked-in
[evaluation policy](../../tools/policies/wgsl-repair-v12-evaluation-policy.json)
is authoritative for execution and public-split access; the JSON design
receipt remains the historical initial freeze.

Before any V12 verifier score was opened, evaluation execution was also made
explicitly evaluation-only: completion generation omits GRPO policy/reference
log-probability passes that the compiler metrics do not consume. The verified
group records carry `rolloutPurpose="evaluation"`, and Doppler rejects those
groups if they are passed to rejection-sampling or DPO row builders. Sampling,
seeds, completions, compiler checks, denominators, and the lane decision are
unchanged.

## Full-lane data comparison

Every lane at seeds 11, 29, and 47 executes 1,200 microsteps with accumulation
8, or 150 optimizer updates. Gamma orders every row by
`sha256(seed + "\0" + rowId)`, records the resulting order hash, and consumes
the full lane once. The model, rank-32 adapter, learning rate, precision,
sequence length, and checkpoint rule are identical.

The seed-11 orders are:

| Lane | Doppler rows | Zero-TVM rows | Row-order SHA-256 |
| --- | ---: | ---: | --- |
| anchor | 1,200 | 0 | `d03f28eafc80a94958a7d0e24d07f7f6214c0dfebe3212f2572abe73d39c744c` |
| external20 | 960 | 240 | `033c182d1c1e28adf71977934803c0d539487dfa466db49d7cd1e0a09794593e` |
| random20 | 1,200 | 0 | `29fbb49b0a9350f101100b84c24bcf893d9a2d53741885a5fabeafd53b7f908e` |

This comparison must train a new anchor. V10's 800-step adapter is a successful
compiler-repair baseline, but it is not a valid control for the 1,200-step,
seed-ordered V12 lanes.

## Short and long repair strata

The split rule uses only the visible broken span:

```text
short: span.broken.length <= 128 Unicode code units, maxTokens = 64
long:  span.broken.length > 128 Unicode code units, maxTokens = 640
```

The threshold and ceilings were derived from the 1,200-row external20 training
lane. Under the pinned Qwen tokenizer, its short partition has a maximum
54-token target. Its long partition contains 22 rows, 21 targets over 64
tokens, and a maximum 619-token target; 640 adds a 21-token margin. Holdout
references do not assign tasks to a stratum.

The immutable partitions are:

| Task set | Short | Long | Original total |
| --- | ---: | ---: | ---: |
| diagnostic | 275 | 10 | 285 |
| public test | 290 | 9 | 299 |

Every policy must run both strata. Overall pass rates are recombined over all
original tasks and samples; the long denominator cannot be omitted because it
is harder or more expensive. Short and long results are also reported
separately.

## Experimental order

V11 answered the optimizer question from the existing seed-11 SFT checkpoint:
one diagnostic-only GRPO update improved public pass@1 from 88.29% to 94.98%,
while the matched DPO lane regressed and was rejected. V12 answers the data
question from nine new base-initialized SFT runs. Mixing the new row order,
external data, longer decoder, and an optimizer in one lane would destroy
attribution. See the
[V11 optimizer result](wgsl-repair-v11-2026-07-12.md).

The V12 data gate is:

1. train anchor, external20, and random20 at seeds 11, 29, and 47 under their
   checked-in workloads;
2. evaluate all nine adapters on the same frozen short and long diagnostic
   strata;
3. select external20 only if it beats anchor on recombined diagnostic pass@1
   at every seed, beats random20 on mean recombined diagnostic pass@1, and does
   not reduce mean long-stratum pass@1 versus anchor;
4. record the treatment decision without reading the public or sealed semantic
   outcomes;
5. open the frozen public diagnostic only after all nine diagnostic receipts
   are sealed, then run the sealed semantic suite once for the selected result.

Compilation remains a partial reward. Promotion still requires dispatch,
CPU-oracle, numerical, metamorphic, and historical-regression checks. The
machine-readable design receipt is
[wgsl-repair-v12-design-2026-07-12.json](wgsl-repair-v12-design-2026-07-12.json).
