# Review: Problem D Solution

Submission: `ACS-D-20260726T202536Z-273dbe2f`

## Mathematical verdict

`COMPLETE`

The submission gives a sound resolution of Problem D under a
solve-or-rigorously-disprove rule. It establishes:

- the exact kernel-collision characterization;
- existence of a separating map with the stronger depth bound
  \(k\le\lceil\log_2 r_E(x)\rceil\);
- deterministic finite construction and nested full-rank extension;
- the corrected difference-set criterion;
- Hamming-ball distance and counting consequences;
- translated-ball conditions; and
- necessary and sufficient first-hit verification conditions.

## Specification findings

### D3

The original equality formulation fails for \(B=\varnothing\). The accepted
correction is either:

\[
\ker H\cap(B-B)\subseteq\{0\},
\]

or the additional hypothesis \(B\ne\varnothing\).

### D4

The exact \(j\)-evaluation count is valid for the canonical sequential direct
verifier. It is not an unrestricted lower bound over all possible verifiers.

Both findings are recorded as semantic errata for the next problem version.
They do not invalidate the submitted mathematical analysis.

## Seal-transfer verdict

`ALGEBRA_ONLY`

The solution validates parity separation and first-hit certification. It does
not provide:

- an enwik9 energy assigning sufficiently low ranks to real blocks;
- an efficient bounded decoder;
- an exact target-bearing archive;
- source and framing accounting;
- deterministic full-corpus reconstruction; or
- eligible runtime and memory receipts.

Accordingly:

```text
Seal-2 binding:       UNBOUND
compression credit:  0 bytes
route authorization: none
```

## Extracted research consequence

The residual constructive question is:

> Produce a deterministic, cheaply searchable energy ordering whose true WRT
> blocks have sufficiently low rank, then demonstrate that bounded
> parity-constrained reconstruction beats causal coding after every counted
> cost.

This is the remaining MOIRAI-style research obligation. The solved linear
algebra cannot substitute for it.
