# Matched macro / fragment development comparison

Owner authorization: 2026-11-09, “go ahead, get it done”, following the fully
charged 64/128/256-entry comparison. This resumes this composition experiment;
protected populations and prior results remain unchanged.

Population: the historical 300 development-fit and 100 exposed development-
validation IDs in cost-decomposition-v1/contract.json. Acquire exact qualified
JavaScript and Python bytes only through the existing KnownSpecService boundary.
Keep unavailable, rejected and unsupported IDs in the original denominators.
Fit and select dictionaries only on fit sources. Freeze dictionaries before
opening validation source bytes. This is exposed development, not unseen evidence.

Compare exact source representations first. Both arms reproduce source bytes,
including wrappers, names, constants and whitespace. Existing source receipts
apply only to those exact reconstructed bytes, with their original caveats.
Python compact transformation is a separately labeled static diagnostic until
fresh native qualification exists; it cannot increase qualified coverage.
No candidate execution, model calls, corpus download or protected access occurs.

B: existing fragment-spelling-v1, one escape code; remaining entries are exact
fragments. A: lossless AST-derived fixed-arity source macros and exact fragments
compete in one table. Code 0 spells bytes (9 bits/byte plus closing bit), code 1
concatenates operands, remaining codes name fragments or macros. Macro arity
comes from its table entry; no END token. Each operand is one recursively encoded
expression. Multiple pieces need a charged CONCAT plus a fixed-width count
(ceil(16/width) code words). Root sequences end at the packet bit-length boundary.
This is a source macro DSL, not the twelve-op semantic codec or a new solver.

All primary codes cost width bits. Charge spelling payloads, transition bits,
CONCAT counts, operands, nine-byte framing and padding. Report primary selections
separately from payload bits and total_bits/width word-equivalents. Mean, median,
nearest-rank p95 and worst are conditional on represented sources; report complete
coverage and paired intersections beside them. Dictionary/decoder storage is
separate from per-program input. No measured human interaction claim.

Candidates: token-aligned spans up to eight tokens/160 bytes; AST shells up to
four proper child operands, with full and one-hole specializations. Each entry
must occur in at least two distinct fitting source hashes (byte-identical problem
solutions count once; no claim of complete semantic-family independence). Exclude whole sources,
function units and complete function-body spans. Original bodies remain banned
for both candidate pools. Never insert a problem identifier or answer dispatcher.

Selection: choose between deterministic reuse-weighted and overlap-aware greedy literal
ranking by exact aggregate fit packet bits; exact bit segmentation
for fixed dictionaries over permitted AST occurrences and literal matches.
Mixed search starts from the matched literal table,
screens at most 24 reusable macro candidates, and accepts only strict aggregate
fit packet-bit improvements (framing and byte padding included) after replacing its least-used literal. This is heuristic
selection, not an optimal codebook claim. Preserve all attempted fit scores.
Widths receive the same candidate policy and trial limit. Validation never
selects candidates or determines acceptance. Report the matched literal control
inside the mixed protocol to distinguish codec overhead from macro improvement.

Budget: one CPU worker, no GPU; 2 GiB address-space target, 64 KiB/source,
400 IDs/language, 24 macro trials/width/language, 256 MiB retained private output.
Retain private dictionaries/packets outside Git, publish hashes and aggregate
measurements only. Focused judge/lane and codec tests precede the run. Independently
round-trip every final packet; reject malformed/trailing/noncanonical payloads.
Novelty, autonomous solving, current-runtime execution, and generalization remain
unestablished by this representation experiment.

## Review amendment before rerun

The first frequency-only attempt is retained with its implementation and results
outside Git. The rerun adds an overlap-aware literal candidate selector; only fit
packet bits choose between it and frequency ranking. Validation does not select
that choice. All three widths receive both candidates and the same macro budget.

Primary selections count opcode/entry dispatches, including spelling and CONCAT.
`count_words` separately counts CONCAT count words; spelling payload and closing
bits remain separate. Reject root CONCAT, CONCAT directly inside CONCAT, adjacent
spelling runs within one sequence, empty spelling, count < 2 and unused opcodes.
Single operands compete against charged multi-piece CONCAT operands in the DP.

Ban whole-body spans before hole extraction, including arrow/method bodies, and
require non-whitespace static shell bytes. Compact mining additionally inherits
original pre-transform body bans. Fit compact dictionaries on fit transforms,
seal them before transforming validation, and report full paired intersections
with original fallbacks plus transformed-only validation subsets. Compact source
successors remain unqualified; exact-source primary arms retain historical scope.

The second attempt is retained too. A subsequent adversarial test added the
missing JavaScript class-unit literal exclusion. The final replay uses that fix
with unchanged fitting policy, populations and trial limits. Earlier validation
scores do not select the rerun's dictionaries or candidates.
