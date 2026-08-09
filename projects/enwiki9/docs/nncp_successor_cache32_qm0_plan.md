# NNCP Successor Cache-32 QM0

## Question

Does the exact midpoint gain contain short episodic transitions that the
successful unconditional cache-32 marginal cannot express?

## Frozen mechanism

For each stream and target symbol, use the immediately preceding decoded symbol
as a key. Search only the preceding 32 decoded positions and collect the symbols
that followed earlier occurrences of that key. Marginalize those successor
symbols against the faithful NNCP branch probability with prior masses 16:1.
Source locations, selectors, distances, and lengths are never transmitted.

## Controls and gate

The exact same arithmetic coder also emits the faithful base, the previously
measured unconditional cache-32 arm, and a lag-17 context-query control. Require
exact decode, deterministic payload identity, at least 10,000 actual bytes over
base, at least 1,000 bytes over each control, positive original-coordinate
thirds, and at most 65,536 compressed source bytes. Any miss retires this exact
mechanism without window, lag, prior, reset, or blend sweeps.

This is a trace-bound causal shadow. It receives no score, forecast, or LibNC
eligibility credit.
