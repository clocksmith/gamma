# NNCP Branch-Residual-Weighted Cache-32 QM0

Candidate: `nncp_branch_residual_cache32_qm0_v1`

## Mechanism

The exact midpoint/cache joint replay proves that midpoint adaptation and
recent exact symbol identity retain nonredundant information at `262,144`
symbols. This gate tests one compact causal explanation: midpoint adaptation
may emphasize symbols the parent just underpredicted.

After a symbol is decoded, compute its integer realized branch error:

```text
e = sum(32768 - realized_faithful_branch_mass)
```

Store `(symbol, e)` for the preceding `32` symbols of the same native stream.
At a future symbol branch, compatible cached occurrences vote with weight `e`
instead of unit weight. The weighted cache distribution is marginalized with
the faithful branch probability using the already frozen `16:1` prior and
Bayesian within-symbol update. Encoder and decoder rebuild every error from
earlier truths and earlier faithful probabilities. No cache, error, selector,
distance, length, or source identity is transmitted.

## Matched arms

- `base`: faithful probability trace.
- `uniform`: the already measured unit-weight cache-32 marginal.
- `weighted`: identical cache with each symbol occurrence weighted by its own
  preceding realized error.
- `rotated`: identical symbols and identical error-weight multiset, but each
  cache occurrence receives the next occurrence's weight cyclically.

The rotated arm tests the residual-to-symbol association rather than generic
weight capacity.

## Frozen decision

Promotion requires at least `10,000` actual bytes over `base`, at least
`1,000` bytes over both `uniform` and `rotated`, positive
`weighted - uniform` savings in every independently terminated
original-coordinate third, byte-identical repeat, exact arithmetic symbol
decode, and compressed source at most `65,536` bytes.

Any failure retires this mechanism without error transform, weight floor,
window, prior, lag, or bucket sweeps. This remains zero-credit because the
faithful probability trace is a teacher artifact and closed LibNC is not an
eligible submission dependency.
