# PCMF-1: Paid Conditional Multinomial Fibers

Status: `FROZEN RESEARCH PROBLEM`
Version: `PCMF-1`

## Definitions

Let \(x=x_1\ldots x_n\) be a word over a finite ordered alphabet \(A\).
Before position \(i\), a deterministic causal function of
\(x_1\ldots x_{i-1}\) produces a context \(\kappa_i\) in a finite set \(C\).
For \(c\in C\), define

\[
I_c=\{i:\kappa_i=c\},\qquad
n_{c,a}=|\{i\in I_c:x_i=a\}|,\qquad
N_c=|I_c|.
\]

The exact parent ideal cost on \(I_c\) is \(P_c\). A selected context transmits
its nonzero count vector at price \(d_c\) bits and codes its next-symbol
subsequence without replacement. Unselected contexts retain the parent code.
A nonempty selected family pays one shared framing price \(h\).

## Questions

Prove all of the following.

1. The sets \(I_c\) uniquely partition the sequence positions.
2. Conditional on the count vector, the number of possible symbol
   subsequences at context \(c\) is
   \[
   M_c=\frac{N_c!}{\prod_{a\in A}n_{c,a}!}.
   \]
3. If the next symbol at context \(c\) receives probability equal to its
   remaining count divided by the remaining total for \(c\), every admissible
   subsequence has probability \(1/M_c\).
4. Prove the same probability identity after factoring every categorical
   choice through a fixed ordered binary tree over \(A\).
5. For a selected context family \(U\), define ideal saving
   \[
   G(U)=
   \sum_{c\in U}
   \left[P_c-d_c-\log_2M_c\right]-h,
   \]
   and \(G(\varnothing)=0\). Prove that the inclusion-minimal optimum contains
   every context with strictly positive bracketed contribution if their sum
   exceeds \(h\), and otherwise is empty.
6. Give canonical tie rules, a finite certificate, and construction bounds.
7. Prove exact causal reconstruction when the decoder receives selected
   contexts and count vectors before the stream, chooses the parent or
   multinomial code from its reconstructed prefix, and updates the parent
   predictor after every reconstructed symbol.
8. Explain why ideal type-class length does not determine the exact bytes of
   a finite-precision range coder.

## Frozen application

For WRT position \(i\ge2\),

\[
\kappa_i=256x_{i-2}+x_{i-1}.
\]

The first two positions always use the parent. The exact input is:

```text
results/wrt_wiki_shell_v1/trace_1m_v1/residual_cache.tsv
results/wrt_wiki_shell_v1/trace_1m_v1/wrt_stream.bin
results/wrt_wiki_shell_v1/trace_1m_v1/output.cmix
```

The side model uses:

```text
selected-context count: 4 bytes
side-payload length:    4 bytes
each context key:       2 bytes
each support size:      2 bytes
each support symbol:    1 byte
each symbol count:      3 bytes
```

All selected contexts share one frozen 16-bit binary-tree range stream.
Unselected contexts retain exact parent bit probabilities.

Promotion requires parent payload identity, a nonempty side-coder roundtrip,
exact WRT reconstruction, at least 2,000 net bytes per million raw bytes, and
complete source cost. Failure retires this context-two complete-distribution
representation without a context-length, support-pruning, or probability
resolution sweep.
