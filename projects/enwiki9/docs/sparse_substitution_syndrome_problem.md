# Independent Problem SS-1: Sparse Substitution Syndromes

Status: `FROZEN RESEARCH PROBLEM`
Version: `SS-1`

## Definitions

Let \(a,b\in\Sigma^L\). A substitution instruction is a pair
\((i,\sigma)\) with \(0\le i<L\) and \(\sigma\in\Sigma\). A valid script
applies at most one instruction per position to \(a\) and must produce \(b\).
Every instruction has the same positive cost.

For a finite ordered prototype family \(A=\{a_1,\ldots,a_m\}\), prototype
\(a_j\) also has a supplied nonnegative selection cost \(d_j\).

## Questions

Prove all of the following.

1. Every valid script from \(a\) to \(b\) must contain an instruction at every
   position where \(a_i\ne b_i\).
2. The unique minimum-cardinality canonical script is
   \[
   \{(i,b_i):a_i\ne b_i\},
   \]
   ordered by increasing position.
3. The minimum script size is the Hamming distance \(d_H(a,b)\).
4. The minimum total reconstruction cost over the prototype family is
   \[
   \min_j[d_j+c\,d_H(a_j,b)],
   \]
   where \(c\) is the per-instruction cost. A fixed prototype order gives a
   canonical minimizer.
5. For independently framed target blocks, prove that selecting the cheapest
   among literal coding and every prototype syndrome independently in each
   block gives the exact global optimum.
6. Give a finite certificate and exact verifier cost.

## Frozen application

The WRT stream is partitioned into aligned 64-byte blocks. Four deterministic
eight-byte signatures sample residues \(0,2,4,6\) modulo eight. For each
signature, only the four most recent prior matching blocks are prototype
candidates. A candidate is admitted only with at most eight substitutions.

Every selected syndrome uses:

```text
target position: 3 bytes
source distance: 3 bytes
edit count:      1 byte
each edit:       1-byte position + 1-byte value
```

A four-byte count header is charged. Selected blocks are omitted from exact
range replay and reconstructed before predictor update. Promotion requires
parent payload identity, exact transform roundtrip, and at least 2,000 net
bytes per million raw bytes. Failure retires this exact syndrome family without
block-size, signature, edit-cap, or history sweeps.
