# CMIX21 / FX2 family trace correction

## Decision

The earlier full-CMIX21 complement is real only on its measured substrate. Its
`1,400.007 B/1M` result used the original-order FX2/WRT stream, not the
geometry-order stream used by the constructive PAQ-free `96x2` candidate. It
must not be subtracted from that candidate's `109,789,279` forecast.

The corrected matched-geometry experiment is terminal. A frozen `62.5%`
probability blend of the continuously evolved full-CMIX21 endpoint with the
exact archive-producing `96x2` endpoint saved `290` range-coded bytes over the
first `1M` raw bytes. Its internal holdout saved `71` bytes, normalized to
`355 B/1M`, with zero block regressions and exact decoder replay. This barely
covers the `289.279 B/1M` forecast debt before any source, state, or integration
cost and fails the frozen `500 B/1M` native-integration screen.

The first compact-family screen did not validly test FXCM or PAQ8. `CMX21F2`
stored each family's last output, and those terminal slots are constant `0.5`
padding values. Both columns therefore contained only integer probability
`32768` over all `4,805,936` rows.

## Corrective mechanism

The quarantined `CMX21F3` observation build records the most-confident causal
probability within FXCM and PAQ8, matching the existing summaries for other
multi-output families. It uses a new trace magic and leaves the arithmetic
prediction path untouched.

The `5,360`-row neutrality gate established:

- identical `250`-byte archives, SHA-256
  `c0abe25414f3153c1d5045d17a2de14b8431ef35d48408d06e5efaf2f7e63e58`;
- identical final P1 traces, SHA-256
  `28193076d0ba0c8e5aaa5071e2badc999eaff35b74b56f5a366c5fb54118b495`;
- `928` distinct corrected FXCM values and `755` distinct PAQ8 values;
- peak process-tree RSS `7,335,576 KiB`, below decimal `10GB`.

Receipt:
`/home/x/enwiki9-nonproof/results/cmix21_f3_neutrality_1k/receipt.json`.

## Corrected full-scope result

`CMX21F3` completed the identical `1M` FX2/WRT replay without changing the
archive or final probability stream. On the frozen whole-event split, the full
post-SSE teacher retained `1,482.783 B/1M` on sealed holdout, but the strongest
compact family mixture retained only `323.434 B/1M`. All corrected-family
subsets therefore miss the `700 B/1M` discovery floor.

Receipt:
`/home/x/enwiki9-nonproof/results/cmix21_on_fx2_store_1m_f3/family_distillation_v2.json`.

That receipt is an original-order attribution result. The two WRT stores have
different identities:

```text
original-order store: 1e209c7d19a22af5ce6a1de3bab1fc636669f40686aebd88bbe9dc8e5411e583
geometry-order store: 21b998d3f5ede3cfe24147acac0a92ad19df0c477fa7a52330be488c34578952
```

## Matched geometry correction

The archive-neutral `CMNEST1` observation build recorded, before current-bit
update, the exact `96x2` post-SSE probability, pre-SSE probability, active
96-cell byte endpoint, continuously evolved 160/200-cell probes, and all 26
layer-0 mixer outputs. Its observed archive is byte-identical to the known
`174,268`-byte `96x2` archive, SHA-256
`00d9bda24a8ee322b2b9ac81dcc81099af32afcca95519a8884dd9d69d073776`.
The base probability replay also reproduces the exact archive payload.

A separate full-CMIX21 run evolved all of its state continuously over the
byte-identical geometry WRT stream. It emitted exactly `4,805,936` endpoint
rows, produced a standalone `174,104`-byte archive, stayed below decimal
`10GB` at `8,767,964 KiB`, and joined the matched trace without a row or truth
mismatch.

The exact two-expert result is:

| Mechanism | Full gain | Internal holdout rate | Boundary |
|---|---:|---:|---|
| Best individual `96x2` endpoint blend | `50` bytes | `45 B/1M` | Insufficient |
| Full CMIX21 fixed blend, weight `625000` | `290` bytes | `355 B/1M` | Exact range encode/decode; zero holdout block regressions |
| Full CMIX21 causal fixed share, best dev setting | Below fixed blend | `324.726 B/1M` dev shadow | Insufficient |
| Train-fitted affine-logit base plus full endpoint | `298.963` qbit bytes | `351.665 B/1M` | All holdout blocks positive, but below the `500 B/1M` screen before fixed-point and code cost |
| Existing active interactions, global logistic diagnostic | `130.157` bytes | `58.366 B/1M` | Insufficient |
| Active interactions plus 160/200 probes | `368.410` bytes | `313.439 B/1M` | Insufficient and adds recurrent state |
| Bit-position routing plus 160/200 probes | `446.017` bytes | `329.700 B/1M` | Below screen and unstable across splits |

Primary exact receipt:
`/home/x/enwiki9-nonproof/results/cmix21_full_teacher_geometry_1m_v1/matched_screen_receipt.json`.
The matched trace and source instrumentation are discovery-only and do not
authorize promotion.

The affine result is now reproducible independently of the earlier family
probe. A three-coefficient Newton logistic fit used only the matched training
prefix, then saved `70.333` qbit bytes over the proportional `200K` holdout,
or `351.665 B/1M`, with all eight holdout blocks positive. Base-only
calibration saved only `11.589 B/1M`, so the measured gain is genuine endpoint
complement rather than calibration leakage. It remains too small to justify
fixed-point integration. Receipt:
`/home/x/enwiki9-nonproof/results/cmix21_full_teacher_geometry_1m_v1/affine_endpoint_screen.json`;
replay tool: `tools/fx2_cmix21_affine_endpoint_screen.py`.

A subsequent train-only contextual screen used exact current-byte prefixes,
bit position, base-confidence buckets, endpoint vote, and endpoint spread. The
profile selected on development retained `55.981 B/1M` on holdout; the largest
holdout result among the frozen profiles was `58.955 B/1M`. This is far below
the `500 B/1M` headroom gate, so the failure is the measured endpoint universe,
not a missing selector search. Receipt:
`/home/x/enwiki9-nonproof/results/cmix21_nested_trace_1m_v1/contextual_endpoint_screen.json`.

## Promotion boundary

The corrected family averages, individual `96x2` mixer endpoints, continuous
160/200-cell probes, and full-CMIX21 final endpoint are retired from the current
promotion queue in these measured forms. This retires the current endpoint
universe, not contextual compression generally. A selector cannot manufacture
the missing incremental information.

This retirement does not apply to the separately constructive standalone
`200x2` PAQ-free codec. That codec changes the complete recurrent and downstream
mixer trajectory instead of adding the recorded 200-cell probe to a frozen
`96x2` trajectory. Its first-`1M` receipt therefore remains an active capacity
discovery result, subject to larger-scope and execution qualification.

The next probe must add a new causal WRT-native endpoint: decoder-built
page/phrase memory, title echoes, template/reference continuations, or a direct
FX2-residual SRSTC mechanism. It must first clear the `500 B/1M` held-out
headroom screen against the exact geometry `96x2` probability stream. Do not
run another broad native gate or tune a richer selector over these same
endpoints.

This remains shadow/teacher evidence. Only counted native integration with
roundtrip, determinism, RSS, and exact archive reduction can advance the proof
lane.
