# JMF-1: Joint Multinomial Symbol Fibers

Status: `FROZEN RESEARCH PROBLEM`
Version: `JMF-1`

## Definitions

Let \(x=x_1\ldots x_n\) be a word over a finite ordered alphabet \(A\).
For \(a\in A\), write

\[
F_a=\{i:x_i=a\},\qquad n_a=|F_a|.
\]

Choose a set \(S\subseteq A\) of extracted symbols and replace every
unselected symbol by one residual category \(\rho\). Put

\[
n_\rho=n-\sum_{a\in S}n_a.
\]

The category word therefore has counts
\((n_\rho,(n_a)_{a\in S})\). Each selected symbol has description price
\(d_a\) bits, and a nonempty model has fixed framing price \(h\) bits.
The supplied parent ideal cost of all occurrences of \(a\) is \(C_a\).

## Questions

Prove all of the following.

1. The selected fibers and the residual positions form a unique disjoint
   partition of \(\{1,\ldots,n\}\).
2. The number of category words with the fixed counts is
   \[
   M(S)=
   \frac{n!}{n_\rho!\prod_{a\in S}n_a!}.
   \]
   Consequently an injective fixed-length joint rank requires and suffices
   with \(\lceil\log_2 M(S)\rceil\) bits.
3. In a left-to-right without-replacement model, assign the next category
   probability \(r_j/(n-i+1)\), where \(r_j\) is its remaining count.
   Prove that the probability of every admissible category word is
   \(1/M(S)\).
4. Factor every categorical choice through any fixed ordered binary tree
   whose leaves are the categories. At an internal node, use the ratio of
   the remaining count in the chosen child to the remaining count in the
   node. Prove that the product along all paths is still \(1/M(S)\).
5. Define the unrounded ideal saving
   \[
   G(S)=
   \sum_{a\in S}(C_a-d_a)-h-\log_2 M(S)
   \]
   for nonempty \(S\), and \(G(\varnothing)=0\). Prove that an exact optimum
   is obtained by a zero-one knapsack over total extracted count. For an
   item \(a\), use weight \(n_a\) and value
   \[
   V_a=C_a-d_a+\log_2(n_a!).
   \]
   If \(D(k)\) is the maximum item value at total weight \(k\), prove
   \[
   \max_S G(S)=
   \max\left(
   0,\max_{1\le k\le n}
   \left[
   D(k)-h-\log_2\frac{n!}{(n-k)!}
   \right]\right).
   \]
6. Give canonical exclusion-on-tie rules, a finite certificate, and
   \(O(|A|n)\) time and \(O(|A|n)\) certificate-bit bounds.
7. Prove exact reconstruction when the category stream is decoded before the
   residual stream and the parent predictor is updated with every
   reconstructed symbol, including extracted symbols.
8. State why real-valued multinomial optimality does not prove the byte
   length of a finite-precision arithmetic implementation.

## Frozen application

Use the exact opening-1M endpoint trace represented by:

```text
results/wrt_wiki_shell_v1/trace_1m_v1/residual_cache.tsv
results/wrt_wiki_shell_v1/trace_1m_v1/wrt_stream.bin
results/wrt_wiki_shell_v1/trace_1m_v1/output.cmix
```

The joint side stream uses:

```text
version and selected count: 2 bytes
side-payload length:        4 bytes
each selected symbol:       1 byte
each selected count:        3 bytes
```

The category sequence is coded by the frozen 16-bit binary-tree range model.
The residual symbols retain their exact parent bit probabilities. The empty
selection emits the parent payload unchanged.

Promotion requires:

```text
parent payload identity
exact side-coder roundtrip
exact WRT reconstruction
net gain at least 2,000 bytes per million raw bytes
complete counted source cost
```

Failure retires joint full-symbol multinomial extraction. It does not retire
context-conditioned fibers, variable-length phrases, or a new information
source.
