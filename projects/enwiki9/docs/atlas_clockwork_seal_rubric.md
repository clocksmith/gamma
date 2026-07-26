# Independent Finite Prediction Olympiad: Organizer Rubric

Rubric version: `ACS-RUBRIC-2`
Required Seal: `ACS-SEAL-2`

## 1. Scope

This rubric grades five independent mathematical routes under the separately
versioned Seal. It does not redefine coding, serialization, accounting,
resources, proof visibility, runtime isolation, or transfer. Those meanings
come only from the frozen Seal.

The final rule is

\[
\boxed{
\operatorname{PASS}
=
\operatorname{PASS}_A
\lor\operatorname{PASS}_B
\lor\operatorname{PASS}_C
\lor\operatorname{PASS}_D
\lor\operatorname{PASS}_E.
}
\]

One passing route is sufficient. Other routes may be absent or fail.

## 2. Verdict vocabulary

Each route receives exactly one verdict:

```text
PASS
FAIL
INVALID
ABSENT
```

- `PASS`: every mandatory route and Seal gate succeeds.
- `FAIL`: the submission is well formed but misses a required mathematical
  identity, inequality, reconstruction, resource, or physical bound.
- `INVALID`: the submission cannot be interpreted under the frozen grammar,
  uses prohibited information or dependencies, omits a mandatory object, or
  relies on undefined semantics.
- `ABSENT`: no submission was made for that route.

Diagnostics and rankings never change a terminal verdict.

## 3. Frozen organizer manifest

Before accepting submissions, the organizer publishes hashes for:

- Public problem set.
- Seal and rubric versions.
- Construction object and boundaries.
- Runtime object.
- Observable generators.
- Canonical serializer.
- FDAC encoder and decoder.
- Route adapters.
- Fixed interpreter.
- Verifier.
- Targets and resource bounds.
- Physical execution protocol.
- Private application-binding manifest commitment.

A changed hash creates a new examination instance.

## 4. Common route gates

Every attempted route passes all gates in this section before its specific
adapter is considered.

### G0. Artifact completeness

Require:

```text
route manifest
canonical C input
canonical Z input, possibly empty
payload construction declaration
framing declaration
proof object P
exact length ledger
exact operation ledger
exact memory ledger
causality proof
joint replay proof
route-specific proofs
```

A missing mandatory object yields `INVALID`.

### G1. Construction/runtime isolation

Run the route interpreter without access to the construction copy of \(x\).
Verify that every runtime observable is generated from the frozen runtime
object, reconstructed prefix, and logically released auxiliary data.

Reject:

- Direct access to \(x_t\) or later symbols.
- Precomputed future observables.
- Uncharged prediction or teacher traces.
- Runtime access to proof channel `P`.
- Network or external file access.

Unavailable information yields `INVALID`.

### G2. Canonical serialization

Serialize `F`, `C`, and `Z` with the frozen grammar. Require one unique byte
representation for every submitted mathematical object.

Reject alternate graph numbering, map ordering, integer width, padding,
table order, sparse-entry order, or unused degree of freedom not permitted by
the Seal.

A serialization ambiguity yields `INVALID`.

### G3. Exactly-once accounting

Assign every non-fixed runtime object to exactly one of `F`, `C`, `Z`, or `Y`.
Require proof channel `P` to be runtime-inaccessible.

Reject duplicated tables, uncharged seeds, advice hidden in names or ordering,
labels duplicated in the payload alphabet, and fixed costs omitted from
`L_fixed`.

Compute

\[
L_i
=
L_{\mathrm{fixed},i}
+8|F_i|
+8|C_i|
+8|Z_i|
+|Y_i|.
\]

An unreconciled bit yields `INVALID`.

### G4. Causality and logical release

For every reconstructed symbol or block, verify that all inputs to prediction,
selection, retrieval, or reconstruction are available at that point.

A paid record in `Z` may depend on future construction data only when its
complete representation is charged and its logical release precedes first use.
Future `Z` records remain inaccessible.

A causality violation yields `INVALID`.

### G5. Exact FDAC or literal replay

For every FDAC payload, record:

- Position and block.
- Numerator.
- Pre-update interval.
- Split.
- Selected interval.
- Renormalization events.
- Emitted or consumed bits.
- Post-update state.

For every literal route field, verify exact declared length and identity.

Require exact payload determinism, exact symbol count, exact reconstruction,
identical numerator traces, legal zero fill, and identical second encoding.

Defined but incorrect reconstruction yields `FAIL`. Undefined coding semantics
yield `INVALID`.

### G6. Joint state replay

Run independent encoder and decoder recurrences. Before and after every symbol,
require equality of:

- Route and block position.
- Released auxiliary state.
- Observable state.
- Predictor, index, prototype, or clockwork state.
- Numerator or literal mode.
- Arithmetic-coder state.
- Every tie, collision, eviction, failure, and fallback choice.

A defined mismatch yields `FAIL`.

### G7. Absolute target

Use only the exact integer total. Require

\[
L_i\le T_i.
\]

Forecasts, ideal log loss, entropy, projections, oracle savings, and separately
added mechanism gains receive no credit.

A valid route above target yields `FAIL`.

### G8. Mathematical resources

Recompute the route's exact or conservative declared operation count and peak
memory under the fixed interpreter. Include initialization, parsing, state,
search, indexing, arithmetic coding, literal copying, finalization, and every
exceptional path.

Average or expected resource claims are inadmissible.

A valid route over a resource bound yields `FAIL`.

### G9. Physical execution

When required by the instance, run the fixed interpreter under the frozen
reference protocol. Require encode time, decode time, process-tree peak memory,
output identity, and deterministic replay to pass.

A mathematically valid route missing the physical bound yields `FAIL`.
Infrastructure failure without a completed measurement yields `INVALID` until
rerun.

### G10. Proof isolation and verification

Use `P` only to verify mathematical obligations. Confirm that deleting `P`
after verification does not change serialization, encoding, decoding,
resources, or output.

A proof that supplies runtime information yields `INVALID`.

### G11. Route independence

Evaluate the route in an environment containing no submitted artifacts from
other routes. A route that imports another route's table, state, label, payload,
proof witness, or score credit yields `INVALID`.

### G12. Private binding

Verify the precommitted private binding theorem for the route. Confirm hashes,
fixed costs, target mapping, package mapping, resource mapping, and adapter
identity.

A route may pass the public mathematics without this gate, but the examination
must not issue transferable `PASS` unless G12 succeeds.

## 5. Route A adapter: Paid Partition Martingale

### A0. Required finite objects

Require:

- Finite label alphabet.
- Prefix-free label code.
- Complete block-label sequence.
- Finite predictive state representation.
- Initial state.
- Transition map.
- Numerator map.
- Exact closure and accounting proofs.

### A1. Label validity

Verify prefix-freeness directly. Parse exactly one label per declared release
point. Confirm future labels remain unavailable and every used codeword occurs
exactly once in `Z_A`.

### A2. State validity

Verify the initial state, every reachable successor, numerator range, transition
single-valuedness, and exact equality of repeated evaluations.

### A3. Route bounds

Require

\[
|C_A|\le B_{A,C},
\quad
|Z_A|\le B_{A,Z},
\quad
|S|\le B_{A,S},
\]

\[
\operatorname{Ops}_A\le B_{A,O},
\quad
\operatorname{Mem}_A\le B_{A,M}.
\]

### A4. Verdict

Issue `PASS_A` exactly when A0 through A3 and G0 through G12 pass. No other
route is loaded.

## 6. Route B adapter: Predictive Quotient

### B0. Required finite objects

Require quotient states, initial state, deterministic transition, numerator
map, represented exceptions, congruence proof, and closure proof.

### B1. Descriptor causality

Recompute every descriptor from the runtime prefix. A descriptor stream that
is merely supplied by the construction view yields `INVALID`.

### B2. Congruence

For every reachable pair represented by the same quotient state and current
descriptor, verify that equal next bits produce equal successor states unless a
specific charged exception applies.

### B3. Exception accounting

Verify every exception is finite, reachable or explicitly retained, canonically
ordered, and represented once in `C_B`.

### B4. Route bounds

Require

\[
|C_B|\le B_{B,C},
\quad
|Q|\le B_{B,Q},
\]

\[
\operatorname{Ops}_B\le B_{B,O},
\quad
\operatorname{Mem}_B\le B_{B,M}.
\]

### B5. Verdict

Issue `PASS_B` exactly when B0 through B4 and G0 through G12 pass. No other
route is loaded.

## 7. Route C adapter: Exact Continuation Geometry

### C0. Required finite objects

Require signature map, online index update, retrieval map, candidate weighting,
fallback blend, all capacities, and deterministic collision and eviction rules.

### C1. Prefix-only index

Construct the index from an empty initial state while replaying the decoded
prefix. Reject offline target-position tables or entries created before their
source events complete.

### C2. Candidate legality

For every retrieval, require each candidate position \(u<t\). Verify every
candidate bit used by the numerator is already reconstructed and stored.

### C3. Deterministic geometry

Verify ordering, tie breaking, collisions, eviction, fallback, and candidate
exhaustion independently in encoder and decoder recurrences.

### C4. Controls

Publish exact totals for C0, C1, C2, and CR controls under identical coding and
finalization. Controls do not affect acceptance.

### C5. Route bounds

Require

\[
|C_C|\le B_{C,C},
\quad
\operatorname{IndexBits}_C\le B_{C,I},
\]

\[
\operatorname{Ops}_C\le B_{C,O},
\quad
\operatorname{Mem}_C\le B_{C,M}.
\]

### C6. Verdict

Issue `PASS_C` exactly when C0 through C5 and G0 through G12 pass. No other
route is loaded.

## 8. Route D adapter: Integer Dynamical Realization

### D0. Required finite objects

Require bounded state layout, initial state, transition instruction sequence,
numerator instruction sequence, constants, tables, instruction-legality proof,
closure proof, and exact global teacher comparison.

### D1. Teacher isolation

Permit the teacher only during construction and diagnostics. Run the candidate
without teacher state, output trace, parameters, or tables unless their complete
representation appears in `C_D`.

### D2. Integer semantics

Verify every opcode, operand width, signedness, overflow, shift, division,
rounding, saturation, lookup bound, branch, and output range.

### D3. State closure

Prove every reachable state belongs to the declared bounded state space. Full
trace execution supplements but does not replace a required universal closure
proof.

### D4. Global comparison

Report

\[
\Delta L_D=L_D-L_{\mathrm{teacher}}.
\]

Per-position log loss must be labeled diagnostic and nonadditive. The absolute
target remains decisive.

### D5. Route bounds

Require

\[
|C_D|\le B_{D,C},
\quad
\operatorname{StateBits}_D\le B_{D,S},
\]

\[
\operatorname{Ops}_D\le B_{D,O},
\quad
\operatorname{Mem}_D\le B_{D,M}.
\]

If the instance requires it, also require

\[
\Delta L_D\le\Sigma_D.
\]

### D6. Verdict

Issue `PASS_D` exactly when D0 through D5 and G0 through G12 pass. No other
route is loaded.

## 9. Route E adapter: Prototype-Coset Reconstruction

### E0. Required finite objects

Require prototype selection, bounded prototype bank, explicit-edit grammar,
parity family, bounded residual decoder, literal fallback, and complete mode
records.

### E1. Prototype availability

For every block, verify that its selected prototype is fixed in `C_E` or
generated from completed earlier blocks. Reject current-block or future-block
prototype leakage.

### E2. Explicit-edit inversion

For every explicit edit, verify unique parsing, bounded indices, exact inverse,
and exact reconstructed block identity.

### E3. Syndrome validity

For every syndrome mode, verify matrix construction, dimensions, rank over
\(\operatorname{GF}(2)\), transmitted syndrome, candidate ordering, tie
breaking, search bound, returned candidate, and exact block identity.

An ideal minimum-energy decoder does not substitute for the submitted bounded
decoder.

### E4. Failure and fallback

Verify every bounded-search failure deterministically selects a represented
fallback. Literal mode must reconstruct every otherwise unsupported block.

### E5. Route bounds

Require

\[
|C_E|\le B_{E,C},
\quad
|Z_E|\le B_{E,Z},
\quad
\operatorname{StateBits}_E\le B_{E,S},
\]

\[
\operatorname{Ops}_E\le B_{E,O},
\quad
\operatorname{Mem}_E\le B_{E,M}.
\]

### E6. Verdict

Issue `PASS_E` exactly when E0 through E5 and G0 through G12 pass. No other
route is loaded.

## 10. Audit artifacts

For every attempted route, publish:

- Route and Seal versions.
- Frozen-instance hashes.
- Verdict and first failing condition.
- `F/C/Z/Y` lengths.
- Exact total and target margin.
- Certificate and payload hashes.
- Numerator or reconstruction trace hash.
- State trace hash.
- Decoded-object hash.
- Deterministic second-encoding hash.
- Operation and memory totals.
- Physical receipt when required.
- Proof-verifier result.
- Private-binding manifest hash.

The verifier's exact integer output controls the verdict when a contestant's
ledger disagrees.

## 11. Final decision table

| Passing routes | Final verdict |
|---|---|
| At least one of A, B, C, D, E | `PASS` |
| No pass, at least one well-formed failure, no invalid attempt | `FAIL` |
| No pass, at least one invalid attempt | `INVALID` |
| All routes absent | `INVALID` |

An invalid or failed route cannot overturn an independent passing route.

## 12. Acceptance theorem

For each route \(i\), G0 through G12 establish that:

- Runtime information is legal.
- Serialization is canonical.
- Every runtime bit is counted exactly once.
- Coding or reconstruction is exact.
- Encoder and decoder recurrence agree.
- The absolute target is met.
- Mathematical and physical resources pass.
- Proof data is runtime-isolated.
- No other route is required.
- The private transfer implication is valid.

Therefore

\[
\exists i\in\{A,B,C,D,E\}:\operatorname{PASS}_i
\]

is sufficient for final acceptance. QED.
