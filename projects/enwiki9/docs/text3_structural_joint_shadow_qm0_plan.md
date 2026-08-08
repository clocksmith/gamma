# TEXT3 Structural-Joint Shadow QM0

## Objective

Test whether the structural state in Kaido Orav's 2025 `text3.cfg` contains
target-scale information absent from the exact Endpoint428 probability stream.
This is a zero-credit causal shadow, not a ZPAQ score comparison and not a
dictionary-transform experiment.

The canonical parent forecast is `109,389,323` counted bytes, leaving
`4,389,323` bytes of debt to the `105,000,000` objective. The opening-10M gate
therefore requires `45,000` gross bytes and `40,000` bytes after compressed
shadow-source accounting. A smaller effect cannot justify native integration.

## Source audit

The official ZPAQ utilities page links Kaitz's configuration bundle. Audited
artifacts:

- `text3.zip`: SHA-256
  `54491c9d5e57cd60adef1cde5b61447b5c272525b6ce68e11b6beceac87826b2`.
- `text3.cfg`: 5,619 bytes, SHA-256
  `395e5c2338fd2bcbfa6f6616e84568c357278baa044291236d65daeec0fead91`.

The configuration combines character-class history, byte and word histories,
line column, bracket depth, a colon-conditioned prior word, and a causal byte
transition table. Endpoint428 already contains strong word, match, bracket,
indirect, PPMD, PAQ8, FXCM, WRT, and recurrent models. The gate therefore tests
only the joint structural coordinates, not TEXT3 as a standalone compressor.

## Exact population and arms

- Input: canonical opening 10,000,000 raw bytes.
- Coded population: the exact 6,251,857-byte WRT stream inverted to that raw
  input.
- Parent: exact 50,014,816-row Endpoint428 Q16 P1 trace.
- `P0`: parent only.
- `C0`: causal character-class history plus prior byte.
- `L0`: causal line column plus prior byte.
- `S0`: a deterministic cyclic misalignment of the complete joint state.
- `J0`: character classes, column, bracket depth, word phase,
  colon-conditioned word hash, and byte-transition state jointly.

Each expert is a causal KT binary trie. Its key contains only state completed
before the current byte plus the already decoded prefix of the current byte.
The scored paid arm is a Bayesian mixture with an exact parent expert. A
per-bit selector is reported only as a zero-credit ceiling.

## Decision

Promote only if `J0` saves at least 45,000 bytes with every chronological third
positive, beats every non-parent control by 5,000 bytes, and retains 40,000
bytes after compressed source accounting. Otherwise retire this exact
structural joint. A pass authorizes a native compact implementation and exact
payload gate; it does not alter the Hutter frontier by itself.

