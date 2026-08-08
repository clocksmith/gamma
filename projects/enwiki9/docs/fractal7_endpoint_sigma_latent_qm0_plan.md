# FRACTAL-7 Endpoint-Sigma latent continuation QM0

Candidate: `fractal7_endpoint_sigma_latent_qm0_v1`.

## Question

Can persistent, addressless exact-event source marginalization expose target-scale
information against the exact Endpoint428 probability trajectory without a source
selector, occurrence number, or copy length?

## Frozen model

At every complete WRT-event boundary, query decoder-built indexes for earlier
continuations sharing the exact preceding 2, 4, or 8 events. At most eight recent
continuations per suffix enter a 128-state latent population. Existing states retain
15/16 mass and new states share 1/16; if no state survives, new states receive all
mass. States predict prior decoded bits, advance after the truth bit, die on a
mismatch, and merge when they reach the same prior bit pointer.

A causal sleeping two-expert mixture combines this ECHO probability with the exact
Endpoint428 Q16 probability. Mixer state is keyed by source support, posterior
concentration, and bit position. It updates only after the current truth bit.

## Arms

- `SIGMA`: persistent exact-event suffix sources.
- `RECENCY`: only the most recent exact-event continuation.
- `SHUFFLED`: equal source count mapped deterministically to unrelated prior events.
- `BYTE8`: persistent sources from an exact preceding eight-byte context.

All arms use identical state caps, injection, mixture, and finite probability rules.
No arm emits source metadata. Direct-mapped indexes are capacity-bounded and hash
hits are verified against exact prior bytes or events.

## Gates

This QM0 receipt is an ideal finite-codelength screen and earns zero score credit.
Require:

- SIGMA truth-aware displaced ceiling at least 100,000 bytes on canonical 10M;
- ceiling margin over every control at least 20,000 bytes;
- causal SIGMA gain at least 75,000 bytes;
- causal margin over every control at least 10,000 bytes;
- every chronological stream third positive;
- all sources strictly earlier than the coded truth bit.

A miss retires this exact suffix set, state cap, mass injection, and mixture context.
It does not retire every possible latent-source model.

## Claim boundary

No arithmetic archive, decoder package, raw roundtrip, program accounting, runtime,
transfer, or full-corpus result is claimed. A gate pass would authorize an exact
finite arithmetic payload and decoder only.
