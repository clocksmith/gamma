# Atlas-Clockwork Seal Specification

Seal version: `ACS-SEAL-2`

## 1. Purpose

The Seal is organizer-owned grading and transfer machinery for the Independent
Finite Prediction Olympiad. It is not a contestant problem and contributes no
mathematical hint about any route.

The Seal owns:

- Construction-view and runtime-view isolation.
- Canonical finite-object serialization.
- Exact finite-state coding.
- Disjoint bit accounting.
- Logical release schedules.
- Deterministic interpretation.
- Exact inversion and canonical re-encoding.
- Mathematical resource accounting.
- Physical reference execution.
- Route independence.
- The private application-binding theorem.

Problem statements define admissible mathematical objects. The Seal determines
whether those objects form an accepted finite representation.

## 2. Version and freeze rule

Before accepting submissions, the organizer freezes and hashes:

1. This Seal version.
2. The construction object and boundaries.
3. The runtime object.
4. Every causal observable generator.
5. The canonical serializer.
6. The exact finite-state coder.
7. Every route adapter.
8. Every route target and resource bound.
9. The fixed interpreter.
10. The verifier.
11. The physical execution protocol.
12. The private application-binding manifest.

Any semantic change creates a new Seal version and a new examination instance.
No submission may select among Seal versions.

## 3. Construction and runtime separation

### 3.1 Construction view

The contestant and offline verifier may inspect the complete finite object
\(x\) while constructing or checking a submission.

### 3.2 Runtime view

The runtime interpreter receives only:

```text
frozen runtime object R
framing F
certificate C
paid auxiliary channel Z
payload Y
previously reconstructed symbols
logically released auxiliary records
```

It does not receive:

```text
construction copy of x
proof channel P
future symbols
unreleased labels or selectors
offline prediction traces
teacher traces unless charged in C
network or external files
```

### 3.3 Observable rule

Every runtime observable must be produced by a frozen causal generator

\[
\omega_t=\Omega(R,x_{<t},\zeta_{\le t}).
\]

The generator's implementation and fixed tables belong to the route's fixed
ledger. Any submission-specific table belongs to `C`.

A precomputed position-indexed observable stream is prohibited unless its
complete representation is charged in `C`. The verifier must test runtime
isolation by executing reconstruction in an environment where the construction
copy of \(x\) is inaccessible.

## 4. Canonical channels

Each route has five channels:

```text
F  framing and canonical lengths
C  decoder-required submitted certificate
Z  paid labels, selectors, modes, edits, or auxiliary choices
Y  exact coded payload
P  verifier-only proof and audit material
```

The runtime representation is

\[
W=F\mathbin\Vert C\mathbin\Vert Z\mathbin\Vert Y.
\]

`P` is stored separately. It is never visible to the runtime interpreter and
is not part of the coded-length objective.

The serializer must reject duplicate ownership. Every non-fixed object used at
runtime has exactly one owner:

| Object | Owner |
|---|---|
| channel lengths, block counts, padding counts | `F` |
| submitted maps, states, tables, constants, instructions | `C` |
| paid labels, selectors, modes, edits, syndrome bits | `Z` |
| arithmetic-coded or literal data payload | `Y` |
| arguments, derivations, audit annotations | `P` |

Proof material that is consulted during reconstruction is runtime data and must
be moved to `C` or `Z`.

## 5. Length units and accounting

All mathematical targets and bounds are integers measured in bits.

For route \(i\), define

\[
L_i
=
L_{\mathrm{fixed},i}
+8|F_i|_{\mathrm{bytes}}
+8|C_i|_{\mathrm{bytes}}
+8|Z_i|_{\mathrm{bytes}}
+|Y_i|_{\mathrm{bits}}.
\]

If an external application uses a byte target \(T_{i,\mathrm{bytes}}\), the
route target is frozen as

\[
T_i=8T_{i,\mathrm{bytes}}.
\]

Acceptance uses \(L_i\le T_i\). Conversion by ceiling is permitted only for a
published external format that explicitly counts a final partial byte. The
private binding manifest must state that rule.

`L_fixed,i` includes every fixed byte required by the route in the bound
application, including the interpreter, decoder support, fixed tables, format
adapter, and mandatory metadata. No fixed cost may be hidden merely because it
is organizer-owned.

## 6. Canonical finite-state dyadic arithmetic coder

Every arithmetic-coded binary symbol uses numerator

\[
a_t\in\{1,\ldots,2^r-1\}
\]

for probability \(a_t/2^r\) of symbol one.

Let

\[
w\ge r+3,
\quad
M=2^w,
\quad
H=2^{w-1},
\quad
Q=2^{w-2},
\quad
U=3Q.
\]

The encoder state is \((l,h,c)\), initialized to

\[
(l,h,c)=(0,M-1,0).
\]

For numerator \(a\), calculate

\[
R=h-l+1,
\]

\[
s=l+\left\lfloor\frac{R(2^r-a)}{2^r}\right\rfloor.
\]

For symbol zero, set \(h=s-1\). For symbol one, set \(l=s\).

Then repeatedly apply the first applicable rule:

1. If \(h<H\), emit zero followed by \(c\) ones, set \(c=0\), and set
   \((l,h)=(2l,2h+1)\).
2. If \(l\ge H\), emit one followed by \(c\) zeros, set \(c=0\), and set
   \((l,h)=(2(l-H),2(h-H)+1)\).
3. If \(l\ge Q\) and \(h<U\), increment \(c\) and set
   \((l,h)=(2(l-Q),2(h-Q)+1)\).
4. Otherwise stop renormalizing.

After the final symbol, increment \(c\). If \(l<Q\), emit zero followed by
\(c\) ones. Otherwise emit one followed by \(c\) zeros.

The decoder initializes the same interval and a \(w\)-bit code register from
the stated payload. It appends zero bits only after the exact stated payload
length for initialization and renormalization. At each symbol it computes the
same split \(s\), decodes zero when the code register is less than \(s\), and
otherwise decodes one. It mirrors every interval and renormalization update.
It stops after the exact symbol count supplied by `F` or the frozen instance.

The fixed verifier must establish for every accepted route:

- No empty subinterval is produced.
- Encoder and decoder numerator traces are identical.
- The payload is deterministic.
- The decoder reconstructs the exact symbol count.
- A second encoding emits the identical payload.
- No bit beyond the declared zero fill is consumed.

Block-reset coding is permitted only when declared by the route adapter. Each
block is terminated independently, and exact block bit lengths belong to `F`.

No ideal interval length, Shannon length, or floating-point log loss replaces
the emitted payload length.

## 7. Canonical serialization

Every finite submitted object has exactly one canonical grammar encoding.
Canonicalization fixes:

- Integer sign and width.
- Integer byte order.
- List order.
- Map key order.
- Graph-node numbering.
- State numbering.
- Table dimensions.
- Sparse-entry order.
- Zero and empty representations.
- Prefix-code representation.
- Padding and partial-byte rules.

Unused degrees of freedom are rejected where practical and charged otherwise.
A submission cannot hide information in symbol names, table ordering, hash
collisions, undefined fields, proof prose, filesystem order, or alternate
serializations.

The organizer publishes the serializer and a grammar hash before submissions.

## 8. Logical release schedule

`Z` is physically serialized before `Y`, but the interpreter exposes each
record only at its route-declared logical release point. Future records remain
inaccessible.

For each `Z` record, `F` or the route grammar determines:

- Its canonical boundary.
- Its route-defined type.
- Its logical release point.
- The first payload symbol allowed to depend on it.

The verifier rejects a probability, state transition, prototype choice, or
search decision that reads a record before release.

## 9. Deterministic interpreter

The fixed interpreter executes finite mathematical objects, not contestant
programs. It must define:

- Integer widths and signedness.
- Overflow and saturation.
- Shift semantics.
- Division and rounding.
- Lookup bounds.
- Branch and tie order.
- Graph traversal order.
- Queue order.
- Collision handling.
- Allocation and eviction.
- Failure and fallback behavior.

Runtime behavior may not depend on floating point, uninitialized memory,
thread scheduling, wall-clock time, address layout, unordered iteration,
filesystem order, or randomness without a charged fixed seed.

## 10. Exact inversion and replay

For a submitted route certificate, the organizer-owned interpreter constructs
an encoder \(E_i\) and decoder \(D_i\).

The verifier must establish

\[
D_i(E_i(x))=x
\]

and

\[
E_i(D_i(E_i(x)))=E_i(x).
\]

The proof and full replay proceed by induction. Before each reconstructed
symbol, encoder and decoder must agree on:

- Route and block position.
- Released auxiliary records.
- Observable state.
- Predictor or reconstruction state.
- Probability numerator or literal mode.
- Arithmetic-coder state.
- Every deterministic tie and fallback decision.

After the symbol, they must agree on every update.

A mismatch with defined behavior yields `FAIL`. Undefined or unavailable
information yields `INVALID`.

## 11. Mathematical resources

Every route adapter defines exact functions

\[
\operatorname{Ops}_i(C,Z,Y,F,x)
\]

and

\[
\operatorname{Mem}_i(C,Z,Y,F,x).
\]

Operations include initialization, parsing, label release, prediction,
transition, indexing, search, arithmetic coding, literal copying, finalization,
and exceptional paths.

Memory includes fixed resident tables charged to the route, submitted tables,
dynamic state, indexes, stacks, queues, temporary buffers, arithmetic state,
and exceptional allocations.

Average, expected, sampled, or amortized resource claims do not replace the
route's declared exact or conservative worst-case count.

## 12. Physical execution gate

A mathematical resource ledger does not by itself imply physical eligibility.
For every route requiring a physical bound, the organizer runs the fixed
interpreter under a frozen protocol specifying:

- Machine and processor.
- Core count.
- Operating-system image.
- Interpreter and adapter hashes.
- Input and output hashes.
- Encode and decode commands.
- Process-tree accounting.
- Memory measurement method.
- Repetition and warmup policy.
- Maximum encode time.
- Maximum decode time.
- Maximum peak memory.

A route passes physical eligibility only when the measured receipt passes.
Alternatively, the Seal may include a precommitted conservative theorem mapping
mathematical resource bounds to physical acceptance for the exact fixed
interpreter and reference machine.

## 13. Proof channel

The contestant submits a finite proof object `P`. It may contain derivations,
lemmas, witness indexes, audit annotations, and independently checkable
certificates.

`P` is not charged to coded length because it is not part of the runtime
representation. The runtime interpreter cannot open it. If any runtime result
requires information found only in `P`, the route is `INVALID`.

The proof verifier may use `P` to establish closure, causality, rank,
prefix-freeness, exact lengths, or other mathematical obligations.

## 14. Route independence

Each route has a separate adapter and verdict. To evaluate route \(i\), the
verifier loads no submitted object from route \(j\ne i\).

Cross-route citations are allowed only for public mathematical theorems that do
not contain instance-specific data or artifacts. A route may not inherit
another route's score credit, state, table, label, payload, or proof witness.

The final examination verdict is the logical OR of route verdicts.

## 15. Private application-binding theorem

Before public release, the organizer freezes a private binding manifest. It
must establish a mechanical map \(\Psi_i\) for every route \(i\) such that a
passing route becomes a complete artifact in the bound application.

The manifest binds:

- Construction-object hash to bound input hash.
- Route target to bound counted-size target.
- `L_fixed,i` to every fixed counted application byte.
- `F/C/Z/Y` to application package and archive fields.
- Fixed interpreter and adapter to the application decoder.
- Mathematical and physical resource gates to application limits.
- Determinism and exact inversion to application requirements.

For every route, the organizer must prove

\[
V_i(C_i,Z_i,Y_i,F_i,P_i)=\operatorname{PASS}
\Longrightarrow
\operatorname{Accept}_{\mathrm{bound}}(\Psi_i(C_i,Z_i,Y_i,F_i)).
\]

The binding may remain private when the public examination must reveal no
external interpretation, but its hash, creation time, and Seal version must be
committed before accepting submissions.

Without this theorem, the examination may still be mathematically valid but is
not certified as transferable.

## 16. Verdicts

Each route receives one verdict:

```text
PASS
FAIL
INVALID
ABSENT
```

`PASS` means every route, common, target, resource, physical, and transfer-bound
condition succeeds.

`FAIL` means the submission is well formed but misses a required equality,
inequality, reconstruction, or bound.

`INVALID` means the submission uses unavailable information, undefined
semantics, ambiguous serialization, prohibited dependencies, or missing
mandatory objects.

`ABSENT` means the route was not attempted.

The final examination passes when at least one route receives `PASS`.
