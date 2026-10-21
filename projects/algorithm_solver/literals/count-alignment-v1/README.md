# Source-informed integer-count alignment

This goals 2a/2b pilot asks whether general, complete count-read and count-increment definitions can align correct sources across problems 560 and 781. Preserve both helper-aligned and no-helper alternatives as candidates for input, storage and readability tradeoffs. Readability and memorability have not yet been measured; larger installation storage alone does not reject the design.

The [component charter](CATSCAN.md) preserves the existing Algorithm Solver authority and gates. [Aggregate evidence](evidence.json) records source and artifact hashes without exporting full private programs, original test bodies, claim tokens or ledger contents.

## Mechanism and contract

[`rewrite.py`](rewrite.py) contains the exact general JavaScript/Python helper definitions and a bounded, source-hash-guarded replacement mechanism. It recognizes four reviewed predecessor identities, replaces uniquely witnessed spans, includes all helper text, checks the expected successor hash, and parses Python syntax. This is not general semantic equivalence or an AST rewrite engine. It never runs the supplied source.

The integer count container is private to the program. Reading an absent key returns zero without inserting it; increment changes only that key by one and returns no value. Keys are integers, excluding booleans, NaN, objects and strings; JavaScript keys and counts stay safe integers. There are no input aliases, callbacks, global effects or observable iteration-order guarantees. Expected per-operation time is O(1), with O(u) map storage and implementation-dependent overhead. Increment calls read. Dense, bounded arrays and object/dictionary predecessors remain distinct eligible implementations; this pilot does not claim maps are universally preferable.

Python helper metadata is registered through the existing [`algsolve/synth/components.py`](../../algsolve/synth/components.py) API, in memory only. No second registry is introduced or persisted. The existing registry normalizes its helper source to one terminal newline; emitted Python source includes an additional explicitly charged separator newline. The combined helpers occupy 155 JavaScript / 198 Python bytes.

## Portable use

From the repository root, supply the existing public component-registry path explicitly:

```bash
python3 projects/algorithm_solver/literals/count-alignment-v1/rewrite.py \
  --components projects/algorithm_solver/algsolve/synth/components.py --describe

python3 projects/algorithm_solver/literals/count-alignment-v1/test_rewrite.py \
  --components projects/algorithm_solver/algsolve/synth/components.py
```

To reproduce a reviewed source transformation, obtain its authorized witness externally and provide its path yourself. The package supplies no private witness files or default machine paths:

```bash
python3 projects/algorithm_solver/literals/count-alignment-v1/rewrite.py \
  --components projects/algorithm_solver/algsolve/synth/components.py \
  --witness 0560-python /authorized/local/witness.py \
  --output /authorized/local/new-output-directory
```

Repeat `--witness KEY PATH` for any of `0560-javascript`, `0560-python`, `0781-javascript` and `0781-python`. Every supplied file must match its pinned predecessor and produce its pinned successor. All witnesses are checked before creating output. Existing output directories are refused, source files are not changed, and generated files/manifest do not establish a new execution qualification or admission. Runtime qualification still requires the unchanged isolated judge and its original evidence contract.

The focused tests use synthetic text and the public existing registry only. They check exact-span/hash guards, separators, dependency visibility, registry collision handling and preservation of existing outputs. They neither execute candidate programs nor substitute for the pending primitive runtime suite.

## Measured evidence

The original private experiment qualified eight full program identities: predecessor/successor for each problem in each language. Independent saved-output auditing verified **136 calls and 3,612 program observations**: 672 original, 16 public and 2,924 independent observations, with eight observer controls. Original problem 560 cases 25 and 27 exceed pinned input-value bounds; their unchanged results remain compatibility diagnostics. Finite tests are not full-domain proof.

The fixed-table comparison measured and independently audited **54 cells**, followed by a **192-state exact restricted reference**: eight helper subsets, four source assignments, two languages and three widths. The reference reports 288 exact marginal additions and 144 pair comparisons. Each helper has two distinct supporting problems and two supporting successor variants; those are not four independent problems. All strings, runtime operands, wrappers and whitespace are charged. Whole-program entries are forbidden. Line tables still include blank and punctuation-only lines, so they do not establish a complete human-readable vocabulary.

Six-bit fixed-successor comparison, across both problems:

| Language | Encoding | Selections | Payload bits | Packet bits | Installed dictionary bytes | Dictionary + packets |
|---|---|---:|---:|---:|---:|---:|
| JavaScript | Exact lines | 51 | 306 | 968 | 1,825 | 1,946 B |
| JavaScript | Lines + joined helpers | 41 | 246 | 912 | 1,984 | 2,098 B |
| Python | Exact lines | 46 | 276 | 936 | 1,982 | 2,099 B |
| Python | Lines + joined helpers | 36 | 216 | 872 | 2,184 | 2,293 B |

In each language, ten fewer selections saves **60 payload bits**. Packet savings differ (56 JavaScript / 64 Python bits) because each packet pads to a byte. Dictionary installation rises separately by 159 / 202 bytes. These are distinct objectives; no frequency-of-use model or amortization break-even was established. The common 8,240-byte decoder is reported separately. Complete helper source remains included in every decoded program.

Read and increment produce additive selection savings in this restricted pool. Python's small extra packet-bit saving from their pair is rounding, not semantic synergy. Joined and individual definitions overlap and substitute for one another in parses. When both predecessors are also eligible, this additive-pool reference chooses the unchanged predecessors and no extra helper for measured input/package minima at all three widths. That is not a global optimum, a reason to discard the readable helper candidate, or a test of whether removing/relearning base entries would improve it.

The prior no-helper predecessors take 41 JavaScript / 34 Python selections under their common exact-line tables. Keep those controls alongside the helper-based alternatives. Future experiments can measure source/library changes and human usefulness without silently changing these frozen results.

The separate **258-case primitive runtime suite has not run**. These records authorize no admissions, BITS profile promotion, autonomous-composition claim, M1 claim or external publication. All three private receipt sets are preserved unchanged; this portable package contains their aggregate/hash summaries rather than a claim to reproduce private qualification without its inputs.
