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

The next bounded round keeps all per-problem minimum counts and searches alternate
equally short segmentations for a smaller dictionary. It runs after the first
explorer deployment; its result must be recorded separately.
