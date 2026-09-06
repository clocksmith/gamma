# Research Register

[Record index](research_register/README.md) | [Earlier records](research_register/archive/README.md)

## 2026-09-06 - Competing Gemini design and blind decoder review

ROOT owns one bounded [Gemini design request](../operations/provenance/dualstream_gemini_design_20260906/request.md)
using the installed CLI and existing authentication. Its request manifest binds
the measured v1 source, synthetic tests, exact opening development input and
terminal failure. It asks for one implementable successor, encoder/decoder
procedures, termination and inversion arguments, complexity and a falsifying
test. Model output is a proposal with zero evidence or score authority.
Tools, extensions, MCP and hooks are disabled; validation/confirmation bytes and
model-campaign artifacts are withheld. A separate reviewer starts from codec
source and synthetic fixtures without result claims. Publication precedes the
request; a returned design still needs implementation, independent inverse
review and a separately frozen exact comparison before it can advance.

The request was published at `2eff25f26ba4bc3022f68b1ea9853843b740aae6`.
The installed client then failed authentication with `IneligibleTierError`:
its Code Assist access was reported unsupported. The retained execution receipt
has return code 1 and an empty response. No Gemini proposal or model-quality
claim follows; no dependency installation or credential change was made.

The independent reviewer found a separate v1 inversion failure for one-byte
frames: 74,074 identical bytes produce an archive above the decoder's cap.
ROOT's new `dualstream_grammar_bounded_v1.py` checks each write against the same
cap and preserves accepted v1 archive bytes and source. Eighteen synthetic tests
pass, including the reported boundary and atomic file rejection. This repair
is locally authored; it is not a Gemini design or new corpus compression result.

The user explicitly removed Gemini from the required workflow. This consultation
attempt is closed; authentication or another provider is not a research blocker.
Continue locally from the measured literal-definition cost, with independent
review and exact benchmark comparisons. Keep the failed request as historical
provenance and keep confirmation inputs withheld from development.

## 2026-09-06 - Standalone two-stream parameter grammar development

ROOT owns the new standalone `dualstream_grammar_v1` implementation work. The
user's `sandbox:/mnt/data/dualstream_grammar_v0.zip` is not accessible on this
host and no local copy was found; this is a new implementation from the supplied
specification, not a verified modification of that ZIP. The user-reported
prototype measurements remain unverified external evidence.

Hypothesis: jointly factoring exact phrases, parameterized byte templates and
repeated invocation arguments can reduce complete framed archives against an
identically framed Deflate baseline. All definitions precede use, references
are backward-only, and independent frames permit bounded encoder lookahead.
The decoder only interprets exact byte programs. XMill's grouping and existing
phrase grammars are precedent, not Gamma novelty. Prior XML deletion ledger
losses and the retired schema-exception realization remain unchanged.

The [18-test synthetic receipt](../operations/evidence/20260906_dualstream_grammar_v1_unit.json)
proves exact byte/interpreter behavior and the bounded runner checks.
The [development plan](../operations/provenance/dualstream_grammar_development250k_q0_v1_plan.json)
binds 11 inputs, eight configurations, 18 arms and 54 separate phases. Ownership
was published at `a46a8109f31f0d03ade9beaa799401992bc3025e` before release after
fresh admission. CPU2, 2GiB memory, 256MiB scratch, zero swap and the frozen
elapsed/phase stops were enforced. HORIZON and model campaigns stayed separate.

The [terminal audit](../operations/provenance/dualstream_grammar_development250k_terminal_20260906.json)
verifies all 54 phases, 18 exact inverses and repeats, 237 final outputs and
complete additive archive accounting. P is 89,041 bytes; S is 113,406; matched
G2 is 109,201; best T2 is 102,492. T6 ties T2, with the frozen stable-ID tie break
selecting T2. Shared templates save 6,709 bytes against G2 but lose 13,451 bytes
against plain Deflate. Each T activates 12 repeated argument references.
T2's literal definitions cost 64,557 bytes, motivating a representation-cost
diagnostic; the accounting does not isolate separate binding/template effects.

The [validated reflection](../operations/adaptive/reflections/20260906T174841Z_181d2f2c47.json)
records an algorithmic loss and authorizes only a separately identified
development mutation. No validation or confirmation population was opened.
All eight tested configurations remain retained; this is no impossibility claim
about grammar compression. Eighteen normalized run rows are linked to unchanged
arm receipts. The guard passed with 141.2443 seconds elapsed; shared-host timing
and incomplete Python/zlib package accounting provide no qualification credit.
The [codec guide](dualstream_grammar_v1.md) covers the implementation and results.

## 2026-09-06 - Organization audit connects reflections to the agent loop

The [parallel audit](organization_audit.md#organization-scorecard-2026-09-06)
rates the pre-change environment 5.6/10, with experiment-loop simplicity the
weakest dimension. The existing ledger now projects recorded lessons, causes,
uncertainties, retired dimensions and next actions into CLI and browser search
and candidate history. The workbench prompt requires the next experiment to name
the lesson it applies or uncertainty it tests. This changes browsing and routing,
not evidence validity or scientific status. Historical snapshots and source paths
remain intact. The audit distinguishes implemented retrieval from recommended
terminal-record consolidation and routine/full report refresh profiles.

## 2026-09-06 - SHA observer cost comparison reuses the sealed MIDAS driver

ROOT owns `midas_open_observer_sha_cost4096_q0_v1`, initially held job
`20260906T145045Z_48b35ff173`. The explicit build-authority adapter
`tools/midas_open_observed_sha_gate_v1.py` reuses the original driver's execution,
comparison and publication functions in a private module. It authenticates the
successor's actual six-test receipt. Its [eleven synthetic tests](../operations/evidence/20260906_midas_open_observed_sha_gate_unit.json)
reject stale authority, changed source, missing parity, corrupt probabilities
and incomplete boundaries, while preserving elapsed-stop classification.

The [frozen plan](../operations/provenance/midas_open_observer_sha_cost4096_q0_v1_plan.json)
binds 304 inputs, including original synthetic4096 witnesses, and 157 outputs.
It runs on CPU2 only after the distant100KB gate closes, ownership is published
and fresh admission passes. Limits are 2GiB outer memory, 256MiB scratch,
zero swap and a 180-second aggregate stop; native phase limits are unchanged.
It grants no compression or qualification credit. Any corpus successor requires
its own freeze using measured cost and complete boundary evidence.

The [first attempt](../operations/provenance/midas_observer_sha_cost4096_admission_failure_20260906.json)
stopped before any codec phase: the initial guard sampled inherited 32-CPU
affinity before the inner `taskset` applied CPU2. No result file was created;
cleanup passed. Its validated infrastructure-failure reflection permits a new
held job for the unchanged experiment, with the entire canonical launcher
pinned to CPU2 before fork. The strict guard and frozen budgets stay unchanged.

The [retry terminal audit](../operations/provenance/midas_open_observer_sha_cost4096_terminal_20260906.json)
passes all 16 phases, 304 input hashes and 60 retained original-observer file
comparisons. All synthetic archives remain 4,143 bytes. Observed/reference
encoder CPU ratios are P 1.600, K 1.399, F 1.369, S 1.373; the strict guard observed
one allowed CPU from startup and cleanup completed. The validated reflection
holds scientific promotion: these are implementation and cost results only.
Four new normalized rows bring the ledger to 1,005 unique identities.

During preparation, admission rejected an attempted edit to the older bound
observer documentation. ROOT restored its exact bytes before enqueueing and
reverified all 238 distant-gate and 304 cost-gate input hashes. Executable
sources and cached binaries were unchanged; current guidance stays here.

## 2026-09-06 - MIDAS distant100KB passes exact observed transfer

The [terminal audit](../operations/provenance/midas_open_observed_distant100k_terminal_20260906.json)
closes all 16 phases. P/K produce 51,531 bytes, F 45,587, and S 50,882.
F saves 5,944 bytes against P and 5,295 against S. All four raw inverses,
repeated archives, fresh unobserved reference archives/final states, 800,000
pre-truth probabilities and 3,127 boundary records pass their comparisons.
The resource guard passes and the cgroup is removed. The [validated reflection](../operations/adaptive/reflections/20260906T143122Z_85238bbb11.json)
permits a separately frozen 250KB gate after observation cost is measured under
the unchanged native limits. Four new run rows bring the ledger to 1,001 unique
identities. This previously examined cold population provides transfer evidence;
complete-package, fresh-confirmation and full-corpus claims remain unproved.

ROOT owns `midas_open_observed_distant100k_q0_v1`, initially held job
`20260906T143122Z_85238bbb11`. The [plan](../operations/provenance/midas_open_observed_distant100k_q0_v1_plan.json)
reuses the exact opening-gate codecs and 16-phase runner at canonical raw offset
500,000,000 for 100,000 bytes, with cold causal initialization and all P/K/F/S
controls. Its 238 inputs include the validated opening reflection. CPU2, 2GiB
outer memory, 256MiB scratch, zero swap and 1,200-second aggregate stop are bound;
native limits stay unchanged. F must beat P and S with complete boundary
evidence. This is a transfer test on previously examined data, not a sealed
holdout or full-score claim. Publication precedes release and execution.

## 2026-09-06 - MIDAS opening100KB passes complete boundary observation

The [terminal audit](../operations/provenance/midas_open_observed_opening100k_terminal_20260906.json)
closes all 16 phases with passing resource guards. P/K archives are 52,661 bytes,
F is 48,714, and S is 52,770. F saves 3,947 bytes against P and 4,056 against S.
All four inverses and repeats pass; fresh unobserved reference archives and
complete final states agree. Every same-arm 800,000-probability trace and 3,127
boundary records match exactly. P/K authoritative projections agree.

The [validated reflection](../operations/adaptive/reflections/20260906T135533Z_1c3e7bc7d3.json)
selects a separately frozen distant100KB transfer gate. This opening population
was examined before; package accounting, calibrated resources and full-1G
performance remain unknown. Four corpus run rows retain zero full-score credit.
The [record reconciliation](../operations/evidence/20260906_midas_observed_record_reconciliation.json)
disambiguates identical P/K row IDs by arm while preserving all measured files
and values. All 997 row IDs are unique; complete older register records move
intact into the existing archive to keep the current register bounded.

## 2026-09-06 - MIDAS observation cost gate frozen before execution

ROOT owns `midas_open_observer_cost4096_q0_v1`, initially held job
`20260906T133935Z_7bac5ae319`. The [runner tests](../operations/evidence/20260906_midas_open_observed_gate_unit.json)
pass six synthetic cases, including probability divergence, missing boundary
evidence, changed reference archives, and elapsed-budget exhaustion.
The [frozen plan](../operations/provenance/midas_open_observer_cost4096_q0_v1_plan.json)
binds a deterministic 4,096-byte synthetic population and both published cached
codecs. Sixteen phases compare unchanged P/K/F/S encoding with independently
observed encoding, decoding, and repeat encoding. CPU2, one thread, zero swap,
2GiB outer memory, 256MiB scratch, 600-second aggregate and 120-second phase
stops are explicit execution limits.

This measures observation cost and exact archive/state parity. It supplies no
corpus economics or full-score credit. Ownership and all frozen inputs must be
published before release; HORIZON and measured codec sources remain unchanged.

The [terminal audit](../operations/provenance/midas_open_observer_cost4096_terminal_20260906.json)
now closes all 16 phases, 227 inputs and 157 required outputs. Every arm
independently reconstructs and repeats; all reference archives, complete final
states, 32,768 probabilities and 130 boundary records agree within their
required comparisons. P/K authoritative projections agree. Each synthetic
archive is 4,143 bytes; this gives no corpus compression evidence.

Observed/reference encoder CPU ratios are P 3.039, K 2.613, F 2.257 and S 2.219.
The guard passes with 50,470,912-byte sampled tree RSS and 25,883,922-byte sampled
logical scratch. The validated reflection holds automatic promotion: measure a
smaller frozen corpus synchronization gate or optimize observation before
attempting opening250KB under the unchanged native 120-CPU-second cap. Four
canonical run rows retain unknown complete-package and full-score values.

ROOT next owns `midas_open_observed_opening100k_q0_v1`, initially held job
`20260906T135533Z_1c3e7bc7d3`. Its [frozen plan](../operations/provenance/midas_open_observed_opening100k_q0_v1_plan.json)
reuses both codecs and the same runner for 16 phases on canonical opening100KB.
This previously examined population is a boundary-observation replay, not fresh
confirmation data. The reduced scope follows measured observation overhead;
native limits stay unchanged. F must beat both P and S with complete identity
evidence before a separately frozen transfer gate. Complete-package and
full-corpus qualification remain unresolved.

ROOT is preparing an [observation-only SHA adapter](../operations/provenance/midas_observer_sha_source_v1.json)
to the same sealed observer. It retains the attributed public upstream block
routine and scalar fallback. Synthetic parity tests must pass before this
unmeasured implementation can enter a separately frozen corpus gate.

The [accelerated observer unit receipt](../operations/evidence/20260906_midas_open_boundary_observer_sha_unit.json)
now records six passing tests: five inherited observer cases and 138 digest
vectors checked against both the unchanged scalar routine and Python hashlib.
Every retained archive, probability trace, boundary record, final state and
snapshot matches the original observer across all P/K/F/S phases. The native
binary is 437,128 bytes; 540 observer and 521 hash-fixture compiler dependencies
were rehashed. The guard and child cleanup pass. This remains synthetic
correctness evidence; corpus-scale observation cost still needs measurement.

## 2026-09-06 - MIDAS boundary observability passes exact synthetic checks

The [new observer](midas_open_boundary_observer_v1.md) wraps the unchanged native
MIDAS codec and records every pre-truth probability plus complete serialized
state at initialization, every 32 decoded bytes, and finalization. All five
[synthetic regression tests](../operations/evidence/20260906_midas_open_boundary_observer_unit.json)
pass on CPU2. P/K/F/S preserve the retained 105-byte archives of the 65-byte
fixture; each independent decoder and repeat matches every probability,
boundary record, complete state and exact snapshot. An independent parser
checks all 17 component ranges, and identical malformed bundles cannot pass.

The 432,528-byte observer executable and all 532 compiler dependencies are
hash-bound. The aggregate guard passes and its cgroup is removed. This supplies
observability code, not a corpus certificate or package qualification. The
existing opening250KB gain remains held until a separately frozen successor
measures these boundaries on corpus data. No measured MIDAS source changed.

## 2026-09-06 - Schema transfer is exact but every block falls back

The [terminal audit](../operations/provenance/wiki_schema_exact_transfer250k_terminal_20260906.json)
closes all 24 phases of `wiki_schema_exact_transfer250k_q0_v2`. All P/L/D/C arms
produce 111,159 bytes on opening250KB and 106,139 bytes on distant250KB; all eight
inverses and repeats pass. ROOT independently reconstructs every baseline block
and verifies its framing, hash, and exact accounting. Serialized dictionaries
agree at all 62 block boundaries across every arm and phase.

D proposes 454 opening and 337 distant references, but no grammar block is
selected. Even the cheapest proposal exceeds its baseline by 168 opening bits
or 88 distant bits. Archive saving is zero and selected C associations are
inactive, leaving causal attribution inconclusive. This evidence concerns the
tested cold-population realization and does not disprove grammatical structure.

The [canonical decision](../results/wiki_schema_exact_transfer250k_q0_v2/decision.json)
binds all 142 other required outputs. Its frozen aggregate rules yield both
promotion and kill false, hence `retry`; the [validated reflection](../operations/adaptive/reflections/20260906T023145Z_eb44974e5c.json)
holds work without an automatic rerun or 1M gate. Eight canonical ledger rows
preserve unknown complete-package and full-score values.

## 2026-09-06 - Tensor restorations recover partial archive quality

The [terminal audit](../operations/provenance/public_fx2_weight_restore_groups_terminal_20260906.json)
closes all 43 phases of `fx2_weight_restore_groups_fixture50051_q0_v1`.
Eight arms independently invert and repeat; all 24 same-arm probability/coder
traces agree. ROOT rehashed 376 frozen inputs and 646 indexed files and
recomputed every recorded arithmetic transition. The original P archive is
3,223 bytes; quantized Q and bookkeeping K are both 4,430 bytes.

| Restored group | Archive bytes | Bytes recovered against Q | Added model bytes against Q |
| --- | ---: | ---: | ---: |
| E: embeddings and output embedding | 4,265 | 165 | 17,316 |
| A: full-attention projections | 4,400 | 30 | 64,443 |
| R: recurrent-attention projections and gates | 4,230 | 200 | 260,809 |
| U: MLP up projections | 4,237 | 193 | 261,664 |
| V: MLP down projections | 4,311 | 119 | 261,314 |

These are independent restorations into the same Q model. Effects cannot be
added, and no single group restores original-parent quality. E has the smallest
model cost; that observation does not select a mixed-precision successor.
The [validated hold reflection](../operations/adaptive/reflections/20260906T012956Z_3b36cd0326.json)
preserves missing fresh confirmation, complete package and resource qualification.
Eight normalized ledger rows retain unknown program/full-score values.

## 2026-09-06 - Schema corpus gate v2 ready under held ownership

The [v2 contract](../operations/adaptive/experiments/wiki_schema_exact_transfer250k_q0_v2.json)
binds the unchanged schema codec, opening/distant raw populations, P/L/D/C,
186 inputs, and explicit CPU2 resource stops. The v1 preflight rejected two
legitimate empty Python package files. The separately identified v2 accepts
hash-bound empty runtime files; [nine synthetic checks](../operations/evidence/20260906_wiki_schema_exact_transfer_v2_unit.json)
pass without changing v1 source or evidence. Job `20260906T023145Z_eb44974e5c`
is held pending publication and admission. The 143-output manifest includes
ROOT's terminal decision and eight normalized result receipts. No corpus result
or complete-package measurement is implied by registration.

## 2026-09-06 - Exact-residual model identity passes; standalone cost fails

The [terminal audit](../operations/provenance/public_fx2_weight_exact_residual_terminal_20260906.json)
closes `fx2_weight_exact_residual_model_q0_v1` job
`20260906T021414Z_3e6eef5746`: all 21 phases and the resource guard pass.
D emits 2,908,306 model bytes versus the selected marginal 2,908,329, saving
**23 bytes per model**. All three fresh restores reproduce the original
2,930,652-byte parameter stream exactly, preserving 434 tensor metadata rows,
111 INT4 tensors, all non-INT4 bit patterns and generated RoPE behavior.

Every native P/K/D inverse and repeat passes. All six archives equal the
3,223-byte parent, and all nine complete 7,275,072-byte probability/coder traces
match the retained parent. Thus archive saving is zero; this exact factorization
causes no observed native predictive loss. This differs from the prior even7
parameter mutation, whose archive penalty came from changed predictions.

The required 103,088-byte restorer and paid options make the two-container
compiled component delta **+206,212 bytes**. The separate raw-source-compressor
allowance is +141,866 bytes; these alternatives are not summed. Conservative
component net savings are **-206,212 bytes**, while complete-package net and
full-corpus score remain unknown. Generated original-model bytes are scratch.

The [validated canonical reflection](../operations/adaptive/reflections/20260906T021414Z_3e6eef5746.json)
holds promotion with the frozen economic kill predicate true. This rejects only
the standalone realization, not exact residuals as an information source. The
guard peak is 5,563,486,208 bytes; timings remain shared-host diagnostics.
Three normalized P/K/D run-ledger rows preserve the immutable raw result files
and explicitly omit unqualified score credit. No larger gate follows automatically.

## 2026-09-06 - Frozen exact-residual model gate and tensor diagnosis

`root_explore` owns the [exact-residual model comparison](../operations/adaptive/experiments/fx2_weight_exact_residual_model_q0_v1.json)
under held job `20260906T021414Z_3e6eef5746`. Its 21 bounded phases pack P/K/D,
restore the original parameter stream, and independently encode, decode and
repeat the public 50,051-byte fixture with the unchanged native predictor.
The economic comparison includes the residual restorer, metadata and options;
unchanged probability streams and exact archives are mandatory. The model has
not run under this gate at registration. CPU2, memory, scratch and the 900-second
aggregate execution stop are frozen; publication and fresh admission precede release.

The separate [tensor-restoration diagnostic](../operations/adaptive/experiments/fx2_weight_restore_groups_fixture50051_q0_v1.json)
is held under job `20260906T012956Z_3b36cd0326`, behind exact packing. It restores
each predefined tensor group independently from the failed even7 configuration
and measures archive recovery, probability differences and package costs. It
does not sum group effects or select a mixed-precision successor automatically.
Both gates retain external FX2/CMIX authorship and grant zero full-corpus credit.

## 2026-09-06 - Open MIDAS opening250KB terminal component result

The [independent terminal audit](../operations/provenance/midas_open_incremental_corpus250k_terminal_20260906.json)
closes job `20260906T011941Z_c572f1e842` with all 13 phases successful and the
owned guard closed. On the fixed 250,000 raw bytes, archives are P/K 115,921,
F 107,176 and S 119,779 bytes. F saves **8,745 archive bytes against P** and
12,603 against S. These are component measurements; `netBytesSaved` and the
complete package/full-corpus score remain null.

Every arm independently reconstructs the input, repeats its archive and agrees
on complete terminal state. P/K archives and authoritative parent projections
match. Terminal equality does not establish unseen intermediate probability or
state boundaries. The guard reports a 51,527,680-byte peak; shared-host timings
remain diagnostic. The unchanged retained binary was authenticated without
compilation; source and runtime inventory checks passed.

The [validated canonical reflection](../operations/adaptive/reflections/20260906T011941Z_c572f1e842.json)
supports this bounded hypothesis and **holds promotion** for missing detailed
boundary traces, complete package accounting and isolated qualification. Four
diagnostic P/K/F/S rows retain the measured archives in the
[run ledger](../results/run_ledger.jsonl), with unknown package score preserved.
No distant confirmation or successor launch follows automatically.

## 2026-09-06 - Open MIDAS opening250KB ownership and exact-residual unit

`root_explore` owns `midas_open_incremental_corpus250k_q0_v1`, the first bounded
raw corpus runner for the unchanged standalone incremental codec. Its
[frozen experiment](../operations/adaptive/experiments/midas_open_incremental_corpus250k_q0_v1.json)
binds the existing kernel measurements, retained executable, exact opening
250,000-byte population, P/K/F/S controls, package components and CPU2 resource
envelope. Eighteen [runner tests](../operations/evidence/20260906_midas_open_corpus_runner_unit.json)
pass, including retained 65-byte archives and cache-drift rejection. No compiler
runs in the corpus gate. No corpus result is available at registration.

Each arm must independently invert, repeat and agree on complete terminal
state; P/K authoritative parent projections must agree. The unchanged codec
does not emit every-midpoint probability/state traces. That missing evidence
blocks promotion and cannot be inferred from terminal equality. Complete package
and calibrated resource qualification remain unresolved. HORIZON is unchanged.

The [exact-residual probe unit](../operations/evidence/20260906_fx2_exact_residual_unit.json)
passes seven synthetic tests, including independent goldens, exact signed XOR,
exceptional floating-point payloads, malformed-input rejection and exclusive
publication. Rejection tests now require the probe's exact error exit and
diagnostic prefix; crashes cannot pass as expected codec rejection. The trained
model package and probability comparison remain unmeasured.

## 2026-09-06 - Exact representation experiments and precision diagnosis

The active target remains 99,000,000 complete bytes; the 10,389,323-byte distance
from the best counted Gamma forecast is planning debt. HORIZON remains unchanged.
The user selected exact-residual model packing, an independently framed schema
codec with paid exceptions, and a predefined tensor-restoration diagnostic.
These are separate experiments; existing component savings do not prove 99M.
MIDAS independently advances the unchanged standalone codec toward a bounded
P/K/F/S raw corpus comparison after synthetic runner validation and published
ownership. No new corpus result is implied by these source assignments.

The [run-ranked exception screen](../operations/provenance/public_fx2_xml_exception_geometry_screen_20260906.json)
counts masks with n positions, e exceptions and r runs by
`C(e-1,r-1) * C(n-e+1,r)`. The reviewer checked all 8,191 masks of lengths 0..12.
On opening 250KB, 87 eligible prior-route pairs displace only 10.8837 parent ideal
bytes; even optimistic mask/descriptor costs leave -301.479 bytes saved. No pair
pays, and the distant cold population has no eligible explicit-key pairs.
This rejects that screened realization on these populations, not grammar,
cross-field dependencies or mature-history opportunities as information sources.

A separate considered mechanism keys a later template field by an earlier
field's decoded value, learned only from completed previous templates. Its
conditional lookup differs from same-route value copying and outer-XML numeric
dependencies. An exact equal mixture of two sequence models costs at most one
ideal bit above the better model per activation; finite rounding and package
cost remain unmeasured. [SQUISH](https://arxiv.org/abs/1602.04256v2) provides an
attribute-dependency precedent, not transferable Gamma compression credit.
It is considered evidence, not another queued specialist.

For the selected schema realization, sequential reversible grammar construction
has [published precedent](https://doi.org/10.1109/18.841161), while ambiguous
grammars require a [paid derivation or deterministic resolution](https://arxiv.org/abs/2003.08097).
The proposed block fallback is compared with an equivalently framed baseline;
it does not inherit an overhead bound against uninterrupted FX2.

## 2026-09-06 - Open MIDAS source bundle survives relocation and exact replay

`tools/midas_open_source_bundle_v1.py` materializes the unchanged default
incremental codec as a deterministic 84,030-byte source ZIP containing 30 local
files and its source manifest. Compiler-discovered includes preserve the sealed
forward translation unit; Python helpers and Gamma-relative LICENSE layout are
retained. This is counted local source, not a complete submission package.

A fresh extracted tree, isolated Python imports and a separate empty build cache
produce the same native executable. Repacking from the extracted tree produces
the identical source ZIP despite the intentionally different absolute-path cache
identity. All four P/K/F/S arms reproduce the retained 65-byte fixture archives,
decode without the raw source, and re-encode with exact same-arm final-state
witnesses. P/K archives and authoritative parent-state projections match.
The 105-byte archives exceed raw size; no compression gain is inferred.

Nine new regressions and all 26 combined MIDAS tests pass. Review corrections reject noncanonical manifest
bytes and file/directory prefix collisions, enforce aggregate bounds before
loading excess source, and name the required `prlimit` and `ldd` utilities.
Corruption, extra/missing members, path escapes, symlinks, FIFO input and existing
output targets fail closed. No extracted code runs automatically. All 46 source
bindings in the prior standalone evidence remain unchanged.

Evidence: `operations/evidence/20260906_midas_relocatable_source_bundle_unit.json`.
Usage: `docs/midas_open_source_bundle_v1.md`. Compiler/runtime distribution,
license closure, accepted package accounting, composite resource qualification
and full-corpus performance remain unproved. This source reconstruction and
synthetic inversion result grants no queue or objective authority. HORIZON's
worker, observer and partial scientific outputs were not changed or inspected;
the concurrent external-derived FX2 lane was preserved. The compact predictor
still needs a separately frozen compression and kernel-budget gate before a
corpus claim or larger population launch.

## 2026-09-05 - Parallel build deduplication and standalone open MIDAS

`lib/native_fixture_build_cache.py` now reuses unchanged C++ builds under a
compiler/toolchain, flag, environment and transitive source/header identity.
Per-key locking prevents duplicate compilation; corrupt entries are quarantined
and rebuilt. Stricter inherited resource ceilings are preserved. Sixteen cache
tests pass, including the inherited-file-limit failure found during integration.
This is a local build cache, not a hermetic package or resource certificate.

`tools/midas_open_codec_v1.py` exposes bounded build, inventory, encode and decode
commands through a new C++ driver using the unchanged incremental predictor.
Output directories publish without overwrite only after coding and validation.
FIFO, symlink, corrupted-input, stale-build, no-overwrite and interrupted-operation
checks pass. Inventory reports local source and resolved runtime bytes separately
and leaves complete-package qualification explicitly unknown.

Seventeen combined MIDAS tests pass, for 33 tests with the parallel cache suite.
The standalone driver retains all original 65-byte P/K/F/S archive known answers.
On 1,024 synthetic bytes, incremental and reference F produce the same 1,043-byte
archive and model/optimizer projection after 32 updates. Independent decoding
after source removal and deterministic re-encoding reproduce exact bytes and
same-arm final-state witnesses. The archive is larger than raw; no compression
gain, corpus result, package qualification or objective credit is claimed.

Evidence: `operations/evidence/20260905_parallel_native_cache_standalone_midas_unit.json`.
Usage: `docs/midas_open_codec_v1.md`. One complete older record moved to archive
part 028 with link targets preserved, keeping this register within its line cap.
Neither implementation lane waited for HORIZON; its process, observer and partial
scientific output remained untouched. The other agent's FX2 work was preserved.
A corpus successor still needs frozen architecture, population, control, package
and composite resource budgets before launch.

## 2026-09-05 - Incremental open MIDAS preserves the retained reference

`lib/midas_open_profile_incremental_fixture.hpp` adds a separate cached-forward
implementation of the fixed one-layer integration fixture. The original parent
and sealed neural kernels remain unchanged. Its translation unit includes the
original forward source instead of linking it twice, preserving the arithmetic
helpers. Future zero-symbol K/V placeholders and the full masked softmax row are
retained; the reference exponential floor does not make masked weights zero.
Every parameter update invalidates the cache and replays the causal prefix.

Nine regression tests pass. On 65- and 129-byte synthetic populations, all
P/K/F/S F32 rows, Q16 probabilities and finite archives match the reference.
Model, optimizer, detached memory and discarded K-shadow states also match.
Encoder/decoder checkpoints include the complete incremental cache, including
pending predictions at every bit offset around midpoint and segment boundaries.
Cross-decoding, deterministic repeats, partial-segment inverses and corrupted
cache rejection pass. No corpus data or teacher state enters these tests.

The paired 129-byte F diagnostic records reference encode/decode CPU of
0.243620/0.229980 seconds versus incremental 0.034700/0.034990 seconds, with
13,996 KiB cumulative process peak RSS. Initialization, full updates and cache
resets are included. This is shared-host diagnostic evidence, not qualification.
The synthetic F/S archives are 170 bytes versus P/K's 169; no gain is claimed.

Evidence: `operations/evidence/20260905_midas_incremental_profile_identity_unit.json`.
The receipt distinguishes implementation validation from budget exhaustion and
retains exact finite bytes, source bindings and sanitizer outcomes. This adds no
compression, package, resource-qualification or full-corpus score credit. Before
a corpus successor, coordinate the compact-parent owner and freeze the chosen
architecture, population, package, memory and kernel/runtime budgets. HORIZON
and the other agent's FX2 work remain unchanged by this implementation.

## 2026-09-05 - Real open MIDAS parent passes a bounded native roundtrip

`lib/midas_open_profile_fixture.hpp` connects the existing Gamma open neural
forward, complete backward and full optimizer update kernels to the new native
coder and P/K/F/S scheduler. It does not call the legacy replay's differently
defined K/S dispatcher and does not consume LibNC or pretrained tensors. The
integration fixture has one 64-feature layer, an eight-unit feedforward inner
dimension, eight memory positions, a 256-byte vocabulary and fixed initialization.
This is not a selected competitive architecture or a corpus candidate.

All four arms encode 65 synthetic bytes into 105-byte finite framed archives,
invert exactly, and re-encode identically. P/K probabilities, archives and
authoritative predictive-state projections match. K's discarded real full update
and rebuild matches F's midpoint backend byte-for-byte. F visits all 18 declared
parameter tensors and changes 15, including embedding, attention, feedforward and
output weights; S produces a different full-model midpoint state. Every arm shares
the full 64-byte parent update; F/S add the causal 32-byte midpoint update. This
schedule is not claimed to inherit the old teacher replay's compression behavior.

Six regression tests pass. The separate address/undefined-behavior sanitizer
build also passes and produces the same four archives. Pending and boundary
checkpoints match across encoder and decoder; corrupted tensors, negative second
moments and mismatched cached probabilities are rejected. A separate process
decodes an additional fixture after its source file is removed.

Evidence: `operations/evidence/20260905_midas_open_profile_parent_roundtrip_unit.json`
retains raw and archive bytes as hex, SHA-256 values, source bindings, the build
recipe, validation output and bounded encode/decode CPU/RSS observations. This
closes a synthetic inversion and synchronization gate, not a compression-gain,
gradient-reference, complete-package, resource-qualification or full-corpus gate.
No compression gain or objective credit is awarded.

The reference recomputes all 64 graph states for every byte. Before any corpus
successor, coordinate the compact-parent owner, bind an incremental pre-truth
forward implementation against this reference, and select the architecture under
explicit kernel, package, memory and runtime budgets. The other agent's candidate
tree and HORIZON remain unchanged. This session's requested `rdpull gamma` still
fails SSH public-key authentication; local and concurrent work was preserved.

## 2026-09-05 - Join the native MIDAS bit boundary and checkpoint state

`lib/midas_bit_predictor.hpp` now connects the causal midpoint scheduler and
byte adapter behind one pre-truth `predict()` / `observe(decoded_bit)` interface.
Combined checkpoint restore rejects inconsistent byte/bit clocks, mismatched
pending-byte ownership, differing pre-truth distributions, excess checkpoint
size, truncation and trailing bytes. All P/K/F/S finite sentinel inverses and
repeats pass through this interface with exact predictor and normalized coder
state agreement. P/K probabilities, payloads and authoritative-state projections
remain identical. Three regression tests and the joined address/undefined-behavior
sanitizer fixture pass.

Evidence: `operations/evidence/20260905_midas_bit_predictor_join_validation.json`.
This is implementation correctness only, with zero score credit and no corpus
access. A real complete-update trainable backend and its parent roundtrip remain
missing; the other owner's compact predictor source was not changed. The prior
source-bound infrastructure receipt remains unchanged and resolves at local
commit `9d327137`.

The user's `rdpush gamma` request created that commit but could not publish:
GitHub rejected SSH public-key authentication and the agent had no loaded
identities. No credential configuration was changed. Authentication must be
restored before publishing these local commits. HORIZON and its sole observer
remain unchanged, without partial scientific access.

## 2026-09-05 - Public FX2 reproduction and measured comparisons

| Frozen gate | Population | Result and canonical evidence |
|---|---|---|
| `fx2_cmix_transformer_static_vocab_fixture50051_q0_v1` | Public 50,051-byte fixture | 3,223-byte exact archive/repeat; [audit](../operations/provenance/public_fx2_static_vocab_fixture_terminal_20260905.json), [reflection](../operations/adaptive/reflections/20260905T195118Z_c39265f90c.json) |
| `fx2_cmix_transformer_transfer250k_q0_v2` | Raw `[0,250000)` and `[500000000,500250000)` | 33,429/9,499-byte exact cold archives/repeats; [audit](../operations/provenance/public_fx2_transfer250k_terminal_20260905.json), [reflection](../operations/adaptive/reflections/20260905T204313Z_bd6edb2ed4.json) |
| `fx2_bytemodel_argmax_unit_q0_v1` | 32 synthetic families, 256 paths each | Exact state/probabilities; 4,641,532 fewer comparisons; [audit](../operations/provenance/public_fx2_argmax_unit_terminal_20260905.json), [reflection](../operations/adaptive/reflections/20260905T211007Z_358c05f2db.json) |
| `fx2_cmix_transformer_argmax_fixture50051_q0_v1` | Same public fixture, P/K/D/C | All archives 3,223 bytes; twelve complete coder traces identical; [audit](../operations/provenance/public_fx2_argmax_native_terminal_20260905.json), [reflection](../operations/adaptive/reflections/20260905T212145Z_70e5363a53.json) |
| `fx2_weight_pack_roundtrip_q0_v1` | Full pinned trained model, six synthetic populations | Exact inverse/repeat but model grows 2,930,652 to 2,938,887 bytes; [audit](../operations/provenance/public_fx2_weight_pack_terminal_20260905.json), [reflection](../operations/adaptive/reflections/20260905T215312Z_bd5e9a17b9.json) |
| `fx2_weight_marginal_roundtrip_q0_v1` | Full pinned trained model, eight synthetic populations, P/K/D/G | D: 2,908,329 bytes, saving 22,323; G: 2,911,998 bytes, saving 18,654; exact inverse/repeat; [audit](../operations/provenance/public_fx2_weight_marginal_terminal_20260905.json), [reflection](../operations/adaptive/reflections/20260905T222955Z_5eb35a57d6.json) |
| `fx2_weight_native_fixture50051_q0_v1` | Same public fixture, native P/K/D; all 434 tensors including RoPE | All archives 3,223 bytes and nine coder streams identical; native runtime-pair components save 20,070 bytes; [audit](../operations/provenance/public_fx2_weight_native_terminal_20260905.json), [reflection](../operations/adaptive/reflections/20260905T230139Z_d8475c03dc.json) |
| `fx2_weight_native_transfer250k_q0_v1` | Same opening/distant 250KB populations, cached native P/K/D | All archives 33,429/9,499 bytes; exact inverse/repeat and all 18 coder streams identical; [audit](../operations/provenance/public_fx2_weight_native_transfer_terminal_20260905.json), [reflection](../operations/adaptive/reflections/20260905T233740Z_c2a28dc2f7.json) |

Native argmax D/K diagnostic CPU ratio 0.9987045 missed the frozen 0.99 budget trigger: hold without a larger runtime gate.
Retire preceding-symbol weight packing for 8,235 extra asset bytes before loader costs; neither result rejects its whole information source.
Fixed-marginal P/K preserve the original 2,930,652 model bytes; each D/G restore and fresh repeat is exact. Both savings include all 7,169 extra side-information bytes.
The frozen size rule selected D; native integration now passes exact tensor, probability, inverse and repeat checks with 12,288 added executable bytes per copy.
The standalone utility does not pay: D runtime/source inventories exceed the original model alone by 89,671/38,977 bytes; G exceeds it by 93,340/42,646 bytes.
Native components save 20,070 bytes for two runtime copies, or 21,489 for the separate source-compressor/decoder alternative. Opening/distant transfer now passes without recompilation or additional saving; complete package closure and full-corpus qualification remain missing. Transfer guard closed with 1,653 samples, 6,242,869,248 peak cgroup bytes and 15,354,466,504 peak logical scratch bytes; timing is diagnostic and full-score credit remains zero.
Source-only successor considered: transmit the exact Q11 trees directly. Fourteen 11-bit values plus the constrained final node fit 20 bytes per tree; 112 tables would remove 4,480 header bytes per model before changed loader costs. This is byte arithmetic, without implementation, measured gain, or descendant selection.
[Dependency gap review](../operations/provenance/public_fx2_dependency_gap_review_20260905.json) retains versioned LLVM terms and declared CUDA/libdevice provenance; model permission evidence, runtime closure and two unsupported license identifiers remain explicit gaps, without an incompatibility finding.
The existing dependency-closure tool now materializes an [incomplete bundle](../results/fx2_weight_native_fixture50051_q0_v1/release/incomplete_dependency_closure_v1/dependency-closure.json): 137 counted occurrences, 9,523,363 file bytes plus 99 declared unique-option bytes. The [receipt](../operations/provenance/fx2_native_dependency_closure_v1/receipt.json) preserves failed metadata attempts, repeated dictionary/model roles and exact unresolved licensing/build/option gaps; it is not the final two-package submission layout.
The [even7 gate](../operations/adaptive/experiments/fx2_weight_even7_fixture50051_q0_v1.json) is terminal: all 107 phases pass infrastructure checks, with exact raw inverses, deterministic repeats and twelve complete coder streams. P/K archives are 3,223 bytes, D is 4,430 and row-rotated C is 4,785. D changes 3,119,371 of 5,868,864 INT4 symbols and produces a 2,066,802-byte model. Against the selected marginal baseline, two model copies save 1,646,942 component bytes after 36,112 added source/option bytes. The +1,207-byte fixture archive penalty produces a frozen planning delta of +22,468,461 bytes: hold this exact configuration for budget reasons, with no full-score credit or futility claim. The [independent audit](../operations/provenance/public_fx2_weight_even7_terminal_20260906.json) binds 870 retained artifacts and the [validated reflection](../operations/adaptive/reflections/20260906T001115Z_fcb2f27fea.json). The closed guard records 476 samples, 5,577,420,800 peak cgroup bytes and 14,811,642,322 peak logical scratch bytes; concurrent timing remains diagnostic. The [closed probability diagnosis](../results/fx2_weight_even7_fixture50051_q0_v1/probability-loss-diagnosis.json) attributes +426.85/+5,621.31/+3,607.68 interval-code bits to chronological thirds. Sustained predictive loss is observed, but particular tensor sensitivity is unknown. A successor requires a changed mechanism, a separately frozen development budget, and fresh confirmation data.
Preserved failures: [launcher affinity](../operations/provenance/public_fx2_static_vocab_launch_failure_20260905.json) and [transfer-v1 preflight](../operations/provenance/public_fx2_transfer250k_preflight_v1_20260905.json).

[Container authentication](../operations/provenance/public_fx2_container_pair_20260905.json) verifies both release hashes and identical binary, dictionary and model components.
The files total 100,420,830 bytes, including both model copies; [the official FAQ](https://www.hutter1.net/prize/hfaq.htm#addcomp) explains that intentional cost.
Neither binary was executed for this inventory. Required options and committee acceptance remain unverified.

Transfer peak cgroup memory: 5,826,895,872 bytes; preceding-symbol weight probe: 133,156,864 bytes; fixed-marginal probe: 160,862,208 bytes. Guards closed; concurrent timing is diagnostic.
The conservative transfer inventory is 9,403,013 raw bytes with overlapping source/runtime assets; package closure and model licensing remain open.
Direct-WRT cold slices do not reproduce the public reorder/PHDA pipeline or a 1G score. FX2/CMIX/model authorship remains upstream; Gamma has no full-corpus gain credit.

## 2026-09-05 - Restore missing terminal receipt links

These retained decisions were missing exact candidate references in the logical
register. The table restores navigation without changing their source bytes,
scientific conclusions, or objective bindings. Labels are reported by the source
receipts; they are not new launch authority or independently revalidated results.
Use the linked decision and its canonical terminal reflection before selecting
ancestry. Missing or invalid reflections remain visible in `records --view reviews`.

The public GCC v2 and v3 failures concern compilation and instruction selection;
v4 passed the build but rejected its fixture vocabulary. Its held configuration
requires a separately frozen mapping adapter. The initializer's historical
`authorize-integrated-replay` label is narrowed by its canonical reflection to
fixture reuse; it does not authorize a new integrated codec gate.

| Candidate | Retained source label |
|---|---|
| `cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v14` | [structured decision; inspect source](../results/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v14/decision.json) |
| `fx2_cmix_transformer_gcc_fixture50051_q0_v2` | [execution_failed](../results/fx2_cmix_transformer_gcc_fixture50051_q0_v2/decision.json) |
| `fx2_cmix_transformer_gcc_fixture50051_q0_v3` | [execution_failed](../results/fx2_cmix_transformer_gcc_fixture50051_q0_v3/decision.json) |
| `fx2_cmix_transformer_gcc_fixture50051_q0_v4` | [mapping_rejected](../results/fx2_cmix_transformer_gcc_fixture50051_q0_v4/decision.json) |
| `nncp_ggml_postupdate_forward_parity_64_q1_retry_v1` | [retry](../results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v1/decision.json) |
| `nncp_ggml_profile_forward_parity_64_qm13_v1` | [retire_exact_open_profile_forward_port](../results/nncp_ggml_profile_forward_parity_64_qm13_v1/decision.json) |
| `nncp_ggml_profile_forward_parity_64_qm18_v1` | [authorize_production_P_K_O_OK_F_S_attribution](../results/nncp_ggml_profile_forward_parity_64_qm18_v1/decision.json) |
| `nncp_libnc_bf16_gradient_merge_64_q0_retry_v5` | [retire](../results/nncp_libnc_bf16_gradient_merge_64_q0_retry_v5/decision.json) |
| `nncp_libnc_final_rmsnorm_affine_order_64_q0_v1` | [retry](../results/nncp_libnc_final_rmsnorm_affine_order_64_q0_v1/decision.json) |
| `nncp_libnc_final_rmsnorm_order_64_q0_retry_v1` | [retry](../results/nncp_libnc_final_rmsnorm_order_64_q0_retry_v1/decision.json) |
| `nncp_libnc_geglu_gate_avx2_64_q0_v1` | [authorize-successor](../results/nncp_libnc_geglu_gate_avx2_64_q0_v1/decision.json) |
| `nncp_libnc_profile_initial_fixture_65536_closurefix_q0_v1` | [authorize-integrated-replay](../results/nncp_libnc_profile_initial_fixture_65536_closurefix_q0_v1/decision.json) |
| `nncp_libnc_top_attention_product_oracle_64_q0_retry_v2` | [authorize-successor](../results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2/decision.json) |
| `nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1` | [retry](../results/nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1/decision.json) |
| `nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2` | [authorize-successor](../results/nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2/decision.json) |
| `nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2` | [authorize-successor](../results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/decision.json) |
| `nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1` | [authorize-successor](../results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1/decision.json) |
| `nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2` | [authorize-successor](../results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2/decision.json) |
| `nncp_open_branch_reduction_postupdate_64_q0_retry_v1` | [authorize-exact-reducer-integration](../results/nncp_open_branch_reduction_postupdate_64_q0_retry_v1/decision.json) |
| `nncp_open_concat_head_identity_64_q0_v1` | [authorize-successor](../results/nncp_open_concat_head_identity_64_q0_v1/decision.json) |
| `nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2` | [retire](../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2/decision.json) |
| `nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v1` | [authorize-successor](../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v1/decision.json) |
| `nncp_open_top_attention_forward_inputs_64_q0_v1` | [authorize-successor](../results/nncp_open_top_attention_forward_inputs_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_raw_branch_join_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_raw_branch_join_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_residual_conversion_order_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_residual_conversion_order_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_rmsnorm_backward_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_rmsnorm_backward_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1` | [authorize-successor](../results/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_total_adjoint_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_total_adjoint_64_q0_v1/decision.json) |
| `nncp_open_w_o_weight_slice_post_add_64_q0_v1` | [authorize-successor](../results/nncp_open_w_o_weight_slice_post_add_64_q0_v1/decision.json) |

## 2026-09-05 - Native MIDAS coder and causal scheduler pass synthetic checks

`lib/midas_native_codec.hpp` provides native finite Q16 arithmetic encoding and
decoding, explicit raw-byte identity framing, a pre-truth byte-to-bit adapter,
complete coder checkpoints and an exact first-state-divergence comparison.
`lib/midas_midpoint_schedule.hpp` provides the P/K/F/S update boundary: ordinary
parent updates after each 64 decoded bytes, an additional F update after the
first 32, and S with those already decoded targets cyclically shifted left once.
Every update rebuilds the active prefix from its retained segment origin. K
executes update and rebuild on a discarded copy, preserving the authoritative
parent. These are reusable components, not a sealed corpus candidate.

Three targeted tests pass with strict C++17 compilation. Separate address and
undefined-behavior sanitizer executions also pass. The native counting-fixture
payload equals the independently implemented Python payload; finite inverses,
repeats, corruption rejection, checkpoint continuation, P/K probability and
payload identity, and encoder/decoder state synchronization pass on synthetic
fixtures. The scheduler's sentinel deliberately invalidates recurrent state at
update, so prediction without rebuilding fails. These fixtures do not implement
or prove a neural predictor, complete-model gradients, or a MIDAS gain.

Evidence: `operations/evidence/20260905_midas_native_codec_scheduler_unit_validation.json`
binds source SHA-256 values, test commands, compiler identity and observed output.
Score credit is zero. The standalone trainable parent roundtrip remains missing.
No corpus experiment was launched and no partial HORIZON science was read.

The concurrent unregistered `programs/compact_midas_open_parent_q0_v1` source
tree was left untouched. Coordinate its owner before integrating the one compact
challenger: validate full gradients and optimizer/recurrent state, measure its
dominant kernel, and prospectively freeze the bounded parent P/K/F/S archive
gate. An independent eligible-parent explorer must preserve that ownership and
HORIZON's sole observer, retain source/package/resource bindings, and produce
exact finite archives without inheriting compression claims from a teacher.

## 2026-09-05 - Execute bounded comparisons against the updated frontier

The active objective is now `gamma-enwiki9-hutter-99m-v2`: at most
99,000,000 complete submission bytes. The 105M v1 contract and every historical
objective digest remain unchanged. `operations/provenance/competitive_frontier_v1.json`
retains September 5 source snapshots and separates the official displayed record
from contingent published submission figures. Endpoint428's 109,389,323-byte
forecast has 10,389,323 bytes of planning debt; no full-corpus deficit is measured.
Committee reference/accounting questions are drafted in
`workbench/committee-inquiry.eml` and have not been sent.

The existing release tools passed a real synthetic canary:
`results/release_canary_rle_q0_v1/release/20260905_acceptance_v1/canary-validation.json`.
Three independently built copies encoded 7,616 bytes into 2,998 archive bytes,
repeated the archive exactly, and decoded without corpus access. The counted
canary total is 5,403 bytes, including package and options; objective credit is
zero. Missing manifest/build files, tiny input presented as full enwik9, and a
canary presented as an objective receipt were rejected. Guard logs and declared
license notices are retained. This closes a release-machinery gate, not a
compression hypothesis or full-corpus certificate.

`lib/predictor.py` now supplies a reusable pre-truth Q16 bit interface with
explicit frontend identity, decoded-bit updates, deterministic state serialization
and trace-reuse bindings. Fixtures check encoder/decoder probability and state
agreement and reject silent frontend exchange. The existing `lib/driver.py`
runs frozen parent/bookkeeping/treatment/control arms from one candidate build,
retains exact/repeat artifacts and first-divergence diagnostics, then publishes
an atomic decision. Optional telemetry failures become missing diagnostics;
mandatory evidence remains necessary for promotion. No fixture compression is
credited to Gamma's competitive frontier.

HORIZON retains its original experiment predicates and sole observer. Its
recovery cannot recreate missing continuous resource certification. Independent
public-transformer reproduction and the smallest missing deep-MIDAS initializer
are bounded discovery work; shared-host timing is diagnostic. Fiber-FOSSIL's
failed exact-retrieval configuration remains retired. No joint gain or new
transformer compression inheritance is assumed.

## 2026-09-04 - Fiber-FOSSIL exact semantic retrieval is retired

The corrected opening-1M gate
`wiki_fiber_fossil_endpoint428_opening1m_receiptfix_q0_v1` completed with an
authoritative decision. Every evidentiary control passed: the raw inverse and
all eight finite-coder inverses were exact, the repeated semantic tape and
probability construction were identical, `P == K`, the output manifest was
complete, active-HORIZON access was denied, and the owned 512 MiB/zero-swap
cgroup peaked at 273,793,024 bytes and was removed without residue.

The scientific hypothesis was decisively refuted. Parent `P`, bookkeeping `K`,
and inactive opening-scope physical control `G` each produced a 173,859-byte
payload. Same-route exact-continuation `D` produced 173,937 bytes, a loss of 78
bytes instead of the required 4,080-byte saving. Its minimum chronological-third
saving was -42 bytes, its minimum control margin was -42 bytes, and it had zero
positive virtual-distance buckets. Only 311 bytes activated `D`; 253 donor
bytes were correct, confirming again that correct-byte counts do not establish
retained information against a mature parent.

This retires the frozen Fiber-FOSSIL same-route 16-byte exact-retrieval axis and
its dependent Fiber-LOOM/route-fast-weight successors without a parameter
sweep. It does not retire HARM-Delta. HARM-Delta remains a distinct experiment:
it aligns complete prior route values through causal match/substitute/insert/
delete state rather than requiring exact 16-byte lockstep. No Fiber result is
credited to or subtracted from HARM-Delta.

Evidence: `results/wiki_fiber_fossil_endpoint428_opening1m_receiptfix_q0_v1/decision.json`,
`results/wiki_fiber_fossil_endpoint428_opening1m_receiptfix_q0_v1/receipt.json`,
and `operations/adaptive/reflections/20260904T212450Z_50c3d23da3.json`.
