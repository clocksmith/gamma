# Complete line-span search

[Experiment index](../INDEX.md) · [Frozen candidate pool](spans-v1/contract.json) ·
[Result](spans-v1/summary.json) · [Execution](spans-execution-v1/report.json)

The next literal-only round enumerates every contiguous line span in the same
three frozen source alternatives for the same twenty development problems.
The previous admission rule is unchanged: no whole-program literals, no unique
function-header/body shortcut, and large pieces must occur in multiple problems.
Of 1,477 distinct spans, 341 are admitted.

Exact shortest segmentation over that pool yields 62 used strings, 74 selections
and 444 selection bits at six bits per choice. All twenty programs fit within
64 entries. Per-problem minimum counts are retained in the result. This reaches
the minimum selection count for this finite pool and these source alternatives;
it is not a global optimum over arbitrary substrings or rewritten programs.

| Candidate | Strings | Selections | Selection bits | Dictionary bytes | Complete package bytes |
|---|---:|---:|---:|---:|---:|
| Shared baseline | 79 | 154 | 1,078 | 3,507 | 4,468 |
| Prior greedy winner | 58 | 77 | 462 | 4,086 | 4,972 |
| Complete span pool | 62 | 74 | 444 | 4,522 | 5,405 |
| Equal-length compaction | 59 | 74 | 444 | 4,126 | 5,009 |

Fewer selections again costs more storage. Only three strings are shared across
the chosen programs, accounting for 15 selections. Large prefixes and duplicated
stored text remain visible; this does not establish more reusable programming
primitives. The old candidates remain valid tradeoffs.

The existing Linux judge on host128 executed all twenty decoded source/packet
pairs: 3,834/3,834 development output and input-preservation checks passed. Expected
outputs remained outside the sandbox. The execution receipt retains raw outputs,
runner, oracle, codec and source identities. Nine focused search/admission tests
passed locally. No source semantics changed, models ran, protected problems were
opened, or autonomous solutions were generated.

Reproduce from this directory using new output paths:

```bash
python3 -B -m unittest -v test_spans test_compare
python3 -B spans.py --output /tmp/literal-spans
python3 -B verify.py --packages /tmp/literal-spans --output /tmp/literal-spans-execution
```

## Round after the first explorer deployment

[Equal-length compaction](compact-v1/summary.json) keeps every per-problem minimum
count and searches alternative segmentations by deleting used candidates from
the full pool. Five accepted deletions across 361 evaluations reduced the
dictionary from 4,522 to 4,126 bytes, while retaining 74 selections and twenty
complete programs. The measured local run took 12.67 seconds. This is a bounded
deletion search, not a minimum-dictionary proof.

The [separate execution receipt](compact-execution-v1/report.json) records another
3,834/3,834 passing checks on the new packets. Five entries are now shared by
multiple selected programs, accounting for 20 selections. The prior greedy
package still costs 37 fewer total bytes, but needs three more selections and
18 more input bits. Both remain visible.

A [further storage-frontier round](frontier-v1/summary.json) allowed up to 75, 77
or 80 selections under the same 64-entry cap, minimizing complete package bytes.
All three searches returned the identical 59-string, 74-selection result after
361 evaluations each. This is a retained negative result for that search rule.
[Byte comparisons](frontier-v1/verification.json) establish identical dictionaries,
all packets and all decoded sources, so these reuse the compact execution receipt
instead of claiming three more independent runs. Folder suffixes 75/77/80 denote
selection allowances; every manifest still declares a 64-entry dictionary cap.

```bash
python3 -B spans.py --compact --output /tmp/literal-compact
python3 -B verify.py --packages /tmp/literal-compact --output /tmp/literal-compact-execution
python3 -B frontier.py --output /tmp/literal-storage-frontier
```

The [live set explorer](https://256.one/labs/two-button/compositions/) displays
the distinct packages, exact strings, program sequences, storage and input
costs. It exports explicitly recorded solutions, not predictions.

Next research should expand the source rewrite pool or change fragment search
rather than repeat the same greedy deletions. A new source rewrite needs a new
hash, independent execution, matched costs and a separate result; protected
generalization remains unopened.
