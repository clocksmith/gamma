# NNCP Midpoint plus Cache-32 Joint Replay QM0

Candidate: `nncp_midpoint_cache32_joint_qm0_v1`

## Question

Does the frozen decoder-visible cache-32 marginal retain useful information
after the full midpoint teacher has already changed the exact probability
trajectory?

This is the only permitted re-entry for the mature cache realization. Separate
midpoint and cache gains are not additive. The gate independently terminates
faithful, midpoint-only, midpoint-plus-cache, and midpoint-plus-cross-cache
arithmetic streams on the same receipt-bound `262,144` symbols.

## Frozen mechanism

- Balanced `16,392`-symbol branch alphabet.
- Full-midpoint branch frequencies from
  `nncp_midsegment32_update_262144_qm1_v1`.
- Cache window `32` over preceding decoded symbols in the same native stream.
- Midpoint-to-cache prior mass `16:1`, updated causally within each symbol.
- Capacity control from stream `(s + 17) mod 32` at the same prior positions.
- No selector, distance, length, cache contents, or source address is emitted.
- No cache-window, prior, lag, midpoint, or bucket sweep.

The probability traces remain teacher evidence. They are not reconstructed by
an eligible submitted decoder, so this gate has zero score credit regardless
of outcome.

## Promotion and kill conditions

All of the following are required:

- faithful and midpoint-only payloads reproduce their registered bytes and
  hashes exactly;
- midpoint-plus-cache improves midpoint-only by at least `4,000` actual bytes;
- incremental gain is positive in every independently terminated
  original-coordinate third;
- midpoint-plus-cache beats midpoint-plus-cross-cache by at least `1,000`
  actual bytes;
- the repeat payload is byte-identical;
- arithmetic decoding reconstructs all `262,144` symbols exactly;
- compressed incremental source is at most `65,536` bytes.

A miss retires this joint realization without parameter rescue. A pass only
authorizes a same-object mature joint replay after a mature full-midpoint trace
exists. It does not authorize native integration, a full-corpus forecast, or
use of closed LibNC in an official package.
