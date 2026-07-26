# The Atlas and Clockwork Challenge: Organizer Rubric

## 1. Purpose

This document defines strict organizer-owned verification for the two
independent problems in the public statement.

The Seal is not a contestant problem. It is the fixed acceptance procedure,
fixed interpreter, measured resource gate, and theorem used by the organizer.

The final decision is:

PASS = PASS_A OR PASS_B.

A submission that passes either route is accepted even if the other route is
absent or fails.

---

## 2. Decision vocabulary

Each route receives exactly one terminal verdict:

- PASS: every mandatory condition for that route is established.
- FAIL: the submission is well formed but violates at least one mandatory
  inequality, exactness condition, or resource limit.
- INVALID: the submission cannot be evaluated under the fixed specification,
  uses prohibited information or arithmetic, has ambiguous serialization, or
  omits a mandatory artifact.

No partial credit changes a terminal verdict. Diagnostics may rank failed
research submissions, but they do not weaken acceptance.

---

## 3. Organizer-owned objects

Before releasing an instance, the organizer freezes and hashes:

1. the finite input and block boundaries;
2. all observable streams and availability times;
3. w, r, FDAC, and framing rules;
4. the canonical serializer;
5. the fixed interpreter for each route;
6. exact operation-count and memory-count semantics;
7. targets and finite bounds;
8. the reference execution protocol;
9. the complete verifier;
10. a private adapter, if the instance is embedded in another application.

Contestants do not submit or modify these objects. Their fixed length is the
stated L_fixed,A or L_fixed,B. The organizer publishes hashes of all public
frozen objects before accepting solutions. Any change creates a new instance.

---

## 4. Canonical serialization and disjoint accounting

### 4.1 Four variable channels

For each route, the serializer produces:

- C: certificate bytes;
- Z: label or auxiliary-choice bytes;
- Y: FDAC payload and its final partial-byte length;
- F: framing bytes.

The channels are concatenated in the fixed order F || C || Z || Y. Framing
contains only canonical lengths, block counts, modes, and padding counts. It
contains no model parameter or prediction table.

### 4.2 Exactly-once rule

Each non-fixed object used during reconstruction has one owner:

| Object | Required owner |
|---|---|
| transition or probability table | C |
| instruction sequence and constants | C |
| non-fixed state initializer | C |
| block label or auxiliary selector | Z |
| coded data symbols | Y |
| channel lengths and block boundaries | F |

The verifier rejects an object duplicated across channels, an uncharged used
object, a label present in both Z and the FDAC source alphabet, a table expanded
from an uncharged seed, or a certificate charged again as executable size.

### 4.3 Exact total

The only acceptance length is

L_total = L_fixed + 8|F_bytes| + 8|C_bytes| + 8|Z_bytes| + |Y_bits|.

For a byte target T, acceptance requires ceil(L_total/8) <= T.

No ideal interval length, Shannon length, entropy estimate, projection,
hypothetical amortization, or extrapolation may replace this integer.

---

## 5. Fixed FDAC verification

The verifier implements the public FDAC recurrence literally. For every symbol
it records position, block, numerator, pre-update interval, split, selected
subinterval, renormalizations, emitted bits, and post-update state.

The independent decoder records its payload position, code register, decoded
bit, interval trace, reconstructed state, and numerator.

A route fails unless:

1. encoder output is bit-for-bit deterministic;
2. decoder reconstructs exactly n bits;
3. reconstructed data equals the frozen instance;
4. encoder and decoder numerator traces agree everywhere;
5. a second clean encoding emits the identical payload;
6. all termination and partial-byte rules are exact;
7. only specified zero fill is read after the payload.

An ideal rational interval is diagnostic only.

---

## 6. Common causality and replay gate

At every position t, the verifier compares the encoder state after the true
prefix with the decoder state after the reconstructed prefix. It demands exact
equality of visible history, paid-label availability, every state register,
every observable, every numerator, every boundary transition, and every
post-symbol update.

A route is INVALID if a probability uses x_t before decoding, any later
symbol, a label before its codeword is available, an observable before its
declared time, nondeterministic iteration, wall-clock state, thread scheduling,
external files, network state, or unspecified floating-point behavior.

Whole-block-dependent labels are allowed only because their exact codewords are
charged in Z and available before first use.

---

## 7. Problem A rubric

### A0. Artifact completeness

Problem A must provide the label alphabet, prefix code, all block labels,
finite state representation, initial state, transition, numerator construction,
all tables and constants, canonical serializer input, causality proof,
joint-replay proof, exact length ledger, and exact resource ledger.

A missing mandatory item gives INVALID.

### A1. Label-code proof

The grader verifies directly that every label has one codeword, no codeword is
a prefix of another, concatenation parses uniquely, every used label is
declared, and Z is exactly the canonical concatenation.

### A2. Finite-state proof

The grader enumerates states when the bound permits and always executes the
full trace. The initial state and every successor must lie in S, maps must be
single-valued, every numerator must lie in {1, ..., 2^r-1}, and equal inputs
must give equal outputs.

### A3. Atlas target gate

Compute

L_A = L_fixed,A + |C_A| + |Z_A| + |Y_A| + |F_A|.

All must hold:

L_A <= T_A,

|C_A| <= B_C,  |Z_A| <= B_Z,  |S| <= B_S,

Ops_A(x) <= B_O,  Mem_A(x) <= B_M.

Equality at a bound passes.

### A4. Atlas route verdict

PASS_A is issued if and only if A0 through A3 and all common gates pass.
Problem B is not loaded or consulted.

---

## 8. Problem B rubric

### B0. Artifact completeness

Problem B must provide the bounded state layout, exact initial state, complete
update and numerator instruction sequences, all constants and tables,
canonical serializer input, instruction-legality proof, state-closure proof,
causality and joint-replay proofs, exact global length ledger, and exact
resource ledger.

A missing mandatory item gives INVALID.

### B1. Independence from Atlas

The grader starts from the separately frozen teacher. The route is INVALID if
it imports an Atlas label, state, table, certificate, teacher, score credit, or
artifact requiring an Atlas solution. The common input and fixed FDAC do not
create dependence.

### B2. Instruction legality

For every instruction, the grader checks opcode membership, operand type and
width, overflow behavior, rounding and division, table bounds, deterministic
branches, output width, and exact counted cost. An undeclared instruction or
arithmetic semantic gives INVALID.

### B3. State closure

The proof establishes closure for all reachable states when universal closure
is requested. The verifier also checks the full observed trace. Out-of-range
lookup, undeclared state, or overflow outside declared semantics gives FAIL.

### B4. Clockwork target gate

Compute

L_B = L_fixed,B + |C_B| + |Z_B| + |Y_B| + |F_B|.

All must hold:

L_B <= T_B,

|C_B| <= B'_C,

StateBits(U) <= B'_S,

Ops_B(x) <= B'_O,  Mem_B(x) <= B'_M.

The teacher comparison is diagnostic. Passing depends on the absolute target.

### B5. Global degradation rule

The only exact coded-length difference is

Delta L = (|C_B| + |Z_B| + |Y_B| + |F_B|) - L_teacher.

Per-symbol rational log loss may locate errors, but it must be labeled
`diagnostic_nonadditive` and cannot substitute for Delta L.

### B6. Clockwork route verdict

PASS_B is issued if and only if B0 through B5 and all common gates pass.
Problem A is not loaded or consulted.

---

## 9. Resource acceptance

### 9.1 Mathematical resource ledger

The fixed interpreter counts exact operations under the instance. This count
is reproducible but does not by itself imply a physical execution bound.

### 9.2 Reference execution gate

When physical limits apply, the organizer runs the fixed interpreter under a
frozen protocol specifying machine and processor configuration, core count,
memory limit and measurement method, interpreter hash, operating-system image,
input and output hashes, process-tree accounting, encode and decode commands,
repetition policy, and maximum encode and decode times.

Physical eligibility requires both the mathematical resource ledger and the
measured fixed-interpreter receipt to pass.

An instance may instead publish a conservative calibrated implication theorem
from operation and memory bounds to physical acceptance, but it must be frozen
and proved for the fixed interpreter. Without it, measured execution is
mandatory.

### 9.3 No contestant executable

Contestants submit finite mathematical objects and proofs, not encoders,
decoders, manifests, shell commands, or resource monitors. The organizer-owned
interpreter serializes and evaluates those objects. A private application
adapter is organizer-owned, fixed, and charged in L_fixed.

---

## 10. Controls and audit artifacts

Controls create no acceptance credit. The organizer publishes the baseline or
teacher payload, submitted payload, exact global difference, separate C/Z/Y/F
lengths, numerator-trace hash, state-trace hash, payload hash, decoded-output
hash, deterministic second-encode hash, operation count, peak interpreted state
bytes, and physical receipt when required.

A disagreement between a claimed integer and verifier output is resolved in
favor of the verifier.

---

## 11. Uniformity and forbidden tailoring

A construction may depend on the finite instance only through objects that are
explicitly serialized and charged. It may not hide instance bits in symbol
names, noncanonical table order, proof prose, unused constants, undefined
behavior, timing, addresses, hash collisions, interpreter choices, floating
point payloads, or alternative serializations.

The serializer rejects irrelevant degrees of freedom where practical. All
remaining submitted bits are charged regardless of whether they are called
parameters, proofs, metadata, or padding.

---

## 12. Seal acceptance theorem

### Theorem

Assume the frozen serializer, FDAC implementation, verifier, and interpreter
satisfy their published specifications.

If PASS_A is issued, the Atlas objects alone define a finite, deterministic,
exactly reversible construction whose complete charged length is at most T_A
and whose resources satisfy the Atlas bounds.

If PASS_B is issued, the Clockwork objects alone define a finite,
deterministic, exactly reversible construction whose complete charged length
is at most T_B and whose resources satisfy the Clockwork bounds.

Therefore PASS_A OR PASS_B is sufficient for final acceptance.

### Proof

For either passing route, framing uniquely separates C, Z, and Y. The fixed
interpreter reconstructs the finite predictor from C, obtains every permitted
auxiliary choice from Z, and computes a dyadic numerator before each symbol.
Joint replay gives equality of encoder and decoder numerator sequences. The
FDAC inverse therefore reconstructs every symbol exactly. The exactly-once
ledger includes every non-fixed bit, and the absolute target gate bounds the
total together with fixed machinery. The resource gate supplies the required
mathematical and, when applicable, physical bounds. Neither argument refers to
the other route. QED.

---

## 13. Final decision table

| Atlas | Clockwork | Final |
|---|---|---|
| PASS | any verdict or absent | PASS |
| any non-PASS verdict or absent | PASS | PASS |
| absent | absent | INVALID |
| FAIL | FAIL | FAIL |
| INVALID | FAIL or absent | INVALID |
| FAIL or absent | INVALID | INVALID |
| INVALID | INVALID | INVALID |

The organizer reports route verdicts separately even when the other route has
already established final acceptance.
