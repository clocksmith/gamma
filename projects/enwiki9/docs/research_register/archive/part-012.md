# Research Register Archive 012

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-08 - NNCP/Endpoint common-raw-block routing closure

Candidate `nncp_endpoint_commonblock_route_qm0_v1` compared the exact mature
NNCP and Endpoint428 conditional losses only after aggregating them onto 35
identical decoder-common raw blocks spanning `[6,757,802, 8,991,577)`. It never
mixed probabilities across their incompatible alphabets. Endpoint428 costs
`349,389.971` qbit-equivalent bytes; NNCP costs `414,466.459`. Endpoint wins
every block. The framed noncausal oracle loses `284.375` bytes, while the
one-block-lag causal route selects zero NNCP blocks and loses `280` bytes with
chronological thirds `-96`, `-96`, and `-88`. The rotated control is identical.

Disposition: retire routing between these two frozen mature representations.
This result does not test retraining a CMIX backend on NNCP symbols, but it
substantially lowers that cross's prior. Exact trace permutation, WRT inverse,
common-boundary, and decimal-memory proofs pass. Score credit is zero. Decision
SHA-256: `e83545f6fd91a15d0bc24e15b14c69bd252e915cb104a3068b52bbb2a34c5f7a`;
guard SHA-256:
`25aeb7bebc6b2ab85d5489c52d405e2fbc29aa847541a0e5e79cbb139de74025`.

## 2026-08-08 - SABLE preceding-context deterministic ceiling

Candidate `sable_precontext_consensus_qm0_v1` corrected the far-history
activation boundary by using only the 32 transformed bytes preceding each
target. Exact contexts are admitted only after they are strictly more than
60,000,000 bytes old; all candidate continuations are intersected, compared
with the actual target, and counted as a disjoint chronological union. Two
full-stream scans and interval artifacts are byte-identical.

The result contains `2,952,843` distinct correctly implied bytes, which is
`1,103,982` below the `4,056,825` debt-plus-allowance-plus-reserve gate. This
fails even under the impossible ceiling of eight saved bits per addressable
byte, so no donor probability extraction is warranted. The shifted-37 control
covers only `149,731` bytes; genuine coverage is positive by thirds at
`140,561`, `361,577`, and `2,450,705` bytes. The compact state payload alone
is at least `230,625,536` bytes. Because the public donor already exceeds the
strict decimal limit, an additive realization would require at least `897,596`
KiB of identified donor-memory removal.

Disposition: retire deterministic preceding-context consensus on this frozen
context width, anchor rule, distance, and donor stream. This does not prove an
upper bound for probabilistic disagreeing-source experts, but such a successor
needs an independently target-bearing causal ceiling. Score and forecast
credit remain zero. Decision SHA-256:
`5e7eb5a124dfff6ed35181c1f6b588cf80a0ec5f8d73933283b6859d6a6ad3c2`;
guard SHA-256:
`93600c13dfcbb4be106f6bcc02fe10386ecce4e8a1aa9a0d81690df2e55a9049`.

## 2026-08-08 - NNCP mature symbol-domain hierarchical PPM closure

Candidate `nncp_symbol_hierppm_mix_qm0_v1` replayed the exact 1,998,848-row
NNCP trace, preserved its original-ordinal permutation and state-major
32-stream schedule, and scored only the complete mature 499,712-symbol block.
It mixed normalized decoder-built order-0, stream-order-1, stream-order-2, and
execution-order-1 symbol models with NNCP through per-stream Bayesian switches
reset at the existing 64-symbol update boundary.

The best arm, stream-order-2, loses `854.541` ideal bytes with chronological
thirds `-289.304`, `-303.849`, and `-261.388`. It recovers only `96.140` bytes
over stream-order-1 and `121.459` over the execution-order-1 control, versus
the frozen 1,000-byte margins. Its standalone loss is `4,754,514` bits against
NNCP's `3,316,098`. Peak RSS is `304,684` KiB and the source package is `5,708`
bytes.

Disposition: retire this PPM hierarchy, concentrations, native-stream context,
and 64-symbol switch without order or parameter sweeps. A successor must
change NNCP's learned recurrent state or symbol representation and show its own
mature headroom. Score and forecast credit remain zero. Decision SHA-256:
`cc6d8fd9e5f148f500c236bbeba1390ff07dbd0317c0fb2bc10ba7a12c135a05`;
guard SHA-256:
`5f5a5071fedb35db25f931d6ddc714b41c34160bc13e249cdcdba7cc4e38aac4`.

## 2026-08-08 - NNCP evicted-state EMA memory closure

Candidate `nncp_evicted_ema_memory_qm0_v1` changed one coordinate of the exact
65,536-symbol incremental-KV NNCP construction. For every layer and stream,
the oldest slot became a decoder-built decay-0.5 summary of the oldest 64 exact
states, while the newest 255 states, the 256-slot allocation, parameters,
optimizer, attention, arithmetic alphabet, and update schedule remained fixed.

The candidate archive is `96,129` bytes versus the faithful `96,142`, an actual
gain of only `13` bytes against the frozen `800`-byte gate. Aligned ideal gain
is `12.114` bytes and is positive but negligible in corpus-chronological thirds
at `3.474`, `6.032`, and `2.608` bytes. Two encoders reproduce byte-identical
archives and complete states; decoder symbols, branch frequencies, losses, and
official NNCP raw inverse all agree. Peak allocated and reserved device memory
are `8,884,454,400` and `9,525,264,384` bytes. The incremental source package
is `4,768` bytes.

Disposition: retire the one-slot decay-0.5 oldest-64 mean mechanism. Do not
sweep decay, slot count, pooling, or context length around it. The result shows
that this fixed compressed-memory coordinate is causal and exact but carries
no target-scale headroom. Score and forecast credit remain zero. Decision
SHA-256:
`4b8801b250f6e2dc7d382b74064227f7f0e306983414a189232f9945c8b6efce`;
guard SHA-256:
`3f389587e2aff8dae887439d75c09ebc9403fc13e93a7af191bdef72ad0dd815`.

## 2026-08-08 - NNCP hierarchical 448-position memory closure

Candidate `nncp_hierarchical_448_memory_qm0_v1` replaced the flat 256-vector
hidden memory with 64 four-state historical means followed by 192 exact recent
states. This nominally covers 448 causal positions while preserving the exact
tensor shape, parameters, optimizer, attention, arithmetic alphabet, update
schedule, and incremental-KV path. It is a two-resolution representation, not
a parameter variation of the one-slot EMA.

The candidate archive is `96,145` bytes versus the faithful `96,142`, an actual
loss of `3` bytes against the frozen `800`-byte gain gate. Aligned ideal gain is
`-3.674` bytes, with true corpus-chronological thirds `-10.542`, `+18.897`, and
`-12.030`. Two encoders reproduce byte-identical archives and complete states;
decoder symbols, branch frequencies, losses, and official NNCP raw inverse all
agree. Peak allocated and reserved device memory are `8,884,454,400` and
`9,537,847,296` bytes. The incremental source package is `5,468` bytes.

Disposition: retire the fixed 64-summary, four-state-mean, 192-exact geometry.
Do not sweep summary count, pooling width, or horizon around it. Together with
the one-slot EMA result, this closes simple parameter-free NNCP tail-memory
compression at the exact 65,536-symbol gate; a successor must change the
learned state or coded representation and establish new mature headroom. Score
and forecast credit remain zero. Decision SHA-256:
`39066d304371cff4aa9bae642083814168f042662a3dedb38d460806e8d06832`;
guard SHA-256:
`2da824abf04d51b4dae06f4c89204ef82b002153788567bcd4206fbd258a63b3`.

## 2026-08-08 - NNCP zero-table Zipf output-prior candidate frozen

Candidate: `nncp_zipf_output_bias_qm0_v1`. Epistemic tier before execution:
full-symbol oracle plus planned exact constructive child; score credit zero.

The exact receipt-bound NNCP preprocessed corpus contains `200,608,961`
symbols over vocabulary size `16,392`. Although symbol ID and empirical
frequency rank have only `0.02796` linear rank correlation, the fixed law

```text
q(i) proportional to (i + 1)^-0.435
```

costs `13.724519` bits/symbol under full-corpus counts versus `14.000704` for
uniform, a zero-table oracle difference of `6,925,664` bytes. On the first
`65,536` symbols the same frozen exponent saves `1,764` ideal bytes versus
uniform. These values compare static priors only and do not claim improvement
over the trained NNCP trajectory.

The constructive candidate initializes NNCP's existing trainable output bias
to `-0.435 * log(i + 1)` instead of zero. It adds no parameter, table, symbol,
or archive metadata; encoder and decoder derive the vector from vocabulary ID.
All other initialization, parameters, optimizer state, online updates,
attention, arithmetic alphabet, and memory remain unchanged.

Promotion requires at least `800` actual bytes against the faithful
`96,142`-byte 65,536-symbol archive, positive aligned ideal gain in every true
corpus-chronological third, exact repeated encode/decode/state identity,
official NNCP inversion, decimal-memory compliance, and at most `65,536`
compressed incremental source bytes. A miss retires this exponent and rank-law
initialization without exponent, offset, piecewise, or frequency-table sweeps.

The exact candidate produced `96,357` bytes, losing `215` actual bytes against
the faithful `96,142`. Aligned ideal gain is `-215.279` bytes, with true
chronological thirds `-227.915`, `+188.672`, and `-176.036`. Two encoders,
decoder symbols, branch frequencies, losses, complete state, and official NNCP
raw inversion all agree. Peak allocated and reserved device memory are
`8,632,796,160` and `9,271,508,992` bytes; incremental source is `5,392` bytes.

Disposition: retire alpha `0.435` and numeric-rank output-prior initialization.
Do not sweep exponent, offset, piecewise laws, or transmitted frequency tables
around it. The static prior's large advantage over uniform does not survive
the random output embedding and joint online-training trajectory. Score and
forecast credit remain zero. Decision SHA-256:
`0f5c036a92ff3327ccdda538f6316e0f308fb4f324b9f26c555a3bd0492cf76b`;
guard SHA-256:
`4a6a236054dbb07bd5264b1c7d1d975b9aca71fd57316776ee9c265d66a948ff`.

## 2026-08-08 - NNCP tied BF16 symbol embedding candidate frozen

Candidate: `nncp_tied_bf16_embedding_qm0_v1`. Epistemic tier before
execution: planned exact constructive learned-representation child; score
credit zero.

The faithful model uses independent input and output matrices over `16,392`
symbols and width `1,024`: a float32 input embedding and a bfloat16 output
embedding. The candidate initializes one bfloat16 matrix from the faithful
input embedding and uses the same `Parameter` for symbol lookup and output
projection. PyTorch parameter enumeration and Adam therefore see one shared
parameter, not two aliased optimizer entries.

This removes `67,141,632` parameter bytes relative to the two faithful matrices
before gradient and optimizer-state effects. It adds no table, symbol,
metadata, model blob, or archive field. Transformer blocks, output bias,
optimizer hyperparameters, online update schedule, attention memory,
arithmetic alphabet, and official inverse remain unchanged. BF16 input lookup
is part of the frozen mechanism and is not separable from tying in this gate.

Promotion requires at least `800` actual bytes against the faithful
`96,142`-byte 65,536-symbol archive, positive aligned ideal gain in every true
corpus-chronological third, exact repeated encode/decode/state identity,
official NNCP inversion, decimal-memory compliance, and at most `65,536`
compressed incremental source bytes. A miss retires this exact tied-BF16
representation without dtype, partial-tying, scale, or projection sweeps.

The exact candidate produced `101,076` bytes, losing `4,934` actual bytes.
Aligned ideal gain is `-4,934.703` bytes, with every true chronological third
negative at `-1,736.997`, `-2,004.540`, and `-1,193.166`. Two encoders, decoder
symbols, branch frequencies, losses, complete state, and official NNCP raw
inversion all agree. The shared matrix removes `67,141,632` parameter bytes;
peak allocated and reserved device memory fall to `8,431,354,880` and
`9,072,279,552` bytes. Incremental source is `5,912` bytes.

Disposition: retire tied BF16 input/output embeddings. Do not sweep dtype,
partial tying, scale, or projection around this construction. Independent
symbol-reading and symbol-prediction geometry is essential to the present
online model; the memory reduction does not compensate its predictive loss.
Score and forecast credit remain zero. Decision SHA-256:
`2dc84d240a6bab5f4ab6c84e403a9f228ff601083af356142f58e6f380eb5968`;
guard SHA-256:
`217044fdf982ac7025b4c9fee37911fd1769979786374b1525279200841036fb`.

## 2026-08-08 - cmix rich-state H128 capacity gate rejected

Candidate: `cmix_richstate_lstm128_ceiling_qm0_v1`. Epistemic tier: exact
local same-object capacity diagnostic; score and forecast credit zero.

The donor's complete golden trace was absent, so a local `KH_TRACE` build
generated an exact opening `4,000,000`-byte trajectory on the receipt-bound
`transformed_ready.bin`. Its `32,000,040` `res_v3` records include the donor's
five-byte framing prefix. Bit reassembly is clean, the trace was not truncated,
and trace entropy differs from the byte-tier accumulator by only
`0.000047653` bits. The base finite archive is `492,615` bytes.

The frozen H32 fp16 head was retained and an independent zero-output H96
branch was trained once on one `1,048,576`-bit block. Summed logits form a
block-diagonal H128 realization that begins exactly at H32. A second block was
development-only; the next three blocks were disjoint confirmations. Scoring
used the donor u16 discretization and exact 32-bit finite range update. Dense
H128 bytes were conservatively charged twice.

H128 beat H32 in all confirmation thirds, but only by `6`, `4`, and `4`
finite bytes: `14` bytes over `393,216` modeled bytes, or `35.603841` B/MB.
The frozen target-derived gate was `7,816` B/MB. Full projection is
`20,904.397` gross bytes against a `4,588,897`-byte debt, model, source, and
reserve requirement, leaving `-4,567,992.603` bytes. H32 itself was positive
against the base in every confirmation block, so the rich feature path did
detect its known mechanism. Guarded peak RSS was `2,686,764` KiB.

Disposition: retire hidden-width, dense or block-diagonal widening, reset,
feature, optimizer, learning-rate, epoch, and fp16 rescue sweeps for this
rich-state residual-head neighborhood. A successor must expose a materially
different representation or information source with a measured multi-megabyte
ceiling. Exact evidence:
`results/cmix_richstate_lstm128_ceiling_qm0_v1/decision.json` and
`results/cmix_richstate_lstm128_ceiling_qm0_guard_v3.json`.

## 2026-08-08 - NNCP CP8 symbol readout rejected, resource donor retained

Candidate: `nncp_cp8_symbol_readout_qm0_v1`. Epistemic tier: exact constructive
65,536-symbol representation child; score and forecast credit zero.

The candidate kept NNCP's independent float32 input embedding and exact
16,392-way output bias but replaced its `16,392 × 1,024` BF16 output matrix.
For symbol `s = 256h + l`, its logit was an additive high-class projection,
low-identity projection, and fixed rank-8 CP interaction. This removed
`32,891,888` BF16 parameter bytes before optimizer-state savings and
transmitted no symbol table.

Two encodes produced the same `102,310`-byte archive and complete state. Branch
frequencies, losses, decoded symbols, joint arithmetic boundary, and official
NNCP raw inversion all agree. Peak allocated and reserved device memory were
`8,498,503,168` and `9,313,452,032` bytes. Each encode/decode phase completed
in approximately `105` measured seconds at this scope.

Compression failed decisively: the faithful archive is `96,142`, so actual
gain is `-6,168` bytes. Aligned ideal gain is `-6,168.721` bytes, with all
true chronological thirds negative at `-2,152.294`, `-1,660.433`, and
`-2,355.995`. Incremental source is `7,616` bytes.

Disposition: retire CP rank, high/low partition, dtype, bias, initialization,
and interaction-form sweeps for symbol-ID-factorized NNCP output readouts. The
implementation remains a zero-credit runtime/memory donor only if an
independently target-bearing information source can pay its compression loss.
Decision: `results/nncp_cp8_symbol_readout_qm0_v1/decision.json`; guard:
`results/nncp_cp8_symbol_readout_qm0_guard_v2.json`.

## 2026-08-08 - NNCP causal 32/32 update schedule authorized

Candidate: `nncp_midsegment32_update_qm0_v1`. Epistemic tier: exact
constructive 65,536-symbol changed-schedule child; score and full-corpus
forecast credit remain zero.

The faithful parent predicts each 64-symbol segment and then performs one Adam
update. This child predicts states 0–31, trains only on those completed
targets, performs the frozen Adam update, rebuilds decoder-visible KV state
under the updated weights, and predicts states 32–63. A second update uses
only the completed second-half targets. No parameter or archive side
information is added. Outgoing memory retains the parent's pre-update-forward
convention.

Two encodes produced the same `91,351`-byte archive and complete
model/optimizer/memory state. The faithful parent is `96,142` bytes, so the
exact finite payload gain is `4,791` bytes against an `800`-byte gate. Aligned
ideal gain is `4,790.561` bytes, positive in all true corpus-order thirds at
`1,614.137`, `1,814.825`, and `1,361.599` bytes. Branch frequencies, losses,
decoded symbols, joint arithmetic boundary, and official NNCP raw inversion
all agree.

The compressed incremental source is `5,488` bytes. Peak device allocation
and reservation are `9,052,226,560` and `9,563,013,120` bytes, both below the
decimal 10 GB boundary; guarded process RSS peaked at `3,873,536` KiB.

Disposition: authorize one source-native realization gate and a larger
constructive maturity gate. Do not infer the published NNCP result, a local
full-corpus score, or Endpoint428 composability from this prefix. The native
gate must charge any changed package, reproduce a decodable archive, and
distinguish the exact 32/32 rebuild schedule from the source's available
`train_len=32` surrogate. Decision SHA-256:
`7245450832f5e31240b861e62461b736ad25e5965f6af53b90b77427d5fd76a7`;
guard SHA-256:
`5ef4db12a8f64095188896b7164ff563c1f27970ac9fd63e00ace9bb55ef6cd1`.

## 2026-08-08 - source-native NNCP train-length-32 surrogate authorized

Candidate: `nncp_libnc_trainlen32_surrogate_qm1_v1`. Epistemic tier: exact
source-native 10,000-symbol surrogate; score and full-corpus forecast credit
remain zero.

The held LibNC binary exposes a 32-state training segment, which supplies two
updates per former 64-state interval but is not numerically identical to the
ROCm child's post-midpoint KV rebuild. The first attempt correctly failed
before compression: keeping `d_pos=320` made
`mem_len + train_len - d_pos = -32`, and LibNC rejected the negative
`nc_pad`. Those partial artifacts are preserved under the candidate's
`_infra1` results directory. The mechanically valid coupled profile is
`train_len=32`, `mem_len=256`, and `d_pos=288`.

With that invariant, two source-native encodes produced the identical
`8,417`-byte archive, SHA-256
`495919f83d46aa19e0514169df18204f60c44d4cf224c03ce6ec14d4ca598078`.
The exact batch-32 parent is `9,246` bytes, so actual gain is `829` bytes
against a frozen `500`-byte gate. Native decode reconstructed the exact
`13,310`-byte raw prefix, SHA-256
`a6ea11e7cb1674925943c9f8f3ecfd81f88a44bf59568c2564664602d02feebe`.
No executable or library bytes changed. Peak sampled single-process and tree
RSS were `4,343,288` and `4,361,708` KiB, below decimal 10 GB.

Disposition: authorize a mature source-native cadence measurement and preserve
the exact KV-rebuild implementation as a distinct integration path. Do not
inherit the published NNCP archive, project this opening gain, or sweep other
training lengths. Decision SHA-256:
`05a19d64ab9610c37e6772bf9b5f0304cb3dc9e264456750c92c14dd2cf40853`;
guard SHA-256:
`ba7920d63ed55bbbd539da3919d497e46b25a0b9b09d3bdfbc5716a9ae471f35`.

## 2026-08-08 - NNCP causal 32/32 update maturity gate authorized

Candidate: `nncp_midsegment32_update_262144_qm1_v1`. Epistemic tier: exact
constructive 262,144-symbol changed-schedule child; score and full-corpus
forecast credit remain zero.

Qm1 executed a fresh faithful parent on the same first `262,144` receipt-bound
symbols, whose endpoint maps exactly to raw byte `1,215,854` and a WRT
emission-group boundary. The faithful archive is `341,558` bytes. The frozen
32/32 update child produced `324,373` bytes twice, with identical complete
model, Adam, and persistent-memory state. Actual finite gain is `17,185` bytes
against the `8,000`-byte maturity gate.

Aligned ideal gain is `17,185.334` bytes. Every true corpus-order third is
positive at `5,629.646`, `5,374.912`, and `6,180.776` bytes. Branch
frequencies, segment losses, decoded symbols, joint arithmetic boundary, and
official NNCP raw inversion all agree. The candidate incremental source is
`6,212` bytes.

The faithful parent peaked at `8,634,352,640` allocated and `9,271,508,992`
reserved device bytes. The child peaked at `9,053,783,040` allocated and
`9,565,110,272` reserved bytes. Both pass decimal 10 GB. The outer guard's
maximum sampled process RSS was `3,926,500` KiB.

Disposition: authorize native integration and preserve the coupled built-in
`train_len=32,d_pos=288` profile as an independently positive source-native
path. Do not linearly project the gain, inherit the published NNCP score, or
claim Endpoint428 composability. The already launched exact
`1,998,848`-symbol LibNC maturity screen is the next scale discriminator.
Decision SHA-256:
`443facb7caf6e9c73de07d6d51403965c52d77e6fc5f91a6c6711196d344319e`;
guard SHA-256:
`11f631a2e130a47f8caf215f4eed3e920f7ff3a8c43818b7134660c3c3c31785`.

## 2026-08-08 - exact source-native NNCP 32/32 schedule authorized

Candidate: `nncp_libnc_exact_midsegment32_qm2_v1`. Epistemic tier: exact
source-native 10,000-symbol constructive codec; score and full-corpus forecast
credit remain zero.

The source patch serializes an explicit `midsegment32` archive flag. It codes
states 0-31, completes LibNC's fixed 64-state gradient graph with causally
irrelevant zero future inputs, restricts the first loss to states 0-31,
updates Adam without shifting persistent memory, rebuilds the first-half
key/value graph under the new coefficients, codes states 32-63, applies the
second-half loss, and only then shifts memory. Both online updates use the
faithful parent's segment-level learning-rate coordinate. The enwik9 retrain
path retains its independent `retrain_train_step` and original full-segment
update.

After one clean-source build failure exposed trace-only calls inherited from a
locally instrumented donor, the canonical source-tar patch was corrected
mechanically; no compression parameter changed. Two clean-source encodes then
produced byte-identical `8,422`-byte archives, SHA-256
`882185c36f42ef837b31770d30731dd01a9f3cddb08b89cc5f2d27c0c8abac1e`.
The identical faithful archive is `9,246` bytes, so actual gain is `824` bytes
against the frozen `500`-byte gate. The patched decoder reconstructed the
exact `13,310`-byte raw prefix, SHA-256
`a6ea11e7cb1674925943c9f8f3ecfd81f88a44bf59568c2564664602d02feebe`.
The version-2 header proves batch `32`, segment `64`, and `midsegment32=1`.

The receipt-bound source tar is `1,180,969` bytes and the patch compresses to
`3,592` bytes, yielding a complete `1,184,561`-byte source package under the
`1,300,000`-byte gate. Peak sampled single-process and process-tree RSS were
`5,764,328` and `5,784,936` KiB, below decimal 10 GB.

Disposition: authorize one exact source-native maturity gate on a larger
identical population. Do not inherit the published NNCP score, linearly
project the opening gain, claim Endpoint428 composability, or vary the split,
optimizer, learning rate, segment length, or stream count. Decision SHA-256:
`71032efdb387c62dd09057d843041b7a838fe53a9b2cb5ea3d0b3862025283f3`;
guard SHA-256:
`391410a1ded379a95259c5402f00c573325322d5daa455a247b09e69252a26d0`.

## 2026-08-08 - SYMBIONT-16 P64 crossing screen frozen

Candidate: `nncp_symbiont16_p64_cmix21_qm0_v1`. Epistemic tier before
execution: planned exact same-backend representation control; score and
forecast credit zero.

Earlier candidates fed official NNCP big-endian U16 symbols directly into the
byte-native B2 cmix21 backend. On `250,000` raw input bytes, text and binary
backend modes produced `56,905` and `56,930` byte archives and missed the
frozen `44,678`-byte ceiling. Those receipts close direct interleaved U16BE,
but they did not test byte-plane layout, alignment specificity, or native
symbol decisions.

This screen binds the first `1,048,576` symbols of the full-corpus NNCP
artifact, whose complete `401,217,922`-byte file has SHA-256
`c82bfca1b4fb8e31d31ded609de579dc55dd12153411961a7ae0cc9b9f9605a5`.
Three identical-backend arms are frozen: original interleaved bytes (`I16`),
64-symbol high-then-low planes (`P64`), and a cyclic one-block low-plane
rotation (`P64R`). All layouts must invert exactly after cmix decode, and P64
must reproduce byte-identically.

Promotion requires P64 at or below `4.30` actual payload bits per symbol and
strictly smaller than both I16 and P64R under the same cmix binary. This is the
predeclared `0.15` bits/symbol engineering distance from the approximately
`4.14`-`4.16` all-in target band. A pass authorizes exactly one native CMIX16
branch-tree design, not a score forecast. A miss retires this byte-layout
crossing without endian, block-size, plane-width, dictionary, or backend
parameter sweeps. SABLE, copies, tries, and event-source models remain closed.

Before the cmix arms terminated, a zero-credit empirical diagnostic on the
identical `1,048,576` symbols measured `11.693727` zero-order bits/symbol and
`6.291043` bits/symbol conditioned on the immediately prior symbol. Byte
order-1 conditional entropy is `6.013934` bits for I16, `6.746009` for P64,
and `6.745923` for P64R. Thus P64 has no first-order byte-entropy advantage and
its alignment control is indistinguishable at that order. This does not price
cmix's longer contexts and cannot decide the gate; it makes an eventual P64
win specifically attributable to higher-order class/identity modeling rather
than generic adjacent-byte entropy.

## 2026-08-08 - NNCP output-bias-only midpoint attribution frozen

Candidate: `nncp_midpoint_bias_only_qm0_v1`. Epistemic tier before execution:
planned exact 65,536-symbol causal attribution child; score and forecast credit
zero.

The exact full-parameter 32/32 schedule saves `4,791` bytes at `65,536`
symbols and `17,185` bytes at `262,144` symbols. This child isolates whether
that information gain is primarily a compact symbol-rate correction. It keeps
the faithful model and its full-parameter update after state 63, but inserts
one midpoint Adam step whose gradients are restricted to the existing
`16,392`-entry output bias. The second-half keys and values are rebuilt under
the updated bias state. No parameter, table, or archive field is added.

Promotion requires at least `1,600` actual bytes against the identical
faithful `96,142`-byte archive, positive chronological thirds, exact repeated
archives and complete state, independent decode, official raw inversion,
decimal-memory compliance, and at most `65,536` compressed incremental source
bytes. The `1,600`-byte floor is approximately one third of the full midpoint
gain and scales to target-debt magnitude over the receipt-bound symbol count,
but receives no forecast credit. A pass authorizes compact symbol-bias transfer
to a runnable substrate. A miss retires this exact bias-only mechanism without
parameter-group, split, optimizer, learning-rate, or scope sweeps; the full
midpoint result remains separate evidence.

Terminal result: **REJECT**. Both independent arithmetic encodes produced
`97,746` bytes and the identical complete-state SHA-256
`687722a02a7ce708707a130dd0a5b439de367cfc89191523e41806caf6c77316`.
The faithful parent is `96,142` bytes, so output-bias-only midpoint adaptation
loses `1,604` actual bytes. Aligned ideal gain is also negative in every
chronological third: `-559.703219`, `-516.453129`, and `-528.749002` bytes.
Independent arithmetic decode, decoded-symbol identity, branch-frequency and
loss identity, complete-state identity, and the official NNCP raw inverse all
pass. The incremental compressed source is `6,056` bytes. The external RSS
guard passes at `3,868,856` KiB sampled tree RSS, while NNCP reports
`9,052,210,176` peak allocated bytes and `10,068,426,752` peak reserved bytes;
the latter fails the strict decimal reservation criterion. This exact scalar
symbol-bias realization is retired. It does not adjudicate a distinct
output-projection-plus-KV interaction gate, which is authorized only if both
the exact native and mature cadence antecedents pass.

## 2026-08-08 - Agent B convergence protocol frozen

Agent B owns causal predictive discovery and compact NNCP/symbol-domain
realization. Agent A owns representation legality, full-corpus backend
adjudication, packaging, inversion, and submission proof. Agent B will not
duplicate Agent A's far-history or transform work, and concurrent-job timing
is diagnostic rather than qualifying.

The three unchanged Agent B gates form a triangulation. The exact native
`65,536`-symbol midpoint gate and the mature `1,998,848`-symbol cadence gate
must both pass before one nested `K/O/OK/F/S` causal attribution is authorized.
That descendant must isolate unchanged-parameter KV rebuild, exact
output-projection-plus-bias update, their interaction, the full update, and a
shifted-residual control. The already rejected scalar-bias child supplies a
separate negative control and is not reopened. A compact midpoint realization
must retain at least `80%` of the full gain, add at most `15%` parent runtime
and `128 MiB` resident memory, keep every chronological third positive, beat
the shifted control, and decode exactly.

The P64 crossing must pass its frozen `4.30` bits/symbol, I16, P64R, inverse,
determinism, and memory conditions before one larger unchanged-layout maturity
gate. Only a second pass authorizes one memory-substitutive native CMIX16
comparison: balanced numeric-ID tree (`TID`) versus a canonical trie over exact
dictionary expansions (`TEXP`). No endian, block, plane, dictionary, or
backend sweep is allowed. Midpoint and CMIX16 gains remain non-additive until
one exact same-object joint replay proves complementarity. No fourth Agent B
family is authorized before these descendants either reach an exact `100M`
result or retire.

Conditional MIDAS exactness audit, before materialization: the faithful NNCP
head is an untied `16,392 x 1,024` bfloat16 output embedding plus a
`16,392`-entry bias. The first-half cross-entropy gradient is not rank `32`:
the native midpoint loss contains `32` positions in each of `32` streams, so
it is a sum of `1,024` residual/hidden outer products and has rank at most
`1,024` before optimization. Earlier rank-32 wording omitted the batch/stream
dimension and is superseded by this correction. The production profile uses
Adam with `beta1=0`, `beta2=0.9999`, epsilon `1e-8`, and per-parameter
clipping. Its elementwise second-moment normalization depends on the existing
dense optimizer state and does not preserve even the corrected raw-gradient
rank in general. Therefore an exact MIDAS child cannot inherit a low-rank
parameter-delta claim from the teacher.
The exact `O/OK` arms must first measure the existing head update. A later
low-rank episodic correction is an approximation requiring its own joint
arithmetic replay. The output matrix itself is `33,570,816` bytes in bfloat16;
one float32 second-moment surface is `67,141,632` bytes. A compact descendant
must reuse or replace those parent surfaces rather than count them as free new
state.

## 2026-08-08 - NNCP midpoint phase persistence attributed exactly

Diagnostic: `nncp_midpoint_phase_attribution_qm0_v1`. Epistemic tier: exact
trace attribution with zero score and forecast credit.

The receipt consumes all `917,527` balanced-branch frequencies from the
receipt-bound faithful, full-midpoint, and bias-only traces over the identical
`65,536` symbols. All input hashes, branch populations, registered totals,
registered chronological thirds, and the unchanged first half of segment zero
match exactly. The full midpoint's `4,790.561037` ideal bytes decompose into
`2,081.894044` bytes in positions `0-31` and `2,708.666993` bytes in positions
`32-63`: `43.458251%` versus `56.541749%`. Segment zero contributes exactly
zero before its first midpoint and `53.206193` bytes afterward. All eight
position octets, all four segment quarters, and all `32` segment totals are
positive; segment-quarter gains are `1,289.544721`, `1,328.820558`,
`1,107.472339`, and `1,064.723420` bytes.

The bias-only trace instead loses `1,604.905350` ideal bytes, split
`-810.080613` before and `-794.824737` after the midpoint. Its quarter losses
worsen from `-162.026946` to `-595.796653` bytes. The diagnostic source package
is `4,580` bytes and the guarded process completes below its `1 GiB` limit.

Conclusion: the full midpoint mechanism creates a persistent beneficial model
trajectory, not only a stateless correction to the immediately following 32
states. A compact child must reproduce a causal persistent-state effect.
Second-half-only savings are an upper bound on immediate plus accumulated
effects, not transferable MIDAS credit. This receipt does not identify a
sufficient parameter subset, authorize `K/O/OK/F/S` before both exact-native
and mature antecedents pass, or support a full-corpus forecast.

## 2026-08-08 - NNCP midpoint persistence replicated at 262,144 symbols

Diagnostic: `nncp_midpoint_phase_attribution_262144_qm1_v1`. Epistemic tier:
exact larger-scope trace attribution with zero score and forecast credit.

The receipt consumes the fresh faithful-parent and full-midpoint traces for all
`262,144` symbols and `3,670,169` branch frequencies. It reproduces the
registered `17,185.333882` ideal bytes and every chronological third exactly.
The gain splits into `7,613.926179` bytes before current midpoint updates and
`9,571.407703` bytes afterward, or `44.304791%` versus `55.695209%`. The
pre-midpoint share differs from the exact `65,536`-symbol receipt by only
`0.846539` percentage points.

Every second half is positive. Two first halves and one combined segment are
nonpositive; the minimum is segment `3` at `-47.498210` bytes. All `16`
consecutive eight-segment blocks are positive. Most importantly, the final
`32` segments gain `4,242.888556` bytes: `1,847.051537` before and
`2,395.837019` after their midpoint updates, with every tail segment positive.
All hashes, registered totals and thirds, branch populations, first-segment
identity, persistence-share replication, and tail conditions pass. The source
package is `5,568` bytes and the guarded process stays below `1 GiB`.

Conclusion: persistent trajectory benefit is stable at four times the exact
population and remains strong in the tail. A stateless within-segment adapter
cannot realize the full teacher mechanism. Any later `O/OK` or low-rank child
must carry a deterministic state across segment boundaries and must be priced
through a new joint replay. The separate exact-native and mature source-native
gates still control descendant authorization.

Conditional attribution graph audit: both the LibNC `enwik9` profile and the
faithful ROCm model use an untied input embedding and output embedding
(`tied_embed=0`). The hidden path is input embedding, twenty Transformer
blocks, and final normalization; only then do the output embedding and output
bias produce logits. Neither output-head tensor feeds keys, values, hidden
states, or persistent memories.

Consequently, under an output-head-only midpoint update, rebuilding first-half
KV state cannot change any probability: the proposed `O` and `OK` arms must be
byte- and probability-identical. Rebuilding KV with no parameter update also
makes `K` identical to the parent. These arms remain useful integrity controls;
any difference proves implementation or replay drift. The substantive compact
comparison is therefore persistent exact output-head adaptation versus the
full deep update and shifted-truth control. A head update can still explain
later first-half gains because its weights and Adam second-moment state persist
across segments, but it does not require a KV rebuild. This structural result
does not authorize the gate before both active antecedents pass.

Conditional native implementation audit: do not isolate the output head by
calling `nc_sgd_opt_set(param, NULL)` and later reattaching it. Disassembly of
the receipt-bound LibNC shows that detachment invokes the optimizer variable
destructor and frees its state; reattachment invokes the constructor. That
would reset Adam's persistent second moment and create a different mechanism.

The attributable native `O` route is instead a midpoint-only stop-gradient at
the final hidden tensor immediately before `embed_out`. Forward probabilities
are unchanged, while midpoint backward reaches only `embed_out` and
`out_bias`; all parameter objects and optimizer surfaces remain attached. The
shared optimizer step intentionally advances, so its later effect is part of
the causal head-update trajectory and must be controlled by shifted truth.
For LibNC, the stopped deep first-half graph and key/value references must be
preserved rather than released by the full-update cleanup path. If they remain
valid, second-half coding can continue on identical cached values without a
replay, and the ordinary second-half gradient can consume the complete deep
graph. `K=P` and `O=OK` probability/state hashes are mandatory implementation
checks. Any state reset, missing graph reference, or equality failure kills
that realization rather than authorizing a workaround. This is a source-level
plan only until both active antecedents pass.

