# Tight State-Cell Layout

## Independent finite problem SLC-1

Fix the following record-layout machine:

- an unsigned 16-bit object has size and alignment \(2\);
- an unsigned 8-bit object has size and alignment \(1\);
- array elements are contiguous;
- members are placed in declaration order at the least offset satisfying their
  alignment;
- a record's size is rounded up to its maximum member alignment;
- a union's size is the rounded-up maximum of its member sizes.

For an integer \(A\ge1\), define the logical record

\[
\mathcal R_A=
\bigl(
\operatorname{chk}[A]:U16,\ 
\operatorname{last}:U8,\ 
\operatorname{bh}[A][7]:U8
\bigr).
\]

For \(B\ge1\), define a union \(\mathcal E_{A,B}\) containing
\(\mathcal R_A\) and a byte array \(\operatorname{pad}[B]\).

## A. Exact layout

1. Determine the offsets of `chk`, `last`, and `bh`.
2. Derive exact closed forms for
   \[
   |\mathcal R_A|
   \quad\text{and}\quad
   |\mathcal E_{A,B}|.
   \]
3. Evaluate the formulas for \((A,B)=(10,96),(10,92),(14,128)\).
4. Prove that \(92\) is the minimum union width for \(A=10\) that preserves
   the declared logical record on this machine.

## B. Array alignment and addressability

Let an array of \(\mathcal E_{10,92}\) begin at an address divisible by \(128\).

1. Prove that every `chk` element remains 2-byte aligned.
2. Prove that every `bh` byte is addressable by the same within-record offset
   as in \(\mathcal E_{10,96}\).
3. Give the exact memory reduction for \(N\) cells when replacing width 96 by
   width 92 without changing \(N\).

## C. State-equivalence theorem

Two deterministic machines have the same:

- number \(N\) of cells;
- initial logical field values;
- table-index function;
- lookup, replacement, update, and probability rules;
- already-decoded input history.

One stores each cell as \(\mathcal E_{10,96}\); the other uses
\(\mathcal E_{10,92}\). Neither machine reads padding bytes or derives model
state from object addresses.

Prove by induction that their logical cell fields, emitted integer
probabilities, arithmetic-coder states, and decoded outputs are identical at
every step.

State precisely why reading padding, hashing addresses, serializing raw object
representations, or using an ABI that violates the frozen layout hypotheses
invalidates the theorem.

## D. Dense reinvestment

Let the former byte budget be \(M=128N_0\), where \(N_0=2^k\).

1. Derive the exact capacities
   \[
   N_{96}=\lfloor M/96\rfloor,
   \qquad
   N_{92}=\lfloor M/92\rfloor.
   \]
2. Express both ratios to \(N_0\) in lowest terms before flooring.
3. Derive an exact formula and a sharp floor-error bound for
   \(N_{92}-N_{96}\).
4. Give complete memory accounting when each table has \(g\) guard cells and
   \(a\) alignment bytes outside the usable budget.

## E. Finite ABI certificate

Specify a finite compile-and-run certificate that checks:

- sizes and alignments of the scalar types;
- all three member offsets;
- record and union sizes;
- alignment of `chk` in a finite array;
- equality of logical values after deterministic writes through both layouts.

The certificate must not claim compressed-size improvement.

## Organizer-owned transfer reduction

The current A10 FXCM cell is `E1<10,96>`. SLC-1 licenses a separate
archive-identity candidate using `E1<10,92>` at the same cell count. Only after
exact identity passes may the 92-byte layout be composed with DRB-1 to allocate
\(\lfloor128N_0/92\rfloor\) range-indexed cells.

SLC-1 proves representation equivalence and capacity arithmetic. A composed
dense candidate receives score credit only from exact native codelength,
roundtrip, deterministic replay, package, runtime, and memory receipts.

