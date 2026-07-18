# PAQ-free FX2/CMIX21 LSTM frontier

## Verdict

The PAQ-free hybrid is a useful bounded substrate, but fixed `96x2` is retired
from the promotion queue because its exact cumulative `10M` archive gain is
only `509.8` bytes per `1M`. Its fully counted forecast requires `799.079`
bytes per `1M` under the original package and `762.537` under the reproducible
two-entry source package.

This is an economics retirement of fixed `96x2`, not a claim that the hybrid
mechanism is disproven. A separate sealed default `200x2` codec is constructive
at the first `1M`, but its frozen offset-`500M` reset archive saves only
`370 B/1M` against the reproducible-source `762.424 B/1M` requirement. It is
therefore retired without replay or a larger unchanged gate. Exact `112+80`
wrapper identity, roundtrip, and determinism pass at cumulative `10M`; on the
offset-`500M` reset slice it saves only `353 B/1M` versus FX2 and only `4 B/1M`
over native `112x2`. Unchanged recurrent factorization is therefore retired
from promotion, not erased as capacity evidence.

A phase-aligned `112x2 + 2x44x2` construction is also fully constructive at
the first `1M`: its counted source codec reproduces the `174,185`-byte archive,
roundtrips exactly, and linearly projects `109,280,922`. Its advantage over
plain portable `112x2` is only `9 B/1M`; after the extra `913` source bytes,
that is `8,087` projected full-corpus bytes before runtime. The portable build
fails the local execution screen, so this is mechanism evidence rather than a
promotion candidate.

## Counted boundary

```text
calibrated FX2 forecast:       110,181,114
target:                        109,500,000
forecast debt:                     681,114
baseline program bytes:            183,008
candidate source ZIP:               264,427
candidate option bytes:                   3
incremental program bytes:           81,422
archive marker bytes:                     1
required gross gain at 1G:          762,537
required gross rate:                762.537 B/1M
```

The exact `1M` constructive receipt saves `936` archive bytes and therefore
projects `109,326,537`, or `173,463` bytes below the target under the smaller
package. That is a linear forecast only. The exact `10M` screen saves `5,098`
bytes, which normalizes to `509.8 B/1M` and projects `109,752,737`, or
`252,737` bytes above the target.

The reproducible default `200x2` source package is `264,314` ZIP bytes plus
three option bytes. Its incremental program cost is `81,309` bytes, so its
fully counted required gross rate is `762.424 B/1M`. The first-`1M` gain of
`1,149 B/1M` does not transfer: the offset-`500M` reset slice saves only
`370 B/1M`, missing the floor by `392.424 B/1M`.

The phase-aligned source ZIP is `301,812` bytes plus three option bytes. Its
fully counted required gross rate is `799.922 B/1M`; the exact first-`1M` gain
is `1,019 B/1M`, leaving `219.078 B/1M` linear forecast margin. The matched
plain-`112x2` source ZIP is `300,899` bytes and its portable first-`1M` gain is
`1,010 B/1M`.

## Exact evidence

| Scope and cell | FX2 archive | Candidate archive | Gross gain | Rate | Candidate encode | Peak RSS | Boundary |
|---|---:|---:|---:|---:|---:|---:|---|
| `250K`, `80x2`, native fast-math | `45,366` | `45,171` | `195` | `780 B/1M` | `45.0379 s` | `7,477,732 KiB` | Archive screen |
| `250K`, `96x2`, native fast-math | `45,366` | `45,157` | `209` | `836 B/1M` | `50.0415 s` | `7,482,564 KiB` | Archive screen |
| `250K`, `112x2`, native fast-math | `45,366` | `45,135` | `231` | `924 B/1M` | `57.0499 s` | `7,486,360 KiB` | Archive screen |
| `250K`, `128x2`, native fast-math | `45,366` | `45,150` | `216` | `864 B/1M` | `63.0533 s` | `7,490,072 KiB` | Archive screen |
| `250K`, `160x2`, native fast-math | `45,366` | `45,133` | `233` | `932 B/1M` | `75.0653 s` | `7,498,440 KiB` | Archive screen |
| `250K`, default `200x2`, portable `O3` | `45,366` | `45,133` | `233` | `932 B/1M` | `122.0987 s` | `7,509,476 KiB` | Archive screen |
| `250K`, `200x2` BPTT prefix `1000`, stride `8` | `45,366` | `45,147` | `219` | `876 B/1M` | `148.1565 s` | `7,509,384 KiB` | Current-load archive screen; above local counted rate |
| `250K`, full-rate `112x2` plus two parity `44x2` LSTMs | `45,366` | `45,139` | `227` | `908 B/1M` | `105.1088 s` | `7,505,380 KiB` | Exact guarded archive screen |
| `250K`, symmetric `96+96` | `45,366` | `45,145` | `221` | `884 B/1M` | measured terminal encode | `7,503,824 KiB` | Retired: ten bytes worse than native `112x2` |
| `250K`, heterogeneous `112+80` | `45,366` | `45,131` | `235` | `940 B/1M` | measured terminal encode | `7,503,908 KiB` | Four bytes better than native `112x2`; advances to one `1M` screen |
| First `1M`, plain `112x2`, portable `O3` | `175,204` | `174,194` | `1,010` | `1,010 B/1M` | `349.3786 s` | `7,542,016 KiB` | Matched control; archive screen |
| First `1M`, `80x2`, native fast-math | `175,204` | `174,403` | `801` | `801 B/1M` | `145.1263 s` | `7,534,060 KiB` | Archive screen |
| First `1M`, `96x2`, native fast-math | `175,204` | `174,268` | `936` | `936 B/1M` | `172.1402 s` | `7,537,828 KiB` | Roundtrip and determinism proven |
| First `1M`, default `200x2`, portable `O3` | `175,204` | `174,055` | `1,149` | `1,149 B/1M` | `451.3781 s` | `7,565,212 KiB` | Roundtrip and determinism proven; later-region transfer fails |
| First `1M`, `200x2` BPTT prefix `1000`, stride `8` | `175,204` | `174,772` | `432` | `432 B/1M` | `450.491 s` | `7,565,156 KiB` | Retired: below counted rate |
| First `1M`, full-rate `112x2` plus two parity `44x2` LSTMs | `175,204` | `174,185` | `1,019` | `1,019 B/1M` | `383.4142 s` source build | `7,559,480 KiB` | Exact source archive identity, roundtrip, clean rebuilds; portable runtime screen fails |
| First `1M`, heterogeneous `112+80` | `175,204` | `174,120` | `1,084` | `1,084 B/1M` | measured terminal encode | `7,559,712 KiB` | Beats native `112x2` by `71` bytes; advances to cumulative geometry-title `10M` |
| Reset slice at offset `500M`, `96x2` | `45,612` | `45,277` | `335` | `335 B/1M` | `180.1466 s` | `7,448,548 KiB` | Disjoint archive screen; geometry inverse verified |
| Reset slice at offset `500M`, `200x2` | `45,612` | `45,242` | `370` | `370 B/1M` | measured terminal encode | `7,474,064 KiB` | Retired: misses source-accounted floor by `392.424 B/1M` |
| Cumulative geometry-title `10M`, `96x2` | `1,643,626` | `1,638,528` | `5,098` | `509.8 B/1M` | `1730.5062 s` | `7,553,300 KiB` | Exact guarded archive screen |
| Cumulative geometry-title `10M`, native `112x2` | `1,643,626` | `1,636,868` | `6,758` | `675.8 B/1M` | measured terminal encode | `7,556,272 KiB` | Clean guarded archive; misses counted ceiling by `1,234` bytes |
| Cumulative geometry-title `10M`, heterogeneous `112+80` | `1,643,626` | `1,635,670` | `7,956` | `795.6 B/1M` | measured terminal encode | `7,574,772 KiB` | Deflate ZIP misses by `37` bytes; clean-built bzip2 ZIP clears by `92` bytes |

The matched first-`1M` FX2 encode took `206.224 s`; fixed `96x2` took
`172.1402 s`. Its decode took `166.1382 s`, restored the exact input SHA-256,
and deterministic recompression produced the identical `174,268`-byte archive
with SHA-256 `00d9bda24a8ee322b2b9ac81dcc81099af32afcca95519a8884dd9d69d073776`.

The source ZIP builds identically from two clean extractions. The source codec
and wrapper hashes match between builds, and the wrapper's `1K` codec payload
is byte-identical to the discovery binary. These checks establish source
equivalence at the recorded scopes, not a full-corpus score.

### Geometry-title package correction

The native `112x2` source-package audit found a transform mismatch before
promotion. Its embedded `geometry.py` implements the geometry-only key, while
the active `10M` backend screen consumes the independently materialized
geometry-title stream with SHA-256
`fa8ec8a64e0e623796af5a6a11e789529680a6b1c4c43c87a97f726c3fbd87cf`.
The codec binary is still the exact source-built codec, so the active run is
valid backend-on-matched-stream evidence. It is not yet a constructive package
receipt.

The exact source change extends category title context from 40 to 80 bytes and
adds title context to infobox and fallback keys. In an in-memory raw-deflate
check, the `geometry.py` ZIP entry grows from `1,169` to `1,173` bytes. Treat
that four-byte delta as provisional accounting only. It raises the projected
full-scope requirement from `799.102` to `799.106 B/1M`; both round up to the
same `7,992`-byte required gain at `10M`, so the backend archive ceiling remains
`1,635,634`. If the backend archive passes its screen, promotion requires a
reproducibly rebuilt source ZIP, exact transform hash, wrapper archive identity,
roundtrip, and determinism. No package-level forecast may use the provisional
wrapper.

The backend did not pass: its terminal archive is `1,636,868`, which is
`1,234` bytes above the unchanged counted ceiling. The geometry-title wrapper
correction is therefore not built for fixed `112x2`; decode, deterministic
recompression, `100M`, and `1G` are forbidden. The terminal receipt is
`results/fx2_cmix21_lstm112_native_10m_v1/receipt.json`.

Receipts:

- `results/fx2_cmix21_geometry_nopaq_lstm96x2_constructive_v1/receipt.json`
- `results/fx2_cmix21_geometry_nopaq_lstm96x2_constructive_v1/geometry_title_10m_screen.json`
- `results/fx2_cmix21_geometry_nopaq_lstm96x2_constructive_v1/offset500m_fx2_control.json`
- `results/fx2_cmix21_geometry_nopaq_lstm96x2_constructive_v1/offset500m_candidate.json`
- `/home/x/enwiki9-nonproof/results/fx2_cmix21_geometry_nopaq_constructive_v1/receipt.json`

## Mechanism learned

Removing PAQ improved both bytes and execution, so PAQ is redundant on this
FX2/WRT substrate. The two-layer online byte LSTM supplies most of the remaining
gain: one-layer and no-byte-mixer variants lose too much. Width is non-monotonic
at `250K`, but the exact `200x2` result gains another `213` bytes over `96x2` by
the first `1M`. The cost is dense recurrent execution, not memory or payload.

Post-warmup BPTT is not dispensable. Updating every eighth horizon after the
first `1,000` full updates still saved `876 B/1M` at `250K`, but collapsed to
`432 B/1M` at the first `1M`. The late online recurrent updates carry real
compression information; this exact sparse-training schedule is retired, and
no decode or larger gate is justified from it.

The first phase-aligned factorization is positive but narrow. A full-rate `112x2` LSTM
receives the original dense byte-model input. Two independent `44x2` LSTMs
receive alternating byte parities with no dense auxiliary input; each phase
predicts the next byte in its own subsequence, and the existing mixers adapt to
the full-rate and phase-selected probabilities. Encoder and decoder execute the
same freeze/update schedule. The candidate saves `908 B/1M` at `250K` and
`1,019 B/1M` at the first `1M`. Its counted source build matches the discovery
archive, two clean builds are identical, and exact decode restores the input.
Plain portable `112x2` saves `1,010 B/1M`, so the phase endpoint contributes
only `9 B/1M`; after source cost its projected increment is `8,087` bytes. The
portable encode is `1.859x` the matched local FX2 encode, which fails the local
execution screen. Native equivalence and larger-scope slope are unknown.

The declining gain rate shows that a fixed LSTM endpoint spends work broadly
while its independent information is concentrated. A selector cannot create
missing probability information, so the next lane must first prove a stronger
expert universe.

## Matched endpoint experiment

The requested archive-neutral matched experiment is complete. The trace
preserved the exact `174,268`-byte `96x2` archive while exposing its pre/post
SSE probabilities, active byte endpoint, 26 individual layer-0 outputs, and
continuously evolved 160/200-cell probes. A separately continuous full-CMIX21
endpoint was then aligned to the same `4,805,936` geometry-WRT truth rows.

The best exact fixed blend saved `290 B/1M` overall and `355 B/1M` on the
internal holdout, with zero holdout block regressions and exact range-decoder
replay. A separate train-only three-coefficient affine-logit fit retained
`351.665 B/1M` on holdout; base calibration alone retained only
`11.589 B/1M`. Both fail the `500 B/1M` native-integration screen. Existing
individual endpoints save only `50 B/1M` overall; multivariate and bit-position
controls also remain below the screen. See
`docs/cmix21_fx2_family_trace_correction.md` and the quarantined receipt
`/home/x/enwiki9-nonproof/results/cmix21_full_teacher_geometry_1m_v1/matched_screen_receipt.json`.

The smaller reproducible `96x2` package lowered the forecast debt enough to
authorize one frozen disjoint confirmation. On the offset-`500M` same-store
slice, the opening-selected `625000`-ppm blend saved only `61 B/1M` overall
and `85 B/1M` on proportional holdout. Base archive and probability payload
identity, both memory guards, zero holdout block regressions, and exact
range-decoder replay pass. The result misses the revised `252.737 B/1M` debt
by `191.737 B/1M` before any integration code or state. This retires the fixed
blend and selector work over that endpoint pair. Canonical receipt:
`results/fx2_cmix21_matched_disjoint_terminal_v1/receipt.json`.

## Next experiment

Selector and recurrent-width work over the measured geometry endpoint universe
are terminal. The queued decoder-rebuilt WRT phrase-copy endpoint has also been
executed: all `432` active development configurations lose bytes after explicit
activation/rank/distance/length coding, so its frozen holdout action is
abstention. That exact action universe is retired.

The remaining full-teacher signal was then tested as an alternative
original-order construction. Against the archive-identical exact FX2 stream,
the compact `96` fixed blend saves `1,201 B/1M` overall and `1,105 B/1M` on
internal holdout. Compact `200` improves those values to `1,345` and
`1,325 B/1M`, with zero holdout regressions and exact decoder replay. Directly
adding `200` to compact `96` retains only `298 B/1M` overall, so the mechanism
is the FX2/compact contrast, not another recurrent endpoint. Freeze the
`750000`-ppm FX2/compact-`200` blend for cumulative `10M`, charge the exact
`506.4 B/1M` original-order penalty, and advance only if one native process can
close source, state, RSS, runtime, roundtrip, and determinism.

The staged `96x2` ensemble source has now been audited directly. Its
`Predictor::AddMixers` constructs exactly two continuously updated `96`-cell,
two-layer LSTMs from one deterministic random stream, so their initial weights
differ reproducibly. Both endpoints receive every causal byte-model vector and
enter the existing mixer; endpoint zero alone supplies the FXCM feedback value.
This closes the selective-state-continuity concern for that implementation.
The staged source ZIP still embeds the geometry-only Python transform, however,
while target-bearing archive screens use the geometry-title transform. Treat
the ZIP as a backend-discovery artifact only. A paying backend must be rebuilt
with the exact geometry-title key and must reproduce the precomputed stream and
archive before it becomes constructive package evidence.

The first ensemble comparison should include a heterogeneous `112+80`
construction. It preserves the strongest measured primary endpoint and its
FXCM feedback path while adding an independently initialized smaller endpoint
to the downstream mixer. Its recurrent matrix work is comparable to two
`96`-cell endpoints, but it does not discard the measured `112x2` trajectory.
Screen `112+80` and `96+96` on the identical input, build flags, seed stream,
and package accounting. Advance only the smaller paying set; do not add a
router unless the direct online mixer first shows target-rate margin.

The comparison is now terminal. Symmetric `96+96` loses to native `112x2` and
is retired. Heterogeneous `112+80` wins by `4` bytes at `250K` and `71` bytes
at the first `1M`, while remaining continuously replayable. Its corrected
geometry-title source ZIP is `301,162` bytes. The transform reproduces the
exact cumulative-`10M` geometry-title stream and reverses to the original
prefix; a clean source build reproduces the discovery backend binary exactly.
Its cumulative-`10M` archive is now terminal at `1,635,670` bytes. That misses
the deflate-ZIP ceiling by `37` bytes but clears the clean-built direct-source
bzip2-ZIP ceiling of `1,635,762` by `92` bytes. The selected linear forecast is
`109,490,775`, only `9,225` bytes below target. Exact source-wrapper archive
identity, roundtrip, and deterministic replay pass. Two independent framed
archives are byte-identical at `1,635,671`, and the restored `10M` SHA-256 is
`5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97`.
No larger gate is authorized by this narrow forecast alone.

Dictionary/package compression is secondary but now exact for the active
construction. A standard bzip2-method ZIP with two direct entries, `Makefile`
and readable `source_bundle.sh`, is `264,646` bytes. The bundle reconstructs
all `77` counted source files verbatim; two independent clean builds reproduce
the exact backend and wrapper hashes already covered by the `10M` proof. It is
`23,619` bytes smaller than the former selected package and is now the accepted
counted representation for any bit-identical descendant. A deterministic tar.xz
is smaller at `247,404` bytes, but the official
relaxation explicitly names ZIP source packages ([detailed rules](https://prize.hutter1.net/hrules.htm)), so tar.xz requires committee
acceptance before it can affect score accounting. Packaging cannot substitute
for a failed codec or unaccepted accounting path.

Execution eligibility also fails the promotion direction. The exact `112+80`
backend took `3,076.1042 s` on cumulative `10M`, versus `2,183.2284 s` for
native `112x2`, a `1.409x` ratio on this host. The source wrapper proof seals
correctness and identity, not the official Geekbench-scaled runtime rule.
The matched later-region control removes the reason to optimize smaller widths:
native `112x2` archives to `45,263`, while `112+80` reaches only `45,259`, an
increment of `4 B/1M`. The next endpoint must add new WRT-native information,
not approximate this weak secondary more cheaply.

The cumulative `795.6 B/1M` average also includes a strong first-`1M` warmup
region and is not the only credible scaling model. From `1M` to `10M`, gross
gain grows from `1,084` to `7,956` bytes, a tail slope of
`763.555556 B/1M`. Extending that measured tail gives `763,876` projected gross
bytes at `1G`. The former source package projected `109,522,498`; replacing it
with the accepted `264,646`-byte package reduces that same forecast by `23,619`
bytes to `109,498,879`, a forecast margin of `1,121` bytes. This does not
invalidate the matched reset-slice failure or authorize promotion. The codec
still needs new disjoint information and execution headroom before any larger
gate.

The first WRT-native representation probe is also terminal. A deterministic
swap of low-frequency two-byte dictionary slots with high-frequency three-byte
words saved `546` bytes under the gzip proxy, but the exact `112+80` archive
grew by `1,140` bytes at cumulative `10M`. That dictionary shape is retired.
Its smaller package was an accounting confound and is kept separate from the
negative archive effect. See
`results/wrt_static_boundary_swap_112plus80_terminal_v1/receipt.json`.

## Claim boundary

No `10.95%` claim is made. The strongest constructive recurrent evidence is a
passed exact source-wrapper replay at cumulative `10M`; the matched later-region
control retires it from promotion. The combined decision is
`results/fx2_cmix21_lstm112_plus80_terminal_v1/receipt.json`. The dual-rate
receipt remains quarantined at `/home/x/enwiki9-nonproof/results/fx2_cmix21_dual_rate_constructive_v1/receipt.json`.
A target claim still requires a counted `1G` archive at or below `109,500,000`
with exact roundtrip.
