# Delta-MIDAS PPM0 Joint Evaluator v4

## Scope

This is a correction-only evaluation successor for the frozen
`cmix_obias_bithead_delta_midas512_ppm0_q0_v3` C/P/K/O/R/D/S artifacts.
It does not change compressor source, corpus, arm definitions, coefficients,
numeric behavior, package boundary, or promotion thresholds.

## Correction

The v3 evaluator could dereference a missing `encode1` receipt while checking
whether O/R/D/S controls were live. A missing or malformed terminal receipt is
an experiment failure, not an evaluator exception. v4 therefore short-circuits
each control check and records `controls_live: false` when the receipt is absent.

## Frozen decision rules

- Every arm must complete two byte-identical encodes and one exact bare decode.
- C and P payloads must be identical.
- P and K probability, state, and payload identities must match.
- Encode, repeat encode, and decode receipts must synchronize for every
  instrumented arm.
- O/R/D/S injections must be nonzero and all adapter arithmetic must be finite.
- D must beat P, K, O, R, and S in actual arithmetic-coded payload bytes.
- Every monitored process tree must stay within 9,765,625 KiB RSS.
- D incremental required program material must not exceed 65,536 bytes.

The evaluator grants zero compression or prize credit. Promotion still requires
all gates to pass and preserves the sealed v3 algorithm identity.
