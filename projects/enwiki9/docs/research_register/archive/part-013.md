# Research Register Archive 013

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-08 - Exact native 65,536-symbol raw-proof guard corrected

The running `nncp_libnc_exact_midsegment32_65536_qm3_v1` driver leaves its
candidate source unchanged, but its post-decode Boolean is insufficient for
promotion. It currently accepts any nonempty decoded byte string for which
the one-million-byte raw input `startswith(restored_bytes)`. A truncated raw
prefix could therefore satisfy the recorded field
`raw_prefix_decode_exact=true`.

An initial audit incorrectly selected the `322,978`-byte raw inverse from the
receipt-bound full-corpus dictionary population. Direct comparison disproves
that population identity: q3's locally built first-1M `16384,512` dictionary
changes preprocessed byte zero. The first `131,072` bytes have hashes
`6c5e26cbd314c8e6980387049790986b2827642d437d80aee71cb5e51309146d`
for q3 and
`6e4e2e7d17de3e37de6d81699a132113b4c7bdd330173cad614cdc8a9247e4cb`
for the full-corpus-dictionary stream. The earlier `322,978`-byte comparator
and `symbol_raw_map.bin` row therefore apply only to the distinct full-corpus
population and are quarantined from q3 adjudication.

Before the active encoder removed its staging files, the exact q3 population
was bound as follows:

```text
candidate.nncp.pp bytes       1,506,396
candidate.nncp.pp SHA-256     bd1c6153bad848e739acb3dba139d411f527d6372e3707b5ca31de063a9ad0b5
candidate.nncp.voc bytes      804
candidate.nncp.voc SHA-256    814ebc4be8ebf998f77c0bc62fc29df834a34be086ceb6355123070a3be515dd
modeled prefix bytes          131,072
modeled symbols               65,536
expected raw bytes            88,279
expected raw SHA-256          02693fbe724e91de753a65fe7f036c552dc18ea183eba0605799e885badacf95
```

The expected raw reference was constructed by taking exactly the first
`131,072` bytes of q3's staging stream and invoking the same receipt-bound
NNCP `pd` inverse with q3's staging vocabulary. It is byte-identical to the
first `88,279` bytes of the raw 1M input. The `.pp` and `.voc` files are
encoder staging artifacts, not external decoder dependencies: NNCP embeds the
compressed vocabulary in the main archive, recreates temporary inverse files
during decode, and removes them afterward.

The method independently reproduces the completed q2 result: taking the first
`20,000` staging bytes (`10,000` symbols) yields exactly `13,310` raw bytes,
SHA-256
`a6ea11e7cb1674925943c9f8f3ecfd81f88a44bf59568c2564664602d02feebe`,
byte-identical to q2's native `restored.raw`. This validates the local-prefix
inverse construction without trusting q3's weak Boolean.

After q3 terminalizes, promotion requires its restored output to have exactly
`88,279` bytes and the expected SHA-256 above, in addition to direct raw-prefix
identity, serialized mode header, archive gain, source package, and process-
tree memory compliance. A mismatch quarantines the native result and forbids
descendant authorization. This correction changes no active process and
grants zero score or forecast credit.

Conditional head-only graph implementation audit: the current full-midpoint
patch completes 32 dummy future states because ordinary
`trf_eval_gradient()` factorizes and consumes all key/value graph nodes up to
`graph_len=64`; it then rebuilds states `0..31` after the deep update. A
compact output-head arm should not inherit that path unchanged.

The exact attributable route is a dedicated first-half head-gradient helper.
During states `0..31`, detach only the final normalized hidden tensor with
`nc_stop_grad()` immediately before `embed_out`, while retaining every
decoder key/value node. Concatenate and backpropagate only those 32 detached
head outputs, release only their output tensors, and leave the deep key/value
references alive. Then apply the shared Adam update and continue coding states
`32..63` directly; the ordinary second-half deep gradient can consume the
complete 64-state key/value graph. This removes both dummy future evaluation
and first-half replay from the proposed `O` realization without changing its
coded probabilities.

Receipt-bound disassembly confirms that `nc_stop_grad()` consumes its tensor:
for a multiply referenced tensor it allocates and copies a detached value,
then frees the supplied reference; for a single reference it frees the graph
node in place. The implementation must therefore pass it an intentionally
owned reference at the head boundary. `O=OK` remains an exact probability and
state control: an optional unchanged-deep first-half replay may recreate graph
references, but it must not alter the second-half probabilities. Any missing
key/value reference, output mismatch, or optimizer-state reset kills the arm.
This is still conditional source design with zero credit; no child is
authorized before both active midpoint antecedents pass.

Conditional optimizer-preserving attribution audit: an exact output-head-only
midpoint update does not require detaching parameters from the shared LibNC
optimizer.  Each `NCParam` retains its private `sgd_opt` variable pointer, and
that pointer is the opaque value delivered to `sgd_opt_update_var()` during
backward.  A midpoint-only callback can therefore forward gradients only when
the opaque pointer equals the existing `embed_out` or `out_bias` optimizer
variable and discard every other parameter callback.  LibNC applies each
forwarded variable update inside that callback; the subsequent shared
`nc_sgd_opt_update()` advances the optimizer clock.  Deep parameter values and
their private Adam surfaces remain unchanged at the midpoint, while the shared
clock advancement is intentionally retained and controlled by shifted truth.
No parameter object or second-moment surface is destroyed or recreated.
Receipt-bound disassembly confirms that `sgd_opt_update_var()` dispatches the
per-variable Adam operation immediately, whereas the Adam target reached by
`nc_sgd_opt_update()` increments the shared step and recomputes its bias
correction scalars without walking the parameter list.

This supplies the safest exact but deliberately expensive `OK` attribution
arm: retain the full 64-state backward geometry, filter optimizer writes to
the untied output head, update, and rebuild the unchanged deep first-half
keys/values before coding the second half.  It is not the compact realization,
because full deep backward and replay remain.  The efficient `O` arm still
requires the dedicated detached-head gradient helper described above so it
can preserve the original key/value graph without replay.  Since the output
head is downstream of every key/value and hidden tensor, `O` and `OK` must
produce identical probabilities, archives, parameters, optimizer state, and
persistent memories.  A mismatch kills the implementation.  This refinement
changes no active source, authorizes no job before both antecedents pass, and
receives zero score and forecast credit.

The conditional shifted-truth control is frozen before either antecedent
terminalizes.  At each midpoint and independently within each of the 32
streams, `S` pairs hidden state `i` with the already decoded first-half target
at `(i + 1) mod 32`.  This one-position cyclic permutation preserves the exact
target multiset, update count, graph size, optimizer calls, learning-rate
coordinate, and timing shape while destroying correct hidden/target
alignment.  Its second-half truths and update are unchanged.  `S` therefore
controls generic extra optimization capacity without importing future data.
No shift distance or permutation sweep is allowed.

The `K` integrity arm performs no midpoint optimizer step: it discards the
first-half graph, rebuilds the same first-half states under unchanged
parameters, then retains the parent's ordinary full-segment truth and update.
It must be byte-, parameter-, optimizer-, and memory-identical to `P`.  The
`O` and `OK` arms instead use true first-half targets for the head-only
midpoint step and the true second-half-only deep update at segment end, exactly
matching `F`'s two loss populations.  `OK` consumes and rebuilds the first-half
deep graph; `O` preserves it through the detached-head helper.  These frozen
definitions prevent a favorable terminal result from selecting the control
or update semantics post hoc.

Active q3 payload checkpoint: the exact clean-source 65,536-symbol candidate
encode terminalized at `41,564` bytes, SHA-256
`c879411c5bfe4c8afb3998fd46fe367963da33fcd96130af559ddb7577991ce7`.
Its adjacent faithful archive is `44,786` bytes, so the finite native gain is
`3,222` bytes against the frozen `3,000`-byte threshold.  Independent header
inspection shows file version `2`, batch `32`, segment `64`, and serialized
`midsegment32=1`.  This passes the payload condition only.  The patched native
decoder is still active, and q3 remains unauthorized until the exact
`88,279`-byte raw reference hash, direct prefix comparison, complete source
accounting, and terminal decimal-memory guard all pass.

Package-aware maturity interpretation is frozen separately from qm2's
unchanged `30,000`-byte scientific screen.  The published NNCP total is
`107,261,318` bytes with `628,955` program bytes.  Q3's currently measured
source package is `1,184,561` bytes, a `555,606`-byte increase.  Closing the
published total's `2,261,318`-byte debt while charging that increase and a
precommitted `500,000`-byte reserve requires `3,316,924` full-symbol archive
bytes.  Normalized only as a promotion gate to qm2's exact
`1,998,848 / 200,608,961` symbol fraction, that is `33,049.505219` bytes, so
the whole-byte floor is `33,050`.  A qm2 result from `30,000` through `33,049`
passes its frozen mechanism screen but is not target-bearing under this
package and reserve; `33,050` or more clears this normalization but remains
zero-credit until a decodable same-schedule archive and full-corpus package
exist.  No linear score forecast is claimed.

## 2026-08-08 - SYMBIONT-16 P64 crosses its monotone rate ceiling

The active `nncp_symbiont16_p64_cmix21_qm0_v1` job has produced a decisive
rate impossibility result before terminalization. On the frozen
`1,048,576`-symbol population, `4.30` bits/symbol permits at most `563,609`
whole archive bytes. While the P64 encode was still incomplete, its actual
monotone archive descriptor reached `565,248` bytes, or exactly `4.3125`
bits/symbol. The final P64 archive cannot shrink, so the frozen rate condition
is permanently false regardless of P64R, repeat-encode, or decode outcomes.

The preceding I16 arm completed at `1,000,845` bytes, or
`7.63584136962890625` bits/symbol. The driver remains untouched so it can
produce its full exact controls, determinism, inverse, and external memory
receipt, but those fields can no longer authorize a native CMIX16 child.
The P64 arm subsequently terminalized at `1,458,972` bytes, or
`11.131072998046875` bits/symbol: `895,363` bytes above the largest whole
archive allowed by the frozen rate gate and `458,127` bytes worse than I16.
Its matched P64R, repeat, and decode stages continue unchanged so the driver
can emit the complete control receipt; they cannot reverse the rate failure.
Decision boundary: retire NNCP-symbol byte-plane crossing, 64-symbol
transposition, and this unchanged byte-native CMIX backend. Do not sweep
endian order, block length, plane width, dictionary size, or backend. The
planned `TID/TEXP` CMIX16 descendant is unauthorized. This is a zero-credit
prefix-screen rejection and does not change the `109,389,323` forecast or the
`4,389,323`-byte debt to the active `105,000,000` target.

## 2026-08-08 - Mature train-length-32 first-block diagnostic

The active `nncp_libnc_trainlen32_mature_1998848_qm2_v1` encode completed its
first exact `499,712`-symbol native block and loaded the second block. A
read-only `/proc` observer recorded input position `1,998,848` bytes
(`999,424` symbols loaded) while the candidate archive descriptor remained at
`573,440` bytes. The next observed write was `638,976` bytes after second-block
processing had begun. These live sizes are buffered cumulative output and are
not an exact terminated first-block payload.

The receipt-bound faithful-parent native trace prices the identical first
block at `618,776` actual range-coder bytes. Its four independently terminated
Q16 shadow blocks are `618,778`, `504,341`, `453,176`, and `414,513` bytes.
The full shadow payload is `1,990,806` bytes, while the native parent archive
is `2,042,820`; the final native trace counter is `1,990,804` coder bytes, so
the native archive carries `52,016` non-coder bytes. This establishes strong
early diagnostic benefit for train length 32, but stdio buffering and the
unterminated candidate stream forbid subtracting the live descriptor from the
parent block as an exact gain.

The frozen decision remains unchanged: only the final candidate archive can
pass the `30,000`-byte mature gate, and a pass authorizes a repeated decodable
confirmation with marginal chronological evidence. No score, forecast, or
compact-midpoint descendant credit is granted by this block observation.

## 2026-08-09 - Agent A native cmix-obias 250M baseline completed

The frozen baseline arm of
`cmix_obias_helical_xmlsafe_prefix_qm4_v1` completed with return code zero.
The exact 250,000,000-byte input has SHA-256 `ba261e95...9de8`. Native
`cmix-obias` produced a 33,262,388-byte payload (`40bdd7f0...020e`) and the
fixed package wrapper produced a 33,554,085-byte archive
(`ed5a5b6c...8f09`). Peak sampled single-process and tree RSS were both
9,216,780 KiB, below the 9,765,625 KiB decimal limit.

The observed 20,348.5528-second wall time is diagnostic because independent
dense jobs shared the host. No roundtrip or residual comparison is claimed by
this arm alone. The executable, head asset, working-directory shape, model
settings, wrapper, and resource policy remain frozen for the residual arm.
Receipt:
`results/cmix_obias_helical_xmlsafe_prefix_qm4_v1/baseline_backend_receipt.json`.

## 2026-08-09 - QM4 same-residual literal-ledger control proves source value

Candidate
`cmix_obias_helical_xmlsafe_literal_ledger_control_qm4_v1` retained the exact
249,407,080-byte QM4 residual and replaced only the source-distance column
with the 592,920 removed literal bytes. The finite copy ledger is 36,640
compressed bytes; the matched literal ledger is 156,696 bytes. Exact
far-history source reuse therefore contributes 120,056 bytes relative to
literal reinsertion on this identical residual.

The literal ledger decompressed, reconstructed a materialized 250,000,000-byte
prefix, and reproduced SHA-256 `ba261e95...9de8`. All frozen residual and
ledger hashes passed, as did the guarded adaptive job. This is exact
attribution evidence, not a backend gain or target forecast. Receipt:
`results/cmix_obias_helical_xmlsafe_literal_ledger_control_qm4_v1/decision.json`.

## 2026-08-09 - QM5 full-corpus XML-safe census passes direct physical ceiling

Candidate `cmix_obias_helical_xmlsafe_full_census_qm5_v1` applied the unchanged
QM4 selector to the full canonical 1G corpus and frozen raw far-history
ledger. It selected 253,428 matches covering 24,413,010 exact bytes. Coverage
by chronological third is 1,016,167, 19,803,452, and 3,593,391 bytes, so the
later corpus is materially denser than the opening 250M population. Every
source is exact, fully prior, and closed; every target stays inside one text
payload and excludes CR, LF, `<`, and `>`.

The complete full-corpus copy ledger compresses to 1,425,836 bytes. A
conservative LZMA charge for the existing complete transform/inverse source is
3,664 bytes. The direct eight-bit ceiling is therefore 22,983,510 bytes. It
exceeds the `cmix-obias` research-parent debt plus frozen 500,000-byte reserve
by 18,990,685 bytes. This authorizes the already planned matched residual
backend adjudication, but supplies no actual parent surprisal, retained-stream
trajectory, archive delta, compliant full-1G package, or score credit. Receipt:
`results/cmix_obias_helical_xmlsafe_full_census_qm5_v1/decision.json`.

Live-position unit audit: NNCP's `--max_size=1,998,848` is a symbol count, but
`/proc/<pid>/fdinfo` reports the underlying byte offset.  The receipt-bound
preprocessed alphabet is serialized as big-endian U16, so complete input
consumption requires descriptor position `3,997,696`, not `1,998,848`.
The observed `1,998,848`-byte position is exactly `999,424` symbols: two
`499,712`-symbol native blocks and one half of the frozen population.  Source
inspection confirms that `encode_file()` right-shifts the physical file size
by `symb_shift=1`, compares `max_size` in symbols, and `read_block()` consumes
two bytes per symbol.  Any live report treating the current descriptor offset
as full-population completion is invalid.  The terminal archive and its
serialized symbol count remain the only promotion evidence.

## 2026-08-09 - SYMBIONT-16 rotated control confirms negligible alignment value

The first matched `P64R` arm of the still-running
`nncp_symbiont16_p64_cmix21_qm0_v1` driver terminalized at `1,459,780`
archive bytes on the frozen `1,048,576`-symbol population, or
`11.137237548828125` bits/symbol. The correctly aligned `P64` arm is
`1,458,972` bytes (`11.131072998046875` bits/symbol), so alignment improves
this byte-plane realization by only `808` bytes, or `0.00616455078125`
bits/symbol, relative to the one-segment-rotated low-plane control.

This establishes a real but target-negligible alignment effect. Both arms are
catastrophically above the frozen `563,609`-byte `4.30`-bits/symbol ceiling,
and `P64` is already `458,127` bytes worse than interleaved `I16`. The driver
has advanced unchanged to its second `P64` encode for determinism and later
decode checks, but no remaining field can authorize `TID`, `TEXP`, or another
CMIX16 descendant. The byte-plane crossing, block layout, and unchanged
byte-native backend remain retired with zero score and forecast credit.

## 2026-08-09 - Exact native 65,536-symbol midpoint antecedent passes strict audit

Candidate `nncp_libnc_exact_midsegment32_65536_qm3_v1` completed its patched
native decode and terminal guard. The matched parent archive is `44,786`
bytes and the exact midpoint candidate is `41,564` bytes, an actual `3,222`-
byte gain against the frozen `3,000`-byte gate. The archive hashes are
`a5bf29c6...d7324dc` and `c879411c...99ce7`, respectively. The serialized
header is valid and binds version 2, batch 32, segment 64, midpoint mode 1,
vocabulary 336, seed 123, CPU bf16 execution, and no CUDA flag.

An independent audit supersedes the driver's permissive nonempty-prefix
Boolean. The restored output is exactly `88,279` bytes, has SHA-256
`02693fbe...acf95`, and is byte-identical under direct `cmp` to the first
`88,279` bytes of the canonical one-million-byte raw input. The complete
counted source package is `1,184,561` bytes, below the frozen `1,300,000`-
byte ceiling. The guard returned zero without exceeding its decimal limit;
peak sampled single-process and process-tree RSS were `5,778,764` and
`5,799,804` KiB against `9,765,625` KiB.

This passes the exact-native 65,536-symbol antecedent only. It does not prove
deterministic repeat encoding, isolated runtime, a compact realization, an
eligible NNCP package, full-corpus transfer, or any Hutter score. The compact
`P/K/O/OK/F/S` attribution child remains unauthorized until the separately
running `1,998,848`-symbol mature cadence gate also passes. Strict receipt:
`results/nncp_libnc_exact_midsegment32_65536_qm3_v1/strict_audit.json`.

## 2026-08-09 - Mature cadence crosses the first-half processing boundary

The live `nncp_libnc_trainlen32_mature_1998848_qm2_v1` encoder loaded its
third native block at `2026-08-09T04:04:45-04:00`. The read-only process
descriptor moved from `1,998,848` to `2,998,272` physical input bytes, binding
`1,499,136` of the frozen `1,998,848` big-endian U16 symbols as loaded. At
that transition, the monotone on-disk candidate archive remained `1,097,728`
bytes.

This is the first observation after the encoder finished processing the first
two `499,712`-symbol blocks. It is still not an exact first-half payload:
stdio may retain an unwritten tail, and the arithmetic stream is not
terminated. The receipt-bound parent shadow totals `1,123,119` coder bytes
over its first two blocks, but subtracting the live descriptor would produce
an invalid `25,391`-byte gain claim because the counted objects and buffering
boundaries differ. Only the terminal candidate archive may be compared with
the `2,042,820`-byte native parent and the frozen `30,000` scientific or
`33,050` package-aware gain thresholds. This boundary receives zero score and
does not yet authorize `P/K/O/OK/F/S`.

## 2026-08-09 - SYMBIONT-16 terminal receipt retires layout crossing

Candidate `nncp_symbiont16_p64_cmix21_qm0_v1` completed every frozen encode,
repeat, and decode control on the exact `1,048,576`-symbol population. `I16`
is `1,000,845` bytes (`7.635841369628906` bits/symbol), `P64` is `1,458,972`
bytes (`11.131072998046875` bits/symbol), and `P64R` is `1,459,780` bytes
(`11.137237548828125` bits/symbol). Every decoded layout exactly reproduced
its `2,097,152`-byte serialized input. The second `P64` encode reproduced the
same `1,458,972` bytes and SHA-256
`d71caa89c87468efbb96e277344b2af48c11b06060c413dc6d28f9c0ebdb2d37`.

Thus the small `808`-byte alignment value is deterministic, but `P64` is
`458,127` bytes worse than `I16` and `895,363` bytes above the largest whole
archive allowed by the `4.30`-bits/symbol gate. Peak sampled single-process
and process-tree RSS were `9,639,156` and `9,669,788` KiB, leaving only
`126,469` and `95,837` KiB beneath the `9,765,625` KiB decimal limit. The
guard returned zero without exceeding the limit; timing is diagnostic because
the host was shared.

Terminal decision: retire NNCP-symbol byte-plane crossing, 64-symbol plane
transposition, and this unchanged byte-native CMIX backend. Do not sweep
endian order, block size, plane width, dictionary size, or backend. `TID`,
`TEXP`, and all CMIX16 descendants are unauthorized. This exact negative
receipt receives zero score and does not change the `109,389,323` forecast or
the `4,389,323`-byte debt to `105,000,000`. Receipt:
`results/nncp_symbiont16_p64_cmix21_qm0_v1/decision.json`.

## 2026-08-09 - Concurrent mature-midpoint and QM4 gates invalidated by ENOSPC

Jobs `20260809T002749Z_e3dd8c43dc` and
`20260809T055112Z_b3d4d1e586` both terminated with `OSError: [Errno 28] No
space left on device`. Their guard writers could not emit terminal JSON, so
the stale running receipts were reconciled to `cancelled` with reason
`infrastructure_failure_enospc_no_terminal_receipt`. This is an infrastructure
failure, not compression evidence for or against either mechanism.

The mature train-length-32 attempt left a monotone but unterminated
`1,490,944`-byte archive with SHA-256
`bca5a07758e08ff52bc7ac94e6466f97ce5146074bb4b974a9479442c2185792`.
It is below both frozen terminal ceilings, but arithmetic termination, final
model updates, and framing are absent; it receives zero gain, score, forecast,
or promotion credit. The exact-native `65,536`-symbol antecedent remains
passed, while the `1,998,848`-symbol maturity antecedent remains unknown.

Disk recovery removed only closed regenerable scratch: completed
`cmix-richhead` temporary toolchain/QM0 directories, plus the failed July 27
article-order transfer work directories `cmix_lex_article_order_transfer_v1`
and `_retry1`. Canonical receipts and the successful `_retry2` artifact remain
intact. Available filesystem capacity rose to `13,214,461,952` bytes. Agent B
may retry the unchanged mature gate after removing its partial output
directory; Agent A retains ownership of any QM4 residual retry.

## 2026-08-09 - Factor replay superseded by conditional MIDAS-G1024

The unmaterialized `MIDAS-1024-1` factor-cache idea is superseded with zero
evidence credit. Its `35,667,968`-byte factors can be multiplied once at the
midpoint to form the ordinary output-head gradient, then accumulated directly
into the existing output matrix. Retaining and replaying the factors would add
an avoidable second projection on every later forward pass and introduce an
arbitrary cache horizon.

Conditional descendant: `MIDAS-G1024`. It remains unauthorized until the
exact native and mature cadence antecedents both pass and exact `O` establishes
that output-projection-plus-bias adaptation retains enough of full `F`.
At each midpoint, form the exact causal gradient from all `32 x 32 = 1,024`
decoded examples:

```text
G_W = mean_i((p_i - onehot(y_i)) outer h_i)
G_b = mean_i(p_i - onehot(y_i))
```

Update the existing output matrix and bias in place. LibNC disassembly shows
that `gradient_clip=0.05` caps the L2 norm of each complete parameter gradient,
not individual elements. Let `clip(g)=g*min(1,0.05/||g||_2)`. Replace Adam's
dense elementwise midpoint state with one persistent second-moment scalar per
tensor and one shared midpoint counter:

```text
t   <- t + 1
g_W <- clip(G_W)
g_b <- clip(G_b)
v_W <- beta2 * v_W + (1 - beta2) * mean(g_W ** 2)
v_b <- beta2 * v_b + (1 - beta2) * mean(g_b ** 2)
W   <- W - lr * g_W / (sqrt(v_W / (1 - beta2 ** t)) + epsilon)
b   <- b - lr * g_b / (sqrt(v_b / (1 - beta2 ** t)) + epsilon)
```

Use the parent's fixed `beta2=0.9999`, epsilon `1e-8`, learning-rate
coordinate, and L2 cap. `beta1=0` requires no scalar first moment. The ordinary
full parent Adam update still occurs after state 63; its persistent surfaces
and step counter are not advanced by the compact midpoint update. The midpoint
mechanism therefore adds two scalar moments and one integer counter, no archive
data, and no forward-time expert. A full float32 `G_W` temporary is
`67,141,632` bytes;
the first-half hidden population is `4,194,304` bytes, keeping the intended
increment below `128 MiB` before allocator overhead. Actual process-tree RSS
controls eligibility.

If authorized, compare parent `P`, exact head-Adam `O`, full teacher `F`,
scalar-RMS `MIDAS-G1024`, and an identical-capacity control whose first-half
truths are cyclically shifted by one position within each stream. Require
exact arithmetic decode, deterministic repeat, every chronological third
positive, the shifted control materially worse, at least `80%` of `F`'s
actual gain, at most `128 MiB` added resident memory, and at most `15%` added
parent runtime. Do not sweep normalization, optimizer constants, split,
parameter group, or shifted control around a miss.

## 2026-08-09 - MIDAS-G1024 LibNC ownership contract audited

Read-only audit of the receipt-bound `libnc.so` and `libnc.h` establishes a
safe native implementation path if the antecedent gates authorize it.
`nc_dup_tensor()` is not a copy: disassembly shows it increments the reference
count and returns the identical tensor pointer. Calling `nc_set_param()` on
such a duplicate would mutate the parent parameter graph and is forbidden.

The midpoint head-gradient helper must instead:

1. retain the first-half final hidden tensors before `embed_out`;
2. detach copied hidden values without releasing the deep key/value graph;
3. allocate distinct tensors with `nc_new_tensor_from_tensor()`, populate them
   with `nc_tensor_copy()`, and attach custom gradient tags only to those
   temporary `embed_out` and `out_bias` copies;
4. recompute the head softmax/loss on the exact `1,024` first-half examples;
5. capture the two gradients through a custom `nc_backward()` callback;
6. apply scalar-RMS updates to the original head using tensor operations and
   `nc_tensor_convert()` while leaving its parent Adam objects attached; and
7. free only the temporary head graph, preserving the original first-half
   hidden/key/value graph for the exact second-half loss and segment-end full
   update.

`nc_new_tensor_from_tensor()` allocates a distinct same-shaped tensor with no
graph node; `nc_set_param()` asserts that no node already exists.
`nc_stop_grad()` consumes its input and may remove a graph in place when the
reference count is one, so it may be used only on a deliberately retained
copy, never directly on a parent parameter or sole deep-state reference.

The shifted control changes only the temporary head-loss targets by a
one-position cyclic shift within each stream. Coded truths, parent forward
probabilities, persistent deep memory, update capacity, and execution order
remain matched. Mandatory integrity assertions are unchanged: `K=P`,
`O=OK`, parent Adam state survives bit-identically outside intended updates,
and arithmetic encode/decode reproduce the same exact symbol stream.

## 2026-08-09 - Archive-neutral NNCP block observer specified

The mature qm2 driver decides only the terminal total; live file sizes cannot
establish chronological marginal gains. The receipt-bound arithmetic coder
already exposes every required state field in `PutBitState`: `range`, `low`,
pending `current_byte`/`n_bytes`, buffered `idx`, flushed `byte_count`, and the
arithmetic buffer itself. Its existing `put_bit_get_bit_count()` is explicitly
approximate and should not be promoted as exact block evidence.

For a positive maturity result, the repeated decodable confirmation may add an
archive-neutral observer after each native `process_block()`:

1. copy the `PutBitState` structure;
2. allocate a separate same-sized arithmetic buffer and copy the live buffered
   bytes through `idx`;
3. replace the copied state's write callback with a count-only sink;
4. invoke `put_bit_flush()` on only the copied state; and
5. record original symbol boundary, exact hypothetical terminated arithmetic
   bits, model step, and learning-rate coordinate.

The live coder, live buffer, output file, model state, and probability
trajectory remain untouched. Add the fixed header byte count separately.
Run the same observer on the faithful and candidate schedules over the exact
same continuous symbol population. Cumulative candidate-minus-parent gains at
matched boundaries provide chronological evidence; differences of cumulative
gains provide marginal block evidence. Each intermediate boundary includes
its own finite termination cost and is therefore a terminated-prefix measure,
not an additive independently reset block stream. The final boundary must
equal the actual terminated archive arithmetic count, and an observer-enabled
repeat must reproduce the observer-disabled archive byte-for-byte.

Physical-byte correction from direct `arith.c` inspection: `put_bit_flush()`
returns the minimum number of bits sufficient for decoding, while the counted
archive stores every final byte delivered to the write callback. These values
can differ by the unused tail bits of the last byte. The cloned observer must
therefore record both (a) the return value from `put_bit_flush()` and (b) the
cloned state's `byte_count` after flushing. Chronological promotion and archive
equality use physical arithmetic bytes from (b), plus the fixed header bytes;
(a) is diagnostic only. At the final boundary, cloned physical bytes must
equal the live archive's arithmetic-byte extent exactly. Comparing rounded or
fractional minimum-bit counts to file size would be an accounting error.

## 2026-08-09 - Native midpoint attribution byte gates frozen

The strict exact-native population binds parent `P=44,786` bytes and full
midpoint teacher `F=41,564` bytes, hence `G_F=3,222` actual bytes. If the
mature cadence antecedent passes, the single `P/K/O/OK/F/S` attribution gate
uses these fixed whole-archive thresholds:

```text
required O retention        ceil(0.80 * 3,222) = 2,578 bytes
largest passing O archive   44,786 - 2,578      = 42,208 bytes
minimum aligned-vs-S margin ceil(0.10 * 3,222) =   323 bytes
incremental source package                           <= 65,536 bytes
```

`K` must be byte-identical to `P`; `OK` must be byte-identical to `O`.
The archive-neutral block observer must show positive `O` gain at every
chronological boundary and at least `80%` of `F`'s gain on every matched
chronological split. The shifted-truth `S` control uses identical update
capacity and must trail aligned `O` by at least `323` terminal bytes. All arms
must independently decode the exact symbol population, reproduce the expected
raw prefix through the official inverse, and repeat byte-identically.

These are attribution thresholds, not Hutter score credit. `O` passing only
authorizes the predeclared scalar-state `MIDAS-G1024` approximation. That
compact descendant separately retains the existing `80%` gain, `128 MiB`
incremental RSS, `15%` runtime, shifted-control, exact decode, and deterministic
repeat conditions.

## 2026-08-09 - Native source audit limits mature train-length inheritance

Read-only inspection of the receipt-bound NNCP source establishes that the
active `train_len=32` surrogate is not merely the exact 64-symbol model with
one extra optimizer call. `process_block()` sets `n_states` from `seg_len`,
evaluates and differentiates one complete `n_states` population, calls the
optimizer, then advances the transformer memory by `train_len`. Consequently,
changing the native option from 64 to 32 jointly changes graph length,
attention/memory advancement, and update cadence. The arithmetic predictions
and learned trajectory all change together.

The mature run also exercises a mechanism absent from the finite 65,536-symbol
exact gate. The `enwik9` profile sets `retrain_period=1`; after `process_block()`
codes a nonterminal native block, `encode_file()` calls `retrain_block()` over
the decoder-visible retrain buffer before reading the next block. That pass
uses the same configured `seg_len`, performs full evaluate/gradient/update
cycles, and maintains a separate retrain learning-rate step. The live retry's
stable `573,440`-byte descriptor, unchanged `999,424`-physical-byte input
position, and RSS rise from about `4.70` to `5.69` GB identify this post-block
retraining phase; they do not establish a terminated block payload. The
65,536-symbol q3 population reaches end-of-file after its sole block and skips
this path entirely.

This gives the terminal mature result a strict interpretation. A pass at
`30,000` actual bytes proves only that the native 32-symbol realization remains
useful at the frozen population. A pass at the separately frozen `33,050`
package-aware gate establishes target-scale authorization under its stated
normalization. Neither result transfers archive bytes to the exact
segment-64 midpoint candidate. Only the already frozen `P/K/O/OK/F/S`
same-object attribution can identify which portion belongs to midpoint state
refresh, output-head adaptation, deep adaptation, or generic extra optimizer
capacity. This audit receives zero score credit and does not alter the active
job or either threshold.

## 2026-08-09 - Exact output-head attribution maps to LibNC optimizer semantics

Read-only source and binary inspection resolves the native implementation
contract for conditional arm `O`. The transformer computes its symbol logits
only after the final hidden state, through `embed_out` and `out_bias`; neither
parameter feeds attention keys, values, persistent memory, or later hidden
states. LibNC invokes `sgd_opt_update_var()` from the backward callback only
for parameter variables reached by the current graph. The subsequent
`nc_sgd_opt_update()` advances the optimizer's shared step and bias-correction
coordinate. Thus a detached-hidden helper graph containing only the real
`embed_out`, `out_bias`, softmax, and first-half truth loss performs an exact
head-only midpoint Adam update while retaining the same extra global optimizer
step as full arm `F`; it does not silently update deep parameters.

Arm `O` must preserve the original first-half transformer graph while the
detached head helper backpropagates, then code states 32--63 using the updated
head and the unchanged first-half keys/values. Arm `OK` discards and rebuilds
states 0--31 after the same head update. Because the head is downstream of all
hidden and key/value state, the rebuilt transformer state is identical to the
preserved state; `O` and `OK` must therefore produce byte-identical archives
and model trajectories. Any divergence is an implementation failure, not a
new compression effect. Similarly, `K` must be identical to `P` when it
performs the same discard/rebuild without an optimizer update.

The helper must copy final hidden values into distinct no-graph tensors; a
LibNC tensor duplication only increments a reference and does not detach.
Backward must still use the real head parameters so their existing Adam
moments advance, followed by exactly one global optimizer-step advance. This
is a frozen implementation invariant for `P/K/O/OK/F/S`, receives zero score
credit, and remains unauthorized until the mature antecedent passes.

