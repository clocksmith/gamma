# Readable shared-block comparison freeze

This is a three-problem development mechanism pilot, not a substitute for the
frozen 500-problem population or any M1-M6 threshold. There is no autonomous
assembly, untouched-generalization, human-fluency, promotion or deployment claim.
The method below is declared before source fitting. A hash-bound contract is
created by `compare.py freeze`; changing code or source afterwards invalidates it.

## Population and qualification

- Public, previously exposed readable-v1 problems #547, #841 and #1091, in
  JavaScript and Python separately. No protected final 100 or protected 66 is read.
- Cross original source with the fully stored shared-breadth successor. Every
  helper, callback, official wrapper, binding and punctuation byte is encoded.
- `QUALIFICATION.md` owns behavioral/effect/complexity requirements. Before any
  production fitting, require a fresh isolated successful receipt for all 12
  exact source hashes. Syntax, representation and synthetic tests cannot open
  this gate. A blocked/failed/missing/stale receipt prevents the run.
- Rehash the qualification contract, current runner/source/policy code and
  unchanged sandbox. Rebuild the complete public/synthetic case population;
  require exact case hashes/counts, all scheduled batch executions and no failures.
  Replay every saved observation through the host comparator and predecessor
  effect comparison. A manually asserted `passed` boolean is insufficient.
- No source is executed by `compare.py`; its imported variant builder returns
  strings. Unit tests fit inert synthetic strings only.

## Factorial comparison

For each language and each cap (128 entries/7 bits, 256 entries/8 bits), fit one
dictionary on original sources and seal it. Fit a second dictionary on shared
sources with the identical policy and budget. Measure all four combinations:

1. Original source / original-fitted frozen dictionary.
2. Shared source / original-fitted frozen dictionary: source-only transfer.
3. Original source / shared-refitted dictionary: reverse transfer.
4. Shared source / shared-refitted dictionary: joint source/dictionary choice.

This yields 16 profile rows and 48 complete packets if qualification succeeds.
The baseline is a newly fitted matched pilot baseline, not invented reproduction
of the unavailable 500-problem dictionary. No other dictionary is relabeled as
the historical current best. There is no held-out inference from these three fit
programs; p95 is the maximum with this sample size.

## Coverage, entries and deterministic fitting

The existing `lagrange-select-v2/selection.py` policy is verified by inspecting
its actual ALPHABET expression: 95 printable ASCII characters U+0020-U+007E plus
LF U+000A, in that order. These 96 exact single-character strings are mandatory,
paid entries. This is not all 128 ASCII control characters. Tabs, CR, non-ASCII
and unknown characters fail rather than using an uncounted escape.

Candidate entries are complete nonblank formatted lines and windows of at most
three adjacent complete lines, at most 256 UTF-8 bytes. Multi-line entries must
occur in at least two distinct fit programs. Single-line entries may be one-off;
their support and largest selected size are reported. Full sources from either
variant are banned, including stripped equivalents. The actual solution bodies
all exceed the three-line cap. No whole-solution, placeholder, operand, hidden
state, macro expansion or problem-dependent dispatch channel is allowed.

At most 1,024 learned candidates are allowed; overflow fails rather than changing
the pool after observing results. Start with the 96 paid characters. On each
pass evaluate every remaining candidate's exact marginal total-selection cost.
Choose the smallest total; ties prefer fewer added UTF-8 bytes, then lexicographic
literal order. Accept only a strict total-selection reduction. Stop at the cap
or no positive-gain addition. Retain every accepted move and its exact cost.
IDs always put the 96 alphabet entries first, followed by lexicographically
sorted learned strings. There are no deletions, swaps, stochastic choices,
adaptive pool widening or restarts. Fewer entries than the cap are permitted and
reported; unused padding entries are not fabricated.

Each fit is bounded by 163,840 candidate evaluations and 120 CPU seconds, across
at most 160 accepted additions. Budget exhaustion is a retained failed arm, not
a truncated success. There are eight fits total, no retries. These are engineering
bounds, not claims of global or local optimality beyond the declared additions.

## Exact accounting and validation

Reuse `literals.py` for exact canonical shortest segmentation and LTD1 storage;
reuse the unchanged readable-v1 `literal_codec.py` for byte-DP, packed LTV1
encoding and verification. An independent integer-bit decoder verifies every
packet. Test exhaustive short inert strings against the existing scorer;
test malformed dictionary/hash/width/ID/length/padding controls and deterministic
reproduction across process hash seeds. No candidate execution is implied.

Report complete source UTF-8 bytes, helper bytes via source provenance, literal
bytes, `8 + 4K` dictionary framing, total dictionary bytes, selection IDs/bits,
single-character selection bits/fraction, 41-byte packet framing, padding,
packet bytes, dictionary-plus-packet bytes, median, nearest-rank p95, worst,
per-problem source/packet/dictionary hashes, whole-source count and reuse support.
The retained codec source is separately charged once per profile; do not sum it
16 times when discussing one multi-profile distribution. The full comparison
harness, JSON, duplicate source/artifact files, qualification runner, Python/Node
runtime distribution, navigation, human submission/correction controls and
runtime performance are not silently included in the compact wire total.
No runtime, solving-time or human-input reduction follows from packet size.

## Reproduce when the isolation prerequisite is available

Run from this directory with Python 3 and the standard library. No installation
or model download is required by the comparison.

```sh
python3 -B -m unittest -v test_compare
python3 -B compare.py freeze --output /tmp/readable-joint-freeze-new
python3 -B qualify.py --output /tmp/readable-joint-qualification-new
python3 -B compare.py run --freeze /tmp/readable-joint-freeze-new \
  --qualification /tmp/readable-joint-qualification-new/qualification.json \
  --output /tmp/readable-joint-comparison-new
```

All output directories must be new. The actual qualification result filename is
the one emitted by the qualification CLI. Never substitute a manually marked
receipt for a blocked isolated run.
