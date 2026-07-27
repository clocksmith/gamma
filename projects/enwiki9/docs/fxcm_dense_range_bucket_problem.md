# Dense Range Buckets

## Independent finite problem DRB-1

This problem concerns finite permutations, balanced maps, and deterministic
state machines. It does not assume a compression corpus or a probabilistic
model.

Let \(w\ge 1\), \(Q=2^w\), and identify the word space with
\(\mathbb Z/Q\mathbb Z\). For an integer \(N\) with \(1\le N\le Q\), define

\[
R_N(x)=\left\lfloor \frac{Nx}{Q}\right\rfloor
\in\{0,\ldots,N-1\}.
\]

For odd constants \(a,c\), positive integers \(r_1,r_2,r_3<w\), and arbitrary
\(b\), define

\[
\begin{aligned}
u_0&=x+b \pmod Q,\\
u_1&=u_0\mathbin{\mathtt{xor}}(u_0\mathbin{\mathtt{shr}}r_1),\\
u_2&=a u_1\pmod Q,\\
u_3&=u_2\mathbin{\mathtt{xor}}(u_2\mathbin{\mathtt{shr}}r_2),\\
u_4&=c u_3\pmod Q,\\
P(x)&=u_4\mathbin{\mathtt{xor}}(u_4\mathbin{\mathtt{shr}}r_3).
\end{aligned}
\]

For a salt \(s\in\mathbb Z/Q\mathbb Z\), put

\[
H_{N,s}(x)=R_N(P(x+s)).
\]

All arithmetic has the exact fixed-width semantics above.

## A. Dense allocation

Let a table have a usable byte budget \(M\) and fixed cell width \(B\).

1. Prove that the maximum number of complete cells is
   \[
   C(M,B)=\left\lfloor M/B\right\rfloor
   \]
   and that the unused budget is in \(\{0,\ldots,B-1\}\).
2. Suppose an old table has \(2^k\) cells of width \(128\), while a new cell
   holding the same logical fields has width \(96\). Under the unchanged
   budget \(M=128\cdot2^k\), derive the exact new capacity and a sharp lower
   bound on its ratio to \(2^k\).
3. Separate the usable budget from alignment and guard cells. Give the exact
   allocation formula when \(g\) guard cells and \(A\) alignment bytes are
   charged outside \(M\).

## B. Permutation and balance

1. Prove that \(P\) is a permutation of the \(Q\) words.
2. Write
   \[
   Q=qN+r,\qquad 0\le r<N.
   \]
   Prove that exactly \(r\) buckets of \(R_N\) have \(q+1\) preimages and the
   remaining \(N-r\) buckets have \(q\) preimages.
3. Prove that the same statement holds for every \(H_{N,s}\).
4. Prove that no map from \(Q\) words to \(N\) buckets can have a smaller
   maximum-minus-minimum preimage count.

## C. Exact collision law

Let \(X,Y\) be independent uniform words. Prove

\[
\Pr[H_{N,s}(X)=H_{N,s}(Y)]
=
\frac{r(q+1)^2+(N-r)q^2}{Q^2}
=
\frac1N+\frac{r(N-r)}{NQ^2}.
\]

Deduce

\[
\frac1N
\le
\Pr[H_{N,s}(X)=H_{N,s}(Y)]
\le
\frac1N+\frac{N}{4Q^2}.
\]

When \(N_0=2^k\mid Q\) and

\[
N_1=\left\lfloor\frac{4N_0}{3}\right\rfloor,
\]

give an exact comparison between the collision laws for \(N_0\) and \(N_1\).
Do not assume that two differently salted hashes are independent.

## D. Deterministic state equivalence

Consider two machines with identical:

- initial arrays of \(N\) cells;
- word arithmetic;
- permutation constants;
- salts;
- update, replacement, and probability rules;
- arithmetic-coder semantics.

At step \(t\), both machines receive the same already-decoded symbol and use
only that symbol and their current state to form all table keys.

Prove by induction that both machines select the same cells, make the same
replacements, emit the same integer probability, and reach the same state at
every step. Conclude that replacing a power-of-two mask by \(H_{N,s}\) cannot
by itself compromise losslessness, although it can change compressed length.

## E. Finite certificate

Specify a finite certificate and verifier for an implementation claiming this
construction. It must bind:

- \(w,N,B,M,g,A\);
- all constants and salts;
- allocated and usable byte counts;
- the exact index routine;
- a finite set of index test vectors including \(0,Q-1\), wraparound, every
  bucket boundary, and every table offset used by the machine.

Give exact verifier work in terms of the number of test vectors.

## Organizer-owned transfer reduction

The current FXCM cmC2 realization uses \(2^k\) cells and mask indexing even
when `CMIX_FXCM_CMC2_ASSOC=10` makes each cell 96 bytes. It therefore uses
only \(96\cdot2^k\) bytes from the former \(128\cdot2^k\) budget.

A DRB-1 transfer may:

1. retain associativity ten;
2. allocate
   \[
   \left\lfloor128\cdot2^k/96\right\rfloor
   \]
   cells within each frozen cmC2 budget;
3. replace every cmC2 mask access by the certified salted range index;
4. leave all other predictor mechanisms unchanged.

The theorem certifies allocation, index balance, and encoder/decoder agreement.
It does not certify that changed collisions improve codelength. Promotion
requires exact native roundtrip, deterministic second archive, decimal-10GB
memory compliance, complete program accounting, and positive held-out bytes.

