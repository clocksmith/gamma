# Independent Problem CC-1: Maximum-Weight Causal Copy Covers

Status: `FROZEN RESEARCH PROBLEM`
Version: `CC-1`

## Definitions

Let \(x=x_0\cdots x_{n-1}\) be a finite word. A causal copy candidate is a
triple

\[
c=(s(c),u(c),\ell(c))
\]

with

\[
0\le u(c)<s(c),\qquad
s(c)+\ell(c)\le n,
\]

such that

\[
x_{s(c)+j}=x_{u(c)+j}
\quad(0\le j<\ell(c)).
\]

Overlapping source and target are allowed; copying proceeds left to right.
The target interval is

\[
I(c)=[s(c),s(c)+\ell(c)).
\]

The input supplies a finite candidate family and integer weights \(w(c)\).
A copy cover is a subfamily with pairwise disjoint target intervals.

## Questions

Prove all of the following.

1. Sort candidates by nondecreasing target end, then by the supplied canonical
   candidate order. Let \(\pi(i)\) be the largest earlier candidate whose
   target ends no later than candidate \(i\) starts. Prove the recurrence
   \[
   F(i)=\max\{F(i-1),\,w(i)+F(\pi(i))\}.
   \]
2. Resolve every equality by exclusion. Prove that backtracking gives the
   unique canonical optimum having the fewest latest-order inclusions among
   all maximum-weight covers.
3. Give exact \(O(m\log m)\) construction time for \(m\) candidates and a
   linear certificate verifier after sorting.
4. Prove reversible decoding from the literal subsequence plus the ordered
   copy commands, including overlapping copies.
5. Suppose each omitted target symbol would otherwise be coded with a supplied
   nonnegative ideal cost and each command has an exact fixed cost. Prove that
   setting \(w(c)\) to omitted ideal cost minus command cost makes the
   recurrence the exact ideal-cost optimum over the supplied family.
6. If each candidate weight changes by at most \(\eta(c)\), prove a stability
   bound for the optimal cover value.

## Frozen application

The exact native trace is packed into WRT bytes. At every byte position, the
application considers the longest match among the four most recent prior
occurrences of the current eight-byte key, capped at 255 bytes. Each command
uses:

```text
target position: 3 bytes
source distance: 3 bytes
length:          1 byte
```

A four-byte command-count header is charged once. Candidate weight is the
parent ideal qbit cost of the target minus 56 command bits. The optimal
nonoverlapping cover is selected once. Exact range replay then omits copied
target bits while predictor state is conceptually updated from reconstructed
bytes.

Promotion requires:

- exact parent payload identity;
- exact byte-level transform roundtrip;
- at least 2,000 net bytes per million raw bytes after command bytes.

Failure retires this fixed causal-copy representation without hash-width,
history-count, pointer-format, or minimum-length sweeps.
