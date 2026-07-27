# Budget-Preserving Capacity Problem

## Problem

Let there be `r` independent finite tables. Table `i` currently stores `n_i`
records of `a` bytes each, so its immutable payload budget is

```text
B_i = a n_i.
```

A representation theorem replaces every record by an observationally
equivalent record of `b` bytes, where `0 < b < a`. No byte may move between
tables. Choose integer capacities `m_i >= n_i` satisfying

```text
b m_i <= B_i
```

and maximize the total capacity `sum_i m_i`.

Prove:

1. The unique coordinatewise maximal feasible capacity is
   `m_i = floor(a n_i / b)`.
2. This vector maximizes total capacity and every nonnegative
   coordinatewise objective.
3. The exact added capacity is
   `sum_i floor((a-b)n_i/b)`.
4. The unused payload in table `i` is the unique residue
   `(a n_i) mod b`, hence is smaller than `b`.
5. Give a canonical finite construction and an exact verifier.

## Frozen FXCM instance

Use `a=96`, `b=92`, and the 18 capacities:

```text
2097152 4194304 2097152 2097152 2097152 2097152
4096 524288 1048576 2097152 2097152 2097152
2097152 2097152 524288 32768 131072 524288
```

Report every new capacity, total added capacity, original payload, new
payload, and residual slack.

## Transfer boundary

The theorem licenses only a budget-preserving capacity vector. It does not
prove that the additional records improve prediction, that an index mapping
is correct, or that virtual payload equals measured RSS. Those require the
dense-range theorem and native codec receipts.
