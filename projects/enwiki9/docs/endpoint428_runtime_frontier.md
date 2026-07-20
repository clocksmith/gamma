# Endpoint428 runtime frontier

## Boundary

The frozen counted candidate remains the endpoint428 compact/FX2 pair, 26
layer-0 endpoints, fused recurrent-gate traversal, explicit output update, and
online residual mixer. Its exact `10M` archive is `1,634,500` bytes. Removing
comments from the counted `102`-file source tree reduces the deterministic LZMA
package from `280,147` to `261,125` bytes while two clean builds retain the
frozen backend and wrapper hashes. The revised counted forecast is therefore
`109,389,323` bytes (`10.9389323%`), `110,677` bytes below the `109,500,000`
target. No official full-`1G` score exists.

Runtime successors are screened on the same `250K` transformed prefix in
alternating reference/candidate/candidate/reference order with CPUs `0-3` and
the decimal-`10GB` guard. A changed-stream candidate uses the Pareto evaluator:
same-role archives must be deterministic, its calibrated counted projection
must remain at or below target, and its matched median runtime reduction must
be at least `10%` before a larger gate is authorized.

The calibrated prefix projection is research evidence. It is not an official
score and does not establish transfer beyond the measured prefix.

The dual-`112` BF16 numeric screen is score-safe on the opening `250K` prefix.
Rounding both recurrent endpoints' weights after initialization and every Adam
update produces a `44,955`-byte archive, three bytes better than the
`44,958`-byte parent. Exact decode and independent re-encode pass. Converting
the dense recurrent input to BF16 and using AVX-512 BF16 dot products produces
`44,957` bytes and reduces one encode from `134.32 s` to `122.41 s` (`8.87%`).
Peak tree RSS remains below decimal `10GB`. This is not an alternating matched
runtime result and it misses the `10%` promotion threshold, so it receives no
forecast or score credit. The only authorized successor packs each input once
and maintains BF16 weight shadows; it must preserve the hardware stream and
clear the same score and runtime gates.

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
| Dual `112`, atomic handoff plus serial fused forward | `44,958` | `0` | `61.6707 s` | `66.0642 s` | `-7.12%` | `109,448,323` | `51,677` | Archive-exact; retired for runtime regression |
| Dual `112`, sidecar tail `memmove` and reverse suffix compare | `44,958` | `0` | `54.9064 s` | `55.4065 s` | `-0.91%` | `109,448,323` | `51,677` | Archive-exact; retired for runtime regression |
| Atomic endpoint handoff | `44,958` | `0` | `119.2097 s` | `105.1546 s` | `11.79%` | unchanged | `91,655` | Retired after reduction decayed to `5.62%` at `1M` |
| Runtime composite at `1K` | `259` | same size, different hash | `21.56675 s` | `21.69125 s` | `-0.58%` | not projected | n/a | Retired before `250K`; dual-backward accumulator changes stream |
| Dual `112` BF16 weights, AVX-512 BF16 gate dots | `44,957` | `-1` | `134.32 s` scalar BF16 | `122.41 s` hardware BF16 | `8.87%` single-run | not projected | unknown | Score-safe primitive; matched runtime promotion withheld |

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

Dual `112` with half horizons was reopened only after two new facts changed its
economics: lexical package minification enlarged the score budget, and a
cold-reset offset-`500M` population reduced its loss from `59 B/1M` on the
opening prefix to `12 B/1M`. The conservative projection retains the worse
`59 B/1M` loss, giving `109,448,323` bytes (`10.9448323%`), `51,677` below
target. On the disjoint population it reduces elapsed encode time from
`255.0435 s` to `180.0267 s` (`29.4133%`) with clean roundtrip and decimal-RSS
guards. These are two exact cold-reset `1M` populations, not a full-corpus
score or an official runtime qualification.

Two archive-exact dual-`112` follow-ups are terminal at `250K`. Composing the
atomic endpoint handoff with serial fused forward traversal regresses matched
median runtime by `7.1240%`. Replacing the 32-byte sidecar tail shift with
`memmove` and comparing suffixes backward regresses it by `0.9108%`. Neither
can supply the missing absolute runtime reduction, so both stop before larger
gates.

The replacement-economics branch asks whether removing the whole FX2-lite428
endpoint can pay in source bytes and recovered compact-only residual signal.
The sealed same-execution trace attributes `272 B/1M` to FX2. A deterministic
minified compact-only LZMA package is `235,176` bytes, only `25,949` bytes
smaller than the `261,125`-byte pair package; deletion alone therefore projects
to `109,635,374`, `135,374` above target. Replaying the existing 26 layer-0
endpoints over compact alone recovers `103 B/1M` overall and `55 B/1M` on
proportional holdout. The resulting package-adjusted projection is
`109,532,374`, still `32,374` above target, so layer-0 alone is retired.

The frozen hierarchical WRT phase residual is the only promoted recovery
follow-up. Over compact plus layer-0 it saves another exact `36 B/1M`; all ten
blocks, development, and holdout are positive. With its conservative
`1,407`-byte source reserve, the opening-prefix projection is `109,497,781`
(`10.9497781%`), only `2,219` below target. The unchanged frozen form passes
its offset-`500M` confirmation: compact layer-0 saves `85 B/1M`, phase saves
another `49 B/1M` against its `34 B/1M` floor, and the combined `45,045`-byte
payload is `58` bytes better than the original compact/FX2 pair payload on that
population.

The first native integration composes exactly at `1K`, `250K`, and `1M`, but
its `238,406`-byte source package leaves the exact `174,099`-byte `1M` archive
three bytes above the authorized archive ceiling. It is terminal without a
decode. Removing only inactive trace paths, unused LSTM serialization, an
inactive crash handler, and non-build package entries produces two identical
`235,420`-byte LZMA packages. Two reconstructed clean builds are byte-identical.
The reconstructed candidate reproduces the `254`-byte `1K`, `44,979`-byte
`250K`, and `174,099`-byte `1M` archives. The `1M` decode roundtrips exactly,
the deterministic re-encode is byte-identical, and all decimal-memory guards
pass with peak process-tree RSS `7,578,364 KiB`.

After the measured `25,705`-byte package saving versus the frozen pair, the
native replacement projects to `109,499,618` bytes (`10.9499618%`), only `382`
below target. This is the score-qualified replacement frontier, not an
official full-`1G` score. Its measured `1M` encode remains runtime-unqualified,
so the exact implementation stops before `1G`. The next runtime branch must
change the recurrent representation or supply model-level concurrency while
retaining counted score; source-only micro-optimizations cannot close the
throughput gap.

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

That candidate is terminal. Its `1K` archive and probability trace are exact,
but on the first matched `250K` candidate run it reaches only `73.10%` after
`152.59 s`, already beyond the `105.0611 s` ceiling derived from the completed
`116.7345 s` atomic-endpoint reference. The adaptive atomic/futex dispatch does
not convert the profiled barrier cost into wall-time savings; all remaining
runs and every larger gate were stopped.

The dual-`80` score-rescue branch is also closed. The retained `250000 ppm` WRT
phase residual produces `44,952` bytes at `250K`. Doubling phase strength to
`500000 ppm` produces `44,968`; changing the already-counted outer mixer to the
pre-existing faster local-adaptation regime (`global24/local20`, warmup `128`,
regret decay `12`) produces `44,991`. Both miss the precommitted `44,947` ceiling,
so no further strength/rate ladder or `1M` run is authorized.

Freezing both recurrent BPTT bodies after their first `1,000` horizon updates
is terminal at the matched `250K` gate. The candidate archive is `44,986`, `28`
bytes worse than the `44,958` reference. After the already-measured `1,407`-byte
source reserve, its calibrated counted projection is `109,483,335` bytes
(`10.9483335%`), leaving only `16,665` bytes of target margin. Runtime falls
from `85.7544 s` to `81.7419 s`, a `4.679%` reduction, below the precommitted
`30%` gate. Even the impossible upper bound of eliminating the measured BPTT
region from the beginning cannot supply the official runtime reduction, so the
remaining matched runs, decode, and every larger gate were stopped.

The exact-source runtime composite is terminal before `250K`. Atomic endpoint
handoff, a flat `32K` mixer table, serial fused forward traversal, and fused
dual backward accumulators are deterministic at `1K`, but the candidate's
`259`-byte archive hash differs from the frozen hash. Removing only the dual
backward accumulator restores exact SHA-256
`245b647b159599882620e473c5694e305aa0b2fd390a28a19cae72b04fdd72d4`,
isolating compiler reassociation in that accumulator as the stream change.
The full composite is also `0.577%` slower in the matched startup-dominated
screen. The surviving exact components have an optimistic additive measured
reduction of only `13.963%`, versus `83.093%` required to turn the measured
`88.7147 h` projection into the published four-core `14.9989 h` cap. This
numeric bound forbids the `250K` timing gate.

A profiling-only rebuild of the pruned compact-replacement source confirms
that the architectural boundary is recurrent work rather than an unprofiled
outer hot spot. On the existing `250K` population, `gprof` accounts for
`169.47` aggregate sampled CPU seconds. LSTM OpenMP worker bodies, Adam, and
OpenMP synchronization account for `143.49` seconds (`84.67%`); barrier waits
alone account for `94.80` seconds (`55.94%`). Address inspection maps the two
mislabelled local-symbol buckets to the LSTM forward and predict/perceive
OpenMP workers, and the LSTM sources contain every OpenMP pragma in the codec.
The profiling build changes the archive and receives no score credit. The
concentration supports modeled-work removal, but does not reopen the retired
serial, persistent-region, worker-count, or BPTT schedule ladders.

Independent page sharding is terminal. A deterministic splitter chooses four
decoder-visible `<page>` boundaries at offsets `222,281`, `495,350`, and
`742,779` in the opening `1M`. The four independent dual-`112` archives total
`185,480` bytes; a reversible fixed-width directory adds `44`, producing an
exact `185,524`-byte container. Every shard roundtrips, but the container is
`11,563` bytes larger than the `173,961`-byte unsharded archive.

The reset cost fits the parent's diagnostic `51,677`-byte score margin, but
the concurrency dependency does not fit memory. Four unmodified processes
cross the decimal-`10GB` tree guard during initialization at `9,841,944 KiB`.
Quartering the shared and FXCM compound tables retains a favorable `+6` bytes
on the `222,281`-byte first shard, yet four-process initialization still
reaches `10,293,400 KiB`. Reducing shared, match, direct-hash, and compound
tables to one-sixteenth misses the four-way per-shard ceiling even at `1K`.
It fits the three-way per-shard ceiling at `222,281` bytes, but loses `15`
archive bytes (`67.482 B/1M`), above the parent's `51.677 B/1M` score budget.
The diagnostic projection is `109,515,805` bytes, `15,805` above target before
any full-corpus shard-directory or reset uncertainty. No concurrency timing or
larger gate is authorized for independent page sharding.

The counted package lane is independently positive. Lexical comment stripping
removes `109,041` source bytes without changing tokens or line counts. Two
bundles and two direct-entry LZMA ZIPs are identical; the `261,125`-byte ZIP
has SHA-256 `b6fe6b09...`, and both clean builds reproduce backend SHA-256
`d1066630...` and wrapper SHA-256 `37ee8cd7...`. The `19,022` counted bytes are
accepted in the forecast, but do not authorize a full-`1G` run while runtime is
unqualified.
