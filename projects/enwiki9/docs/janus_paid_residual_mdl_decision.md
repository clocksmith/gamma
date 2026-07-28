# JANUS Paid Residual MDL Q0 Decision

Date: 2026-07-28

Candidate: `janus_paid_residual_mdl_q0_v1`

Status: `PROVISIONAL_WITNESS_REQUIRES_CORRECTED_Q0`

Score credit: zero

## Exact opening-1M result

The oracle replayed the exact endpoint428 parent payload at 173,859 bytes.
On the represented complete population, the parent required 173,807 bytes and
JANUS required 168,900 bytes, an exact arithmetic gain of 4,907 bytes.

The represented raw population was 999,723.675 bytes. The measured gross rate
was 4,908.356301 B/M.

The frozen model artifact was 127,695 bytes and the compressed implementation
source was provisionally 3,883 bytes. Amortized over one billion raw bytes, the
projected package-adjusted rate was 4,776.778301 B/M.

The literal opening-1M two-part result remains negative by 126,671 bytes because
the fixed model cost is not amortized at that scope. This candidate therefore
has no achieved score improvement and contributes no bytes to the frontier.

## Controls

The node-bias control gained only 46 exact bytes. The circular-shift control
lost 11,586 exact bytes. JANUS therefore passed the predeclared tests that its
gain exceeds a static calibration and is not reproduced by a temporally
misaligned residual stream.

## Superseding correction

The original Q0 compared freshly terminated complete-block substreams, used
provisional package accounting, did not charge J1 as an independent paid
candidate, and did not require A/B model and payload identity. Its 4,907-byte
signal remains useful evidence, but it does not authorize Q1.

The candidate is blocked pending a corrected Q0 with full-stream arithmetic,
parent payload byte identity, candidate arithmetic decode, WRT/raw inverse
binding, canonical JMDL1 and JBIAS1 serialization, frozen decoder allowances,
J1/J2 projected-total selection, and same-machine A/B determinism.

## Prior decision, now withdrawn

The earlier authorization for one frozen canonical-10M test is withdrawn until
the corrected Q0 passes. The exact 10M endpoint trace remains authorized as
zero-credit infrastructure because it is independently archive-identity gated.

The 10M gate is:

```text
exact parent replay                 required
gross exact gain                    >= 30,000 bytes
package-adjusted projected net      >= 21,000 bytes
node-bias control                   beaten
circular-shift control              beaten
deterministic training receipt      required
```

No integer decoder, native integration, 100M run, or full-corpus run is
authorized by this result. Failure at the frozen 10M gate retires this model
family unchanged.

Authoritative receipt:

`results/janus_paid_residual_mdl_1m_v1/decision.json`
