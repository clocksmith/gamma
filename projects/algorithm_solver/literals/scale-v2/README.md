# Eighty problems: select literals by actual encoding savings

This 3a successor fixes the frequency-ranking/truncation weakness: a proposed
string earns admission only after exact resegmentation measures a positive
selection reduction. It expands the exposed development set from 60 to **80
problems**, retaining both **128-entry / seven-bit** and **256-entry / eight-bit**
flat languages. Every source character still comes from literal concatenation.
There are no whole-program entries, holes, hidden helpers, or source escapes.

The best eight-bit candidate represents all 80 supplied programs in **6,413
selections**, median **63**, versus **9,218** for matched frequency truncation
and **7,933** for a matched 64-merge lexical control. Its complete binary package
is **11,781 bytes**, including dictionary, per-program headers and padding.
These are reconstruction/compression results, not autonomous solving or human
typing measurements. Seven/eight bits means **per selection**, not per program.

## Matched results

All rows below use the same 80 compact source programs, 96 charged printable
ASCII/newline entries, exact shortest segmentation, and source-execution evidence.
Only dictionary construction differs. The lexical control has fewer than 256
entries because its fixed 64-merge schedule runs out of eligible proposals; this
is the earlier method's bounded control, not a fully optimized competitor.

| Width | Dictionary method | Entries | Total selections | Median | Worst | Complete bytes |
|---|---|---:|---:|---:|---:|---:|
| 7 | Frequency/truncation | 128 | 12,576 | 134 | 816 | 15,194 |
| 7 | Lexical merge control | 128 | 11,261 | 120.5 | 773 | 13,985 |
| 7 | Measured marginal gain | 128 | **10,155** | **107.5** | 759 | **13,002** |
| 8 | Frequency/truncation | 256 | 9,218 | 96.5 | 740 | 14,867 |
| 8 | Lexical merge control | 213 | 7,933 | 80.5 | 647 | 12,713 |
| 8 | Measured marginal gain | 256 | **6,413** | **63** | 517 | **11,781** |

The eight-bit reduction is 30.4% against frequency truncation and 19.2% against
the lexical control on identical source. Separately, with measured selection on
both sides, compact scope-safe source uses 6,413 selections versus 7,866 for
longer canonical source. [All twelve comparisons](audit.json) preserve both
source arms rather than attributing source shortening to dictionary selection.

On the **original 48 fitting problems**, the new eight-bit package uses **3,601
selections**, median 59.5, versus the retained prior package's **5,345**, median
95. Both saw those 48 development problems; the successor also saw 32 others.
This is a useful overlapping-set comparison, not a heldout result.

## Techniques and limits

1. Resolve lexical bindings before shortening names. Preserve properties,
   closure references, recursion and shared class declaration bindings. Use an
   AST printer for compact source; the resulting exact text is stored and tested.
   There is no runtime printer in the decoder.
2. Propose contiguous spans of two to four entries from current shortest
   sequences, requiring occurrence in at least two distinct problems and at most
   160 UTF-8 bytes. Whole programs are excluded. Frequency orders a bounded
   shortlist of twelve; it does not determine acceptance.
3. For each shortlisted string, recompute exact shortest sequences for affected
   programs. Choose actual net selection savings, counting overlapping matches
   jointly. Record every alternative score and accepted decision.
4. Reclaim learned entries no longer used after resegmentation. At each budget,
   test twelve complete remove/add dictionaries and retain a beneficial swap.
   Canonical and compact arms reclaimed 20 and 17 slots respectively; all four
   budget-end swaps improved measured cost. [Decision traces](search-v2/).
5. Retain all 96 ASCII/newline entries, including unused ones. This avoids missing
   punctuation such as the old `@` failure, but coverage from this fallback is
   deliberately not called semantic composition. No protected vocabulary was
   altered; this is a new exposed-development experiment.

For the eight-bit compact winner, **53.2% of selections are single characters**;
they emit 18.4% of source characters. At seven bits those figures are **75.7%**
and 41.5%. Much reuse remains syntax and spelling. The winner has 236 entries
used across problems, but that count includes shared characters and does not
mean 236 reusable algorithms. A median of 63 selections and worst case of 517
remain far from a handful of meaningful algorithm operations.

The shortlist, sequential decisions and bounded swaps are heuristics. Exact
resegmentation does not make vocabulary discovery globally optimal. This fixes
a concrete implementation weakness; it is not a research novelty claim.

## Sources, coverage and execution

[Contract and exact IDs](contract.json) · [all sources and hashes](generated/manifest.json)
· [additional source provenance](additional-provenance.json).

The previous 60, including their twelve formerly heldback cases, are now exposed
development material. The additional twenty are **3, 4, 7, 9, 11, 14, 20, 28, 34,
35, 42, 53, 55, 58, 62, 64, 67, 69, 70, 1046**, taken from a previously qualified
development catalog. They add sliding windows, sorted search, stacks, dynamic
programming, numeric operations, and a heap. The first 60 retain their
[upstream attribution and notices](../clusters-v1/ATTRIBUTION.json); the added
sources retain their catalog attribution without inventing a new license grant.
No recognition ledger, protected composition problem, or admission status changes.

The [final native receipt](qualification/report.json) records **240/240 source
versions**, **25,236/25,236 checks**, and **8,412 distinct development cases**.
The new twenty use 1,653 independently authored bounded cases; the original sixty
reuse 6,759 cases. Three source versions repeat these cases. Expected results
stay outside the Linux sandbox. Rewrites must match independent outputs and
the original's input effects. These are finite domain tests, not formal
equivalence, official judge acceptance, or maximum-size execution qualification.
A [fresh-copy rerun](qualification-rerun-v1/README.md) on 2026-10-21 reproduced
these counts, hashes and all 510 observation files; only per-call times differed.

The [independent packet audit](audit.json) decodes **960** selected/control
packets, checks source/qualification identities and byte costs, and checks raw
observation hashes. Selected packets reuse native evidence through identical
decoded source hashes; the audit is not another JavaScript execution run.

Preserved failures:

- [First source qualification](failed-v1/qualification/report.json): the inherited
  class renamer broke #1046 constructor references, causing 166 failed checks.
  The successor unifies the inner/outer declaration identity. Both failed source
  versions, original observations and old implementation remain in `failed-v1/`.
- [Initial search](search-v1/summary.json): the first frequency control counted
  truncated end-of-stream windows repeatedly. `search-v2` fixes that control and
  adds the lexical comparison. The measured-gain winners were unchanged. Initial
  results and the exact earlier search implementation remain available.

## Inspect and reproduce

- [Seven-bit dictionary](search-v2/compact-marginal-128/dictionary.json) and
  [all seven-bit sequences](search-v2/compact-marginal-128/manifest.json).
- [Eight-bit dictionary](search-v2/compact-marginal-256/dictionary.json) and
  [all eight-bit sequences](search-v2/compact-marginal-256/manifest.json).
- [Rewritten programs](generated/sources/), [search](search.py),
  [execution](verify.py), [oracles](checks.py), [audit](audit.py).

Run the following in a fresh copy of this directory beside the existing
`clusters-v1`, `pass2`, codec, checks and harness files. Preserve published output
directories; generators deliberately refuse to overwrite them. Node needs the
existing Acorn, eslint-scope and escodegen installation; execution needs the
existing Gamma Linux sandbox. No model download or dependency installation is
required. On 128, use the existing Python 3.13 interpreter recorded in
`../clusters-v1/REPRODUCE.md`.

```sh
node test-generate.cjs
python3 -m unittest test_search.py
node generate.cjs . generated
python3 verify.py --output qualification
python3 search.py --output search-v2
python3 audit.py --output audit.json
```

Qualification took 17.84 seconds. Search took 10.45 seconds on canonical source
and 4.40 seconds on compact source (one CPU worker); neither hit its recorded
300-second/2,200-trial limit. Execution and search time are development costs,
not query-time synthesis latency. The active directory remains under its 128 MiB
artifact cap, retaining failed attempts. Live BITS/editor alphabets are unchanged.
