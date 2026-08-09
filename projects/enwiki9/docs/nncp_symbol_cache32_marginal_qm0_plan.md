# NNCP addressless cache-32 symbol marginal

Candidate: `nncp_symbol_cache32_marginal_qm0_v1`.

Epistemic tier: same-symbol-domain causal arithmetic shadow. It receives zero
Hutter score because its faithful probabilities come from a receipt-bound
teacher trace rather than an eligible decoder-built backend.

## Mechanism

For every exact NNCP symbol, retain the preceding 32 decoded symbols from the
same native stream. Treat their empirical distribution as a latent cache
expert and marginalize it with the faithful parent distribution using fixed
prior masses `16:1`:

```text
P(symbol) = 16/17 * P_parent(symbol) + 1/17 * P_cache32(symbol)
```

The mixture is evaluated conditionally down the existing balanced symbol tree.
After each decoded branch, base and cache masses update by Bayes' rule and
cache candidates incompatible with the decoded prefix disappear. Thus a novel
symbol pays only the single symbol-level prior penalty; it does not pay the
penalty again at every branch. No source identity, distance, length, selector,
or cache contents are transmitted.

The capacity-matched control uses the preceding 32 symbols from stream
`(stream + 17) mod 32`, excluding the current position. Those symbols are also
decoder-visible and use the identical prior and arithmetic code.

## Frozen gate

Run on the exact faithful/full-midpoint `262,144`-symbol population. Encode a
same-coder faithful payload, the genuine cache payload twice, and the
cross-stream control. Decode the genuine cache payload and reproduce every
symbol. Original-coordinate thirds use independent terminated shadow coders
while all model state continues causally across the full population.

Promotion within the teacher lane requires:

```text
actual candidate gain versus faithful       >= 4,000 bytes
candidate gain in every chronological third  > 0 bytes
candidate margin over cross-stream control  >= 1,000 bytes
candidate repeat payload                     byte-identical
candidate arithmetic decode                  exact
compressed source                           <= 65,536 bytes
```

A miss retires this exact cache window, prior, source geometry, and
symbol-level marginal without parameter sweeps. A pass still cannot inherit
NNCP score or eligibility; it only authorizes porting the measured coordinate
to a complete open same-object backend.
