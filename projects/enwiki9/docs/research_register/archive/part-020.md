# Research Register Archive 020

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-09-03 - HARM-Delta is frozen as a distinct causal edit-residual mechanism

Broad HARM is rejected as a replacement codec. The retained mechanism is
`harm_route_edit_residual_shadow_q0_v1`: a bounded auxiliary predictor over the
most recent fully completed value of the exact decoder-visible template-name
plus explicit-field-key route. It operates in Endpoint428 WRT-byte space and
never reorders pages, emits copy commands, transmits a route or source address,
installs an offline dictionary, changes Endpoint428 state, or selects an edit
path after seeing the completed current value.

V1 fixes one implementation rather than a parameter family: a 4,096-slot
direct-mapped value bank with exact route-and-witness tag checks, a 512-byte
value cap, offsets from -8 through +8, match/substitute/insert/delete states,
integer forward mass normalized to `2^30`, and one global sleeping Q63 mixture
for each of L/E/G/S/R; N shares E's pretruth weight and owns no state. Candidate byte masses are converted to MSB-first conditional integer
probabilities using only the already decoded prefix of the current byte. The
current value becomes a future donor only after its field exit and all delayed
semantic commits. Overflowing values sleep and are not installed.

The frozen arms are `P/K/L/E/G/S/R/N`. `L` is exact same-route lockstep without
edit tolerance; `E` is the route-conditioned edit treatment; `G` applies the
same edit arithmetic to a physical HORIZON field-entry donor; `S` resolves the
immediately preceding completed route through E's same collision/tag geometry;
`R` uses a deterministic
truth-independent SplitMix64 route bucket; and `N` reflects E's exact pretruth
byte distribution through xor-255 without owning edit or calibration state.
P/K identity, E over L, E over G, and E over S/R/N are separate required
attributions. Fiber-CTS is neither an antecedent nor a promotion prerequisite:
short route-local context and alignment to a complete prior value are different
hypotheses. Because they share the semantic-route population and route-local
donor universe, this mechanism distinction is not evidence of statistical
independence, residual gain, or complementarity.

The restricted GSRT2 adapter applies delayed value commits, then structural
callbacks, then prediction. It does not expose event-3 `raw_after`, current raw
expansion, future field length, descriptor sidecar, or offline tape state to the
predictor. A source-only fixture repeats byte-identically, preserves exact P/K
probabilities, distinguishes inserted-byte and silent-donor-deletion paths from
lockstep, keeps sleeping mixtures exactly parent-neutral, rejects malformed or
missing deferred events and forged physical seeds, and changes state only after
the first differing truth in a twin-future causality check. The frozen known
answers are probability SHA-256
`8ba2a030e57ad0399b98a33cfe9a691517d4e975bb82638da79b5fb46824689d`
and terminal-state SHA-256
`2bfa5c120b9293d22c0b7ee76af125da055e362116433cc4ca4d8b4b7813c334`.
These are implementation checks only; they access no corpus and grant zero
archive or score authority.

The required corpus input is intentionally not fabricated. The current
`GHORA1` manifest contains a target coordinate and four donor bytes but no
historical source coordinate or bounded continuation, so it cannot drive G's
edit transducer. After the active HORIZON experiment terminalizes, a separately
frozen zero-authority observer must reconstruct and repeat a field-entry source
coordinate and donor continuation from decoded history. Opening-1M can reject
HARM-Delta but cannot establish E over G because the physical age floor is
100,000,000 WRT bytes. Promotion requires opening and distant state-warm scopes;
the distant sparse parent trace must cover every HARM-active coordinate through
the measured interval so route, alignment, and Q63 state are truly warm.

The current design uses the provisional Endpoint428 gross floor of
`40,163,160` bits only as a prospective shadow gate. It must be rebound if an
exact native parent package changes the debt. A miss retires the exact route
population, memory geometry, drift band, transition/emission law, and endpoint
without a sweep. HARM-conditioned MIDAS remains forbidden until HARM-Delta and
compact MIDAS independently produce paying native archives, followed by a new
joint replay.

The two v1 shadow scopes are now fixed in canonical raw coordinates before any
parent trace is read: opening `[0,1,000,000)` and distant
`[500,000,000,510,000,000)`. State is replayed from raw byte zero; only the
bound interval is measured. Chronological thirds use each prediction's
pretruth `raw_before` coordinate under the fixed floor formula, never WRT
length. Provisional density screens are respectively
`40,164` and `401,632` ideal mixture-gain bits. They grant no forecast or score
credit. E must also be positive in every third, exceed L/S/R/N in both scopes,
and exceed an admissible matched physical G in the distant scope. Route, edit,
drift, support, and positive-opportunity reports are diagnostics only.

G is fixed to the Endpoint428 HORIZON-A source law, not an arbitrary donor and
not the existing one-byte HORIZON endpoint: a `2^24` direct-mapped
oldest-surviving clock over exact preceding-16-byte contexts, polynomial base
`0x9e3779b185ebca87`, high-32-bit tag, exact historical verification, and age
strictly greater than `100,000,000` WRT bytes. At field entry it supplies its
already decoded continuation, bounded by the current coordinate, to the same
edit arithmetic as E. A repeated source-coordinate observer is mandatory;
without it the G comparison is inadmissible.

The source-only sparse boundary is now implemented and validly reflected as
`harm_delta_sparse_input_abi_q0_v1`. HSP1 stores one coordinate plus eight Q16
parent counts in a 24-byte record and advances monotonically with the GSRT2
replay; a missing callback row and an unused row are both fatal. HGS1 binds a
field-entry target, causal source, exact-context hash, and rolling anchor-state
witness in a 32-byte record. Both formats bind full headers, payload and
coordinate-set hashes, parent/observer state, and separately materialized A/B
identity. The manifest additionally binds raw, WRT, coder-bit, mapping, and
frontend/parent boundary state.

Its generated eight-byte gate consumed exactly six parent rows for six
predictive callbacks in both repeats, preserved P/K identity, woke E on all
three bytes of the second route occurrence, kept absent opening G
inadmissible, reconstructed one valid causal physical donor, and rejected all
ten prospectively frozen malformed-input controls. Maximum self RSS was
`24,796 KiB`. This proves only the input and replay boundary: it read no corpus
or active HORIZON scientific output, measured no HARM gain, and grants zero
archive, native-integration, or objective credit. It is held until terminal
HORIZON routing and the repeated corpus-bound GSRT2/HSP1/HGS1 inputs exist.

The next conversion boundary is also source-valid and held as
`harm_delta_sparse_parent_materializer_q0_v1`. It fixes the otherwise implicit
coordinate law: a predictive GSRT2 event-3 byte at WRT coordinate `c` copies
the eight little-endian CMX21P1 counts at offset `16 + 16*c`, in unchanged
MSB-first coder-bit order. Its generated nine-byte gate selected exactly four
predictive coordinates and 32 counts, emitted byte-identical A/B HSP1 files,
passed the already measured HSP1 parser, and reproduced independently computed
boundary witnesses over the complete truth/probability transcript. All ten
frozen trace, route, population, probability, identity, and witness corruptions
failed before output installation; maximum self RSS was `22,992 KiB`.

The boundary witness is deliberately described as observational trajectory
evidence, not opaque Endpoint428 state serialization. Native P/K still needs
complete future-affecting state hashes. This fixture opened neither corpus nor
the active HORIZON result namespace and grants zero scientific or score credit.
Production materialization remains a separately frozen successor gated by the
terminal HORIZON router, repeated corpus GSRT2, exact raw/WRT/coder mapping,
and distant HGS1 evidence.

The physical-comparator source boundary is now also source-valid and held as
`harm_delta_horizon_field_entry_observer_q0_v1`. Its native observer replays
the exact frozen HORIZON-A oldest-anchor state but performs lookups only at
causal GSRT2 explicit-field-entry coordinates. In the generated 128-byte gate,
native A/B emitted the same two target/source/context/transition rows as an
independent Python state machine, selected no non-entry callback, and matched
terminal rolling, anchor-table, and anchor-transition witnesses. The rows also
passed the already measured HGS1 parser and reconstructed the expected causal
donors through HARM's frozen G adapter.

All eight frozen path, header, event-count, callback-order, population,
pretruth, timing, and route-identity corruptions failed closed. Maximum self
RSS was `96,088 KiB`; corpus and active-HORIZON access counts were both zero.
This establishes causality, arithmetic/source-law identity, repeatability, and
container compatibility only. It measures no parent-relative gain and grants
no archive, native-integration, corpus-execution, or objective authority. A
production A/B successor remains forbidden until the terminal HORIZON router
and repeated full-WRT GSRT2 inputs are bound, and it must reproduce all three
frozen source-census terminal witnesses before emitting admissible HGS1.

The final source-only coordinate boundary is valid and held as
`harm_delta_scope_coordinate_mapper_q0_v1`. It defines `map(r)` as the first
WRT coordinate whose pretruth raw frontier is at least raw boundary `r`, then
maps raw `[a,b)` to WRT `[map(a),map(b))` and MSB-first coder bits
`[8*map(a),8*map(b))`. A complete little-endian coordinate/raw-span
transcript is represented by one SHA-256 digest, while each requested boundary
also binds every future-affecting inverse state in a domain-separated digest.
This removes the remaining ambiguity when a canonical raw boundary falls
inside a multi-byte dictionary expansion without emitting a corpus-scale
ledger.

The generated 38-raw-byte, 32-WRT-byte fixture mapped the seven frozen raw
boundaries to WRT coordinates `0, 9, 12, 16, 19, 24, 32`. Two native processes
were byte-identical and matched an independent Python inverse at every
boundary, input identity, transcript digest, frontend-state digest, and
derived scope/coder bound. The constant-only production descriptor closed,
all eight symlink, wrapper, raw-truth, length-header, terminal-code, and
dictionary-count corruptions failed before output, and maximum self RSS was
`132,116 KiB`. Corpus and active-HORIZON access counts were zero. This is a
causality/arithmetic/representation/repeat proof for the source boundary only;
it measures no gain and grants no production, archive, native-integration, or
objective authority. A separately frozen production A/B successor still waits
for terminal HORIZON routing and must reconcile its terminal witnesses against
repeated GSRT2 before supplying HARM's opening and distant bounds.

Evidence: `operations/planning/harm_route_edit_residual_shadow_q0_v1.json`,
`programs/harm_route_edit_residual_shadow_q0_v1/`, and
`tests/test_harm_route_edit_residual_shadow.py`; sparse-boundary evidence:
`operations/planning/harm_delta_sparse_input_abi_q0_v1.json`,
`operations/adaptive/experiments/harm_delta_sparse_input_abi_q0_v1.json`,
`results/harm_delta_sparse_input_abi_q0_v1/decision.json`, and
`operations/adaptive/reflections/20260904T161256Z_2483c5c0e6.json`;
materializer evidence:
`operations/planning/harm_delta_sparse_parent_materializer_q0_v1.json`,
`operations/adaptive/experiments/harm_delta_sparse_parent_materializer_q0_v1.json`,
`results/harm_delta_sparse_parent_materializer_q0_v1/decision.json`, and
`operations/adaptive/reflections/20260904T163548Z_e7983e7de3.json`;
physical-observer evidence:
`operations/planning/harm_delta_horizon_field_entry_observer_q0_v1.json`,
`operations/adaptive/experiments/harm_delta_horizon_field_entry_observer_q0_v1.json`,
`results/harm_delta_horizon_field_entry_observer_q0_v1/decision.json`, and
`operations/adaptive/reflections/20260904T165807Z_e8c7faaa7d.json`;
coordinate-mapper evidence:
`operations/planning/harm_delta_scope_coordinate_mapper_q0_v1.json`,
`operations/adaptive/experiments/harm_delta_scope_coordinate_mapper_q0_v1.json`,
`results/harm_delta_scope_coordinate_mapper_q0_v1/decision.json`, and
`operations/adaptive/reflections/20260904T172918Z_909f4801d8.json`.

## 2026-09-01 - HORIZON terminal routing is made fail-closed before observation

The active `endpoint428_horizon_retained_parent_trace_q0_v1` job remains
nonterminal and scientifically unread. A new terminal router now binds its
exact job ID, `647,798,592`-symbol gate, candidate tree, revision, proposal,
experiment, and runner. While that exact job is pending or running, the router
returns before opening the result namespace. Unrelated legacy queue records do
not control this candidate-specific decision.

Static inspection found that the frozen experiment declares seven result
artifacts while its successful runner necessarily creates sixteen additional
build, scan, guard, and log artifacts. The live experiment and runner remain
immutable. At terminal, the router streams hashes over declared opaque outputs,
parses only the hash-bound decision, independently recomputes every frozen
predicate, and classifies the known extra-output condition as
`CORRECTION_RETRY_ONLY`. It cannot promote a positive result directly through
that bookkeeping defect, retire an algorithm after an identity failure, or
reinterpret a failed/cancelled run as scientific evidence.

The correction route authorizes only a separate zero-credit output-closure
successor over the immutable result directory. It does not authorize deleting
logs, changing probabilities, rerunning CMIX, changing thresholds, starting the
exact reprice, or launching a native codec. Positive and negative scientific
outcomes must both survive unchanged through the closure correction.

That dormant successor is now implemented as
`endpoint428_horizon_retained_parent_trace_output_closure_q0_v2`. It requires
the exact hash-bound terminal-router correction receipt, replays the pinned
router, binds the exact 23-file v1 namespace, preserves `decision.json`
byte-for-byte, recomputes the underlying positive or negative scientific
branch, and publishes only the preserved decision plus a self-validating
receipt into a clean successor root. Its receipt schema is registered for
validation, but the successor remains unregistered as an adaptive candidate
and unexecuted while v1 is live.

The router uses no-follow directory traversal, bounded semantic JSON reads,
incremental hashes for the multi-gigabyte trace, stable-file checks, and a
durable no-clobber terminal receipt. Its receipt schema is registered with the
canonical research-contract validator, which can independently rehash every
terminal binding and output. Synthetic coverage exercises nonterminal access,
all terminal states, identity drift, reflection contradictions, nonfinite
measurements, missing and extra outputs, symlink rejection, receipt durability,
and canonical revalidation. This is governance and evidence-preservation work;
it adds zero archive authority and zero score credit.

Evidence: `tools/endpoint428_horizon_terminal_route_v1.py`,
`contracts/research/v1/endpoint428-horizon-terminal-route.schema.json`,
`tests/test_endpoint428_horizon_terminal_route_v1.py`, and
`tools/research_contracts.py`; plus
`tools/endpoint428_horizon_retained_parent_trace_output_closure_q0_v2.py`,
`contracts/research/v1/endpoint428-horizon-output-closure-receipt-v1.schema.json`,
and `tests/test_endpoint428_horizon_output_closure_q0_v2.py`.

## 2026-09-01 - Eligibility-first audit selects the original CMIX PPM runtime override

A repository-wide evidence audit changes the execution priority without
changing the canonical `105,000,000`-byte Gamma objective. The prior strategy
correctly retired q1 as a prize-facing parent, but it overgeneralized q1's
failure to the whole `cmix-obias` memory lineage. q1 file-backed the hot FXCM
tables and reproduced the `107,730,531`-byte payload at the cost of a
`300,711.6978`-second encode and incomplete decode. That result does not test
the original binary's already implemented `CMIX_PPM_RSS_MB` residency control.

Source audit found a simpler first candidate than the patched q0 binary. The
exact original source-built binary reads `CMIX_PPM_RSS_MB` once and uses it as
the total-RSS trigger for `MADV_DONTNEED` on the already file-backed PPM heap.
Setting it to `8192` during both encode and decode selects the same threshold
without changing the codec binary. Conservatively counting the complete
required encode and decode command text adds `100` bytes, giving a provisional
`108,513,807` complete count and `1,171,389` bytes below the current strict
one-percent ceiling if the known archive remains identical. This is planning
arithmetic, not a new measured package.

The patched q0 correction changes output-neutral residency control: it lowers the
existing file-backed PPM purge trigger from `9216` to `8192` MiB, calls
`malloc_trim` before Predictor construction, and adds optional phase markers.
It leaves FXCM resident and preserves the predictor, update order, transform,
and coder. Two clean builds already produced byte-identical `468,777`-byte
compressors and the same `23,002`-byte head. No q0 compression run exists, so
its probability identity, payload, inverse, memory, runtime, and package remain
unproved. Because it combines three implementation changes and grows the
compressor from `468,481` to `468,777` bytes, it is now conditional: use it only
if the env-only run fails before Predictor construction and the retained phase
evidence supports allocator residue.

This is strategically important because the exact external source-built Arm A
already produced a `108,513,707`-byte complete count and exact full inverse.
Its diagnostic encode/decode durations were `65,024.79` and
`66,377.101263917` seconds. Arm B repeated the payload and archive but stopped
during decode. The largest retained VmHWM lower bound is `10,472,880 KiB`,
`707,255 KiB` above the strict decimal limit. The current official page lists a
`110,793,128`-byte record and requires a strict one-percent score below
`109,685,197`, so the source-built count has a provisional `1,171,489`-byte
official-record margin before the q0 archive and program delta is measured.
This is volatile external context, not repository-owned rule authority.

The campaign now separates two claims. A memory-, runtime-, package-, and
roundtrip-qualified q0 derivative could be an external-derived official-record
candidate, subject to GPL compliance, attribution, author agreement, and the
official multiple-author prize-division rule. It would receive zero Gamma
objective credit. The canonical Gamma objective remains a Gamma-authored
complete score at or below `105,000,000`; against the current source-built
parent it still requires at least `3,513,707` archive/package bytes plus child
cost and reserve.

After the active Endpoint428 HORIZON trace terminalizes, the first external-derived
execution lane is therefore the independently audited identity-only successor
to v10-v12, `cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v13`, using the exact original
package, a clean environment, disk-backed scratch, managed exclusive stages, a
decimal-10GB hard cap, process-tree and VmHWM observation, one-CPU affinity, and
complete package accounting. CPU affinity and disk use are diagnostic
abort-after-observation signals, not hard eligibility proofs. The dormant q0 full runner is not reusable
unchanged because it inherits the old `/dev/shm` envelope, references missing
runner symbols, calls a keyword-only API positionally, loses the peak scratch
value, and expects the wrong restored filename. v13 is intentionally restricted
to exact opening-1M identity. It declares memory, runtime, CPU, disk, and trigger eligibility
not applicable and does not consume an activation receipt. A pass does not
authorize a larger gate; it supplies prerequisite identity evidence from which
governance may freeze one separate 100M resource successor. That successor must
bind the currently absent official Geekbench 5 binary and raw report and must
pass before separate full-1G Arm A and Arm B contracts can exist. The v13 runner compares the
default `9216` MiB control to the
`8192` MiB treatment, runs two treatment encodes and one treatment decode, and
keeps sampled PPM drops diagnostic-only because the native 5,000-byte purge
cadence can occur between external samples. A probability
or payload mismatch reclassifies the child; resource observations remain
diagnostic at this population. There is no threshold sweep: one later resource miss
may authorize only one phase-attributed correction. A pre-Predictor failure
authorizes patched q0; a failure caused only by the 5,000-byte check sawtooth
authorizes one measured cadence successor; a post-purge trough at or above the
limit retires PPM purging.

The `8192` MiB mechanism is plausible, not proved. Its trigger is
`8,388,608 KiB`, leaving `1,377,017 KiB` to the strict limit. A retained
77.62-percent snapshot had `8,508,652 KiB` total RSS and `92,464 KiB` in
`ppm.temp`, suggesting a current non-PPM footprint of `8,416,188 KiB`. But no
peak-time smaps sample proves that PPM residency caused the historical peak.
The 1M gate therefore tests identity, inverse, environment propagation, and
accounting only. The 100M resource result is reject-only and requires complete
matched control/treatment residency, fault, IO, tree-RSS, cgroup, and disk
telemetry plus a peak below `9,000,000 KiB`. Failure to sample a PPM drop is
inconclusive rather than a pass or failure. Full 1G is the first authoritative
memory and runtime gate.

Endpoint428 remains the active information-source laboratory, not the primary
submission substrate. Its best counted forecast is `109,389,323`, but no exact
full-1G score exists and its measured runtime frontier requires an
architectural replacement. The active HORIZON trace remains immutable and
unread until terminal. A valid pass still requires exact integer repricing and
one native one-byte P/K/D archive.

For the `105,000,000` objective, the first post-q0 information test becomes a
sparse, in-process CMIX/q0 HORIZON retained-parent measurement on the exact
CMIX transformed representation. The q1 census is only an opportunity
antecedent; it cannot transfer parent-relative gain. The measurement should
emit or aggregate only frozen active coordinates rather than write another
all-bit probability trace. Its economic floor must be recomputed from the
actual q0 package, child cost, and reserve. HORIZON-LOCKSTEP remains conditional
on a measured incremental corridor outside the one-byte expert; it is not an
automatic rescue.

The independent hedge is Fiber-HORIZON/Fiber-FOSSIL. The existing exact 1M
Endpoint probabilities and independently replayed semantic route ABI permit a
bounded D/G/S/R/N offline test before any recurrent route model. Failure
retires semantic-distance retrieval before LOOM or route fast weights. NNCP
MIDAS remains strong mechanism evidence, but the compact competitive open
parent does not exist; the only justified work is completing the already
frozen open 65,536-symbol P/K/F/S replay. ANCHOR-MIDAS, ROUTE-MIDAS, bit-head
FTRL, output-bias, shallow Delta-MIDAS, SAFE-MIX, and SWITCHBOARD receive no
independent execution priority.

The first Fiber implementation, version v3, was rejected before measurement.
Its `N` arm complemented the donor but owned an independent symmetric KT
correct/wrong state. Complementation swaps those two counts, allowing `N` to
relearn the sign and mirror `D` within one Q16 count; `D > N` was therefore not
an identifiable control. OMEGA exclusion
`fiber_fossil_complemented_independent_symmetric_kt_q0_v1` permanently retires
that construction. The corrected scientific core is
`wiki_fiber_fossil_endpoint428_opening1m_q0_v4`: `N` uses `D`'s exact pretruth
reliability, complements only the donor direction, and owns no update state.
Two algebra tests pass. Static execution audit then found that v4 merely sampled
its own `RUSAGE_SELF.ru_maxrss` after computation; the adaptive worker uses a
plain subprocess, so v4 could neither prevent overshoot nor include descendants.
Versions v5 through v7 then exposed three execution-authority defects before
measurement. v5 could not create its required cap on the plain adaptive worker;
v6 created a child cgroup but could write lifecycle claims before outer cleanup;
v7 moved authority outward but checked only output names rather than binding
every output by content. The independently audited runnable successor is
`wiki_fiber_fossil_endpoint428_opening1m_q0_v8`. It preserves the v4 core
byte-for-byte, creates an outer-owned child with exact `536,870,912`-byte
`memory.max` and zero swap before spawn, installs inherited `RLIMIT_AS`, records
peak/events/exit, and verifies same-inode empty cleanup. The worker and receipt
remain non-authoritative. A decision published last is the sole authority and
binds the other 21 declared artifacts exactly once as path, bytes, and SHA-256.
Injected extra-file, non-regular, and hash-drift failures leave no authoritative
artifact. Independent static audit passed this opening-1M execution envelope.
No scientific gate has run and all Fiber versions still earn zero credit.

The env-only CMIX execution envelope was first materialized and sealed as
`cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v2`. Read-only preflight and
contract validation passed, but independent static review rejected the v2
execution contract before measurement. It represented 100M-only memory and
runtime predicates as `true` at 1M instead of not applicable, omitted the flat
measurement/predicate map needed for reflection, budgeted 64 added bytes while
its exact commands add 100, incompletely bound guard and lease evidence, and
did not close every output through one manifest. v2 must not run. Independent
review then rejected v3 because CPU affinity was observed rather than imposed,
the lease namespace was caller-overridable, runtime authority was not
prospectively hash-bound, the source archive was missing from the frozen
inputs, and kill predicates were not reported exactly. v4 fixed those defects
but remained rejected because its dynamically loaded verifier escaped the
Python source closure, its result root was arbitrary, and a one-sided optional
witness silently became not-applicable.

The 1M-only v5 identity envelope fixed the earlier path and source-binding
defects but was still not executable authority: its dynamic validation closure
depended on a large third-party Python surface. v6 replaced that surface, but
contradictorily required q1 runtime evidence and performed shallow cgroup and
CPU checks. v7 created a q0-specific activation producer, yet used an invalid
resource phase, omitted the required phase marker, left its future cgroup
present, and did not bind the actual benchmark executable, cgroup parent, or
complete runtime closure. All v1 through v7 revisions remain immutable,
unmeasured negative infrastructure evidence.

The corrected envelope is
`cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v8`. Its activation producer
is stdlib-only and can run only after the adaptive running set and canonical
lease namespace are empty. It pins the exact Geekbench 5 executable and argv,
current host, singleton CPU, canonical managed lease, delegated cgroup parent,
random 128-bit owned child name, exact decimal-10GB cap, zero swap, pre-exec
join/release handshake, every observed cgroup PID affinity, event deltas, final
peak, and same-inode empty cleanup. The actual opening-1M coordinator uses a
separate stdlib-only resource guard bound to the exact objective-contract hash.
Its memory, runtime, and PPM-trigger eligibility fields remain null/N_A; an
opening-1M pass cannot authorize a larger gate.

The terminal v8 CMIX revision is
`operations/adaptive/candidate-revisions/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v8/20260901T175115312984Z_d2b986e8779a.json`
at SHA-256
`863a38b16af449f83d66ec9ccf2ab4bb500384f664ed00a6bc9588cd499df861`.
Its candidate tree is
`d2b986e8779ab29990f3b9d38a0513da8aa60380ad854f400e09e4ded4ba4bc8`
and its post-seal source closure is
`operations/adaptive/source-closures/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v8.json`
at SHA-256
`144314c91ca3a53195cbf4addc3034ade7e9a8e16b90c7f6f4347d09b8262d85`.
Static contract, AST, source-closure, and CPU-pinned fail-closed validations
passed, but independent adversarial review blocked v8 before execution. Its
sealed activation contract accidentally names the v7 future cgroup. More
importantly, the coordinator rehashes receipt-provided launcher data without
binding an independently authoritative producer invocation, trusts cleanup
booleans after the cgroup is gone, omits producer runner/guard identity from
the lease comparison, applies no strict receipt schema, and does not rederive
the current delegated-parent identity immediately before the 1M stages. These
are authority defects, not compression evidence. Correction-only v9 must bind
a decision-last producer execution, exact launcher semantics and complete
output closure, strict receipt schema, current parent identity, every sampled
PID affinity, and residual-process cleanup. The activation is deliberately
absent, so no Geekbench, cgroup, corpus, archive, inverse, memory, runtime, or
score evidence exists. Execution remains blocked by both this v8 audit and the
live HORIZON lane. Neither CMIX nor Fiber was queued or run during this audit.

Correction-only v9 added a decision-last materializer, current delegated-parent
rechecks, stronger residual-cgroup cleanup, exact v9 guard selection, and two
future CLI hashes. Independent review still blocked it. The activation contract
continued to name the v7 future cgroup and contradicted its own running-job
admission rule. The supposed own-job proof checked only caller-controlled job
and candidate strings, not the live adaptive worker, revision, tool, arguments,
PID/start identity, or terminal job receipt. Both hashes therefore originated
from one unauthenticated local materializer. The launcher check accepted
substrings instead of one exact join/exec program, the lease comparison omitted
producer runner and guard identities, and the bound schema was neither applied
nor recursively constrained. It also rejected a legitimate zero-byte benchmark
stderr. No v9 activation or execution occurred.

The v10 correction removed the unnecessary activation dependency from this
opening-1M identity question. No official Geekbench 5 executable exists in the
workspace or standard host locations, and this population cannot establish
full-corpus resource eligibility in any case. v10 therefore freezes one exact
identity-only candidate with fixed result, scratch, cgroup, lease, CPU, package,
source, runtime-closure, and resource-guard identities. Its hard decimal-10GB
cap is a safety boundary, while memory, runtime, and PPM-trigger eligibility are
explicitly null/N_A. Contract validation, AST compilation, source-closure checks,
and CPU-pinned validation-only preflight passed. Independent audit nevertheless
blocked execution: `memory.swap.max=0` was neither required nor set, and sampled
CPU affinity and disk use were described as strict safety even though neither is
a kernel/quota cap. No v10 corpus, cgroup, activation, or benchmark execution
occurred. Correction-only v11 must set and verify zero swap before exec and must
downgrade CPU and disk to diagnostic abort-after-observation claims. A 100M or
full resource successor remains separately versioned and blocked until the exact
Geekbench 5 authority is supplied. This is execution infrastructure with zero
compression or objective credit.

The terminal v10 CMIX revision is
`operations/adaptive/candidate-revisions/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10/20260901T182036268003Z_c06a4899c0b9.json`
at SHA-256
`8d8221a187619e9893c0b25def9981cb2c50e390afaaddb5aced77396f8f98d8`.
Its candidate tree is
`c06a4899c0b999bcfc634744e7b4ba4fc37fc4753d8d2401e4e9f324697ec019`,
its coordinator is SHA-256
`7044081f6fa4e31ee4ce6d9895e124fd6dc9d16a99f85830f46a0cc7807c597f`,
and its post-seal source closure is SHA-256
`4493d75d79dfa767dac689b2a3f95536b7091c0c9301953ca5bb6d608e9f09a2`.
Its blocking independent audit is
`operations/evidence/20260901T182717Z_cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v10_independent_static_audit.json`
at SHA-256
`76714b19b54dfa6c33f5839047ac8f01692c3f433510b40821165b120066ae5e`.

Correction-only v11 then set and read back `memory.swap.max=0` before child
execution and reclassified CPU affinity, temporary disk, elapsed time, memory,
runtime, CPU, disk, and PPM eligibility correctly as diagnostic or N/A.
Independent audit still blocked v11 before execution because two transitive
Python bases were listed only inside an unvalidated nested runtime-closure JSON,
the wrapper leaked a v10 preflight schema, and it set
`separately_frozen_100m_experiment_required=false` despite denying larger-gate
authority. The blocking receipt is
`operations/evidence/20260901T183852Z_cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v11_independent_static_audit.json`
at SHA-256
`81b3633de9fde0a53c28c1a4baddf0474105388ef46684cb138930f3d3c98d15`.
No v11 corpus, cgroup, lease, benchmark, or HORIZON access occurred. v12 is the
only authorized correction: directly verify the full transitive executable
closure, emit v12 schemas, and require a wholly separate frozen 100M successor
without authorizing it.

Correction-only v12 implemented those three changes without altering the P,
E-A, E-B, decode arms or the `955,881`-byte bounded accounting. Its preflight
directly rehashes all 13 transitive executable artifacts and requires exact
equality with the runtime index; it emits the v12 schema and sets
`separately_frozen_100m_experiment_required=true` while retaining
`larger_gate_authorized=false` and a null next gate. Exact zero swap remains a
pre-exec safety requirement, while CPU, disk, elapsed, and every resource
eligibility field remain diagnostic/N_A. Contract validation, revision-file
verification, direct-source drift rejection, and CPU-pinned validation-only
preflight pass. No v12 scientific gate has run.

The terminal v12 revision is
`operations/adaptive/candidate-revisions/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12/20260901T184349771061Z_9d35c87a82e7.json`
at SHA-256
`01d7a595ed43a9c90c40d3b2a4c8fe236be6b670b72f7d02e86b3331e211235e`.
Its tree is
`9d35c87a82e71e6d2cbdb184e2b86226415fb43e1bcb83a3f3218a91869fadbc`,
its coordinator is SHA-256
`9063d0b2df50a2808b94d7ae2c6df89c7132b94d0355a243a594aeb170c03982`,
and its post-seal source closure is SHA-256
`41a777d07c35f5de14b3894cf78cfc84db0ebd4cfe3c1aa4c1d326e83864c5aa`.
Independent audit still blocked v12 because it imported and executed the
v11/v10/v3/v2 chain before verifying that chain, then used an artifact helper
obtained from the unverified imports. Direct hashes after import do not close
pre-verification execution authority. The blocking audit is
`operations/evidence/20260901T185015Z_cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v12_independent_static_audit.json`
at SHA-256
`a6933c438dcc685e2e9b39a7b177b6f10b04afa8e89a8656a8cb3d21c96aeb3a`.
The only correction is v13: a minimal local-stdlib bootstrap must verify every
transitive source by path, bytes, and SHA-256 before importing any inherited
implementation or guard module. No v12 corpus, cgroup, lease, benchmark, or
HORIZON access occurred.

V13 implements that trust boundary. The coordinator hardcodes and verifies 13
inherited runtime artifacts with local `pathlib`/`hashlib` code before importing
`importlib` or v12. The guard independently verifies the v12/v11/v10 guard chain
before importing it. The candidate revision binds both v13 entrypoints without
a circular self-hash. Three bounded tests prove that drifted coordinator and
guard bases are rejected before sentinel code executes and that the import
statements follow the verification calls. The source closure contains 26 exact
records, the runtime closure contains 15, and the direct/runtime sets agree.
Independent static audit passed. Opening-1M v13 remains unexecuted and gives
zero compression, memory, runtime, CPU, disk, PPM-trigger, or objective credit.

The terminal v13 revision is
`operations/adaptive/candidate-revisions/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v13/20260901T191023552396Z_4b7cd7b5c67e.json`
at SHA-256
`138020ee7b08a329b24f8a9f2a1ad422089d52ffc52a6fd0e589b17f39f0b5ce`.
Its tree is
`4b7cd7b5c67e3daeb0979f3985b2509ef1e06968e81c930836923ccf8dc29773`.
The independent PASS receipt is
`operations/evidence/20260901T191507Z_cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v13_independent_static_audit.json`
at SHA-256
`df5345c4b32d7c47e05ac4b14474488d9946ccb0645a264229d691c5b6e7ca4a`.

The terminal v8 Fiber revision is
`operations/adaptive/candidate-revisions/wiki_fiber_fossil_endpoint428_opening1m_q0_v8/20260901T173422874597Z_8326287ddb4d.json`
at SHA-256
`c619323e7640f13ebb1a7cb6687430308835860b1be7e9ae962c2e8f42b0ff22`.

The complete strategy, exact evidence table, gates, kill conditions, and claim
boundaries are frozen at
`docs/eligibility_first_cmix_horizon_strategy_20260901.json`. This strategy is
zero-credit governance. It does not claim that q0 will pass or that any current
Gamma codec has solved the objective.

`evidence_conditioned_mutation_router_v9` makes the new order canonical while
preserving v8's active HORIZON liveness, no-partial-peek, exact-repricing, and
native one-byte rules. It adds no execution authority. Its only search-space
change is to admit the already-frozen PPM-only correction as a separate
external-derived eligibility lane and, after exact qualification, permit the
same physical HORIZON, semantic Fiber, and compact midpoint families to be
freshly measured on q0 rather than transferred from q1 or Endpoint428.

Evidence: `results/cmix_obias_source_full1g_roundtrip_a_qm0_v1/decision.json`,
`results/cmix_obias_source_full1g_roundtrip_b_qm0_v1/oom-terminal-receipt.json`,
`results/cmix_obias_source_full1g_ab_terminal_audit_v2/decision.json`,
`programs/cmix_obias_memory_safe_parent_q0_v1/manifest.json`,
`programs/cmix_obias_memory_safe_parent_q0_v1/program-lock.json`,
`results/cmix_obias_memory_safe_parent_build_ab_q0_v1/comparison.json`,
`docs/cmix_obias_ppm_env8192_audit_20260901.json`,
`results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json`,
`docs/endpoint428_runtime_frontier.md`, and
`operations/planning/evidence_conditioned_mutation_router_v9.json`.

## 2026-09-01 - Exact HORIZON repricing and independent semantic replay are sealed

The active retained-parent job remains
`endpoint428_horizon_retained_parent_trace_q0_v1`, job
`20260830T224837Z_a120752fb5`. At the latest read-only snapshot its trace held
`1,138,126,840 / 5,182,388,736` rows (`21.961433%`). The process ancestry was
intact, the guard remained `running`, and no RSS or official decimal-memory
violation was recorded. Peak sampled single-process and tree RSS were
`9,098,816 KiB` and `9,102,532 KiB`. This is operational progress only: the
live header row count is intentionally incomplete, no analyzer has read the
growing trace, and no scientific or archive conclusion exists.

`evidence_conditioned_mutation_router_v8` corrects one governance defect in
v7. A healthy nonterminal predecessor now means wait and authorizes no retry,
successor, promotion, retirement, or scientific conclusion. Only a terminal
infrastructure failure can authorize one correction-only retry. A causal,
alignment, identity, or provenance failure is quarantined before any retry.
All v7 scientific thresholds, exact-repricing requirements, source-family
limits, and composition order remain bound by the exact v7 hash.

The mandatory correction
`endpoint428_horizon_retained_parent_trace_exact_q0_v2` is now implemented and
sealed at candidate tree
`77906aafeb9ba22f5318a53ddfdba1aec6e4c737806037581edc94e43721e344`.
It preserves the active experiment's `2^63`, equal-prior, half-up law while
replacing only `long double` posterior division with a source-ordered 63-bit
unsigned-`__int128` quotient and exact remainder tie test. The full analyzer
runs exact and legacy trajectories together, records their first divergence,
requires legacy aggregate parity, and prices D/S/R/N twice on the same future
immutable trace. The runner requires the adaptive snapshot ID, revision
receipt, candidate-tree digest, and complete file closure. While v1 is live it
fails before opening `parent.p1` or `manifest-a.bin`.

Bounded arithmetic validation compiled both C++ sources under the frozen
strict flags. Python arbitrary-precision arithmetic matched all 15 full-scale
boundary vectors and all `225,450` exhaustive reduced-state rows. This proves
the integer state transition implementation, not HORIZON gain. No exact full
reanalysis ran and no v2 result directory was created.

The prospective native one-byte design is frozen separately as
`endpoint428_horizon_a_native_pkd_q0_v1`. It specifies an authoritative
Endpoint428 parent, bookkeeping-identical K arm, exact D arm, a bounded oldest-
anchor table, causal decoded-history spool, exact KT and Q63 state, P/K and K/D
identity witnesses, coder/inverse gates, package accounting, and resource
closure. It remains dormant and cannot become an adaptive proposal unless the
terminal exact reanalysis passes every frozen scientific predicate.

An independent audit also found that the sealed semantic-route v2 production
envelope was not launchable: it rejected the canonical raw symlink, ignored
the adaptive snapshot, did not prospectively bind the ordering addendum, and
its Python verifier checked ABI shape rather than independently replaying
semantic state. Full v2 execution therefore remains forbidden.

Correction candidate `endpoint428_semantic_route_tape_q0_v3` is sealed at tree
`c0f355845c3baa970d3f2c15255fc6a466528fa57aba1972236f4334c39f4cd0`.
Its new native replay independently decodes the bounded WRT fixture to raw and
checks every descriptor, route, ordinal, field ordinal, depth, event, flag,
availability coordinate, and raw frontier. The valid A/B fixture passed, while
five paired A/B corruptions of virtual ordinal, depth, field ordinal, raw
coordinate, and equal-availability event order were all rejected. The
contract-correction experiment binds the final design and ordering hashes.
A complete semantic scan remains dormant until a future production runner
binds this exact snapshot and holds the managed exclusive lease across both
scans and verification.

All artifacts in this entry are zero-credit governance, source, fixture, or
causal-shadow work. The objective remains a completely counted deterministic
score at or below `105,000,000` bytes. The verified Gamma full-1G score remains
unknown; the best counted forecast remains `109,389,323`, or `4,389,323` bytes
above target.

Evidence:
`operations/planning/evidence_conditioned_mutation_router_v8.json`,
`operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json`,
`operations/adaptive/candidate-revisions/endpoint428_horizon_retained_parent_trace_exact_q0_v2/20260901T131620927394Z_77906aafeb9b.json`,
`operations/planning/endpoint428_horizon_a_native_pkd_q0_v1.json`,
`operations/planning/endpoint428_semantic_route_tape_q0_v3.json`,
`operations/adaptive/experiments/endpoint428_semantic_route_tape_q0_v3_contract_retry_v1.json`,
and
`operations/adaptive/candidate-revisions/endpoint428_semantic_route_tape_q0_v3/20260901T131904564070Z_c0f355845c3b.json`.

## 2026-08-31 - Endpoint428 router supersedes the stale q1 execution order

`evidence_conditioned_mutation_router_v7` now governs prospective execution.
It preserves router v6 as immutable q1-era provenance but removes q1
qualification, q1 economics, and q1 coordinates from the active dependency
chain. The terminal q1 reflection retired q1 as a prize-facing parent, and the
recorded q1 and Endpoint428 transformed prefixes are nonidentical. Therefore a
q1-bound semantic tape, probability trace, or threshold cannot activate an
Endpoint428 result.

The active branch remains the immutable
`endpoint428_horizon_retained_parent_trace_q0_v1` job. A scientific miss
retires physical HORIZON without a LOCKSTEP, table, key-length, distance,
calibration, or contextual-mixture rescue. A pass does not jump directly to
LOCKSTEP: it first requires one portable exact-integer reanalysis and then one
native one-byte P/K/D finite coder. Only positive native single-expert evidence
may authorize a continuation-persistence shadow.

The exact reanalysis closes a concrete arithmetic mismatch found before the
active result was observed. The active frozen analyzer stores Q63 weights as
integers but computes posterior division through `long double`, uses total
`2^63`, and rounds halves upward. The frozen reusable SAFE-MIX law forbids
floating point, uses total `2^63-1`, and rounds ties to even. Those are
different algorithms, so SAFE-MIX cannot be silently substituted as the fix.
`endpoint428_horizon_retained_parent_trace_exact_q0_v2` instead preserves the
active experiment's intended `2^63`, equal-prior, half-up law and changes only
posterior division to exact 63-step unsigned-integer long division. The active
analyzer remains valid for its own prospectively frozen question, but only the
corrected result may authorize a native codec. The same immutable trace must
be repriced regardless of which result is better.

Semantic work is no longer allowed to inherit the dormant q1 route tape.
Source-only work may materialize an Endpoint428-bound parser and tape contract
while HORIZON runs, but no competing full-stream scan may start. The new tape
must bind Endpoint428's exact `647,798,592`-byte WRT stream, causal raw-prefix
coordinate, coder-bit coordinate, WRT inverse state, descriptor identity, and
two independent identical builds. Fiber-CTS remains the first semantic
predictor. Fiber-FOSSIL is conditional residual work, and oldest-anchor versus
most-recent retention and lockstep persistence are separate mutations.
ROUTE-MIDAS remains parked until Fiber-CTS and an open compact midpoint parent
independently qualify.

That source-only tape is now implemented and sealed as candidate tree
`a5e8391fc089f8e11b583d2e9c272b3619958ac55c5502618001e358957df4b8`.
The implementation freezes route eligibility before reading the current WRT
truth, incrementally reconstructs and compares raw bytes, emits fixed tape and
descriptor ABIs, and never synthesizes template or field exits at EOF. The
ordering addendum corrects the v2 prose without changing its information
source: deferred state from source `i-2` and structural posttruth state from
source `i-1` precede prediction at `i`; an ambiguous P/R at `i` cannot update
history until prediction coordinate `i+2`.

A bounded source-only fixture consumed `617` WRT bytes, reconstructed `604`
raw bytes, and produced two identical `176`-record tapes and seven-descriptor
sidecars. It exercised one-, two-, and three-byte dictionary codes, case and
escape controls, explicit and positional fields, delimiter predictions,
nested-route pause/resume, depth overflow, 96/97-byte atoms, and a final
pending delimiter. The independent verifier accepted the causal ABI and
rejected three corrupted variants: unknown route, witness mutation, and
prediction-before-state-action order. This is implementation validation only;
no complete route-tape build ran, no parent probabilities were read, and it
earns zero score credit. The guarded complete runner now fails closed while
the HORIZON retained-parent job is active.

The five proposed synthesis names are narrowed as follows. HORIZON-LOCKSTEP is
conditional on a corrected exact-integer HORIZON pass and then a positive
native one-byte P/K/D archive; it must show incremental value specifically
where the ordinary one-byte arm sleeps or changes donors. ANCHOR-MIDAS is
parked because neither a native HORIZON expert nor an eligible compact deep
midpoint parent exists. FIBER-HORIZON is merged into the existing conditional
Fiber-FOSSIL residual question rather than receiving a parallel family name.
ROUTE-MIDAS/LOOM-FASTWEIGHTS remains parked until Fiber-CTS proves semantic
virtual time and a frozen compact adapter basis exists. GAMMA-SWITCHBOARD is a
composition mechanism only and remains forbidden until two independent native
singles pass their own exact gates.

The adaptive queue was reconciled at the same boundary. Seventeen claimable
duplicate NNCP diagnostic/retry records and four held records with terminal or
superseding evidence were moved to `operations/adaptive/cancelled/` through
the canonical workflow. All source, results, reflections, and lineage evidence
remain intact. Twenty-six legacy jobs remain held and zero claimable pending
jobs remain. This is queue hygiene, not algorithmic evidence, and adds zero
score credit.

Evidence: `operations/planning/evidence_conditioned_mutation_router_v7.json`,
`operations/planning/endpoint428_horizon_retained_parent_trace_exact_q0_v2.json`,
`operations/planning/endpoint428_semantic_route_tape_q0_v2_ordering_addendum.json`,
`operations/adaptive/candidate-revisions/endpoint428_semantic_route_tape_q0_v2/20260831T213947752614Z_a5e8391fc089.json`,
`results/endpoint428_horizon_dualclock_source_census_q0_retry_v1/decision.json`,
`operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_q0_v1.json`,
and `operations/adaptive/reflections/20260823T215147Z_7827ad9bc5.json`.
