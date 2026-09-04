# enwiki9 Research Register

## 2026-09-04 - Adaptive ranking now respects candidate lifecycle

The proposal ranker previously considered proposal status, experiment
validity, and parent reflection but not the developed candidate's own state.
That made the live HORIZON trace and already reflected, held HARM-Delta source
fixtures appear eligible for duplicate scheduling. `enwiki9_reflections.py`
now overlays candidate metadata and all durable queue states before granting
eligibility. Pending or running candidates, candidates marked
`blocked_dependency`, `measured_negative`, or `retired`, and candidates whose
latest terminal job still awaits reflection are fail-closed. A reflected
`retry` or `next-gate` remains actionable.

Nine focused tests cover held/negative/retired states, pending and running
jobs, the latest-terminal reflection barrier, reflected retry, and an
undeveloped proposal. The real inventory check now excludes both running
HORIZON candidates and all four reflected HARM-Delta source prerequisites.
This is scheduling-integrity evidence only; it changes no candidate,
probability, experiment population, scientific result, archive, or score.

## 2026-09-04 - Live Hutter rule authority remains byte-identical

The official task, detailed-rules, and FAQ pages were fetched directly over
HTTPS and rehashed. Their returned sizes and SHA-256 values remain exactly
equal to the frozen authority documents in
`hutter_prize_rules_20260822`: `48,606` bytes and
`065186dc3e6ef61f295aa30873c142bd6e4a2f6f310cfbd1d28ec09cbc6cbff7`,
`15,907` bytes and
`e55d9f96b227e61ec0996adaf36304185d74db8c17093b403bb325240b2dc163`,
and `96,252` bytes and
`9233864b9ab2ce7b75ca2092416b518b196fcd498ab4e70e8c8f20b1bc42f52b`.
No rule migration is required: the published record remains `110,793,128`
bytes, the minimum eligible next score remains strictly below `109,685,197`,
and Gamma's `105,000,000`-byte objective remains the stronger threshold. The
single-CPU-core, no-GPU, decimal-`10 GB` RAM, decimal-`100 GB` temporary-disk,
Geekbench5 wall-time, necessary-option-byte, self-contained execution, and
public documented OSI-source requirements remain binding.

This is rule evidence only. It grants no candidate score, package, resource,
or eligibility credit, and the live pages must be checked again immediately
before an actual submission. Evidence:
`operations/provenance/hutter_prize_rules_20260904_revalidation.json`.

## 2026-09-04 - Reflected exact HORIZON recovery bridge is sealed

`endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3` closes the
single admissibility gap created when the original retained-parent controller
disappeared but its exact wrapper and CMIX child continued. It is a new
zero-credit candidate, not a repair or mutation of the active v1 source. The
only scientific input change is evidence admission: v3 requires the
prospective orphan observer to publish a validated `SEALED_IMMUTABLE_TRACE`
result with both adopted identities absent, complete geometry, unchanged
static inputs, no scientific access, and
`continuousResourceProofPass=false`. A valid adaptive reflection must bind the
exact recovery-result digest before any probability row is opened.

V3 does not synthesize the missing terminal v1 decision or pretend that
forward observation repairs the stopped resource guard. It verifies the
candidate snapshot and complete source binding before trace access. It then
resolves `parent.p1`, `parent.archive`, and `manifest-a.bin` only through the
recovery receipt; checks regular-file, one-link, size, digest, device, inode,
timestamp, and trace-header identity; and rehashes those inputs after analysis.

The scientific code remains byte-identical. Two independent builds and runs
of the frozen v1 floating-posterior analyzer must agree. Two independent
builds and runs of the frozen exact-v2 unsigned-`__int128` analyzer must agree.
The latter's embedded legacy trajectory must reproduce the former's complete
aggregate values. The arbitrary-precision Q63 fixture, exact `2^63` half-up
law, `2,331,505` active coordinates, D/S/R/N controls, chronological thirds,
and `40,163,160`-bit target-bearing gate are unchanged. Each phase uses one
logical CPU. The diagnostic analyzer ceiling is `9,500,000 KiB`, below the
official decimal limit; this accommodates the frozen sparse `mmap` working set
and conveys no native resource authority.

The selected candidate is sealed at tree
`39e29c51d13b3b16c1178007d1c98de981b220018e017191199ebf5416f9323f`
and remains dormant while the observer is live. The independently prepared
`endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3` tree
`a236ae6296c7bb86fd3c804fb8bd75e5ca8a32c4a548b411f9d05f6b164e2946`
is retained but will not execute: its `1,048,576 KiB` ceiling is not credible
for the frozen sparse mapping and it omitted the required adaptive reflection.
This is a pre-execution infrastructure rejection, not HORIZON evidence.

A complete selected-v3 pass may authorize only a recovered-dependency version
of the already-planned native P/K/D implementation. It grants no archive
score, inverse proof, package credit, composite resource evidence, or Hutter
result. Recovery, identity, fixture, repeat, legacy-crosscheck, or resource
failure invalidates the analysis attempt without judging HORIZON. With those
foundations valid, missing target scale, any nonpositive third, or any failed
control margin retires physical HORIZON without reinterpretation.

Evidence:
`operations/planning/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.json`,
`operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.json`,
`operations/adaptive/proposals/developed/000_endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.json`,
`operations/adaptive/candidate-revisions/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3/20260904T142927224038Z_39e29c51d13b.json`,
`programs/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3/`,
and
`tools/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.py`.

## 2026-09-04 - Isolated open dP is terminal negative; only integrated replay remains

The open top-attention probability-adjoint lineage has a valid terminal
scientific answer. Two v2 jobs failed before arithmetic because their runners
compared raw `meta.json` bytes against revisions whose identity contract uses
`semantic-meta-v1`; those jobs are implementation evidence only. The single
correction-only v3 then executed the complete `5,242,880`-word population twice
under external single-core resource guards. Scalar and AVX2/FMA treatments are
byte-identical, both repetitions are exact, the negated control is live, the
source package and dependency closure pass, and no work tree survived.

The frozen primary source-layout predicate nevertheless fails. Treatment and
source differ at `5,197,470` BF16 words. The prospectively registered alternate
serialization, originally labeled the wrong-layout control, equals all
`5,242,880` source words exactly and has SHA-256
`94763dc5ad7c78020c2620a06b0824fd7f2280c6a2a4c3783618931da44dbe22`.
The open kernel emits `state,head,stream,key`; the retained source tensor is
`state,stream,head,key`. This is an exact representation bridge, not a passed
isolated dP gate.

A separate read-only verifier independently recounted the treatment mismatch,
materialized the fixed permutation twice, reproduced the source digest, and
validated the population, repeats, controls, resource receipts, package,
dependency log, cleanup, terminal job, and source reflection. Its valid
reflection promotes only that zero-credit bridge. The OMEGA exclusion retires
the frozen source-equivalence claim and every further isolated dP layout,
permutation, tolerance, or correction successor. V3 receives no arithmetic,
compression, package-score, or objective credit.

The only allowable MIDAS continuation is
`nncp_open_integrated_midpoint_segment_replay_65536_q0_v2`. Its modern
experiment and proposal are prospectively frozen and validate, but the proposal
is `dormant_dependency`. It preserves three exact boundaries: the retained
`65,536`-row, `917,527`-branch F/O probability population; the one-boundary open
chain in which all `246` Adam parameter payloads, `20` memory layers, `244`
next-forward tensor groups, and `896` branch rows match; and the exact dP layout
bridge. Those boundaries do not compose themselves.

Activation still requires a complete open backward that generates every update
target without captured teacher gradients, a canonical full-population lock for
model, optimizer, recurrent, attention, cache, truth, activation, and oracle
state, and one sealed LibNC-free integrated runner. Missing closure keeps the
experiment dormant and is not a MIDAS failure. No more disconnected backward
primitive is authorized. Even complete integrated parity would remain a
zero-credit causality proof; finite archive gain would require a later compact
native candidate and fresh replay.

Source implementation has begun inside that single integrated identity without
activating or executing the experiment. Revision
`651287cce12b60e38e5e49b058a4b04cccf55317098a529b0d5e42151bac9e98`
implements a canonical duplicate-key-safe input-lock inspector and a one-thread
LibNC-free C++ arithmetic library. The library consolidates the already
attributed BF16 rules for flat and chronological-state parameter reductions,
ordered 128-coordinate transpose panels, final-root and sequential RMSNorm
backward, GEGLU, residual joins, causal loss residuals, scalar softmax backward,
the value-product probability adjoint, and the frozen head/stream layout bridge.
Seven local source tests pass, including compilation with AVX2/FMA and disabled
implicit contraction. Replay remains fail-closed: full forward caches,
remaining attention/QKV backward, optimizer/state traversal, population input
lock, oracle parity, repeats, and resource closure are still absent. This is an
implementation checkpoint with zero scientific or objective credit.

A second source-only revision,
`08b47bf743395906b76884a03f28b5e2646555dcd7fe886c3b56198e8186a669`,
now implements a candidate complete reverse topology. It adds content and
relative attention adjoints, Q/K/V and projection paths, reverse traversal of
all transformer layers, shared `b_r_0` accumulation, the output and final-norm
roots, the F32 embedding gradient, and the exact 246-entry production gradient
descriptor order. Release and ASAN/UBSAN self-tests pass, and the focused
seven-test source suite still passes. This does not yet satisfy the
`complete_open_backward` dependency: several previously unattributed reduction
schedules remain implementation hypotheses until the treatment materializes
all 246 payloads and compares them against prospectively bound oracles. No
teacher gradient payload was read as a treatment input, and this checkpoint
receives zero arithmetic, compression, archive, package, or objective credit.

A third source-only revision,
`d4e5927df08df92d42d5b0f5e5f5cd56ce40710da5f30f3b04fa5e29389a7192`,
closes the source-materialization boundary without activating the experiment.
It adds a bounds-checked tensor-container parser, an exact production fixture
loader that refuses to consume retained `train_h` activations as treatment
inputs, a candidate full open transformer forward, and a separate treatment
executable with no oracle-path argument. The executable binds every produced
gradient to the canonical 246-entry descriptor sequence and emits typed
BF16/F32 payloads plus checkpoints through collision-refusing partial files,
with its completion marker written last. A small end-to-end emitter test,
release build, ASAN/UBSAN build, and the seven focused source-contract tests
pass. Forward checkpoints and all 246 gradients have not yet been compared to
prospectively bound teacher payloads, so the arithmetic remains unvalidated
and this revision receives zero scientific, compression, package, or objective
credit. Adam, recurrent transition, midpoint rebuild, population locking, and
the O/K/F/S replay remain missing.

A fourth source-only revision,
`a9261969f38c518eaee3b365213672a40d1369434e010ad7e4c824c6bfadf93b`,
composes the next previously exact boundaries without running the production
population. It loads the 491-tensor optimizer state under exact names, types,
shapes, and configuration; binds it to the same canonical parameter/gradient
topology; and implements per-tensor norm and clipping, compensated BF16 low
words, the F32 embedding path, second-moment state, and the two-update bias
correction schedule. The update-5 scalar schedule matches the retained exact
Adam receipt bit-for-bit. It also implements the decoder-visible recurrent
shift-and-append law and the frozen segment sequence: zeroed future graph,
first-half update, full causal rebuild without shifting persistent memory,
second-half update, and one end-of-segment memory shift. Synthetic topology,
causality, exact-repeat, release, ASAN/UBSAN, and focused contract tests pass.
The test changes second-half inputs and truths and confirms first-half
probability identity. This remains an unvalidated implementation: no
production treatment has been materialized and compared against forward or
all-gradient oracles, no complete-population state lock exists, and O/K/F/S
have not run. It receives zero arithmetic, compression, archive, package, or
objective credit.

A fifth source-only revision,
`28a2f9b6960eeac24ec9644f036e0e90bdf3fa0d32c2bffe37f80dc303203580`,
adds the isolated production-comparator boundary without reading any retained
gradient payload during implementation. The treatment executable still has no
oracle argument. A separately linked comparator first requires the completed
full-comparator treatment marker and exact zero-teacher-input receipt; only
then may it open the retained oracle fixture. It verifies the canonical
metadata and every byte of all `246` gradient payloads plus all `20` rebuilt
`train_h` tensors, accounts for length differences, records the first differing
byte, and emits a collision-refusing zero-credit receipt. Release and
ASAN/UBSAN builds, the focused seven-test suite, and synthetic exact,
one-byte-different, and incomplete-treatment cases pass. No production oracle
comparison has run, so exact arithmetic parity, compression gain, package
credit, and objective credit remain unproved and zero.

Evidence:
[`v3 decision`](../results/nncp_open_top_attention_probability_adjoint_64_q0_v3/decision.json),
[`terminal verification`](../results/nncp_open_top_attention_probability_adjoint_64_q0_v3_terminal_verify_q0_v1/verification.json),
[`valid reflection`](../operations/adaptive/reflections/20260904T152612Z_cde41120fb.json),
[`OMEGA exclusion`](../operations/adaptive/exclusions/nncp_open_top_attention_probability_adjoint_64_q0_v3_source_layout_negative.json),
[`integrated v2 plan`](../operations/planning/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2.json),
[`integrated v2 experiment`](../operations/adaptive/experiments/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2.json),
[`integrated source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T182911157959Z_651287cce12b.json),
[`complete-topology source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T184647005158Z_08b47bf74339.json),
[`forward and treatment source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T191749467383Z_d4e5927df08d.json),
[`Adam and midpoint-segment source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T193633977336Z_a9261969f38c.json),
[`post-treatment comparator source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T195020353197Z_28a2f9b6960e.json),
and
[`integrated v2 proposal`](../operations/adaptive/proposals/proposed/934_nncp_open_integrated_midpoint_segment_replay_65536_q0_v2.json).

## 2026-09-04 - PALIMPSEST-MARKET-v2 is frozen as a nested finite-coder shadow

`palimpsest_market_v2` is the separately versioned successor to the retained
HARM mechanism, not a revival of the historical broad PALIMPSEST factorization.
The old portfolio warning remains binding: semantic elegance does not excuse
parser, realization, source, framing, model, table, package, runtime, or memory
cost. The proposal is therefore `dormant_dependency` while the active HORIZON
experiment continues unchanged. No corpus replay may read HORIZON's scientific
outputs before its fail-closed terminal route.

The later explicit PALIMPSEST directive supersedes the earlier instruction to
retain only HARM-Delta when deciding whether this shadow may be frozen. Its
nested arms are matched ablations inside one zero-credit experiment, not a
combination of separately measured score gains. The prohibition on a broad
replacement codec and on adding gains across changed probability trajectories
remains fully binding.

The frozen nested arms are `P/K/A/M/H/T/X/C/G`. A is exactly HARM-Delta's
latest completed exact-route value and generic causal edit transducer. M changes
only the exact-route reservoir depth from one to eight. H adds only normalized
route-shape and content-type backoff, with current content type inferred from
the already decoded value prefix. T adds one fixed typed leaf per unchanged H
donor: signed-integer affine variants, delimiter-preserving substitution,
bounded token alignment, or prefix/suffix grafting. X preserves T geometry but
permutes donor routes within power-of-two age and length buckets. C retains the
correct donors and generic leaves but changes every typed-kernel assignment to
a different valid kernel. G uses physical-history donors matched to each H
donor's exact causal age, content type, and length bucket. P is immutable;
K executes all bookkeeping while sending only P to its coder.

All markets use fixed factorized priors: equivalence masses `8/5/3`, newest to
oldest ancestor masses `128/64/32/16/8/4/2/1`, and generic-to-typed masses
`3/1`. Per-occurrence leaf weights and the global parent-versus-market weight
use exact Q63 sleeping Bayesian updates. A sleeping leaf is multiplied by the
awake market truth count, preserving its relative mass; transducers update only
after the complete truth byte. Coin betting is excluded from v2 and can enter
only as a new one-axis successor.

The decision surface is literal finite arithmetic, not ideal gain. Every arm
owns a 32-bit E1/E2/E3 arithmetic interval, explicit bit-count frame,
termination, byte padding, and decoder replay. P and K must match at every Q16
probability, interval transition, payload byte, and hash. Actual payload,
framing, source, model, table, and transmitted package bytes enter economics.
Process-tree memory and measured runtime remain separate hard gates and are
never converted into fictional byte charges. Bootstrap and ideal-log-loss
summaries are diagnostic only.

The prospective populations remain canonical raw opening `[0,1,000,000)` and
distant `[500,000,000,510,000,000)`, state-warm from raw byte zero. T must save
at least `5,021` and `50,204` exact payload bytes respectively and be positive
in every independently terminated chronological third. M must beat A by at
least `9/82` opening/distant bytes, H must beat M by `33/328`, and T must beat H
by `66/656`; these are density screens for frozen incremental package ceilings
of `8,192`, `32,768`, and `65,536` full-scope bytes. T must also beat admissible
A/M/H/X/C/G controls economically on both scopes. Any extension failure stops
at the simpler surviving arm without a rescue sweep. Only a complete T pass
may authorize one new native candidate, which still requires fresh package and
composite resource evidence.

The source-only implementation now fixes the reservoirs, all four typed
kernels, hierarchical sleeping updates, matched controls, and independent
finite coder. It opens no corpus and grants zero credit. Repeated fixture replay
passes exact HARM-A probability identity, P/K probability/interval/payload
identity, X/G admissibility, every arm's finite decode, a 4,096-bit coder stress
roundtrip, and all typed-kernel exercises. The known-answer run SHA-256 is
`a0614457cd000abf604fbe333458fe883d55a44a4f2bb4bd62d2be61147c82fa`.

MIDAS is not privileged as a combination. A later study must measure both
conditional PALIMPSEST marginals given MIDAS active/asleep and reverse MIDAS
marginals given PALIMPSEST active/asleep. Dominant overlap routes to expert
competition. Complementary residuals may expose only decoder-visible posterior
entropy, selected transformation family, and parent-surprise gap, followed by a
fresh joint finite archive. Separate gains are never added.

Evidence: `operations/planning/palimpsest_market_v2.json`,
`operations/adaptive/experiments/palimpsest_market_v2.json`,
`operations/adaptive/proposals/proposed/000_palimpsest_market_v2.json`, and
`programs/palimpsest_market_v2/`.

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

## 2026-08-28 - score-first HORIZON-FIBER pivot replaces q1 blocking

The campaign no longer treats q1 qualification as the blocking path to a win.
The q1 Arm A encode reproduced the external `107,730,531`-byte payload, but its
full decode was stopped incomplete and it receives zero score credit. No q1
Arm B is authorized unless a terminal runtime adjudication shows that another
full run can contribute to prize eligibility or a named retained-parent proof.

The primary mechanism is now **HORIZON-FIBER**: addressless far-history
retrieval. HORIZON indexes exact decoded physical context and predicts a remote
historical continuation without transmitting a source address, distance, or
length. FIBER is conditional: after a repeated causal semantic-route tape and
retained-parent evidence, the same principle operates in template-field virtual
time. A compact parent remains authoritative and untouched; specialists expose
pretruth integer probabilities through a sleeping mixture. This is not
checkpointing CMIX and does not require duplicating its persistent state.

The first frozen gate,
`fxcm_fossil_match_source_census_q0_retry_v1`, is terminal. Two complete scans
of the `587,138,826`-byte transformed stream produced the same
`4ca4be5e1c9d660b13e61e450e5d33985fd1b9ef6bd1c05998e50fb2aec368f2`
receipt hash. The census found `1,712,006` active far-history bytes, with
`1,343,200` correct treatment bytes, a `140,790`-byte minimum treatment margin
over the strongest control in every chronological third, five positive
distance buckets, causal/K-state identity, and `159,272 KiB` maximum tree RSS.
All frozen gates passed. This authorizes only a retained-parent probability
trace on the same representation and proves no probability gain, arithmetic
archive, inverse, package score, parent compatibility, or Hutter result.

The independent hedge remains compact causal midpoint learning. The deep NNCP
oracle saved `4,726` bytes over `322,978` raw bytes and was positive in all
thirds, while the output-head-only arm lost `569` bytes. Therefore output-bias
MIDAS is retired as the explanation, and full closed NNCP backpropagation is not
the prize-facing implementation. Any successor must be a bounded,
decoder-reconstructible deep update on a compact substrate.

The current best source-bound forecast is still `109,389,323`, which is
`4,389,323` bytes above the target before a prospective child package and
reserve. The active provisional gross requirement is `5,020,395` bytes. No
verified Gamma full-1G score exists, and no Hutter result has been proved.
Evidence: `docs/score_first_horizon_fiber_strategy_20260828.json`,
`operations/adaptive/experiments/fxcm_fossil_match_source_census_q0_retry_v1.json`,
and the terminal q1 reflection
`operations/adaptive/reflections/20260823T215147Z_7827ad9bc5.json`.

A raw-coordinate crossover check prevents an invalid compact-parent inference.
Endpoint428's exact opening-10M WRT stream contains `6,251,852` bytes with
SHA-256 `8f220e06860909f4b2a16d676ce696c5af0c738b7cc35b577618c63cbdff1ed7`.
The same-length prefix of the q1/CMIX transformed population has SHA-256
`8e93114628cc24cae6e1819fa1acff610983dae36d76bd3eee410ae71e26b5ca`;
the bytes differ. Therefore the terminal FOSSIL census is q1-representation
source evidence only. Prize-facing HORIZON must receive a new repeated census
on Endpoint428's exact full WRT stream, using its actual `100,000,000`-modeled-
byte history floor, before retained-parent pricing. No opportunity count or
control margin may cross this representation boundary.
The frozen crossover design is
`operations/planning/endpoint428_horizon_match_source_census_q0_v1.json`.
It preserves the 16-byte exact context and direct table, raises the eligibility
floor to Endpoint428's actual `100,000,000` modeled bytes, uses the exact
`647,798,592`-byte full WRT stream, and retains P/K/D/S/R/N plus repeat and
resource gates. If most-recent replacement alone is subscale while distance
suppression dominates, exactly one oldest-anchor persistence mutation is
authorized; a control failure retires physical HORIZON without a sweep.

Before v1 execution, the more efficient frozen v2 supersedes it with a single
two-clock scan: `endpoint428_horizon_dualclock_source_census_q0_v2`. `M` keeps
the most-recent exact continuation; `A` keeps the oldest surviving exact anchor
for the table residency. Both require an age greater than `100,000,000`, exact
16-byte verification, and transmit no address. The motivation is concrete:
the prior full-WRT helical census found `25,088,821` exact selected WRT bytes in
closed spans beyond that floor, but an explicit ledger consumed the value.
DUALCLOCK asks whether decoder state can recover that reservoir implicitly.
Both arms are scored against matched alias/random/negated controls and a causal
KT byte endpoint; a frozen rule selects one, both as sleeping experts, or
neither. High active count alone cannot authorize parent integration.

The implementation-only retry
`endpoint428_horizon_dualclock_source_census_q0_retry_v1` is now terminal. The
parent attempt faulted before scanning because an `8 MiB` identity buffer used
automatic stack storage; its reflection grants no scientific evidence. The
retry moved only that buffer to static storage. Two full Endpoint428-WRT scans
then produced the identical receipt SHA-256
`df0cf2ce43680a1cd96d22ad0863c41f467ab37680ce5c9bf79ca0f200f1c01f`
under a `380,016 KiB` maximum process-tree RSS.

The persistence attribution is decisive. Most-recent `M` exposed only `57,469`
active bytes and failed the frozen `313,775`-byte scale floor. Oldest-anchor
`A` exposed `2,331,505` active bytes, predicted `1,949,315` correctly, beat its
matched controls in every chronological third and four distance buckets, and
earned `14,097,745.513471339` causal KT gain bits against the frozen uniform
endpoint, with at least `340,336.866358339` gain bits in every third. All
population, repeat, causality, transition-identity, and resource gates passed.
This authorizes exactly one read-only Endpoint428 parent-probability trace at
the unchanged `A` coordinates. It proves no parent-residual gain, arithmetic
archive saving, inverse, package score, or Hutter result. Evidence:
`results/endpoint428_horizon_dualclock_source_census_q0_retry_v1/decision.json`
and
`operations/adaptive/reflections/20260830T005015Z_dd5329d770.json`.

The authorized successor is now materialized as
`endpoint428_horizon_retained_parent_trace_q0_v1` and queued under job
`20260830T224837Z_a120752fb5`. It regenerates the exact `A` manifest twice,
observes the complete `5,182,388,736`-row Endpoint428 pretruth integer trace,
and evaluates `D/S/R/N` through the same prefix-conditional KT endpoint and
global sleeping Q63 parent mixture. Its prospective target-bearing floor is
`40,163,160` mixture-gain bits, equal to the provisional `5,020,395`-byte
gross requirement. Falling below that floor, losing any chronological third,
or failing a matched control retires physical HORIZON on Endpoint428; a pass
authorizes one native `P/K/D` finite coder only. The stale pending q1 discovery
receipt `20260823T215202Z_d965c0aa22` was cancelled because q1 is retired as a
prize-facing parent; all terminal q1 evidence remains preserved.

## 2026-08-24 - activation corrections close economics, coordinates, and Fiber authority

Commit `aa65ae9ad309f139c26abc2f366b2c64edcdf0b4` is now the canonical
zero-credit portfolio freeze. No new information-source family is authorized.
The remaining work is to qualify the parent, falsify the frozen broad and
orthogonal routes, select exact winners, and scale singles before combinations.

The first correction removes provisional target constants from activation.
`q1_target_economics_activation_v1` can be generated only after independent q1
Arm A/B qualification and complete-package closure. Its receipt freezes q1's
archive, every counted package component, complete score, signed target
distance, nonnegative debt, a pre-result child-package ceiling and engineering
reserve, full raw/transformed/coder denominators, and four raw-scope gross
gates. Every gate is recomputed as
`ceil(gross_required * canonical_raw_scope_bytes / 1,000,000,000)`. Earlier
`4,080`, `40,793`, `407,925`, and `4,079,243` values remain historical
provisional gates and receive no activation authority. Evidence:
`operations/planning/q1_target_economics_activation_v1.json` and
`contracts/research/v1/q1-target-economics-activation-v1.schema.json`.

`canonical_raw_transformed_coder_scope_q0_v1` makes raw enwik9 coordinates the
economic authority. Every population begins as a half-open canonical raw
interval and binds the exact transformed interval, binary coder-decision
interval, frontend/parent/coder entry state, raw-to-transformed trace, repeat
trace, and activated scope threshold. Distant populations causally replay from
raw byte zero unless a separately proven exact checkpoint exists. Frontend
token boundaries may not round or resize the raw denominator. Evidence:
`operations/planning/canonical_raw_transformed_coder_scope_q0_v1.json` and
`contracts/research/v1/canonical-raw-transformed-coder-scope-v1.schema.json`.

The structural families now share one scientific parser population.
`semantic_route_tape_q0_v1` freezes a 64-byte little-endian record containing
the physical coder-decision coordinate, raw and transformed coordinates,
128-bit route fingerprint, 128-bit descriptor witness digest, event, flags,
template depth, explicit/positional identity, and field ordinal. Fresh Build A
and B tapes, descriptor sidecars, and summaries must be byte-identical with no
observed descriptor aliases. The sidecar is audit-only and cannot be queried by
a predictor; records become visible only at their causal coordinates. The tape
is forbidden from the final package, and native codecs must parse independently.
Evidence: `operations/planning/semantic_route_tape_q0_v1.json` and
`contracts/research/v1/semantic-route-tape-receipt-v1.schema.json`.

The Fiber-CTS dependency is now explicit rather than circular.
`wiki_fiber_cts_shadow_q0_v1` is the future source-bound D/G/S/R/N direct
probability generator. It commits uint16 probabilities and state digests before
truth and emits no arithmetic archive. The separate
`q1_causal_surprisal_atlas_fiber_cts_q0_v2` addendum repeats q1 only at the
shadow's exact coordinates, joins through raw/transformed/coder/tape identities,
and compares D against the parent and G/S/R/N using the activated raw-scope
gate. A pass authorizes one native P/K/D implementation only; a miss retires
semantic virtual-time contexts before LOOM. Evidence:
`operations/planning/wiki_fiber_cts_shadow_q0_v1.json` and
`operations/planning/q1_causal_surprisal_atlas_fiber_cts_q0_v2.json`.

Fiber-FOSSIL v1 remains immutable but cannot activate because it allowed a
choice between the Atlas KT calibration and a direct endpoint.
`wiki_fiber_fossil_q0_v2` preserves the route, 16-byte virtual key, tables,
controls, and resource limits while selecting exactly one endpoint: isolated
per-arm, per-bit-position uint64 KT correctness counts with no saturation or
rescale. Atlas and native code must emit identical integer probabilities and
state digests. A direct distribution may exist only as a separately versioned,
terminally authorized one-axis successor. Evidence:
`operations/planning/wiki_fiber_fossil_q0_v2.json`.

Router v6 binds these corrections and the exact memory branch. A terminal q1
tree peak at most `9,000,000 KiB` may pass the engineering-parent memory
dimension, subject to every other gate. A peak above `9,000,000 KiB` but below
`9,765,625 KiB` may pass the official dimension but fails engineering-parent
admission and authorizes one probability-identical headroom successor. A peak
at least `9,765,625 KiB`, or a strict cgroup/OOM failure, is a strict memory
failure. Declared specialist state never substitutes for measured composite
admission. The execution order is q1 A, independent B, economics, optional
headroom correction, midpoint 250KB/1M, repeated structural manifests, repeated
route tape, base Atlas, Fiber shadow, Fiber Atlas addendum, one native single,
transfer, 100M, one pair, and at most one triple. No live q1 process was changed
and no new source, scan, tape, shadow, replay, archive, inverse, compression
credit, or objective proof exists. Evidence:
`operations/planning/evidence_conditioned_mutation_router_v6.json`.

## 2026-08-24 - semantic virtual time becomes the first orthogonal source test

The independent strategy audit corrected the score accounting and the source
portfolio without changing any evidence verdict. `3,022,224` bytes is only the
gap from the external `108,022,224`-byte archive to `105,000,000`. The preserved
external package is `491,483` bytes, so the known complete counted baseline is
`108,513,707` and its actual gap is `3,513,707` bytes. Adding the prospective
`65,536`-byte child-package ceiling and `500,000`-byte engineering reserve gives
a provisional gross requirement of `4,079,243` bytes. That number is not q1's
final debt: after q1 qualifies, its actual archive and complete package must be
counted again. Evidence:
`operations/planning/semantic_virtual_time_strategy_q0_v1.json` and
`docs/semantic_virtual_time_portfolio_20260824.json`.

The source ranking is now explicit. CMIX-native causal midpoint adaptation is
the best evidenced broad route, but remains entirely unproved on q1. Semantic
virtual time is the best orthogonal route. The project will test it first with
`wiki_fiber_cts_q0_v1`, a bounded context-tree specialist whose state advances
only when the already-decoded template and field route appears. It uses a
4,096-record route bank and a direct-mapped 10 MiB exact-key context table;
fingerprint mismatch sleeps instead of merging unrelated fields, and any
observed descriptor alias invalidates the scientific receipt.
The parent is never checkpointed, restored, forked, or written. P/K/D/G/S/R/N
arms isolate semantic routing from generic eligible-byte recurrence, shifted
routes, random routes, and negation. If this direct model is subscale or fails a
control, semantic virtual-time contexts retire before WIKI-LOOM. The recurrent
LOOM route can activate only when Fiber-CTS first proves the source and a frozen
residual remains target-bearing. Evidence:
`operations/planning/wiki_fiber_cts_q0_v1.json`.

`wiki_fiber_fossil_q0_v1` is a separate conditional source. It searches the
last sixteen bytes in a field route's virtual history and predicts the byte
following the most recent exact route-key occurrence, even when unrelated
physical text separates the occurrences. It transmits no route, position,
distance, length, or copy command. Its aligned D arm must beat the unchanged
physical-time FOSSIL G arm, shifted-route, random-route, and negated controls in
every chronological third and in preregistered virtual-distance strata. If it
does not beat physical FOSSIL, the semantic-distance claim retires without a
key-length or table sweep. Evidence:
`operations/planning/wiki_fiber_fossil_q0_v1.json`.

Correct opportunity counts still cannot select either algorithm. The dormant
`q1_causal_surprisal_atlas_q0_v1` contract combines immutable WIKI-SCHEMA,
WIKI-PDA, and physical FOSSIL manifests by physical coder coordinate, then
records exact q1 integer truth probabilities in one repeated parent replay.
Every deterministic donor must first become a normalized causal probability
model through an isolated, pretruth KT correctness tracker; a guessed correct
byte is not accepted as probability evidence. The Atlas reports signed ideal
gain, control margins, chronological thirds, semantic and distance strata,
resource estimates, and pairwise overlap. Its `4,080`-byte-equivalent 1M and
`40,793`-byte-equivalent 10M thresholds are provisional target-bearing gates,
not forecasts. The Atlas is no-fit shadow evidence only; native arithmetic
archives decide value. Evidence:
`operations/planning/q1_causal_surprisal_atlas_q0_v1.json`.

Router v5 preserves all unrelated v4 routes while replacing the old
"everything else failed, then audit LOOM" rule. After q1 qualifies, the order is
exact package accounting, causal opportunity manifests, one retained-parent
Atlas pass, independent CMIX midpoint gates, Fiber-CTS, and only then residual
LOOM or conditional Fiber-FOSSIL. Positive singles advance before one fresh
pair archive, and at most one evidence-selected triple follows. SAFE-MIX remains
a risk-control wrapper and Schema-VM remains primarily a router; neither is an
information source. No source build, scan, parent replay, or substantial gate
is authorized while the live full-1G lease exists. These designs create no
probability trace, archive, inverse, compression saving, Gamma credit, or Hutter
Prize proof. Evidence:
`operations/planning/evidence_conditioned_mutation_router_v5.json`.

## 2026-08-24 - sparse exact associativity is the semantic CMIX contingency

The qm8 runtime-pressure audit motivated a source-level alternative to further
page-cache tuning. CMIX's 41 `ContextMap3` instances contain exactly
`41,664,640` semantic `E1<14,128>` buckets. Including each instance's frozen
alignment tail, those arrays allocate `5,333,745,664` bytes. A 96-byte base
can hold slots 0--9, the unchanged two-recent-index byte, a four-byte overflow
handle, and one reserved byte. The handle is naturally aligned at bytes 20--23;
the recency and reserved bytes occupy 24--25 and the ten seven-byte histories
occupy 26--95, so the representation requires no packed or unaligned typed
access. A separately owned 36-byte record holds the
complete checksums and seven state bytes for logical slots 10--13, and is
allocated only when the original fourteen-way transition first selects one of
those slots.

This is not the old false claim that a small shared pool magically recovers
stranded private capacity. Every overflowed bucket receives all four remaining
slots with no capacity ceiling. Absent overflow is exactly four zero slots;
present overflow preserves the parent's indexes, lowest-index checksum match,
protected recent entries, strict victim tie order, keep bits, run state, and
updates. Each instance reserves one contiguous `MAP_NORESERVE` arena and packs
activated records into its sequentially committed prefix. This needs only 41
additional VMAs, no chunk directory, and gives stable `cp` and `runp` pointers.
Virtual reservation is recorded separately from RSS; allocation identities and
addresses never enter prediction state, so a correct implementation should
reproduce every parent probability and archive byte by induction.

Before overflow, the representation releases exactly `1,333,436,416` bytes.
With `O` activated buckets, a conservative saving is
`1,333,436,416 - 36*O - 167,895`. Even charging maximum page-rounding waste
across all 41 arenas, at most `29,578,696` overflowed buckets (`70.9923%`)
preserves a `262,144 KiB` user-page reduction. Page tables and other kernel
costs still require cgroup measurement. The actual overflow demand is unknown
and receives no inferred credit.

A standalone differential transition verifier now supplies the first bounded
implementation evidence. It models both the frozen 128-byte fourteen-way
parent record and the 96-byte base plus owned 36-byte overflow record, compares
the returned slot, access class, and normalized logical bucket after every
operation, and mutates saved history pointers later to exercise pointer
stability. Two guarded executions each covered `500,065` operations across 257
buckets, observed all fourteen returned slots and all fourteen miss victims,
crossed overflow-record page boundaries, exercised absent-overflow checksum-zero
selection and reset/decommit, and emitted byte-identical semantic receipts with
SHA-256 `ed61546e...82a097`. Both receipts validate against the frozen schema.

This is a bounded differential model, not exhaustive state-space proof and not
native CMIX evidence. A preliminary invocation that mixed verifier stdout with
the resource guard's stdout was excluded because guard labels, PIDs, RSS, and
elapsed fields made the combined files non-identical. Requiring `--output`
separated semantic output before the two bound repeats; no transition mismatch
was observed. The result proves neither source integration nor probability,
coder, payload, inverse, memory, runtime, package, or compression identity.
Evidence:
`results/cmix_obias_sparse_exact_assoc14_q0_v1/finite-transition-verification.json`.

`cmix_obias_sparse_exact_assoc14_q0_v1` is therefore frozen as a dormant,
one-mechanism semantic contingency. It may activate only after qm8
terminalizes and either misses engineering headroom or a later exact-package
runtime gate attributes failure to reclaim/writeback pressure. Its D arm must
match q1's post-head probabilities, coder checkpoints, payload, and inverse;
plain ten-way packing is only the lossy C control. Any identity mismatch,
overflow-bound failure, less than `262,144 KiB` measured peak reduction, peak
above `8,750,000 KiB`, or runtime/package failure retires it without changing
the layout in rescue. No native source candidate, native coder run, archive,
inverse, memory gain, compression gain, or score credit exists. Evidence:
`operations/planning/cmix_obias_sparse_exact_assoc14_q0_v1.json`.

## 2026-08-24 - q1 memory pressure now carries a measured runtime-risk warning

The live qm8 Arm A gate remains non-terminal and untouched, but its resource
trajectory now rules out describing file backing as a free memory repair. At a
bound observation it was still encoding at `29.66%` after `78,762.6988`
seconds. That elapsed time already exceeds the complete earlier Arm A encode's
diagnostic `65,024.79` seconds by `13,737.9088` seconds. The active process had
recorded `780,463,370,240` read bytes and `42,261,831,495,680` write bytes,
while the cgroup had crossed `memory.high` `494,281` times without any
`memory.max`, OOM, or OOM-kill event. Thus soft-high reclaim is successfully
avoiding the previous hard-cap failure so far, but it is exchanging resident
headroom for heavy writeback/refault behavior.

A deliberately weak elapsed/fraction projection gives `265,551.9177` seconds
for the encode. Under the prize equation `252000000 / Geekbench5`, that
projection would pass only at a score below `948.967`; it exceeds the
`210,000`-second score-1200 limit by `55,551.9177` seconds. This is not an
official runtime failure: qm8 has not terminalized, progress may be nonlinear,
the present host has no retained raw Geekbench 5 report, and the earlier Arm A
timing was itself diagnostic. It is a receipt-bound risk warning, not a finish
forecast.

The routing consequence is strict. A qm8 exact memory pass still receives no
runtime authority until the already sealed exact-package, host-scored encode
and decode gate passes. A future 16 MiB backing threshold cannot promote on RSS
alone because additional file-backed hot pages may worsen this I/O trade. If
the exact-package runtime gate fails, q1 remains diagnostic infrastructure and
the prize-facing parent moves to a semantically compact codec such as the open
NNCP student. No roundtrip, memory qualification, runtime qualification,
compression gain, Gamma score credit, or Hutter objective follows. Evidence:
`operations/planning/cmix_filebacked_fxcm_qm8_runtime_risk_q0_v1.json`.

## 2026-08-24 - exact 16 MiB threshold geometry bounds one q1 memory contingency

A source-and-live-map audit now identifies one attributable q1 memory
contingency without modifying or signaling the active qm8 process. The sealed
FXCM allocation templates currently file-back exactly 26 allocations at or
above 64 MiB. Evaluating those same templates at a 16 MiB boundary finds
exactly 24 additional source allocations: two stationary maps, `dcsmN` state,
five mixer slabs, one run-context table, six 32 MiB `ContextMap3` tables, and
nine 16 MiB `ContextMap3` tables. Together they contain `662,421,824`
semantic bytes and require `662,423,968` allocation bytes, or
`631.7367248535156 MiB`. The expected mapping count would change from 26 to
50; no table dimension, value, hash, predictor, or coder operation changes.

The live allocation order provides a conservative reconciliation, not a
source-owned RSS claim. Anonymous VMAs interleaved among q1's file mappings
totaled `432,292 KiB`, with `432,112 KiB` resident and effectively all of it
referenced and dirty. Their geometry matches the named mixer and ContextMap3
cohorts. The other planned ranges occupy allocator-coalesced heap VMAs and
cannot receive allocation-level residency credit without the dormant marker
and pagemap protocol. The important negative result is that these are hot
pages: lowering the threshold can make another 631.7 MiB reclaimable, but it
does not reduce the semantic working set and may exchange RSS for writeback
and refault cost.

The exact one-axis contingency is therefore
`cmix_filebacked_fxcm_16m_backing_opportunity_q0_v1`: in a new candidate only,
change `kMinimumBackedBytes` from 64 MiB to 16 MiB. Connecting the dead
`ByteUpdate` hook, changing pageout cadence, resizing tables, or changing the
cgroup policy is forbidden. This is not yet an authorized candidate. If qm8
terminalizes exact at or below the already frozen `9,000,000 KiB` engineering
target, q1 remains the parent and this contingency is suppressed. Only an
otherwise-semantic-clean qm8 memory failure or peak above that target may
authorize q2. Its first matched gate must preserve integer probabilities,
payload, inverse, mapping count, and cleanup while reducing peak tree RSS by
at least `262,144 KiB` to no more than `8,750,000 KiB`; a smaller reduction
retires this threshold without a cadence rescue.

At the bound non-terminal observation qm8 was still encoding at `29.53%` with
no terminal receipt. No q2 source, build, run, archive, inverse, resource
qualification, compression gain, or score credit exists. Evidence:
`operations/planning/cmix_filebacked_fxcm_16m_backing_opportunity_q0_v1.json`
(`1bf1c0b0...756aa9f`).

## 2026-08-24 - verification v2 prevents a schema pass from impersonating native causality

Generalizing causal closure exposed an authority bug in the historical
verification receipt. V1 has one `verified` boolean and a mandatory
`join_closure_pass`; it cannot say whether only the representation is valid,
whether a shadow scorer is truth-independent despite physically seeing truth,
or whether a native arithmetic decoder commits probability before revealing
truth. Collapsing those statements would turn compiler hygiene into a false
causal algorithm claim.

The design-only verification-v2 schema separates three results.
`representation_verified` requires nineteen structural checks: reopened hashes,
mechanism identity, unique IDs, exact IR arm/role/source equality, event/source
order, state authority, pretruth exclusion, matched opportunities, control
outcome isolation, reset and mixture closure, safe paths, deterministic
reverification, and either a real join proof or an explicit no-join proof. A
pass has no errors and authorizes only compiler input; a failure has at least
one error and false check and has no compilation authority.

For `shadow_score_only_argument`, physical truth visibility must be disclosed
and a content-addressed independent AST/use-def proof is required for a
representation pass. That still leaves native causality false while the native
boundary is unverified. For `native_predecode`, truth must be physically absent
during construction and a bound native-boundary proof is required. Overall
`native_causality_proved` can be true only when representation and native
predecode both pass. Execution, compression, promotion, and claim authority are
always false.

Three positive receipt shapes validate: shadow representation pass with native
unverified, native representation/native-causality pass, and a fail-closed
shadow failure. Thirty-three contradictions are rejected, including pass/fail
authority mismatches, shadow/native truth lies, invalid proof-stage states,
missing proof evidence, native-causality derivation errors, non-independent
verification, unsafe artifact identities, and every execution or score
authority leak.

No actual verification receipt or verifier source was created. The schema says
what future independent evidence must prove; it does not prove the WIKI-PDA
source, execute a mechanism, or change the archive frontier. Qm8 remains live
and untouched. Evidence:
`contracts/research/v1/gamma-mechanism-causal-closure-verification-v2.schema.json`,
`operations/planning/gamma_mechanism_ir_v4_verification_authority_q0_v1.json`,
and its adjacent static review.

## 2026-08-24 - causal closure v2 represents WIKI-PDA without a fake fork or fake truth boundary

The generalized Mechanism IR exposed a second compiler-format defect. Historical
causal closure v1 enumerates only P/K/D/M/R/S and requires every mechanism to
declare a non-null join plus a forbidden copy pair. Corrected WIKI-PDA v3 is
P/K/C/T/D/R/S/N, has no mixture, and is one persistent structural scanner. A
fabricated M arm or byte-boundary rejoin would silently change the experiment.

The design-only causal-closure v2 schema now uses dynamic arm identities, binds
its source IR by bytes and SHA-256, orders events as before-truth, truth-reveal,
or after-truth, and declares every arm's source reads, state reads/writes,
action, and truth access. Named state subregions separate coordinate targets,
persistent causal transitions, matched opportunity identity, arm-private score
evidence, and write-only posttruth evidence. Null join is legal only with an
explicit no-join reason; a real join still requires retained/discarded state and
forbidden copy pairs.

The WIKI-PDA closure binds all eight arms, six IR sources, twenty state regions,
and nine ordered events: prefix ready, C/T construction, T-before-C treatment
selection, matched R/S/N freeze, logical truth reveal, score, parser advance,
completed-event commit, and coordinate advance. D/R/S/N share one opportunity
manifest. Control score outcomes are arm-private and unreadable. K may advance
only matched shadow state and its own digest; it cannot write parent/coder state
or emit a prediction.

The truth boundary is deliberately not overstated. The sealed scanner receives
`truth` as the `ScoreBeforeTruth` argument before all target expressions have
physically executed. Static inspection finds that argument only in six Score
comparisons and the write-only opportunity digest, not in target expressions,
but this is not a transitive data-flow proof. The closure therefore labels the
source `shadow_score_only_argument`, records that truth is physically visible,
and requires independent AST/use-def verification plus a native probability
commit before decoder truth before any causal execution claim.

Two positive shapes pass: the exact WIKI-PDA no-join instance and the schema's
non-null join branch. Twenty-two adversarial mutations are rejected, including
arm/source/state mismatch, pretruth truth access, phase inversion, private
outcome leakage, detached matched controls, artifact mismatch, and false
shadow/native truth declarations. These are inline static checks, not the
future independent verifier.

No compiler source, scanner, probability, coder, archive, inverse, package,
resource result, savings, or objective credit exists. Qm8 remains live and
untouched. Evidence:
`contracts/research/v1/gamma-mechanism-causal-closure-v2.schema.json`,
`operations/planning/wiki_pda_structural_replay_ceiling_q0_v3.causal-closure-v2.json`,
`operations/planning/gamma_mechanism_ir_v4_causal_closure_q0_v1.json`, and its
adjacent review.

## 2026-08-24 - Mechanism IR v4 restores the mandatory control alphabet

Attempting to express corrected WIKI-PDA v3 exposed a compiler-level omission.
The current `gamma-mechanism-ir.v1` schema represents only P/K/R/S controls,
the causal-closure schema enumerates only P/K/D/M/R/S, and compiler v3 rejects
any arm set other than exactly P/K/D/M/R/S. It also requires M to write
persistent mixture state even when a mechanism has no mixture. Therefore it
cannot honestly encode WIKI-PDA's C/T components or mandatory negated N arm.
Dropping those arms would violate the preregistered experiment and the campaign
requirement that random, shifted, negated, and causal-misalignment controls are
generated rather than described only in prose.

The correction-only `gamma-mechanism-ir.v2` source schema uses dynamic arm
identities and explicit multi-role declarations. Every IR must cover parent,
zero-write identity, treatment, random direction, shifted association, negated
output, and causal misalignment. Each arm declares its information sources,
output class, matched-opportunity treatment, state-access group, and whether it
is mandatory at the gate. A null mixture no longer implies a synthetic M arm;
a future compiler must instead enforce mixture/posterior obligations only when
the IR declares a mixture.

WIKI-PDA v3 is the first generalized instance. It encodes P/K/C/T/D/R/S/N,
with S explicitly serving both shifted-association and causal-misalignment
roles and N retaining the byte-complement control. Its update equation freezes
score-before-truth ordering, T-over-C priority, matched D/R/S/N coordinates,
and post-score parser/table/stack mutation. The exact equation hash is
`3dd5a97f...3bec7c`. This is a static IR for the already sealed scanner, not a
new scientific mechanism or execution.

Two positive schema shapes pass and eleven missing-role/resource controls are
rejected. JSON Schema cannot enforce unique arm IDs, cross-reference source and
state IDs, matched access sets, mixture-state isolation, safe output paths, or
closure equality. Those are frozen as mandatory future verifier checks rather
than asserted as completed. `gamma_mechanism_ir_v4` is the sole authorized
source successor, and it remains blocked on qm8 terminalization plus migration
of the separately identified managed-lease owned-cleanup correction.

No compiler source, compilation, scanner, probability, archive, inverse,
resource result, package, or objective credit exists. Evidence:
`contracts/research/v1/gamma-mechanism-ir-v2.schema.json`,
`operations/planning/wiki_pda_structural_replay_ceiling_q0_v3.mechanism-ir-v2.json`,
`operations/planning/gamma_mechanism_ir_v4_control_alphabet_q0_v1.json`, and
its adjacent static review.

## 2026-08-24 - WIKI-PDA v3 separates opportunity, resource, and infrastructure verdicts

The single correction authorized by router v4 now has a dormant decision
contract and fail-closed receipt shape. `wiki_pda_structural_replay_ceiling_q0_v3`
does not change the sealed v2 parser, stack, transition table, targets, controls,
population, or truth order. It reuses the exact unexecuted v2 scanner only as a
raw opportunity instrument. The scanner's `required_correct_bytes`,
`target_scale_correct_ceiling_pass`, and `absolute_ceiling_pass` fields are
retained as source-consistency diagnostics and are explicitly forbidden from
entering the v3 decision.

V3 rederives its scientific gates from raw D/R/S/N counts. D must activate on
at least `254,953` positions; every control must use exactly those positions
globally and by chronological third; D must have a positive correct count in
every third and strictly beat the maximum R/S/N correct count in every third.
Both scanner receipts, causal/K-transition identities, resources, qualified
parent evidence, population, and managed-lease cleanup must also pass. Even a
complete pass authorizes only a retained-parent integer-probability and
donor-surprise trace over the frozen opportunity manifest.

The decision schema distinguishes three terminal meanings. A complete
scientific miss retires the exact WIKI-PDA information source. A measured guard
failure before a scan receipt also retires it without fabricating counts. A
binding, authority, input, compiler, schema, lease, output, or observer failure
has no scientific verdict and authorizes one runner-only correction. This
prevents both free retries of genuine resource failures and false scientific
retirements from missing infrastructure.

Four in-memory positive shapes pass: scientific pass with both legacy correct-
byte diagnostics false, scientific retirement, pre-receipt resource retirement,
and infrastructure failure. Fourteen adversarial shapes are rejected, including
a pass below `254,953` active positions, a zero-correct treatment third, absent
parent evidence, use of the legacy gate, false resource classification, archive
credit, and a v2 identity in a v3 receipt. JSON Schema cannot compare arm counts
or rederive receipt hashes, so a future independent verifier remains mandatory.

No v3 source, adaptive proposal, compiler, scan, probability, archive, inverse,
resource result, package, or compression credit exists. Qm8 remains live and
untouched. Evidence:
`operations/planning/wiki_pda_structural_replay_ceiling_q0_v3.json`,
`operations/planning/wiki-pda-ceiling-decision-v3.schema.json`, and
`operations/planning/wiki_pda_structural_replay_ceiling_q0_v3_decision_review_q0_v1.json`.

## 2026-08-24 - router v4 prevents a false WIKI-PDA retirement

A cross-check of the next scientific gate found that WIKI-PDA v2 still used
`4,079,243` complete correct bytes as an "absolute eight-bit ceiling." That is
not a valid impossibility test. CMIX's actual-bit probability floor bounds
parent surprisal by 16 bits per bit, so one active byte has at most 128 bits,
or 16 bytes, of optimistic leverage. Complete-byte correctness is also not
necessary: a byte-level miss can share correct leading bits with truth. The
valid opportunity-volume screen for the frozen `4,079,243`-byte gross-gain
requirement is therefore `ceil(4,079,243 / 16) = 254,953` D-active bytes.

The v2 scanner is still useful because it already emits globally and by third
the exact D/R/S/N active and correct counts, matched opportunity identities,
causal-offset counters, and K/D transition digests. Its parser, stack,
transition table, controls, and source remain unchanged and unexecuted. What
is revoked is only v2's terminal decision authority: it may not run as the
scientific gate and may not retire WIKI-PDA because complete correct bytes are
below `4,079,243`.

The static futility audit authorizes exactly one correction-only
`wiki_pda_structural_replay_ceiling_q0_v3`. It must preserve the v2 scientific
transition, require at least `254,953` matched active bytes, positive aligned
correct bytes in every third, strict D-over-R/S/N third margins, duplicate
receipts, causal identities, and resources. Passing authorizes only an exact
retained-parent probability/donor-surprise trace. Active or correct counts
remain zero-credit and cannot establish archive gain.

`evidence_conditioned_mutation_router_v4` now encodes that correction, rebinds
the future midpoint observation to the compositional v6 proof identity, adds
the already-frozen WIKI-SCHEMA-VM and FOSSIL-MATCH ladders, and makes the
WIKI-LOOM source audit genuinely dormant. WIKI-LOOM can be audited only after
q1 qualifies, CMIX adaptation/open NNCP/WIKI-PDA terminalize subscale, and the
two already-frozen information-source families are terminally classified.
None of these static corrections activates source, runs a scan, changes qm8,
or creates compression, authorship, or objective credit. Evidence:
`operations/planning/wiki_pda_structural_replay_ceiling_q0_v2_futility_audit_q0_v1.json`
and `operations/planning/evidence_conditioned_mutation_router_v4.json`.

## 2026-08-24 - midpoint v6 freezes a bounded compositional ABI and fail-closed receipts

The compositional-boundary successor now has a fixed typed layout, binary ABI,
direct-bound parse schema, joint finite-coder schema, and adjacent static
review. This closes the design-only activation item left by the prior v6
entry; it does not materialize source or authorize execution.

The sparse component layout reuses the exact 130 Byte-LSTM/midpoint tensors
without renumbering them and adds eleven canonical ByteMixer/ByteModel wrapper
tensors. The complete component is therefore 141 tensors, `17,806,224`
logical bytes, 4,412 leaves, at most 8,683 tree nodes, and `277,856` digest
bytes. The wrapper includes the one-output probability, byte-model search
state, 256 probabilities, byte map, inputs, folded obias row, offset, and a
one-byte output-bias binding selector. Raw pointer bits are forbidden. Because
the sealed source lazily sizes `folded_bias_`, future v6 source must allocate
its fixed 256-float positive-zero extent at construction and prove exact
probability neutrality; this is an allocation-only prospective change, not a
current source fact.

`gamma-midpoint-compositional-abi-v2` replaces v5's four large streams with
two compact files. A 192-byte header binds source, ABI, layout, population,
arm, replicate, and direction. The checkpoint file is exactly 1,472 bytes:
six 204-byte rows at start, first closure, native horizon, population midpoint,
terminal pre-flush, and finalization. Probability and component-boundary
values are hashed online rather than written per bit. The update file contains
one 256-byte row per causal closure, or `1,000,184`, `4,000,248`, and
`40,000,248` bytes at 250KB, 1MB, and 10MB for K/F/S. Six full component roots
read `106,837,344` canonical bytes per run instead of scanning all state every
64 events.

Two review corrections matter. First, an independent parser cannot recompute
online digest preimages that the compact streams intentionally omit. It must
rederive framing, body hashes, formulas, flags, and comparisons; a separate
source-hook audit, mutation controls, and observer neutrality establish the
online preimages. Second, six sparse roots cannot prove the preregistered
10MB rule that aligned F beats P and shifted S in every chronological third.
V6 therefore binds three isolated fresh-start copies of the exact integer
range coder, fed the final probabilities and decoded bits for their original
coordinate thirds. Their encoder/decode-identical payloads are exact causal
controls, never native archive savings and never score credit.

Draft 2020-12 static controls accept all twelve P/K/F/F/S/S encode/decode
parse shapes, all three positive population decisions, and complete subscale
failure receipts at all three populations. Nine malformed parse cases and
twelve false joint-pass cases are rejected, including wrong ABI/layout
bindings, reordered checkpoints, false K restoration, 4,079-byte and
40,792-byte threshold misses, a nonpositive third, OOM evidence, an oversized
package, a failed parse, and false persistence authority.

Source visitor/emitter/parser implementation, final source-interface audit,
mutation controls, clean builds, neutrality, and every native archive remain
absent. Q1 is still unqualified while qm8 owns the full-1G lane. V6 therefore
retains zero compression and objective credit. Evidence:
`operations/planning/cmix_obias_shadow_midpoint_oracle64_q0_v6_source_layout_q0_v1.json`,
`operations/planning/cmix_obias_shadow_midpoint_oracle64_q0_v6_compositional_observability_abi_q0_v1.json`,
the two named v2/v6 schemas under `contracts/research/v1/`, and the adjacent
ABI review artifact.

## 2026-08-24 - midpoint observability pivots to a compositional boundary proof

The every-64 six-partition Merkle design is superseded before implementation.
The exact phase-1 map shows why: its five Byte-LSTM/midpoint partitions alone
contain `17,802,103` logical bytes. Full scans at the v5 checkpoint cadence
project to `69,588,420,627` bytes at 250KB, `278,211,265,684` at 1M, and
`2,781,632,000,059` at 10M. More decisively, v4 explicitly clears
`4,096,154` logical midpoint bytes at every closure. Soft-dirty records those
writes even when they restore zero, forcing at least `640,024,062,500` bytes
of canonical rehash input at 10M before dynamic or external CMIX state. This
is a proof-harness failure, not evidence against midpoint learning.

The reserved v6 design keeps v4's P/K/F/S arithmetic unchanged and uses the
actual source boundary. The component is ByteMixer, its ByteModel base, its
owned LSTM, and midpoint state. The rest of Predictor can observe it only
through `ByteMixer::Predict()[0]`; `lstmpr` and `lstmex` are assigned but not
read in the bound tree. Conversely, the component receives only the declared
Perceive, SetInput, SetOutputBias, ByteUpdate, and Predict calls. The midpoint
overlay has no pointer or reference capable of bypassing that interface.

For P versus K, equal initial environment state plus the complete rolling
component-output transcript gives an inductive certificate: equal output and
the same decoded bit drive the deterministic environment to equal next state
and therefore equal next component input. K additionally retains its inline
bitwise hidden/cell restoration check and is forbidden from committing live
parameter or optimizer writes. Every final coder probability, payload, and
inverse must still match P exactly.

V6 therefore keeps online probability and component-boundary digests, bounded
per-closure update records, sparse typed component roots at no more than six
coordinates, native payloads, exact inverses, repeats, resources, and package
accounting. It drops repeated full gradients, optimizer tensors, and external
state roots because exact longitudinal outputs and the source write-set prove
the relevant behavior more directly. The 130-tensor phase-1 map remains useful
for sparse localization; its soft-dirty path is parked.

No ABI-v2 schema, source, build, parser, fixture, or archive exists yet. V6 is
design-only, q1 remains unqualified while qm8 runs, and all compression and
score credits remain zero. Evidence:
`operations/planning/cmix_obias_shadow_midpoint_oracle64_q0_v6_compositional_observability_q0_v1.json`.

## 2026-08-24 - midpoint v5 freezes 130 typed tensors and bounded dirty scheduling

The first source-bound layout pass now closes the Byte-LSTM dynamic,
parameter, optimizer, ordinary-tape, and midpoint partitions against the
exact sealed q1 source and dormant v4 overlay. The bound release geometry is
one 256-cell layer, a 256-symbol vocabulary, a 128-event native horizon,
`sli=528`, `soh=272`, `scell=256`, and `sdense=528`.

The canonical expansion contains 130 tensors totaling `17,802,103` logical
bytes and 4,401 4KiB leaves. Its pair-or-lone Merkle storage is bounded by
8,672 digest nodes, or `277,504` bytes. The map separates the interleaved
NeuronLayer w/u/m/v slabs into source-order logical tensors and includes
padded lanes only when the bound SIMD kernels consume them. It excludes
pointers, allocator rounding, object padding, capacity, addresses, and the
inactive F16 `input_ptrs_` payload.

A hybrid dirty strategy is selected for the future observer. Typed visitors
remain the only source of canonical hash bytes. Linux soft-dirty bit 55 is
used only to conservatively schedule which registered leaves must be
rehashed after `/proc/self/clear_refs` receives `4`. This catches
write-then-restore and can overmark strided aliases without changing a root.
It does not establish source coverage, enter a digest, or replace the
mandatory terminal rebuild from zero. Heap, valarray/vector, aligned,
anonymous, file-backed, huge-page-advised, cross-page, write-restore,
pageout, remap, and permission cases remain mandatory calibration gates.

This is deliberately not described as complete observability. The external
predictor partition is still open. The existing q1 observer maps only the 26
large FXCM allocation ranges affected by q1; it does not enumerate mixers,
SSE, small contexts, ByteMixer wrapper state, the bit head, frontend, or
reversible transform. Until those objects have the same typed leaf and source
write coverage, the six-partition ABI remains fail-closed and no v5 build or
run is authorized. Evidence:
`operations/planning/cmix_obias_shadow_midpoint_oracle64_q0_v5_source_layout_phase1_q0_v1.json`
and its adjacent static review.

## 2026-08-24 - midpoint v5 receives a canonical observability ABI

The observability-only successor reserved by the v4 audit now has a frozen
binary evidence contract and two direct-bound Draft 2020-12 receipt schemas.
This remains design infrastructure: no v5 source, parser, build, fixture, or
archive exists, and the P/K/F/S midpoint arithmetic has not changed.

`gamma-midpoint-observability-abi-v1` defines four independently parsed
streams for every encoder and decoder run: tensor layout, every final uint16
coder probability, rolling checkpoints, and midpoint updates. A 160-byte
header binds the exact candidate source tree, ABI artifact, raw population,
modeled stream, arm, replicate, and direction. A 56-byte footer binds body
bytes, record count, body SHA-256, and clean EOF. Checkpoints have an exact
332-byte representation at start, every 64 modeled events, terminal pre-flush,
and finalization. Updates have an exact 328-byte representation and preserve
all nine aggregate witnesses before detached buffers are cleared.

The six state partitions now have a reproducible current-state definition.
Every named initialized logical tensor is split into 4,096-byte leaves and
hashed through a domain-separated pair-or-lone SHA-256 tree. Dirty leaves and
only their ancestors are refreshed after semantic writes, avoiding v4's
infeasible repeated scan of all large FXCM ranges. Start builds read every
leaf in bounded chunks; terminal control independently rebuilds all six trees
from zero. A tree with N leaves stores fewer than 2N digest nodes, and the
future build must reject if its exact layout makes observer storage and
scratch exceed `268,435,456` bytes.

The update aggregate ABI fixes type tags, tensor metadata, logical lengths,
content digests, observation timing, canonical empty groups, and source-order
population for targets, capture, errors/adjoints, recurrent gradient plus
Adam result, output gradient plus result, pre-restore state, post-replay
state, complete detached values, and post-clear scratch. F and S retain the
same target vector; the record's frozen rotation field remains their only
association difference.

The parse schema requires exactly the dynamic, parameter, optimizer,
ordinary-tape, external-predictor, and midpoint partitions. The joint receipt
requires P, K, F-A, F-B, S-A, and S-B, with encoder/decode observations,
roundtrips, resources, package accounting, matched comparisons, and zero
Gamma credit. In-memory positive controls validate both schemas; duplicate
partition and wrong-repeat negatives are rejected.

The global schema registry was deliberately left byte-identical because qm8's
live terminal dispatcher binds it by SHA-256. V5 schemas remain directly bound
until qm8 terminal dispatch; any later registry revision must rebind all
active dependents. Evidence:
`operations/planning/cmix_obias_shadow_midpoint_oracle64_q0_v5_observability_abi_q0_v1.json`
and its adjacent review artifact.

## 2026-08-24 - midpoint oracle v4 has an observability-only pre-archive gap

A source-level audit separated the midpoint algorithm from the proof harness
that would be required to interpret it. The frozen v4 overlay implements the
P/K/F/S arm selection, local-32 capture and backward path, detached K update,
F/S parameter commits, state-only replay, and canonical scratch clear. It does
not emit any successful-path trace, state digest, update count, or update
manifest. Its only output calls are fatal diagnostics, and each closure clears
the detached witnesses that the evidence contract requires the future archive
receipt to preserve.

The existing q1 full-identity observer is reusable but insufficient by itself.
It hashes every post-head integer probability, coder checkpoints, and the 26
large FXCM semantic allocations affected by q1. That is a valid, deliberately
allocation-specific completeness argument; it does not register the complete
Byte-LSTM dynamic, parameter, optimizer, ordinary-tape, external-predictor,
and midpoint partitions required at every 64-event checkpoint by the v4
evidence contract. Retained `KH_TRACE` likewise covers arithmetic probability
and residual evidence, not those partitions.

Literal reuse would also be computationally invalid. The q1 observer is
encoder-only, omits payload-prefix digests, and rereads then pages out all 26
large ranges at each state checkpoint. Applying that operation every 64 events
would read at least 6.8 TB on the 250KB gate alone. The existing midpoint
receipt schema is bound to the obsolete v2 candidate and cannot represent the
v4 six-partition or update-row evidence.

The contract also names hashes without freezing their canonical preimages.
It does not define field tags, traversal order, integer byte order,
floating-point object encoding, tensor geometry rows, checkpoint hook order,
or payload-prefix digest semantics. Consequently, adding ad hoc print calls
would still not yield independently comparable evidence.

The exact v4 overlay is therefore classified
`dormant_prearchive_observability_incomplete`, not scientifically rejected.
No build or run exists, and no compression conclusion follows. One
observability-only derived successor is reserved as
`cmix_obias_shadow_midpoint_oracle64_q0_v5`: it must preserve all P/K/F/S
arithmetic, populations, controls, thresholds, reset/join behavior, and
resource ceilings while adding fail-closed partition hashes, complete update
manifests, and receipt plumbing under a versioned binary observability ABI.
Because its source changes, it receives a new candidate identity rather than
editing v4 in place.

The correction must compose the calibrated q1 observer for every-bit
probability and coder primitives, not its repeated full-range pageout path.
V5 needs matched encoder/decoder hooks, payload-prefix hashes, complete LSTM
and midpoint visitors, and an incremental canonical mutation transcript for
large external state with bounded snapshots. It must pass a one-byte mutation
control for every new partition, freeze an independently parsed canonical
serialization and receipt schema, and prove
instrumented/uninstrumented probability and payload neutrality
before F/S results are interpretable. This audit is dormant while qm8 owns the
full-1G lane and while q1-v3 qualification receipts are absent. It grants no
source execution, archive, compression, package-score, or objective credit.
Evidence:
`operations/planning/cmix_obias_shadow_midpoint_oracle64_q0_v4_observability_audit_q0_v1.json`.

## 2026-08-24 - midpoint oracle v4 receives a dormant source overlay

The authority-only v4 midpoint proposal now has concrete, reviewable
implementation text without violating its q1 qualification dependency. The
new artifact is not a candidate tree: it is an inert integration patch plus
four detached declaration/implementation fragments bound to the exact sealed
q1 makefile and Byte-LSTM source hashes. A read-only verifier rehashes those
five parent files, the four authority artifacts, itself, and every overlay
file; checks that the patch touches only the makefile and four LSTM files; and
runs only `git apply --check --whitespace=error-all`. All static checks pass. No patch was
applied, no source tree was materialized, and no build or codec arm ran.

The implementation is not whole-compressor checkpointing. It preallocates
separate 32-row recurrent histories, output errors and adjoints, gate
transposes, dense/symbol/gamma/beta gradients, detached control rows, and
dynamic-state snapshots. At causal closure it reconstructs each historical
output matrix from the absolute native pending factors, runs local reverse
BPTT without calling the ordinary 128-row backward path, applies recurrent
Adam before output SGD, restores only Byte-LSTM hidden/cell state, and replays
with a history-free numerical clone of the recurrent forward pass. The
closure byte keeps the feature that actually predicted it. K performs the
same update arithmetic on detached copies and aborts unless replay reproduces
the closure dynamic state bit-for-bit; F commits aligned targets; S changes
only the frozen 16-position target rotation.

The review text totals `44,862` bytes. For the sealed `V<=256`, `C=256`,
one-layer geometry, the rounded buffer and vector payload formula is
`4,096,192` bytes and the design records a conservative `5,000,000`-byte
live-allocation bound, far
below the frozen `268,435,456`-byte incremental ceiling. Neither number is an
official package or memory measurement. Compilation, P/q1 identity, K/P
complete identity, F/S synchronization, resource compliance, inversion, and
all compression effects remain unproved. The overlay is dormant and receives
zero archive, compression, package-score, or objective credit.

A separate dormant evidence contract now prevents the future harness from
weakening that boundary. It freezes the P/K/F/F-repeat/S/S-repeat output tree,
64-event rolling hashes for coder and six state partitions, the exact
midpoint-update row contents, the closure-count formula, complete inverses and
resources, P/q1 and K/P cross-arm equality, F/S repeat equality, package cost,
and fail-closed decision equations. It grants no execution authority.

During this static work, qm8 remained the sole substantial process. Its Arm A
encode advanced to `23.80%`; the process tree is live, its guard reports no
cgroup `max`, `oom`, or `oom_kill` event, and no full-roundtrip receipt exists.
The process was not signaled, modified, or treated as q1 qualification.

## 2026-08-24 - midpoint oracle rebound to exact q1 v3 authority

The post-q1 CMIX midpoint route was not executable despite its corrected v3
causal semantics. `cmix_obias_shadow_midpoint_oracle64_q0_v3` still required
the policy-v4 q1 decision and v2 verification surface that policy v6 has
mechanically revoked. The dormant persistence-attribution v2 compounded that
defect by depending on both the revoked q1 route and the superseded midpoint
oracle v2. Neither proposal had candidate source or archive evidence, so this
is a prospective authority correction, not a reinterpretation of a run.

The new
`cmix_obias_shadow_midpoint_oracle64_q0_v4` proposal preserves the exact v3
scientific mechanism: `P/K/F/S`, 64-event segmentation, closure only after
decoded `x_(s+32)`, first adapted prediction `x_(s+33)`, detached local-32
backward arithmetic, native-tape-isolated state replay, persistent donor-order
updates in `F/S`, the 16-event target-rotation control, and the frozen 250KB,
1MB, and 10MB gates. It changes only qualification authority. V3 is now
superseded; persistence-attribution v2 is also superseded, with v3 reserved
only after a valid target-scale causal oracle-v4 pass.

The adaptive proposal activator now recognizes one new fail-closed dependency
kind, `terminal_parent_qualification_v3`. Activation requires both canonical
q1 v3 artifacts, the exact bound verification schema and verifier digests, a
revision-7-or-later active policy, all positive verification and evidence
checks, zero Gamma credit, and `memory_safe_external_parent_only` authority.
It rehashes the authority policy and activated full-identity plan, then calls
the exact v3 verifier again against the qualification router and absent
canonical lease namespace. The stored verification must equal that fresh
replay byte-for-byte as a JSON value; a narrative verdict cannot activate the
proposal.

Even after that dependency passes, activation authorizes only a new
content-addressed source materialization from the sealed q1 tree. The midpoint
implementation, Mechanism IR compilation, arm-difference manifest, synthetic
phase and negative controls, two clean builds, package closure, and guarded
finite-coder arms remain unproved and must be produced before scientific
execution. The v4 contract is dormant, unexecuted, and worth zero archive,
compression, package-score, or objective credit. Static schema, reference,
source-closure, and rank derivations pass; the ranker returns `selected: null`.
V4 names v3 as its direct proposal parent and is the exact successor in v3's
`superseded_by` field, so a future receipt-backed activation can escape the
inherited v3 block without reviving any other descendant.

The next source-only boundary is now frozen without crossing that activation
gate. `cmix_obias_shadow_midpoint_oracle64_q0_v4_materialize.py` names one
canonical output and accepts no caller-selected source or destination. Before
creating a lock or temporary tree it must reopen the actionable proposal,
require exactly the two canonical q1-v3 activation artifacts, reproduce the
activator's single verified requirement through the bound v3 verifier, require
the full-1G lease namespace absent, reserve its lock against a new run, and
revalidate the sealed 119-file q1 source and program lock. It then copies every
parent file, adds the four
reviewed midpoint files, proves the complete 123-file pre-patch closure,
applies the bound patch, and permits only five modified files, four additions,
zero removals, and 114 byte-identical parent files. The complete difference
and materialization receipts are bound to two new Draft 2020-12 schemas and
publish only through `renameat2(RENAME_NOREPLACE)` under an inode-owned sibling
lock.

The proposal may remain in `proposed` after activation or undergo the normal
single `claim` transition. The materializer normalizes only the exact
owner/state/claimed-at fields added by that transition before comparing the
original semantic digest; any other proposal mutation fails closed.

This materializer has not been invoked. Its AST, two schemas, and fourteen
planning bindings pass read-only checks, but the proposal is still dormant,
the q1-v3 qualification artifacts do not exist, the qm8 lease exists, and the
canonical output is absent. Therefore these artifacts prove only that a
fail-closed post-qualification source route is reviewable. No candidate tree,
build, fixture, codec arm, archive, scientific verdict, or Gamma byte credit
exists.

An independent adversarial audit correctly found that the legacy
`cmix_memory_safe_parent_qualification_verify.py` v1 surface trusts supplied
full-stream hashes and a supplied persistent-state boolean. That surface is
already revoked and is not the v4 dependency. The current v3 route reopens the
zero-authority v2 evidence verifier; v2 reruns the full-identity verifier over
the raw probability, coder, and state manifests and separately reruns the
Geekbench-bound runtime verifier. V3 then requires the exact activated
phase-11 plan and active policy. No authority rewrite is therefore warranted.
The remaining proof boundary stays explicit: probability identity covers every
modeled bit, persistent-state identity covers seven frozen checkpoints, and
runtime remains an unmet independent qualification artifact until measured.

At the authority-correction point, qm8 remained the sole substantial lane. Its
Arm A encode was live at `23.02%` with a `30,375,959`-byte progress payload;
the recorded maxima were `8,978,032 KiB` single-process RSS and
`8,998,152 KiB` process-tree RSS, and cgroup `max`, `oom`, and `oom_kill`
events remained zero.
No q1 full-corpus payload identity, inverse, terminal memory result, or parent
qualification exists yet, and no new proof experiment was launched.

During the later source-materializer review, the same untouched qm8 Arm A
encode advanced to `24.39%`. Its guard remained `running`; peak sampled tree
RSS was still `8,998,152 KiB`, peak cgroup memory was `9,002,086,400` bytes,
and cgroup `max`, `oom`, and `oom_kill` deltas were still zero. No encode-stage
or full-roundtrip receipt existed, so this observation changes no q1 authority.

## 2026-08-24 - Named-gradient lineage removed from the actionable scheduler

A read-only audit of the proposal selected after the q1 scheduler quarantine
found that `delta_midas_named_midpoint_gradient_65536_q0_v1` was not pending
science. Q0 and q1 ended in invalid implementation failures, q2 completed only
as a non-authoritative numeric diagnostic, and q3 then completed the exact
direct-F32 experiment with a valid terminal reflection. That reflection
refuted the prospectively frozen single-stable-deep-group hypothesis and
retired squared-gradient-energy localization on the production F population.

The proposal router had not projected that descendant result back onto the
four developed proposal records. Because absent `operational_status` defaults
to `actionable`, the ranker could select q0 even though its exact successor
lineage was already terminal. The records now encode the actual lifecycle:
q0 is superseded by q1, q1 by q2, q2 by q3, and q3 is retired with the exact
terminal-reflection digest. This is scheduling repair only. It changes no
candidate, source, experiment, receipt, archive, scientific conclusion, or
objective credit, and it authorizes no proof execution while qm8 is live.

The corrected rank then exposed the same metadata mismatch in
`gamma_safe_mix_v2`. Its interface, source contract, and revision-1 execution
plan all say `dormant_dependency`, `execution_authorized=false`, and require a
future activation revision binding qm8 terminal evidence, owned-lease
migration, process and namespace closure, and an exact toolchain. The developed
proposal omitted that operational state, so the ranker selected it as
actionable. The proposal now carries the exact dormant plan digest and blocker.
SAFE-MIX remains source-complete proof infrastructure with zero execution,
archive, inverse, compression, package-score, or objective authority.

The next rank exposed a different successor-routing defect. The unexecuted
bit-head DELTA-MIDAS v2 leaves CMIX's original memory policy intact, while the
already frozen v3 composes the identical `P/K/O/R/D/S` science with the sealed
PPM0 residency policy. V2 is now explicitly superseded by v3; v3 is dormant
until qm8 terminalizes and releases the proof lane. Neither has measured gain,
and the `4,013,707`-byte net figure is a forecast only.

The ranker previously propagated every non-actionable parent state into all
descendants, which also suppressed the exact child named by a parent's
`superseded_by` field. It now exempts only that explicitly designated direct
successor. Retired, dormant, or otherwise non-actionable successors remain
non-actionable themselves, and all other descendants still inherit the block.
This preserves lineage while allowing a future activated v3 to become
selectable without resurrecting v2. No proof process or candidate source was
changed.

The original `cmix_obias_ppm_always_purge_q0_v1` proposal is also not the
runnable resource gate. It binds the pre-disk experiment and declares a joint
output for which no matching adaptive job or result exists. The later frozen
`cmix_obias_ppm_disk_joint_q0_v3` contract instead binds separate clean and
PPM0 disk-backed runners, direct durable payload comparison, allocated-scratch
accounting, and a fail-closed joint evaluator. It has no proposal/candidate
materialization and no result. The original proposal is therefore superseded
by that correction identity rather than selected for execution. A future
materialization must remain dormant until qm8 releases the lane and must not
inherit any compression credit from this zero-savings infrastructure policy.

After these corrections, a fresh full proposal/reference derivation returns
`selected: null`. That is the intended fail-closed scheduler state while qm8
is the only live gate: no stale ancestor, retired oracle, dormant proof
envelope, or unmaterialized correction can be launched by ranking alone.

## 2026-08-23 - canonical CMIX/q1 interpretation and corrected launch ladder

This section supersedes any wording that implied CMIX had already been
repaired, qualified, or improved. The frozen evidence state is:

```text
External archive size reproduced:          true
External payload reproduced:               true
Arm A exact canonical inverse:              true
Arm B independent encode identity:          true
Arm B independent full roundtrip:           false
Arm B decode completion:                    false, terminated at 39.07%
External implementation memory eligible:    false
File-backed q1 probability identity:         proven on bounded scopes
File-backed q1 compression improvement:      none
File-backed q1 full-1G qualification:        unproven
Gamma authorship credit:                     0
Gamma score credit:                          0
```

Arm B reproduced the `107,730,531`-byte payload and `108,022,224`-byte
self-extracting archive exactly. That proves two-run encode identity under the
bound external package. It does not prove a second roundtrip: decode stopped at
`39.07%`. The shared-scope OOM was the immediate infrastructure termination,
and `/dev/shm` scratch aggravated the pressure, but the CMIX process was also
independently ineligible at `VmHWM=10,425,744 KiB`, `660,119 KiB` above the
strict `9,765,625 KiB` ceiling. The correct classification is therefore
infrastructure-terminated plus implementation resource failure, not a
compression-math failure and not an environment-only excuse.

q1 is an identity-preserving eligibility correction. It has matched exact
post-head integer probabilities, traces, payloads, and decoded output on three
cold 250KB scopes, one cumulative opening 1M scope, and opening plus distant
cold-reset 10M scopes. It has not proved full-stream probability or state
identity, full-1G archive identity and inverse, runtime eligibility, package
closure, or any archive-byte improvement. The interior reset populations prove
parent/q1 decoded-output identity, not standalone raw inversion.

The corrected next-launch ladder reserves headroom for a Gamma mechanism. The
next newly launched expensive q1 gate, if terminal evidence still requires one,
is a 100M identity and phase-resolved resource run. It must bind parent/q1
integer probabilities, payload/archive identity, exact raw inverse, rolling
persistent-state identity, process-tree RSS, per-process VmHWM, cgroup peak,
phase-specific mappings and buffers, and scratch logical/allocated bytes. Its
engineering gate is at most `9,000,000 KiB`, not merely below the official
`9,765,625 KiB` ceiling. The prospective, execution-disabled arm separation
and terminal branches are frozen in the
[`100M gate`](../operations/planning/cmix_filebacked_fxcm_100m_identity_resource_q0_v1.json).
At that gate, “archive identity” is split precisely: the parent and q1
arithmetic payloads must be byte-identical, while each self-extracting archive
must be exact, invertible, and separately package-accounted. The complete
self-extracting files are not expected to be byte-identical because q1
necessarily contains different allocator code; requiring that equality would
confuse predictor preservation with package identity.

The diagnostic observer source, matched observer-build runner, calibration
runner/verifier, and joint 100M coordinator/verifier are now sealed; all
execution receipts remain absent. The coordinator refuses an active full-1G
lease, independently hashes the canonical opening prefix before creating its
result root, then runs instrumented `I-P` and `I-Q` roundtrips followed by one
observer-free `R-Q` release roundtrip. `R-Q` is guarded by cgroup v2 at the
strict `10,000,000,000`-byte hard cap and a restorable `9,000,000,000`-byte
`memory.high` pressure boundary. Its eight ordered phases independently record
process-tree RSS, per-process VmHWM, cgroup memory composition, and scratch
logical/allocated peaks. The independent verifier reconstructs every semantic
state-manifest digest, validates exact observer checkpoint geometry, and proves
that the release executable is the literal concatenation of the independently
built q1 binary plus the sealed dictionary, article-order, and header assets.
No syntax, schema, or hash-closure check is an execution result.

A subsequent adversarial proof audit found and closed one pre-execution gap:
the verifier had validated the release-stage receipt and the resource-guard
receipt independently without proving that they described the same child
command. The verifier now recomputes the guard's NUL-delimited argv digest and
requires it to equal both the release-stage command digest and the `R-Q` arm
binding. It also rehashes the soft-high wrapper's underlying v3 guard, binds
the wrapper and guard to the same cgroup path/inode and `memory.events.high`
count, and independently matches the raw 16-event phase-marker stream to the
eight ordered phase records. Both instrumented arms now schema-validate their
v2 guard receipts and bind the exact encode/decode argv, diagnostic labels,
limits, sampling, disk, and affinity observations. These are prospective proof
hardening changes only; they add no execution evidence or compression credit.
The same audit found that this detailed plan still named the generic dormant
campaign schema despite not conforming to it. The plan now validates against a
dedicated strict schema whose digest is pinned independently by both the
coordinator and verifier; the plan also carries that digest explicitly.
Observer build, observer calibration, calibration verification, joint
coordination, and joint verification now all invoke the same schema-pinned
plan validator before accepting or producing evidence.

The build runner requires two byte-identical builds within each I-P/I-Q arm
before packaging replicate A. The observer registers the
same source-ordered semantic ranges in both arms and requires exactly `26`
allocations of at least `67,108,864` bytes. At coded-byte checkpoints `0`,
`16,777,216`, `33,554,432`, `50,331,648`, and terminal, it hashes each range's
ordinal, requested semantic size, alignment, and exact semantic bytes. It also
hashes every post-head `uint16` probability immediately before the arithmetic
split and records clone-finalized coder checkpoints. Virtual addresses,
mapping padding, filenames, inode identities, page residency, and fault history
are excluded. The q1 diagnostic arm may page out already-hashed file-backed
ranges; therefore neither diagnostic arm has memory authority. The independent
`R-Q` arm remains the observer-free sealed release. Exact `--fuzz=0` patch
application and frozen-definition C++ syntax validation pass; no observer build
has been executed, and no calibration, 100M identity result, or resource result
is claimed.

Semantic-coverage audit: q1 can enter `AllocateBacked` only through the two
`fxcmv1.cpp` allocation templates, `alloc` and aligned `alloc1`, and only at
the same 64 MiB threshold used by the observer. The observer hooks both the
file-backed and ordinary allocation branches after allocation. `alloc` hashes
the exact requested object extent; `alloc1` hashes the aligned data pointer and
exact usable extent while excluding allocator/alignment padding. `Begin` then
requires all 26 runtime registrations before coding can start. Thus every
allocation whose storage implementation q1 changes is inside the state
manifest, while non-semantic mapping slack remains correctly excluded.

`cmix_filebacked_fxcm_full_a_qm8_v1` was already running when this launch-order
correction was adopted. It remains an unchanged zero-credit diagnostic and is
not killed or retroactively promoted. No new independent full-1G arm or native
compression mechanism is launched from bounded identity evidence alone. An
identity failure authorizes only first-divergence localization; identity with
insufficient headroom authorizes one phase-specific memory successor; failure
to create useful headroom moves the prize-facing primary lane to the compact
open NNCP student. New CMIX midpoint, MIDAS, SAFE-FORK, or structural mechanisms
remain execution-blocked until q1 is an exact memory-safe parent. Their eventual
archive effects require fresh joint replay and cannot be added algebraically.

### Midpoint persistence attribution v1 is superseded; correction-only v2 is frozen

A pre-execution authority audit found that the original
`cmix_obias_midpoint_persistence_attribution64_q0_v1` cannot validly execute.
It names `cmix_obias_full_midpoint_oracle64_q0_v1`, which was already
superseded before execution because the donor CMIX update horizon is 128
events and therefore cannot be invoked unchanged at a 32-event midpoint. The
v1 attribution also allowed its persistent branch to name a compact
curvature/tangent successor without first binding functional-JVP evidence. No
v1 proposal, source candidate, archive, or scientific result exists. Its
immutable supersession receipt records zero score credit.

Correction-only
`cmix_obias_midpoint_persistence_attribution64_q0_v2` now binds the actual
source-defined 32-event truncated-BPTT oracle v2 and the exact q1 qualification
policy v4. Its P/F/J/S comparison preserves the original scientific question
and the preregistered `0.80` threshold. J must reproduce F's aligned update and
adapted probability/state trajectory through byte 63 while a simultaneously
advanced untouched branch reproduces P. At the join, every adapted
probability-affecting write is discarded, the untouched parent state is
retained, and the arithmetic coder interval is neither forked nor rewound.
Truth-only storage may be shared only after a source and writable-alias audit;
copy-on-write, sparse journals, or recomputation are implementation choices,
not weaker state semantics.

The execution ladder begins with a 250KB exactness/rejoin gate; a pass
authorizes only 1MB calibration, and a target-scale causal 1MB pass authorizes
only the 10MB attribution. The decisive test is exact integer arithmetic on a
fresh 10MB P/F/J/S joint archive: `F_gain = archive(P)-archive(F)`,
`J_gain = archive(P)-archive(J)`, and local retention passes exactly when
`5*J_gain >= 4*F_gain`. F must still save at least `40,793` bytes and beat its
frozen shifted S control. A retention pass authorizes only SAFE-FORK source
materialization. A retention miss authorizes only functional-JVP persistence
attribution; it cannot directly authorize a persistent codec.

The planning contract, current structured experiment, oracle authority
interface, receipt and verification schemas, and independent arithmetic/hash
verifier are frozen. Adaptive proposal
`cmix_obias_midpoint_persistence_attribution64_q0_v2` is explicitly
`dormant_dependency`: it cannot be claimed until q1 has a positive terminal
policy-v4 qualification decision and the shadow midpoint oracle v2 has a
positive terminal 10MB decision. No execution, source candidate, archive gain,
compression credit, or score credit is claimed.

The historical mutation router and SAFE-FORK v1 contract also named the
superseded attribution. Router v2 now binds the corrected oracle, attribution,
sealed SAFE-MIX v2 wrapper, and one-successor ladder. SAFE-FORK v1 is
explicitly superseded before execution; only a positive 10MB attribution-v2
receipt may authorize materializing one new SAFE-FORK v2 source candidate.

### Source-level closure supersedes midpoint oracle v2 and its attribution dependency

A direct audit of the sealed q1 C++ source found that shadow midpoint oracle
v2 was still not implementable as written. `Predict(x_t)` writes the
distribution for `x_(t+1)`, and the corresponding target is installed only by
the later `Perceive(x_(t+1))`. Therefore the recurrent forward rows for a
nominal first half `x_s..x_(s+31)` do not have 32 decoder-visible losses until
`x_(s+32)` has already been coded. The old contract incorrectly treated byte
32 as both unavailable future truth and an adapted prediction.

The source exposes four additional blocking ownership facts. Native recurrent
`BackwardPass` keys its accumulator reset, complete dense-gradient sweep, Adam
step, and shadow refresh to epochs 127 and 0, so it cannot become a local-32
pass by changing one loop bound. Native `ForwardPass` writes the 128-event
history tape later consumed by the ordinary update, so rebuilding through that
entry point would silently replace already coded evidence. `HHistRow(epoch_)`
must retain the pre-replay hidden feature that actually predicted the closure
byte; recording rebuilt hidden state there would pair the ordinary pending
error with the wrong feature. Finally, a live mid-burst parameter update means
the later ordinary boundary sees histories from multiple parameter versions,
which v2 never interpreted.

The complete read-only finding is bound to q1 source closure
`e2aaf037...f628f`, program lock `edd1252e...f5787`, and release binary
`610edd6a...8808`. No v2 program, build, arm, archive, inverse, or scientific
result exists. Oracle v2 is now superseded before execution rather than
silently completed. Because persistence-attribution v2 defined F/J/S by exact
identity to that obsolete trajectory, it is also superseded before execution;
its exact `5*J_gain >= 4*F_gain` scientific question remains unmeasured.

Correction-only `cmix_obias_shadow_midpoint_oracle64_q0_v3` freezes the first
source-complete realization. Sixty-four-event segments align with native
128-event phases: snapshots occur at phases 0 or 64 after any ordinary
phase-zero update, and closure hooks occur at phases 32 or 96. At entry to
`Perceive(x_(s+32))`, byte 32 remains parent-coded, the exact 32-loss target
vector is `x_(s+1)..x_(s+32)`, and the first adapted probability is emitted by
the subsequent normal `Predict(x_(s+32))` for byte 33. This honestly leaves 31
affected bytes per complete segment.

The v3 gradient copies the native window into detached storage, reconstructs
each event-time output matrix from the burst base and all absolute-phase
pending rank-one factors, and runs a new local-32 backward path with temporal
adjoints zero outside the window. F/S commit one donor-order recurrent Adam
step followed by one output SGD step and refresh the exact fp16 shadows; K
performs the same update arithmetic on detached copies. Replay restores only
the segment-start hidden/cell state and uses a new state-only forward primitive
that cannot write native tape, epochs, loss, optimizer, mixer, SSE, context, or
coder state. The ordinary pending output feature for the already coded closure
byte is explicitly preserved from before replay.

The later native 128-event update keeps its source call site and cadence. v3
defines it transparently as the existing current-boundary approximation over
mixed-version history; it does not claim an unchanged or exact
historical-weight graph. The P/K/F/S Mechanism IR and current structured
experiment are frozen, and the adaptive proposal is `dormant_dependency` on a
positive independently verified q1 policy-v4 qualification. The first gate is
250KB exactness and strict F-over-P/F-over-S ordering; 1MB requires `4,080`
bytes, and 10MB requires `40,793` bytes plus positive original-coordinate
thirds. No source candidate, compile, execution, archive gain, compression
credit, or score credit exists. Router v3 permits a corrected persistence
attribution identity only after a valid positive 10MB v3 oracle.

### Live qm8 residency attribution and corrected bounded-to-full routing

A read-only live snapshot at `2026-08-24T03:14:27Z`, with the encode progress
log at `9.07%`, resolves the main q1 residency ambiguity without modifying the
running process. The guard still reported no hard-cap, OOM, or OOM-kill event;
its retained peaks were `8,534,408 KiB` process-tree RSS,
`8,518,220 KiB` CMIX `VmHWM`, and `9,002,086,400` cgroup bytes. The snapshot
itself is diagnostic and non-terminal: completion, inverse, cleanup, and the
soft-high verifier remain required.

The 26 file-backed FXCM mappings can be identified exactly from constructor
order and allocation geometry. Ordinal 0 is the match-position hash;
ordinals 1--3 are the three at-least-64-MiB `DirectStateMap::CxtState`
arrays; ordinals 4--7 are the four at-least-64-MiB mixer weight arrays; and
ordinals 8--25 are the eighteen at-least-64-MiB `ContextMap3` bucket arrays.
At the snapshot their aggregate `smaps` values were:

| Semantic group | Mappings | Size KiB | RSS KiB | Referenced KiB | Private-dirty KiB |
|---|---:|---:|---:|---:|---:|
| match-position hash | 1 | 65,540 | 65,536 | 65,536 | 36,288 |
| direct-state arrays | 3 | 589,824 | 589,824 | 589,824 | 107,068 |
| mixer weights | 4 | 419,856 | 238,436 | 170,604 | 27,148 |
| context-map buckets | 18 | 4,850,024 | 4,849,664 | 4,847,636 | 942,292 |
| total | 26 | 5,925,244 | 5,743,460 | 5,673,600 | 1,112,796 |

The separate `14,336,000 KiB` PPM virtual mapping held only `75,956 KiB`
RSS. CMIX anonymous RSS was about `2,456,736 KiB`. Thus the live pressure is
not a runaway PPM residency bug: it is predominantly the deliberately broad
FXCM context-table working set plus persistent anonymous model state. Only
the mixer group was materially nonresident. Targeting those already-reclaimed
pages has an observed ceiling of roughly `181,420 KiB`; it cannot by itself
produce a large memory reduction.

This evidence rejects connecting q1's dead blanket cadence as the default
successor. `PageOutAll()` would scan every mapping each modeled MiB and evict
tables whose pages are almost all being referenced, converting the same
semantic working set into refault and writeback churn. If qm8 terminalizes
with insufficient headroom, the single correction must instead target the
actual high-water mechanism: either one source-attributed allocation or an
exact bounded semantic-page arena that preserves table bytes while controlling
its resident cache. That is a prospective direction, not an authorized
candidate and not compression credit.

Planning revision 2 also closes a routing error. An opening-100M pass can no
longer blindly authorize an unchanged full-1G q1 run. It must be joined to
qm8's terminal class: exact and engineering-clean qm8 permits one independent
unchanged repeat; exact but headroom-failing qm8 permits one attributed
residency successor; infrastructure-incomplete qm8 permits only a retry after
the exact infrastructure cause is corrected. Bounded evidence may not erase
contrary full-corpus evidence.

### Mechanism IR managed-lane audit finds a two-sided ownership defect

Mechanism IR v3 had a pre-execution activation contradiction. All five v3
entry points required `exclusive_full1g.json` to be a regular JSON file with
`active=false`, but the canonical managed lease has no `active` field and
represents release by removing both the lease and `.lock` paths. Thus v3
rejected the live lane correctly but could never execute after a clean managed
release. No compiler arm or archive had run.

Candidate `gamma_mechanism_ir_v3_managed_lane_q0_v1` implemented the smallest
prospective correction: exact `O_EXCL|O_NOFOLLOW` ownership of the canonical
`.lock` namespace, retained directory/lock descriptors and random token,
inherited ownership witnesses for compiler-verifier children, all inherited
v3 causal controls, and a truthful wrapper-to-upstream compiler provenance
projection. Before execution, a harder competitor audit refuted the exact
wrapper. The bound `c3cedd46...` `ManagedExclusiveLease.acquire()` catches an
`O_EXCL` collision in a broad exception handler and unconditionally unlinks
the `.lock` path without proving that this call created it. A competing
full-1G acquisition can therefore delete the wrapper's foreign lock. This is a
source-level transaction bug, not an environment condition and not a
compression result.

The counterexample is frozen in
[`static rejection`](../operations/planning/gamma_mechanism_ir_v3_managed_lane_q0_v1.static-rejection.json).
The rejected implementation is preserved at candidate tree
`6d020fb1d3d2e04ec937c1117c3f56cabb98e11e4c91f491e04e912edc8211b7`;
it was not executed and receives zero infrastructure promotion, compression,
or score credit. This rejects only wrapper-only ownership against the current
manager, not Mechanism IR's P/K/D/M/R/S causal semantics.

Exactly one successor is authorized:
`gamma_managed_exclusive_lease_owned_cleanup_q0_v1`. Its prospectively frozen
transaction changes only acquisition/release ownership. An `O_EXCL` collision
closes local descriptors without touching the existing name; successful
creation retains directory and lock descriptors, device, inode, single-link
count, PID, and a random 256-bit token; terminal release removes the exact
owned lease while the lock still excludes competitors, then removes only the
reproved owned lock. Ambiguous post-publication failures remain occupied for
audit. Lease fields, transitions, descendant/signal rules, verifier semantics,
and public API remain unchanged.

The separate successor source is sealed at tree
`eb9c5f669cf05cbe1b361065ff4faefbe70fcea905c14e2483e6e97427ad1a44`.
It includes unexecuted normal/reacquire, foreign-lock, second-manager,
symlink, post-acquire appearance, inode, hardlink, token, partial-publication,
schema, and normalized replay controls. The current
`tools/managed_exclusive_lease.py` remains byte-identical because qm8 is live.
No control, canonical migration, Mechanism IR operation, or substantial gate
may run until qm8 terminalizes and releases both namespace paths. Static AST,
JSON, schema, source-set, candidate-budget, and adaptive-contract validation
pass; those checks are not execution evidence.

A later read-only qm8 snapshot at `16.80%` remains non-terminal. CMIX
`VmHWM` is `8,986,384 KiB`, current RSS was `8,366,460 KiB`, and cgroup peak
is `9,002,086,400` bytes. `memory.events` records `166,799` high-pressure
events but zero `max`, OOM, or OOM-kill events. Progress continued while the
process alternated runnable and disk-wait states. Combined with the previously
measured direct reclaim, file-cache refaults, and 26 mapping residency, this is
implementation-level working-set and page-reclaim pressure from file-backed
CMIX, not the old `/dev/shm` placement error recurring. Exact payload,
inverse, cleanup, runtime, and qualification remain unknown until terminal
receipts exist.

The ownership successor now also has a frozen post-qm8 execution closure,
without executing the candidate. The coordinator requires the exact qm8 Arm-A
terminal-receipt path, independently rejects any remaining qm8 or
exclusive-lane controller process, and requires both canonical namespace names
to be absent. A guarded worker then
loads the sealed candidate manager by exact path, acquires the canonical lane,
runs all 13 local controls in a child with a fixed environment, preserves a
complete scratch-tree manifest, freezes terminal lease evidence, and releases
the lane. The outer coordinator rederives the nine registered measurements and
promotion gates from the controls and guard-v3 receipt. A separately bound
verifier reopens the candidate revision and immutable blobs, every plan source,
the dynamic qm8 terminal receipt, the scratch tree, phase-marker sequence,
outer transition hash chain, exact result manifest, resource peaks, and
zero-credit authority boundary. A harder static audit found that revision 1's
`execution_authorized=false` declaration was not enforced by the coordinator
and was incorrectly required by the worker. The closure now fails closed: the
current revision-1 plan cannot launch, and every entry point requires a future
revision-2 activation with `execution_authorized=true`, the activated status,
and the actual qm8 terminal-receipt SHA-256. No result directory or control
receipt exists while qm8 owns the host.

At the latest read-only sample the encode had advanced to `17.40%`. Cgroup
current use was `8,999,227,392` bytes with the same `9,002,086,400`-byte peak;
`memory.events.high` had reached `180,490`, while `max`, OOM, and OOM-kill
remained zero. The split was about `2.55 GB` anonymous and `6.23 GB` file,
including about `6.01 GB` mapped file state. This strengthens the same
non-terminal attribution and does not qualify q1.

The terminal proof route is now symmetric for success and failure. The
existing soft-high verifier accepts only a terminally passing qm8 arm; the
older failure verifier was specific to qm7's exact hard-cap event. A new
prospective qm8 failure verifier can classify any schema-valid terminal Arm-A
failure through one ordered branch: hard-cap/OOM, RSS/decimal memory, other
resource limit, payload identity, decode/inverse, cleanup/lease, encode/stage,
or otherwise unclassified infrastructure. Exactly one correction route is
selected, and every branch retains zero promotion, parent-qualification,
archive, compression, and score authority.

Revision 1 is deliberately dormant. The verifier itself refuses to run until
a future revision at least 2 binds the actual failed terminal-receipt SHA-256,
sets the activated status and execution authority, and observes no remaining
qm8 process. The preflight occurs outside the receipt-writing exception path,
so an early invocation cannot poison the canonical output name with a
verification-failure file. The verifier reopens exact antecedent contracts,
package concatenation, stage and guard commands, result/scratch ownership,
soft-high state, outputs, managed-lease transitions, cleanup state, and its own
strict output schema. The plan validates against the campaign static-contract
schema and binds the Python runtime plus all source and schema files by byte
count and SHA-256. The new output schema is self-validated but is not yet added
to `research_contracts.py`, because qm8 imported that file before launch and
live source integrity takes precedence. No verifier execution or output
receipt exists. At the sealing snapshot encode progress was `18.02%`, cgroup
current use was `8,999,391,232` bytes, peak was `9,002,086,400` bytes, and
`memory.events.high` was `192,968`; hard-cap and OOM counters remained zero.

A symmetric audit then found the same dormant-output hazard in the older
passing-arm verifier. Its planning file named the campaign static-contract
schema without conforming to it and declared immediate execution authority;
its caught missing-source path could write `full-soft-high-verification.json`
before qm8 terminalized. That route is now fail-closed as well. The corrected
revision 1 is dormant and schema-valid, and preflight requires a future
revision at least 2 with the exact passing terminal-receipt hash, explicit
activation, Arm A `terminal_pass=true`, and process closure before the output
path can be opened. The verifier also reconstructs both guarded stage commands,
binds exact result and scratch ownership, rederives aggregate resource and
accounting fields, verifies managed-lease transition semantics, and validates
its output against the registered schema. No success-verification output or
Arm B authority exists while qm8 is live.

The post-audit read-only qm8 sample remains non-terminal at `18.57%` of the
encode. The codec, stage, nested guards, coordinator, and adaptive owner remain
live. Cgroup current use is `8,998,580,224` bytes and the peak remains
`9,002,086,400` bytes; `memory.events.high` has reached `205,484`, while
`max`, OOM, and OOM-kill remain zero. The codec is still alternating runnable
and disk-wait states under a one-CPU guard. This is continued pressure evidence
only: payload identity, inverse, cleanup, runtime, and q1 qualification remain
unknown until the terminal receipt and the matching independent verifier exist.

### qm8 terminal dispatch now has an independently closed authority boundary

The first receipt-to-verifier dispatcher draft was rejected before execution.
Its process scan excluded ancestors and could miss an orphan native `./cmix`;
branch and digest evidence came from separate receipt reads; its planning lock
did not reserve the canonical full-1G namespace; and it supplied neither a
durable intent nor a reconstructive predecessor after plan publication. A
second audit also found that the verifiers trusted too little of the dispatch
chain and wrote their canonical outputs before releasing the full-1G lock.

The corrected shared closure keeps one no-follow terminal-receipt descriptor
from schema validation through branch selection and verifier output. Verifiers
consume that parsed value rather than rereading the receipt pathname. It checks
every available recorded PID/start identity and scans all processes for the
candidate, result, scratch, and cgroup tokens, scratch cwd, and cgroup
membership. Only a shell-launcher ancestor whose sole match is its embedded
command is ignored. Native codec closure therefore does not depend on the
terminal lease recording an optional codec PID.

The dispatcher now holds both an exact planning lock and the canonical
full-1G acquisition lock. It checks both verifier outputs before locking,
after both locks, and before activation-receipt publication. One durable intent
binds the descriptor-witnessed receipt, both branch templates, both locks, and
the pre-publication closure. `RENAME_EXCHANGE` changes only the selected plan
and retains the exact displaced dormant inode at a deterministic recovery
path. Independent verification reverses `revision`, activation status,
execution authority, and terminal-receipt SHA-256 from the activated JSON and
requires the exact frozen dormant bytes and digest. The non-selected plan must
remain identical.

Canonical verifier authority is also ordered correctly. Each verifier prepares
and fsyncs its complete schema-valid receipt while holding the full-1G lock,
releases that lock, and only then publishes the canonical pathname with
`RENAME_NOREPLACE`. A release failure cannot leave a passing receipt that could
authorize Arm B. Both verifier paths require the exact frozen Python runtime
and argv. The dispatcher itself imports no subprocess or signal facility and
cannot execute a verifier or Arm B.

Static AST, schema-meta, plan-schema, serialization, recursive binding, branch
hash, and diff checks pass. The independent audit found no remaining route to
premature verification or Arm-B authority. The remaining non-authority gap at
that snapshot was an executable post-intent recovery transaction; it is closed
by the separately frozen recovery source below. Six directly validated
dispatch/recovery schemas are not yet in the shared `research_contracts.py`
registry because that module is part of the live qm8 closure.

No dispatcher, verifier, recovery path, test, Arm B, or new proof workload ran.
At the frozen review snapshot qm8 Arm A was still encoding at `25.64%`; peak
process-tree RSS was `8,998,152 KiB`, cgroup peak was `9,002,086,400` bytes,
and max, OOM, and OOM-kill events remained zero. No live process, candidate,
lease, cgroup, result tree, or scratch tree was modified or signaled. The
corrected audit and review remain zero-credit infrastructure evidence.

### qm8 terminal dispatch now has an inode-bound crash-recovery transaction

`cmix_filebacked_fxcm_full_qm8_terminal_dispatch_recover.py` is frozen for the
only two legitimate interrupted-dispatch outcomes. With no activation receipt,
it accepts only the exact dormant/absent, activated/dormant, or
dormant/activated selected/displaced plan state and rolls back to both frozen
dormant plans. With a valid activation receipt, it independently revalidates
the complete activation chain and leaves every authority-bearing artifact
unchanged. The action is rederived on every resume; a preparation cannot label
a committed activation as rollback.

The transaction ID is the SHA-256 of the immutable dispatch intent. Before any
rename it publishes a preparation, verifies that the original owner PID is
dead, and rescans recorded identities, all process argv/cwd/cgroup bindings,
cgroup occupants, and lease ownership under the surviving full-1G lock. It
rescans again immediately before completion. Rollback requires both exact
locks. Committed recovery additionally recognizes the dispatcher-ordered crash
state where the planning lock was already released but the exact full-1G lock
survives.

An uncommitted exchange is reversed with `RENAME_EXCHANGE`; any aborted
activated inode and the original intent move to transaction-addressed archive
paths. A durable completion is published while descriptors for every surviving
lock remain valid. Only then may the exact path/device/inode/link-count/payload
identity be unlinked, followed by a finalization after both lock paths are
absent. The preparation/completion split also permits resumption after a crash
inside recovery itself.

The [`recovery contract`](../operations/planning/cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_recovery_q0_v1.json),
three strict receipt schemas, source, and
[`static review`](../operations/planning/cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_recovery_review_q0_v1.json)
are hash-bound. AST, schema-meta, rollback/committed/partial-lock instance,
campaign-plan, artifact-binding, and diff checks pass. No recovery, dispatcher,
verifier, Arm B, or proof workload ran. At the review snapshot qm8 was still
encoding at `26.17%`; peak tree RSS remained `8,998,152 KiB`, cgroup peak
`9,002,086,400` bytes, and max/OOM/OOM-kill events remained zero. This closes
a liveness/provenance gap only and receives zero compression and score credit.

### q1 qualification authority is artifact-derived, not self-reported

An independent adversarial audit found a fatal consolidation weakness before
any q1 qualification receipt existed. The v1 verifier compared hashes and
booleans supplied inside one summary receipt, but did not reopen the full A/B,
phase-11, runtime, and dependency artifacts that those values purported to
summarize. In particular, `persistent_state_identity_pass` and runtime
eligibility could be asserted without a mechanically bound phase-11 or
Geekbench receipt. Downstream dormant tools treated `verified=true` plus
`qualified=true` as sufficient even though v1 declared no promotion authority.

The v1 consolidator and both v1 receipt schemas are now fail-closed: they can
only represent `qualified=false`, and the planning policy is superseded. The
replacement v2 input is only a router
to nine immutable artifacts: A receipt/verification, B receipt/verification,
full identity receipt/verification, runtime receipt/verification, and complete
dependency closure. It contains no qualification decision fields. The v2
verifier reopens those files, checks each router reference's declared byte
count and SHA-256 without symlink or hard-link aliases, validates schemas, and
rederives A/B package, payload, archive, inverse, resource, package-accounting,
and license conclusions. It reruns the A/B, phase-11, and runtime verifiers and
requires their recomputed outputs to equal the supplied verification receipts
exactly. It requires at most `9,000,000 KiB` A/B process-tree
RSS, strictly less than `10,000,000,000` cgroup bytes, and exact package
identity across the diagnostic, runtime, and counted dependency artifacts.

Runtime now has a separate proof shape. Its verifier parses exactly one
single-core score from retained raw output identifying Geekbench 5, requires
the compression and decompression guard commands to name the exact packaged
compressor/head/archive, recomputes each wall limit as `252000000 / score`, and
requires complete guard-v3 memory, disk, affinity, cgroup, phase, and elapsed
measurements. Diagnostic qm8 timing cannot satisfy this contract.

Phase 11 now states its narrower legitimate claim. It can prove continuous
byte-zero post-head integer-probability identity and exact coder checkpoints.
For q1-mutated persistent storage it freezes state digests at modeled-stream
indices `0`, `16,777,216`, `33,554,432`, `50,331,648`, `100,000,000`,
`500,000,000`, and the dynamically observed terminal modeled byte. These are
checkpoint identity, not continuously observed state-trajectory identity. The
raw corpus remains exactly `1,000,000,000` bytes but is a different coordinate;
retained full preprocessing currently yields `934,220,701` modeled bytes. The
independent verifier also requires retained
opening/distant 10M calibration equality, observer-off/on payload identity,
a differing pre-head negative control, a detected single-byte state mutation,
and rejected checkpoint omission/reordering controls.

SAFE-FORK memory admission and the frozen WIKI-SCHEMA-VM runner now accept only
a positive v2 verification with
`claim_authority=memory_safe_external_parent_only` and
`promotion_authority=true`. No v2 router, phase-11 arm, runtime receipt, or
qualification verification has been executed. This closure changes no archive
measurement and grants zero Gamma compression or score credit.

### Source-bound runtime producer and corpus-independent decode closure

A further pre-execution audit found that the dormant runtime design still did
not implement the proof it described. It had receipt schemas and an independent
verifier, but no producer, no exact executable plan, no managed-lease binding,
and no transitive source closure. More importantly, the generic full-stage
wrapper accepted the canonical enwik9 path in both modes. Its decode subprocess
ran only the self-extracting archive, but the timed wrapper itself first read
and hashed the original corpus. That is conservative for elapsed time but is
not a clean proof that decompression receives only the archive.

Runtime contract revision 2 closes those gaps before any execution. The
dedicated coordinator requires two independently verified, byte-identical q1
full roundtrips; an exact Arm-A package; one retained raw Geekbench 5 report;
the current host fingerprint; absent result, scratch, cgroup, and lease paths;
and the plan-bound working directory and command vector. It acquires the
managed exclusive full-1G lease, runs compression and decompression under the
v3 process-tree/cgroup/disk/affinity guard, and derives each phase limit as
`252000000 / single_core_score`. Compression must reproduce the A/B payload
and self-extracting archive before decode can begin.

The new runtime stage has an asymmetric information contract. Encode receives
the canonical corpus, packaged compressor, and head. Decode receives only the
newly generated archive and runs exactly `./archive9`; no original-corpus path
appears in its stage argv or codec argv. The restored output is then checked
against the fixed `1,000,000,000`-byte identity and canonical SHA-256. Hashing,
copying, wrapper startup, codec execution, output validation, and receipt
creation all remain inside the guarded elapsed interval, making the runtime
measurement conservative without giving the decoder forbidden information.

The independent verifier now reconstructs every stage and guard argv, the
coordinator argv, and their NUL-delimited hashes from the sealed plan. It
reopens both full arms and their verifications, rederives A/B/package/output
identity, reparses the Geekbench report, re-fingerprints the host, validates
the managed-lease transition hash chain and cleanup, and rejects any corpus
path in the decode command. The producer records pre-run source bindings and
terminally rejects source, plan, antecedent, package, population, or report
drift. Success removes scratch and releases the lease; failure preserves
scratch and emits a false receipt when execution has begun.

The exact runtime execution surface is a 145-member Python/research-schema
closure rooted at the coordinator, independent verifier, corpus-independent
stage, and v3 resource guard. The opening-100M and phase-11 closures, now 150
and 148 members respectively, were mechanically resealed because the shared
contract registry reaches the revised runtime schemas. Qualification policy v4
supersedes v3 for future authority and binds this producer, stage, plan,
schemas, verifier, lease semantics, and source closure. No Geekbench run,
runtime stage, full q1 arm, qualification receipt,
compression improvement, authorship credit, or score credit is created by this
static closure.

### Phase-11 modeled-coordinate repair and executable observer closure

A pre-execution audit found that the old full-identity schemas could never
correctly describe the intended run. They required the terminal arithmetic
checkpoint to be coded byte `1,000,000,000`, but the observer counts bytes only
after CMIX preprocessing. Retained full q1 scratch proves the coordinates
differ: the canonical raw corpus is `1,000,000,000` bytes and `.ready4cmix` is
`934,220,701` bytes. Opening 10M calibration is `5,766,051` modeled bytes.
This was a contract error, not predictor evidence.

The repaired observer binary now carries fixed modeled checkpoints at
`16,777,216`, `33,554,432`, `50,331,648`, `100,000,000`, and `500,000,000`.
The last two are enabled only by
`GAMMA_FULL_IDENTITY_EXTENDED_CHECKPOINTS=1`. Calibration and opening-100M
omit it, so their geometry remains start, the first three fixed points, and
terminal regardless of transformed length. Full arms set it and produce seven
records: start, five fixed points, and a terminal point required to equal the
bound transformed-stream artifact. This is the same calibrated binary, so no
second observer build or compiler-equivalence assumption is needed.

The opening-100M harness now has its own exact transitive Python
and research-schema closure rooted at its coordinator, identity arm,
independent verifier, release stage, observer build, calibration runner, and
calibration verifier. This is deliberately separate from the retained q1
`source_closure`, which binds the candidate implementation rather than the
orchestration code. The observer build and calibration each validate and record
the closure before creating their output roots; calibration requires the build
to carry the same closure. The coordinator rejects a path/hash, stale-stage, or
closure mismatch before creating its result root, the joint receipt records the
harness closure as an antecedent, and both independent verifiers rederive the
same ordered closure.

The full arm runner, sequential parent/q1 coordinator, strict plan schema, arm
and joint schemas, and independent verifier are now source-complete and
content-addressed. Each arm is single-CPU, owns disjoint result, scratch, and
backing roots, requires descent from the coordinator's exact owned full-1G
lease, retains its transformed stream and raw observer manifests, and is
bounded by an `11,500,000 KiB` diagnostic
guard. That higher guard is deliberately non-authoritative: the external parent
is already known to violate prize memory, and hashing semantic ranges faults
pages. qm8 A/B remain the only resource authority.

The independent verifier does not trust arm summaries. It reparses every
probability, coder, and 26-range state record; reconstructs ordered aggregate
digests; reopens the observer build and calibration; reruns the opening-100M
and full A/B verifiers; and independently rejects omitted, duplicated,
reordered, wrong-count, and wrong-terminal checkpoint controls. Full execution
remains disabled until qm8 A, an independent B, observer calibration, and the
opening-100M gate all terminalize as passes.

The prospective phase-11 Python execution surface is also frozen as an exact
transitive closure rooted at the coordinator, arm runner, and
independent verifier. It includes every recursively imported project-local
Python helper and, because the contract registry is reachable, every research
contract schema the registry can resolve. Both execution and independent
verification recompute the ordered path/digest rows. Any omitted, added,
reordered, or hash-divergent row rejects the evidence before identity authority
is interpreted; direct top-level script hashes alone are no longer accepted as
complete implementation provenance.

Qualification policy v2 is preserved byte-for-byte because the dormant
WIKI-LOOM proposal already hash-binds it. New policy v3 supersedes v2 only for
future qualification authority and binds the corrected seven-checkpoint plan
and implementation. None of these static repairs is a run, archive saving,
Gamma authorship credit, or score credit.

### Phase-11 full identity now owns its serialized lane

A harder audit rejected phase-11 revision 5 before execution. The coordinator
and each full arm called only `require_released_lease()`: all three observed an
absent path, but none acquired it. A competing full-1G workload could claim the
lane after any check, so sequential parent/q1 probability and state equality
would not have been produced under an exclusive execution contract. The plan
also required `execution_authorized=false`, making dormancy an execution
precondition instead of a barrier. This was an algorithm-harness ownership
error, not a host environment failure and not compression evidence.

Revision 6 replaces that path with a source-bound owned transaction. It is
still dormant and the coordinator refuses it: only a future revision at least
7 with `execution_authorized=true`, the activated status, and an exact passing
verification for `gamma_managed_exclusive_lease_owned_cleanup_q0_v1` can
execute. The activated coordinator atomically acquires the canonical full-1G
namespace once, retains the lease across both arms, heartbeats while each child
runs, and releases only after both terminate. Each arm now requires the exact
lease ID, owner PID/start tick, coordinator result/scratch roots, a live owner,
an owned lock path, and its own process descent from that owner. Both arm
receipts freeze the same witness.

Terminal authority is independently rederived. The joint receipt binds the
managed-lease activation verification, terminal lease evidence, and transition
chain. The independent verifier reruns the generic transition verifier, checks
the coordinator source and command bindings, compares both child witnesses,
requires the evidence and transition files inside the result root, and rejects
residual canonical lease, lock, or scratch paths. `exclusive_lane_pass` is now
a required conjunct of full identity.

The contract changes rebound the opening-100M, full-identity, and runtime
Python/schema closures to `154`, `153`, and `149` members. Qualification policy
v5 supersedes v4, explicitly revokes v4 future authority, and marks every
downstream candidate still binding v4 as stale until it receives a separately
identified activation successor. No manager control, parent arm, q1 arm,
verifier, codec, or proof experiment ran; qm8 still owns the host lane. All
Gamma compression and score credit remain zero.

### q1 qualification revocation is now enforced by the verifier

A follow-on call-graph audit found that policy v5's revocation was descriptive
but not executable. `cmix_memory_safe_parent_qualification_verify_v2.py`
accepted only the evidence router, lease namespace, and output path. It neither
accepted nor emitted a policy binding. The dormant FOSSIL-MATCH and WIKI-PDA
v2 runners invoked that exact verifier independently while separately
requiring policy v4. Consequently, a future complete evidence router could
have produced `qualified=true` through the v2 executable and then satisfied a
v4-bound successor even though v5 declared that route stale. No such router or
positive qualification receipt exists; this was a prospective authority bug,
not fabricated evidence and not a codec failure.

The v2 verifier now remains a complete artifact reopener but always appends
the exact failure `qualification authority revoked: v2 does not bind the
superseding qualification policy or its exact activated phase-11 plan`. It can
emit only `qualified=false`, `claim_authority=none`, and
`promotion_authority=false`. Its source SHA-256 is
`63d98e7b...d2fa8`; every known v4-bound runner freezes the prior
`c2b5b298...5139b` digest and therefore fails its own source-binding check
before execution.

The registered v2 verification schema is retired at the representation layer
as well. It now requires `qualified=false`, at least one qualification failure,
`claim_authority=none`, and `promotion_authority=false`; its SHA-256 is
`a935e041...11490`. Thus a handwritten or legacy positive v2 object cannot
pass current schema validation even in a consumer that does not rerun the
verifier. Known v4 consumers bind the older `3bcf4748...8a74d` schema digest,
so they also fail their frozen schema-closure check.

Policy v6 freezes the replacement authority shape without activating it. A v3
router binds exactly one v2 evidence router and one future active policy. The
v3 verifier reopens every v2 evidence predicate, requires the sole remaining
v2 failure to be the explicit revocation above, and then separately requires
that an active policy v7 or later bind the exact evidence router, the activated
revision-at-least-7 phase-11 plan embedded in the full-identity receipt, both
v3 schemas, both verifier generations, the canonical absent lease namespace,
and a recomputed transitive Python/schema closure. The future active-policy
schema also requires explicit revocation of every v1-v6 authority path.
The v3 CLI rejects an occupied lease namespace before verification and creates
the canonical output only for a fully qualified result, so an early or false
invocation cannot consume the authority receipt path.

The rebound closures contain `156` members for opening-100M, `155` for
phase 11, `151` for runtime, and `154` for the v3 qualification authority.
Static AST, JSON Schema, plan-schema, ordered closure, objective-hash, policy
hash-graph, and stale-runner hash checks pass. No test suite, verifier, codec,
or proof experiment ran. Qm8 remains live and untouched; q1 full-1G payload,
inverse, cleanup, runtime, and qualification remain unknown. This change has
zero Gamma compression, authorship, archive, or score credit.

The v3 schemas are intentionally direct-validator contracts rather than new
entries in the global `research_contracts.py` registry. A trial registration
changed that shared source digest and made unrelated sealed NNCP experiments
appear invalid. The registration was removed before any run; the global
registry is restored byte-for-byte to SHA-256 `744d3cc2...fa5b`, while the v3
verifier and its 154-member closure still bind and validate both v3 schemas
directly. This preserves unrelated historical evidence instead of forcing a
campaign-wide migration for a dormant authority format.

The same audit reached the adaptive scheduler. Before correction,
`next-experiment` labeled the already-retried qm7 proposal, the dormant owned
lease manager, the statically rejected Mechanism-IR wrapper, WIKI-PDA v2,
WIKI-SCHEMA-VM v1, and FOSSIL-MATCH v3 as eligible at ranks `2`, `4`, `5`,
`6`, `7`, and `8`. Their executable entry points would still have failed, but
the scheduler could select them and waste the serialized lane. Their canonical
proposal records now encode the evidence already established: qm7 is
superseded by live qm8; the wrapper is superseded by its static rejection; the
owned-cleanup manager is dormant until qm8 terminalizes and releases the
namespace; and all three q1 mechanisms are superseded pending new candidate
identities bound to a positive v3 qualification.

A fresh rank derivation marks all six rows `eligible=false` at ranks `8`, `9`,
`10`, `13`, `14`, and `15`; the selected unrelated proposal remains
`delta_midas_named_midpoint_gradient_65536_q0_v1`. This is scheduling
quarantine, not scientific retirement of the WIKI-PDA, schema-VM, or FOSSIL
mechanisms. No candidate, control, archive, or proof run occurred.

### SAFE-MIX static closure audit

`gamma_safe_mix_v1` remains unexecuted and zero-credit. Its Q63 native
implementation, arbitrary-precision reference, transactional controls, build
capture, and five-population oracle suite are materialized, but the planning
document was not actually valid under the generic schema named in its
`$schema` field. The generic schema rejected its extra `role` and
`theory_sources` fields and also required an absent dependency list. The
pending program lock separately omitted the integer-reference receipt schema
and the final SAFE-MIX receipt schema, so a future lock could have appeared
complete while leaving two authority-bearing shapes outside its closure.

Planning revision 2 closes those static gaps with the dedicated
`gamma-safe-mix-plan.schema.json`, explicit parent/treatment/lock
dependencies, and `execution_authorized=false`. The pending lock now includes
the plan, its schema, the arbitrary-precision receipt schema, and the final
receipt schema. The interface requires dedicated-plan validation before any
execution.

The non-circular program lock is now materialized. It binds all `31` declared
source, contract, build, control, plan, and receipt-schema files. The lock
SHA-256 is `0234709a...6f41c`; an independently executed verifier rehashed the
same ordered manifest to `88fcb5e6...a9895`, bound the exact Python executable,
and emitted terminal-pass verification `8ff09542...3ad65`. Direct schema
validation and a second manifest/hash reconstruction also pass. See the
[`program lock`](../programs/gamma_safe_mix_v1/program-lock.json) and
[`verification`](../results/gamma_safe_mix_v1/01_program_lock/program-lock-verification.json).
The locked plan deliberately remains `execution_authorized=false`, so this
proves source closure only. No compiler build, transactional control, integer
oracle population, finite coder, or mixture archive was run, and all
compression and score credit remain zero.

The proof boundary is unchanged but now explicit. The ideal two-expert
Bayesian inequality supplies at most a one-bit ideal log-loss penalty. It does
not prove a bound for Q63 posterior rounding, probability-count rounding, the
finite CMIX range state, archive termination, package bytes, or runtime. Native
versus arbitrary-precision identity can prove only that the frozen integer law
was implemented; fresh P/K/D/M arithmetic archives remain the sole compression
authority.

A subsequent activation audit found that the source closure is not yet a safe
execution closure. All four proof entry points that inspect the exclusive lane
still require an obsolete `active=true` field before treating a lease as live.
The canonical managed-lease schema has no `active` property, and the current
schema-valid qm8 lease therefore passes those functions as apparently absent
even while its owner PID and descendants are live. Separately, the frozen build
contract requires `clang++` plus `ld.lld`, neither of which exists on the
selected host. These are an execution-control contract-drift error and an
environment dependency absence, respectively; neither is evidence against the
Q63 mixture law.

The exact v1 files remain immutable and their program-lock verification remains
valid. Direct v1 execution is now quarantined. The only authorized mutation is
a separately identified `gamma_safe_mix_v2` proof envelope that preserves the
v1 arithmetic and populations, requires receipt-bound activation, rejects any
extant lease or acquisition-lock path under no-follow inspection, proves qm8
process closure, and binds a compiler/linker pair that actually exists. No
dependency installation, compiler substitution, proof execution, archive, or
score claim was authorized. See the
[`activation audit`](../operations/planning/gamma_safe_mix_v1_activation_audit_q0_v1.json).

`gamma_safe_mix_v2` now materializes that correction as a sealed, still-dormant
proof envelope. Candidate tree `f316e4a9...afe9d` contains the revisioned
activation plan, no-follow source and namespace validation, an exact-token
atomic acquisition lock, synthetic collision/replacement/token/hardlink and
process controls, guarded dispatch to the immutable v1 phases, receipt
schemas, and an independent verifier that reopens the terminal, source,
toolchain, child, guard, and managed-lease migration evidence. The plan binds
all `13` authority-bearing source artifacts, including the verifier and its
schema. Static AST, Draft 2020-12 schema, dormant-plan, proposal/experiment,
source-binding, and candidate-file closure checks pass. Counted candidate
source is `65,236` bytes under the frozen `65,536`-byte ceiling.

This is source-complete infrastructure, not executed SAFE-MIX evidence. Plan
revision 1 has `execution_authorized=false`, null activation dependencies, and
no phases. Activation still requires qm8 to terminalize and receive a matching
independent classification, the owned-cleanup lease candidate to pass and
migrate exactly into the canonical manager, and content-addressed `clang++`
and `ld.lld` executables to exist. No v2 control, build, oracle, finite coder,
archive, or inverse has run; Gamma compression and score credit remain zero.

A deeper off-PATH search supersedes only the earlier tool-availability
observation. It found a single-link regular Clang 17 driver at
`/home/x/enwiki9-nonproof/cmix-obias-donor/cmix-obias/tools/llvm17-local/bin/clang-17`
and a single-link regular AMD LLD 23 driver inside the retained ROCm SDK. Under
the exact v2 scrubbed environment, both `--version` probes return zero and
contain the required `clang` and `lld` family markers. Their SHA-256 values are
`d8e99328...a414` and `da235ec5...74b2`. This removes the shallow
"no suitable binary exists" conclusion; it does not prove that the mixed
Clang/LLD pair accepts the frozen build, produces byte-identical independent
builds, or passes any SAFE-MIX population. Those remain guarded activation
phases after qm8 and managed-lease closure. See the zero-authority
[`toolchain availability audit`](../operations/planning/gamma_safe_mix_v2_toolchain_availability_q0_v1.json).

## 2026-08-24 - FOSSIL-MATCH targets exact history beyond FXCM's 16 MiB ring

`fxcm_fossil_match_q0_v1` is a new zero-credit information-source design, not
a checkpoint or optimizer variant. The frozen FXCM match model stores absolute
32-bit candidate positions, but `bufr(position)` always resolves through
`buffer[position & 0x00ffffff]`. Once a position is more than `16,777,216`
transformed bytes old, the model reads the current ring alias rather than the
original decoded byte. This proves an information gap in the implementation;
it does not prove that enwik9 contains useful far repetitions.

FOSSIL-MATCH keeps the exact already-decoded transformed prefix in an
append-only file-backed history and a fixed `2^24` table of 8-byte records.
Before byte `i`, it hashes and exactly verifies the preceding 16 decoded bytes,
requires a continuation distance above 16 MiB, and predicts only the byte at a
strictly earlier verified continuation. It scores before inserting the current
truth. Encoder and decoder therefore have identical information and update
order without transmitting offsets or commands.

The first eventual scan freezes K/D/R/S/N. K performs all bookkeeping with
prediction disabled. D reads exact far history. S reads D's identical absolute
position through the parent's 16 MiB alias, isolating exact addressability.
R supplies deterministic random bytes and N negates D. The full transformed
population must repeat exactly, every chronological third and multiple distance
buckets must be positive, D must beat every matched control, and incremental
process-tree memory is capped at `262,144 KiB`. The target-scale impossibility
screen requires at least `254,953` active bytes because one active byte has at
most 16 bytes of optimistic leverage under the parent's count floor.

Passing would authorize only exact retained-parent surprisal tracing at the
sealed opportunities. A native P/K/D finite archive, exact inverse, package,
memory, runtime, and distant transfer remain mandatory. A prospectively frozen
[`adaptive experiment`](../operations/adaptive/experiments/fxcm_fossil_match_q0_v1.json)
and dependency-gated proposal now bind the design to Gamma's workflow. The
proposal was rejected before implementation after an independent static audit
found that its resource and transition proof surface was underfrozen. No
scanner, source, candidate revision, scan, or receipt exists, so v1 has zero
compression and score credit. See the
[`design contract`](../operations/planning/fxcm_fossil_match_q0_v1.json).

Correction-only `fxcm_fossil_match_q0_v2` retains the same information source
but closes those static defects before source exists. It freezes a modulo-
`2^64` 16-byte polynomial hash, the exact `2^24` record layout and sentinel,
unconditional post-score replacement, no continuation state, the parent's
pre-insertion ring-alias control, SplitMix and negated controls, and six
inclusive distance buckets. The scanner must route every nonsequential byte
read through an `index < current_position` accessor.

v2 also replaces a weak global transfer check. D must now beat the maximum of
S/R/N separately in every chronological third and in at least two distance
buckets. Its resource gate includes process-tree RSS, fresh cgroup-v2 peak,
sampled file-cache residency, max/OOM/OOM-kill events, and scratch; even a
standalone pass can authorize only donor-surprise tracing. Native integration
still requires a fresh joint parent-plus-specialist cgroup, process-tree,
archive, inverse, runtime, and package replay. The v2
[`design`](../operations/planning/fxcm_fossil_match_q0_v2.json),
[`experiment`](../operations/adaptive/experiments/fxcm_fossil_match_q0_v2.json),
and dependency-gated proposal receive zero credit. Candidate development found
a real provenance defect before source materialization: the proposal's frozen
superseded-v1 qualification-policy digest does not match the retained v1 file.
Claim/develop therefore failed closed. The rejection transition then exposed a
workflow atomicity defect: it wrote `state=rejected` before recursive evidence
validation failed, leaving the quarantined exact bytes under the `proposed/`
path. v2 remains unclaimable and unexecuted; its path is retained because v3
hash-binds the failure artifact. The shared adaptive controller is active for
qm8, so its transition implementation is not edited under that process.

Correction-only `fxcm_fossil_match_q0_v3` changes no scientific transition,
control, bucket, threshold, or resource ceiling. It replaces only the stale
activation binding with source-bound q1 qualification policy v4 and adds the
missing executable proof closure. The native candidate now contains an exact
C++ scanner, zero-credit interface, and strict local scan schema. Its semantic
state is exactly `150,994,944` bytes: `2^24` eight-byte table records plus the
parent-equivalent `2^24`-byte ring. Every random historical read goes through
one `PastBytes(begin,size,current)` guard, whose requested terminal offset must
not exceed `current`; prediction and all D/S/R/N scoring precede table, ring,
and rolling-hash mutation.

The scanner emits chronological-third and six-distance-bucket control tables,
terminal table/ring hashes, an exact opportunity digest, a terminal rolling-
hash recomputation, and duplicate treatment/K transition digests constructed
without any control outcome. The sealed native candidate tree is
`bff0b35e7ce18439839bf7291d096f602908d455018bd6643122d7bbc899ed39`.
Clang syntax validation initially exposed a toolchain environment failure:
the sealed driver could not find `libLLVM-17.so.1`. The execution plan now
binds the regular resolved Clang binary, canonical `--driver-mode=g++`, the
exact loader library and `LD_LIBRARY_PATH`, rather than treating that failure
as an algorithm result.

The source-bound runner and independent verifier re-open a positive v2-format
q1 receipt under exact policy v4, rerun the policy-bound parent verifier before
lease acquisition, hash the complete transformed population, compile from the
sealed candidate, and launch two fresh scanner processes. Each process is
single-CPU and bounded at `196,608 KiB` process-tree RSS, `760,000,000` bytes
cgroup memory including file cache, and `100,000,000` scratch bytes. The runner
samples cgroup file residency independently, requires zero max/OOM/OOM-kill
events and cleanup, and emits an exact output manifest. The verifier
reconstructs compiler, guard, taskset, cgroup, scan, lease, measurements,
gates, and verdict from retained artifacts.

Only static JSON-schema validation, Python AST parsing, policy/hash closure,
candidate-revision sealing, and C++ syntax compilation have run. No transformed
population scan or finite archive has run because qm8 still owns the exclusive
full-1G lease and q1 is not qualified. v3 therefore has zero compression,
authorship-score, and objective credit. See the
[`scientific design`](../operations/planning/fxcm_fossil_match_q0_v3.json),
[`execution plan`](../operations/planning/fxcm_fossil_match_q0_v3_execution.json),
and [`experiment`](../operations/adaptive/experiments/fxcm_fossil_match_q0_v3.json).

An independent post-materialization audit was reconciled against the current
revisions rather than the superseded drafts it inspected. Its q1 objection
applies to the authority-revoked v1 qualification receipt and verifier, which
accepted caller-supplied full-stream digests and a persistent-state boolean.
Policy v4 instead binds the v2 artifact router and verifier: the verifier
reopens every retained artifact, reruns both soft-pressure arm verifiers, the
full probability/state verifier, and the Geekbench-5-bound runtime verifier,
and requires the recomputed objects to equal the supplied verifications. Thus
the old v1 weakness is real historical evidence but is not a present v4 proof
path. Runtime remains a required future measured artifact, not an inferred qm8
property.

The same audit's FOSSIL-MATCH objections were already the reason v1 was
rejected and are explicit v3 predicates: cgroup peak includes file cache and
must stay at or below `760,000,000` bytes with zero max/OOM/OOM-kill events; D
must beat S/R/N in every chronological third; and the hash constants,
index/tag split, sentinel, replacement order, no-continuation rule, alias
off-by-one, and distance buckets are frozen in the interface and sealed source.
This reconciliation adds no run evidence. It confirms only that v3 tests the
intended causal mechanism under the corrected proof surface.

## 2026-08-24 - WIKI-PDA v1 is causally rejected and v2 closes the proof surface

The dormant `wiki_pda_structural_replay_q0_v1` scanner was rejected by static
inspection before any transformed-population run. Its transition-table lookup
is selected only after the current opening `L` truth has entered parser state,
but its offline scoring loop then credits transition target offset zero. That
position predicts the already observed `L`, so v1 can receive one free correct
byte per predicted event. The source also initializes its declared FNV-1a
digest with `1469598103934665603` rather than the standard 64-bit FNV-1a offset
`14695981039346656037`. Its ad hoc runner does not source-bind the compiler,
candidate, q1 authority, resource guard, managed lease, result file set, or an
independent decision verifier. These are proof defects, not measured negative
compression evidence. v1 remains unexecuted and has zero credit.

Correction-only `wiki_pda_structural_replay_ceiling_q0_v2` changes causal
scoring and proof closure while retaining the scientific mechanism and frozen
scale: 16-byte names, depth 16, 1,024 direct-mapped unanimous transition
records, poisoned conflicts, exact closing-name replay, and the `4,079,243`
correct-byte threshold. The scanner consumes `L` before lookup but forbids T
credit until relative offset one. C cannot activate until decoded `L/slash`
and relative offset two. For each current byte, D/R/S/N are selected and
scored from state through the previous byte before truth changes parser,
table, stack, or digests. R, cyclically rotated S, and negated N use every and
only D's active positions; T has deterministic overlap priority over C.

The scanner emits C/T attribution, D/R/S/N counts in three exact transformed
coordinate thirds, dedicated forbidden-early counters, standard FNV-1a input,
opportunity, table, stack, and terminal-state digests, and duplicate K/D
transition digests. The prospective gate requires two byte-identical complete
receipts, D correct bytes at least `4,079,243`, D strictly above max(R,S,N) in
every third, zero early-credit counters, causal identity, and both resource
guards passing at `65,536 KiB` process-tree and VmHWM, `256,000,000` cgroup
bytes including cache, `100,000,000` scratch bytes, one CPU, and zero
max/OOM/OOM-kill events.

The native candidate is sealed at tree
`8f674767ceb8f452f24f2167460f89519957652624340ef3ecdcd1dfa2302419`.
Its five counted candidate files total `30,596` bytes, below the prospective
`65,536`-byte ceiling. The execution plan binds that revision, scanner,
interface, local receipt schema, runner, independent verifier, shared
content-addressed proof helper, five result schemas, q1 policy-v4 verifier,
managed lease, v3 resource guard, resolved Clang toolchain and loader, taskset,
and exact `587,138,826`-byte transformed population. Static schema, AST,
candidate-revision, plan-binding, and C++ syntax checks pass.

No corpus hash, scanner process, executable link, result root, or receipt was
created. qm8 still owns the exclusive full-1G lane and q1 has not produced the
required positive v2 qualification. This candidate is therefore a frozen
zero-credit causal ceiling only. A future pass authorizes retained-parent
donor-surprise tracing; it cannot authorize a WIKI-PDA archive, package,
inverse, prize score, or Gamma score credit without a fresh native replay. See
the [`design`](../operations/planning/wiki_pda_structural_replay_ceiling_q0_v2.json),
[`experiment`](../operations/adaptive/experiments/wiki_pda_structural_replay_ceiling_q0_v2.json),
and [`execution plan`](../operations/planning/wiki_pda_structural_replay_ceiling_q0_v2_execution.json).

### 2026-08-24 - WIKI-PDA v2 receives a correction-only q1-v3 authority successor

The frozen WIKI-PDA v2 scanner did not change, but its first execution plan
became stale when q1 policy v6 revoked all policy-v4/v2-verifier successor
paths. `wiki_pda_structural_replay_ceiling_q0_v2_execution_v2` corrects only
that parent-authority axis. It retains candidate tree
`8f674767ceb8f452f24f2167460f89519957652624340ef3ecdcd1dfa2302419`,
scanner
`3e9aebfa0b32aa57fc23eb41b91bfc6dde737ff0428fbe28a7fa1ac52af4b82f`,
the exact `587,138,826`-byte population, all D/R/S/N definitions, the
`4,079,243`-correct-byte threshold, chronological-third predicates, and every
resource ceiling.

The successor requires a future active q1 policy revision at least 7, a
schema-valid q1-v3 authority router, an exact stored v3 verification, a fresh
independent v3 re-verification, and an absent full-1G lease and lock. Its
decision and independent verifier bind both the active policy and the v6
design policy. The old policy-v4 execution plan remains stale and has no
execution authority.

AST, Draft 2020-12 schema, exact 32-artifact plan-binding, candidate-tree,
scanner-hash, and diff checks pass. No population scan, compilation, result
root, or receipt was created because qm8 owns the live full-1G namespace and
q1-v3 authority does not yet exist. This remains the same zero-credit causal
ceiling, not a new algorithm and not Hutter evidence. See the
[`authority review`](../operations/planning/wiki_pda_structural_replay_ceiling_q0_v2_authority_v3_review.md)
and [`execution successor`](../operations/planning/wiki_pda_structural_replay_ceiling_q0_v2_execution_v2.json).

## 2026-08-24 - WIKI-LOOM freezes semantic virtual time as a dormant new source

An exclusion audit rejected three superficially creative routes before any new
source was written. Whole-page semantic permutation repeats exact negative
article-order, geometry, revision-order, and GEPA evidence. Entity/template
retrieval repeats terminal WIKIBACK, WIKIFORWARD, WIKIGRAPH, TESSERA, SRSTC,
typed Skip-CTS, and FRACTAL slot-trie neighborhoods. Explicit far-history
macros repeat paid copy/ledger failures. Those mechanisms remain retired at
their measured boundaries.

`wiki_loom_shared_state_lstm_q0_v1` instead changes the time coordinate of an
auxiliary recurrent expert. The raw byte stream and authoritative q1 parent
remain untouched. Once the opaque post-WRT parser has completely decoded a
template name and explicit field key or positional index, it selects one of
`4,096` direct-mapped hidden/cell slots. The selected state advances only on
bytes in that template-field value. When the same descriptor returns later,
the expert therefore resumes a virtual field-local trajectory even though
unrelated bytes and pages were interleaved in the real stream.

The auxiliary transition reads the current parent ByteMixer recurrent
parameters but is no-train: it cannot write parent weights, optimizer,
deferred updates, recurrent state, mixers, contexts, SSE, preprocessing, or
coder state. It is not a full-CMIX checkpoint, fork, rejoin, page permutation,
copy command, or new model asset. Its new information is the decoder-derived
projection of history onto a structural subsequence. A fingerprint miss sleeps
for the entire field, then initializes the slot; a hit must have `128` prior
bytes at field entry. One global SAFE-MIX posterior combines the awake expert
with P and neither updates nor resets while sleeping.

The prospective native arms are P/K/D/M/G/S/R/N. K must be byte-identical to
P while exercising all mechanism bookkeeping. G uses one unpartitioned
auxiliary state; S uses the previous completed field descriptor; R uses causal
ordinal-random routing; N complements the aligned byte distribution. The
opening-10M gate requires exact finite archives and inverses, deterministic M
repeat, positive M gain in every third, at least `50,000` net bytes after
incremental source/framing, and at least `10,000` byte-equivalent raw-D margin
over every matched control. One miss retires the frozen slot, warmth, route,
state, and mixture realization without a sweep.

The [`design`](../operations/planning/wiki_loom_shared_state_lstm_q0_v1.json),
[`Mechanism IR`](../operations/planning/wiki_loom_shared_state_lstm_q0_v1.mechanism-ir.json),
[`experiment`](../operations/adaptive/experiments/wiki_loom_shared_state_lstm_q0_v1.json),
and dependency-dormant proposal are schema-valid and hash-bound. No source,
compiled causal closure, run, probability, archive, inverse, saving, or score
exists. Router revision 4 authorizes a source audit only after q1 qualifies,
CMIX adaptation/open NNCP/WIKI-PDA terminalize subscale, and the already-frozen
WIKI-SCHEMA and FOSSIL-MATCH routes are terminally classified. WIKI-LOOM
therefore has zero credit and does not delay the current q1, WIKI-PDA,
WIKI-SCHEMA, FOSSIL-MATCH, or MIDAS order.

## 2026-08-23 - WIKI-SCHEMA-VM replaces checkpointing as the primary new information-source proposal

SAFE-FORK is classified as checkpoint/fork/rejoin infrastructure, not a novel
compression algorithm. It may later contain an independently valuable causal
expert, but checkpointing CMIX does not itself address the `3,513,707`-byte
counted-score debt and receives no scientific priority on that basis.

The new zero-credit proposal is `wiki_schema_vm_ceiling_q0_v1`: a bounded
online virtual machine over opaque post-WRT bytes. It parses `PP`/`RR` template
invocations, conditions on the decoded template name, prior field key, and
field index, and learns deterministic next-key-plus-equals programs from
completed prior invocations. No rule identifier, value, dictionary decoding,
raw-corpus oracle, or future delimiter is transmitted or consulted.

A pre-measurement audit found that the first source draft updated its program
table at key completion, which would allow later fields to learn from the same
still-open invocation. The sealed implementation instead stages at most 64
state/target programs per template and commits them in source order only when
that invocation closes. Staging overflow discards that invocation's complete
staged learning set. Its `32,768 x 4` fixed table retains two deterministic
Space-Saving candidates per state; parser depth, atom lengths, collision
policy, replacement order, storage, and controls are all frozen.

Treatment D predicts only at causally selected field boundaries and stops at
its first mismatch. R substitutes deterministic SplitMix bytes at the exact D
positions. S uses the immediately preceding completed template-name state at
the matched prior-key/index coordinate and target length. K is the same
parse/lookup/learn state machine with prediction disabled. Two fresh processes
must emit byte-identical receipts.

The initial sealed candidate tree was `3d110ac4...680c5`; strict C++17 syntax
validation and all registered JSON schemas passed. Its prospective rule was
`4,079,243` correct D bytes, with every chronological third positive and D
strictly above R and S. That number was a hypothesis, not a result. No scan or
decision receipt exists. The runner fails closed unless it receives a
fully positive, independently verified q1 qualification with runtime and
package closure, process-tree peak at most `9,000,000 KiB`, and a released
full-1G lease. See the
[`execution contract`](../operations/planning/wiki_schema_vm_ceiling_q0_v1.json),
[`experiment`](../operations/adaptive/experiments/wiki_schema_vm_ceiling_q0_v1.json),
and
[`interface`](../programs/wiki_schema_vm_ceiling_q0_v1/interface-contract.json).

A later read-only proof audit confirmed the byte-order causality: each active
prediction is scored before the current byte mutates parser or table state,
programs are close-committed from earlier invocations, and a mismatch terminates
the opportunity before any successor byte is counted. It also found that the
first runner merely observed a free `exclusive_full1g` lease and therefore had
a check-to-launch race. Planning revision 2 corrects only that execution
boundary: the unchanged candidate tree now runs under an atomically acquired
managed lease whose evidence and transition chain are required outputs. The
output manifest additionally compares the complete pre-manifest directory to
the frozen filename set, so unlisted files prevent closure. The same audit
found that the plan's former generic `$schema` label did not validate its actual
shape. Revision 2 replaces it with a dedicated strict schema, and the runner
now validates that plan plus every transitive source, schema, compiler, lease,
population, command, and output binding before acquisition. This is static
harness evidence only; the scanner remains unexecuted and receives zero credit.

The same audit rejected the initial correct-byte rule as futility authority.
CMIX discretizes every bit probability to at least `1/65,536`; consequently an
active byte has up to `8 * 16 = 128` bits, or 16 bytes, of optimistic parent
log-loss leverage. A byte that misses D can also share a correct leading-bit
prefix. Therefore `4,079,243` correct bytes are neither a necessary condition
for target-scale gain nor an arithmetic-code ceiling. The corrected unmeasured
revision `0e08910e...ba958a` preserves the scanner implementation and instead
requires at least `ceil(4,079,243 / 16) = 254,953` active opportunity bytes,
positive correct bytes in every third, and strict wins over R and S. It reports
the old one-byte-per-correct screen only as a diagnostic. Passing authorizes an
exact retained-parent donor-surprise trace; only that trace can determine the
available parent log-loss, and only a native finite archive can establish gain.

## 2026-08-23 - cmix-obias Arm B terminalizes as an OOM/resource failure

The source-built full-1G Arm A remains an exact host-bound external baseline.
Its `108,022,224`-byte archive and `107,730,531`-byte payload decode to the
canonical `1,000,000,000` bytes with SHA-256
`159b8535...744bc`. Charging the independently reproduced `491,483`-byte
program package gives a counted total of `108,513,707` bytes. This is an
external-candidate measurement, not Gamma-authored score credit.

Arm B completed encoding and reproduced Arm A's archive and payload
byte-for-byte, but it did not complete inversion. Its decode log stops at
`39.07%` at the same host event where the kernel OOM snapshot contains the
wrapper and `archive9` decoder and the enclosing tmux scope failed with
`oom-kill`. The preserved strict-memory observation records
`VmHWM=10,425,744 KiB`, exceeding the decimal `9,765,625 KiB` limit by
`660,119 KiB`; the independent tmpfs-aware receipt is also a resource failure.
The incomplete scratch tree remains unchanged in `/dev/shm` as evidence.

Recovery-only terminalization archived both stale runtime sidecars before
removing them from the live lease namespace. The independent verification
rehashed every retained archive, payload, log, sidecar snapshot, and OOM log;
all 18 checks pass. The terminal A/B audit consequently records
`correctness_pass=false` and `strict_resource_pass=false`: the pair proves
repeat encode identity on this host, but not a second exact inverse or a
resource-qualified deterministic full-1G package. Arm B receives zero score
and authorship credit and must never be resumed or rerun. Evidence:
[`Arm A`](../results/cmix_obias_source_full1g_roundtrip_a_qm0_v1/decision.json),
[`Arm B terminal receipt`](../results/cmix_obias_source_full1g_roundtrip_b_qm0_v1/oom-terminal-receipt.json),
[`independent verification`](../results/cmix_obias_source_full1g_roundtrip_b_qm0_v1/oom-terminal-verification.json),
and [`A/B audit`](../results/cmix_obias_source_full1g_ab_terminal_audit_v2/decision.json).

The unique authorized successor is the correction-only file-backed
memory-safe parent. It must first prove output identity and process-tree plus
file-backed residency compliance at the smallest frozen gate. No midpoint,
mixture, or structural mechanism may inherit compression credit from this
resource correction.

## 2026-08-23 - q1 file-backed parent passes reset scopes and cumulative 1M

The q1 correction now has a clean, content-addressed qm7 build lineage. Two
release builds are byte-identical with SHA-256 `610edd6a...5a8808`; two harness
builds are byte-identical with SHA-256 `8fc7b519...b65f`. All 17 compiler
controls and the isolated allocator positive fixture plus all 15 allocator
negative controls pass. The packaged shared allocator event descriptor is not
used as a lifecycle sequence: package creation launches helper CMIX processes
that inherit the descriptor, so its stream contains three concatenated
lifecycles. Lifecycle authority remains the isolated fixture and controls,
while each codec arm must leave its backing directory empty.

The corrected v2 reset-scope receipt passes opening, middle, and tail 250KB
cold-start populations. Parent and q1 have identical post-head integer
probabilities, complete residual and byte traces, payloads, and decoded output
within every scope. The aggregate scoped probability hash is
`cc232442...11afe9`. Opening restores the exact 250,000 raw bytes. The
specialized preprocessor restores 249,871 bytes for the middle fragment and
249,350 for the tail fragment; those two populations therefore require exact
parent/q1 decoded-output identity rather than the invalid claim that an
arbitrary interior fragment is a standalone raw round trip. All 12 guards
pass, with worst sampled tree RSS `8,351,304 KiB`, and q1 backing cleanup is
exact. See the
[`scope receipt`](../results/cmix_obias_memory_safe_parent_filebacked_q1_qualification_qm7_v1/06_scope_identity/fixed-reset-scopes/scope-identity-receipt.json).

The cumulative opening-1M successor also passes. Both arms emit the same
`172,605`-byte payload (`a723ca62...d70db7`), the same exact probability stream
(`d34a8d4b...5458d`), and byte-identical complete traces; both restore the
canonical 1,000,000-byte prefix with SHA-256 `369b6889...52cad`. Its four
guards pass at worst sampled tree RSS `8,388,568 KiB`, worst sampled scratch
`20,991,792,710` bytes, and one allowed CPU. See the
[`cumulative receipt`](../results/cmix_obias_memory_safe_parent_filebacked_q1_qualification_qm7_v1/07_cumulative_identity_1m/cumulative-identity-receipt.json).

These are exact parent-preservation and resource-feasibility results, not a
compression improvement. q1 remains unqualified for full-stream authority,
Gamma compression credit, or score credit. The next bounded gate is the
frozen opening-prefix and distant cold-reset 10M transfer pair; the latter is
explicitly not a byte-zero persistent-state claim.

## 2026-08-23 - q1 passes 10M transfer, then exposes a cgroup-cache full-1G failure

The opening and distant cold-reset 10M transfer phase passes. Opening q1 emits
the same `1,599,341`-byte payload as its qualified parent and restores the
canonical opening 10M bytes. The distant scope emits the same `459,091`-byte
payload and decoded stream as its parent. Both scopes have exact post-head
integer-probability identity; worst sampled tree RSS is `8,503,092 KiB`, worst
scratch is about `23.5 GB`, every guard passes, and the independent verifier
rehashes both populations and receipts. This remains bounded reset/transfer
evidence and does not establish the byte-zero persistent full-1G trajectory.

Candidate-owned full Arm A `cmix_filebacked_fxcm_full_a_qm7_v2` then failed at
a new phase boundary. The two package-helper compressions completed and the
real transformed-payload compressor reached pretraining `0.39%`, but its
cgroup hit the effective page-rounded hard cap of `9,999,998,976` bytes and
recorded `537` `memory.events.max` events. The guard terminated the tree with
SIGTERM. There was no OOM kill, process-tree RSS itself peaked at only
`7,395,300 KiB`, no encode-stage receipt was written, decode never started,
and all output, inverse, qualification, and score claims correctly remain
false. The scratch tree is preserved. All independent failure-verifier checks
pass; see the
[`terminal receipt`](../results/cmix_filebacked_fxcm_full_a_qm7_v2/full-roundtrip-receipt.json),
[`verification`](../results/cmix_filebacked_fxcm_full_a_qm7_v2/full-failure-verification.json),
and
[`reflection`](../operations/adaptive/reflections/20260823T213424Z_653b446c89.json).

The single correction-only successor is
`cmix_filebacked_fxcm_full_a_qm8_v1`. It leaves the q1 binary, package bytes,
model, coder, preprocessing, corpus, accounting, and 10,000,000,000-byte hard
cap unchanged. A bound wrapper instead sets cgroup `memory.high` to a
page-rounded `8,999,997,440` bytes so Linux initiates cache reclaim before the
hard cap, then restores the prior value. The wrapper preflight passes and is
schema-validated. Adaptive job `20260823T215147Z_7827ad9bc5` is the only
authorized full-1G execution for this correction. It receives zero score
credit unless a later exact package receipt independently closes every prize
gate.

## 2026-08-23 - phase-11 audit preserves post-head evidence and finds a dead residency hook

A harder read-only audit corrected a false concern before it could mutate the
qualification route. The source closure's stock `KH_TRACE` call is pre-head,
but the retained qm7 identity populations did not execute that source
unchanged. Their content-addressed diagnostic build applies
`exact-integer-probability-trace.patch` (`09c87e09...71e`), which moves
`KhWriteRes` after `KhBitLstm32Head::Adjust` and immediately before the
arithmetic range split. The materialized build confirms that placement, and
its receipt explicitly binds the patch and post-head contract. The opening and
distant 10M probability hashes `d6512550...4e97a` and
`4ab13c5d...ec59` therefore remain valid exact coder-probability evidence.

The same audit found a real resource-observer defect. q1 defines
`FXCM::ByteUpdate()` to invoke the 1,048,576-modeled-byte pageout cadence, but
`Predictor::Perceive()` never calls `fxcm_model_.ByteUpdate()`. Source-wide
call-site inspection finds only the method definition. Thus qm8 exercises the
constructor's initial `PageOutAll` plus kernel reclaim under `memory.high`, not
the declared periodic hook. This does not change predictor arithmetic or
invalidate the live run, but its resource receipt must be interpreted under
that actual mechanism. Repairing the hook inside qm8 is forbidden; any repair
would be a new correction-only candidate.

The unbound phase-11 successor is recorded only as a draft at
[`cmix_filebacked_fxcm_full_probability_state_identity_q0_v1`](../operations/planning/cmix_filebacked_fxcm_full_probability_state_identity_q0_v1.json).
It replaces the infeasible full `KH_TRACE` with an online post-head uint16
SHA-256 stream calibrated against both retained 10M digests, coder-state
checkpoints, and source-ordered semantic hashes of every large allocation that
the q1 mutation can affect. It has no execution authority until exact,
independently verified full A/B roundtrips release the full-1G lease.

## 2026-08-16 - The layer-19 output projection is open in both directions

A same-run production probe sealed the tensor immediately after
`concat_head` and before `w_o_19`, its input adjoint, and the initial
`w_o_19` matrix over all 64 states and 32 streams. Both complete source
populations were byte-identical, every non-probe fixture file was unchanged,
and the retained matrix-gradient identity held. The source job completed the
science but named an undeclared pre-cleanup decision artifact; its receipt-only
successor rehashed both 256-file probe populations, published the three durable
BF16 artifacts, and removed the transient capture trees. See the valid
[`decision`](../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T162351Z_97a6519638.json).

The open matrix-gradient attribution first reproduced a prospectively fixed
128-row slice, then expanded the same chronological kernel across all
1,048,576 `w_o_19` weights. Each state accumulates its 32-stream dot from
zero with sequential AVX2 FMAs, adds the decoded prior BF16 gradient after the
dot, and rounds once to BF16. The full treatment is exact; its sign-negated
control differs everywhere. See the full
[`decision`](../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T163533Z_7a29124cd9.json).

The complete transpose then transferred the independently attributed
128-feature panel schedule to `w_o_19`. Eight ordered panels reproduce every
one of the 2,097,152 source input-adjoint words exactly across two replays. A
single unblocked 1,024-feature chain differs in 285 words and the sign-negated
control differs everywhere. The evaluator has no LibNC, GGML, CUDA, OpenMP,
BLAS, or other forbidden dynamic dependency. See the
[`decision`](../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T164348Z_ff5718724e.json).

Finally, the already exact 32-stream open forward exposed its existing
layer-19 merged-attention value without changing arithmetic. Two full
populations retained zero mismatch across all 640 layer-input checkpoints and
equal aggregate hashes. State-major assembly reproduces all 2,097,152 source
pre-`w_o` words exactly; the prospectively frozen stream-major control differs
in 2,088,943 words. The expensive run first failed before science because its
fixture parent was absent. Its retry completed every predicate but used a
decision label outside the result schema. A receipt-only successor freshly
rechecked the source tensor, replay receipts, control, artifact copy, and
original resource envelope, then emitted a contract-valid result. See its
[`decision`](../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/decision.json),
[`execution receipt`](../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/execution.json),
[`guard`](../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T171305Z_fdae41e74c.json).

This closes the layer-19 output projection's forward value, parameter
gradient, and input adjoint. It remains zero-credit teacher-removal evidence:
the forward binds a pinned static GGML source archive and sealed fixture, and
none of these results proves a compact predictor, recursive adaptation,
compression gain, transfer, package closure, or a Hutter score. The next live
boundary is the eight-head value-attention product and `concat_head` backward.

## 2026-08-16 - The layer-19 pre-FF total adjoint is open and exact

The residual-join investigation found an evidence-lineage error rather than a
new arithmetic rule. A production same-run probe captured the pre-FF input,
total adjoint, RMSNorm branch adjoint, and direct residual adjoint in one graph
over the complete retained population. Both source captures were complete,
byte-identical, fixture-preserving, and within the decimal-memory and scratch
limits. The total and branch reproduced their independently sealed source
artifacts exactly. The direct differed from the older
`final_norm_backward` artifact in eight BF16 words, but reproduced the already
promoted streaming-dot final-RMSNorm residual in every word. Adding the
same-run branch and direct in F32 and rounding once to BF16 reproduced every
source total word; the negated control remained live. See the terminal
[`decision`](../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/decision.json),
[`execution receipt`](../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/execution.json),
[`guard`](../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T155008Z_4831e25438.json).

This supersedes the earlier interpretation of the three-word total mismatch.
Five of the eight corrected direct words did not cross the final BF16 sum
boundary; three did. The generic shared-BF16 merge experiments were therefore
driven by a stale direct input and do not establish special merge behavior.
Raw F32 branch joins, coordinate repair, and special residual accumulation are
not needed. Historical receipts remain unchanged.

The first source job completed both large captures but failed at finalization
because it imported the comparator from the wrong module. Its manifest-only
retry completed every scientific comparison, staged durable artifacts, and
removed the transient capture trees before schema validation rejected an
extra `id` in the result's experiment reference. A receipt-only immutable
successor rebound those staged artifacts and published the valid result. The
two implementation failures and their reflections remain part of the audit
trail; no teacher rerun was used to repair either finalization error.

Finally,
`nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1` replaced only the stale
direct input with the promotion-backed streaming-dot artifact. Two
teacher-free full-population compositions replay byte-for-byte and reproduce
the complete sealed source total with zero error. The small executable has no
LibNC, GGML, BLAS, OpenMP, or CUDA dependency. See its
[`decision`](../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T155508Z_53d5388d2c.json).

This closes the open backward boundary through the layer-19 FF block and its
pre-FF normalization/residual join. It remains zero-credit teacher-removal
evidence and proves no attention backward, recursive update, compression
gain, transfer, package, or Hutter result. The next frozen boundary is the
layer-19 attention output projection: the pre-`w_o_19` value tensor, its input
adjoint, the retained `w_o_19` gradient, and the transpose residual.

## 2026-08-16 - The complete top FF1 backward is open through its input adjoint

Three prospectively frozen experiments resolved the remaining `ff1_19`
matrix-gradient boundary. The source attribution first replayed 64
chronological graph states over a fixed 128-output by 1,024-input slice. Its
LibNC treatment matched the retained gradient exactly, while a flat
whole-population product missed 101,753 words and reverse state order missed
110,634. This established that matrix gradients, like bias gradients, retain
BF16 materialization at every graph-state boundary. See the
[`decision`](../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/execution.json),
[`guard`](../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T114029Z_4b8fd50e01.json).

The first open arithmetic grid then refuted its frozen prior-initialized FMA
hypothesis: that cell and the nonfused cell each missed 43 of 131,072 words.
The prospectively declared post-dot cell was exact. Its immutable successor
confirmed the localized contract over the entire slice and two replays:
accumulate each 32-stream dot from zero with sequential AVX2 FMAs, add the
decoded prior BF16 gradient after the dot, then round-to-nearest-even BF16
once per state. It also reproduced the independent reverse-state and
sign-negated oracles exactly while retaining both 43-word failures. See the
grid
[`decision`](../results/nncp_open_ff1_weight_slice_kernel_grid_64_q0_v1/decision.json)
and
[`reflection`](../operations/adaptive/reflections/20260816T115801Z_99a2e7695e.json),
then the immutable successor
[`decision`](../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T120602Z_ec1474d292.json).

Finally,
`nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1` expanded that uniform
kernel to the complete 1,024-input by 6,144-output matrix without changing
arithmetic. Both full 6,291,456-word projections replayed byte-for-byte. Every
one of 48 prospectively fixed 128-row partitions, the inherited parent slice,
and the retained production gradient matched exactly. The generated gradient
also reproduces the retained artifact SHA-256. The executable has no LibNC,
GGML, BLAS, OpenMP, or CUDA dependency and passed the decimal-memory,
temporary-disk, source-closure, and cleanup guards. See the
[`decision`](../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T121133Z_b2c70f9ec5.json).

The next source probe attached a marked zero tensor immediately before the
production `ff1_19` matmul and sealed two complete input and input-adjoint
populations. Its raw science was sound but its first gate retried: the reused
fixture helper excluded only the historical `top_ff2_` namespace and counted
all 256 declared `top_ff1_` probe files in each capture as fixture mutations.
An immutable manifest-only correction did not rerun the teacher. It proved
that all 512 stale mismatches were exactly the enumerated probe paths and that
every non-probe fixture payload remained identical. The corrected oracle
retains two byte-identical 2,097,152-word adjoints, exact source/open FF1 input
identity, and a verbatim 6,291,456-word initial BF16 matrix. See the original
[`decision`](../results/nncp_libnc_top_ff1_input_adjoint_64_q0_v1/decision.json)
and
[`reflection`](../operations/adaptive/reflections/20260816T121911Z_d066eaf1cf.json),
then the corrected
[`decision`](../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T123446Z_5cbfc56c6d.json).

Finally, `nncp_open_top_ff1_input_adjoint_block128_64_q0_v1` transferred the
already attributed LibNC matmul-driver schedule from FF2 to the wider FF1
transpose. Forty-eight ordered 128-feature panels reproduced every source
input-adjoint word exactly across two full replays. A one-panel unbroken
6,144-feature reduction differed in 1,256 words, proving that the panel
boundary remains operationally live. The generated open artifact reproduces
the source-oracle digest and the executable has no LibNC, GGML, BLAS, OpenMP,
or CUDA dependency. See the
[`decision`](../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T123635Z_f1f6615808.json).

This retires LibNC for both top-FF1 parameter gradients and the complete FF1
input-adjoint projection. It remains zero-credit teacher-removal evidence: no
compression, transfer, package, or Hutter improvement follows. The next live
top-layer boundary is the layer-19 pre-FF normalization backward, including
`ln_g_39`, `ln_b_39`, its input adjoint, and the direct FF residual branch.

## 2026-08-16 - The top FF1 bias gradient is fully open and exact

The complete top-layer backward chain now has an open exact projection through
`ff_bias1_19`. Candidate
`nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1` combined the promoted
128-feature-panel FF2 transpose with the attributed AVX2 bounded-exp GELU
backward. Both complete populations replayed byte-for-byte. All 6,291,456
FF2-input residual words, all 6,291,456 gate-branch words, and all 6,291,456
value-branch words matched their independent source captures exactly. The
remaining flat bias projection still differed in 4,708 of 6,144 words, with
maximum absolute error `1.52587890625e-05`, localizing the discrepancy after
the elementwise FF1-output adjoint. See the
[`decision`](../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/execution.json),
and
[`guard`](../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/guard.json).

Static `nc_backward` attribution showed that each broadcast-bias parameter
node invokes `nc_reduce_sum(existing_gradient, state_gradient, 1)`. Candidate
`nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1` therefore replayed the 64
chronological `[6144, 32]` state panels instead of flattening all 2,048
samples. The source operation reproduced every retained word exactly; the
flat control retained 4,708 mismatches and the reverse-state control retained
5,099. See its
[`decision`](../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T111831Z_64dcc1173e.json).

The immutable LibNC-free successor
`nncp_open_ff1_bias_state_reduce_64_q0_v1` then implemented the attributed
contract directly: decode the prior BF16 gradient, add streams 0 through 31
sequentially in float32, and round-to-nearest-even BF16 once after each state.
Two complete executions were byte-identical and matched all 6,144 independent
LibNC oracle words with zero error. The flat, reverse-order, and sign-negated
controls remained live; the executable had no LibNC, GGML, BLAS, or OpenMP
dependency. See the
[`decision`](../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/guard.json), and
terminal
[`reflection`](../operations/adaptive/reflections/20260816T112548Z_7841e2cc5b.json).

This retires both flattened bias accumulation and LibNC as an FF1-bias
dependency. It remains zero-credit teacher-removal evidence: no compression,
transfer, package, or Hutter result follows. The next unproven top-layer
parameter boundary is the `ff1_19` matrix gradient. Its gate must preserve the
same chronological graph-state accumulation rather than borrowing a flat
whole-population reducer.

## 2026-08-16 - The exact FF2 transpose uses ordered 128-feature panels

Two prospectively frozen arithmetic attributions resolved the 775-word
source/open FF2-input-adjoint boundary. The first mapped SIMD lanes to
adjacent output features and accumulated each lane through one unbroken
1,024-feature FMA stream. It was valid but worse: 929 of 6,291,456 source
BF16 words differed, with maximum absolute error
`2.9802322387695312e-08`. This retires the unblocked lane stream and shows
that identifying the inner kernel alone is insufficient. See its
[`decision`](../results/nncp_libnc_ff2_transpose_lane_order_64_q0_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T093214Z_c6950a77d0.json).

Static dispatch attribution then exposed the missing driver boundary: the
1,024-feature reduction is executed as eight ordered 128-feature panels. The
second candidate preserved adjacent-feature lanes, reset each lane
accumulator at every panel, and added each completed panel to the prior
output. Two complete executions replay byte-for-byte and reproduce every one
of the 6,291,456 independent source-adjoint words with zero error. The
horizontal and unblocked controls retain their distinct 775-word and
929-word mismatch populations, so the panel boundary is live. Parameter and
LibNC digests, strict outputs, source closure, memory, scratch, and cleanup
guards pass. See the
[`decision`](../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/execution.json),
[`guard`](../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T093907Z_7f51e2d346.json).

This authorizes one uniform open FF2-transpose implementation: adjacent
output-feature SIMD lanes, ordered 128-feature reduction panels, one panel
combination before the next panel, and one final BF16 conversion. It remains
zero-credit teacher-removal evidence and proves no GEGLU, FF1, recursive
update, compression improvement, transfer, package, or Hutter result.

## 2026-08-16 - The first remaining divergence is the FF2 transpose

Candidate `nncp_libnc_top_ff2_input_adjoint_64_q0_v1` placed a marked zero
probe on the production layer-19 GEGLU output immediately before `ff2_19` and
captured its complete backward adjoint twice. The frozen comparison withheld
the open residual until both source populations were complete and preserved
all non-probe fixture payloads.

The experiment is valid and its byte-identity hypothesis is refuted. Both
source captures replay exactly, expose all 6,291,456 expected BF16 input and
adjoint words, leave the production fixture unchanged, retain a live
comparator, and pass strict output, source, memory, scratch, and cleanup
guards. The source adjoint nevertheless differs from the open streaming
transpose residual in 775 words, with maximum absolute error
`2.9802322387695312e-08`. See the
[`decision`](../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/execution.json),
[`guard`](../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T090818Z_428a8e6c62.json).

This is the first measured divergence after the exact final-RMSNorm adjoint
and exact `ff2_19` parameter gradient. GEGLU backward is downstream of an
already-nonexact residual and is therefore not needed to explain the retained
`ff_bias1_19` mismatch. The current eight-lane streaming transpose is retired
as source-exact, but FF2 transpose itself is not. The next gate must compare
frozen arithmetic variants against the captured source adjoint before GEGLU
is reopened. This source oracle has zero objective credit and proves no
recursive update, compression improvement, transfer, package, or Hutter
result.

## 2026-08-16 - The first open GEGLU backward contract is refuted

Candidate `nncp_open_profile_top_ff1_bias_gradient_64_q0_v1` started from the
promoted exact final-RMSNorm input residual, regenerated both complete forward
populations with fresh layer-19 FF1 outputs, and applied one frozen backward
contract: streaming BF16 FF2-transpose dots, a BF16 transpose-output boundary,
the measured unfused tanh-GELU derivative, and explicit BF16 product
boundaries. The retained `ff_bias1_19` gradient remained unavailable until both
open projections were complete.

The experiment is valid and the hypothesis is refuted. Both populations and
their complete FF2-input and FF1-output residuals replay byte-for-byte, all
forward checkpoints remain exact, the sign-negated control changes, strict
outputs validate, and dependency, source, memory, scratch, and cleanup guards
pass. Nevertheless, 4,708 of 6,144 retained `ff_bias1_19` BF16 words differ,
with maximum absolute error `1.52587890625e-05`. Both the gate and value halves
contain mismatches, so the bias projection alone cannot distinguish the shared
FF2-transpose adjoint from branch-specific GEGLU arithmetic. See the
[`decision`](../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T084751Z_2949ede196.json).

This retires the combined contract, not FF2 transpose or GELU individually.
The next justified experiment must capture or independently validate the
production FF2-input adjoint before changing activation arithmetic. Tuning
against the retained bias vector is forbidden. This result has zero objective
credit and proves no FF1 matrix gradient, earlier-layer backward, recursive
update, compression improvement, transfer, package, or Hutter result.

## 2026-08-16 - The open tail is exact through the top FF2 gradient

Candidate `nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1` installed
only the source-attributed streaming eight-lane FMA reduction at the final
RMSNorm `g*y` dot. Its first job stopped during digest-bound preflight because
the wrapper retargeted an inherited antecedent checker; no scientific payload
was produced. The first immutable retry completed both populations and every
scientific comparison, but strict validation rejected its result because the
cloned output manifest still named the ancestor candidate. Both failures are
retained as implementation evidence in their terminal
[`preflight reflection`](../operations/adaptive/reflections/20260816T080014Z_9da1ba0532.json)
and
[`manifest reflection`](../operations/adaptive/reflections/20260816T080451Z_d5838c6e4e.json).

The manifest-only second retry preserved the C++ algorithm byte-for-byte and
reran the complete guarded population. The prospectively frozen gate passed
every predicate. Two independent 32-stream executions preserve all inherited
forward, output-head, final-normalization parameter, and projection results;
the complete final-RMSNorm input residual matches the independent source
adjoint in all 2,097,152 BF16 words; and all 3,145,728 retained `ff2_19`
gradient words are exact. Replay is deterministic, the residual-negation and
FF2-negation controls remain live, the strict nine-output manifest validates,
and dependency, source, memory, and scratch guards pass. See the
[`decision`](../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/execution.json),
[`guard`](../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json).

This opens the production backward tail from the output head through final
RMSNorm and the top-layer FF2 parameter gradient. It remains a zero-credit
teacher-removal result. It proves no FF2 input residual, GEGLU derivative,
`ff1_19` or bias gradient, earlier transformer backward, recursive update,
compression improvement, transfer, package, or Hutter result. The next frozen
boundary is the FF2 transpose residual through GEGLU into the top-layer FF1
and bias gradients.

## 2026-08-16 - The final RMSNorm discrepancy is the product reduction

The four-cell
`nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1` attribution crossed two
product-reduction orders with two algebraically equivalent scalar placements.
Both generic block-combined dot cells reproduced the retained open residual
and differed from the source adjoint in the same 8 BF16 words. Both ordered
eight-lane streaming FMA cells reproduced the independent source adjoint
exactly. Mean-scaled versus width-scaled placement was BF16-identical across
the complete population, so the frozen uniqueness hypothesis was refuted even
though the causal boundary became sharper.

This retires generic 64-element block combination as a source-equivalent
implementation of the final-RMSNorm `g*y` dot and retires scalar placement as
the cause on this population. It authorizes one uniform streaming reduction,
not coordinate patches or tolerance. See the
[`decision`](../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/execution.json),
[`guard`](../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T075342Z_b33521b4a0.json).

The attribution uses retained source tensors only as post-completion
comparators and has zero objective credit. No source executable, captured
adjoint, gradient, trace, or probability may enter a submitted codec.

## 2026-08-16 - The production top-layer FF2 adjoint is localized

The first `nncp_libnc_top_ff2_adjoint_64_q0_v1` job stopped before measurement:
its probe definitions were below their first call sites and lacked forward
declarations. The terminal
[`reflection`](../operations/adaptive/reflections/20260816T064522Z_bd9f01360c.json)
classifies that compiler failure as implementation evidence and preserves the
unchanged scientific predicates.

The declaration-only retry attached a zero-valued marked parameter after the
production layer-19 FF2 bias at the first retained update. Two complete source
executions each emitted the same 757-file population and aggregate hash. Every
non-probe file remained byte-identical to the retained production fixture, and
the combined source FF2 inputs, post-FF2 adjoints, reconstructed gradients, and
sign-negated controls replayed byte-for-byte.

The attribution is exact. Source input plus source adjoint under the frozen
128-sample reducer reproduces all 3,145,728 retained `ff2_19` BF16 words with
zero error. The open final-normalization input residual differs from the source
post-FF2 adjoint in 8 of 2,097,152 words across 8 output features, with maximum
absolute error `2.9802322387695312e-08`. This retires FF2 outer-product
reduction order as the cause of the prior 184-word mismatch and moves the next
boundary to an operation-level decomposition of the open final RMSNorm
per-sample adjoint. See the retry
[`decision`](../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/guard.json), and
terminal
[`reflection`](../operations/adaptive/reflections/20260816T065037Z_1d8853ab41.json).

This source capture is a zero-credit attribution oracle. No teacher
executable, LibNC dependency, captured tensor, gradient, trace, or probability
may ship in a submitted codec, and no compression, transfer, package, or
Hutter result follows.

## 2026-08-16 - The first top-layer FF2 reduction is narrowly refuted

Candidate `nncp_open_profile_top_ff2_gradient_64_q0_v1` retained the complete
exact output-head and final-normalization tails, exposed fresh BF16 layer-19
GEGLU outputs, and applied the promoted 128-sample output-head matrix-gradient
reduction directly to the complete `ff2_19` outer product. Both 32-stream
executions were byte-identical, every inherited comparator remained exact,
both negative controls changed, and dependency, source, memory, scratch, and
finalization guards passed.

The FF2 claim itself failed exactly: 184 of 3,145,728 retained BF16 words
differed, with maximum absolute error `9.5367431640625e-07`. This valid result
localizes the remaining discrepancy to operation-specific FF2 product or
reduction semantics. It retires direct reuse of the output-head reduction
without an FF2-specific arithmetic boundary; it does not weaken exact parity
or authorize tolerance. See the
[`decision`](../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T055603Z_52a69ff065.json).

The first immutable retry tested a uniform BF16 boundary after the final
RMSNorm incoming-gradient times gain product. It was a valid numerical no-op:
the digest-bound initial `ln_g_40` tensor is BF16 `1.0` in every coordinate,
and the retry reproduced both the normalization-input residual and `ff2_19`
gradient artifact hashes byte-for-byte, including the same mismatch set. This
retires that boundary at the selected update. See its
[`decision`](../results/nncp_open_profile_top_ff2_gradient_64_q0_retry_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json).

This experiment has zero Hutter objective credit. The next justified gate is
a zero-credit source capture of the actual production post-FF2 residual-join
adjoint. It must compare that complete per-sample tensor with the open
normalization-input residual before another arithmetic retry is authorized.

## 2026-08-16 - The complete final RMSNorm backward tail is open and exact

The first `nncp_open_profile_final_norm_backward_64_q0_v1` execution generated
both full open populations but failed during result finalization because its
runner removed the work tree before reading cached element counts. Its
terminal
[`reflection`](../operations/adaptive/reflections/20260816T045714Z_6eb299ed8d.json)
classifies that attempt as an implementation failure rather than scientific
evidence.

The first immutable retry fixed finalization, applied the already measured
concat-root centered RMSNorm input rule, and changed `ln_g_40` to the promoted
chunked reduction. Its valid result isolated two different outcomes. The
centered input residual reproduced every retained top-layer `ff_bias2_19`
projection word exactly, but the gain gradient retained the same mismatches as
the unchunked attempt. This retired reduction reassociation as the gain cause.
See its
[`decision`](../results/nncp_open_profile_final_norm_backward_64_q0_retry_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T051419Z_4df92ec3b4.json).

Candidate `nncp_open_profile_final_norm_backward_64_q0_retry_v2` changed one
remaining boundary: every per-sample normalized-state times incoming-gradient
product is rounded to BF16 before the unchanged reduction. The prospectively
frozen gate then passed every predicate. Both full executions reproduce all
retained output-head gradients, the promoted final-hidden residual, all
`ln_g_40` and `ln_b_40` words, and all `ff_bias2_19` projection words exactly.
The complete centered normalization-input residual replays byte-for-byte, both
negative controls remain live, the open executables have no forbidden dynamic
dependency, and source and resource guards pass. See the
[`decision`](../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/decision.json),
[`execution receipt`](../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/execution.json),
[`guard`](../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T053159Z_b79233ecb1.json).

This opens the complete production final-normalization affine and centered
input-backward tail. It proves no FF2 activation residual, GEGLU backward,
earlier normalization, attention, recursive training, transfer, archive
score, package eligibility, or full-corpus reconstruction and has zero Hutter
objective credit. The next frozen boundary is the complete top-layer
`ff2_19` parameter gradient from the exact normalization-input residual and a
fresh open GEGLU output.

## 2026-08-16 - The complete output-head activation residual is open

Candidate `nncp_open_profile_final_hidden_residual_64_q0_v1` advances the
exact open BF16 loss residual through the digest-bound initial `embed_out`
transpose. The standalone reducer consumes only decoder-visible targets,
freshly generated probabilities and final hidden states, and initial
parameters. It generates both complete activation-residual payloads before
hash-verifying or reading any retained gradient comparator.

The prospectively frozen gate passed every predicate. Two independent
32-stream executions emitted byte-identical 2,097,152-word BF16 final-hidden
residuals. Their broadcast reductions reproduce all 1,024 retained `ln_b_40`
gradient words exactly, while both previously promoted output-head parameter
gradients remain exact and the cyclic target-shift control changes. The open
executables have no forbidden dynamic dependency, the dependency-closed
incremental source remains within its frozen ceiling, and the guarded work
tree was removed. See the
[`decision`](../results/nncp_open_profile_final_hidden_residual_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_final_hidden_residual_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_final_hidden_residual_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T043203Z_ca54b4761d.json).

This independently validates the complete output-head activation residual by
an exact retained final-normalization bias projection. It does not provide a
direct retained comparator for every per-sample residual word and proves no
final-normalization gain or input gradient, transformer-layer backward,
recursive training, transfer, archive score, package eligibility, or
full-corpus reconstruction. It has zero Hutter objective credit. The next
frozen boundary reconstructs `ln_g_40` and the final-normalization input
residual separately, using the retained top-layer `ff_bias2_19` gradient as an
independent projection before entering the transformer block.

## 2026-08-16 - The complete output-head parameter gradient is open and exact

Candidate `nncp_open_profile_output_matrix_gradient_64_q0_v1` advances the
promoted BF16 loss residual through the complete open final hidden state. The
standalone reducer consumes only digest-bound initial parameters and state,
decoder-visible targets, and freshly generated probabilities and hidden
states. Both retained gradient comparators are hash-verified only after two
complete open payloads exist.

The prospectively frozen gate passed every predicate. Two independently built
32-stream executions match all 640 layer-input checkpoints, all 16,392
`out_bias` gradient words, and all 16,785,408 `embed_out` gradient words
exactly. Both gradients and the forward trees replay byte-for-byte, while a
cyclic target remap changes an independently reduced matrix slice. The open
executables have no forbidden dynamic dependency, the counted incremental
source remains below its frozen ceiling, and the guarded work tree is removed.
See the
[`decision`](../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T040455Z_f7722f8e27.json).

This removes the complete output-head parameter-gradient tail from the closed
teacher. It does not yet prove the residual propagated into the final hidden
state, normalization backward, any transformer layer, recursive training,
transfer, archive size, package eligibility, or full-corpus reconstruction. It
has zero Hutter objective credit. The next frozen boundary is the
`embed_out`-transpose activation residual, independently checked through the
retained final-normalization bias gradient before any deeper-backward claim.

## 2026-08-15 - The production loss-to-output-bias backward tail is exact

The first all-stream open backward attempt completed both forward populations
but failed before evidence finalization because its source packer treated a
candidate-owned materializer as a project tool. It also exposed a control-design
error: permuting target states preserves the target histogram and therefore
cannot change a bias-only gradient. The failed job and terminal
[`reflection`](../operations/adaptive/reflections/20260816T031213Z_57a9477621.json)
retain those defects as implementation evidence; its scientific hypothesis was
not tested.

Diagnosis from the independently generated outputs localized the remaining
arithmetic boundary. The production graph converts each per-sample F32 softmax
residual to BF16 before reducing the broadcast output bias. An F32-only
reduction was close but not identical. Candidate
`nncp_open_profile_output_bias_gradient_64_q0_retry_v1` preserves the complete
forward and loss population, applies that BF16 boundary explicitly, packages
candidate source without broadening the tool closure, and replaces the dead
state permutation with a cyclic vocabulary-successor target remap.

The guarded retry passed every frozen predicate. Two independently rebuilt
32-stream populations match all 640 retained layer-input checkpoints and all
16,392 BF16 output-bias gradient words exactly, with zero maximum error,
byte-identical replay, a live negative control, no forbidden dynamic
dependency, and a dependency-closed source package below its frozen ceiling.
See the
[`decision`](../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T033450Z_727c49438a.json).

This proves only the production negative-log-likelihood tail through
`out_bias`. It has zero objective credit and proves no output-matrix,
normalization, transformer-layer, embedding, recursive-training, archive,
transfer, package, or full-corpus result. The next teacher-removal boundary is
the output-matrix gradient and hidden-state residual generated from this exact
open BF16 logit residual.

## 2026-08-15 - One causal open production segment transition is exact

The post-update boundary is no longer an incumbent-state-only forward probe.
The retained post-update fixture first exposed a small arithmetic mismatch:
the complete open forward matched all tensors, while a scalar left-fold tree
reduction changed a subset of integer branch counts. Focused candidate
`nncp_open_branch_reduction_postupdate_64_q0_retry_v2` proved that the
previously promoted LibNC-order reducer eliminates the difference. Candidate
`nncp_ggml_postupdate_forward_parity_64_q1_retry_v2` then replayed the complete
retained next segment twice with exact tensor, topology, truth-path, and branch
parity. See its
[`decision`](../results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T021607Z_81c2c9ae94.json).

The first joint integration attempt was deliberately retained as an
implementation failure. Its canonical Adam reports and all recurrent-memory
layers were exact, but a separately duplicated output loop emitted `203`
parameter payloads differently. The resulting next-forward error was therefore
not evidence against the open update. Its
[`decision`](../results/nncp_open_profile_update_forward_chain_64_q0_v1/decision.json)
and
[`reflection`](../operations/adaptive/reflections/20260816T023511Z_83fa6c7a64.json)
record the non-equivalent treatment and authorize only an emitter retry.

Candidate `nncp_open_profile_update_forward_chain_64_q0_retry_v1` removes that
duplicate arithmetic. A reproducible source patch writes each predicted word
from the canonical exact Adam replay function immediately before its existing
comparison. Two fresh chains independently generate all `246` parameter
payloads, both complete pre-update forwards, all `20` target-stream recurrent
memory layers, and both complete next-segment forwards. The incumbent
post-update parameter and state containers are removed before the chained
forward. All `244` next-forward tensor groups and `896` arithmetic branches are
exact in both repetitions, with byte-deterministic outputs and no forbidden
dynamic dependency. The guarded run stayed below the frozen decimal-memory and
scratch limits. See the
[`decision`](../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/decision.json),
[`chain receipt`](../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/chain-receipt.json),
[`guard`](../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T024338Z_3839f396a6.json).

This is one causal open production segment transition, not recursive training.
Its dense gradients remain captured teacher outputs. It has zero objective
credit and proves no open backward pass, archive gain, transfer, package
economics, or full-corpus result. The next honest teacher-removal boundary is
an open backward pass that reproduces the same named dense gradients and then
feeds this unchanged update-to-forward chain. The best source-bound forecast
and target debt are unchanged.

## 2026-08-15 - Complete open production optimizer replay is exact

The segment-transition program now has a complete, retained production update
oracle. The Q0 through Q2 fixture attempts were terminal implementation
evidence: stale external digests, callback identity, and incomplete gradient
naming prevented a scientific conclusion. Candidate
`nncp_libnc_profile_update_fixture_64_q3_v1` corrected the shared callback
boundary by using the callback's opaque `NCParam` pointer as the parameter-name
key. Two fresh teacher executions then emitted byte-identical complete
fixtures. The retained local fixture contains all `246` dense gradients,
initial and final parameter/optimizer containers, initial and final recurrent
state, and the train-step `4` to `5` boundary. See its
[`decision`](../results/nncp_libnc_profile_update_fixture_64_q3_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json).

The first two official open-replay jobs stopped before arithmetic. Their
separate reflections preserve two general orchestration defects: a consumer
decoded the structured reflection decision as a scalar, then rejected the
empty scratch root that `enqueue-tool` had correctly pre-created. Measured
source and experiment bindings were not edited in place. Each repair received
a new candidate and prospective experiment, leaving both failed jobs
auditable.

Candidate `nncp_open_profile_adam_replay_64_q0_retry_v2` passed the resulting
gate. Its standalone Gamma-authored C++ implementation parses the retained
containers and reproduces the complete production update without calling
LibNC. It implements the exact 64-value reduction, per-tensor norm clipping,
step-five Adam correction, deterministic fast reciprocal square root, fused
update order, BF16 round-to-nearest-even, and biased low-word serialization.
Across `313,000,456` parameter words, `245` BF16 tensors, one F32 tensor, and
all variance tensors, both fresh reports are byte-identical and every mismatch
counter is zero. The dependency-closed source package is retained with the
[`decision`](../results/nncp_open_profile_adam_replay_64_q0_retry_v2/decision.json),
[`guard`](../results/nncp_open_profile_adam_replay_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T003855Z_aab09244b0.json).

This closes the optimizer and serialization oracle, not recursive training.
The dense gradients are still captured teacher outputs, the result has zero
objective credit, and no open backward pass, second-segment forward, archive
gain, transfer result, or full-corpus package exists. The next admissible gate
is a separately frozen post-update forward fixture and open
update-to-next-forward replay. Only after that passes may work claim one
causally continuous segment transition; open gradient generation remains the
larger teacher-removal blocker.

## 2026-08-15 - Open production arithmetic identity is exact

The retained Q18 GGML forward already matched every exported output tensor,
but its scalar left-fold tree reduction differed from LibNC by one integer
frequency count on a small subset of visited branches. Candidate
`nncp_ggml_profile_arithmetic_64_q0_v1` terminated both paths through the same
fixed Gamma range coder and independent decoder. Both payloads reconstructed
the exact frozen transformed symbols and had equal length, but their bytes
differed. The terminal
[`reflection`](../operations/adaptive/reflections/20260815T225004Z_10e9a0f5af.json)
therefore retires one-count branch tolerance as sufficient codec-boundary
evidence. It does not reject the open GGML forward or the Gamma coder.

Candidate `nncp_ggml_profile_arithmetic_64_q1_v1` changed only that final
reduction. Its counted source reconstructs LibNC's 64-value AVX reduction,
masked-tail semantics, and binary partial accumulation; model parameters,
forward tensors, softmax, quantizer, coder, fixture, and population remained
frozen. The prospective
[`experiment`](../operations/adaptive/experiments/nncp_ggml_profile_arithmetic_64_q1_v1.json)
required zero frequency drift rather than preserving Q18's tolerance.

The guarded run passed. Every visited integer branch frequency is exact, both
open tree paths repeat byte-for-byte, oracle/open/repeated-open payloads are
identical, and all three payloads independently decode the exact symbols. See
the [`decision`](../results/nncp_ggml_profile_arithmetic_64_q1_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T230010Z_836682be9c.json).
This is a real open-runtime correctness gain with zero objective credit: it
proves one production-profile segment, not online parameter updates,
multi-segment continuity, package economics, transfer, or archive improvement.

The next admissible integration had to preserve this exact arithmetic boundary
while exposing the segment transition explicitly. Candidate
`nncp_ggml_profile_memory_transition_64_q0_v1` compiled LibNC's visible
`mem_update` rule into a counted shift-and-append transform. For every layer it
independently combined the retained initial teacher memory with either the
ordered teacher layer inputs or one of two open executions. All layer states
match byte-for-byte and all three aggregate state digests are identical. See
the [`decision`](../results/nncp_ggml_profile_memory_transition_64_q0_v1/decision.json),
[`state receipt`](../results/nncp_ggml_profile_memory_transition_64_q0_v1/state-digests.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T231108Z_4912fe7f1f.json).

This removes memory movement as the blocker, but it does not authorize a
fixed-parameter second segment. The incumbent also computes full deep
gradients, clipping, optimizer moments, and updated parameters after each
production segment. The next honest boundary is therefore a prospectively
frozen full-update receipt, followed only after a pass by a later-segment
oracle. Generic prefix compressor jobs for these infrastructure descriptors
remain held because they would compare different work.

## 2026-08-15 - Direct-F32 named-gradient oracle retires the localization lineage

The q0 named-gradient implementation reached the first production F backward
pass and reproducibly aborted at `libnc.c:7564`: `nc_free_tensor` observed an
already-consumed tensor reference. The defect is localized: LibNC's
`nc_tensor_isfinite` consumes its input, while q0 passed the callback-owned
gradient without first duplicating the reference. The
[`reproduction guard`](../results/delta_midas_named_midpoint_gradient_65536_q0_v1/abort-reproduction.guard.json)
records the same `SIGABRT` under the declared memory and scratch bounds.

Candidate `delta_midas_named_midpoint_gradient_65536_q1_v1` is an immutable
implementation retry. Its
[`experiment contract`](../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q1_v1.json)
changes only reference ownership by calling `nc_tensor_isfinite` on a duplicate
and makes subprocess failure streams durable. Population, F-arm behavior,
grouping, thresholds, repeats, promotion, kill conditions, and zero-credit
boundary are unchanged. Q0 remains terminal implementation evidence; q1 must
still prove both exact archives and complete deterministic rows before any
gradient localization conclusion is allowed.

Q1 then preserved the native stream and exposed the next exact defect:
`nc_get_scalar_f32` rejected the non-F32 squared-energy reduction. Its
[`reflection`](../operations/adaptive/reflections/20260815T172412Z_47ccd874f6.json)
again leaves the scientific hypothesis untested. Candidate
`delta_midas_named_midpoint_gradient_65536_q2_v1` is frozen from q1 with the
new implementation-retry composer: every scientific field and predicate is
inherited, while the runner, materializer, parent revision, negative control,
failure evidence, outputs, and declared implementation delta are rebound. Q2
converts only the completed BF16 squared-energy reduction to `NC_TYPE_F32`
before the scalar read. That restores the scalar-reader type contract but does
not make the accumulated energy authoritative: a direct F32 reducer must
re-evaluate the unchanged localization predicates before any group ablation can
be authorized. Agreement with q2 is a sensitivity diagnostic, not a promotion
condition, because q2's low-precision ranking is not scientific ground truth.

Q2 subsequently completed both encodes with byte-identical retained F archives
and identical complete named-gradient rows. Its schema and semantic receipt
validation pass, including the 64-state block coordinates, parameter coverage,
artifact hashes, and predicate derivation. The low-precision summary selects
feed-forward overall but not in every chronological third, falls below the
frozen minimum-third share, and remains output-head dominated. Those values are
retained as sensitivity evidence only. The terminal
[`reflection`](../operations/adaptive/reflections/20260815T172824Z_465e6837f4.json)
classifies the ranking as incomplete evidence, authorizes `retry`, and retires
only post-reduction F32 conversion as an authoritative localization oracle.

Candidate `delta_midas_named_midpoint_gradient_65536_q3_v1` was frozen from
that reflection. Its
[`experiment contract`](../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q3_v1.json)
binds the direct reducer, explicit F32 reference, complete runtime source and
JSON-contract closure, q2 decision/detail/reflection, retained F comparator,
exact midpoint patch, and strict output set before execution. Direct-reference
finiteness and relative agreement are prerequisites for both promotion and
retirement. Q2 comparisons are diagnostic only. Q3 remains closed-teacher,
zero-credit attribution; it cannot claim codec savings or objective progress.

Job `20260815T200718Z_9b504935f5` completed both encodes under the declared
process-tree memory and scratch guard. The two archives are byte-identical to
each other and to retained F, the two complete named-gradient tables repeat
exactly, and every direct-F32 energy equals its independent explicit-F32
reference. The valid result remains output-head dominated. Feed-forward is the
largest non-head group overall but the dominant non-head group changes across
chronological thirds, and the minimum-third share misses its prospectively
frozen threshold. See the [`decision`](../results/delta_midas_named_midpoint_gradient_65536_q3_v1/decision.json),
[`gradient detail`](../results/delta_midas_named_midpoint_gradient_65536_q3_v1/gradient-detail.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T200718Z_9b504935f5.json).

The exact hypothesis is refuted: squared-gradient energy does not select one
stable deep midpoint parameter group on the frozen production F population.
No group ablation is authorized, and this entire localization lineage is
retired with zero objective credit. The result does not refute a multi-group,
signed-logit, Hessian, activation-residual, or decoder-visible causal
mechanism. The next experiment must be materially different and prospectively
bound; it may not inherit teacher energy, archive savings, or score credit.

## 2026-08-15 - Named production midpoint-gradient localization is prospectively frozen

Candidate `delta_midas_named_midpoint_gradient_65536_q0_v1` is the next
bounded teacher attribution after the positive deep F-versus-O residual and
the negative compact hashed-linear probe. Its structured
[`experiment contract`](../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q0_v1.json)
binds the exact `65,536`-symbol production population, the legacy attribution
receipt that names retained F, closed-source inputs, immutable parent revision,
analyzer, materializer, two repeat encodes, and zero-credit boundary. That
legacy receipt carries the retained archive digest, but q0 through q2 do not
bind the archive itself as a separate prospective input; their archive-identity
measurement is therefore useful execution evidence, not a tamper-evident
comparator boundary.

The only changed mechanism is observation: during each F-arm first-half
midpoint backward pass, the instrumented teacher emits the stable `NCParam`
name, gradient shape, hash, finiteness, and squared gradient energy. The
instrumented archive must remain byte-identical to retained F, both encodes and
complete named-gradient rows must repeat exactly, and every block must expose
the same parameter set. A successor is authorized only if one non-head group
is dominant in every chronological third, its minimum share of non-head energy
is at least `0.35`, and the output-head share of total energy is at most `0.5`.

Passing selects exactly one separately preregistered group-ablation arm.
Failing the localization thresholds with all integrity predicates intact
retires gradient-energy localization. Gradient magnitude is not probability
attribution, the closed LibNC teacher remains unshippable, and this run cannot
claim archive savings, an open correction, transfer, package economics, or
objective bytes.

The first queued execution, job `20260815T170528Z_778414d866`, stopped before
the teacher began because the guard required its declared result scratch
directory to pre-exist. The terminal
[`reflection`](../operations/adaptive/reflections/20260815T170528Z_778414d866.json)
classifies this as an infrastructure failure and leaves the hypothesis
untested. The general executor boundary now records candidate-owned scratch
directories in the job, constrains them below `results/<candidate_id>/`, and
materializes them before guard preflight. Retry job
`20260815T171447Z_33eeb89e5c` retains the same experiment, candidate revision,
proposal, and runner bindings while adding that explicit lifecycle input.
That retry confirmed the lifecycle fix and entered the first instrumented F
encode, then NNCP terminated with `SIGABRT` before archive completion. Peak
sampled process-tree RSS remained below the declared guard; the terminal
[`implementation reflection`](../operations/adaptive/reflections/20260815T171447Z_33eeb89e5c.json)
keeps the hypothesis untested. Because the analyzer discarded captured native
stderr when `check=True` raised, the next action is an exact stream-preserving
reproduction, not a localization conclusion or parameter sweep.

## 2026-08-15 - Fixed decoder-visible DELTA-MIDAS probe is terminal negative

The first prospective successor to the deep-residual receipt is terminal
`REJECT`. Candidate `delta_midas_decoder_feature_probe_65536_q0_v1` froze one
`4,096`-weight hashed-linear model, four normalized online passes, chronological
train/validation/test partitions, int16 replay, an `8,200`-byte payload ceiling,
and a one-segment shifted-label control before execution.

The experiment was causally valid but lost `887.0184641356755` ideal bits on
validation and `1,080.7027626223207` on sealed test. Every test third was
negative, only `13` of `171` test segments improved, and the aligned treatment
was `696.9629361023035` bits worse than the shifted-label control. See the
[`decision`](../results/delta_midas_decoder_feature_probe_65536_q0_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T162913Z_047c55d5ea.json).

This retires the exact feature map, optimizer, clipping, partition,
quantization, and O-offset replay contract without sweeps. It does not refute
the measured deep teacher residual. Any recurrent or low-rank successor must be
a materially new, prospectively bound mechanism; it cannot be a parameter retry
or inherit archive bytes, transfer, package economics, or score credit.

A source-bound design audit confirms that LibNC exposes stable `NCParam` names
at the midpoint backward callback (`embed`, output head, attention, feed-forward,
normalization, and per-layer parameters). The next justified teacher action is
the now-frozen F-arm midpoint-only named gradient projection above, summarized
by group and chronological third. Its only possible consequence is selection
of one later group-ablation arm; gradient magnitude is not itself probability
attribution. It remains zero-credit teacher work.

## 2026-08-15 - DELTA-MIDAS deep residual survives exact retained-trace gate

Terminal candidate
`nncp_libnc_output_head_midpoint_attribution_65536_qm1_v1` closes the
output-head theory. On its same-run population, rebuild-only `K` is `148,141` bytes, full midpoint `F` is
`143,414`, and output-head-only `O` is `148,709`. Thus F beats K by `4,727`
bytes while O is `568` bytes worse than K. The earlier bridge reports `4,726`
because its parent archive is one byte smaller; those values come from
different exact runs and are not combined. The terminal decision remains a
four-thread closed-LibNC teacher result with zero score credit.

Proposals `nncp_gram_midas_full_hidden_65536_qm0_v1` and
`gamma_orbit192_gram_midas_65536_qm0_v1` are retired because both depended on
an output-head gain that does not exist. Their rejection receipts preserve the
closed neighborhood; the ORBIT feature idea is not inherited into a new result.

Experiment `delta_midas_deep_residual_65536_q0_v1` retrospectively froze an
exact F-versus-O retained-trace analysis before its analyzer emitted a result.
All `65,536` rows and `917,527` truth-path branches aligned. On second halves,
F beats O by `22,783.981772296793` ideal bits. All original-coordinate thirds
are positive, and `1,001` of `1,024` segments are positive. See
[`decision.json`](../results/delta_midas_deep_residual_65536_q0_v1/decision.json)
and the hash-linked
[`reflection`](../operations/adaptive/reflections/20260815T161658Z_636aa4dd6c.json).

The result localizes useful information beyond the output head and authorizes
only one prospectively frozen decoder-visible feature-capture experiment. It
does not show realizable archive savings, a compact student, transfer, package
cost, or Hutter score credit. Hidden state, teacher probabilities, and the
closed LibNC executable remain forbidden submission inputs.

The running q2 named-gradient retry has a separate numeric-validity boundary.
The production profile defaults parameters to BF16, and q1's retained native
[`nc_get1_f32` assertion](../results/delta_midas_named_midpoint_gradient_65536_q1_v1/F_named_gradient_1.stderr)
proves the squared-energy reduction did not produce an F32 tensor. The
[`q2 materializer`](../tools/materialize_nncp_named_midpoint_gradient_q2.py)
converts only after the BF16 elementwise square and reduction, so it repairs
the scalar-reader crash but does not establish precision-stable group shares.
The hash-bound LibNC binary exports `nc_reduce_sum_sqr`; its implementation
creates an F32 scalar and dispatches BF16 inputs through the direct
`vec_sum_sqr_bf16` F32 accumulation path. Therefore q2 may retain archive,
gradient-hash, coverage, and implementation-liveness evidence, but its energy
ranking cannot by itself authorize a group ablation. The smallest valid
measurement retry replaces only the energy expression with
`nc_reduce_sum_sqr(nc_dup_tensor(gradient))`, repeats both exact F encodes, and
cross-checks every value against an explicit BF16-to-F32 multiply-and-sum path.
Both paths must be finite and pass the frozen relative-error bound before the
original group and chronological-third predicates can authorize or retire an
ablation. Agreement with q2 remains diagnostic because q2's BF16 ranking is not
an oracle. Q3 also binds retained `F_clean.nncp` directly and checks its path,
byte count, and digest against the legacy attribution receipt before starting
the teacher, closing the comparator-identity gap instead of inheriting it.

## 2026-08-15 - Recursive self-improvement boundary audited

The adaptive lane now binds the objective, immutable candidate revisions,
structured experiments, terminal reflections, evidence-aware selection,
dependency packaging, and clean-room receipt composition. The executor uses
three fresh builds, two archive-identity runs, and a corpus-blind decode under
sealed one-core resource guards. It is still not authorized for unattended
mutation or prize-facing promotion because no eligible Gamma candidate has
produced a complete full-1G package receipt or second-host identity receipt.
See [`recursive_self_improvement_system_audit.md`](recursive_self_improvement_system_audit.md).
Missing roundtrip, determinism, process-tree resource, dependency-closure, or
peer evidence still fails closed.

## 2026-08-09 - Agent A/B strategy and ownership merge under the 105M target

Agent B has accepted Agent A's handoff and now owns both active scientific
tracks. The canonical objective is an exact, self-contained full-1G score no
larger than `105,000,000` bytes. `cmix-obias` is David Freelan's externally
authored submission candidate, derived from Ibrahim Marcouch's `cmix-lex` and
earlier cmix/PAQ work; Gamma did not invent it and cannot treat reproduction as
a Gamma prize entry. Its reported `108,492,825` score leaves `3,492,825` bytes
of counted debt to the project target. The active full-corpus jobs are
zero-credit external-baseline, provenance, determinism, and resource evidence
only. They may support an independently novel, fully attributed Gamma child,
but they cannot satisfy the objective by themselves. KAIROS was the first
same-stream Gamma correction test, but its completed paid opening replay
retired the frozen dyadic final-head realization; it is no longer a promotion
path.

The independent NNCP lane has now confirmed that the changed update cadence
persists over `1,998,848` symbols, saving `82,432` actual encode-only archive
bytes. That teacher result authorizes the predeclared production-alphabet
state-refresh/output-head/full-update attribution and, only if attribution
passes, a compact MIDAS-style descendant.

The external cmix-obias baseline and NNCP teacher lanes do not inherit or add
projected savings. Only a separately attributable Gamma mechanism may enter
the winning path, and any use of upstream code requires complete attribution
and compliance with its authorship and licensing boundary. A future
combination is authorized only after the new mechanism independently passes
its paid gate, and then only through a new exact joint coder replay with
complete package and memory accounting. The XML-safe far-history/copy family
and the measured KAIROS dyadic realization remain terminally closed.

## 2026-08-09 - Local cmix-obias archive and source snapshot are hash-bound

The previously external-only cmix-obias evidence is now present locally under
`/home/x/enwiki9-nonproof/cmix-obias-donor`. The tracked outer repository is
clean at commit `51488a0c1228dbeab7c1be837fc90ceaed351728`; its tracked
`cmix-obias` subtree has Git tree
`23de249ff899db5ba84dd3514a6a1bb52a83d0f5`. Untracked entries are confined to
the locally provisioned Clang, LLD, compatibility-library, and UPX tools.

The local `final/archive9` is exactly `108,009,834` bytes with SHA-256
`664823c5d9f167bda342745d7b34a3ccb98fd7108723ba83643d9d09bf693900`,
matching the public submission claim. The local packaged compressor is
`459,989` bytes with SHA-256
`eee69c879f4bbd58015efd4d34f55c6dc986ec818fa68c2f32a9ee5ab5568f68`;
the required head blob is `23,002` bytes with SHA-256
`35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078`.
Their arithmetic total is the claimed `108,492,825` bytes.

This advances artifact availability and provenance only. No completed local
full decode, repeat encode, strict-memory qualification, runtime qualification,
or Gamma score credit exists. The root filesystem has only about `15 GB` free,
but the later RAM-backed qualification entry records the safe `/dev/shm`
workspace used by the active decode. No unrelated workspace data was removed
to manufacture capacity.

This register tracks strategy and algorithm research separately from measured
candidate proof. It is a map from idea to local implementation, not a scoreboard.

Claim rule:

```text
Research status is not compression proof.
Promotion requires exact receipts: result JSON, shadow-coder receipt, or guard
receipt depending on the lane.
```

Current proof boundary: the active target is `105,000,000` counted bytes
(`10.5000000%`). The best source-bound forecast is
`endpoint428_gate_dot_fuse_output_update_loop_v1` at `109,389,323` bytes, a
signed target distance of `+4,389,323` bytes before any successor's additional
program, model, table, metadata, or framing cost. The verified exact full-1G
score remains unknown. The current official one-percent prize ceiling is
`109,685,196`; it is an eligibility boundary, while `105,000,000` remains the
research stopping condition. Older `108M`, `109.5M`, `10.95%`, `109,498,879`,
and `109,452,151` targets or forecasts are historical evidence only and do not
control new promotion decisions.

The mature negative record closes fixed mixer blends, width/cell adjustments,
simple residual calibration, explicit phrase-copy commands, and metadata-heavy
semantic partitions as primary routes. Current work therefore requires a new
decoder-visible information source or reversible representation with
million-byte leverage, plus an open self-contained CPU realization. NNCP
midpoint receipts remain causal teacher evidence but are not prize-facing
while they depend on closed LibNC and an ineligible runtime. Native promotion
still requires exact same-object replay, complete package accounting,
determinism, raw reconstruction, decimal-memory compliance, and eventually an
official full-1G receipt at or below the active target.


## Archived entries

Older entries are stored by complete H2 record in [research_register/archive/](research_register/archive/README.md).

- [part-001.md: Novelty Portfolio Contract through 2026-07-26 VULCAN V0 event-control result](research_register/archive/part-001.md)
- [part-002.md: 2026-07-26 D02 TWINSTREAM opening-1M terminal decision through 2026-07-26: official NNCP v3.3 CPU eligibility control](research_register/archive/part-002.md)
- [part-003.md: 2026-07-26: delayed raw, heading, AUTOPSY-rule, and compact-neural closure through 2026-07-27: PCMF-1 paid context-two multinomials are terminal negative](research_register/archive/part-003.md)
- [part-004.md: 2026-07-27: CBM-1 label-free causal block mixture theorem through 2026-07-28 - CHIRON frozen causal residual Q0 - REJECTED](research_register/archive/part-004.md)
- [part-005.md: 2026-07-28 - ROCm batched causal teacher - REJECTED through 2026-08-01: MOBIUS-2 NOEMA binary-carry hierarchy is terminal negative](research_register/archive/part-005.md)
- [part-006.md: 2026-08-01: Typed Event Sleeping Bayes Envelope and parent recovery through 2026-08-02: MÖBIUS-2 frontier-teacher WRT event alphabet QH0 frozen](research_register/archive/part-006.md)
- [part-007.md: 2026-08-02: MÖBIUS-2 frontier-teacher WRT event alphabet is terminal negative through 2026-08-02: LibNC FF2 output adjoint localizes the missing gradient upstream](research_register/archive/part-007.md)
- [part-008.md: 2026-08-02: LibNC FF2 residual-adjoint replay frozen through 2026-08-02: MÖBIUS-2 JANUS parity token-fill ceiling frozen](research_register/archive/part-008.md)
- [part-009.md: 2026-08-02: MÖBIUS-2 JANUS parity token-fill ceiling is terminal negative through 2026-08-02: endpoint428 runtime-eligibility boundary re-audited](research_register/archive/part-009.md)
- [part-010.md: 2026-08-02: WIKIFORWARD prior-destination lexical ceiling proposed through 2026-08-03: corrected WIKISECTION exact-heading ceiling rejected](research_register/archive/part-010.md)
- [part-011.md: 2026-08-03: WIKIFORWARD prior-destination lexicon QM1 materialized through 2026-08-08 - HELICAL direct-WRT far-history QM3 closure](research_register/archive/part-011.md)
- [part-012.md: 2026-08-08 - NNCP/Endpoint common-raw-block routing closure through 2026-08-08 - NNCP midpoint persistence replicated at 262,144 symbols](research_register/archive/part-012.md)
- [part-013.md: 2026-08-08 - Exact native 65,536-symbol raw-proof guard corrected through 2026-08-09 - Exact output-head attribution maps to LibNC optimizer semantics](research_register/archive/part-013.md)
- [part-014.md: 2026-08-09 - Mature train-length retry crosses first block boundary through 2026-08-09 - Shared research-register partition is lint-enforced](research_register/archive/part-014.md)
- [part-015.md: 2026-08-09 - Exact decision-ID coverage reconciled across the shared register through 2026-08-09 - Exact KAIROS opening retires the final-head dyadic realization](research_register/archive/part-015.md)
- [part-016.md: 2026-08-09 - GGML output-head gradient and update parity proposed through 2026-08-09 - GGML head q1 exposes the direct-optimizer API boundary](research_register/archive/part-016.md)
- [part-017.md: 2026-08-10 - Full-score accounting q0 isolates one fixture-size error through 2026-08-10 - Conservative cmix-obias package boundaries are certified](research_register/archive/part-017.md)
- [part-018.md: 2026-08-09 - Branch-residual-weighted cache-32 proposed through 2026-08-09 - Historical FRACTAL-8 survival-hazard result recovered and retired](research_register/archive/part-018.md)
- [part-019.md: 2026-08-10 - Production output-head attribution is dependency-frozen through 2026-08-09 - cmix-obias technical source/runtime closure frozen](research_register/archive/part-019.md)

## Current entries

## 2026-08-10 - Production-alphabet midpoint bridge passes exactly

Candidate `nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1` terminated
successfully on `65,536` symbols from the real `16,392`-symbol dictionary and
the corresponding `322,978` raw bytes. The faithful parent archive is
`148,140` bytes and the midpoint archive is `143,414` bytes, for an actual
gain of `4,726` bytes against the frozen `3,000`-byte gate. Exact
original-coordinate third gains are `1,593`, `1,775`, and `1,359` bytes; every
third is positive.

Clean and traced parent archives are byte-identical with SHA-256
`e4f1b99393bee047d5ee809182d0f0ace2fb5391b37d960d26ab0df878c2842b`.
Clean and traced midpoint archives are byte-identical with SHA-256
`85208cda0ab962d7f8ce61367e0902c0bb864de05e57e733534f782b54736134`.
Both decodes reproduce the same exact `322,978`-byte raw population with
SHA-256 `a5daeae040c2575ae1c2fd5f3284d73caafa0fcd48c3f546e199ab7c5f1ab7e9`.
The serialized schedule is valid: segment `64`, midpoint enabled, batch `32`,
seed `123`, BF16 enabled, CUDA disabled, vocabulary `16,392`. There are no
failed conditions.

The terminal guard reports return code `0`, peak single-process RSS
`6,380,124 KiB`, peak process-tree RSS `6,419,324 KiB`, and zero excess over
the decimal `10 GB` limit. This authorizes production `P/K/O/OK/F/S`
attribution scientifically but remains a four-thread closed-LibNC teacher
result with zero score credit, no single-core eligibility, no full-corpus
transfer, and no verified score. Under the frozen Gamma One order, proposal
`nncp_ggml_profile_forward_parity_64_qm0_v1` was activated and developed next;
attribution remains blocked until that parity candidate itself passes.

## 2026-08-10 - Gamma One compiles MIDAS into GRAM and ORBIT

The post-bridge Gamma path is now frozen as `Gamma One`: the reversible NNCP
symbol transform feeds a Gamma-authored, deterministic, single-thread CPU
predictor, a branch-local `GRAM-MIDAS-32` fast-weight correction, one integer
arithmetic stream, and the exact inverse. The 20-layer LibNC/GGML NNCP model is
an oracle and parity reference, not the intended submission codec. No teacher
archive, hidden trace, probability, or package normalization transfers to the
student.

The exact sequence is dependency-bound: terminal production bridge, open
one-segment profile parity, production `P/K/O/OK/F/S` attribution,
`nncp_gram_midas_full_hidden_65536_qm0_v1`, then
`gamma_orbit192_gram_midas_65536_qm0_v1`. Attribution cannot activate from the
bridge alone; it now also requires the parity receipt. GRAM cannot activate
without an attribution verdict explicitly authorizing it, and ORBIT cannot
activate without a GRAM verdict explicitly authorizing it. Both new proposals
have `operational_status=blocked_dependency` and zero score credit.

GRAM replaces a dense `16,392 x 1,024` midpoint mutation with sparse ephemeral
branch state. For each first-half truth-path branch, it accumulates the decoded
truth residual times a causal feature vector plus an intercept residual. It
then corrects only queried second-half branch logits using frozen counted
depth scales. The full-hidden gate requires an actual terminated arithmetic
gain of at least `ceil(0.90*G_O)`, positive original-coordinate thirds, a
shifted-truth margin of at least `ceil(0.10*G_O)`, exact symbol and raw inverse,
byte-identical replay, no deep midpoint rebuild, source no larger than `32,768`
bytes, and decimal-memory compliance. Any miss retires this formulation rather
than opening a rank, optimizer, tree, scale, or coefficient sweep.

ORBIT is one frozen `192`-dimensional causal feature engine: decoded dictionary
symbol, decoder-rebuilt structural mode, short hashed symbol contexts, compact
recurrent state, and bounded gated-delta memory. It optimizes the
residual-weighted first-half/second-half Gram geometry that affects truth-path
arithmetic bytes, not generic hidden-state error. Promotion requires its own
exact archive to retain at least `max(ceil(0.60*G_F), paid scope requirement)`,
positive thirds, failing shifted/permuted controls, exact deterministic inverse,
one runnable CPU thread at at least `1,500` transformed symbols/second,
incremental compressed source and parameters no larger than `131,072` bytes,
and decimal-memory compliance. A miss retires the fixed ORBIT-192 profile.

The counted targets remain distinct: prize lock below `109,685,197`, primary
Gamma objective at most `105,000,000`, and stretch `101,101,101` only after a
certified record exists. The official site currently identifies the eighth
winners, record `110,793,128`, an ongoing contest, and the single-core,
memory, disk, and self-containment boundary. Any eventual public claim must be
about a transparently AI-led new record after official verification, never the
first solution of a contest with prior winners. External theory motivating
test-time learning remains zero-credit context: `https://arxiv.org/abs/2407.04620`.

## 2026-08-10 - External cmix full-corpus jobs intentionally cancelled

The three live `cmix-obias` full-corpus jobs were intentionally terminated at
the user's direction after the authorship boundary was corrected. The external
bare decode had reached `16.38%`; source-built encodes A and B had each reached
`9.03%` with identical emitted-byte progress. These jobs tested David
Freelan's external candidate and supplied zero Gamma score or authorship
credit; they are no longer on the Gamma prize path.

Exact driver process groups were sent `SIGTERM`. The adaptive guards closed
with process return code `-15` and the worker registry records `241`; neither
value is a codec, roundtrip, compression, or memory verdict. Two independently
sessioned `cmix` children survived their drivers and were then terminated by
their exact process groups. No `cmix`, `archive9`, or external-candidate worker
remains. The NNCP production midpoint bridge was not targeted and remains the
sole active job.

The killed drivers could not execute normal temporary-directory cleanup.
Three exact incomplete regenerable `/dev/shm` scratch directories totaling
about `12.9 GB` were deleted after process verification; durable logs, guard
receipts, source/build certificates, and accounting receipts remain. This
operator cancellation does not retire the external codec scientifically and
does not create a full-1G result. It removes external qualification work from
the active resource budget so the Gamma-authored MIDAS/open-predictor route
can proceed without its CPU, memory, or memory-bandwidth contention.

## 2026-08-10 - Open GGML production-profile forward parity is dependency-frozen

Proposal `nncp_ggml_profile_forward_parity_64_qm0_v1` closes the explicit
decoder-eligibility step after the already passed GGML kernel and output-head
update parity gates. Direct inspection of the production `enwik9` profile
binds the specialized transformer to `20` layers, model width `1,024`, `8`
heads, key width `128`, inner width `3,072`, memory `256`, and segment length
`64`. This is a deliberate profile rewrite, not a generic shim for the roughly
`71` reachable closed LibNC calls.

The proposal is machine-blocked on a passing full-dictionary native midpoint
bridge. Once activated, it compares one receipt-bound LibNC segment with an
MIT GGML CPU implementation loaded from the same parameters and
decoder-visible memory. It requires deterministic finite hidden, key/value,
logit, tree, and branch outputs; at most `1e-5` matched tensor error; at most
one integer probability count of branch error with no truth-path disagreement;
a static source closure no larger than `2,000,000` bytes; and decimal-memory
compliance. A pass authorizes one full open forward archive screen only.

This is zero-credit source-eligibility infrastructure. It cannot inherit the
teacher archive, midpoint gain, or package normalization, and it cannot run
before the bridge verdict
`authorize_production_P_K_O_OK_F_S_attribution`. A miss retires the exact
profile port without tolerance, layer, dtype, or kernel sweeps. Evidence: the
proposal, archived part 019, GGML kernel q1, GGML head-parity q2, and the LibNC
source-eligibility audit q3.

## 2026-08-10 - Production bridge passes and fixed-shape parity is materialized

The production bridge is terminal PASS: parent `148,140` bytes, full midpoint
`143,414` bytes, and actual gain `4,726` bytes against the frozen `3,000`-byte
gate. Independently terminated original-coordinate thirds save `1,593`,
`1,775`, and `1,359` bytes; their one-byte nonadditivity against the whole
archive is termination overhead, not an additive archive decomposition. Clean,
traced, and repeated archives are identical, all `65,536` symbols decode, the
`322,978`-byte raw inverse is exact, the schedule matches, and strict decimal
memory passes. This is decisive zero-credit teacher evidence on the real
`16,392`-symbol representation, not a submission score.

The inherited `32 x 256` output-head scaffold has been removed from
`nncp_ggml_profile_forward_parity_64_qm0_v1`. Its replacement freezes stream
zero at original truth coordinates `[256,320)`, the earliest 64-symbol segment
whose complete 256-symbol memory is decoder-visible. A patched LibNC oracle
exports ordered, hashed parameters, selected-stream memory and input, causal
mask, relative tensors, every layer checkpoint, final logits/probabilities,
and the exact balanced-tree branch path. The fixture is explicitly zero-credit
and forbidden as a runtime dependency.

The open side is now a static CPU-only profile implementation: 20 layers,
width 1,024, eight 128-wide heads, GEGLU inner width 3,072, memory 256,
segment 64, relative span 320, and vocabulary 16,392. GGML performs fixed BF16
matrix products; the candidate explicitly implements the frozen BF16
conversion points, RMSNorm, relative shift, causal mask, attention softmax,
residual order, tanh GELU, output softmax, numerical symbol tree, and integer
probability quantization. Both the oracle extractor and open source closure
compile; the compressed open source closure is about 1.174 MB, below the
2.000 MB ceiling. No teacher or open forward has yet been executed under this
candidate, so it still has zero parity or score credit.

The first qm0 launch stopped after the frozen-input audit and before model
initialization. Its handwritten expected identity table contained incorrectly
transcribed digests; the actual pristine source is unchanged since July 26 and hashes to
`9a44757c4837607b0be9abc0bb2780dbe006b381728549481eedc339599a138a`.
An independent preflight then rebound the unchanged LibNC library,
preprocessed symbol stream, dictionary, and terminal bridge decision to their
complete measured SHA-256 values before qm1 could launch. The donor tarball,
source size, and all bound artifact bytes remain unchanged.
Peak sampled RSS was only `1,332 KiB`; therefore qm0 supplies no forward,
parity, compression, or memory evidence. Correction-only successor
`nncp_ggml_profile_forward_parity_64_qm1_v1` changes only those expected
identity constants and candidate/result names while preserving every
scientific parameter and gate.

Qm1 passed every corrected artifact identity and initialized the full teacher,
but terminalized before fixture export because its source patch instrumented
the `--encode_only` batch branch while the passing bridge and decodable archive
use the true sequential branch. It consumed `2,226.996` seconds, peaked at
`6,380,244 KiB` single-process and `6,417,024 KiB` process-tree RSS, and stayed
under the decimal limit. No fixture marker, open forward, tensor comparison, or
parity verdict exists, so this is an infrastructure rejection with zero
scientific or score credit.

Correction-only qm2 moves capture to the decoder-compatible sequence of 64
one-symbol evaluations at block position 256. It freezes parameters and memory
before position zero, records stream-zero truth paths as each symbol is coded,
captures the persistent key/value state after each append, and binds ordered
per-position hidden, attention, relative, logit, and probability tensors. The
open fixed-profile program reconstructs its 64 causal input symbols from the
decoder-visible predecessor plus the preceding 63 truths. Sequential oracle
tensors are aggregated in original position order; final K/V and invariant
relative tensors use their exact matched terminal/initial states. Geometry,
`1e-5` tolerance, one-count branch limit, source ceiling, and verdict are
otherwise unchanged.

Qm2 reached the intended block-256 boundary, wrote the complete
`659,578,911`-byte parameter snapshot, `10,507,510`-byte decoder state, exact
target symbols/tree stream, and exactly `15,616 = 244 x 64` selected-stream
checkpoint tensors. It peaked at `6,380,220 KiB` single-process and
`6,417,340 KiB` tree RSS with no violation. Validation then stopped before the
open build because the declared per-layer manifest order placed persistent K/V
before relative tensors, while LibNC constructs/dumps the relative tensors
before entering the sequential append branch. Qm2 therefore proves that the
sequential capture boundary and population are correct but provides no open
parity verdict. Qm3 changes only this ordered manifest contract; no tensor,
model, arithmetic path, tolerance, or promotion threshold changes.

Qm3 accepted the corrected manifest and bound all `15,616` checkpoint tensors,
then produced a deterministic `2,543,298,652`-byte compressed oracle fixture.
The open executable built within its `1,173,776`-byte compressed source ceiling,
but stopped before its first calculation: its loader incorrectly required the
64 sequential occurrences of each internal checkpoint label to be globally
unique. A direct replay against the preserved fixture reported `duplicate
tensor name: embedding_input`. Parameters and initial state remain unique;
the repeated internal tensors are ordered comparison evidence. Qm3 therefore
has no parity verdict and zero score credit.

Correction-only qm4 retains strict parameter/state uniqueness while validating
internal tensors by their already bound category index and payload. It also
preserves a failed open subprocess's stdout/stderr in the adaptive log. The
fixture selection, tensor values, profile implementation, `1e-5` tolerance,
branch conditions, package ceiling, and authorization verdict are unchanged.

## 2026-08-10 - Production forward numerical correction chain reaches local parity

Qm4 through qm8 repaired only representation and operation-order defects found
at the first mismatching checkpoint: sequential tensor addressing, matrix
layout, RMSNorm scalar order, the observed reduction lanes, and explicit BF16
node boundaries. Qm9 then tested a sequential AVX/FMA dot product and exposed
that LibNC's default four-thread kernel does not use one 1,024-wide reduction.
Qm10 and qm11 tested non-fused variants and were worse. Qm12 tested an inferred
BF8 boundary and was also worse; all three are diagnostic rejections with zero
score credit.

An exact dispatch probe and kernel trace established the missing rule: LibNC's
default kernel splits each 1,024-wide dot into eight 128-input AVX/FMA chunks,
resets the partial accumulator at each chunk, then adds chunk results. Qm13
implemented that rule. Its durable receipt has exact layer-zero attention
input, key state, value state, relative weight, and relative bias. The first
mismatch moved to attention probability (`3.0517578125e-05` maximum); the full
forward still missed by `0.078125`, and the branch-count error fell to `106`.
The repeated open outputs are byte-identical, source closure is `1,174,284`
bytes, fixture package is `2,543,303,900` bytes, and the run stayed below the
decimal memory guard. Qm13 therefore remains a zero-credit parity rejection.

Qm14 applied the same proved reduction to transposed content and relative
attention products. A manifest-bound replay showed that its pre-softmax scores
are exact: passing all `163,840` layer-zero scores through LibNC reproduces the
oracle attention probabilities bit-for-bit. Qm15 replaced `std::exp` with an
open AVX2 implementation of LibNC's BF16 exponential polynomial, fixed 64-item
sum tree, binary block accumulation, and BF16 normalization. Layer-zero
attention probability then became exact. Qm16 applied the 128-input reduction
to the 320-wide attention-value product; every checkpoint in layers zero and
one became exact.

Qm17 corrected the remaining softmax boundary from elementwise division to
LibNC's single reciprocal followed by multiplication. Exactness then extended
through layer three. A direct open-versus-LibNC replay isolated the next defect
to the feed-forward RMS normalization after an exact layer-four attention
residual. Qm18 replaced the approximate 16-lane squared-sum with LibNC's exact
64-item AVX2 square-reduction and binary block tree.

Qm18 is terminal PASS on both the preserved fixture and an independently
regenerated guarded fixture. Maximum tensor error is exactly zero; repeated
open outputs are byte-identical; all 896 branch rows preserve tree topology,
symbol order, and truth path; maximum integer probability difference is one
count, exactly at the frozen allowance. The compressed source closure is
`1,175,720` bytes with no forbidden dynamic dependency. Peak sampled RSS was
`6,380,224 KiB` single-process and `6,417,168 KiB` process-tree, below the
decimal guard. Its zero-credit verdict is
`authorize_production_P_K_O_OK_F_S_attribution`, so the dependency-frozen
six-arm production attribution may now materialize without changing its gates.

## 2026-08-10 - Production output-head attribution implementation reaches exact smoke parity

Candidate `nncp_libnc_output_head_midpoint_attribution_65536_qm0_v1` now
materializes one serialized `P/F/K/O/OK/S` decoder contract over the exact
production NNCP source. `O`, `OK`, and `S` retain LibNC's proved 64-state
backward geometry but filter midpoint optimizer writes to the existing
`embed_out` and `out_bias` variables. `S` cyclically shifts first-half truths
within each stream. `K` discards and rebuilds without a midpoint update; `OK`
adds an extra discard/rebuild cycle after the identical head-only update.

The one-segment, `2,048`-symbol smoke is infrastructure evidence only. Every
arm decoded the same `9,965`-byte raw population. `P` and `K` were both
`55,635` bytes and differed only at serialized schedule offset 18. `O` and
`OK` were both `55,628` bytes and likewise differed only at offset 18; their
head-gradient, updated-head, complete-parameter, persistent-memory, and
optimizer-step witnesses were exact. Shifted `S` was `55,633` bytes, preserved
the target-multiset bias update, and changed the aligned weight update as
intended. No allocator leak remained.

The indexed observer rebuilt successfully and reproduced O's clean archive
byte-for-byte. The complete compressed incremental source package is `10,432`
bytes against the frozen `65,536`-byte ceiling. This authorizes the already
frozen guarded `65,536`-symbol run; it supplies no compression promotion or
score credit. The scientific thresholds remain O gain at least `3,781` bytes,
O over S at least `473` bytes, and original-coordinate third floors
`[1,275, 1,420, 1,088]`.

The first guarded qm0 launch failed before extraction because the driver
created its temporary source directory and then called the bridge helper that
also requires creating it. It ran no arm, returned `1`, sampled only `1,284`
KiB RSS, and provides zero scientific evidence. Correction-only qm1 extracts
into the already-created directory and retains every scientific input, arm,
threshold, observer, and guard unchanged.
