# Endpoint428 runtime frontier

## Boundary

The frozen counted candidate remains the endpoint428 compact/FX2 pair, 26
layer-0 endpoints, fused recurrent-gate traversal, explicit output update, and
online residual mixer. Its exact `10M` archive is `1,634,500` bytes and its
counted forecast is `109,408,345` bytes (`10.9408345%`), `91,655` bytes below
the `109,500,000` target. No official full-`1G` score exists.

Runtime successors are screened on the same `250K` transformed prefix in
alternating reference/candidate/candidate/reference order with CPUs `0-3` and
the decimal-`10GB` guard. A changed-stream candidate uses the Pareto evaluator:
same-role archives must be deterministic, its calibrated counted projection
must remain at or below target, and its matched median runtime reduction must
be at least `10%` before a larger gate is authorized.

The calibrated prefix projection is research evidence. It is not an official
score and does not establish transfer beyond the measured prefix.

## Terminal screens

| Candidate | Candidate archive | Archive delta | Reference median | Candidate median | Runtime reduction | Provisional counted forecast | Target margin | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Mixer last-key cache | `44,958` | `0` | `127.0401 s` | `125.8935 s` | `0.90%` | unchanged | `91,655` | Preserve component result; insufficient runtime movement |
| Flat mixer context table | `44,958` | `0` | `77.2373 s` | `77.9896 s` | `-0.97%` | unchanged | `91,655` | Retired |
| Half horizons (`100/128 -> 50/64`) | `44,931` | `-27` | `75.0937 s` | `78.3503 s` | `-4.34%` | `109,336,034` | `163,966` | Score-positive component; not a runtime successor |
| Compact `112`, endpoint `200` | `44,979` | `+21` | `74.7278 s` | `70.2020 s` | `6.06%` | `109,464,588` | `35,412` | Runtime/score tradeoff; threshold missed |
| Compact `96`, endpoint `200` | `44,980` | `+22` | `74.2279 s` | `68.7119 s` | `7.43%` | `109,467,266` | `32,734` | Runtime/score tradeoff; threshold missed |
| Compact `112`, endpoint `112` | `44,982` | `+24` | `73.7184 s` | `54.9143 s` | `25.51%` | `109,472,623` | `27,377` | Pareto prefix pass |
| Compact `96`, endpoint `96` | `44,981` | `+23` | `74.0967 s` | `52.5286 s` | `29.11%` | `109,469,944` | `30,056` | Pareto prefix pass |
| Dual `112`, half horizons | `44,958` | `0` | `73.6100 s` | `53.6551 s` | `27.11%` | `109,408,345` | `91,655` | Pareto prefix pass |
| Dual `96`, half horizons | `44,949` | `-9` | `73.9870 s` | `50.6564 s` | `31.53%` | `109,384,242` | `115,758` | Pareto prefix pass; score fallback |
| Dual `80`, half horizons | `44,967` | `+9` | `74.8597 s` | `48.2715 s` | `35.52%` | `109,432,449` | `67,551` | Pareto prefix pass; failed transfer at `1M` |
| Atomic endpoint handoff | `44,958` | `0` | `119.2097 s` | `105.1546 s` | `11.79%` | unchanged | `91,655` | Retired after reduction decayed to `5.62%` at `1M` |

All listed runs have deterministic same-role archives and clean decimal-memory
guards. Identity candidates additionally reproduce the reference archive.

The aborted clean-PGO instrumentation reached only a partial training pass and
has no archive, score, or runtime credit. It was stopped because it occupied
the heavy lane ahead of the higher-leverage recurrent-width tests.

## Active decision sequence

The bounded half-horizon ladder is closed at its predeclared `80`-cell floor.
Changing compact width changes global random-number consumption and therefore
the endpoint initialization, so these rows are legal co-adapted candidates;
they do not isolate recurrent width as the sole cause of archive movement.
Do not continue to smaller widths from the same opening-prefix evidence.

Dual `80` with half horizons advanced first because it had the strongest
terminal runtime reduction while retaining calibrated target margin. Its
deterministic `1M` archive is `174,087` bytes against the `173,902`-byte
reference. The resulting `109,532,213`-byte projection is `32,213` above target,
so it is a terminal runtime-positive, score-negative result despite a `44.66%`
matched runtime reduction and clean guards.

Dual `96` with half horizons is the predeclared score fallback because it has
the strongest `250K` projection. It passes matched `1M` confirmation with a
deterministic `174,037`-byte archive against the `173,902`-byte reference. The
calibrated projection is `109,498,735` bytes, only `1,265` below target, while
the matched median falls from `234.0037 s` to `141.9240 s`, a `39.35%`
reduction. All four decimal-memory guards pass.

The exact `10M` changed-stream encode is terminal and rejects dual `96`. Its
`1,641,775`-byte archive is `7,275` bytes worse than the frozen
`1,634,500`-byte archive. Before any package delta, that projects to
`109,895,446` bytes (`10.9895446%`), `395,446` above target. The guard passes
with peak tree RSS `9,022,568` KiB, but the stream economics forbid decode,
deterministic re-encode, package promotion, and a full-`1G` gate.

Dual `112` with half horizons is terminal at `1M`. Its `173,961`-byte archive
is `59` bytes worse than the `173,902`-byte reference, and its `263.516 s`
single encode is slower than the prior matched reference median. The guard is
clean, but it misses the precommitted no-regression condition, so no duplicate
or exact `10M` gate is authorized.

The dual-`80` mixer/adapter/phase composition is terminal. At `250K`, the full
composition produces `44,997` bytes and the pair-only form produces `45,015`,
respectively `30` and `48` bytes worse than the `44,967`-byte dual-`80`
reference. The phase-only form saves `15` bytes at `250K` and clears its
predeclared `13`-byte floor, but its exact `1M` archive is `174,054`, `152`
bytes worse than the frozen `173,902`-byte reference. After the measured
`1,407`-byte source reserve its calibrated forecast is `109,511,525`, `11,525`
bytes above target. Even with zero source cost it misses the `174,036`-byte
kill ceiling by `18` bytes, so duplicate replay, tuning, and `10M` promotion
are forbidden.

The atomic-handoff successor preserves the frozen `1,634,500`-byte stream and replaces
the per-bit endpoint428 mutex/condition-variable handoff with an acquire/release
atomic handoff. Its `1K` archive (`259` bytes) and full probability trace are
byte-identical to the frozen implementation. Its completed alternating `250K`
screen produces one `44,958`-byte archive across all four runs. Reference median
is `119.2097 s`; candidate median is `105.1546 s`, an `11.7902%` reduction. All
decimal-memory guards are clean with peak RSS below `8,988,976` KiB. A discarded
partial screen is non-evidence: its early-stop extrapolation mixed fixed
pretraining with compression progress and was invalidated before any terminal
claim. At `1M`, the first terminal reference/candidate pair produces identical
`173,902`-byte archives and clean guards, but elapsed time falls only from
`327.4435 s` to `309.0450 s`, a `5.6188%` reduction. That is below the
precommitted `10%` transfer threshold, so the remaining duplicate/reference
runs were terminated and no `10M` gate is authorized.

The next fresh runtime candidate targets the profiled `49%` OpenMP barrier cost
by replacing mutex/condition-variable persistent LSTM worker dispatch with a
bounded atomic worker protocol, composed with the exact atomic endpoint
handoff. It must first reproduce the frozen probability trace and archive, then
show at least `10%` incremental matched `250K` runtime reduction over the atomic
endpoint implementation. Anything less is terminal before `1M`.
