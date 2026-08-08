# Research Register Archive 003

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-07-26: delayed raw, heading, AUTOPSY-rule, and compact-neural closure

Five additional theorem transfers were tested against the archive-identical
endpoint428 probability trace.

- `delayed_raw_residual_apm_v1` exposed the last eight raw bytes only after
  complete WRT emission groups. Its fixed 65,536-row residual APM changed
  491,981 probabilities, incurred 3,149,920 deterministic evictions, and
  regressed 2,693 exact bytes.
- `heading_state_residual_apm_v1` classified completed wiki headings into ten
  decoder-visible discourse states. The fixed heading-conditioned predictor
  changed 3,957,565 rows and regressed 1,409 bytes.
- `heading_state_bayes_switch_v1` composed that expert with a paid-prior
  per-state Bayesian switch. Every posterior converged to the parent boundary;
  the exact result lost two finalization bytes. This closes the heading expert
  rather than merely its fixed blend.
- `finite_residual_rule_pair_v1` exhaustively searched every one- and
  two-coordinate rule over bit position, previous-byte nibbles, parent
  confidence, heading state, and causal modal-error age. The selected
  three-byte rule gained two bytes on the full opening but lost two bytes on
  sealed holdout.
- `compact_nncp_endpoint_mix_10k_v1` traced a causal 833K-parameter,
  three-layer, 128-wide NNCP expert over 10,000 WRT symbols. After 5,000
  symbols of burn-in, endpoint428 used 2,006 bytes and the expert used 3,369.
  The safe mixture exactly matched endpoint428. A sparse paid router selected
  no rule; its real holdout oracle was 1,753 bits versus 2,779 bits for a
  circular-shift null, identifying selection lottery.

The compact NNCP trace was observation-neutral: trace-on and trace-off
archives were byte-identical. The standalone five-layer, 256-wide compact
model also completed an exact 10,000-byte raw roundtrip, but its 9,434-byte
startup archive is not competitive. CPU controls and hashes are recorded in
`results/nncp_cpu_eligibility_controls_v1/receipt.json`.

Decision: retire delayed-raw APM tuning, fixed heading-state prediction,
single/pair-coordinate residual rules, and unchanged startup compact-NNCP
routing. A mature accelerated under-target teacher remains conceptually open,
but no local trace currently supplies that antecedent.

## 2026-07-27: Draft 3 audit and cmix21 memory-transfer problems

### TS-1 teacher-trace sufficiency

- The current bounded NNCP trace has 10,000 rows, vocabulary size 336, archive
  identity, and only the realized symbol probability. It is sufficient to
  measure teacher true-symbol loss but not to identify or distill the teacher
  distribution.
- `TS-1` proves non-identifiability and a minimax KL lower bound of `1-a` bits
  when only `(true symbol, true probability a)` is observed.
- A top-k vector plus aggregate tail mass is an exact sufficient statistic only
  for a student whose tail is uniform. General students require the complete
  vector, a lossless tail, or a proved tail model.
- The next expensive mature teacher trace must therefore capture the complete
  336-way vector or a frozen top-k/uniform-tail contract. The existing scalar
  trace remains zero-credit evaluation evidence.

### BQ-1 native NNCP binary probability quantization

- The pinned NNCP arithmetic source uses a binary range coder with
  `PROB_UNIT_BITS=15` and `PROB_UNIT=32768`; it does not directly use IF-1's
  flat multiclass frequency table.
- `BQ-1` solves clamped nearest integer quantization for this interface. Every
  true-event excess is at most `log2(3/2)` bits globally, with the useful
  interior bound `log2(alpha/(alpha-1/65536))`.
- Combined approximate-logit and probability-quantization loss is certified
  per bit, but the universal bound is too loose for a long prize stream.
  Exact trace-dependent summation or native replay is required.
- IF-1 remains valid for an alternative flat coder but is not represented as
  the native NNCP transfer path.

### IF-1 mandatory-positive integer frequencies

- `IF-1` gives a canonical largest-remainder projection from a neural
  probability vector to positive integer frequencies summing to `Q`.
- The construction guarantees `q_i >= (1-V/Q)p_i` and therefore a worst-case
  projection penalty of `log2(Q/(Q-V))` bits per symbol.
- Combined with NL-1, the per-symbol bound is
  `osc(delta)/ln(2) + log2(Q/(Q-V))`. If this bound alone exceeds NNCP's
  reproduced byte margin, the chosen frequency precision is rejected before
  native full-corpus work.
- Exact softmax/frequency semantics, online-state synchronization, native coder
  bytes, package, runtime, memory, determinism, and roundtrip remain required.

### NL-1 NNCP multiclass logit-margin certificate

- The pinned NNCP v3.3 source exposes Transformer and LSTM models, CPU threads,
  BF16 processing, online retraining, and sequential arithmetic coding. The
  published enwik9 command uses the Transformer profile with preprocessing;
  CPU eligibility remains the guarantee-bearing open route.
- `NL-1` proves the sharp multiclass perturbation envelope
  `Delta loss <= osc(delta)/ln(2)` bits and the uniform bound
  `2 epsilon/ln(2)` bits per symbol.
- Given exact symbol count `N`, concrete coder redundancy budget `R`, and the
  nominal published margin `H=738682`, a sufficient uniform logit error is
  `epsilon <= 4(H-R)ln(2)/N`. Layerwise and recurrent state errors must be
  included; ideal loss alone is not score credit.

### PE-1 padding-free state serialization

- `PE-1` constructs a canonical packed-record bijection and proves logical
  state conjugacy by induction. With identical coder semantics, a correct
  implementation must produce an identical archive, not merely an equal-size
  archive.
- For the fourteen-way `ContextMap2` record, the logical payload is exactly
  `28 + 98 + 1 = 127` bytes versus the current 128-byte aligned cell. The exact
  table-payload saving is one byte per bucket while preserving all ways and
  fingerprint bits.
- A C++ `packed` attribute is not sufficient evidence because unaligned typed
  accesses may be unsafe. Transfer requires explicit byte accessors or `memcpy`,
  per-event/coder-state identity, final archive-hash identity, RSS, runtime,
  package, roundtrip, and determinism receipts.

### PO-1 pooled overflow theorem

- `PO-1` derives the exact retention of fixed private bucket slots plus a
  shared overflow pool:
  `sum_i min(n_i,a) + min(P, sum_i (n_i-a)_+)`.
- Its proposed claim that total slots alone guarantee `min(total demand,
  total slots)` is false for fixed private cells. The counterexample
  `B=2, a=2, P=0, n=(0,4)` has four slots and four entries but retains only
  two. Global slot optimality requires every slot to be reassignable.
- This correction narrows the transfer experiment: before building pooled
  `ContextMap2`, Gamma must instrument causal overflow demand and count owner,
  link, alignment, source, and lookup costs. PO-1 has zero score credit.

### IC-1 exact interaction certificate

- `IC-1` proves the Boolean-lattice Möbius decomposition for simultaneous
  table interventions and gives an exact constrained optimizer under a valid
  degree bound. For 18 interventions, the additive screen needs 19 values and
  the complete pairwise model needs 172.
- The solution also proves a critical negative result: low-order measurements
  cannot certify a global low-degree interaction model for an unrestricted
  native archive-cost function. Audited triples or final allocations can
  falsify the model but cannot prove it globally.
- Therefore isolated memory/score penalties remain screens only. Every selected
  allocation still requires one joint native replay before receiving score
  credit.

### AF-1 and FP-1 aligned-cell reductions

- Native `B1` MV-2 completed a clean 10M one-pass screen at 1,638,269 archive
  bytes, 564,273 package bytes, and 9,651,604 KiB peak single-process RSS. It
  saves 71 archive bytes versus the retired global-FXCM2 10M screen and has
  114,021 KiB decimal-RSS margin. Roundtrip and determinism were intentionally
  not run, so score credit remains zero.
- Native `B2` ten-way/16-bit cells package to 564,146 bytes. The exact 250K
  gate produced 45,178 bytes with roundtrip and byte-identical determinism,
  peak RSS 9,397,956 KiB. Its 1M screen produced 174,531 bytes, exactly equal
  to `B1`, with peak RSS 9,572,292 KiB.
- `B2` therefore passes the frozen package, 250K, and 1M gates and advances
  unchanged to exact 10M with a first-archive ceiling of 1,638,781 bytes.
  No aligned-cell candidate has full score credit.

- `AF-1` solves the exact 32-byte-aligned associativity frontier for the
  existing `ContextMap2` representation. The complete undominated set is
  `{14, 10, 7, 3}`. In particular, twelve ways require 128 bytes, not 112, and
  are dominated by fourteen ways. This corrects the earlier informal A12
  continuation and excludes it before implementation.
- `FP-1` generalizes the cell calculation to bit-packed fingerprints:
  `C(A,b) <= Q` exactly when `A(b+56) <= 8(Q-1)`. It identifies two
  non-dominated 96-byte candidates: `(10 ways, 16 bits)` and
  `(11 ways, 13 bits)`. The latter retains one more way but has an 8.8x larger
  union-bound false-match ceiling.
- The originally posed FP-1 clause that twelve ways could not fit at seven
  fingerprint bits is false. The solution gives the exact counterexample
  `(A,b,Q)=(12,7,96)` and corrects the boundary. This is retained as negative
  specification evidence.
- Both results have zero compression credit until native joint replay,
  package accounting, exact roundtrip, determinism, decimal-10GB RSS, runtime,
  and transfer gates pass.

- `ACS-MATH-DRAFT-3-WORKING` was independently reconstructed and found mathematically complete. The audit is `docs/atlas_clockwork_seal_draft3_adversarial_audit.md`. It remains a theorem bank, not a transfer-bound examination.
- `ppmd_resident_valve_closure_v1` tested PPMD caps from 20,352 KiB down to 1,024 KiB on the frozen index-13 line. Every 250K run exceeded the official decimal memory limit, and sampled RSS was non-monotone. PPMD-only resident-memory tuning is closed with zero score credit.
- `MV-2 Exact Capacity Allocation` proved an exact finite capacity-knapsack construction and instantiated FXCM indices 5 and 7-17 at divisor two. The candidate saves 810 MiB beyond the index-13-only parent at the source allocation layer.
- The MV-2 250K exact gate passed at archive 45,178 bytes, program 564,273 bytes, exact roundtrip, deterministic replay, and 9,441,308 KiB peak single-process RSS. The 1M one-pass screen produced 174,531 bytes with 150,833 KiB decimal margin; it is shadow evidence only.
- A lock-held 10M one-pass MV-2 screen is active as PID 215555. It receives zero score credit until a full roundtrip and deterministic replay are completed.
- `BP-1 Fixed-Range Bucket Packing` proves that reducing FXCM ContextMap2 associativity from 14 to 10 changes the minimum 32-byte-grained cell from 128 to 96 bytes while preserving the hash bucket range. Source support is implemented but unbuilt and unmeasured while MV-2 owns the heavy lock.

## 2026-07-27 - FXCM full-idx13 plus PPMD joint budget composition

- Proposal: `fxcm_idx13_ppmd_joint_budget_v1`
- Candidate: `cmix21_text_mmap_paq5_ppmd44928k_fxcmassoc10tight92_fxcmidx13full_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Parent: `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10tight92_fxcmidx13full_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Mechanism: compose the semantics-preserving 92-byte FXCM cell layout, complete `idx13` capacity, and a PPMD arena increased from `20,352 KiB` to `44,928 KiB`.
- Mathematical receipt: `results/fxcm_joint_budget_composition_v1/theorem_verifier.json` proves an exact static payload delta of `106,283,008` bytes (`103,792 KiB`) relative to B2.
- Counted program package: `564,157` bytes.
- Status: materialized and unmeasured. It is not queued ahead of the active B2 gate or the already queued SLC archive-identity control.
- Promotion: exact roundtrip, deterministic second archive, decimal-memory guard, and archive improvement over both matched single-slice controls at identical scope.
- Kill: any reconstruction, determinism, or resource failure, or no archive gain over both controls.
- Score credit: `0` bytes.

## 2026-07-27 - NC5 native-domain candidate materialization

- Proposal: `nncp_compact5_preprocessed_maturity_v1`
- Candidate: `nncp_compact5_preprocessed_v1`
- Mechanism: standalone five-layer compact causal NNCP in the official reversible preprocessed symbol domain, without WRT transfer or teacher-state transmission.
- Candidate payload: `313,439` counted bytes: `2,150` bytes for `program.py` plus the canonical `311,289`-byte CPU source closure.
- Materialization receipt: `results/nncp_compact5_candidate_materialization_v1/receipt.json`.
- Package SHA-256: `79e5e7152ef2b419528157ae86e14570b0a87a4cb12765628963d415522f0102`.
- Frozen first gate: exact opening `1,000,000` raw bytes, archive ceiling `250,000`, deterministic second archive, exact raw roundtrip, and resource receipt.
- Status: materialized and unmeasured; native execution remains serialized behind B2 and SLC.
- Score credit: `0` bytes.

## 2026-07-27 - Canonical endpoint428 frontier materialization blocker

- Candidate: `endpoint428_gate_dot_fuse_output_update_loop_v1`.
- Frontier forecast: `109,389,323`; nominal design debt: `1,389,323`; exact full-1G result: absent.
- The adaptive workflow rejected a full-1G enqueue because `programs/endpoint428_gate_dot_fuse_output_update_loop_v1/meta.json` does not exist.
- The exact `280,147`-byte source package named by the 10M receipt has SHA-256 `19ddcc4ec1b6f31958bed4aa19c0fbc83a56c78121933e1447e4ee011547aee0`, but the receipt points to unavailable `/home/x/enwik9-nonproof` artifacts. No matching package, bundle, clean wrapper, or source root was found under the local nonproof root.
- Blocker receipt: `results/endpoint428_frontier_materialization_v1/blocker.json`.
- Required fix: recover the hash-matching source package from the originating host or reconstruct it from complete committed lineage, materialize the candidate, then enqueue exact full-1G proof.
- This host-level blocker does not invalidate the existing exact 10M receipt. It prevents a reproducible full-1G gate here.
- Score credit: `0` bytes.

Superseded on 2026-08-01 by the artifact recovery recorded below. This entry is
retained as history; its claim that the `/home/x/enwiki9-nonproof` artifacts
are unavailable is no longer current.

## 2026-07-27 - FXCM balanced minimum-priority replacement ties

- Proposal: `fxcm_balanced_min_tie_v1`.
- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10balmin_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`.
- Mechanism: on an FXCM checksum miss, retain minimum-priority replacement but select among equal minima using the checksum modulo the tie count instead of unconditional lowest-slot order.
- Mathematical result: every selected slot is eligible and minimum-priority; over all 16-bit checksums, tied selection counts differ by at most one; encoder/decoder synchronization follows by state induction.
- Evidence: `docs/fxcm_balanced_min_tie_problem.md`, `docs/fxcm_balanced_min_tie_solution.md`, `results/fxcm_balanced_min_tie_v1/theorem_verifier.json`, and `patches/fxcm_balanced_min_tie_v1.patch`.
- Counted program package: `564,622` bytes.
- Frozen gate: exact `250,000` raw bytes with roundtrip, deterministic second archive, decimal-memory receipt, and strict archive improvement over the unchanged parent.
- Status: materialized and queued behind the current serialized gates.
- Score credit: `0` bytes.

### NC5 10k infrastructure smoke

- Adaptive job `20260727T182229Z_02002f03ac` completed successfully on `10,000` raw bytes.
- Archive: `6,229` bytes; counted program: `313,439` bytes; exact raw roundtrip: pass; fresh second archive: byte-identical; archive SHA-256: `f5c71060344fcd7ad182dba2dca84f936c2a801281ca58ed5fe9eb8c5a156e26`.
- Receipt: `results/nncp_compact5_preprocessed_smoke_v1/receipt.json`.
- This is infrastructure evidence only. Startup comparison against LZMA does not test the frozen maturity hypothesis and must not retire the candidate.
- The adaptive runner was corrected so `infrastructure`, `diagnostic`, and `oracle` jobs no longer mutate candidate status. NC5 was restored to `candidate` through the canonical contract check.
- Next decision remains the exact opening-1M native-domain gate. Score credit remains `0` bytes.

## 2026-07-27: FRT-1 exact factoradic recency tie-breaking proposed

Candidate mechanism: `fxcm_factoradic_recency_tie_v1`.

The independent FRT-1 problem proves that the complete recency order of ten
ways needs exactly 22 bits because `10! = 3,628,800`, and gives canonical
Lehmer rank/unrank, move-to-front, and minimum-priority/LRU selection. A
32-bit rank fits at offset 92 in the otherwise unused tail of the frozen
96-byte B2 FXCM cell, so the mechanism changes replacement information without
increasing the dominant table allocation. The transfer remains fail-closed:
it preserves the existing priority minimum and uses exact LRU only among tied
minimum ways. Native implementation is not yet materialized. It must beat B2
by at least 8 archive bytes at frozen 1M and by at least 128 counted bytes at
exact 10M, with exact roundtrip, determinism, decimal-memory, package, and
distant-transfer receipts. The theorem and verifier receive zero score credit.

## 2026-07-27: RDC-1 NNCP-preprocessor plus B2-cmix composition materialized

Candidate: `nncp_pc_u16be_cmix21_assoc10_v1`.

RDC-1 proves exact dictionary-framed composition of a reversible preprocessor
and backend codec. The materialized candidate runs official NNCP `pc/pd`,
keeps the canonical big-endian 16-bit symbol stream, transmits the learned
dictionary inside the archive, and uses the frozen B2 cmix21 backend. Its
complete provisional package is recorded in the candidate metadata. The 1M
layout proxy was negative: raw LZMA was 290,692 bytes, while the best
transformed control, U16 big-endian plus its 804-byte dictionary, was 293,112.
Fixed-nine-bit, planar, little-endian, and escape layouts were worse and are
closed unchanged. Because this proxy cannot decide mature cmix interaction,
exactly one native gate is authorized with a target-scale 250K ceiling of
44,753 bytes. Any larger archive, package above 900,000 bytes, roundtrip,
determinism, or decimal-memory failure retires the route. No proxy or theorem
bytes receive score credit.

## 2026-07-27 - FRT-1 exact factoradic recency tie

- Status: developed, exact native 250K gate queued; score credit zero.
- Construction: the solved factoradic-recency problem encodes all `10!` way orders in a 32-bit tail field and chooses the least-recent eligible way only among the existing minimum-priority ties.
- Native candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10frt_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`.
- Counted package: `565130` bytes, `+984` versus B2 and below the predeclared `8192`-byte growth cap.
- Exact theorem evidence: `results/fxcm_factoradic_recency_v1/theorem_verifier.json`.
- Materialization evidence: `results/fxcm_factoradic_recency_v1/materialization.json`.
- Pending gate: `20260727T190337Z_1533fcbec5`.
- Decision boundary: no compression claim until exact roundtrip, deterministic re-encode, decimal-memory, score, and distant-transfer gates pass.

## 2026-07-27 - RDC-1 dictionary-free NNCP binary backend

- Status: developed, exact native 250K gate queued; score credit zero.
- Construction: official reversible NNCP preprocessing emits canonical U16BE symbols; frozen cmix21 is invoked in no-preprocessing mode and the unrelated cmix English dictionary is removed from the package.
- Native candidate: `nncp_pc_u16be_cmix21_assoc10_nopre_v1`.
- Counted package: `702813` bytes, `-175381` versus the forced-text RDC-1 parent.
- Mathematical basis: `docs/reversible_dictionary_backend_composition_problem.md` and `docs/reversible_dictionary_backend_composition_solution.md`.
- Materialization evidence: `results/nncp_binary_backend_dictionary_elimination_v1/materialization.json`.
- Pending gate: `20260727T190759Z_2bb1fb1160`.
- Decision boundary: the fixed package saving is real but earns no net-score credit until matched native archive, roundtrip, determinism, and distant evidence exist.

## 2026-07-27 - BPD-1 decoder-built prefix dictionary

- Status: independent mathematics solved; deterministic real-prefix learner verified; native 1M gate queued; score credit zero.
- Construction: encode the opening 262144 bytes without preprocessing, rebuild a canonical frequency/first-offset word dictionary from that decoded prefix, then encode the suffix in forced-text mode using the decoder-built dictionary.
- Native candidate: `cmix21_assoc10_bootstrapdict256k_v1`.
- Counted package: `390404` bytes, `-173742` versus B2.
- Learner receipt: 6412 unique words, 52919 dictionary bytes, 5300-word overlap with the 44515-word static dictionary, deterministic SHA-256 `35ff76580b4f5d322b1dad156a377c598bd714f6af93b5fd2345d2a6c7e47866`.
- Mathematical evidence: `docs/bootstrap_prefix_dictionary_problem.md` and `docs/bootstrap_prefix_dictionary_solution.md`.
- Materialization evidence: `results/bootstrap_prefix_dictionary_v1/materialization.json`.
- Pending gate: `20260727T191225Z_edc984f041`.
- Kill boundary: retire unchanged if the exact opening or distant 1M archive is more than 100 bytes worse than B2, because that rate consumes the fixed package saving at full scale.

## 2026-07-27 - EPT-1 exact package transcoding

- Status: independent mathematics solved; three recovered-payload identity receipts pass; native resource gates queued; score credit zero pending parent qualification.
- Theorem: replacing package encodings while recovering byte-identical executable, dictionary, or source-tar payloads preserves every compressor state and archive byte. The exact counted delta is the package-length delta.
- B2 XZ successor: package `475731`, exact delta `-88415`; receipt `results/exact_package_transcoding_b2_xz_v1/receipt.json`; gate `20260727T191536Z_4c3cc65e9d`.
- Compact5 NNCP XZ successor: package `248554`, exact delta `-64885`; receipt `results/exact_package_transcoding_nncp_compact5_xz_v1/receipt.json`; gate `20260727T191710Z_271f8504fb`.
- Dictionary-free NNCP binary XZ successor: package `568873`, exact delta `-133940`; receipt `results/exact_package_transcoding_nncp_binary_xz_v1/receipt.json`; gate `20260727T191814Z_059cec2c8e`.
- Boundary: archive identity is theorem-certified from recovered payload and wrapper-grammar identity, but native startup, memory, library availability, parent archive qualification, and official full-1G score remain measured obligations.
- Canonical index: `docs/enwiki9_constructive_mathematics_index.md`.

## 2026-07-27 - ELI-1 loader-identical stripped B2 package

- Status: independent mathematics solved; strict ELF loader projection and native startup control pass; exact 250K native archive/resource gate queued; score credit zero.
- Construction: strip nonloaded ELF metadata, restore the original ELF section-metadata header bytes that lie inside the first mapped page, and package the resulting loader-identical executable plus identical dictionary in LZMA-alone streams.
- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_striplzma_v1`.
- Exact package: `454876` bytes, `-109270` versus B2.
- Strict projection: all 13 program headers, descriptors, mapped payload hashes, entry point, machine, flags, and interpreter-visible bytes agree.
- Native startup control: old and new usage outputs are byte-identical (`482` bytes, SHA-256 `662521b1000f22951085167e2e5561df2bd4389f0dced0ea3427df27a14bfdfa`) with return code `255` on both executables.
- Evidence: `results/elf_load_image_b2_striplzma_v1/receipt.json`.
- Pending gate: `20260727T192337Z_1179f991ff`.
- Boundary: full native compression identity and official resources remain mandatory; the theorem does not transfer B2 score credit before those gates and B2's own terminal receipt.

## RPF-1: row-parallel floating-point equivalence for NNCP Compact5

**Status:** developed and queued; no compression credit.

The row-parallel theorem proves bitwise equivalence when output coordinates are partitioned among workers while every coordinate retains its original scalar reduction order. It does not license reassociation or parallel reduction within a coordinate. The construction was instantiated as `nncp_compact5_preprocessed_xz_t4_v1`, which changes only the NNCP worker count from one to four over the exact Compact5 reversible representation and XZ-transcoded source package.

The exact 10,000-byte gate is job `20260727T192837Z_c6f3177f63`. Promotion requires exact archive identity with `nncp_compact5_preprocessed_xz_v1`, exact reconstruction and deterministic re-encoding, plus at least 25% measured elapsed reduction. Any archive mismatch or insufficient speedup retires this instantiation without a thread ladder. This is a runtime-equivalence mechanism and receives zero score credit until native evidence passes all stated conditions.

## QSP-1: same-domain quantized NNCP soft quotient

**Status:** mathematics complete, observer and arithmetic mechanism instantiated, terminal startup negative, proposal rejected, zero score credit.

QSP-1 projects full NNCP teacher distributions onto finite decoder-visible suffix contexts. The exact dyadic table optimizer follows from discrete concavity: start every symbol count at one and allocate each remaining count to the largest current marginal cross-entropy reduction. A matched hard-label control uses identical contexts, denominator, serialization, and arithmetic coder.

The archive-neutral Compact5 observer is bound by `results/nncp_teacher_distribution_compact5_smoke_v1/receipt.json`. On 64 raw bytes it produced 78 u16be symbols; trace-on and trace-off archives were identical, raw reconstruction was exact, all distributions were positive and normalized, and the maximum normalization error was 1.326e-7. The QSP arithmetic encoder and decoder roundtripped at depths 0, 1, and 2.

The startup compression result is negative. On the 28-symbol chronological holdout, soft tables cost 5 to 6 more payload bytes than matched hard tables. After deterministic LZMA model cost, soft models were worse by 148, 2,091, and 1,724 bytes at depths 0, 1, and 2. This scope is a mechanics receipt, not mature predictive evidence.

The exact 1K successor contains 1,231 reversible symbols with an 820/411 chronological split. Although the teacher itself has 1,433.5 heldout ideal bits, soft suffix centroids lose 99 to 187 arithmetic payload bytes and 241 to 9,881 two-part bytes to their matched hard controls. Proposal `nncp_quantized_soft_quotient_student_v1` is rejected. Exclusion `qsp_suffix_centroid_1k_negative_v1` retires suffix depth, denominator, support, and table-cap tuning for this representation. A genuinely different causal student state may reuse the verified teacher observer. Teacher loss and all startup results receive zero score credit.

### QSP-1 observer reproducibility addendum

The Compact5 distribution observer now has two byte-identical clean builds under fixed file/debug prefix maps and `--build-id=none`. Both produce binary SHA-256 `17c7448c7d082273189852ad838341c23e057eb5b07e1e8df31faca9fe683972`; the deterministic rebuild reproduces the original archive and distribution-trace hashes exactly. The complete source, patch, compiler, flags, runtime-library binding, and twin-build evidence are recorded in `results/nncp_teacher_distribution_compact5_smoke_v1/deterministic_build_receipt.json`.

## DTA-1: deterministic teacher-automaton closure

**Status:** mathematics complete, exact mechanism instantiated, terminal startup negative, zero score credit.

DTA-1 canonically clusters full NNCP distributions, chooses the cellwise mode transition for every `(state, decoded_symbol)` pair, runs that transition table in closed loop, and fits exact dyadic soft outputs. A matched hard-label automaton shares the clustering, transition table, state trajectory, denominator, serialization, and arithmetic coder.

On the 1K Compact5 trace, both automata roundtrip and finish in the same encoder/decoder state. Deterministic closure conflicts on 125 of 819 teacher-state transitions, and the closed-loop path agrees with only 654 of 820 clustered teacher states. The soft automaton uses a 343-byte archive and 646-byte compressed model, versus 237 and 300 bytes for the hard control. It therefore loses 106 payload bytes and 452 complete two-part bytes.

Exclusion `dta_teacher_cluster_1k_negative_v1` retires automaton state-count, iteration-count, denominator, and centroid tuning. The verified teacher headroom remains an oracle for a genuinely different recurrent or factored-state student. No DTA quantity receives score credit.

## FLP-1: factorized dyadic-logit projection

**Status:** mathematics complete, exact mechanism instantiated, terminal startup negative, zero score credit.

FLP-1 uses decoder-visible symbol features at lags 1, 2, 4, and 8, with 64 buckets per lag and a bias table. A fixed convex softmax training schedule produces real teacher and hard-label models; both are quantized to int8 bit logits. Serialized dyadic exponential constants and exact largest-remainder normalization produce deterministic 4096-total arithmetic probabilities.

On the 1K Compact5 trace, both models roundtrip and neither clips a weight. The soft model uses a 328-byte archive and 3,992-byte compressed model. The matched hard model uses 97 and 3,935 bytes. Soft targets therefore lose 231 payload bytes and 288 complete two-part bytes.

Exclusion `flp_lag_logit_1k_negative_v1` retires startup-trace lag, bucket-width, epoch, learning-rate, and logit-scale tuning. Together with QSP-1 and DTA-1, this shows that the present startup teacher trace is useful for observer mechanics but not for selecting another soft-student architecture. Further distillation requires a mature batch-1 teacher trace and one newly frozen recurrent state. No FLP quantity receives score credit.

## 2026-07-27 - EPT-1 solid LZMA composition

The EPT-1 exact-package theorem was composed with the ELI-1 loader-identical
stripped B2 payload. The recovered `722448`-byte executable and `411996`-byte
dictionary are concatenated, encoded in one LZMA-alone stream, and split at the
fixed executable length after decoding. The solid payload is `452488` bytes,
`161` bytes smaller than ELI's two independent LZMA streams. Its `1548`-byte
wrapper yields a complete `454036`-byte package, exactly `840` bytes smaller
than the `454876`-byte ELI parent.

Both recovered payload hashes are identical to ELI. Proposal
`exact_solid_payload_b2_v1` is developed and queued as
`20260727T200845Z_6da7fed519` for an exact 250K native gate. Archive identity,
roundtrip, deterministic re-encode, resource inheritance, and parent
qualification remain measured obligations. Score credit is zero.

## 2026-07-27 - EPT-1 x86-filtered solid payload

A frozen two-chain screen compared raw LZMA2 against x86-filtered raw LZMA2 on
the exact `1134444`-byte ELI runtime payload. Plain raw LZMA2 regressed by 55
payload bytes. The x86-filtered chain produced `440245` bytes, saving `12243`
payload bytes versus solid LZMA-alone. After its `1717`-byte wrapper, candidate
`cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_stripx86rawlzma2_v1`
has a complete `441962`-byte package. This saves exactly `12074` bytes over the
solid parent and `121344` bytes over B2.

The recovered executable and dictionary hashes match ELI, and native usage
behavior matches exactly: return code `255`, `482` output bytes, SHA-256
`662521b1000f22951085167e2e5561df2bd4389f0dced0ea3427df27a14bfdfa`.
Proposal `exact_x86_filter_payload_b2_v1` is developed and queued as
`20260727T202000Z_86450232e2`. Native archive identity, exact roundtrip,
deterministic re-encode, resource inheritance, and parent qualification remain
measured obligations. Score credit is zero.

### ELI nonsegment suffix screen

The stripped executable remains `722448` bytes although the final
program-segment payload ends at byte `720122`. ELI-1 permits removing the
`2326`-byte nonprojected suffix while preserving every program header and
segment payload. The truncated executable has identical native usage behavior.
After the frozen x86-plus-LZMA2 transform, the payload falls from `440245` to
`439792` bytes, an additional exact `453`-byte package opportunity. Receipt:
`results/elf_nonsegment_suffix_x86_v1/screen.json`.

This successor is parked until the x86 parent proves native archive identity.
It has no native compression, determinism, roundtrip, resource, or score
credit.

### EPT segmented-filter control

A structural control reset the filter chain at the executable/dictionary
boundary: x86 plus raw LZMA2 for the executable and unfiltered raw LZMA2 for
the dictionary. Both streams reconstruct exactly, but their combined payload
is `440394` bytes, `149` bytes worse than the single `440245`-byte x86-filtered
solid stream before any second-stream wrapper cost. Decision: retire this
segmentation; do not reopen it through filter or preset ladders. Receipt:
`results/exact_segmented_filter_b2_v1/screen.json`. Score credit is zero.

## 2026-07-27 - SCC-1 source-closure compilation

SCC-1 proves the conditional transfer from a canonical finite source closure
to an ELI-equivalent executable and exact package accounting. The B2 instance
contains 72 source/build/license files plus the exact English dictionary in a
canonical 73-member USTAR archive. Raw LZMA2 compresses the `1218560`-byte
archive to `304731` bytes. With the corrected exact-recipe `2808`-byte
runtime-build wrapper, candidate `cmix21_b2_source_closure_rawlzma2_v1` has a
complete provisional package of `307539` bytes, saving exactly `134423` bytes
over the x86-binary parent and `256607` bytes over B2.

The archive roundtrips and its member manifest is path-safe and exact. Two
low-priority clean builds are byte-identical to each other and to B2:
`837176` bytes with SHA-256
`5913ac6c77b875f5871391db08fb01be3ecb9fff8db9dbc203a5c94bfe624adb`.
Their ELI projections and dictionaries also match exactly.
Proposal `source_closure_compilation_b2_v1` is developed and queued as
`20260727T204000Z_578a72f77b` behind the full-idx13 gate. Two clean builds,
ELI projection identity, and conditional archive identity are proved. Native
wrapper roundtrip, deterministic re-encode, compiler/runtime cost, and memory
remain mandatory. The screen receives zero score credit.

### SCC-1 canonical framing control

A fixed length-prefixed archive was compared with USTAR for the same 73
ordered source and dictionary members. It roundtrips exactly, reduces raw
framing from `1218560` to `1160638` bytes, and reduces the raw-LZMA2 payload
from `304731` to `303032` bytes. This is a `1699`-byte exact payload
opportunity, not a compiler or codec-parameter result. Receipt:
`results/source_closure_framing_b2_v1/screen.json`.

The framing successor remains parked until the USTAR SCC-1 parent proves
clean-build and native archive identity. Score credit is zero.

## 2026-07-27: CQQ-1 C++ comment quotient

CQQ-1 proves and instantiates a deterministic source quotient for the frozen B2 source closure. The scanner removes comments while preserving every physical newline and all non-comment preprocessing tokens, rejects unsupported lexical cases, and serializes the same canonical 73-member closure. It removed 67,380 source bytes and reduced the raw-LZMA2 payload from 304,731 to 284,583 bytes.

Two independent clean builds from the quotiented closure produced the exact parent executable and dictionary: executable size 837,176 bytes with SHA-256 `5913ac6c77b875f5871391db08fb01be3ecb9fff8db9dbc203a5c94bfe624adb`; dictionary size 411,996 bytes with SHA-256 `4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a`. The materialized wrapper is 2,808 bytes, giving a 287,391-byte counted package. This saves 20,148 package bytes against SCC-1, 154,571 against the x86-filtered package, and 276,755 against B2.

Evidence remains `proxy` with zero score credit because no native archive, exact roundtrip, deterministic second archive, runtime, or memory receipt exists for this package. Job `20260727T210000Z_3b7725d39e` is queued behind the heavy-lock chain. If native execution fails or changes the archive, retire this realization rather than adding another comment or whitespace parameter ladder.

## 2026-07-27: LPWQ-1 line-preserving C++ whitespace quotient

LPWQ-1 is an independent source-equivalence theorem and constructive successor to CQQ-1. It preserves every preprocessing directive group, ordinary backslash-newline group, physical newline, literal byte, and non-whitespace byte. On all other lines it maps horizontal whitespace outside literals to a canonical one-space internal form and removes boundary whitespace. The proof establishes idempotence, preprocessing-token identity, `__LINE__` identity, macro-stringification identity, and exact codec transfer conditional on build-output identity.

The frozen transformer changed 70 of 73 closure members, reduced eligible source from 640,568 to 538,268 bytes, reduced canonical USTAR from 1,146,880 to 1,044,480 bytes, and reduced raw-LZMA2 payload from 284,583 to 277,064 bytes. Two independent low-priority builds took 29.37 and 27.22 seconds with peak compiler RSS 337,420 and 337,720 KiB. Both produced the exact parent executable SHA-256 `5913ac6c77b875f5871391db08fb01be3ecb9fff8db9dbc203a5c94bfe624adb` and dictionary SHA-256 `4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a`.

The unchanged 2,808-byte wrapper gives a 279,872-byte counted package, saving 7,519 bytes against CQQ-1, 27,667 against SCC-1, 162,090 against the x86 package, and 284,274 against B2. Evidence is `proxy`; score credit is zero until the native exact gate proves archive identity, roundtrip, deterministic replay, runtime, and memory. CQQ-1, SCC-1, and solid-LZMA native jobs are dominated and replaced by LPWQ-1; the x86 package remains a distinct prebuilt-runtime control. No whitespace or compressor-parameter ladder is authorized after this canonical quotient.

## 2026-07-27: BPDQ-1 bounded adjacent-prefix dictionary quotient

BPDQ-1 is an independent finite code for the 44,515-line runtime dictionary. Each record stores one byte equal to 32 plus its adjacent longest-common-prefix length, its suffix, and line feed. The frozen maximum LCP is 17, so record markers cannot collide with delimiters. The proof gives exact inversion, unambiguous boundaries, a closed-form representation length, canonical archive transfer, and exact codec inheritance after restored-runtime identity.

The tracked encoder maps the 411,996-byte dictionary to 362,457 bytes and reconstructs SHA-256 `4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a` exactly. The LPWQ-1 raw-LZMA2 payload falls from 277,064 to 270,395 bytes. The restoration wrapper grows from 2,808 to 3,514 bytes, leaving a complete counted package of 273,909 bytes. Net package saving is 5,963 bytes against LPWQ-1, 13,482 against CQQ-1, and 290,237 against B2.

The wrapper restored every one of the 73 parent members exactly; the restored closure content hash is `d45eef7c0de21fd4085259175c3e115732396551a360aa2ae1eecc907400daf8`. Its own low-priority build completed in 31.75 seconds at 337,388 KiB peak RSS and produced the exact parent executable and dictionary. The prior two LPWQ-1 clean builds provide independent runtime determinism witnesses.

A general unambiguous varint-prefix and varint-suffix representation was measured negative: payload 291,640 bytes, 14,576 bytes worse before wrapper cost. The earlier newline-delimited raw prefix-byte sketch was ambiguous and receives no evidence. No prefix-code parameter ladder is authorized. BPDQ-1 remains `proxy` with zero score credit until native archive, roundtrip, deterministic replay, runtime, and memory receipts pass.

## 2026-07-27: FCF-1 finite path-payload closure frame

FCF-1 replaces USTAR metadata and 512-byte padding with a proved finite frame containing magic, member count, fixed-width path and payload lengths, UTF-8 relative paths, and payload bytes. The theorem proves exact inversion, unique boundaries, safe root-relative extraction, exact frame length, and codec inheritance after runtime identity.

On the 73-member BPDQ-1 closure, raw framing falls from 993,280 to 941,417 bytes and raw-LZMA2 payload falls from 270,395 to 269,306 bytes. The safe decoder wrapper grows from 3,514 to 4,303 bytes, leaving a complete 273,609-byte package and a narrow but exact 300-byte net saving. Its own extraction and build completed in 33.87 seconds at 337,264 KiB and reproduced the exact parent executable and dictionary.

Two other exact dictionary representations were closed. Lexicographic sort plus explicit 16-bit original ranks produced a 317,020-byte payload, 39,956 bytes worse than LPWQ-1. Splitting source and BPDQ dictionary into independent raw-LZMA2 streams produced 270,826 bytes including framing, 431 bytes worse than the unified BPDQ payload before decoder growth. Both receive zero score credit and no parameter or split ladder is authorized.

FCF-1 remains `proxy` with zero score credit until native archive, roundtrip, deterministic replay, runtime, and memory receipts pass. It replaces the BPDQ-1 native job; prior theorem artifacts remain provenance and controls.

## 2026-07-27: NNCP Compact5 T4 x86-filtered XZ package

The exact-package transcode theorem was applied to the frozen Compact5 T4 source tar. XZ branch conversion plus LZMA2 preset 9e reduces the source payload from 246,404 to 240,720 bytes. The unchanged 2,161-byte wrapper gives a 242,881-byte complete package, saving 5,684 bytes against the plain-XZ T4 candidate and 70,558 bytes against the original gzip Compact5 package.

The extended exact-tar verifier recovered the same 849,920-byte tar with SHA-256 `13dcffd1da71bc80f78aade9174cdee709894435e88e89b71a314fb28ac29081` and required byte-identical wrappers. Archive identity therefore follows if the frozen T4 runtime is deterministic. Evidence remains `proxy` with zero score credit because T4 archive identity, native roundtrip, runtime, and memory are unmeasured. Job `20260727T192837Z_c6f3177f63` was replaced by the x86 successor rather than duplicated. No XZ-filter ladder is authorized.
## 2026-07-27: NNCP CQQ plus x86-XZ normalized-build transfer

`nncp_compact5_preprocessed_cqq_x86xz_nodebug_t4_v1` applies the proved C/C++ comment-and-horizontal-whitespace quotient to 13 files in the exact Compact5 NNCP source closure, canonicalizes the resulting tar, compresses it with the x86-XZ frame, and freezes a no-debug compiler invocation.

The C/C++ source fell from 264,619 to 234,425 bytes. The x86-XZ payload fell from 240,720 to 234,216 bytes. After charging the 2,294-byte wrapper, the counted package is 236,510 bytes, 6,371 bytes below its 242,881-byte parent.

Normalized parent and quotient builds produced byte-identical 144,904-byte `nncp` executables and byte-identical 565,336-byte `libnc.so` files. This proves exact build-output identity under the frozen flags, not native archive identity under the complete wrapper. The exact 10K roundtrip, determinism, archive, runtime, and memory gate remains pending. Score credit is zero.
## 2026-07-27: FCFM-1 finite XZ-family minimum

FCFM-1 formalizes exact minimization over a committed finite deterministic codec family. Its verifier re-encodes and decodes every family member, commits the ordered family, and selects by payload length, decoder-memory rank, then canonical parameter text.

On the 819,200-byte CQQ NNCP source tar, all 377 committed XZ descriptions roundtripped. The unique tie-broken winner is `dict=768KiB,lc=4,lp=0,pb=0,mode=normal,nice=112,mf=bt2,depth=256`: 233,000 bytes, 1,216 below its CQQ parent payload. The full package is 235,294 bytes, 1,216 below the CQQ parent and 7,587 below the original x86-XZ parent. The restored tar and normalized binaries are exact. Native 10K archive and resource gates remain pending, so score credit is zero.

The generic finite-closure-frame instantiation produced only 112 gross payload bytes on this closure and was not materialized because its decoder would add a new counted parser. This closes FCF for this NNCP package unless a decoder-free embedding is found.
## 2026-07-27: DWNF-1 deterministic NNCP wrapper normal form

DWNF-1 gives a path-alpha bisimulation for deterministic build-and-run wrappers. The Compact5 instance reduces the frozen Python wrapper from 2,294 to 1,099 bytes while preserving the source payload, effective normalized build flags, fixed T4 arguments, dynamic-library environment rule, input/output byte operations, and exact `nncp` and `libnc.so` hashes.

The complete package is 234,099 bytes: 1,195 below the finite-XZ-family parent and 8,782 below the original x86-XZ parent. Static and build transfer pass. Native archive, roundtrip, determinism, runtime, and memory remain pending, so score credit is zero.
## 2026-07-27: PPC-1 probability-cell transfer theorem

PPC-1 proves that a decoder-visible CPU student need not reproduce neural floating probabilities. It need only remain inside the teacher's exact arithmetic-quantizer cell at every decoded prefix. Rational polyhedral box containment then proves identical integer frequencies, coder-state induction proves an identical archive, and decoder induction proves teacher-free reconstruction.

The exact rational verifier passes strict-boundary and non-strict synthetic controls. No Compact5 teacher/student instance is yet bound, so this is a theorem-library module with zero score credit. It becomes target-bearing only after the NNCP native gate establishes a valid teacher archive and a real compiled student supplies target-wide interval evidence.
## 2026-07-27: HRQ-1 exact NNCP branch-frequency target

Source inspection fixes the actual Compact5 coder boundary. `write_sym` recursively bisects the active vocabulary and calls `put_bit` with `prob0 = clamp(lrintf(p0*32768/p),1,32767)`. HRQ-1 proves that a student can predict only the visited integer branch frequencies. It need not reconstruct or ship the full floating distribution.

The observation patch records execution index, symbol, vocabulary, coder counts, branch bits, and exact 15-bit frequencies after the normal coding operations. The verifier checks the unique split path and archive neutrality. This directly supersedes the retired suffix-centroid student representation, but it remains uninstantiated until a mature batch-1 trace and compact causal branch student exist. Score credit is zero.

The existing 1,231-row batch-1 distribution trace was converted through the
pinned `vec_sum_f32` implementation into 9,848 branch targets. The 65,267-byte
derived trace passes split and coder-continuity verification. A matched
branch-centroid screen tested twelve depth/support configurations. Soft teacher
centroids lost to hard-label controls in all twelve by 792.032 to 1,502.377
ideal bits. This retires scalar suffix centroids, not HRQ stateful students.

## 2026-07-27: DSAQ-1 and ROLQ-1 recurrent NNCP branch students are startup negative

Two independent constructive results were added and solved:

- `DSAQ-1` proves decoder synchronization, finite-state causality, a unique
  Schur-complement ridge construction, coefficient quantization bounds, and
  log-loss transfer for decoded-state affine students.
- `ROLQ-1` constructs a monotone symmetric exact rational-odds lookup from
  integer scores to positive uint15 branch frequencies, with approximation and
  loss bounds.

Both were instantiated on the exact `1231`-symbol, `9848`-branch batch-1 trace
with `800` chronological training symbols and `431` sealed holdout symbols.
The only recurrent state used node-local and global decoded-branch EWMAs at
shifts `2,5,9,13`. Soft-teacher and hard-label controls had identical state and
serialization shape.

The affine soft recurrence improves its static soft control by `390.570071`
ideal bits but loses the matched hard recurrent control by `508.672803` bits.
The rational-odds soft recurrence improves its static soft control by
`361.612590` bits but loses the matched hard recurrent control by `527.486407`
bits. The hard recurrent variants save `63.552880` and `57.522021` payload bits
respectively, but neither repays added packed model bytes. Compressed-model
variation does not override the equal-capacity hard-control failure.

Proposal `nncp_decoded_state_logit_student_v1` is rejected and OMEGA exclusion
`nncp_decoded_state_branch_affine_startup_v1` retires the frozen shift, ridge,
score-range, affine-frequency, and rational-odds-logit neighborhood. A mature
trace may justify a genuinely different predictive-state quotient, but no
shift/ridge/range ladder is authorized. These are causal shadows with zero
score credit.

Evidence:

- `docs/decoded_state_affine_quantizer_problem.md`
- `docs/decoded_state_affine_quantizer_solution.md`
- `docs/rational_odds_lookup_problem.md`
- `docs/rational_odds_lookup_solution.md`
- `results/nncp_branch_affine_state_1k_v1/decision.json`
- `results/nncp_branch_logit_state_1k_v1/decision.json`

## 2026-07-27: LMC-1 build-literal migration and DWNF-1 B2 composition

LMC-1 formalizes moving a fixed runtime literal from wrapper source into an
already compressed immutable closure. Exact economics require the global
wrapper-plus-compressed-closure difference; literal length alone is not a
certificate. Path freshness, safe extraction, exact literal recovery, and
path-alpha bisimulation preserve effective execution labels.

On the 73-member FCF/BPDQ B2 closure, the 493-byte build flags become member
`cmix21/.gamma_lflags`. The raw frame grows 519 bytes, while raw-LZMA2 grows
only 149 bytes, from 269306 to 269455. The ordinary wrapper shrinks from 4303
to 3774 bytes, so LMC-1 alone saves 380 complete package bytes.

A DWNF-1 successor reduces that wrapper from 3774 to 1885 bytes. The final
package is 271340 bytes, saving 2269 bytes against FCF-1 and 292806 bytes
against original B2 package accounting. A clean build used 337488 KiB and
reproduced the exact 837176-byte executable and 411996-byte dictionary hashes.

The obsolete pending FCF-1 250K job was cancelled and replaced by
`cmix21_b2_line_whitespace_bpdq_fcf_flagsrawlzma2_minwrap_v1` at priority 941
with the unchanged 45178-byte archive ceiling. This is a constructive package
proxy with zero score credit until native archive, roundtrip, determinism,
runtime, and memory pass.

Evidence:

- `docs/literal_migration_compression_problem.md`
- `docs/literal_migration_compression_solution.md`
- `results/literal_migration_fcf_b2_v1/migration.json`
- `results/literal_migration_fcf_b2_v1/screen.json`
- `results/literal_migration_fcf_b2_v1/restoration_build.json`

## 2026-07-27: SCLE-1 NNCP Makefile slack carrier saves 80 package bytes

SCLE-1 embeds a fixed literal inside unused alignment slack of an existing
framed member. It proves unchanged total container length and offsets, exact
literal recovery, semantic identity under an ignored carrier extension, and
the complete wrapper-plus-global-codec accounting inequality. Unchanged raw
length does not imply unchanged compressed length, so the full codec family
must be rerun.

The 788-byte NNCP Makefile has 236 bytes of tar-block slack. Appending a
145-byte `#G=` marker plus evaluated CFLAGS leaves 91 bytes, preserves the
819200-byte tar length, and changes no bytes outside the Makefile header and
allocated data block. All 377 committed XZ configurations were re-evaluated.
The exact child minimum is 233012 bytes at `dict=800KiB,lc=4,lp=0,pb=0,
mode=normal,nice=112,mf=bt2,depth=256`, only 12 bytes above the parent payload.

Reading the carrier reduces the wrapper from 1099 to 1007 bytes. Complete
package size falls from 234099 to 234019 bytes, saving 80. The normalized
144904-byte nncp and 565336-byte libnc.so hashes remain exact. The old priority
956 parent job was cancelled and replaced by
`nncp_compact5_preprocessed_cqq_x86xzopt_nodebug_t4_tarslack_v1` at priority
957 with the unchanged 6229-byte 10K archive ceiling. The HRQ native observer
watcher was rebound to this successor. Score credit remains zero pending the
native gate.

Evidence:

- `docs/slack_carrier_literal_embedding_problem.md`
- `docs/slack_carrier_literal_embedding_solution.md`
- `results/nncp_makefile_slack_embedding_v1/embedding.json`
- `results/nncp_makefile_slack_embedding_v1/xz_family.json`
- `results/nncp_makefile_slack_embedding_v1/build.json`

## 2026-07-27: CWVE-1 removes 504 certified internal-validation bytes from B2

CWVE-1 proves stuttering bisimulation after deleting pure successful checks over
a sole immutable, hash-bound package object. It explicitly excludes checks on
external corpus bytes, archive bytes, arithmetic state, subprocess outcomes,
and roundtrip output.

The frozen verifier certifies all eliminated predicates on the migrated B2
closure: 74 unique safe relative FCF paths, every endpoint in bounds, final
cursor exactly 941936 with no trailing bytes, 44515 nonempty BPDQ records, and
all prefix lengths valid with maximum LCP 17. The wrapper falls from 1885 to
1381 bytes while the 269455-byte payload remains exact. Complete package size
falls from 271340 to 270836, saving 504 bytes. A clean build at 337936 KiB
reproduces the exact 837176-byte executable and 411996-byte dictionary hashes.

The prior minwrap pending job was cancelled and replaced by
`cmix21_b2_line_whitespace_bpdq_fcf_flagsrawlzma2_cwve_v1` at priority 942 with
the unchanged 45178-byte 250K archive ceiling. Score credit is zero pending
native archive, roundtrip, determinism, runtime, and memory evidence.

The bounded second SCLE attempt on NNCP runtime arguments is negative and
excluded. Its dispatch refactor saves 7 wrapper bytes, while the 82-byte
residual-slack marker adds 104 bytes to the selected payload, a 97-byte package
regression. No full family enumeration or parameter ladder is authorized.

Evidence:

- `docs/closed_world_validation_elimination_problem.md`
- `docs/closed_world_validation_elimination_solution.md`
- `results/closed_world_validation_elimination_b2_v1/certificate.json`
- `results/closed_world_validation_elimination_b2_v1/build.json`
- `results/nncp_makefile_slack_embedding_v1/runtime_args_screen.json`

## 2026-07-27: JMF-1 joint multinomial full-symbol fibers are terminal negative

JMF-1 is the exact joint successor left open by the prior independent
symbol-fiber exclusion. It pools every selected WRT symbol fiber and one
residual category into a single without-replacement multinomial stream. The
theorem proves the multinomial count, its sequential probability
factorization, an exact count-weighted zero-one knapsack for the best ideal
subset, and causal reconstruction before parent predictor updates.

The frozen gate reads all 4,805,936 exact endpoint decisions aligned to
600,742 WRT bytes. It reproduces the 175,188-byte parent range payload,
verifies a nonempty finite side-coder control, and verifies residual and WRT
roundtrips. The exact ideal optimizer selects the empty set. The best nonempty
joint subset is already 93.190432 bits worse before finite-coder overhead or
the measured 4,484-byte compressed standalone source cost.

Decision: retire joint full-symbol multinomial extraction on this substrate.
Do not reopen selected-symbol subsets, coupled-count choices, or side-coder
parameter ladders. This does not close context-conditioned joint fibers,
variable-length phrase fibers, a new causal information source, or same-domain
compilation of a mature under-target teacher. Score credit is zero.

Evidence:

- `docs/joint_multinomial_fiber_problem.md`
- `docs/joint_multinomial_fiber_solution.md`
- `tools/joint_multinomial_fiber_gate.cpp`
- `results/joint_multinomial_fiber_v1/decision.json`
- `operations/adaptive/exclusions/joint_full_symbol_multinomial_opening1m_v1.json`

## 2026-07-27: PCMF-1 paid context-two multinomials are terminal negative

PCMF-1 transmits complete next-symbol count vectors for selected causal
two-byte WRT contexts, codes those context subsequences without replacement,
and leaves all other positions on the exact parent range coder. The theorem
proves context partitioning, multinomial and binary-tree probability
factorization, exact paid context selection, and decoder-prefix
reproducibility.

The frozen opening-1M gate reproduces all 4,805,936 parent decisions and the
175,188-byte parent payload. The nonempty side-coder control, residual coder,
and 600,742-byte WRT reconstruction all pass. No context has positive paid
ideal contribution. The best single context is already 31.335846 bits
negative before the shared frame, finite range-coder overhead, or the measured
4,316-byte compressed standalone source cost.

Decision: retire context-two complete conditional multinomials and do not run
a context-length, support-pruning, or probability-resolution ladder. A
successor needs dynamic causal state, variable-length events, or a mature
under-target teacher rather than another static future-count table. Score
credit is zero.

Evidence:

- `docs/paid_conditional_multinomial_problem.md`
- `docs/paid_conditional_multinomial_solution.md`
- `tools/paid_conditional_multinomial_gate.cpp`
- `results/paid_conditional_multinomial_c2_v1/decision.json`
- `operations/adaptive/exclusions/paid_conditional_multinomial_c2_opening1m_v1.json`

