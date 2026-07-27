# Independent Problem SC-1: Cardinality-Priced Surprise Extraction

Status: `FROZEN RESEARCH PROBLEM`
Version: `SC-1`

## Definitions

Let \(w_1,\ldots,w_n\in\mathbb R\) be item benefits. Selecting a subset
\(S\subseteq\{1,\ldots,n\}\) incurs a cost depending only on cardinality:

\[
K(|S|).
\]

The objective is

\[
\sum_{i\in S}w_i-K(|S|).
\]

## Questions

Prove all of the following.

1. For fixed cardinality \(k\), a maximum-benefit subset consists of the
   \(k\) largest weights.
2. A fixed item order resolves ties canonically.
3. If \(w_{(1)}\ge\cdots\ge w_{(n)}\) are the canonically sorted weights, the
   exact optimum is
   \[
   \max_{0\le k\le n}
   \left[
   \sum_{j=1}^kw_{(j)}-K(k)
   \right].
   \]
4. Give an \(O(n\log n)\) algorithm and finite certificate.
5. When a \(k\)-subset is represented by its enumerative rank and each
   selected item carries \(b\) literal bits, prove the exact fixed-length cost
   \[
   K(k)=h+bk+\left\lceil\log_2\binom nk\right\rceil,
   \]
   where \(h\) is fixed framing.
6. Prove exact reconstruction when selected positions and literal values are
   supplied before the remaining stream is decoded.

## Frozen application

Each WRT byte is one item. Its benefit is its parent ideal qbit cost. A selected
byte is omitted from parent range coding and transmitted literally. The
selected position set uses one global enumerative rank.

Costs are:

```text
header:          4 bytes
selected value:  1 byte each
position set:    ceil(log2(binomial(n,k))) bits, rounded once
```

The exact optimum over every \(k\) is evaluated once. Promotion requires exact
parent payload identity, exact reconstruction, and at least 2,000 net bytes per
million raw bytes. Failure retires generic sparse-surprise extraction without
grouping or cardinality sweeps.
