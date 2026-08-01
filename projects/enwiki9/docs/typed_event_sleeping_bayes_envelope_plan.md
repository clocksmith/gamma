# Typed Event Sleeping Bayes Envelope

Candidate architecture: `typed_event_sleeping_bayes_envelope_v0`

Status: highest-priority parent-recovery and exact-trace-gated proposal.

Score credit: zero. The exact full-1G score remains unknown. The counted
planning forecast remains 109,389,323 bytes, leaving 1,389,323 bytes of debt to
the 108,000,000-byte design target.

## Claim boundary

The endpoint428 parent is the exact gate-dot-fuse plus output-update-loop
codec. Its original and minified counted source packages have distinct and
indispensable identities:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Reconstructive package | 280,147 | `19ddcc4ec1b6f31958bed4aa19c0fbc83a56c78121933e1447e4ee011547aee0` |
| Minified counted package | 261,125 | `b6fe6b09d6adbd8a287a08d284ca1f439ba72ff007b4d40c66bf7647a54a5d43` |
| Clean wrapper program | 2,326,416 | `37ee8cd73ade9845b1afcb39f3bbd9358956c3ff9aea3b69328da7441ee32361` |
| Clean backend | 1,899,840 | `d1066630f0d58894e69bd84519ec7d0f608b9e2fce67ab9ebedde65c58eca194` |

Recovering only the 280,147-byte package supports the older 109,408,345-byte
forecast. The current 109,389,323-byte forecast requires the 261,125-byte
minified package or a deterministic recreation of those exact bytes.

Both package pairs, both clean wrappers, both clean backends, and the runtime
backend are present under `/home/x/enwiki9-nonproof` and match their recorded
hashes. Python ZIP integrity checks report no bad member. The archived 10M
payload and independent re-encode are both 1,634,500 bytes with SHA-256
`93d7f5cb69ecad5457078ff9de34a63d8b0a8dcf21cc0fa9e20df895e13b1880`.
The restored 10M corpus matches the canonical input hash
`5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97`.

The exact source identities and 10M proof are therefore materialized on this
host. A fresh exact 1M replay and a parent-trace identity certificate remain
before the event shadow. No full-1G result or runtime qualification follows
from artifact recovery.

Do not alter the FX2 double-update behavior during recovery. A correction, if
tested, is a separately named child experiment after exact parent identity.

## Mathematical envelope

Let B be the exact endpoint428 probability assignment and let E-star be a
baseline-backed typed-event sleeping expert. Both predict the same bitstream
under the same causal filtration. Outside a decoder-visible eligible event:

```text
E-star probability = B probability
```

Inside an eligible event, E-star may deviate using candidates constructed only
from completed decoded state. The ideal whole-sequence mixture is

```text
P_M(x) = pi_B P_B(x) + pi_E P_E-star(x)
```

with `pi_B = 65535/65536` and `pi_E = 1/65536`. It obeys

```text
L_M <= L_B - log2(pi_B)
L_M <= L_E-star + 16 bits
L_M >= min(L_B, L_E-star)
```

The last inequality is crucial: a global Bayes envelope is a safety mechanism,
not evidence of local complementarity. Sparse benefit must already be compiled
into E-star, or exposed by the explicit fixed-block selector control.

## Same-stream typed-event expert

At a decoder-visible event boundary, E-star constructs a deterministic prefix
trie over candidate continuations:

1. Enumerate suffix receipts from completed WRT history.
2. Add Wiki-field continuations whose field state is already visible.
3. Add completed entity, title, and link receipts.
4. Add completed structural-chain continuations.
5. Add a literal escape whose bit probability is exactly B.
6. Assign deterministic priors from the frozen paid MDL code.
7. Aggregate surviving candidate mass under the zero and one trie branches.
8. Remove inconsistent candidates after each decoded bit.
9. Add the current event to memory only after its final byte is reconstructed.

No action label is transmitted separately. The candidate prior is paid through
the arithmetic probabilities. Both B and E-star observe and update on every
truth bit, regardless of which probability is coded.

`typed_receipt_ringmix_v1`, the direct WRT-event SRSTC endpoint, and the raw
SRSTC codecs are code donors only. Their retired or substrate-mismatched
receipts provide no score credit to this candidate.

## Causal integrity gate

Before scoring, the realization must prove:

- event boundaries, fields, and candidates are visible from completed state;
- current event length is not exposed early;
- no candidate reads future bytes or a future-derived control state;
- event memory mutates only after event completion;
- E-star equals B bit-for-bit outside eligible regions;
- both models update on every actual bit;
- all fixed-point probabilities are legal and nonzero;
- a second causal replay reproduces candidate states and probabilities.

Any violation is an infrastructure/correctness failure, not a compression
rejection.

## Frozen opening-1M control family

The first exact shadow uses one implementation, coder, population split,
candidate cap, memory cap, support threshold, prior code, and event parser:

```text
B0  exact endpoint428
C0  matched-capacity state-blind receipt control
E0  suffix receipts only
E1  E0 plus decoder-visible Wiki-field keys
E2  E1 plus entity/title/link receipts
E3  E2 plus structural-chain candidates
M0  ideal high-precision Bayes(B0, E3-star)
M1  fixed-point Bayes(B0, E3-star)
S0  global one-bit selector between B0 and E3-star
S1  deterministic fixed-block selector; both states always update
```

The event universe, candidate ordering, tie breaks, caps, priors, memory
eviction, fixed-point scale, and S1 block size are frozen before chronological
holdout is opened. C0 receives the same opportunities and capacity while
destroying typed alignment.

Promotion requires:

```text
parent payload identity                         exact
candidate arithmetic decode                     exact
WRT and raw reconstruction                      exact
second model/P1/archive replay                   byte-identical
net chronological holdout gain                  >= 2,100 B/M
E3 materially better than C0                    required
fixed-point loss versus ideal gain              < 5%
gain not confined to opening pages or refs      required
all program, table, model, and framing bytes     counted
```

The oracle returns status zero for both promotion and a valid compression
rejection. Nonzero means malformed evidence.

## Gate sequence

### Gate 0 - parent artifacts and replay

Verify both counted packages, clean program, backend, dictionary, canonical
1K/1M/10M archives, roundtrip, and deterministic re-encode. A fresh 1M replay
and exact parent P1 trace are the smallest missing evidence. If the minified
package cannot be reproduced, use 280,147 program bytes until a new exact
minification receipt exists.

### Gate 1 - causality

Run the integrity checks above before reading compression economics.

### Gate 2 - opening 1M

Run B0 through S1. Retire unchanged below 2,100 net B/M or when E3 does not
beat C0. Do not rescue a miss by sweeping caps, priors, support, windows,
selector blocks, or receipt families.

### Gate 3 - distant 1M

Only a Gate 2 pass authorizes the exact frozen realization near raw offset
500M. Require at least 2,100 B/M to retain the primary target claim.

### Gate 4 - native 10M

Only two passing 1M populations authorize native source integration. Require
at least 21,000 archive bytes saved, exact source-package delta, exact
roundtrip, deterministic re-encode, decimal-10GB memory compliance, and a
controlled runtime receipt. Recompute the forecast; do not add shadow gains to
the existing forecast.

### Gate 5 - full 1G

Authorize only after all source artifacts, exact 10M economics, distant
transfer, runtime, memory, and forecast inputs are present. The governing
condition is

```text
archive gain at 1G > 1,389,323 + source delta + framing delta + safety reserve
```

## Disposition

```text
candidate:          typed_event_sleeping_bayes_envelope_v0
status:             highest-priority parent-trace-gated proposal
compression result: unmeasured
mathematical safety: proved only for the ideal same-stream mixture
source status:      original/minified packages and parent 10M proof recovered
score credit:       0
full-corpus claim:  none
```

ACS-MATH-SEAL-2 remains unbound. No solver distribution is authorized.
